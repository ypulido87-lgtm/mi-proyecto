#!/usr/bin/env python3
"""Inspect what an agent really receives: status, redirects, headers, canonical.

Reports the full redirect chain, parses `Link` headers per RFC 8288, and pulls
the canonical URL and meta robots directives out of the HTML head.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "aeo-agent-readiness" / "scripts"))
from aeolib.fetch import fetch  # noqa: E402

LINK_ENTRY = re.compile(r"<([^>]*)>\s*((?:;[^,;]*)*)")


def parse_link_header(value: str) -> list[dict[str, Any]]:
    """Parse an RFC 8288 Link header into target/parameter pairs."""
    links = []
    for match in LINK_ENTRY.finditer(value or ""):
        target, params = match.group(1).strip(), match.group(2)
        entry: dict[str, Any] = {"target": target, "params": {}}
        for param in params.split(";"):
            param = param.strip()
            if not param or "=" not in param:
                continue
            key, raw = param.split("=", 1)
            entry["params"][key.strip().lower()] = raw.strip().strip('"')
        entry["rel"] = entry["params"].get("rel")
        links.append(entry)
    return links


class HeadParser(HTMLParser):
    """Collect head-level machine-readable signals without a DOM library."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonical: str | None = None
        self.alternates: list[dict[str, str]] = []
        self.meta_robots: list[str] = []
        self.title: str | None = None
        self.lang: str | None = None
        self.jsonld_blocks = 0
        self._in_title = False
        self._in_jsonld = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html" and attributes.get("lang"):
            self.lang = attributes["lang"]
        elif tag == "link":
            rel = attributes.get("rel", "").lower()
            if "canonical" in rel:
                self.canonical = attributes.get("href")
            elif "alternate" in rel:
                self.alternates.append(
                    {
                        "href": attributes.get("href", ""),
                        "type": attributes.get("type", ""),
                        "hreflang": attributes.get("hreflang", ""),
                    }
                )
        elif tag == "meta":
            name = attributes.get("name", "").lower()
            if name in ("robots", "googlebot") or name.endswith("bot"):
                self.meta_robots.append(name + ": " + attributes.get("content", ""))
        elif tag == "title":
            self._in_title = True
        elif tag == "script" and attributes.get("type", "").lower() == "application/ld+json":
            self._in_jsonld = True
            self.jsonld_blocks += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            self._in_jsonld = False

    def handle_data(self, data: str) -> None:
        if self._in_title and self.title is None:
            self.title = data.strip()


def inspect(url: str, accept: str = "text/html,application/xhtml+xml", user_agent: str | None = None) -> dict[str, Any]:
    kwargs = {"accept": accept}
    if user_agent:
        kwargs["user_agent"] = user_agent
    response = fetch(url, **kwargs)
    result: dict[str, Any] = {
        "requested_url": url,
        "final_url": response.url,
        "status": response.status,
        "redirects": response.redirects,
        "error": response.error,
        "content_type": response.header("Content-Type"),
        "bytes": len(response.body),
        "headers": response.headers,
        "link_headers": parse_link_header(response.header("Link")),
        "x_robots_tag": response.header("X-Robots-Tag"),
        "vary": response.header("Vary"),
        "cache_control": response.header("Cache-Control"),
    }
    if "html" in result["content_type"] and response.body:
        parser = HeadParser()
        try:
            parser.feed(response.text)
        except Exception as exc:  # malformed markup must not abort an audit
            result["html_parse_error"] = str(exc)
        result["html"] = {
            "title": parser.title,
            "lang": parser.lang,
            "canonical": parser.canonical,
            "alternates": parser.alternates,
            "meta_robots": parser.meta_robots,
            "jsonld_blocks": parser.jsonld_blocks,
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the real HTTP response for a URL")
    parser.add_argument("url")
    parser.add_argument("--accept", default="text/html,application/xhtml+xml")
    parser.add_argument("--user-agent", default=None)
    parser.add_argument("--body", action="store_true", help="Include the response body")
    args = parser.parse_args()
    result = inspect(args.url, args.accept, args.user_agent)
    if args.body:
        response = fetch(args.url, accept=args.accept)
        result["body"] = response.text
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
