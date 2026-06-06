"""Spec 057 — analyzer rule-axis registry.

Each analyzer module declares its own `AXIS_PREFIXES`; `_main` unions them into a
prefix→axis registry at import time. Adding a tool = drop in a wrapper, no central
edit. These tests pin the registry contents, longest-prefix-first lookup, and
cross-axis collision detection.
"""
from __future__ import annotations

import types

import pytest

from agency.capabilities.analyze import _main
from agency.capabilities.analyze._main import _build_axis_registry, _rule_axis


def test_registry_contains_every_shipped_module_prefix():
    # internal axes
    assert _rule_axis("Q001") == "quality"
    assert _rule_axis("S001") == "security"
    assert _rule_axis("P001") == "performance"
    assert _rule_axis("A001") == "architecture"
    assert _rule_axis("IP001") == "paths"
    # external wrappers (Spec 050): ruff → quality, bandit → security
    assert _rule_axis("E501") == "quality"
    assert _rule_axis("F401") == "quality"
    assert _rule_axis("W605") == "quality"
    assert _rule_axis("B101") == "security"


def test_longest_prefix_wins():
    # RUF / SIM / TRY are 3-letter ruff codes; they must resolve to quality, not
    # collapse to a (nonexistent) one-letter prefix.
    assert _rule_axis("RUF100") == "quality"
    assert _rule_axis("SIM105") == "quality"
    assert _rule_axis("TRY300") == "quality"
    # IP (paths) must beat a hypothetical one-letter "I" (ruff imports → quality)
    assert _rule_axis("IP002") == "paths"
    assert _rule_axis("I001") == "quality"


def test_unknown_prefix_maps_to_empty():
    assert _rule_axis("ZZ999") == ""
    assert _rule_axis("") == ""


def test_quality_axis_unions_internal_and_ruff():
    # The 'quality' axis must include BOTH internal Q and ruff E/F/W.
    quality_codes = [c for c in ("Q001", "E501", "F401", "W605", "RUF100")
                     if _rule_axis(c) == "quality"]
    assert quality_codes == ["Q001", "E501", "F401", "W605", "RUF100"]


def test_security_axis_unions_internal_and_bandit():
    assert _rule_axis("S001") == "security" and _rule_axis("B101") == "security"


def test_collision_across_axes_raises():
    mod_a = types.SimpleNamespace(__name__="mod_a", AXIS_PREFIXES={"quality": frozenset({"X"})})
    mod_b = types.SimpleNamespace(__name__="mod_b", AXIS_PREFIXES={"security": frozenset({"X"})})
    with pytest.raises(ValueError, match="collision"):
        _build_axis_registry(modules=(mod_a, mod_b))


def test_same_axis_overlap_is_idempotent():
    mod_a = types.SimpleNamespace(__name__="mod_a", AXIS_PREFIXES={"quality": frozenset({"X"})})
    mod_b = types.SimpleNamespace(__name__="mod_b", AXIS_PREFIXES={"quality": frozenset({"X", "Y"})})
    lookup, _ = _build_axis_registry(modules=(mod_a, mod_b))
    assert lookup[1]["X"] == "quality" and lookup[1]["Y"] == "quality"


def test_live_registry_has_no_collisions():
    # The shipped modules must build cleanly (regression: a future tool that
    # claims an existing prefix for a new axis fails CI here).
    lookup, max_len = _build_axis_registry()
    assert max_len >= 3  # RUF/SIM/TRY are 3-char
    assert lookup[1]["Q"] == "quality" and lookup[2]["IP"] == "paths"


def test_module_constant_is_the_single_source():
    # _main no longer carries a hardcoded prefix map; the registry is built from
    # each module's AXIS_PREFIXES.
    from agency.capabilities.analyze import _quality, _ruff, _bandit
    assert _quality.AXIS_PREFIXES == {"quality": frozenset({"Q"})}
    assert "RUF" in _ruff.AXIS_PREFIXES["quality"]
    assert _bandit.AXIS_PREFIXES == {"security": frozenset({"B"})}
    assert hasattr(_main, "_AXIS_LOOKUP")
