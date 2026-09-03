#!/usr/bin/env python3
"""Validate a sitemap or sitemap index against the sitemaps.org protocol.

Checks XML well-formedness, the correct namespace, protocol limits, absolute and
same-origin URLs, lastmod format, and (optionally) live HTTP reachability.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
MAX_URLS = 50_000
MAX_BYTES = 52_428_800  # 50 MiB uncompressed, per the protocol
W3C_DATE = re.compile(
    r"^\d{4}(-\d{2}(-\d{2}(T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2}))?)?)?$"
)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _namespace(tag: str) -> str:
    return tag[1:].split("}", 1)[0] if tag.startswith("{") else ""


def load_bytes(source: str) -> bytes:
    if source.startswith(("http://", "https://")):
        engine = Path(__file__).resolve().parents[2] / "aeo-agent-readiness" / "scripts"
        sys.path.insert(0, str(engine))
        from aeolib.fetch import fetch

        response = fetch(source, accept="application/xml,text/xml")
        if not response.ok:
            raise SystemExit("Sitemap not retrievable: HTTP " + str(response.status) + " " + (response.error or ""))
        return response.body
    return Path(source).read_bytes()


def validate(raw: bytes, source: str = "", origin: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {
        "source": source,
        "kind": None,
        "valid_xml": False,
        "namespace_ok": False,
        "url_count": 0,
        "urls": [],
        "children": [],
        "errors": [],
        "warnings": [],
        "lastmod_present": 0,
        "lastmod_invalid": [],
    }
    if raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except OSError as exc:
            result["errors"].append("Gzip decompression failed: " + str(exc))
            return result
    if len(raw) > MAX_BYTES:
        result["warnings"].append("Sitemap exceeds the 50 MiB protocol limit")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        result["errors"].append("Invalid XML: " + str(exc))
        return result
    result["valid_xml"] = True
    result["namespace_ok"] = _namespace(root.tag) == SITEMAP_NS
    if not result["namespace_ok"]:
        result["errors"].append("Root element is not in the sitemaps.org 0.9 namespace")
    root_name = _local(root.tag)
    if root_name == "sitemapindex":
        result["kind"] = "sitemapindex"
        result["children"] = [
            (child.findtext("{%s}loc" % SITEMAP_NS) or child.findtext("loc") or "").strip()
            for child in root
            if _local(child.tag) == "sitemap"
        ]
        result["url_count"] = len(result["children"])
    elif root_name == "urlset":
        result["kind"] = "urlset"
        for child in root:
            if _local(child.tag) != "url":
                continue
            loc = (child.findtext("{%s}loc" % SITEMAP_NS) or child.findtext("loc") or "").strip()
            lastmod = (child.findtext("{%s}lastmod" % SITEMAP_NS) or child.findtext("lastmod") or "").strip()
            entry: dict[str, Any] = {"loc": loc, "lastmod": lastmod or None}
            if lastmod:
                result["lastmod_present"] += 1
                if not W3C_DATE.match(lastmod):
                    result["lastmod_invalid"].append(lastmod)
                    entry["lastmod_valid"] = False
                else:
                    entry["lastmod_valid"] = True
                    entry["lastmod_in_future"] = _is_future(lastmod)
            result["urls"].append(entry)
        result["url_count"] = len(result["urls"])
    else:
        result["errors"].append("Unexpected root element: " + root_name)
        return result

    if result["url_count"] > MAX_URLS:
        result["errors"].append("More than 50,000 entries; split into a sitemap index")
    if result["url_count"] == 0:
        result["errors"].append("Sitemap contains no entries")

    locations = [u["loc"] for u in result["urls"]] or result["children"]
    seen: dict[str, int] = {}
    for loc in locations:
        if not loc:
            result["errors"].append("Entry with an empty <loc>")
            continue
        parts = urlsplit(loc)
        if not parts.scheme or not parts.netloc:
            result["errors"].append("Non-absolute URL: " + loc)
        if origin and parts.netloc and parts.netloc != urlsplit(origin).netloc:
            result["warnings"].append("Cross-host URL: " + loc)
        if parts.query:
            result["warnings"].append("URL carries a query string: " + loc)
        if parts.fragment:
            result["warnings"].append("URL carries a fragment: " + loc)
        seen[loc] = seen.get(loc, 0) + 1
    duplicates = sorted(loc for loc, count in seen.items() if count > 1)
    if duplicates:
        result["errors"].append("Duplicate URLs: " + ", ".join(duplicates[:5]))
    if result["kind"] == "urlset" and result["lastmod_present"] == 0:
        result["warnings"].append("No lastmod present; freshness cannot be signalled")
    return result


def _is_future(value: str) -> bool:
    try:
        text = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text) if len(text) > 10 else datetime.fromisoformat(text[:10])
    except ValueError:
        return False
    now = datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now()
    return parsed > now


def check_urls_live(urls: list[str], limit: int = 25) -> list[dict[str, Any]]:
    """Fetch a bounded sample of sitemap URLs and report the real status."""
    engine = Path(__file__).resolve().parents[2] / "aeo-agent-readiness" / "scripts"
    sys.path.insert(0, str(engine))
    from aeolib.fetch import fetch

    checked = []
    for url in urls[:limit]:
        response = fetch(url, method="HEAD")
        if response.status is None or response.status == 405:
            response = fetch(url)
        checked.append(
            {
                "url": url,
                "status": response.status,
                "redirects": len(response.redirects),
                "final_url": response.url,
                "error": response.error,
            }
        )
    return checked


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a sitemap or sitemap index")
    parser.add_argument("source", help="Path or URL to a sitemap")
    parser.add_argument("--origin", default="", help="Expected origin, to flag cross-host URLs")
    parser.add_argument("--check-urls", type=int, default=0, help="HEAD-check up to N sitemap URLs")
    args = parser.parse_args()
    result = validate(load_bytes(args.source), args.source, args.origin)
    if args.check_urls and result["urls"]:
        result["live_sample"] = check_urls_live([u["loc"] for u in result["urls"]], args.check_urls)
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if result["errors"] else 0)


if __name__ == "__main__":
    main()
