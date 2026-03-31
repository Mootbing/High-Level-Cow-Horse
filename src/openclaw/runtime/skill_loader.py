"""Dynamic skill discovery and loading.

Scans the ``skills/`` directory at the repository root for subdirectories
that contain a ``skill.yaml`` manifest and a ``handler.py`` module.  Each
handler must define exactly one :class:`~openclaw.runtime.skill_base.BaseSkill`
subclass, which is registered by the ``name`` declared in ``skill.yaml``.

Directory layout::

    skills/
        designer/
            skill.yaml        # name, description, tier, timeout, max_concurrent
            handler.py        # class DesignerSkill(BaseSkill): ...
        engineer/
            skill.yaml
            handler.py
        ...
"""

from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from typing import Any

import structlog
import yaml

from openclaw.runtime.skill_base import BaseSkill

logger = structlog.get_logger()

# Resolve ``<repo_root>/skills/`` regardless of the cwd at import time.
# ``skill_loader.py`` lives at ``<repo>/src/openclaw/runtime/skill_loader.py``,
# so walking four parents up gets us to the repo root.
SKILLS_DIR: Path = Path(__file__).resolve().parents[3] / "skills"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_skill_metadata(name: str) -> dict[str, Any]:
    """Read and return the parsed ``skill.yaml`` for a single skill.

    Raises ``FileNotFoundError`` if the skill directory or manifest is
    missing.
    """
    yaml_path = SKILLS_DIR / name / "skill.yaml"
    if not yaml_path.is_file():
        raise FileNotFoundError(f"No skill.yaml found at {yaml_path}")
    with open(yaml_path, "r") as fh:
        meta: dict[str, Any] = yaml.safe_load(fh) or {}
    return meta


def load_skill(name: str) -> type[BaseSkill]:
    """Load a single skill by directory name.

    Returns the ``BaseSkill`` subclass found in ``skills/<name>/handler.py``
    with class-level attributes patched from ``skill.yaml`` metadata.

    Raises ``FileNotFoundError`` if either the handler or the manifest is
    missing, and ``RuntimeError`` if no ``BaseSkill`` subclass is found in
    the handler module.
    """
    skill_dir = SKILLS_DIR / name
    handler_path = skill_dir / "handler.py"
    if not handler_path.is_file():
        raise FileNotFoundError(f"No handler.py found at {handler_path}")

    meta = get_skill_metadata(name)

    # Dynamically import handler.py as a unique module
    module_name = f"openclaw_skill_{name}"
    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot create module spec for {handler_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find the BaseSkill subclass defined in the module
    skill_cls: type[BaseSkill] | None = None
    for _attr_name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, BaseSkill) and obj is not BaseSkill:
            skill_cls = obj
            break

    if skill_cls is None:
        raise RuntimeError(
            f"No BaseSkill subclass found in {handler_path}. "
            "Each handler.py must define exactly one BaseSkill subclass."
        )

    # Patch class-level metadata from skill.yaml onto the class.
    # skill.yaml values take priority over class defaults but the class
    # can still override them in __init__ if needed.
    _YAML_TO_ATTR = {
        "name": "name",
        "description": "description",
        "tier": "tier",
        "timeout": "timeout",
        "system_prompt": "system_prompt",
        "model": "model",
        "max_context_messages": "max_context_messages",
        "max_turns": "max_turns",
    }
    for yaml_key, attr in _YAML_TO_ATTR.items():
        if yaml_key in meta:
            setattr(skill_cls, attr, meta[yaml_key])

    logger.info(
        "skill_loaded",
        skill=meta.get("name", name),
        tier=meta.get("tier", skill_cls.tier),
        handler=str(handler_path),
    )
    return skill_cls


def load_all_skills() -> dict[str, type[BaseSkill]]:
    """Scan ``SKILLS_DIR`` and load every valid skill.

    Returns a dict mapping ``skill_name`` (from ``skill.yaml``) to the
    corresponding ``BaseSkill`` subclass.

    Skills that fail to load are logged and skipped so one broken skill
    cannot prevent the rest of the system from starting.
    """
    registry: dict[str, type[BaseSkill]] = {}

    if not SKILLS_DIR.is_dir():
        logger.warning("skills_dir_missing", path=str(SKILLS_DIR))
        return registry

    for child in sorted(SKILLS_DIR.iterdir()):
        if not child.is_dir():
            continue
        # Require both skill.yaml and handler.py
        if not (child / "skill.yaml").is_file() or not (child / "handler.py").is_file():
            logger.debug("skipping_non_skill_dir", path=str(child))
            continue
        try:
            skill_cls = load_skill(child.name)
            registry[skill_cls.name] = skill_cls
        except Exception as exc:
            logger.error(
                "skill_load_failed",
                directory=child.name,
                error=str(exc),
            )

    logger.info("all_skills_loaded", skills=list(registry.keys()), count=len(registry))
    return registry
