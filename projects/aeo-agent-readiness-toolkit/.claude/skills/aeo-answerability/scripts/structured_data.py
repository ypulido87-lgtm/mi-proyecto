#!/usr/bin/env python3
"""Extract and audit JSON-LD, entity clarity and citation readiness.

Parsing successfully is not the same as being correct: this tool separately
reports JSON validity, Schema.org plausibility, entity graph quality and
whether structured claims are supported by visible text.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

# Types this toolkit knows how to reason about. An unlisted type is reported as
# unverified, never as invalid, because Schema.org is large and evolving.
KNOWN_TYPES = {
    "Organization", "LocalBusiness", "Corporation", "NGO", "EducationalOrganization",
    "Person", "Product", "Service", "Brand", "Place", "PostalAddress", "Event",
    "Article", "NewsArticle", "BlogPosting", "TechArticle", "ScholarlyArticle",
    "FAQPage", "Question", "Answer", "HowTo", "BreadcrumbList", "ListItem",
    "WebSite", "WebPage", "AboutPage", "ContactPage", "CollectionPage", "ItemList",
    "Offer", "AggregateOffer", "AggregateRating", "Review", "Rating", "SearchAction",
    "ImageObject", "VideoObject", "Recipe", "JobPosting", "Course", "SoftwareApplication",
}
REQUIRED_PROPERTIES = {
    "Organization": ["name", "url"],
    "Product": ["name"],
    "Article": ["headline", "datePublished"],
    "NewsArticle": ["headline", "datePublished"],
    "BlogPosting": ["headline", "datePublished"],
    "Person": ["name"],
    "Event": ["name", "startDate"],
    "FAQPage": ["mainEntity"],
    "BreadcrumbList": ["itemListElement"],
    "LocalBusiness": ["name", "address"],
}
# Types whose "name" is a navigation label or a structural value, not a claim
# about content. Requiring them to appear in visible text flags correct markup.
NON_CLAIM_TYPES = {
    "ListItem", "BreadcrumbList", "PostalAddress", "ImageObject", "ContactPoint",
    "GeoCoordinates", "OpeningHoursSpecification", "SearchAction", "EntryPoint",
    "Rating", "AggregateRating", "Offer", "AggregateOffer", "PropertyValue", "Brand",
}
# Only top-level entities need a stable @id; a nested address or list item does not.
PRIMARY_TYPES = {
    "Organization", "LocalBusiness", "Corporation", "NGO", "EducationalOrganization",
    "Person", "Product", "Service", "Place", "Event", "Article", "NewsArticle",
    "BlogPosting", "TechArticle", "ScholarlyArticle", "FAQPage", "HowTo", "WebSite",
    "WebPage", "Course", "JobPosting", "SoftwareApplication", "Recipe",
}
CITATION_PROPERTIES = ["author", "datePublished", "dateModified", "publisher", "url", "@id", "citation", "sameAs"]


class Extractor(HTMLParser):
    """Pull JSON-LD blocks, microdata hints and visible text out of a document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self.visible: list[str] = []
        self.microdata_types: list[str] = []
        self.rdfa_types: list[str] = []
        self.meta: dict[str, str] = {}
        self.canonical: str | None = None
        self.title: str | None = None
        self._in_jsonld = False
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {k.lower(): (v or "") for k, v in attrs}
        if tag == "script":
            if attributes.get("type", "").lower() == "application/ld+json":
                self._in_jsonld = True
            else:
                self._skip_depth += 1
        elif tag in ("style", "noscript", "template"):
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "link" and "canonical" in attributes.get("rel", "").lower():
            self.canonical = attributes.get("href")
        elif tag == "meta":
            key = attributes.get("name") or attributes.get("property")
            if key:
                self.meta[key.lower()] = attributes.get("content", "")
        if attributes.get("itemtype"):
            self.microdata_types.append(attributes["itemtype"])
        if attributes.get("typeof"):
            self.rdfa_types.append(attributes["typeof"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            if self._in_jsonld:
                self._in_jsonld = False
            elif self._skip_depth:
                self._skip_depth -= 1
        elif tag in ("style", "noscript", "template") and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_jsonld:
            self.blocks.append(data)
        elif not self._skip_depth:
            text = data.strip()
            if text:
                self.visible.append(text)
                if self._in_title and self.title is None:
                    self.title = text


def _iter_nodes(node: Any):
    """Walk a JSON-LD document, including @graph and nested objects."""
    if isinstance(node, list):
        for item in node:
            yield from _iter_nodes(item)
    elif isinstance(node, dict):
        yield node
        for key, value in node.items():
            if key.startswith("@") and key != "@graph":
                continue
            yield from _iter_nodes(value)


def _types(node: dict[str, Any]) -> list[str]:
    raw = node.get("@type") or node.get("type")
    if isinstance(raw, str):
        return [raw.rsplit("/", 1)[-1]]
    if isinstance(raw, list):
        return [str(t).rsplit("/", 1)[-1] for t in raw]
    return []


def audit(html: str, page_url: str = "") -> dict[str, Any]:
    extractor = Extractor()
    try:
        extractor.feed(html)
        extractor.close()
    except Exception:
        pass

    visible_text = " ".join(extractor.visible)
    visible_lower = visible_text.lower()

    parsed: list[Any] = []
    json_errors: list[dict[str, Any]] = []
    for index, raw in enumerate(extractor.blocks):
        try:
            parsed.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            json_errors.append({"block": index, "error": str(exc), "preview": raw.strip()[:160]})

    nodes = [node for document in parsed for node in _iter_nodes(document)]
    entities: list[dict[str, Any]] = []
    schema_issues: list[dict[str, Any]] = []
    identifiers: dict[str, int] = {}
    type_counts: dict[str, int] = {}

    for node in nodes:
        node_types = _types(node)
        if not node_types:
            continue
        context = ""
        for document in parsed:
            if isinstance(document, dict) and document.get("@context"):
                context = str(document["@context"])
                break
        for type_name in node_types:
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        node_id = node.get("@id")
        if node_id:
            identifiers[node_id] = identifiers.get(node_id, 0) + 1
        entity = {
            "types": node_types,
            "id": node_id,
            "name": node.get("name") or node.get("headline") or node.get("legalName"),
            "url": node.get("url"),
            "properties": sorted(k for k in node if not k.startswith("@")),
        }
        entities.append(entity)

        for type_name in node_types:
            if type_name not in KNOWN_TYPES:
                schema_issues.append(
                    {"severity": "P3", "type": type_name, "issue": "Type not in the toolkit's known list; verify against schema.org before trusting it"}
                )
                continue
            for required in REQUIRED_PROPERTIES.get(type_name, []):
                # A department declared as an article author legitimately has no
                # site of its own; it is identified by its parent organization.
                if required == "url" and node.get("parentOrganization"):
                    continue
                if required not in node:
                    schema_issues.append(
                        {"severity": "P2", "type": type_name, "issue": "Missing recommended property: " + required}
                    )
            # A structured name that appears nowhere in the visible text is the
            # classic fabricated-markup signal — but only for types whose name is
            # a claim about content, never for navigation or structural values.
            name = entity["name"]
            if type_name in NON_CLAIM_TYPES:
                continue
            # alternateName exists precisely for localized or secondary names.
            # A page that shows the Spanish name of an entity declared with its
            # English name is consistent, not fabricated.
            alternates = node.get("alternateName")
            alternates = alternates if isinstance(alternates, list) else ([alternates] if alternates else [])
            if any(isinstance(a, str) and a.lower() in visible_lower for a in alternates):
                continue
            if isinstance(name, str) and len(name) > 3 and name.lower() not in visible_lower:
                # Distinguish a fabricated claim from a wording mismatch: if most
                # of the significant words do appear on the page, the entity is
                # real and only its label differs. Only a name whose words are
                # largely absent looks invented.
                words = [w for w in re.findall(r"[A-Za-zÀ-ÿ0-9]{3,}", name.lower())]
                found = [w for w in words if w in visible_lower]
                ratio = len(found) / len(words) if words else 0
                if ratio >= 0.6:
                    schema_issues.append({
                        "severity": "P2",
                        "type": type_name,
                        "issue": "Structured name differs from the visible wording: " + name[:60],
                    })
                else:
                    schema_issues.append({
                        "severity": "P1",
                        "type": type_name,
                        "issue": "Structured name not supported by visible text: " + name[:60],
                    })
        for key in ("url", "@id", "sameAs", "logo", "image"):
            value = node.get(key)
            for candidate in value if isinstance(value, list) else [value]:
                if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
                    if not urlsplit(candidate).netloc:
                        schema_issues.append({"severity": "P2", "type": ",".join(node_types), "issue": "Malformed URL in " + key})

    if not any(isinstance(d, dict) and d.get("@context") for d in parsed) and parsed:
        schema_issues.append({"severity": "P1", "type": "-", "issue": "JSON-LD without an @context declaration"})
    for context_value in [str(d.get("@context")) for d in parsed if isinstance(d, dict) and d.get("@context")]:
        if "schema.org" not in context_value:
            schema_issues.append({"severity": "P2", "type": "-", "issue": "Non-schema.org @context: " + context_value[:60]})

    duplicate_ids = sorted(k for k, v in identifiers.items() if v > 1)
    if duplicate_ids:
        schema_issues.append({"severity": "P2", "type": "-", "issue": "Duplicate @id values: " + ", ".join(duplicate_ids[:3])})

    entities_without_id = [
        e for e in entities if not e["id"] and (PRIMARY_TYPES & set(e["types"]))
    ]

    # Citation readiness: can a factual claim on this page be attributed?
    citation = {
        "canonical": extractor.canonical,
        "title": extractor.title,
        "meta_description": extractor.meta.get("description"),
        "author": _first_property(nodes, "author") or extractor.meta.get("author"),
        "date_published": _first_property(nodes, "datePublished") or extractor.meta.get("article:published_time"),
        "date_modified": _first_property(nodes, "dateModified") or extractor.meta.get("article:modified_time"),
        "publisher": _first_property(nodes, "publisher"),
        "og_url": extractor.meta.get("og:url"),
    }
    citation["signals_present"] = sum(1 for k, v in citation.items() if k != "signals_present" and v)
    # A date is required to cite an article, but a homepage or a service page is
    # not dated content: demanding datePublished there manufactures a defect and
    # pressures the owner into inventing a date.
    dated_types = {"Article", "NewsArticle", "BlogPosting", "TechArticle", "ScholarlyArticle", "Report"}
    citation["is_dated_content"] = bool(dated_types & set(type_counts))
    citation["ready"] = bool(
        citation["canonical"]
        and citation["title"]
        and (not citation["is_dated_content"] or citation["date_published"] or citation["date_modified"])
    )

    words = re.findall(r"[A-Za-zÀ-ÿ0-9']+", visible_text)
    answerability = {
        "word_count": len(words),
        "has_title": bool(extractor.title),
        "has_meta_description": bool(extractor.meta.get("description")),
        "faq_entities": type_counts.get("FAQPage", 0) + type_counts.get("Question", 0),
        "breadcrumbs": type_counts.get("BreadcrumbList", 0),
        "thin_content": len(words) < 150,
    }

    return {
        "page_url": page_url,
        "jsonld_blocks": len(extractor.blocks),
        "jsonld_parse_errors": json_errors,
        "microdata_types": extractor.microdata_types[:20],
        "rdfa_types": extractor.rdfa_types[:20],
        "entities": entities,
        "entity_types": type_counts,
        "entities_without_id": len(entities_without_id),
        "duplicate_ids": duplicate_ids,
        "schema_issues": schema_issues,
        "citation_readiness": citation,
        "answerability": answerability,
        "note": "Valid JSON is not proof of correct Schema.org. Semantic accuracy still needs human or validator review.",
    }


def _first_property(nodes: list[dict[str, Any]], key: str) -> Any:
    for node in nodes:
        if key in node:
            value = node[key]
            if isinstance(value, dict):
                return value.get("name") or value.get("@id") or True
            if isinstance(value, list) and value:
                first = value[0]
                return first.get("name") if isinstance(first, dict) else first
            return value
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract and audit JSON-LD, entities and citation readiness")
    parser.add_argument("source", help="Path to an HTML file or a URL")
    args = parser.parse_args()
    if args.source.startswith(("http://", "https://")):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "aeo-agent-readiness" / "scripts"))
        from aeolib.fetch import fetch

        response = fetch(args.source)
        if not response.ok:
            raise SystemExit("Cannot fetch: HTTP " + str(response.status) + " " + (response.error or ""))
        html, url = response.text, response.url
    else:
        html, url = Path(args.source).read_text(encoding="utf-8", errors="replace"), args.source
    print(json.dumps(audit(html, url), indent=2))


if __name__ == "__main__":
    main()
