"""Spec 371 Slices 2-3 — load a capability's v2 Skill + read its provenance.

A capability's skill data DERIVES from its module docstring (rule 2 — no
duplicated authored file). :func:`load_skill` returns that derived, schema-valid
v2 Skill — the **back-compat shim** (``owner="auto"``): every existing capability
resolves to a valid `Skill` with no committed file. When a capability SHIPS a
``<cap>/skill.yaml`` (the A6 authored override), :func:`load_skill` parses +
validates THAT instead (``owner="capability"``) — the same v2 schema gates both.

:func:`skill_source` is the Slice-3 **read API**: where a capability's skill data
came from (``source ∈ derived|authored``, ``owner ∈ auto|capability``) + the
``source_stamp``. The renderer (373) and `skills.source` (the verb) consume it.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from ._skill_parse import ParseResult, parse_skill
from .toolresult import Codes


def _capabilities_root(override: Optional[str] = None) -> str:
    """The directory holding ``<cap>/`` folders. Overridable (tests / a foreign
    capability root); defaults to this package's ``capabilities/``."""
    if override:
        return override
    return str(Path(__file__).resolve().parent / "capabilities")


def _skill_name(cap_name: str) -> str:
    """The spec-legal Agent-Skill name (Spec 080 — hyphens, no underscores)."""
    return cap_name.replace("_", "-")


def _yaml_path(cap_name: str, root: str) -> str:
    return os.path.join(root, cap_name, "skill.yaml")


def derive_skill_dict(doc, cap_name: str) -> dict:
    """The back-compat shim: a minimal, schema-valid v2 ``capability`` Skill dict
    built from a capability's docstring-derived SkillDoc. No authored duplication
    (rule 2) — every field rides the existing SkillDoc (``description`` /
    ``overview`` / ``triggers`` / ``canonical_example`` / ``red_flags``). The
    ``capability`` type's required core is just ``description`` (R1), so the
    derived Skill always validates; the richer fields ride along when the
    docstring carried them (so the 373 renderer can inline them, A1)."""
    name = _skill_name(cap_name)
    d: dict = {
        "name": name,
        "kind": "capability",
        "type": "capability",
        "owner": "auto",
        "description": getattr(doc, "description", "")
        or f"Use when working with the {name} capability.",
        "source_stamp": f"derived:{cap_name}",
    }
    overview = getattr(doc, "overview", "")
    if overview:
        d["overview"] = overview
    triggers = getattr(doc, "triggers", None) or []
    if triggers:
        d["when_to_use"] = "; ".join(triggers)
    example = getattr(doc, "canonical_example", "")
    if example:
        d["examples"] = [{"input": f"{name} usage", "output": example}]
    red_flags = getattr(doc, "red_flags", None) or []
    if red_flags:
        d["common_mistakes"] = [
            {"symptom": r, "counter": "see the capability's red flags"}
            for r in red_flags]
    return d


def load_skill(cap_name: str, doc=None, *,
               capabilities_root: Optional[str] = None) -> ParseResult:
    """Load a capability's v2 Skill. A capability that SHIPS ``<cap>/skill.yaml``
    (the A6 authored override) gets it parsed + validated (``owner="capability"``);
    otherwise the Skill is DERIVED from its SkillDoc (``owner="auto"``, the
    back-compat shim). Either path returns a `parse_skill`-validated `Skill` (or a
    typed `ParseResult` failure), so a malformed authored skill fails the same way
    a malformed derived one would."""
    root = _capabilities_root(capabilities_root)
    yaml_path = _yaml_path(cap_name, root)
    if os.path.isfile(yaml_path):
        import yaml
        data = yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8")) or {}
        if isinstance(data, dict):
            data.setdefault("owner", "capability")
            data.setdefault("source_stamp", f"authored:{cap_name}/skill.yaml")
        return parse_skill(data)
    if doc is None:
        return ParseResult.failure(
            Codes.SKILL_PARSE_INVALID,
            f"capability {cap_name!r} ships no skill.yaml and no SkillDoc "
            f"to derive a Skill from")
    return parse_skill(derive_skill_dict(doc, cap_name))


def skill_source(cap_name: str, *,
                 capabilities_root: Optional[str] = None) -> dict:
    """Spec 371 Slice 3 — the source/owner/source_stamp READ API: WHERE a
    capability's skill data comes from. ``source ∈ authored|derived`` (a shipped
    ``skill.yaml`` is authored, A6); ``owner ∈ capability|auto`` (A6)."""
    root = _capabilities_root(capabilities_root)
    if os.path.isfile(_yaml_path(cap_name, root)):
        return {"name": _skill_name(cap_name), "owner": "capability",
                "source": "authored",
                "source_stamp": f"authored:{cap_name}/skill.yaml"}
    return {"name": _skill_name(cap_name), "owner": "auto",
            "source": "derived", "source_stamp": f"derived:{cap_name}"}
