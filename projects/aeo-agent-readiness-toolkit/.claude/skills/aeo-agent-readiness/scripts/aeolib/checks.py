"""Check definitions: applicability gates, local evidence and live evidence.

Two rules govern this module.

1. A repository file is never proof of a public URL. Local findings and live
   findings are recorded separately on the same check; the live layer wins when
   both exist, and the local layer is preserved as context.
2. A check is N/A only when the site genuinely lacks the underlying capability,
   and the reason is always recorded.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

from . import scoring
from .fetch import fetch
from .paths import load_skill_script
from .scoring import AEO_TECHNICAL, AGENT_READINESS, FAIL, MANUAL, NA, PASS, WARNING

robots_parser = load_skill_script("aeo-discoverability", "robots_parser.py")
sitemap_validator = load_skill_script("aeo-discoverability", "sitemap_validator.py")
http_inspect = load_skill_script("aeo-discoverability", "http_inspect.py")
semantic_html = load_skill_script("aeo-content-accessibility", "semantic_html.py")
markdown_negotiation = load_skill_script("aeo-content-accessibility", "markdown_negotiation.py")
structured_data = load_skill_script("aeo-answerability", "structured_data.py")
discovery_scan = load_skill_script("aeo-protocol-discovery", "discovery_scan.py")
bot_access = load_skill_script("aeo-bot-access", "bot_access.py")
commerce_protocols = load_skill_script("aeo-commerce-readiness", "commerce_protocols.py")

# Crawlers SEO comerciales. Bloquearlos es una decisión deliberada y común del
# propietario (coste de ancho de banda, no querer que analicen sus backlinks) y
# no afecta a buscadores ni a agentes de IA. No puede tratarse como un bloqueo
# del sitio.
COMMERCIAL_SEO_CRAWLERS = {
    "ahrefsbot", "semrushbot", "dotbot", "mj12bot", "blexbot", "rogerbot",
    "screaming frog seo spider", "megaindex", "serpstatbot", "dataforseobot",
    "petalbot", "seokicks", "sistrix", "barkrowler", "zoominfobot",
}


def _blocking_severity(groups: list[list[str]]) -> tuple[bool, list[str]]:
    """Return (is_critical, agents). Only a block that reaches search or AI
    crawlers — or the wildcard group — is critical."""
    agents = [a for group in groups for a in group]
    critical = [a for a in agents if a.strip().lower() not in COMMERCIAL_SEO_CRAWLERS]
    return bool(critical), agents


SECTIONS = [
    ("Discoverability", ["robots.txt", "Sitemap", "HTTP Link headers", "DNS-AID"]),
    ("Content Accessibility", ["Markdown negotiation", "Server-rendered content", "Semantic HTML"]),
    ("Bot Access", ["AI Bot Rules", "Actual bot access", "Content Signals", "Web Bot Auth"]),
    (
        "Protocol Discovery",
        ["API Catalog", "OAuth discovery", "OAuth Protected Resource", "Auth.md", "MCP Server Card",
         "A2A Agent Card", "Agent Skills", "WebMCP", "ARD Manifest"],
    ),
    ("Commerce", ["x402", "MPP", "UCP", "ACP"]),
    (
        "AEO",
        ["Crawlability", "Content availability", "Entity clarity", "Structured data", "Answer extraction",
         "Citation readiness", "Canonicalization", "Content duplication"],
    ),
    ("Availability", ["Homepage availability", "llms.txt"]),
]


@dataclass
class Check:
    name: str
    section: str
    score: str
    status: str = MANUAL
    priority: str = "P2"
    detail: str = ""
    local: dict[str, Any] | None = None
    live: dict[str, Any] | None = None
    applicability: str = ""
    recommendation: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "section": self.section,
            "score": self.score,
            "status": self.status,
            "priority": self.priority,
            "detail": self.detail,
            "applicability": self.applicability,
            "recommendation": self.recommendation,
            "local_evidence": self.local,
            "live_evidence": self.live,
            "data": self.data,
        }


class Registry:
    def __init__(self) -> None:
        self._checks: dict[str, Check] = {}

    def define(self, name: str, section: str, score: str) -> Check:
        check = Check(name=name, section=section, score=score)
        self._checks[name] = check
        return check

    def get(self, name: str) -> Check:
        return self._checks[name]

    def all(self) -> list[Check]:
        order = [name for _, names in SECTIONS for name in names]
        return sorted(self._checks.values(), key=lambda c: order.index(c.name) if c.name in order else 999)


def _na(check: Check, reason: str) -> None:
    check.status = NA
    check.priority = "P3"
    check.detail = "Not applicable: " + reason
    check.applicability = reason


def build_registry() -> Registry:
    registry = Registry()
    for section, names in SECTIONS:
        for name in names:
            score = AEO_TECHNICAL if section == "AEO" or name in ("Server-rendered content", "Semantic HTML") else AGENT_READINESS
            registry.define(name, section, score)
    return registry


# --------------------------------------------------------------------------
# Local layer
# --------------------------------------------------------------------------

def run_local(registry: Registry, root: Path, inspection: dict[str, Any]) -> None:
    capabilities = inspection["capabilities"]
    published = capabilities["published_files"]
    # A repository with no web content is not evidence of a website. Saying a
    # robots.txt is missing would imply there is a site that needs one.
    no_web_content = not capabilities["content"]["present"] and inspection["site_type"] == "Unknown"
    undetermined = "No web content detected in this project. If it is deployed, re-run with --url."

    # -- robots.txt --------------------------------------------------
    check = registry.get("robots.txt")
    check.priority = "P1"
    if published["robots.txt"]:
        path = root / published["robots.txt"][0]
        diagnosis = robots_parser.diagnose(path.read_text(encoding="utf-8", errors="replace"))
        check.local = {
            "files": published["robots.txt"],
            "groups": len(diagnosis["groups"]),
            "sitemaps": diagnosis["sitemaps"],
            "syntax_errors": diagnosis["syntax_errors"],
            "conflicts": diagnosis["conflicts"],
            "blocking_groups": diagnosis["groups_blocking_entire_site"],
        }
        check.data["ai_policy"] = diagnosis["ai_policy"]
        if diagnosis["syntax_errors"]:
            check.status, check.detail = WARNING, "Local robots.txt has syntax errors"
        elif not diagnosis["sitemaps"]:
            check.status, check.detail = WARNING, "Local robots.txt does not reference a sitemap"
        else:
            check.status, check.detail = PASS, "Local robots.txt parses cleanly and references a sitemap"
        check.detail += " (local file only; public reachability unverified)"
    elif no_web_content:
        check.status, check.priority = MANUAL, "P2"
        check.detail = undetermined
    else:
        check.status = FAIL if capabilities["content"]["present"] else WARNING
        check.detail = "No robots.txt found in the repository"
        check.recommendation = "Add robots.txt to the published root with an explicit sitemap reference"

    # -- Sitemap -----------------------------------------------------
    check = registry.get("Sitemap")
    check.priority = "P1"
    if published["sitemap.xml"]:
        path = root / published["sitemap.xml"][0]
        result = sitemap_validator.validate(path.read_bytes(), published["sitemap.xml"][0])
        check.local = {
            "files": published["sitemap.xml"],
            "kind": result["kind"],
            "url_count": result["url_count"],
            "errors": result["errors"],
            "warnings": result["warnings"][:5],
        }
        if result["errors"]:
            check.status, check.detail = FAIL, "Local sitemap invalid: " + result["errors"][0]
        elif result["warnings"]:
            check.status, check.detail = WARNING, "Local sitemap valid with warnings: " + result["warnings"][0]
        else:
            check.status = PASS
            check.detail = "Local sitemap is valid with " + str(result["url_count"]) + " entries"
        check.detail += " (local file only; public reachability unverified)"
    elif no_web_content:
        check.status, check.priority = MANUAL, "P2"
        check.detail = undetermined
    else:
        check.status = FAIL if capabilities["content"]["present"] else WARNING
        check.detail = "No sitemap found in the repository"
        check.recommendation = "Generate a sitemap covering canonical, indexable URLs"

    # -- llms.txt ----------------------------------------------------
    check = registry.get("llms.txt")
    check.priority = "P2"
    if published["llms.txt"]:
        check.status = PASS
        check.detail = "llms.txt present in the repository: " + published["llms.txt"][0]
        check.local = {"files": published["llms.txt"] + published["llms-full.txt"]}
    elif no_web_content:
        check.status, check.priority = MANUAL, "P2"
        check.detail = undetermined
    else:
        check.status = WARNING
        check.detail = "No llms.txt. This is optional and its absence is not a defect"
        check.recommendation = "Consider a curated llms.txt if the site has documentation or authoritative resources"

    # -- Semantic HTML / server-rendered content / AEO ---------------
    documents = [root / rel for rel in inspection["html_documents"]]
    if documents:
        _local_html_checks(registry, root, documents)
    else:
        for name in ("Semantic HTML", "Server-rendered content", "Structured data", "Entity clarity",
                     "Answer extraction", "Citation readiness", "Canonicalization", "Content duplication",
                     "Content availability"):
            check = registry.get(name)
            if capabilities["content"]["present"]:
                check.status = MANUAL
                check.detail = "Content is template-generated; inspect rendered output or supply a live URL"
            elif no_web_content:
                check.status = MANUAL
                check.detail = "No local source supplied; judged from the live origin only"
            else:
                _na(check, "no HTML content in this project")

    # -- Crawlability (AEO view of access) ---------------------------
    check = registry.get("Crawlability")
    check.priority = "P1"
    robots_check = registry.get("robots.txt")
    blocking = (robots_check.local or {}).get("blocking_groups") or []
    critical, blocked_agents = _blocking_severity(blocking)
    if blocking and critical:
        check.status, check.priority = FAIL, "P0"
        check.detail = "robots.txt blocks the entire site for: " + ", ".join(blocked_agents)
    elif blocking:
        check.status, check.priority = PASS, "P3"
        check.detail = (
            "Commercial SEO crawlers are disallowed (" + ", ".join(blocked_agents)
            + "). This is an owner decision and does not affect search engines or AI agents"
        )
    elif robots_check.status == PASS:
        check.status, check.detail = PASS, "No site-wide block declared in the local robots.txt"
    elif no_web_content:
        check.status, check.priority = MANUAL, "P2"
        check.detail = undetermined
    else:
        check.status, check.detail = WARNING, "Crawl policy incomplete or undeclared locally"

    # -- Protocol discovery, local applicability ---------------------
    _local_protocol_checks(registry, capabilities)

    # -- Commerce ----------------------------------------------------
    commerce_protocols.apply_local(registry, capabilities, _na)
    if no_web_content:
        # Applicability came from an empty directory, so say that plainly
        # instead of implying a code inspection that never happened.
        for name in ("x402", "MPP", "UCP", "ACP"):
            check = registry.get(name)
            if check.status == NA:
                check.detail = "Not applicable: no local source supplied and no commerce capability observed live"
                check.applicability = "no local source; live evidence only"

    # -- Checks that need a live origin ------------------------------
    for name, reason in [
        ("HTTP Link headers", "response headers require a live origin"),
        ("DNS-AID", "DNS records are external to the repository and are never modified by this toolkit"),
        ("Actual bot access", "edge and origin behaviour can only be observed against a live origin"),
        ("Web Bot Auth", "signature verification requires live request/response exchange"),
        ("Markdown negotiation", "content negotiation requires a live origin or a running server"),
        ("Homepage availability", "no public URL supplied"),
    ]:
        check = registry.get(name)
        check.status = MANUAL
        check.detail = "Requires a live origin: " + reason
        check.priority = "P2" if name != "Actual bot access" else "P1"

    # -- AI bot rules (declared policy, local) -----------------------
    check = registry.get("AI Bot Rules")
    check.priority = "P1"
    policy = registry.get("robots.txt").data.get("ai_policy")
    if policy:
        explicit = [name for name, entry in policy.items() if entry["explicit_rule"]]
        blocked = [name for name, entry in policy.items() if not entry["homepage_allowed"]]
        check.local = {"explicit_rules_for": explicit, "blocked_on_homepage": blocked}
        check.status = PASS if explicit else WARNING
        check.detail = (
            "Declared policy found for: " + ", ".join(explicit) if explicit
            else "No AI-crawler-specific rules; the wildcard group applies"
        )
        if blocked:
            check.detail += ". Currently disallowed: " + ", ".join(blocked)
        check.recommendation = "Policy is the owner's decision; this audit reports it and never changes it"
    elif no_web_content:
        check.status, check.priority = MANUAL, "P2"
        check.detail = undetermined
    else:
        check.status, check.detail = WARNING, "No robots.txt to derive an AI crawler policy from"

    # -- Content signals ---------------------------------------------
    check = registry.get("Content Signals")
    check.priority = "P2"
    if published["robots.txt"]:
        text = (root / published["robots.txt"][0]).read_text(encoding="utf-8", errors="replace")
        signals = bot_access.content_signals(text)
        check.local = signals
        check.status = PASS if signals["present"] else WARNING
        check.detail = (
            "Content signals declared: " + "; ".join(signals["declared"]) if signals["present"]
            else "No explicit content-usage policy declared"
        )
        check.recommendation = (
            "Absent policy is reported, not assumed. Present the owner with valid options for "
            "search, ai-input and ai-train and let them choose."
        )
    elif no_web_content:
        check.status, check.priority = MANUAL, "P2"
        check.detail = undetermined
    else:
        check.status, check.detail = WARNING, "No robots.txt in which to declare content signals"


def _local_html_checks(registry: Registry, root: Path, documents: list[Path]) -> None:
    analyses, structured, canonicals, titles = [], [], [], {}
    for path in documents:
        try:
            html = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        relative = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name
        analysis = semantic_html.analyse(html)
        analysis["file"] = relative
        analyses.append(analysis)
        result = structured_data.audit(html, relative)
        result["file"] = relative
        structured.append(result)
        canonicals.append((relative, result["citation_readiness"]["canonical"]))
        title = (result["citation_readiness"]["title"] or "").strip().lower()
        if title:
            titles.setdefault(title, []).append(relative)

    documents_count = len(analyses)

    # Semantic HTML
    check = registry.get("Semantic HTML")
    check.priority = "P1"
    issues = [i for a in analyses for i in a["issues"] if i["severity"] in ("P1", "P2")]
    without_main = [a["file"] for a in analyses if not a["landmarks"]["main"]]
    without_h1 = [a["file"] for a in analyses if a["h1_count"] == 0]
    check.local = {
        "documents": documents_count,
        "without_main": without_main[:10],
        "without_h1": without_h1[:10],
        "issue_count": len(issues),
        "sample_issues": [i["issue"] for i in issues[:6]],
    }
    if without_h1:
        check.status = FAIL
        check.detail = str(len(without_h1)) + " of " + str(documents_count) + " documents have no h1"
    elif issues:
        check.status = WARNING
        check.detail = str(len(issues)) + " semantic issues across " + str(documents_count) + " documents"
    else:
        check.status = PASS
        check.detail = "Semantic landmarks and heading structure are sound in " + str(documents_count) + " documents"

    # Server-rendered content
    check = registry.get("Server-rendered content")
    check.priority = "P0"
    js_dependent = [a["file"] for a in analyses if a["javascript_dependent_content"]]
    check.local = {"documents": documents_count, "javascript_dependent": js_dependent[:10]}
    if js_dependent:
        check.status = FAIL
        check.detail = str(len(js_dependent)) + " documents deliver primary content only via JavaScript"
        check.recommendation = "Server-render or pre-render primary content; agents generally do not execute JavaScript"
    else:
        check.status = PASS
        check.detail = "Primary content is present in the served HTML"
        check.priority = "P2"

    # Content availability
    check = registry.get("Content availability")
    check.priority = "P1"
    thin = [s["file"] for s in structured if s["answerability"]["thin_content"]]
    check.local = {"documents": documents_count, "thin_documents": thin[:10]}
    if documents_count and len(thin) == documents_count:
        check.status, check.detail = WARNING, "All inspected documents are thin (<150 words of served text)"
    elif thin:
        check.status, check.detail = WARNING, str(len(thin)) + " documents are thin (<150 words)"
    else:
        check.status, check.detail = PASS, "Inspected documents carry substantive served text"

    # Structured data
    check = registry.get("Structured data")
    check.priority = "P1"
    with_jsonld = [s for s in structured if s["jsonld_blocks"]]
    parse_errors = [s["file"] for s in structured if s["jsonld_parse_errors"]]
    schema_issues = [i for s in structured for i in s["schema_issues"]]
    fabricated = [i for i in schema_issues if i["severity"] == "P1"]
    check.local = {
        "documents_with_jsonld": len(with_jsonld),
        "documents": documents_count,
        "parse_errors": parse_errors,
        "issue_count": len(schema_issues),
        "unsupported_claims": [i["issue"] for i in fabricated[:5]],
    }
    if parse_errors:
        check.status, check.detail = FAIL, "Invalid JSON-LD in: " + ", ".join(parse_errors[:3])
    elif fabricated:
        check.status, check.detail = FAIL, str(len(fabricated)) + " structured claims are not supported by visible text"
    elif not with_jsonld:
        check.status, check.detail = WARNING, "No JSON-LD found in the inspected documents"
        check.recommendation = "Add JSON-LD only for entities that are visible or demonstrably valid"
    elif schema_issues:
        check.status, check.detail = WARNING, str(len(schema_issues)) + " structured-data issues to review"
    else:
        check.status, check.detail = PASS, "JSON-LD parses and matches visible content in " + str(len(with_jsonld)) + " documents"
    check.data["note"] = "JSON validity is not Schema.org correctness; semantic review is still required"

    # Entity clarity
    check = registry.get("Entity clarity")
    check.priority = "P1"
    types: dict[str, int] = {}
    for result in structured:
        for name, count in result["entity_types"].items():
            types[name] = types.get(name, 0) + count
    without_id = sum(s["entities_without_id"] for s in structured)
    check.local = {"entity_types": types, "entities_without_id": without_id}
    if not types:
        check.status, check.detail = WARNING, "No typed entities declared; the site's subject is not machine-identifiable"
    elif "Organization" not in types and "Person" not in types and "LocalBusiness" not in types:
        check.status, check.detail = WARNING, "No publisher entity (Organization, LocalBusiness or Person) declared"
    elif without_id:
        check.status, check.detail = WARNING, str(without_id) + " entities lack a stable @id for cross-page linking"
    else:
        check.status, check.detail = PASS, "Entities are typed and identifiable: " + ", ".join(sorted(types))

    # Canonicalization
    check = registry.get("Canonicalization")
    check.priority = "P1"
    missing = [f for f, canonical in canonicals if not canonical]
    check.local = {"documents": documents_count, "without_canonical": missing[:10]}
    if missing and len(missing) == documents_count:
        check.status, check.detail = FAIL, "No document declares a canonical URL"
    elif missing:
        check.status, check.detail = WARNING, str(len(missing)) + " documents lack a canonical URL"
    else:
        check.status, check.detail = PASS, "All inspected documents declare a canonical URL"

    # Answer extraction
    check = registry.get("Answer extraction")
    check.priority = "P1"
    no_description = [s["file"] for s in structured if not s["answerability"]["has_meta_description"]]
    faq_documents = sum(1 for s in structured if s["answerability"]["faq_entities"])
    outline_problems = [a["file"] for a in analyses if a["skipped_levels"] or a["empty_headings"]]
    check.local = {
        "documents_without_meta_description": no_description[:10],
        "documents_with_faq": faq_documents,
        "documents_with_outline_problems": outline_problems[:10],
    }
    problems = len(no_description) + len(outline_problems)
    if documents_count and problems >= documents_count:
        check.status, check.detail = WARNING, "Summaries and heading outlines are weak across the inspected documents"
    elif problems:
        check.status, check.detail = WARNING, str(problems) + " documents have weak summaries or heading outlines"
    else:
        check.status, check.detail = PASS, "Documents expose descriptive summaries and a coherent outline"

    # Citation readiness
    check = registry.get("Citation readiness")
    check.priority = "P1"
    ready = [s["file"] for s in structured if s["citation_readiness"]["ready"]]
    check.local = {"citable_documents": len(ready), "documents": documents_count}
    if not ready:
        check.status, check.detail = WARNING, "No document carries canonical, title and date together for attribution"
    elif len(ready) < documents_count:
        check.status, check.detail = WARNING, str(len(ready)) + " of " + str(documents_count) + " documents are attributable"
    else:
        check.status, check.detail = PASS, "Inspected documents carry the signals needed to cite them"

    # Content duplication
    check = registry.get("Content duplication")
    check.priority = "P2"
    duplicates = {title: files for title, files in titles.items() if len(files) > 1}
    check.local = {"duplicate_titles": {k: v for k, v in list(duplicates.items())[:5]}}
    if duplicates:
        check.status = WARNING
        check.detail = str(len(duplicates)) + " titles are shared by multiple pages, which splits the same answer"
        check.recommendation = "Differentiate or consolidate. Never rewrite content without explicit authorization"
    else:
        check.status, check.detail = PASS, "No competing duplicate titles detected in the inspected documents"


def _local_protocol_checks(registry: Registry, capabilities: dict[str, Any]) -> None:
    api = capabilities["api"]
    auth = capabilities["auth"]
    mcp = capabilities["mcp"]
    agent = capabilities["agent_service"]
    well_known = capabilities["published_files"]["well_known"]

    def local_file(fragment: str) -> list[str]:
        return [w for w in well_known if fragment in w.lower()]

    # API Catalog
    check = registry.get("API Catalog")
    if not api["present"]:
        _na(check, "no API surface detected in this project")
    else:
        found = local_file("api-catalog")
        check.priority = "P2"
        check.local = {"api_evidence": api["evidence"][:5], "catalog_files": found}
        check.status = PASS if found else WARNING
        check.detail = (
            "API catalog file present in the repository" if found
            else "An API exists but no /.well-known/api-catalog is published (RFC 9727)"
        )

    # OAuth
    for name, fragment, source in [
        ("OAuth discovery", "oauth-authorization-server", "RFC 8414"),
        ("OAuth Protected Resource", "oauth-protected-resource", "RFC 9728"),
    ]:
        check = registry.get(name)
        if not auth["present"] or not auth["code_confirmed"]:
            _na(check, "no OAuth implementation detected; publishing discovery metadata would be a false signal")
        else:
            found = local_file(fragment)
            check.priority = "P2"
            check.local = {"auth_evidence": auth["evidence"][:5], "files": found}
            check.status = PASS if found else WARNING
            check.detail = (
                "Metadata document present in the repository" if found
                else "OAuth detected but no " + fragment + " metadata is published (" + source + ")"
            )

    # Auth.md
    check = registry.get("Auth.md")
    if not auth["present"]:
        _na(check, "no authentication surface detected")
    else:
        check.status = MANUAL
        check.priority = "P3"
        check.detail = "Auth.md is an emerging convention; verify the current specification before publishing"

    # MCP
    check = registry.get("MCP Server Card")
    if not mcp["present"]:
        _na(check, "this project does not implement an MCP server")
    else:
        check.status = MANUAL
        check.priority = "P3"
        check.local = {"evidence": mcp["evidence"][:5]}
        check.detail = "MCP implementation detected; verify the current Server Card specification before publishing"

    # A2A
    check = registry.get("A2A Agent Card")
    if not agent["present"]:
        _na(check, "this project does not expose an agent service")
    else:
        check.status = MANUAL
        check.priority = "P3"
        check.local = {"evidence": agent["evidence"][:5]}
        check.detail = "Agent artifacts detected; verify the current A2A Agent Card specification before publishing"

    # Agent Skills
    check = registry.get("Agent Skills")
    index_files = local_file("agent-skills")
    if index_files:
        check.priority = "P1"
        check.local = {"files": index_files}
        check.status = MANUAL
        check.detail = (
            "An Agent Skills index is published here. Verify every artifact it references resolves "
            "and that the site really offers those capabilities"
        )
    else:
        _na(check, "no agent-executable capabilities are offered by this site")

    # WebMCP
    check = registry.get("WebMCP")
    _na(check, "no in-page agent tools are implemented")

    # ARD
    check = registry.get("ARD Manifest")
    _na(check, "ARD applicability not established; the specification must be verified before any implementation")
    check.status = NA
    check.detail = "Not applicable: ARD is pre-1.0 and no ARD capability was detected"


# --------------------------------------------------------------------------
# Live layer
# --------------------------------------------------------------------------

def run_live(registry: Registry, base_url: str, inspection: dict[str, Any]) -> None:
    """Overwrite local conclusions with what a real agent receives."""
    origin = base_url if base_url.endswith("/") else base_url + "/"
    home = http_inspect.inspect(origin)

    check = registry.get("Homepage availability")
    check.priority = "P0"
    check.live = {"status": home["status"], "redirects": home["redirects"], "final_url": home["final_url"], "error": home["error"]}
    if home["status"] and 200 <= home["status"] < 300:
        check.status = PASS
        check.detail = "HTTP " + str(home["status"]) + " after " + str(len(home["redirects"])) + " redirect(s)"
    else:
        tls_problem = bool(home["error"]) and "CERTIFICATE_VERIFY_FAILED" in home["error"]
        if tls_problem:
            # The auditing machine could not validate the chain. That is an
            # environment condition, not evidence that the site is unreachable.
            check.status = MANUAL
            check.detail = (
                "TLS certificate verification failed on this machine, so the origin could not be "
                "audited. Fix the local trust store, or re-run with --insecure for diagnostics only. "
                "Underlying error: " + (home["error"] or "")
            )
            check.recommendation = "Confirm the certificate chain independently before treating this as a site defect"
        else:
            check.status = FAIL
            check.detail = "Homepage not retrievable: HTTP " + str(home["status"]) + " " + (home["error"] or "")
        # Nothing downstream can be trusted; stop before producing misleading results.
        reason = "TLS verification failed on the auditing machine" if tls_problem else "homepage unavailable"
        for name in ("robots.txt", "Sitemap", "HTTP Link headers", "Actual bot access", "Markdown negotiation",
                     "llms.txt", "DNS-AID", "Web Bot Auth", "Content Signals", "AI Bot Rules"):
            other = registry.get(name)
            other.live = {"skipped": reason}
            if other.status == MANUAL:
                other.detail = "Live evaluation skipped: " + reason
        return

    # -- robots.txt --------------------------------------------------
    robots_response = fetch(urljoin(origin, "/robots.txt"), accept="text/plain")
    check = registry.get("robots.txt")
    check.priority = "P1"
    robots_text = robots_response.text if robots_response.ok else None
    if robots_response.ok and "html" in robots_response.header("Content-Type").lower():
        check.status = FAIL
        check.detail = "/robots.txt returns HTML, not a robots file (catch-all route)"
        check.live = {"status": robots_response.status, "content_type": robots_response.header("Content-Type")}
        robots_text = None
    elif robots_response.ok:
        diagnosis = robots_parser.diagnose(robots_text)
        check.data["ai_policy"] = diagnosis["ai_policy"]
        check.live = {
            "status": robots_response.status,
            "content_type": robots_response.header("Content-Type"),
            "groups": len(diagnosis["groups"]),
            "sitemaps": diagnosis["sitemaps"],
            "syntax_errors": diagnosis["syntax_errors"],
            "conflicts": diagnosis["conflicts"],
            "blocking_groups": diagnosis["groups_blocking_entire_site"],
        }
        if diagnosis["syntax_errors"]:
            check.status, check.detail = WARNING, "Served robots.txt has " + str(len(diagnosis["syntax_errors"])) + " syntax errors"
        elif not diagnosis["sitemaps"]:
            check.status, check.detail = WARNING, "Served robots.txt does not reference a sitemap"
        else:
            check.status, check.detail = PASS, "Served robots.txt is valid and references " + str(len(diagnosis["sitemaps"])) + " sitemap(s)"
    else:
        check.status = FAIL
        check.detail = "/robots.txt not served: HTTP " + str(robots_response.status) + " " + (robots_response.error or "")
        check.live = {"status": robots_response.status, "error": robots_response.error}

    # -- Crawlability (live) -----------------------------------------
    crawl = registry.get("Crawlability")
    blocking = (check.live or {}).get("blocking_groups") or []
    critical, blocked_agents = _blocking_severity(blocking)
    if blocking and critical:
        crawl.status, crawl.priority = FAIL, "P0"
        crawl.detail = "Served robots.txt blocks the entire site for: " + ", ".join(blocked_agents)
        crawl.live = {"blocking_groups": blocking, "critical": True}
    elif blocking:
        crawl.status, crawl.priority = PASS, "P3"
        crawl.detail = (
            "Commercial SEO crawlers are disallowed (" + ", ".join(blocked_agents)
            + "). Search engines and AI agents are unaffected"
        )
        crawl.live = {"blocking_groups": blocking, "critical": False}
    elif robots_text:
        allowed = robots_parser.is_allowed(robots_parser.parse(robots_text), "Googlebot", "/")["allowed"]
        crawl.status = PASS if allowed else FAIL
        crawl.detail = "Homepage crawlable by general crawlers" if allowed else "Homepage disallowed for general crawlers"
        crawl.live = {"homepage_allowed": allowed}
    else:
        # RFC 9309: an unavailable robots.txt means unrestricted crawling. The
        # local file is irrelevant here because it is demonstrably not served.
        crawl.status = PASS
        crawl.detail = "No robots.txt is served, so crawling is unrestricted by default (RFC 9309)"
        crawl.live = {"robots_served": False, "homepage_allowed": True}

    if home.get("x_robots_tag"):
        crawl.data["x_robots_tag"] = home["x_robots_tag"]
        if "noindex" in home["x_robots_tag"].lower():
            crawl.status, crawl.priority = FAIL, "P0"
            crawl.detail = "X-Robots-Tag declares noindex: " + home["x_robots_tag"]
    meta_robots = (home.get("html") or {}).get("meta_robots") or []
    if any("noindex" in m.lower() for m in meta_robots):
        crawl.status, crawl.priority = FAIL, "P0"
        crawl.detail = "Meta robots declares noindex: " + "; ".join(meta_robots)

    # -- Sitemap -----------------------------------------------------
    check = registry.get("Sitemap")
    check.priority = "P1"
    declared = (registry.get("robots.txt").live or {}).get("sitemaps") or []
    candidates = declared + [urljoin(origin, "/sitemap.xml"), urljoin(origin, "/sitemap_index.xml")]
    sitemap_result = None
    for candidate in candidates:
        response = fetch(candidate, accept="application/xml,text/xml")
        if response.ok and response.body and "html" not in response.header("Content-Type").lower():
            sitemap_result = sitemap_validator.validate(response.body, candidate, origin)
            sitemap_result["url"] = candidate
            sitemap_result["referenced_in_robots"] = candidate in declared
            break
    if sitemap_result is None:
        check.status = FAIL
        check.detail = "No sitemap retrievable at " + ", ".join(candidates[:3])
        check.live = {"tried": candidates[:3]}
    else:
        sample = []
        if sitemap_result["kind"] == "urlset" and sitemap_result["urls"]:
            sample = sitemap_validator.check_urls_live([u["loc"] for u in sitemap_result["urls"]], 10)
        broken = [s for s in sample if s["status"] is None or s["status"] >= 400]
        redirecting = [s for s in sample if s["redirects"]]
        check.live = {
            "url": sitemap_result["url"],
            "kind": sitemap_result["kind"],
            "url_count": sitemap_result["url_count"],
            "errors": sitemap_result["errors"],
            "warnings": sitemap_result["warnings"][:5],
            "referenced_in_robots": sitemap_result["referenced_in_robots"],
            "sampled": len(sample),
            "broken_urls": [b["url"] for b in broken][:5],
            "redirecting_urls": [r["url"] for r in redirecting][:5],
        }
        if sitemap_result["errors"]:
            check.status, check.detail = FAIL, "Sitemap invalid: " + sitemap_result["errors"][0]
        elif broken:
            check.status, check.detail = FAIL, str(len(broken)) + " of " + str(len(sample)) + " sampled sitemap URLs do not return 2xx"
        elif redirecting or not sitemap_result["referenced_in_robots"] or sitemap_result["warnings"]:
            reasons = []
            if redirecting:
                reasons.append(str(len(redirecting)) + " sampled URLs redirect")
            if not sitemap_result["referenced_in_robots"]:
                reasons.append("not referenced from robots.txt")
            if sitemap_result["warnings"]:
                reasons.append(sitemap_result["warnings"][0])
            check.status, check.detail = WARNING, "Sitemap served with issues: " + "; ".join(reasons)
        else:
            check.status = PASS
            check.detail = "Sitemap valid, referenced from robots.txt, " + str(sitemap_result["url_count"]) + " URLs, sample all 2xx"

    # -- HTTP Link headers -------------------------------------------
    check = registry.get("HTTP Link headers")
    check.priority = "P2"
    links = home["link_headers"]
    check.live = {"link_headers": links, "count": len(links)}
    if links:
        check.status = PASS
        check.detail = "Link header advertises: " + ", ".join(sorted({l["rel"] or "?" for l in links}))
    else:
        check.status = WARNING
        check.detail = "No Link header. Only add relations that point at resources which actually exist"

    # -- Markdown negotiation ----------------------------------------
    check = registry.get("Markdown negotiation")
    check.priority = "P2"
    negotiation = markdown_negotiation.compare(origin)
    check.live = {
        "status_code": negotiation["markdown"]["status"],
        "content_type": negotiation["markdown"]["content_type"],
        "identical_bodies": negotiation["identical_bodies"],
        "byte_reduction_percent": negotiation["byte_reduction_percent"],
        "vary_includes_accept": negotiation["vary_includes_accept"],
        "structural_markdown": negotiation["markdown"].get("structural_markdown"),
    }
    check.status = negotiation["status"]
    check.detail = negotiation["detail"]
    if check.status != PASS:
        check.recommendation = "Optional efficiency feature. Implement only if the stack supports negotiation without breaking HTML"

    # -- Bot access --------------------------------------------------
    check = registry.get("Actual bot access")
    check.priority = "P0"
    probe = bot_access.probe(origin, robots_text)
    contradictions = probe["contradictions"]
    check.live = {
        "browser_baseline": probe["browser_baseline"],
        "agents": [{k: a[k] for k in ("agent", "status", "verdict", "challenge_marker")} for a in probe["agents"]],
    }
    if contradictions:
        check.status = FAIL
        check.detail = str(len(contradictions)) + " agents are allowed by robots.txt but blocked or challenged in practice: " + ", ".join(c["agent"] for c in contradictions)
        check.recommendation = "Investigate CDN/WAF rules. This toolkit never modifies edge configuration"
    else:
        served = [a["agent"] for a in probe["agents"] if a["actually_served"]]
        check.status = PASS
        check.detail = "Declared and actual access agree. Content served to: " + (", ".join(served) or "none")
        check.priority = "P2"

    # -- AI bot rules (live) -----------------------------------------
    check = registry.get("AI Bot Rules")
    policy = registry.get("robots.txt").data.get("ai_policy")
    if policy:
        explicit = [name for name, entry in policy.items() if entry["explicit_rule"]]
        blocked = [name for name, entry in policy.items() if not entry["homepage_allowed"]]
        check.live = {"explicit_rules_for": explicit, "blocked_on_homepage": blocked}
        check.status = PASS if explicit else WARNING
        check.detail = (
            "Served policy declares rules for: " + ", ".join(explicit) if explicit
            else "No AI-crawler-specific rules are served; the wildcard group applies"
        )
        if blocked:
            check.detail += ". Currently disallowed: " + ", ".join(blocked)

    # -- Content signals (live) --------------------------------------
    if robots_text:
        check = registry.get("Content Signals")
        signals = bot_access.content_signals(robots_text)
        check.live = signals
        check.status = PASS if signals["present"] else WARNING
        check.detail = (
            "Content signals served: " + "; ".join(signals["declared"]) if signals["present"]
            else "No content-usage policy is served. Absence is reported, never assumed"
        )

    # -- llms.txt ----------------------------------------------------
    check = registry.get("llms.txt")
    response = fetch(urljoin(origin, "/llms.txt"), accept="text/plain")
    served_type = response.header("Content-Type").split(";")[0].lower()
    if response.ok and served_type in ("text/plain", "text/markdown") and response.body:
        check.status, check.detail = PASS, "llms.txt served as " + served_type
        check.live = {"status": response.status, "content_type": served_type, "bytes": len(response.body)}
    elif response.ok and "html" in served_type:
        check.status, check.detail = WARNING, "/llms.txt returns HTML from a catch-all route rather than a real file"
        check.live = {"status": response.status, "content_type": served_type}
    else:
        check.status, check.detail = WARNING, "No llms.txt served. This is optional; absence is not a defect"
        check.live = {"status": response.status}

    # -- Live protocol discovery -------------------------------------
    home_page = fetch(origin)
    api_evidence = detect_live_api_surface(home_page.text if home_page.ok else "", robots_text)
    _live_protocol_checks(registry, origin, inspection, api_evidence)

    # -- Live HTML analysis ------------------------------------------
    _live_html_checks(registry, home, origin)

    # -- DNS-AID / Web Bot Auth --------------------------------------
    check = registry.get("DNS-AID")
    check.priority = "P3"
    check.status = MANUAL
    check.detail = (
        "DNS-AID requires a DNS record this toolkit never creates. Verify the current specification, "
        "then hand the record name, value and verification procedure to the DNS owner"
    )
    check.recommendation = "Diagnostics only. See references/dns-aid.md for the reporting template"

    check = registry.get("Web Bot Auth")
    check.priority = "P3"
    signature_headers = [k for k in home["headers"] if k.lower() in ("signature", "signature-input", "signature-agent")]
    check.live = {"signature_headers": signature_headers}
    check.status = MANUAL
    check.detail = (
        "No verified signature exchange observed. Web Bot Auth is a property of the requesting agent and "
        "the origin's verification policy; never fabricate cryptographic material"
    )


API_PATH_IN_PAGE = re.compile(r"/api/[A-Za-z0-9_\-/]{2,}")


def detect_live_api_surface(html: str, robots_text: str | None) -> list[str]:
    """An endpoint the served page calls is API surface, even with no local source.

    Without this, a live-only audit would report "no API surface detected" for a
    site whose own homepage calls /api/... — a false reason for an N/A verdict.
    """
    evidence: list[str] = []
    for match in API_PATH_IN_PAGE.findall(html or ""):
        item = "page calls " + match
        if item not in evidence:
            evidence.append(item)
    for line in (robots_text or "").splitlines():
        directive = line.split("#", 1)[0].strip()
        lowered = directive.lower()
        if lowered.startswith(("disallow:", "allow:")) and "/api" in lowered:
            evidence.append("robots.txt declares an API path: " + directive)
    return evidence[:8]


def _live_protocol_checks(registry: Registry, origin: str, inspection: dict[str, Any],
                          live_api_evidence: list[str] | None = None) -> None:
    capabilities = inspection["capabilities"]
    if live_api_evidence:
        # Live evidence supersedes an absent local source for applicability.
        capabilities = {**capabilities, "api": {"present": True, "evidence": live_api_evidence}}
    scan = discovery_scan.scan(origin)
    by_path = {r["path"]: r for r in scan["results"]}

    def gate(name: str, capability_key: str, reason: str, paths: list[str], spec_note: str = "") -> None:
        check = registry.get(name)
        present = [by_path[p] for p in paths if p in by_path and by_path[p]["present"]]
        capability = capabilities.get(capability_key, {}).get("present", False)
        if present:
            # A published endpoint is always audited, even if the local scan
            # found no capability: it is already a public claim.
            entry = present[0]
            check.live = {"path": entry["path"], "status": entry["status"], "content_type": entry["content_type"], "json_valid": entry.get("json_valid")}
            if entry.get("json_valid") is False:
                check.status, check.detail = FAIL, "Published at " + entry["path"] + " but the JSON is invalid"
            else:
                check.status, check.detail = PASS, "Published and served at " + entry["path"]
            check.priority = "P2"
            return
        if not capability:
            _na(check, reason)
            return
        check.priority = "P2"
        check.live = {"probed": paths, "present": False}
        if spec_note:
            check.status, check.detail = MANUAL, spec_note
        else:
            check.status = WARNING
            check.detail = "Capability exists but nothing is published at " + ", ".join(paths)

    gate("API Catalog", "api", "no API surface detected", ["/.well-known/api-catalog", "/openapi.json"])
    gate("OAuth discovery", "auth", "no OAuth implementation detected; publishing discovery metadata would be a false signal",
         ["/.well-known/oauth-authorization-server", "/.well-known/openid-configuration"])
    gate("OAuth Protected Resource", "auth", "no OAuth-protected resource detected",
         ["/.well-known/oauth-protected-resource"])
    gate("Auth.md", "auth", "no authentication surface detected", ["/auth.md"],
         "Auth.md is an emerging convention; verify the current specification before publishing")
    gate("MCP Server Card", "mcp", "this site does not expose an MCP server", ["/.well-known/mcp.json"],
         "MCP detected; verify the current Server Card specification and path before publishing")
    gate("A2A Agent Card", "agent_service", "this site does not expose an agent service", ["/.well-known/agent-card.json"],
         "Agent service detected; verify the current A2A Agent Card specification before publishing")

    # Agent Skills needs artifact-level verification, not just a 200.
    check = registry.get("Agent Skills")
    entry = by_path.get("/.well-known/agent-skills/index.json")
    if entry and entry["present"]:
        check.priority = "P1"
        check.live = {"status": entry["status"], "json_valid": entry.get("json_valid")}
        if entry.get("json_valid") is False:
            check.status, check.detail = FAIL, "Agent Skills index is served but is not valid JSON"
        else:
            broken = _verify_agent_skill_artifacts(origin, entry.get("json") or {})
            check.live["broken_artifacts"] = broken
            if broken:
                check.status = FAIL
                check.detail = str(len(broken)) + " skill artifacts referenced by the index do not resolve"
                check.recommendation = "Remove the index or publish the artifacts. A broken index is a false capability signal"
            else:
                check.status, check.detail = PASS, "Agent Skills index served and all referenced artifacts resolve"
    else:
        _na(check, "no agent-executable capabilities are offered by this site")

    check = registry.get("WebMCP")
    _na(check, "no in-page agent tools detected")

    check = registry.get("ARD Manifest")
    ard = by_path.get("/.well-known/ard.json")
    if ard and ard["present"]:
        check.status, check.priority = MANUAL, "P3"
        check.detail = "An ARD manifest is published; verify it against the current specification"
        check.live = {"status": ard["status"]}
    else:
        _na(check, "ARD is pre-1.0 and no ARD capability was detected")


def _verify_agent_skill_artifacts(origin: str, index: dict[str, Any]) -> list[str]:
    """A published index must point at artifacts that actually resolve."""
    entries = index.get("skills") or index.get("artifacts") or []
    broken = []
    for entry in entries if isinstance(entries, list) else []:
        url = entry.get("url") or entry.get("href") if isinstance(entry, dict) else None
        if not url:
            continue
        response = fetch(urljoin(origin, url), accept="text/markdown,*/*")
        if not response.ok or not response.body:
            broken.append(url)
    return broken


def _live_html_checks(registry: Registry, home: dict[str, Any], origin: str) -> None:
    response = fetch(origin)
    if not response.ok or not response.body:
        return
    html = response.text
    analysis = semantic_html.analyse(html)
    structured = structured_data.audit(html, origin)

    check = registry.get("Semantic HTML")
    check.priority = "P1"
    check.live = {
        "landmarks": analysis["landmarks"],
        "h1_count": analysis["h1_count"],
        "issues": [i["issue"] for i in analysis["issues"]][:6],
        "text_to_markup_ratio": analysis["text_to_markup_ratio"],
    }
    blocking = [i for i in analysis["issues"] if i["severity"] in ("P0", "P1")]
    if blocking:
        check.status, check.detail = FAIL, "Served homepage: " + blocking[0]["issue"]
    elif analysis["issues"]:
        check.status, check.detail = WARNING, str(len(analysis["issues"])) + " semantic issues in the served homepage"
    else:
        check.status, check.detail = PASS, "Served homepage uses landmarks and a coherent heading structure"

    check = registry.get("Server-rendered content")
    check.live = {
        "served_text_chars": analysis["served_text_chars"],
        "executable_scripts": analysis["executable_scripts"],
        "javascript_dependent": analysis["javascript_dependent_content"],
    }
    if analysis["javascript_dependent_content"]:
        check.status, check.priority = FAIL, "P0"
        check.detail = "Served homepage has " + str(analysis["served_text_chars"]) + " characters of text; primary content requires JavaScript"
        check.recommendation = "Server-render or pre-render primary content"
    else:
        check.status, check.priority = PASS, "P2"
        check.detail = "Homepage delivers " + str(analysis["served_text_chars"]) + " characters of text without JavaScript"

    check = registry.get("Content availability")
    check.priority = "P1"
    check.live = {"word_count": structured["answerability"]["word_count"]}
    if structured["answerability"]["thin_content"]:
        check.status, check.detail = WARNING, "Served homepage carries only " + str(structured["answerability"]["word_count"]) + " words"
    else:
        check.status, check.detail = PASS, "Served homepage carries " + str(structured["answerability"]["word_count"]) + " words of extractable text"

    check = registry.get("Structured data")
    check.priority = "P1"
    fabricated = [i for i in structured["schema_issues"] if i["severity"] == "P1"]
    check.live = {
        "jsonld_blocks": structured["jsonld_blocks"],
        "parse_errors": len(structured["jsonld_parse_errors"]),
        "issues": [i["issue"] for i in structured["schema_issues"]][:6],
    }
    if structured["jsonld_parse_errors"]:
        check.status, check.detail = FAIL, "Served JSON-LD does not parse"
    elif fabricated:
        check.status, check.detail = FAIL, str(len(fabricated)) + " served structured claims are unsupported by visible text"
    elif not structured["jsonld_blocks"]:
        check.status, check.detail = WARNING, "No JSON-LD served on the homepage"
    elif structured["schema_issues"]:
        check.status, check.detail = WARNING, str(len(structured["schema_issues"])) + " structured-data issues on the served homepage"
    else:
        check.status, check.detail = PASS, "Served JSON-LD parses and matches visible content"

    check = registry.get("Entity clarity")
    check.priority = "P1"
    check.live = {"entity_types": structured["entity_types"], "entities_without_id": structured["entities_without_id"]}
    types = structured["entity_types"]
    without_id = structured["entities_without_id"]
    duplicated = [name for name, count in types.items() if count > 1 and name in ("Organization", "LocalBusiness", "Person")]
    if not types:
        check.status, check.detail = WARNING, "Homepage declares no typed entity"
    elif not {"Organization", "LocalBusiness", "Person", "WebSite"} & set(types):
        check.status, check.detail = WARNING, "Homepage declares no publisher entity"
    elif duplicated and without_id:
        # Ambiguity needs BOTH conditions: several entities of the same type AND
        # missing @id. Several organizations that each carry a stable @id are
        # correctly distinguished — a site and its agency, for instance.
        check.status = WARNING
        check.detail = (
            "Multiple " + "/".join(duplicated) + " entities are declared and "
            + str(without_id) + " carry no @id, so the publishing entity is ambiguous"
        )
    elif without_id:
        check.status = WARNING
        check.detail = str(without_id) + " entities lack a stable @id for cross-page linking"
    else:
        check.status, check.detail = PASS, "Homepage entities: " + ", ".join(sorted(types))

    check = registry.get("Canonicalization")
    check.priority = "P1"
    canonical = structured["citation_readiness"]["canonical"]
    check.live = {"canonical": canonical, "final_url": home["final_url"], "redirects": len(home["redirects"])}
    if not canonical:
        check.status, check.detail = FAIL, "Homepage declares no canonical URL"
    elif urlsplit(urljoin(origin, canonical)).netloc != urlsplit(origin).netloc:
        check.status, check.detail = FAIL, "Canonical points to a different host: " + canonical
    else:
        check.status, check.detail = PASS, "Canonical declared: " + canonical

    check = registry.get("Citation readiness")
    check.priority = "P1"
    citation = structured["citation_readiness"]
    check.live = {k: v for k, v in citation.items() if k != "signals_present"}
    if citation["ready"]:
        check.status = PASS
        check.detail = (
            "Homepage carries the signals needed to attribute it"
            + (" (dated content with a date)" if citation.get("is_dated_content") else "")
        )
    else:
        required = ["canonical", "title"] + (["date_published"] if citation.get("is_dated_content") else [])
        missing = [k for k in required if not citation.get(k)]
        check.status, check.detail = WARNING, "Attribution signals missing on the homepage: " + ", ".join(missing)

    check = registry.get("Answer extraction")
    check.priority = "P1"
    check.live = {
        "has_meta_description": structured["answerability"]["has_meta_description"],
        "heading_count": analysis["heading_count"],
        "skipped_levels": len(analysis["skipped_levels"]),
        "faq_entities": structured["answerability"]["faq_entities"],
    }
    problems = []
    if not structured["answerability"]["has_meta_description"]:
        problems.append("no meta description")
    if analysis["skipped_levels"]:
        problems.append("heading levels skip")
    if analysis["heading_count"] < 2:
        problems.append("almost no heading structure")
    if problems:
        check.status, check.detail = WARNING, "Homepage answer extraction weakened by: " + ", ".join(problems)
    else:
        check.status, check.detail = PASS, "Homepage exposes a summary and a coherent heading outline"


def findings(registry: Registry) -> list[dict[str, Any]]:
    result = []
    for check in registry.all():
        priority = scoring.priority_of(check.to_dict())
        if priority is None:
            continue
        result.append(
            {
                "priority": priority,
                "check": check.name,
                "section": check.section,
                "status": check.status,
                "detail": check.detail,
                "recommendation": check.recommendation,
                "score": check.score,
            }
        )
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return sorted(result, key=lambda f: (order.get(f["priority"], 9), f["check"]))
