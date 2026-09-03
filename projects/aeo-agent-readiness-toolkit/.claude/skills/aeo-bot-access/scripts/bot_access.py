#!/usr/bin/env python3
"""Compare declared bot policy with the access a bot actually receives.

robots.txt states intent. A CDN, WAF or origin rule states reality. This tool
requests the same URL with several user-agents and reports where the two
disagree. It never changes a policy and never infers what the owner wants.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

ENGINE = Path(__file__).resolve().parents[2] / "aeo-agent-readiness" / "scripts"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "aeo-discoverability" / "scripts"))
from aeolib.fetch import fetch  # noqa: E402
import robots_parser  # noqa: E402

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"

# Probe agents: the token a crawler publishes plus a full UA string, because
# some edge rules match on either.
PROBE_AGENTS = [
    {"name": "GPTBot", "ua": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.1; +https://openai.com/gptbot"},
    {"name": "ClaudeBot", "ua": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ClaudeBot/1.0; +claudebot@anthropic.com"},
    {"name": "PerplexityBot", "ua": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot"},
    {"name": "Googlebot", "ua": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
    {"name": "Bingbot", "ua": "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"},
]

BLOCK_STATUSES = {401, 403, 405, 406, 429, 451, 503}

# Cabeceras que solo aparecen cuando una mitigación se ha aplicado de verdad.
# `Server: cloudflare` NO está aquí a propósito: sitting behind a CDN is not a
# block, and treating it as one raises a false P0 on every Cloudflare site.
MITIGATION_HEADERS = ("cf-mitigated", "cf-chl-bypass", "x-datadome", "x-sucuri-block", "x-captcha-bypass")

# Frases de una página de interstitial. Solo se buscan cuando la respuesta es
# demasiado pequeña para ser la página real.
CHALLENGE_PHRASES = (
    "just a moment", "checking your browser", "attention required",
    "enable javascript and cookies", "verify you are human", "please complete the security check",
)
CHALLENGE_BODY_LIMIT = 20_000


def _challenge(response) -> str | None:
    """Detect a real bot mitigation, not merely the presence of a CDN."""
    headers = {k.lower(): (v or "").lower() for k, v in response.headers.items()}
    for name in MITIGATION_HEADERS:
        if name in headers:
            return name
    # A full page served with 2xx is content, whatever CDN delivered it.
    if response.ok and len(response.body) > CHALLENGE_BODY_LIMIT:
        return None
    body = response.text[:4000].lower() if response.body else ""
    for phrase in CHALLENGE_PHRASES:
        if phrase in body:
            return phrase
    return None


def probe(url: str, robots_text: str | None = None) -> dict[str, Any]:
    """Request one URL as several agents and contrast declared with actual access."""
    robots = robots_parser.parse(robots_text) if robots_text is not None else None
    baseline = fetch(url, user_agent=BROWSER_UA)
    results = []
    for agent in PROBE_AGENTS:
        response = fetch(url, user_agent=agent["ua"])
        declared = robots_parser.is_allowed(robots, agent["name"], url)["allowed"] if robots else None
        actual_blocked = response.status in BLOCK_STATUSES or response.status is None
        challenge = _challenge(response)
        entry = {
            "agent": agent["name"],
            "status": response.status,
            "bytes": len(response.body),
            "error": response.error,
            "challenge_marker": challenge,
            "declared_allowed": declared,
            "actually_served": not actual_blocked,
            "x_robots_tag": response.header("X-Robots-Tag"),
        }
        if declared is None:
            entry["verdict"] = "UNKNOWN"
        elif declared and actual_blocked:
            entry["verdict"] = "CONTRADICTION"
            entry["detail"] = "robots.txt allows this agent but the origin or edge returned HTTP " + str(response.status)
        elif declared and challenge:
            entry["verdict"] = "CONTRADICTION"
            entry["detail"] = "robots.txt allows this agent but an edge challenge was detected: " + challenge
        elif (not declared) and not actual_blocked:
            entry["verdict"] = "DECLARED_BLOCK_NOT_ENFORCED"
            entry["detail"] = "robots.txt disallows this agent; content is still served (robots is voluntary, not enforcement)"
        elif not declared:
            entry["verdict"] = "CONSISTENT_BLOCK"
        else:
            entry["verdict"] = "CONSISTENT_ALLOW"
        if baseline.status and response.status and baseline.status != response.status:
            entry["differs_from_browser"] = {"browser": baseline.status, "agent": response.status}
        results.append(entry)
    return {
        "url": url,
        "browser_baseline": {"status": baseline.status, "bytes": len(baseline.body), "error": baseline.error},
        "agents": results,
        "contradictions": [r for r in results if r["verdict"] == "CONTRADICTION"],
    }


def content_signals(robots_text: str) -> dict[str, Any]:
    """Report declared Content-Signal policy. Absence is reported, never assumed."""
    robots = robots_parser.parse(robots_text)
    declared = robots.content_signals
    parsed = []
    for line in declared:
        for item in line.split(","):
            item = item.strip()
            if not item:
                continue
            if "=" in item:
                key, value = item.split("=", 1)
                parsed.append({"signal": key.strip(), "value": value.strip()})
            else:
                parsed.append({"signal": item, "value": None})
    known = {"search", "ai-input", "ai-train"}
    return {
        "declared": declared,
        "parsed": parsed,
        "unknown_signals": [p["signal"] for p in parsed if p["signal"] not in known],
        "present": bool(declared),
        "note": (
            "No policy is inferred. If absent, present the owner with the technically valid "
            "options and let them decide; never set search, ai-input or ai-train automatically."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare declared and actual AI bot access")
    parser.add_argument("url", help="URL to probe (usually the homepage)")
    parser.add_argument("--robots", help="Path or URL to robots.txt; defaults to the origin's /robots.txt")
    args = parser.parse_args()
    source = args.robots or urljoin(args.url, "/robots.txt")
    try:
        robots_text = robots_parser.load(source)
    except SystemExit:
        robots_text = None
    result = probe(args.url, robots_text)
    result["content_signals"] = content_signals(robots_text) if robots_text else {"present": False, "declared": []}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
