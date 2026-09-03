#!/usr/bin/env python3
"""AEO and AI Agent Readiness audit runner.

Two evidence layers:
  LOCAL  - what the repository contains.
  LIVE   - what an agent actually receives from a public origin (--url).

A repository file is never treated as proof of a public URL. Without --url every
live-only check is MANUAL REVIEW, not FAIL, and is excluded from both scores.

    python aeo_audit.py --project .
    python aeo_audit.py --project . --url https://example.com
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aeolib import checks as checks_module  # noqa: E402
from aeolib import project as project_module  # noqa: E402
from aeolib import report as report_module  # noqa: E402
from aeolib import scoring  # noqa: E402
from aeolib.fetch import origin as normalize_origin  # noqa: E402
from aeolib.fetch import set_insecure_tls  # noqa: E402


def run(project_root: Path, url: str | None, insecure: bool = False) -> dict[str, Any]:
    inspection = project_module.inspect(project_root)
    registry = checks_module.build_registry()
    tests = ["Local repository inspection (" + str(inspection["file_count"]) + " files scanned)"]

    checks_module.run_local(registry, project_root, inspection)
    if url:
        base = normalize_origin(url)
        checks_module.run_live(registry, base, inspection)
        tests.append("Live origin inspection of " + base + (" (TLS verification DISABLED)" if insecure else ""))
    else:
        base = "Not provided"

    check_dicts = [c.to_dict() for c in registry.all()]
    return {
        "meta": {
            "domain": base,
            "project": project_root.name,
            "project_path": str(project_root),
            "stack": inspection["stack"],
            "site_type": inspection["site_type"],
            "capabilities": {
                key: value for key, value in inspection["capabilities"].items()
                if key in ("commerce", "api", "auth", "mcp", "agent_service")
            },
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "evidence_layers": "local+live" if url else "local only",
            "toolkit_version": "2.0",
            "tls_verification": "disabled (diagnostics only)" if insecure else "enabled",
        },
        "scores": scoring.summarize(check_dicts),
        "checks": check_dicts,
        "findings": checks_module.findings(registry),
        "files_modified": [],
        "tests_executed": tests,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", default=".", help="Path to the project root (default: current directory)")
    parser.add_argument("--url", help="Public origin to audit, e.g. https://example.com")
    parser.add_argument("--output", default=None, help="Report directory (default: <project>/reports)")
    parser.add_argument("--json-only", action="store_true", help="Print JSON to stdout and write no files")
    parser.add_argument("--insecure", action="store_true",
                        help="Skip TLS certificate verification (diagnostics only; stamped in the report)")
    args = parser.parse_args()

    project_root = Path(args.project).resolve()
    if not project_root.is_dir():
        raise SystemExit("Project path is not a directory: " + str(project_root))

    if args.insecure:
        set_insecure_tls(True)
        print("WARNING: TLS certificate verification is disabled. Results are diagnostics only.", file=sys.stderr)
    result = run(project_root, args.url, args.insecure)

    if args.json_only:
        print(json.dumps(result, indent=2))
        return

    # Default lands beside the audited project; an explicit path is honoured as given.
    output_dir = project_root / "reports" if args.output is None else Path(args.output).resolve()
    written = report_module.write(result, output_dir)

    agent = result["scores"]["agent_readiness"]
    aeo = result["scores"]["aeo_technical"]
    print("Agent Readiness Score: " + str(agent["score"]) + "/100 (" + str(agent["applicable_checks"]) + " applicable)")
    print("AEO Technical Score:   " + str(aeo["score"]) + "/100 (" + str(aeo["applicable_checks"]) + " applicable)")
    for code in ("P0", "P1", "P2", "P3"):
        print(code + " findings: " + str(sum(1 for f in result["findings"] if f["priority"] == code)))
    print("Reports: " + str(written["markdown"]) + " and " + str(written["json"]))


if __name__ == "__main__":
    main()
