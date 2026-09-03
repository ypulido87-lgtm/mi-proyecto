#!/usr/bin/env python3
"""Test whether a URL serves real Markdown under `Accept: text/markdown`.

A page is only credited when the response is genuinely Markdown. HTML returned
with a 200 is a WARNING, never a PASS, even if the body happens to contain a
line that looks like a heading.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "aeo-agent-readiness" / "scripts"))
from aeolib.fetch import fetch  # noqa: E402

MARKDOWN_TYPES = ("text/markdown", "text/x-markdown", "text/plain")
HTML_MARKER = re.compile(r"<(?:!doctype\s+html|html|head|body|div|span|script|meta)\b", re.I)
ATX_HEADING = re.compile(r"^#{1,6}\s+\S", re.M)
MD_LINK = re.compile(r"\[[^\]]+\]\([^)]+\)")
SETEXT = re.compile(r"^\S.*\n(=+|-+)\s*$", re.M)


def looks_like_markdown(body: str) -> dict[str, Any]:
    """Structural evidence that a body is Markdown rather than HTML."""
    html_hits = len(HTML_MARKER.findall(body))
    headings = len(ATX_HEADING.findall(body)) + len(SETEXT.findall(body))
    links = len(MD_LINK.findall(body))
    # HTML is allowed inside Markdown, so judge by density rather than presence.
    html_density = html_hits / max(len(body) / 1000, 1)
    verdict = headings > 0 and html_density < 2
    return {
        "markdown_headings": headings,
        "markdown_links": links,
        "html_tag_hits": html_hits,
        "html_tags_per_kb": round(html_density, 2),
        "structural_markdown": verdict,
    }


def compare(url: str) -> dict[str, Any]:
    html = fetch(url, accept="text/html,application/xhtml+xml")
    markdown = fetch(url, accept="text/markdown")
    md_type = markdown.header("Content-Type").split(";")[0].strip().lower()
    signals = looks_like_markdown(markdown.text) if markdown.body else {}
    declared = md_type in MARKDOWN_TYPES
    identical = html.body == markdown.body and bool(html.body)

    if not markdown.ok:
        status, detail = "FAIL", "Markdown request returned HTTP " + str(markdown.status)
    elif md_type in ("text/markdown", "text/x-markdown") and signals.get("structural_markdown"):
        status, detail = "PASS", "Served text/markdown with Markdown structure"
    elif identical:
        status, detail = "WARNING", "Identical body for both Accept headers; no negotiation"
    elif declared and signals.get("structural_markdown"):
        status, detail = "WARNING", "Markdown-like body served as " + (md_type or "unknown type")
    else:
        status, detail = "WARNING", "HTML returned for Accept: text/markdown (" + (md_type or "unknown") + ")"

    html_bytes = len(html.body)
    md_bytes = len(markdown.body)
    reduction = round(100 * (1 - md_bytes / html_bytes)) if html_bytes and md_bytes else None
    return {
        "url": url,
        "status": status,
        "detail": detail,
        "vary_header": html.header("Vary"),
        "vary_includes_accept": "accept" in html.header("Vary").lower(),
        "html": {
            "status": html.status,
            "content_type": html.header("Content-Type"),
            "bytes": html_bytes,
        },
        "markdown": {
            "status": markdown.status,
            "content_type": markdown.header("Content-Type"),
            "bytes": md_bytes,
            "preview": markdown.text[:400],
            **signals,
        },
        "identical_bodies": identical,
        "byte_reduction_percent": reduction,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare HTML and Markdown representations of a URL")
    parser.add_argument("url")
    args = parser.parse_args()
    print(json.dumps(compare(args.url), indent=2))


if __name__ == "__main__":
    main()
