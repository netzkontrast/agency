"""Spec 175 Slice 2 — derive the whole install surface as ONE typed object.

Slice 1 shipped the `InstallSurface` / `CapabilityRow` / `CommandFile` dataclasses
but nothing populated them (dormant). This is the deriver: every field comes from a
NAMED live source — the registry (capability rows), `pyproject.toml`
(`userconfig_extras`), and the curated slash-command family (Spec 376/148). It
COMPOSES the existing install.py generators (`_marketplace_description`,
`_generate_per_skill_commands`) rather than re-deriving them (rule 2), so the
derived surface and the committed install never drift.

Invariants (Done-When): `set(rows.name) == set(registry.capabilities)`,
`set(userconfig_extras) == set(pyproject.optional-dependencies)`, and
`slash_commands ⊇ {agency, agency-doctor} ∪ {agency-<skill> | walkable}`.
"""
from __future__ import annotations

import os

from ._typed_shapes_wave1 import CapabilityRow, CommandFile, InstallSurface


def pyproject_extras(path: str = "pyproject.toml") -> "set[str]":
    """The keys of ``[project.optional-dependencies]`` — the userConfig extras a
    new extra auto-appears in. Empty set when the file/section is absent."""
    try:
        import tomllib
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, ValueError, ImportError):
        return set()
    return set((data.get("project") or {}).get("optional-dependencies", {}).keys())


def _cap_description(name: str, cap) -> str:
    """A short, non-empty derived description for the README row (home + verb tally;
    the row's load-bearing fields are name + verb_count, this is the gloss)."""
    home = getattr(cap, "home", "") or "capability"
    return f"{name} — {home} ({len(getattr(cap, 'verbs', {}))} verbs)"


def derive_install_surface(engine, *, pyproject_path: str = "pyproject.toml",
                           generated_at: str = "derived") -> InstallSurface:
    """Render the install surface from live sources. ``generated_at`` is supplied
    by the caller (Date.now() is unavailable here / breaks determinism)."""
    from .install import _generate_per_skill_commands, _marketplace_description
    reg = engine.registry

    rows = tuple(
        CapabilityRow(name=n, verb_count=len(reg.get(n).verbs),
                      description=_cap_description(n, reg.get(n)))
        for n in sorted(reg.names()))

    # The curated /agency-<slug> family (Spec 376) + the hand-authored entry
    # commands the family deliberately skips (Spec 148).
    cmds = [CommandFile(name="agency", path="commands/agency.md"),
            CommandFile(name="agency-doctor", path="commands/agency-doctor.md")]
    for path in sorted(_generate_per_skill_commands(reg)):
        base = os.path.basename(path)                    # agency-<slug>.md
        cmds.append(CommandFile(name=base[:-3] if base.endswith(".md") else base,
                                path=path))

    extras = tuple(sorted(pyproject_extras(pyproject_path)))
    return InstallSurface(
        marketplace_desc=_marketplace_description(engine),
        readme_capability_rows=rows,
        slash_commands=tuple(cmds),
        userconfig_extras=extras,
        generated_at=generated_at)
