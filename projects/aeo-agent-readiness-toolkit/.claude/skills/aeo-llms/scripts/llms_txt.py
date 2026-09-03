#!/usr/bin/env python3
"""Audit an existing llms.txt, or propose a curated one from real URLs.

llms.txt is a curated index for agents, not a copy of the sitemap. This tool
only ever proposes URLs that exist in the supplied source, filters out the
categories that do not belong, and refuses to invent a link.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

# Ordered by the priority an agent needs: identity first, then documentation,
# offering, resources, policies and contact.
PRIORITY_SECTIONS = [
    ("About", ["about", "who-we-are", "company", "team", "mission", "quienes-somos", "nosotros", "sobre"]),
    ("Documentation", ["docs", "documentation", "guide", "guides", "manual", "reference", "handbook", "kb", "knowledge"]),
    ("API", ["api", "developers", "developer", "openapi", "swagger", "graphql", "sdk"]),
    ("Products and services", ["product", "products", "service", "services", "solutions", "pricing", "plans", "catalog", "productos", "servicios"]),
    ("Resources", ["blog", "articles", "news", "resources", "case-study", "case-studies", "whitepaper", "faq", "support", "help", "recursos", "noticias"]),
    ("Policies", ["privacy", "terms", "legal", "security", "cookie", "accessibility", "compliance", "privacidad", "terminos"]),
    ("Contact", ["contact", "contacto", "sales", "book", "demo"]),
]
# Never index these: they are private, transient or duplicate surfaces.
EXCLUDE_SEGMENTS = {
    "admin", "wp-admin", "administrator", "login", "signin", "sign-in", "logout", "register",
    "signup", "account", "dashboard", "cart", "checkout", "search", "tag", "tags", "author",
    "feed", "rss", "amp", "print", "preview", "draft", "test", "staging", "tmp", "temp",
    "cgi-bin", "wp-json", "wp-content", "node_modules", "assets", "static", "_next",
}
EXCLUDE_SUFFIXES = (".json", ".xml", ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".pdf", ".zip", ".woff", ".woff2")


def should_exclude(url: str) -> str | None:
    parts = urlsplit(url)
    path = parts.path.lower()
    if parts.query:
        return "carries query parameters"
    if parts.fragment:
        return "carries a fragment"
    if path.endswith(EXCLUDE_SUFFIXES):
        return "is an asset or data file, not a readable page"
    for segment in [s for s in path.split("/") if s]:
        if segment in EXCLUDE_SEGMENTS:
            return "matches the excluded segment '" + segment + "'"
    if re.search(r"/page/\d+|/p/\d+$", path):
        return "is a pagination URL"
    return None


def classify(url: str) -> str:
    path = urlsplit(url).path.lower()
    segments = [s for s in path.split("/") if s]
    if not segments:
        return "About"
    for section, tokens in PRIORITY_SECTIONS:
        if any(any(token == segment or token in segment for token in tokens) for segment in segments):
            return section
    return "Resources"


def curate(urls: list[str], site_name: str, summary: str) -> dict[str, Any]:
    kept: dict[str, list[str]] = {}
    excluded: list[dict[str, str]] = []
    seen: set[str] = set()
    for url in urls:
        normalized = url.rstrip("/") or url
        if normalized in seen:
            continue
        seen.add(normalized)
        reason = should_exclude(url)
        if reason:
            excluded.append({"url": url, "reason": reason})
            continue
        kept.setdefault(classify(url), []).append(url)

    lines = ["# " + site_name, ""]
    if summary:
        lines += ["> " + summary, ""]
    lines += [
        "This file is a curated index of the pages most useful to an AI agent.",
        "It is not a sitemap and it does not grant any content-usage rights.",
        "",
    ]
    for section, _ in PRIORITY_SECTIONS:
        if section not in kept:
            continue
        lines.append("## " + section)
        lines.append("")
        for url in sorted(kept[section]):
            label = _label(url)
            lines.append("- [" + label + "](" + url + ")")
        lines.append("")
    return {
        "content": "\n".join(lines).rstrip() + "\n",
        "included": sum(len(v) for v in kept.values()),
        "sections": {k: len(v) for k, v in kept.items()},
        "excluded": excluded,
    }


def _label(url: str) -> str:
    segments = [s for s in urlsplit(url).path.split("/") if s]
    if not segments:
        return "Home"
    return segments[-1].replace("-", " ").replace("_", " ").strip().title()


def audit(text: str) -> dict[str, Any]:
    links = re.findall(r"\[([^\]]*)\]\(([^)]+)\)", text)
    headings = re.findall(r"^(#{1,3})\s+(.+)$", text, re.M)
    problems = []
    if not text.startswith("# "):
        problems.append("Does not start with an H1 title")
    if not links:
        problems.append("Contains no links; an index with no entries is not useful")
    excluded = [{"url": url, "reason": should_exclude(url)} for _, url in links if should_exclude(url)]
    if excluded:
        problems.append(str(len(excluded)) + " links point at excluded surfaces (admin, search, assets or parameterised URLs)")
    return {
        "headings": [{"level": len(h), "text": t} for h, t in headings],
        "link_count": len(links),
        "links": [{"label": label, "url": url} for label, url in links][:100],
        "questionable_links": excluded,
        "problems": problems,
        "valid": not problems,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit_parser = subparsers.add_parser("audit", help="Audit an existing llms.txt")
    audit_parser.add_argument("source", help="Path to llms.txt")

    curate_parser = subparsers.add_parser("curate", help="Propose a curated llms.txt from a URL list")
    curate_parser.add_argument("urls", help="File with one URL per line, or a sitemap-derived JSON list")
    curate_parser.add_argument("--site-name", required=True)
    curate_parser.add_argument("--summary", default="")
    curate_parser.add_argument("--output", help="Write the proposal here instead of stdout")

    args = parser.parse_args()
    if args.command == "audit":
        print(json.dumps(audit(Path(args.source).read_text(encoding="utf-8", errors="replace")), indent=2))
        return

    raw = Path(args.urls).read_text(encoding="utf-8", errors="replace").strip()
    if raw.startswith("["):
        urls = json.loads(raw)
    else:
        urls = [line.strip() for line in raw.splitlines() if line.strip() and not line.startswith("#")]
    result = curate(urls, args.site_name, args.summary)
    if args.output:
        Path(args.output).write_text(result["content"], encoding="utf-8")
        print(json.dumps({k: v for k, v in result.items() if k != "content"}, indent=2))
        print("Wrote " + args.output)
    else:
        print(result["content"])


if __name__ == "__main__":
    main()
