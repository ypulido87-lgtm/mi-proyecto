#!/usr/bin/env python3
"""Generate an Agent Skills discovery index together with its artifacts.

Three rules this tool enforces, because breaking any of them publishes a false
capability signal:

1. The index and the artifacts are written together. An index that references a
   SKILL.md which is not published is worse than no index at all.
2. Every digest is computed from the bytes actually written to the publish root.
3. Publishing is opt-in. `--confirm-applicable` is required, and it is only
   honest when the site really offers the skills to outside agents.

The discovery schema for Agent Skills is still evolving. Verify the current
specification at agentskills.io before publishing, and pass the schema version
you verified with `--schema-version`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.S)
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESCRIPTION = 1024


def parse_frontmatter(text: str) -> dict[str, str]:
    """Minimal YAML front-matter reader for the scalar keys skills use."""
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError("Missing YAML front matter")
    fields: dict[str, str] = {}
    key: str | None = None
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^[A-Za-z0-9_-]+\s*:", line):
            key, _, value = line.partition(":")
            key = key.strip()
            fields[key] = value.strip().strip("'\"")
        elif key:  # folded continuation line
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def collect(skills_root: Path) -> list[dict[str, Any]]:
    entries = []
    for skill_file in sorted(skills_root.glob("*/SKILL.md")):
        raw = skill_file.read_bytes()
        fields = parse_frontmatter(raw.decode("utf-8", "replace"))
        name = fields.get("name", "")
        description = fields.get("description", "")
        problems = []
        if not name:
            problems.append("missing name")
        elif not NAME_PATTERN.match(name):
            problems.append("name is not lowercase kebab-case")
        elif name != skill_file.parent.name:
            problems.append("name does not match its directory")
        if len(name) > MAX_NAME:
            problems.append("name exceeds " + str(MAX_NAME) + " characters")
        if not description:
            problems.append("missing description")
        if len(description) > MAX_DESCRIPTION:
            problems.append("description exceeds " + str(MAX_DESCRIPTION) + " characters")
        if problems:
            raise SystemExit(str(skill_file) + ": " + "; ".join(problems))
        entries.append({"name": name, "description": description, "source": skill_file, "bytes": raw})
    return entries


def build(skills_root: Path, publish_root: Path, base_path: str, schema_version: str, dry_run: bool) -> dict[str, Any]:
    entries = collect(skills_root)
    target_dir = publish_root / base_path.strip("/")
    index_entries = []
    written: list[str] = []

    for entry in entries:
        artifact_dir = target_dir / entry["name"]
        artifact_path = artifact_dir / "SKILL.md"
        if not dry_run:
            artifact_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(entry["source"], artifact_path)
            published_bytes = artifact_path.read_bytes()
        else:
            published_bytes = entry["bytes"]
        written.append(str(artifact_path))
        index_entries.append(
            {
                "name": entry["name"],
                "description": entry["description"],
                "url": "/" + base_path.strip("/") + "/" + entry["name"] + "/SKILL.md",
                "content_type": "text/markdown; charset=utf-8",
                "digest": {
                    "algorithm": "sha-256",
                    # Computed from the bytes that are actually published.
                    "value": hashlib.sha256(published_bytes).hexdigest(),
                },
                "bytes": len(published_bytes),
            }
        )

    index = {
        "schema_version": schema_version,
        "generated_by": "aeo-protocol-discovery/generate_agent_skills_index.py",
        "skills": index_entries,
    }
    index_path = target_dir / "index.json"
    if not dry_run:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        written.append(str(index_path))
    return {"index": index, "index_path": str(index_path), "written": written, "dry_run": dry_run}


def verify(publish_root: Path, base_path: str) -> dict[str, Any]:
    """Confirm an already-published index still matches its artifacts."""
    index_path = publish_root / base_path.strip("/") / "index.json"
    if not index_path.is_file():
        raise SystemExit("No index at " + str(index_path))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    problems = []
    for entry in index.get("skills", []):
        url = entry.get("url", "")
        artifact = publish_root / url.lstrip("/")
        if not artifact.is_file():
            problems.append(url + ": artifact missing from the publish root")
            continue
        digest = (entry.get("digest") or {}).get("value") or entry.get("sha256")
        if digest and hashlib.sha256(artifact.read_bytes()).hexdigest() != digest:
            problems.append(url + ": digest does not match the published bytes")
    return {"index": str(index_path), "entries": len(index.get("skills", [])), "problems": problems, "valid": not problems}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skills", required=True, help="Directory containing <name>/SKILL.md artifacts to publish")
    parser.add_argument("--publish-root", required=True, help="Web root that is actually served, e.g. ./public")
    parser.add_argument("--base-path", default=".well-known/agent-skills", help="Path under the publish root")
    parser.add_argument("--schema-version", default="", help="Schema version verified against the current specification")
    parser.add_argument("--confirm-applicable", action="store_true",
                        help="Confirm the site really offers these skills to external agents")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be written without writing")
    parser.add_argument("--verify", action="store_true", help="Verify an existing index against its artifacts")
    args = parser.parse_args()

    publish_root = Path(args.publish_root).resolve()
    if args.verify:
        result = verify(publish_root, args.base_path)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["valid"] else 1)

    if not args.confirm_applicable and not args.dry_run:
        raise SystemExit(
            "Refusing to publish without --confirm-applicable.\n"
            "An Agent Skills index is a public claim that this site offers these capabilities to\n"
            "external agents. Publishing skills that describe actions an outside agent cannot\n"
            "execute against this site is a false signal. Use --dry-run to preview instead."
        )
    if not args.schema_version:
        print(
            "WARNING: no --schema-version given. Verify the current Agent Skills discovery\n"
            "         specification at agentskills.io and record the version you validated against.",
            file=sys.stderr,
        )
    result = build(Path(args.skills).resolve(), publish_root, args.base_path, args.schema_version or "unverified", args.dry_run)
    print(json.dumps({k: v for k, v in result.items() if k != "index"}, indent=2))
    print(("Would write " if args.dry_run else "Wrote ") + str(len(result["written"])) + " files")


if __name__ == "__main__":
    main()
