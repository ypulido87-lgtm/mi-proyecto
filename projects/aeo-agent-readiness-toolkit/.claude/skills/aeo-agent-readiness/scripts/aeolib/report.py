"""Render the audit as Markdown and JSON, including a before/after comparison."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .checks import SECTIONS
from .scoring import FAIL, MANUAL, NA, PASS, WARNING

PRIORITY_TITLES = [
    ("P0", "P0 Blocking Issues", "An agent cannot access, discover or interpret essential content."),
    ("P1", "P1 High Impact", "Significant discoverability, machine-readability or entity-clarity problems."),
    ("P2", "P2 Enhancements", "Improvements to efficiency or interoperability."),
    ("P3", "P3 Experimental", "Emerging standards and advanced capabilities. Never treated as blocking."),
]
STATUS_LEGEND = {
    PASS: "verified evidence",
    FAIL: "applicable defect",
    WARNING: "applicable but incomplete or unverified end to end",
    NA: "not applicable; excluded from scoring",
    MANUAL: "no evidence available here; needs owner, deployment, browser, DNS or specification verification",
}


def _score_line(label: str, block: dict[str, Any]) -> str:
    value = block["score"]
    rendered = "not scored (no applicable evidence)" if value is None else str(value) + "/100"
    return (
        label + ": " + rendered + "  \n"
        "  applicable " + str(block["applicable_checks"])
        + " | passed " + str(block["passed"])
        + " | warnings " + str(block["warnings"])
        + " | failed " + str(block["failed"])
        + " | N/A " + str(block["not_applicable"])
        + " | manual review " + str(block["manual_review"])
    )


def _evidence_cell(check: dict[str, Any]) -> str:
    parts = []
    if check["local_evidence"]:
        parts.append("local")
    if check["live_evidence"]:
        parts.append("live")
    return "+".join(parts) or "none"


def build_markdown(result: dict[str, Any], previous: dict[str, Any] | None = None) -> str:
    meta = result["meta"]
    scores = result["scores"]
    checks = result["checks"]
    by_name = {c["name"]: c for c in checks}
    findings = result["findings"]
    lines: list[str] = []
    add = lines.append

    add("# AEO & Agent Readiness Audit")
    add("")
    add("Domain: " + meta["domain"])
    add("Project: " + meta["project"])
    add("Stack: " + ", ".join(meta["stack"]["frameworks"]) + (" | hosting: " + ", ".join(meta["stack"]["hosting"]) if meta["stack"]["hosting"] else ""))
    add("Site Type: " + meta["site_type"])
    add("Date: " + meta["date"])
    add("Evidence layers: " + meta["evidence_layers"])
    if meta.get("tls_verification", "enabled") != "enabled":
        add("")
        add("> **TLS certificate verification was disabled for this run.** Live results are diagnostics only.")
    add("")
    add(_score_line("Agent Readiness Score", scores["agent_readiness"]))
    add("")
    add(_score_line("AEO Technical Score", scores["aeo_technical"]))
    add("")

    add("## Executive Summary")
    add("")
    counts = {p: sum(1 for f in findings if f["priority"] == p) for p, _, _ in PRIORITY_TITLES}
    add(
        "The audit ran " + str(len(checks)) + " checks: "
        + str(sum(1 for c in checks if c["status"] == PASS)) + " PASS, "
        + str(sum(1 for c in checks if c["status"] == WARNING)) + " WARNING, "
        + str(sum(1 for c in checks if c["status"] == FAIL)) + " FAIL, "
        + str(sum(1 for c in checks if c["status"] == NA)) + " N/A, "
        + str(sum(1 for c in checks if c["status"] == MANUAL)) + " MANUAL REVIEW."
    )
    add("")
    add(
        "Findings by priority: P0 " + str(counts["P0"]) + ", P1 " + str(counts["P1"])
        + ", P2 " + str(counts["P2"]) + ", P3 " + str(counts["P3"]) + "."
    )
    add("")
    if meta["domain"] == "Not provided":
        add(
            "No public URL was supplied, so every live check is MANUAL REVIEW rather than a defect. "
            "A file in the repository is not proof that it is served: re-run with `--url` to confirm."
        )
        add("")
    add("Scoring method: " + scores["method"])
    add("")

    for code, title, description in PRIORITY_TITLES:
        add("## " + title)
        add("")
        add("_" + description + "_")
        add("")
        items = [f for f in findings if f["priority"] == code]
        if not items:
            add("None identified.")
        else:
            for finding in items:
                add("- **" + finding["check"] + "** (" + finding["status"] + ", " + finding["section"] + "): " + finding["detail"])
                if finding["recommendation"]:
                    add("  - Recommendation: " + finding["recommendation"])
        add("")

    for section, names in SECTIONS:
        add("## " + section)
        add("")
        add("| Check | Status | Score set | Evidence | Detail |")
        add("|---|---|---|---|---|")
        for name in names:
            check = by_name.get(name)
            if check is None:
                add("| " + name + " | MANUAL REVIEW | - | none | Check not produced by this run |")
                continue
            score_set = "Agent Readiness" if check["score"] == "agent_readiness" else "AEO Technical"
            detail = check["detail"].replace("|", "\\|")
            add("| " + name + " | " + check["status"] + " | " + score_set + " | " + _evidence_cell(check) + " | " + detail + " |")
        add("")

    add("## Files Modified")
    add("")
    modified = result.get("files_modified") or []
    if modified:
        for item in modified:
            add("- " + item)
    else:
        add("None. This run is read-only: it inspects and reports, it does not edit the site.")
    add("")

    add("## Tests Executed")
    add("")
    for test in result.get("tests_executed") or ["Local repository inspection"]:
        add("- " + test)
    add("")

    add("## Before / After")
    add("")
    if previous is None:
        add("No previous report found; this run is the baseline. Re-run after approved changes to populate this section.")
    else:
        add(_diff_table(previous, result))
    add("")

    add("## Remaining Manual Actions")
    add("")
    manual = [c for c in checks if c["status"] == MANUAL]
    if manual:
        for check in manual:
            add("- **" + check["name"] + "**: " + check["detail"])
    else:
        add("- None.")
    add("")
    add("Owner decisions this toolkit will not make automatically: AI training and retrieval policy, "
        "DNS records, CDN/WAF rules, deployment, payment protocols, authentication, and any capability "
        "the site does not actually provide.")
    add("")

    add("## Status Legend")
    add("")
    add("| Status | Meaning |")
    add("|---|---|")
    for status, meaning in STATUS_LEGEND.items():
        add("| " + status + " | " + meaning + " |")
    add("")
    return "\n".join(lines) + "\n"


def _diff_table(previous: dict[str, Any], current: dict[str, Any]) -> str:
    old_checks = {c["name"]: c for c in previous.get("checks", [])}
    new_checks = {c["name"]: c for c in current.get("checks", [])}
    rows = ["| Item | Before | After |", "|---|---|---|"]
    def rendered(value: Any) -> str:
        return "not scored" if value is None else str(value) + "/100"

    for key, label in (("agent_readiness", "Agent Readiness Score"), ("aeo_technical", "AEO Technical Score")):
        before = previous.get("scores", {}).get(key, {}).get("score")
        after = current.get("scores", {}).get(key, {}).get("score")
        rows.append("| " + label + " | " + rendered(before) + " | " + rendered(after) + " |")
    changed = 0
    for name, check in new_checks.items():
        old = old_checks.get(name)
        if old and old["status"] != check["status"]:
            rows.append("| " + name + " | " + old["status"] + " | " + check["status"] + " |")
            changed += 1
    if not changed:
        rows.append("| Check statuses | no change | no change |")
    return "\n".join(rows)


def write(result: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "aeo-agent-readiness-report.json"
    md_path = output_dir / "aeo-agent-readiness-report.md"
    previous = None
    if json_path.exists():
        try:
            previous = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = None
        # Keep the superseded run so before/after survives repeated audits.
        (output_dir / "aeo-agent-readiness-report.previous.json").write_text(
            json.dumps(previous, indent=2) if previous else "{}", encoding="utf-8"
        )
    md_path.write_text(build_markdown(result, previous), encoding="utf-8")
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return {"markdown": md_path, "json": json_path}
