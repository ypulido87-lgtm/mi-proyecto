"""Locate skills and load module-owned scripts without depending on CWD."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# .../<skills-root>/aeo-agent-readiness/scripts/aeolib/paths.py
SKILLS_ROOT = Path(__file__).resolve().parents[3]

_CACHE: dict[tuple[str, str], object] = {}


def skill_dir(skill: str) -> Path:
    return SKILLS_ROOT / skill


def load_skill_script(skill: str, script: str):
    """Import a script owned by another skill as a module.

    Module scripts must keep every side effect behind `if __name__ == "__main__"`.
    """
    key = (skill, script)
    if key in _CACHE:
        return _CACHE[key]
    path = skill_dir(skill) / "scripts" / script
    if not path.is_file():
        raise FileNotFoundError(f"Missing skill script: {path}")
    mod_name = f"aeo_{skill.replace('-', '_')}_{path.stem}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    _CACHE[key] = module
    return module
