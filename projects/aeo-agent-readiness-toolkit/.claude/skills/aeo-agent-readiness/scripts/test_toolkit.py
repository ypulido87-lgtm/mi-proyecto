#!/usr/bin/env python3
"""Offline test suite for the AEO toolkit.

No test touches the network. Every test asserts a behaviour the toolkit's rules
depend on: correct parsing, honest applicability, and scores that cannot be
inflated by N/A or MANUAL REVIEW.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from aeolib import scoring  # noqa: E402
from aeolib.paths import load_skill_script  # noqa: E402
from aeolib.project import AUTH_CODE_MARKERS, COMMERCE_CODE_MARKERS, classify_site, inspect  # noqa: E402

robots_parser = load_skill_script("aeo-discoverability", "robots_parser.py")
sitemap_validator = load_skill_script("aeo-discoverability", "sitemap_validator.py")
semantic_html = load_skill_script("aeo-content-accessibility", "semantic_html.py")
markdown_negotiation = load_skill_script("aeo-content-accessibility", "markdown_negotiation.py")
structured_data = load_skill_script("aeo-answerability", "structured_data.py")
commerce_protocols = load_skill_script("aeo-commerce-readiness", "commerce_protocols.py")
llms_txt = load_skill_script("aeo-llms", "llms_txt.py")
bot_access = load_skill_script("aeo-bot-access", "bot_access.py")
http_inspect = load_skill_script("aeo-discoverability", "http_inspect.py")
skills_index = load_skill_script("aeo-protocol-discovery", "generate_agent_skills_index.py")

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(condition), detail))


# ---------------------------------------------------------------- robots.txt
def test_robots() -> None:
    text = (
        "Sitemap: https://x.test/s.xml\n"
        "# comment\n"
        "User-agent: *\n"
        "Disallow: /admin/\n"
        "Allow: /admin/public\n"
        "\n"
        "User-agent: GPTBot\n"
        "User-agent: CCBot\n"
        "Disallow: /\n"
    )
    result = robots_parser.diagnose(text)
    check("robots: global Sitemap before any group is captured", result["sitemaps"] == ["https://x.test/s.xml"])
    check("robots: consecutive User-agent lines share one group", len(result["groups"]) == 2)
    check("robots: site-wide block detected", result["groups_blocking_entire_site"] == [["GPTBot", "CCBot"]])

    robots = robots_parser.parse(text)
    check("robots: longest-match Disallow wins", robots_parser.is_allowed(robots, "Googlebot", "/admin/secret")["allowed"] is False)
    check("robots: more specific Allow overrides", robots_parser.is_allowed(robots, "Googlebot", "/admin/public/x")["allowed"] is True)
    check("robots: specific group beats wildcard", robots_parser.is_allowed(robots, "GPTBot", "/blog")["allowed"] is False)
    check("robots: unmatched path defaults to allow", robots_parser.is_allowed(robots, "Googlebot", "/blog")["allowed"] is True)

    conflict = robots_parser.diagnose("User-agent: *\nAllow: /a\nDisallow: /a\n")
    check("robots: conflicting directives on one path are flagged", len(conflict["conflicts"]) == 1)
    broken = robots_parser.diagnose("User-agent *\nDisallow: /x\n")
    check("robots: missing colon reported as a syntax error",
          any("colon" in e["reason"] for e in broken["syntax_errors"]))
    check("robots: rule before any group is an error", len(robots_parser.diagnose("Disallow: /x\n")["syntax_errors"]) == 1)
    check("robots: wildcard pattern matches", robots_parser.is_allowed(robots_parser.parse("User-agent: *\nDisallow: /*.pdf$\n"), "X", "/a/b.pdf")["allowed"] is False)


# ------------------------------------------------------------------ sitemaps
def test_sitemap() -> None:
    valid = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://x.test/</loc><lastmod>2026-01-01</lastmod></url>
<url><loc>https://x.test/a</loc></url>
</urlset>"""
    result = sitemap_validator.validate(valid, "test", "https://x.test/")
    check("sitemap: valid document parses", result["valid_xml"] and not result["errors"], str(result["errors"]))
    check("sitemap: URLs counted", result["url_count"] == 2)
    check("sitemap: namespace verified", result["namespace_ok"])

    broken = sitemap_validator.validate(b"<urlset><url>", "test")
    check("sitemap: malformed XML rejected", not broken["valid_xml"] and broken["errors"])

    wrong_ns = sitemap_validator.validate(b'<urlset xmlns="http://example.com/x"><url><loc>https://x.test/</loc></url></urlset>', "t")
    check("sitemap: wrong namespace rejected", not wrong_ns["namespace_ok"])

    duplicates = sitemap_validator.validate(
        b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        b"<url><loc>https://x.test/a</loc></url><url><loc>https://x.test/a</loc></url></urlset>", "t")
    check("sitemap: duplicate URLs reported", any("Duplicate" in e for e in duplicates["errors"]))

    relative = sitemap_validator.validate(
        b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>/relative</loc></url></urlset>', "t")
    check("sitemap: non-absolute URL reported", any("Non-absolute" in e for e in relative["errors"]))

    bad_date = sitemap_validator.validate(
        b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        b"<url><loc>https://x.test/</loc><lastmod>01-2026</lastmod></url></urlset>", "t")
    check("sitemap: invalid lastmod detected", bad_date["lastmod_invalid"] == ["01-2026"])

    index = sitemap_validator.validate(
        b'<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        b"<sitemap><loc>https://x.test/s1.xml</loc></sitemap></sitemapindex>", "t")
    check("sitemap: sitemap index recognised", index["kind"] == "sitemapindex" and index["url_count"] == 1)

    empty = sitemap_validator.validate(b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>', "t")
    check("sitemap: empty sitemap reported", any("no entries" in e for e in empty["errors"]))


# -------------------------------------------------------------- semantic HTML
def test_semantic_html() -> None:
    good = (
        '<!doctype html><html lang="en"><head><title>T</title></head><body>'
        "<header><nav><a href='/'>Home</a></nav></header><main><article><h1>Title</h1><h2>Sub</h2>"
        "<p>" + ("Real served content. " * 40) + "</p></article></main><footer>f</footer></body></html>"
    )
    result = semantic_html.analyse(good)
    check("semantic: landmarks detected", result["landmarks"]["main"] == 1 and result["landmarks"]["nav"] == 1)
    check("semantic: single h1 accepted", result["h1_count"] == 1)
    check("semantic: content-rich page is not JS-dependent", result["javascript_dependent_content"] is False)

    shell = '<!doctype html><html><body><div id="root"></div><script src="/a.js"></script></body></html>'
    check("semantic: SPA shell flagged as JS-dependent", semantic_html.analyse(shell)["javascript_dependent_content"] is True)

    jsonld_only = (
        '<html><body><main><h1>Hi</h1><p>' + ("Words here. " * 20) + '</p></main>'
        '<script type="application/ld+json">{"a":1}</script></body></html>'
    )
    result = semantic_html.analyse(jsonld_only)
    check("semantic: JSON-LD is not an executable script", result["executable_scripts"] == 0 and result["data_scripts"] == 1)
    check("semantic: JSON-LD alone does not imply JS dependency", result["javascript_dependent_content"] is False)

    skipped = semantic_html.analyse("<html><body><h1>A</h1><h4>B</h4></body></html>")
    check("semantic: skipped heading levels detected", len(skipped["skipped_levels"]) == 1)
    check("semantic: missing h1 detected", semantic_html.analyse("<html><body><h2>x</h2></body></html>")["h1_count"] == 0)

    accessibility = semantic_html.analyse('<html><body><img src="a.png"><input id="q"><button></button><a href="/x">click here</a></body></html>')
    check("semantic: missing alt detected", accessibility["images_without_alt"] == 1)
    check("semantic: unlabelled input detected", accessibility["inputs_without_label"] == 1)
    check("semantic: unnamed button detected", accessibility["buttons_without_accessible_name"] == 1)
    check("semantic: non-descriptive link detected", accessibility["links_non_descriptive"] == 1)

    labelled = semantic_html.analyse('<html><body><label for="q">Q</label><input id="q"></body></html>')
    check("semantic: label/for association recognised", labelled["inputs_without_label"] == 0)

    check("semantic: malformed markup does not crash", isinstance(semantic_html.analyse("<html><body><p>unclosed"), dict))


# ------------------------------------------------------------ structured data
def test_structured_data() -> None:
    html = (
        '<html><head><title>Acme</title><meta name="description" content="d">'
        '<link rel="canonical" href="https://acme.test/">'
        '<script type="application/ld+json">{"@context":"https://schema.org","@graph":['
        '{"@type":"Organization","@id":"https://acme.test/#o","name":"Acme","url":"https://acme.test/"},'
        '{"@type":"Product","name":"Phantom Widget"},'
        '{"@type":"Article","headline":"Acme","datePublished":"2026-01-01"}]}</script>'
        '<script type="application/ld+json">{oops}</script></head>'
        "<body><h1>Acme</h1><p>Acme builds things.</p></body></html>"
    )
    result = structured_data.audit(html, "test")
    check("structured: both JSON-LD blocks found", result["jsonld_blocks"] == 2)
    check("structured: invalid JSON reported", len(result["jsonld_parse_errors"]) == 1)
    check("structured: @graph nodes extracted", result["entity_types"].get("Organization") == 1)
    unsupported = [i for i in result["schema_issues"] if i["severity"] == "P1"]
    check("structured: name absent from visible text is flagged", any("Phantom Widget" in i["issue"] for i in unsupported))
    check("structured: entities without @id counted", result["entities_without_id"] >= 1)
    check("structured: canonical extracted", result["citation_readiness"]["canonical"] == "https://acme.test/")
    check("structured: citation readiness computed", result["citation_readiness"]["ready"] is True)

    duplicate = structured_data.audit(
        '<html><body><script type="application/ld+json">'
        '[{"@context":"https://schema.org","@type":"Organization","@id":"#a","name":"X"},'
        '{"@context":"https://schema.org","@type":"Organization","@id":"#a","name":"X"}]</script>'
        "<p>X</p></body></html>", "t")
    check("structured: duplicate @id detected", duplicate["duplicate_ids"] == ["#a"])

    empty = structured_data.audit("<html><body><p>No markup here at all.</p></body></html>", "t")
    check("structured: page without JSON-LD handled", empty["jsonld_blocks"] == 0 and empty["entity_types"] == {})

    thin = structured_data.audit("<html><body><p>Short.</p></body></html>", "t")
    check("structured: thin content flagged", thin["answerability"]["thin_content"] is True)


# ------------------------------------------------------- markdown negotiation
def test_markdown_detection() -> None:
    html_body = "<!doctype html><html><head><title>x</title></head><body><pre># Not a heading</pre></body></html>"
    check("markdown: HTML with a hash line is not Markdown", semantic_or_false(html_body))
    markdown_body = "# Title\n\nSome text with a [link](https://x.test).\n\n## Section\n\nMore text.\n"
    signals = markdown_negotiation.looks_like_markdown(markdown_body)
    check("markdown: real Markdown recognised", signals["structural_markdown"] is True)
    check("markdown: headings counted", signals["markdown_headings"] == 2)
    check("markdown: links counted", signals["markdown_links"] == 1)


def semantic_or_false(body: str) -> bool:
    return markdown_negotiation.looks_like_markdown(body)["structural_markdown"] is False


# ------------------------------------------------------------- link headers
def test_link_headers() -> None:
    parsed = http_inspect.parse_link_header('</a.json>; rel="describedby"; type="application/json", </b>; rel=alternate')
    check("link header: both entries parsed", len(parsed) == 2)
    check("link header: rel extracted", parsed[0]["rel"] == "describedby")
    check("link header: unquoted rel handled", parsed[1]["rel"] == "alternate")
    check("link header: empty value is safe", http_inspect.parse_link_header("") == [])


# ------------------------------------------------------------------- scoring
def test_scoring() -> None:
    def make(name, status, score=scoring.AGENT_READINESS):
        return {"name": name, "status": status, "score": score, "priority": "P1"}

    checks = [
        make("robots.txt", scoring.PASS),
        make("Sitemap", scoring.PASS),
        make("x402", scoring.NA),
        make("MPP", scoring.NA),
        make("DNS-AID", scoring.MANUAL),
    ]
    summary = scoring.summarize(checks)
    agent = summary["agent_readiness"]
    check("scoring: N/A and MANUAL excluded from the denominator", agent["applicable_checks"] == 2)
    check("scoring: all-pass gives 100", agent["score"] == 100)
    check("scoring: N/A counted separately", agent["not_applicable"] == 2)
    check("scoring: MANUAL counted separately", agent["manual_review"] == 1)

    with_fail = checks + [make("AI Bot Rules", scoring.FAIL)]
    check("scoring: a FAIL lowers the score", scoring.summarize(with_fail)["agent_readiness"]["score"] < 100)

    with_warning = [make("robots.txt", scoring.PASS), make("Sitemap", scoring.WARNING)]
    warned = scoring.summarize(with_warning)["agent_readiness"]
    check("scoring: WARNING is partial credit, not zero", 50 < warned["score"] < 100)

    only_na = scoring.summarize([make("x402", scoring.NA)])["agent_readiness"]
    check("scoring: no applicable checks yields null, not zero", only_na["score"] is None)

    mixed = scoring.summarize([
        make("robots.txt", scoring.PASS, scoring.AGENT_READINESS),
        make("Structured data", scoring.FAIL, scoring.AEO_TECHNICAL),
    ])
    check("scoring: the two scores are independent", mixed["agent_readiness"]["score"] == 100 and mixed["aeo_technical"]["score"] == 0)
    check("scoring: no check falls outside both sets", mixed["unscored_checks"] == [])


# -------------------------------------------------------------- applicability
def test_applicability() -> None:
    no_commerce = {"commerce": {"present": False, "evidence": [], "code_confirmed": False}}
    check("commerce: absent commerce is not applicable", commerce_protocols.commerce_evidence(no_commerce)["applicable"] is False)

    path_only = {"commerce": {"present": True, "evidence": ["path: src/pricing/index.html"], "code_confirmed": False}}
    check("commerce: a pricing page alone is not commerce", commerce_protocols.commerce_evidence(path_only)["applicable"] is False)

    with_stripe = {"commerce": {"present": True, "evidence": ["dependency: stripe"], "code_confirmed": False}}
    check("commerce: a payment dependency makes it applicable", commerce_protocols.commerce_evidence(with_stripe)["applicable"] is True)

    check("site type: content only", classify_site({
        "content": {"present": True, "evidence": ["a.html"]}, "api": {"present": False, "evidence": []}}) == "Content Site")
    check("site type: api only", classify_site({
        "content": {"present": False, "evidence": []}, "api": {"present": True, "evidence": ["a", "b", "c"]}}) == "API / Application")
    check("site type: hybrid", classify_site({
        "content": {"present": True, "evidence": ["a.html"]}, "api": {"present": True, "evidence": ["a", "b", "c"]}}) == "Hybrid")
    check("site type: unknown when there is no evidence", classify_site({
        "content": {"present": False, "evidence": []}, "api": {"present": False, "evidence": []}}) == "Unknown")


# ------------------------------------------------------------------- llms.txt
def test_llms() -> None:
    urls = [
        "https://x.test/",
        "https://x.test/about",
        "https://x.test/docs/getting-started",
        "https://x.test/admin/settings",
        "https://x.test/search?q=a",
        "https://x.test/assets/logo.png",
        "https://x.test/blog/post-1",
        "https://x.test/privacy",
    ]
    result = llms_txt.curate(urls, "X", "A summary")
    excluded = {e["url"] for e in result["excluded"]}
    check("llms: admin excluded", "https://x.test/admin/settings" in excluded)
    check("llms: query URLs excluded", "https://x.test/search?q=a" in excluded)
    check("llms: assets excluded", "https://x.test/assets/logo.png" in excluded)
    check("llms: about section curated", "About" in result["sections"])
    check("llms: documentation section curated", "Documentation" in result["sections"])
    check("llms: output starts with an H1", result["content"].startswith("# X"))
    check("llms: no invented URLs", all(u in result["content"] for u in ["https://x.test/about"]))

    audit = llms_txt.audit("Not a title\n")
    check("llms: file without an H1 is reported", not audit["valid"])


# ------------------------------------------------------- agent skills index
def test_agent_skills_index() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "src" / "demo-skill"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: Demo skill used only by the toolkit test suite when validating index generation.\n---\n# Demo\nBody.\n",
            encoding="utf-8",
        )
        publish = root / "public"
        result = skills_index.build(root / "src", publish, ".well-known/agent-skills", "test", dry_run=False)
        artifact = publish / ".well-known/agent-skills/demo-skill/SKILL.md"
        check("index: artifact is published alongside the index", artifact.is_file())
        entry = result["index"]["skills"][0]
        import hashlib

        check("index: digest matches the published bytes",
              entry["digest"]["value"] == hashlib.sha256(artifact.read_bytes()).hexdigest())
        check("index: url points at the published artifact",
              (publish / entry["url"].lstrip("/")).is_file())
        check("index: verification passes for a consistent index",
              skills_index.verify(publish, ".well-known/agent-skills")["valid"])

        artifact.unlink()
        check("index: verification fails when an artifact is missing",
              not skills_index.verify(publish, ".well-known/agent-skills")["valid"])

        bad = root / "bad" / "Bad_Name"
        bad.mkdir(parents=True)
        (bad / "SKILL.md").write_text("---\nname: Bad_Name\ndescription: x\n---\nbody\n", encoding="utf-8")
        try:
            skills_index.collect(root / "bad")
            check("index: invalid skill name rejected", False, "no error raised")
        except SystemExit:
            check("index: invalid skill name rejected", True)


# ------------------------------------------------------------- end-to-end run
def test_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "public").mkdir(parents=True)
        (root / "public" / "index.html").write_text(
            '<!doctype html><html lang="en"><head><title>Demo</title>'
            '<meta name="description" content="Demo site">'
            '<link rel="canonical" href="https://demo.test/">'
            '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization",'
            '"name":"Demo","url":"https://demo.test/"}</script></head>'
            "<body><main><article><h1>Demo</h1><h2>About</h2><p>" + ("Demo content. " * 40) + "</p></article></main></body></html>",
            encoding="utf-8",
        )
        (root / "public" / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://demo.test/sitemap.xml\n", encoding="utf-8")
        (root / "public" / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            "<url><loc>https://demo.test/</loc><lastmod>2026-01-01</lastmod></url></urlset>", encoding="utf-8")

        completed = subprocess.run(
            [sys.executable, str(HERE / "aeo_audit.py"), "--project", str(root), "--json-only"],
            capture_output=True, text=True, timeout=180,
        )
        check("end-to-end: audit exits cleanly", completed.returncode == 0, completed.stderr[-300:])
        if completed.returncode != 0:
            return
        result = json.loads(completed.stdout)

        check("end-to-end: no live check is reported as FAIL without a URL",
              not [c for c in result["checks"] if c["status"] == "FAIL" and c["live_evidence"]])
        live_only = [c for c in result["checks"] if c["name"] in ("Homepage availability", "Actual bot access", "HTTP Link headers")]
        check("end-to-end: live-only checks are MANUAL REVIEW without a URL",
              all(c["status"] == "MANUAL REVIEW" for c in live_only))
        check("end-to-end: commerce is N/A for a project with no commerce",
              all(c["status"] == "N/A" for c in result["checks"] if c["section"] == "Commerce"))
        check("end-to-end: stack detected", "Static HTML" in result["meta"]["stack"]["frameworks"])
        check("end-to-end: site classified as a content site", result["meta"]["site_type"] == "Content Site")
        check("end-to-end: robots.txt found and passing",
              [c for c in result["checks"] if c["name"] == "robots.txt"][0]["status"] == "PASS")
        check("end-to-end: scores are independent",
              result["scores"]["agent_readiness"]["score"] != result["scores"]["aeo_technical"]["score"]
              or result["scores"]["agent_readiness"]["applicable_checks"] != result["scores"]["aeo_technical"]["applicable_checks"])
        check("end-to-end: every finding carries a priority",
              all(f["priority"] in ("P0", "P1", "P2", "P3") for f in result["findings"]))
        check("end-to-end: passing checks produce no findings",
              not [f for f in result["findings"] if f["status"] == "PASS"])
        check("end-to-end: N/A produces no findings",
              not [f for f in result["findings"] if f["status"] == "N/A"])

        # Empty project: nothing should be claimed about it.
        with tempfile.TemporaryDirectory() as empty:
            empty_run = subprocess.run(
                [sys.executable, str(HERE / "aeo_audit.py"), "--project", empty, "--json-only"],
                capture_output=True, text=True, timeout=180,
            )
            check("end-to-end: empty project audits without crashing", empty_run.returncode == 0, empty_run.stderr[-200:])
            if empty_run.returncode == 0:
                empty_result = json.loads(empty_run.stdout)
                check("end-to-end: empty project is Unknown", empty_result["meta"]["site_type"] == "Unknown")


# ------------------------------------------------------------- portability
def test_portability() -> None:
    """The skills directory must work after being copied into another repo."""
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "other-repo" / ".claude" / "skills"
        shutil.copytree(SKILLS_ROOT, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (Path(tmp) / "other-repo" / "index.html").write_text("<html><body><h1>Other</h1></body></html>", encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(target / "aeo-agent-readiness" / "scripts" / "aeo_audit.py"),
             "--project", str(Path(tmp) / "other-repo"), "--json-only"],
            capture_output=True, text=True, timeout=180,
        )
        check("portability: toolkit runs from a copied skills directory", completed.returncode == 0, completed.stderr[-300:])
        validation = subprocess.run(
            [sys.executable, str(target / "aeo-agent-readiness" / "scripts" / "validate_toolkit.py")],
            capture_output=True, text=True, timeout=120,
        )
        check("portability: validation passes in the copied location", validation.returncode == 0, validation.stdout[-300:])


def test_cdn_is_not_a_block() -> None:
    """Being behind a CDN is not a bot mitigation, and must not raise a P0."""

    class FakeResponse:
        def __init__(self, headers, body, status=200):
            self.headers = headers
            self.body = body
            self.status = status

        @property
        def ok(self):
            return 200 <= self.status < 300

        @property
        def text(self):
            return self.body.decode("utf-8", "replace")

    full_page = b"<html><body>" + (b"real content " * 3000) + b"</body></html>"
    served_by_cloudflare = FakeResponse({"Server": "cloudflare", "Content-Type": "text/html"}, full_page)
    check("bot access: Server: cloudflare alone is not a challenge",
          bot_access._challenge(served_by_cloudflare) is None)

    mitigated = FakeResponse({"Server": "cloudflare", "cf-mitigated": "challenge"}, b"", 403)
    check("bot access: cf-mitigated is a real challenge",
          bot_access._challenge(mitigated) == "cf-mitigated")

    interstitial = FakeResponse({"Server": "cloudflare"}, b"<html><title>Just a moment...</title></html>", 503)
    check("bot access: an interstitial page is a challenge",
          bot_access._challenge(interstitial) == "just a moment")


def test_seo_crawler_block_is_not_critical() -> None:
    """Disallowing commercial SEO crawlers is an owner decision, not an outage."""
    from aeolib.checks import _blocking_severity

    critical, agents = _blocking_severity([["AhrefsBot", "SemrushBot", "DotBot", "MJ12bot", "BLEXBot"]])
    check("crawlability: blocking SEO crawlers is not critical", critical is False)
    check("crawlability: the blocked agents are still reported", len(agents) == 5)

    critical, _ = _blocking_severity([["*"]])
    check("crawlability: blocking the wildcard group is critical", critical is True)

    critical, _ = _blocking_severity([["AhrefsBot", "GPTBot"]])
    check("crawlability: blocking an AI crawler is critical", critical is True)


def test_detector_precision() -> None:
    """Documentation about a capability must never be read as the capability."""
    prose = "We accept Stripe, PayPal and Shopify payments. See the checkout guide."
    check("detector: prose naming payment providers is not commerce code",
          COMMERCE_CODE_MARKERS.search(prose) is None)
    check("detector: a provider allow-list is not commerce code",
          COMMERCE_CODE_MARKERS.search('PROVIDERS = ["stripe", "paypal", "braintree"]') is None)
    check("detector: a real Stripe call is commerce code",
          COMMERCE_CODE_MARKERS.search("await stripe.checkout.sessions.create({})") is not None)
    check("detector: a real cart call is commerce code",
          COMMERCE_CODE_MARKERS.search("function addToCart(id) {}") is not None)

    check("detector: an OAuth endpoint path is not auth code",
          AUTH_CODE_MARKERS.search("/.well-known/oauth-authorization-server") is None)
    check("detector: citing RFC 8414 is not auth code",
          AUTH_CODE_MARKERS.search("OAuth discovery is defined by RFC 8414.") is None)
    check("detector: a real token exchange is auth code",
          AUTH_CODE_MARKERS.search('{"grant_type": "client_credentials"}') is not None)


def test_markdown_is_not_a_website() -> None:
    """A documentation repository must not be audited as a published site."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "README.md").write_text("# Notes\n\nSome documentation.\n", encoding="utf-8")
        (root / "GUIDE.md").write_text("# Guide\n\nMore documentation.\n", encoding="utf-8")
        result = inspect(root)
        check("markdown: a docs repo is not a Content Site", result["site_type"] == "Unknown")
        check("markdown: markdown alone is not web content", result["capabilities"]["content"]["present"] is False)

        completed = subprocess.run(
            [sys.executable, str(HERE / "aeo_audit.py"), "--project", str(root), "--json-only"],
            capture_output=True, text=True, timeout=180,
        )
        check("markdown: audit succeeds on a docs repo", completed.returncode == 0, completed.stderr[-200:])
        if completed.returncode != 0:
            return
        audited = json.loads(completed.stdout)
        check("markdown: nothing is reported as FAIL",
              not [c for c in audited["checks"] if c["status"] == "FAIL"])
        robots = [c for c in audited["checks"] if c["name"] == "robots.txt"][0]
        check("markdown: a missing robots.txt is undetermined, not a defect", robots["status"] == "MANUAL REVIEW")
        check("markdown: scores are null rather than zero",
              audited["scores"]["agent_readiness"]["score"] is None)

        # Adding one HTML page makes it a real site, and the verdicts change.
        (root / "index.html").write_text("<html><body><h1>Hi</h1></body></html>", encoding="utf-8")
        with_html = inspect(root)
        check("markdown: one HTML file makes it a Content Site", with_html["site_type"] == "Content Site")
        check("markdown: markdown joins the content evidence once a page exists",
              with_html["capabilities"]["content"]["present"] is True)


def test_agent_tooling_is_not_site_capability() -> None:
    """A .claude directory describes the audit, not what the site offers."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tooling = root / ".claude" / "skills" / "x" / "scripts"
        tooling.mkdir(parents=True)
        (tooling / "tool.py").write_text('PATHS = ["/.well-known/oauth-authorization-server"]\n', encoding="utf-8")
        (root / "index.html").write_text("<html><body><h1>Hi</h1></body></html>", encoding="utf-8")
        result = inspect(root)
        check("tooling: .claude is excluded from the scan", result["file_count"] == 1)
        check("tooling: agent tooling creates no auth capability",
              result["capabilities"]["auth"]["present"] is False)


def test_project_scan_excludes_vendor_dirs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "node_modules" / "pkg").mkdir(parents=True)
        (root / "node_modules" / "pkg" / "package.json").write_text('{"dependencies":{"stripe":"1"}}', encoding="utf-8")
        (root / "index.html").write_text("<html><body><h1>x</h1></body></html>", encoding="utf-8")
        result = inspect(root)
        check("scan: node_modules is not scanned", result["file_count"] == 1)
        check("scan: vendored dependencies do not create false commerce evidence",
              result["capabilities"]["commerce"]["present"] is False)


def main() -> None:
    for test in (
        test_robots, test_sitemap, test_semantic_html, test_structured_data, test_markdown_detection,
        test_link_headers, test_scoring, test_applicability, test_llms, test_agent_skills_index,
        test_detector_precision, test_markdown_is_not_a_website, test_agent_tooling_is_not_site_capability,
        test_cdn_is_not_a_block, test_seo_crawler_block_is_not_critical,
        test_project_scan_excludes_vendor_dirs, test_end_to_end, test_portability,
    ):
        try:
            test()
        except Exception as exc:  # a crashing test is a failing test
            RESULTS.append((test.__name__ + " raised " + type(exc).__name__, False, str(exc)[:200]))

    failed = [r for r in RESULTS if not r[1]]
    for name, passed, detail in RESULTS:
        if not passed:
            print("FAIL  " + name + ("  -> " + detail if detail else ""))
    print("")
    print(str(len(RESULTS) - len(failed)) + "/" + str(len(RESULTS)) + " assertions passed")
    if failed:
        raise SystemExit(1)
    print("All toolkit tests passed")


if __name__ == "__main__":
    main()
