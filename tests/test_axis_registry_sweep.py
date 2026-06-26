"""Spec 172 Slice 2 — analyzer-axis registry deriver invariants.

`derive_axis_registry` composes the live analyzer wrappers' `AXIS_PREFIXES` into
the typed `AxisRegistry` — longest-prefix-first, order-independent, with collision
+ malformed guards. A new analyzer's prefixes auto-appear; a colliding one is
rejected.
"""
from __future__ import annotations

import itertools

from agency._axis_registry_sweep import (axis_registry_summary,
                                         derive_axis_registry,
                                         detect_collisions)
from agency._typed_shapes_wave1_part2 import AxisRegistry
from agency.toolresult import Codes


# ── fixture analyzer modules (duck-typed: only AXIS_PREFIXES + __name__ used) ──
class _Mod:
    def __init__(self, name, prefixes):
        self.__name__ = name
        self.AXIS_PREFIXES = prefixes


def test_axis_codes_exist():
    assert Codes.AXIS_PREFIX_COLLISION == "axis_prefix_collision"
    assert Codes.AXIS_PREFIX_MALFORMED == "axis_prefix_malformed"


def test_live_registry_has_no_collisions():
    # the real installed analyzer set must build clean
    assert detect_collisions() == []
    reg = derive_axis_registry()
    assert isinstance(reg, AxisRegistry)
    summ = axis_registry_summary()
    assert summ["ready"] is True and summ["collision_count"] == 0


def test_longest_prefix_first_resolution():
    mods = (_Mod("a_mod", {"arch": frozenset({"A"})}),
            _Mod("a0_mod", {"arch0": frozenset({"A0"})}))
    reg = derive_axis_registry(mods)
    # "A001" must resolve to the owner of the LONGER prefix "A0"
    assert reg.resolve("A001") == "arch0"
    assert reg.resolve("A1") == "arch"


def test_registry_is_order_independent():
    base = [_Mod("q", {"quality": frozenset({"Q"})}),
            _Mod("s", {"security": frozenset({"S"})}),
            _Mod("p", {"paths": frozenset({"IP"})})]
    results = {derive_axis_registry(tuple(perm)).prefixes
               for perm in itertools.permutations(base)}
    # every load-order permutation yields the identical prefixes tuple
    assert len(results) == 1


def test_colliding_fixture_is_rejected():
    mods = (_Mod("ruff", {"quality": frozenset({"R"})}),
            _Mod("custom", {"security": frozenset({"R"})}))
    cols = detect_collisions(mods)
    assert cols and cols[0][0] == "R"
    summ = axis_registry_summary(mods)
    assert summ["ready"] is False
    assert summ["code"] == Codes.AXIS_PREFIX_COLLISION


def test_malformed_prefix_fails_fast():
    mods = (_Mod("bad", {"axis": frozenset({""})}),)   # empty prefix
    summ = axis_registry_summary(mods)
    assert summ["ready"] is False
    assert summ["code"] == Codes.AXIS_PREFIX_MALFORMED


def test_same_axis_overlap_is_not_a_collision():
    # two modules declaring the SAME prefix for the SAME axis is idempotent
    mods = (_Mod("a", {"quality": frozenset({"Q"})}),
            _Mod("b", {"quality": frozenset({"Q"})}))
    assert detect_collisions(mods) == []
    reg = derive_axis_registry(mods)
    assert reg.resolve("Q123") == "quality"
