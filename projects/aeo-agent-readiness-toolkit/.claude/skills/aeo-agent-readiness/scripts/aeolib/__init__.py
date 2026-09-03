"""Shared engine library for the AEO & Agent Readiness toolkit.

The library lives inside the orchestrator skill so that copying `.claude/skills/`
into another repository carries the whole toolkit with it. Module-specific tools
stay inside their own skill and are loaded through `aeolib.paths.load_skill_script`.
"""
__all__ = ["paths", "fetch", "project", "checks", "scoring", "report"]
