#!/usr/bin/env python3
"""robots.txt parser and diagnostics.

Implements the grouping and longest-match precedence rules of RFC 9309.
Diagnostics only: this tool never edits an access policy.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

KNOWN_DIRECTIVES = {"user-agent", "allow", "disallow", "sitemap", "crawl-delay", "host", "content-signal"}

# Documented AI-related crawlers, grouped by the purpose their operator publishes.
# Presence in this list is NOT a recommendation to allow or block any of them.
AI_CRAWLERS = {
    "training": ["GPTBot", "ClaudeBot", "Google-Extended", "Applebot-Extended", "CCBot", "Meta-ExternalAgent", "Bytespider"],
    "search": ["OAI-SearchBot", "PerplexityBot", "Applebot", "Amazonbot", "Bingbot", "Googlebot"],
    "user_action": ["ChatGPT-User", "Claude-User", "Claude-SearchBot", "Perplexity-User"],
}
ALL_AI_CRAWLERS = sorted({name for group in AI_CRAWLERS.values() for name in group})


@dataclass
class Group:
    user_agents: list[str] = field(default_factory=list)
    rules: list[dict[str, str]] = field(default_factory=list)
    crawl_delay: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"user_agents": self.user_agents, "rules": self.rules, "crawl_delay": self.crawl_delay}


@dataclass
class Robots:
    groups: list[Group] = field(default_factory=list)
    sitemaps: list[str] = field(default_factory=list)
    content_signals: list[str] = field(default_factory=list)
    unknown_directives: list[dict[str, Any]] = field(default_factory=list)
    syntax_errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "groups": [g.to_dict() for g in self.groups],
            "sitemaps": self.sitemaps,
            "content_signals": self.content_signals,
            "unknown_directives": self.unknown_directives,
            "syntax_errors": self.syntax_errors,
        }


def parse(text: str) -> Robots:
    """Parse robots.txt into groups. Sitemap and Content-Signal stay global."""
    robots = Robots()
    current: Group | None = None
    expecting_agent = False
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            robots.syntax_errors.append({"line": number, "text": raw_line.strip(), "reason": "Missing colon separator"})
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "user-agent":
            if current is None or not expecting_agent:
                current = Group()
                robots.groups.append(current)
                expecting_agent = True
            current.user_agents.append(value)
            continue
        expecting_agent = False
        if key in ("allow", "disallow"):
            if current is None:
                robots.syntax_errors.append(
                    {"line": number, "text": raw_line.strip(), "reason": key + " before any User-agent group"}
                )
                continue
            current.rules.append({"directive": key, "path": value})
        elif key == "sitemap":
            robots.sitemaps.append(value)
        elif key == "content-signal":
            robots.content_signals.append(value)
        elif key == "crawl-delay":
            if current is not None:
                current.crawl_delay = value
        elif key == "host":
            continue
        else:
            robots.unknown_directives.append({"line": number, "directive": key, "value": value})
    return robots


def group_for(robots: Robots, user_agent: str) -> Group | None:
    """RFC 9309: the most specific matching group wins, with * as the fallback."""
    target = user_agent.lower()
    best: tuple[int, Group] | None = None
    wildcard: Group | None = None
    for group in robots.groups:
        for agent in group.user_agents:
            agent_lower = agent.lower()
            if agent_lower == "*":
                if wildcard is None:
                    wildcard = group
            elif target.startswith(agent_lower) or agent_lower in target:
                if best is None or len(agent_lower) > best[0]:
                    best = (len(agent_lower), group)
    if best is not None:
        return best[1]
    return wildcard


def _pattern_match(pattern: str, path: str) -> int | None:
    """Return the specificity of a matching robots path pattern, else None."""
    if pattern == "":
        return None
    anchored_end = pattern.endswith("$")
    core = pattern[:-1] if anchored_end else pattern
    regex = "".join(".*" if char == "*" else re.escape(char) for char in core)
    match = re.match(regex + ("$" if anchored_end else ""), path)
    if match is None:
        return None
    return len(core.replace("*", ""))


def is_allowed(robots: Robots, user_agent: str, path: str) -> dict[str, Any]:
    """Evaluate one path: longest match wins, Allow breaks ties."""
    group = group_for(robots, user_agent)
    if group is None:
        return {"allowed": True, "reason": "No matching group; default allow", "rule": None, "matched_user_agents": []}
    resolved = unquote(urlsplit(path).path or "/")
    best: tuple[int, str, str] | None = None
    for rule in group.rules:
        length = _pattern_match(rule["path"], resolved)
        if length is None:
            continue
        if best is None or length > best[0] or (length == best[0] and rule["directive"] == "allow"):
            best = (length, rule["directive"], rule["path"])
    if best is None:
        return {
            "allowed": True,
            "reason": "No rule matched; default allow",
            "rule": None,
            "matched_user_agents": group.user_agents,
        }
    return {
        "allowed": best[1] == "allow",
        "reason": "Longest match: " + best[1] + ": " + best[2],
        "rule": {"directive": best[1], "path": best[2]},
        "matched_user_agents": group.user_agents,
    }


def ai_policy(robots: Robots) -> dict[str, Any]:
    """Report the declared policy for documented AI crawlers. Never prescribes one."""
    policy: dict[str, Any] = {}
    for name in ALL_AI_CRAWLERS:
        group = group_for(robots, name)
        explicit = bool(group and any(a.lower() != "*" and a.lower() in name.lower() for a in group.user_agents))
        verdict = is_allowed(robots, name, "/")
        policy[name] = {
            "purpose": [p for p, names in AI_CRAWLERS.items() if name in names],
            "explicit_rule": explicit,
            "homepage_allowed": verdict["allowed"],
            "reason": verdict["reason"],
        }
    return policy


def diagnose(text: str) -> dict[str, Any]:
    robots = parse(text)
    conflicts = []
    for group in robots.groups:
        seen: dict[str, set[str]] = {}
        for rule in group.rules:
            seen.setdefault(rule["path"], set()).add(rule["directive"])
        for path, directives in sorted(seen.items()):
            if len(directives) > 1:
                conflicts.append({"user_agents": group.user_agents, "path": path, "directives": sorted(directives)})
    blocking = [g.user_agents for g in robots.groups if any(r["directive"] == "disallow" and r["path"] == "/" for r in g.rules)]
    return {
        **robots.to_dict(),
        "conflicts": conflicts,
        "groups_blocking_entire_site": blocking,
        "ai_policy": ai_policy(robots),
        "has_sitemap_reference": bool(robots.sitemaps),
    }


def load(source: str) -> str:
    if source.startswith(("http://", "https://")):
        engine = Path(__file__).resolve().parents[2] / "aeo-agent-readiness" / "scripts"
        sys.path.insert(0, str(engine))
        from aeolib.fetch import fetch

        response = fetch(source, accept="text/plain")
        if not response.ok:
            raise SystemExit("robots.txt not retrievable: HTTP " + str(response.status) + " " + (response.error or ""))
        return response.text
    return Path(source).read_text(encoding="utf-8", errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse and diagnose a robots.txt file or URL")
    parser.add_argument("source", help="Path or URL to robots.txt")
    parser.add_argument("--user-agent", help="Evaluate a single user-agent against --path")
    parser.add_argument("--path", default="/", help="Path to evaluate (default: /)")
    args = parser.parse_args()
    text = load(args.source)
    if args.user_agent:
        print(json.dumps(is_allowed(parse(text), args.user_agent, args.path), indent=2))
    else:
        print(json.dumps(diagnose(text), indent=2))


if __name__ == "__main__":
    main()
