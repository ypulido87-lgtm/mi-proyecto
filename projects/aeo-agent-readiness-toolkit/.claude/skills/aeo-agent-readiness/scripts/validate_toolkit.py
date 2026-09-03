#!/usr/bin/env python3
"""Validate the toolkit against the Agent Skills conventions and its own rules.

Checks front matter, naming, size, referenced paths, internal links, machine
portability, and the absence of published false capability signals.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.S)
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_BODY_LINES = 500

# A path that only exists on the author's machine makes the toolkit unusable
# anywhere else, which is the portability requirement.
# Assembled from fragments so that this file does not match its own pattern.
_USERS, _HOME = "Us" + "ers", "ho" + "me"
ABSOLUTE_PATH = re.compile(
    r"(?:[A-Za-z]:[\\/]" + _USERS + r"[\\/]|/" + _HOME + r"/[a-z]|/" + _USERS + r"/)", re.I
)
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)#][^)]*)\)")
SCRIPT_REFERENCE = re.compile(r"`?(scripts/[A-Za-z0-9_./-]+\.py)`?")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str] | tuple[None, str]:
    match = FRONTMATTER.match(text)
    if not match:
        return None, text
    fields: dict[str, str] = {}
    key: str | None = None
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^[A-Za-z0-9_-]+\s*:", line):
            key, _, value = line.partition(":")
            key = key.strip()
            fields[key] = value.strip().strip("'\"")
        elif key:
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields, text[match.end():]


def validate_skill(skill_dir: Path, skills_root: Path) -> list[str]:
    errors: list[str] = []
    label = skill_dir.name
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return [label + ": missing SKILL.md"]

    text = skill_file.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(text)
    if fields is None:
        return [label + ": missing or malformed YAML front matter"]

    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name:
        errors.append(label + ": front matter has no name")
    else:
        if not NAME_PATTERN.match(name):
            errors.append(label + ": name '" + name + "' is not lowercase kebab-case")
        if name != skill_dir.name:
            errors.append(label + ": name '" + name + "' does not match its directory")
        if len(name) > MAX_NAME:
            errors.append(label + ": name exceeds " + str(MAX_NAME) + " characters")
    if not description:
        errors.append(label + ": front matter has no description")
    else:
        if len(description) > MAX_DESCRIPTION:
            errors.append(label + ": description exceeds " + str(MAX_DESCRIPTION) + " characters")
        if len(description) < 40:
            errors.append(label + ": description is too short to drive skill selection")
        if not re.search(r"\buse\b|\bwhen\b", description, re.I):
            errors.append(label + ": description does not say when to use the skill")

    body_lines = body.count("\n")
    if body_lines > MAX_BODY_LINES:
        errors.append(label + ": SKILL.md body is " + str(body_lines) + " lines (limit " + str(MAX_BODY_LINES) + ")")
    if body_lines < 15:
        errors.append(label + ": SKILL.md body is only " + str(body_lines) + " lines; too thin to be operational")

    for match in ABSOLUTE_PATH.finditer(text):
        errors.append(label + ": SKILL.md contains a machine-specific absolute path near '" + match.group(0) + "'")

    # Referenced scripts and reference files must exist relative to the skill.
    for reference in set(SCRIPT_REFERENCE.findall(text)):
        candidate = skill_dir / reference
        alternate = skills_root / "aeo-agent-readiness" / reference
        if not candidate.is_file() and not alternate.is_file():
            errors.append(label + ": references a missing script '" + reference + "'")
    for target in set(MARKDOWN_LINK.findall(text)):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (skill_dir / target).resolve()
        if not resolved.exists():
            errors.append(label + ": broken internal link '" + target + "'")
    return errors


def validate_scripts(skills_root: Path) -> list[str]:
    """Every script must import cleanly and keep side effects behind main()."""
    errors: list[str] = []
    for script in sorted(skills_root.glob("*/scripts/**/*.py")):
        source = script.read_text(encoding="utf-8", errors="replace")
        try:
            compile(source, str(script), "exec")
        except SyntaxError as exc:
            errors.append(str(script.relative_to(skills_root)) + ": syntax error: " + str(exc))
            continue
        if script.name == "__init__.py":
            continue
        top_level_calls = re.findall(r"^(?!def |class |if |@|\s)([a-z_][A-Za-z0-9_]*)\s*\(", source, re.M)
        risky = [call for call in top_level_calls if call not in ("print",)]
        if risky and "__name__" not in source:
            errors.append(str(script.relative_to(skills_root)) + ": module-level call(s) " + ", ".join(sorted(set(risky))) + " run on import")
        if ABSOLUTE_PATH.search(source):
            errors.append(str(script.relative_to(skills_root)) + ": contains a machine-specific absolute path")
    return errors


def validate_no_false_signals(repo_root: Path) -> list[str]:
    """A published discovery index must resolve to artifacts that exist."""
    errors: list[str] = []
    for index_path in repo_root.rglob(".well-known/agent-skills/index.json"):
        if any(part in (".git", "node_modules", ".tmp") for part in index_path.parts):
            continue
        publish_root = index_path.parents[2]
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(str(index_path) + ": invalid JSON: " + str(exc))
            continue
        for entry in index.get("skills", []):
            url = entry.get("url", "")
            if not url:
                continue
            artifact = publish_root / url.lstrip("/")
            if not artifact.is_file():
                errors.append(
                    str(index_path) + ": references '" + url + "' which is not published. "
                    "A discovery index pointing at missing artifacts is a false capability signal."
                )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the AEO toolkit")
    parser.add_argument("--skills", default=None, help="Skills root (default: the directory containing this toolkit)")
    parser.add_argument("--repo", default=None, help="Repository root to scan for published false signals")
    args = parser.parse_args()

    skills_root = Path(args.skills).resolve() if args.skills else Path(__file__).resolve().parents[2]
    repo_root = Path(args.repo).resolve() if args.repo else skills_root.parents[1]

    skill_dirs = sorted(d for d in skills_root.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
    if not skill_dirs:
        raise SystemExit("No skills found under " + str(skills_root))

    errors: list[str] = []
    for skill_dir in skill_dirs:
        errors.extend(validate_skill(skill_dir, skills_root))
    errors.extend(validate_scripts(skills_root))
    errors.extend(validate_no_false_signals(repo_root))

    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print("  - " + error)
        raise SystemExit(1)
    print("Validated " + str(len(skill_dirs)) + " skills and all scripts under " + str(skills_root))
    for skill_dir in skill_dirs:
        scripts = len(list((skill_dir / "scripts").glob("**/*.py"))) if (skill_dir / "scripts").is_dir() else 0
        print("  - " + skill_dir.name + " (" + str(scripts) + " scripts)")


if __name__ == "__main__":
    main()
