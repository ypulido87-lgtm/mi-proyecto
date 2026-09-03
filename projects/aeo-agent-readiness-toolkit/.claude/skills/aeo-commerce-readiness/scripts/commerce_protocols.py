#!/usr/bin/env python3
"""Commerce applicability and agent-commerce protocol status.

Nothing here is ever implemented automatically. Payment protocols are only
assessed when the site genuinely transacts, and each one stays MANUAL REVIEW
until its current specification has been verified against primary sources.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

# Every protocol below is emerging or pre-1.0. `verified_spec: False` means the
# toolkit must never generate an implementation for it, only report on it.
PROTOCOLS = [
    {
        "name": "x402",
        "purpose": "HTTP-native payments built on the 402 Payment Required status",
        "detect": {"header": "www-authenticate", "status": 402},
        "verified_spec": False,
    },
    {
        "name": "MPP",
        "purpose": "Machine payable protocol for agent-initiated purchases",
        "detect": {},
        "verified_spec": False,
    },
    {
        "name": "UCP",
        "purpose": "Universal commerce protocol for catalogue and checkout interoperability",
        "detect": {},
        "verified_spec": False,
    },
    {
        "name": "ACP",
        "purpose": "Agentic commerce protocol for delegated purchase flows",
        "detect": {},
        "verified_spec": False,
    },
]


def commerce_evidence(capabilities: dict[str, Any]) -> dict[str, Any]:
    """Decide whether commerce checks apply at all, and say why."""
    commerce = capabilities.get("commerce", {})
    paths = [e for e in commerce.get("evidence", []) if e.startswith("path:")]
    dependencies = [e for e in commerce.get("evidence", []) if e.startswith("dependency:")]
    code = commerce.get("code_confirmed", False)
    # Directory names alone are too weak: a /pricing page is not a checkout.
    applicable = bool(dependencies or code)
    return {
        "applicable": applicable,
        "payment_dependencies": dependencies,
        "code_confirmed": code,
        "path_hints": paths[:8],
        "reason": (
            "Payment integration detected" if applicable
            else "No payment provider, cart, checkout or transaction code detected"
        ),
    }


def probe_live(origin: str) -> dict[str, Any]:
    """Look for a real 402 challenge. Absence is not a defect."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "aeo-agent-readiness" / "scripts"))
    from aeolib.fetch import fetch

    response = fetch(origin)
    return {
        "status": response.status,
        "http_402_observed": response.status == 402,
        "www_authenticate": response.header("WWW-Authenticate"),
        "payment_headers": {k: v for k, v in response.headers.items() if "payment" in k.lower()},
    }


def apply_local(registry, capabilities: dict[str, Any], na_helper) -> None:
    """Populate the four commerce checks on the shared registry."""
    evidence = commerce_evidence(capabilities)
    for protocol in PROTOCOLS:
        check = registry.get(protocol["name"])
        check.data["purpose"] = protocol["purpose"]
        if not evidence["applicable"]:
            na_helper(check, evidence["reason"])
            check.data["commerce_evidence"] = evidence
            continue
        check.priority = "P3"
        check.status = "MANUAL REVIEW"
        check.local = {"commerce_evidence": evidence}
        check.detail = (
            "Commerce detected, so " + protocol["name"] + " is in scope, but its specification is "
            "emerging and unverified here. Verify the current specification before any implementation"
        )
        check.recommendation = "Do not implement. Report as a manual decision for the owner"


def main() -> None:
    parser = argparse.ArgumentParser(description="Report commerce applicability and agent-commerce protocol status")
    parser.add_argument("--origin", help="Optional live origin to probe for a 402 challenge")
    args = parser.parse_args()
    output: dict[str, Any] = {"protocols": PROTOCOLS}
    if args.origin:
        output["live"] = probe_live(args.origin)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
