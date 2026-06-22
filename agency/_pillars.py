"""Spec 375 — the pillar-skill source loader.

The three non-capability concepts of CORE.md's four (Intent · Lifecycle · Memory)
are first-class skills, authored as committed `skill.yaml` of `type: pillar` under
`agency/pillars/`. Unlike capability skills (derived from a capability's docstring
SkillDoc), pillars teach a CONCEPT — there is no `capabilities/<cap>/` folder to
hang them on, so they live as committed source the installer renders.

`load_pillars()` is the single read point: it globs the source dir, loads each
YAML, and validates it against the 371 schema (`parse_skill`). A malformed pillar
is a fail-fast `ValueError` — a broken concept skill must never silently vanish
from the install (the "never silently drop captured data" doctrine applied to the
authored surface). Pure read + validate, deterministic order (sorted by name) so
`install regen` is diff-free (A7).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from ._skill_parse import parse_skill

# The committed pillar source. Ships inside the package so the renderer finds it
# whether running from a checkout or an installed wheel.
PILLARS_DIR = Path(__file__).parent / "pillars"


@lru_cache(maxsize=None)
def load_pillars(directory: Path | str | None = None) -> list[dict]:
    """Load + validate every committed pillar `skill.yaml`.

    Returns the pillar dicts sorted by `name` (deterministic — A7). Raises
    `ValueError` if any pillar fails the 371 schema, naming the offending file so
    a broken pillar fails the install loudly rather than disappearing from it.

    Cached (the source is committed + static) — the skill listing calls this on a
    hot path (`_all_skills` → `skills.find`, 100+ call sites), so the 3-file YAML
    read happens once per process, not per `find`.
    """
    root = Path(directory) if directory is not None else PILLARS_DIR
    if not root.exists():
        return []
    pillars: list[dict] = []
    for path in sorted(root.glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            raise ValueError(f"pillar {path.name!r} must be a YAML mapping")
        res = parse_skill(data)
        if not res.ok:
            raise ValueError(
                f"pillar {path.name!r} failed the 371 schema "
                f"({res.code}): {res.message}")
        pillars.append(data)
    pillars.sort(key=lambda d: d.get("name", ""))
    return pillars


def lint_pillars(verbs_index: dict | None = None,
                 directory: Path | str | None = None) -> list[dict]:
    """Spec 377 Slice 2 — strict-lint every committed pillar against the full
    skill-schema contract (per-type · self-containment · no-stub · verb-resolves),
    beyond the parse-time schema check `load_pillars` already enforces. Returns
    ``[{name, violations}]`` for any pillar that FAILS (empty ⇒ all clean).

    The pillars are the block-set exemplars (Spec 375): `install.generate` and
    `check-drift` refuse to ship a pillar that fails strict lint. Lazy import of
    the lint rule keeps the pillar loader free of the capability surface."""
    from .capabilities.plugin.clusters.lint import lint_skill_schema
    failures: list[dict] = []
    for p in load_pillars(directory):
        res = lint_skill_schema(p, verbs_index=verbs_index)
        if not res["ok"]:
            failures.append({"name": p.get("name", "?"),
                             "violations": res["violations"]})
    return failures
