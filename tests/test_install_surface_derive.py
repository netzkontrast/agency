"""Spec 175 Slice 2 — the install-surface deriver invariants.

Every field of the typed `InstallSurface` derives from a NAMED live source; this
asserts the three Done-When relationship invariants so a new capability / extra /
walkable skill auto-appears (and a removed one auto-drops).
"""
from __future__ import annotations

from agency._install_surface import derive_install_surface, pyproject_extras
from agency.engine import Engine
from agency.toolresult import Codes


def test_install_regen_partial_code_exists():
    assert Codes.INSTALL_REGEN_PARTIAL == "install_regen_partial"


def test_readme_rows_equal_the_live_registry_capabilities():
    e = Engine(":memory:")
    try:
        surf = derive_install_surface(e)
        assert {r.name for r in surf.readme_capability_rows} == set(e.registry.names())
        # verb_count derives from the live cap (not a frozen literal)
        for r in surf.readme_capability_rows:
            assert r.verb_count == len(e.registry.get(r.name).verbs)
    finally:
        e.memory.close()


def test_userconfig_extras_equal_pyproject_optional_dependencies():
    e = Engine(":memory:")
    try:
        surf = derive_install_surface(e)
        assert set(surf.userconfig_extras) == pyproject_extras("pyproject.toml")
        assert "dev" in surf.userconfig_extras           # the canonical extra is present
    finally:
        e.memory.close()


def test_slash_commands_superset_entry_plus_walkable():
    e = Engine(":memory:")
    try:
        from agency.install import _generate_per_skill_commands
        surf = derive_install_surface(e)
        names = {c.name for c in surf.slash_commands}
        assert "agency" in names and "agency-doctor" in names
        # every curated /agency-<slug> the install would generate is present
        for path in _generate_per_skill_commands(e.registry):
            base = path.split("/")[-1]
            assert base[:-3] in names, base
    finally:
        e.memory.close()
