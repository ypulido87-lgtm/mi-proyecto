#!/usr/bin/env python3
"""Probe machine-readable discovery endpoints and report what is actually served.

Probing is not prescribing. A 404 here is only a FAIL when the site genuinely
offers the underlying capability; otherwise the orchestrator marks it N/A.
Paths whose specification this toolkit cannot verify are labelled `unverified`
so they are reported as MANUAL REVIEW rather than implemented.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "aeo-agent-readiness" / "scripts"))
from aeolib.fetch import fetch  # noqa: E402

# check: the audit check this endpoint belongs to
# requires: the capability that must exist before absence is a defect
# spec: "stable" when the path is fixed by a published specification,
#       "unverified" when the toolkit must not assume the path or schema.
ENDPOINTS: list[dict[str, Any]] = [
    {
        "path": "/.well-known/oauth-authorization-server",
        "check": "OAuth discovery",
        "requires": "oauth",
        "spec": "stable",
        "source": "RFC 8414",
        "expect_type": "application/json",
    },
    {
        "path": "/.well-known/oauth-protected-resource",
        "check": "OAuth Protected Resource",
        "requires": "oauth",
        "spec": "stable",
        "source": "RFC 9728",
        "expect_type": "application/json",
    },
    {
        "path": "/.well-known/openid-configuration",
        "check": "OAuth discovery",
        "requires": "oauth",
        "spec": "stable",
        "source": "OpenID Connect Discovery 1.0",
        "expect_type": "application/json",
    },
    {
        "path": "/.well-known/agent-card.json",
        "check": "A2A Agent Card",
        "requires": "agent_service",
        "spec": "unverified",
        "source": "A2A project documentation",
        "expect_type": "application/json",
    },
    {
        "path": "/.well-known/agent-skills/index.json",
        "check": "Agent Skills",
        "requires": "agent_skills",
        "spec": "unverified",
        "source": "agentskills.io",
        "expect_type": "application/json",
    },
    {
        "path": "/.well-known/mcp.json",
        "check": "MCP Server Card",
        "requires": "mcp",
        "spec": "unverified",
        "source": "Model Context Protocol documentation",
        "expect_type": "application/json",
    },
    {
        "path": "/.well-known/ard.json",
        "check": "ARD Manifest",
        "requires": "ard",
        "spec": "unverified",
        "source": "ARD proposal",
        "expect_type": "application/json",
    },
    {
        "path": "/.well-known/api-catalog",
        "check": "API Catalog",
        "requires": "api",
        "spec": "stable",
        "source": "RFC 9727",
        "expect_type": "application/linkset+json",
    },
    {
        "path": "/auth.md",
        "check": "Auth.md",
        "requires": "auth",
        "spec": "unverified",
        "source": "Emerging convention",
        "expect_type": "text/markdown",
    },
    {
        "path": "/llms.txt",
        "check": "llms.txt",
        "requires": "content",
        "spec": "proposal",
        "source": "llmstxt.org",
        "expect_type": "text/plain",
    },
    {
        "path": "/openapi.json",
        "check": "API Catalog",
        "requires": "api",
        "spec": "stable",
        "source": "OpenAPI Specification",
        "expect_type": "application/json",
    },
    {
        "path": "/.well-known/security.txt",
        "check": "security.txt",
        "requires": "content",
        "spec": "stable",
        "source": "RFC 9116",
        "expect_type": "text/plain",
    },
]


def probe_one(base: str, endpoint: dict[str, Any], check_head: bool = True) -> dict[str, Any]:
    url = urljoin(base, endpoint["path"])
    response = fetch(url, accept=endpoint.get("expect_type", "*/*") + ", */*")
    served_type = response.header("Content-Type").split(";")[0].strip().lower()
    result: dict[str, Any] = {
        "path": endpoint["path"],
        "check": endpoint["check"],
        "requires": endpoint["requires"],
        "spec_confidence": endpoint["spec"],
        "source": endpoint["source"],
        "url": url,
        "status": response.status,
        "content_type": served_type,
        "bytes": len(response.body),
        "redirects": len(response.redirects),
        "error": response.error,
        "cors": response.header("Access-Control-Allow-Origin"),
        "cache_control": response.header("Cache-Control"),
        "present": bool(response.ok and response.body),
    }
    if result["present"] and "json" in endpoint.get("expect_type", ""):
        try:
            result["json"] = json.loads(response.text)
            result["json_valid"] = True
        except json.JSONDecodeError as exc:
            result["json_valid"] = False
            result["json_error"] = str(exc)
    if result["present"] and "html" in served_type:
        # A SPA catch-all route answering 200 for everything is a false positive.
        result["present"] = False
        result["note"] = "HTML returned; likely a catch-all route rather than a real endpoint"
    if check_head and result["present"]:
        head = fetch(url, accept="*/*", method="HEAD")
        result["head_status"] = head.status
        result["head_matches_get"] = head.status == response.status
    return result


def scan(base: str, only: list[str] | None = None) -> dict[str, Any]:
    if not base.endswith("/"):
        base += "/"
    selected = [e for e in ENDPOINTS if not only or e["check"] in only or e["path"] in only]
    results = [probe_one(base, endpoint) for endpoint in selected]
    return {
        "origin": base,
        "probed": len(results),
        "present": [r["path"] for r in results if r["present"]],
        "results": results,
        "note": "Endpoints marked spec_confidence=unverified must be reported as MANUAL REVIEW and never generated from this toolkit's assumptions.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe machine-readable discovery endpoints")
    parser.add_argument("origin", help="Origin, e.g. https://example.com")
    parser.add_argument("--only", nargs="*", help="Limit to specific checks or paths")
    args = parser.parse_args()
    print(json.dumps(scan(args.origin, args.only), indent=2))


if __name__ == "__main__":
    main()
