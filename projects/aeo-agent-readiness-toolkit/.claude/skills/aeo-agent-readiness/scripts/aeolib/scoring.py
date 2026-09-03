"""Two independent scores with disjoint check sets.

Agent Readiness measures whether an agent can discover, access and interoperate.
AEO Technical measures whether an answer engine can parse, understand and cite.
No check contributes to both. N/A and MANUAL REVIEW never affect a score:
the first is not applicable, the second has no evidence to judge.
"""
from __future__ import annotations

from typing import Any

PASS = "PASS"
FAIL = "FAIL"
WARNING = "WARNING"
NA = "N/A"
MANUAL = "MANUAL REVIEW"
STATUSES = (PASS, FAIL, WARNING, NA, MANUAL)

# A WARNING is a partial credit: the capability exists but is incomplete or
# unverified end to end. FAIL earns nothing.
STATUS_WEIGHT = {PASS: 1.0, WARNING: 0.5, FAIL: 0.0}
SCORED_STATUSES = set(STATUS_WEIGHT)

AGENT_READINESS = "agent_readiness"
AEO_TECHNICAL = "aeo_technical"

# Relative weight of each check inside its score. Blocking access checks weigh
# more than experimental interoperability ones.
CHECK_WEIGHTS: dict[str, float] = {
    # Agent Readiness
    "Homepage availability": 3.0,
    "robots.txt": 2.0,
    "Sitemap": 2.0,
    "AI Bot Rules": 2.0,
    "Actual bot access": 3.0,
    "Content Signals": 1.0,
    "HTTP Link headers": 1.0,
    "DNS-AID": 0.5,
    "Web Bot Auth": 0.5,
    "Markdown negotiation": 1.0,
    "llms.txt": 1.0,
    "API Catalog": 1.0,
    "OAuth discovery": 1.0,
    "OAuth Protected Resource": 1.0,
    "Auth.md": 0.5,
    "MCP Server Card": 1.0,
    "A2A Agent Card": 1.0,
    "Agent Skills": 1.0,
    "WebMCP": 0.5,
    "ARD Manifest": 0.5,
    "x402": 1.0,
    "MPP": 1.0,
    "UCP": 1.0,
    "ACP": 1.0,
    # AEO Technical
    "Crawlability": 3.0,
    "Content availability": 3.0,
    "Server-rendered content": 3.0,
    "Semantic HTML": 2.0,
    "Structured data": 2.5,
    "Entity clarity": 2.0,
    "Canonicalization": 2.0,
    "Answer extraction": 2.0,
    "Citation readiness": 2.0,
    "Content duplication": 1.0,
}


def score_checks(checks: list[dict[str, Any]], score_name: str) -> dict[str, Any]:
    """Weighted percentage over applicable, evidence-bearing checks only."""
    relevant = [c for c in checks if c.get("score") == score_name]
    scored = [c for c in relevant if c["status"] in SCORED_STATUSES]
    total_weight = sum(CHECK_WEIGHTS.get(c["name"], 1.0) for c in scored)
    earned = sum(CHECK_WEIGHTS.get(c["name"], 1.0) * STATUS_WEIGHT[c["status"]] for c in scored)
    counts = {status: sum(1 for c in relevant if c["status"] == status) for status in STATUSES}
    return {
        "score": round(100 * earned / total_weight) if total_weight else None,
        "applicable_checks": len(scored),
        "passed": counts[PASS],
        "warnings": counts[WARNING],
        "failed": counts[FAIL],
        "not_applicable": counts[NA],
        "manual_review": counts[MANUAL],
        "weighted_earned": round(earned, 2),
        "weighted_total": round(total_weight, 2),
    }


def summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    agent = score_checks(checks, AGENT_READINESS)
    aeo = score_checks(checks, AEO_TECHNICAL)
    unassigned = [c["name"] for c in checks if c.get("score") not in (AGENT_READINESS, AEO_TECHNICAL)]
    return {
        "agent_readiness": agent,
        "aeo_technical": aeo,
        "unscored_checks": unassigned,
        "method": (
            "score = 100 * sum(weight * status_value) / sum(weight) over checks whose status is "
            "PASS (1.0), WARNING (0.5) or FAIL (0.0). N/A and MANUAL REVIEW are excluded from both "
            "numerator and denominator. The two scores use disjoint check sets. A score of null "
            "means no check in that set produced scorable evidence."
        ),
    }


def priority_of(check: dict[str, Any]) -> str | None:
    """Findings inherit the check priority; passing checks produce no finding."""
    if check["status"] in (PASS, NA):
        return None
    return check.get("priority", "P2")
