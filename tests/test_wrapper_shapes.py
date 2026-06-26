"""Spec 166 Slice 2 — analyzer-wrapper registry deriver invariants.

`derive_wrapper_shapes` + `external_tools` read each analyzer wrapper module's
`EXTERNAL_TOOL` / `AXIS_PREFIXES` so the external-tool set and the typed
`WrapperShape` registry DERIVE from the modules — a new wrapper auto-appears and
the doctor's `analyze_extras` is never hand-listed.
"""
from __future__ import annotations

from agency._typed_shapes_wave1_part2 import WrapperShape
from agency._wrapper_shapes import (derive_wrapper_shapes, external_tools,
                                    wrapper_shapes_summary)


class _Mod:
    def __init__(self, name, tool, prefixes, extra="analyze"):
        self.__name__ = name
        if tool is not None:
            self.EXTERNAL_TOOL = tool
            self.EXTERNAL_EXTRA = extra
        self.AXIS_PREFIXES = prefixes


def test_external_tools_derive_from_the_modules():
    # the live external-tool set is exactly the modules declaring EXTERNAL_TOOL
    tools = external_tools()
    assert set(tools) == {"ruff", "bandit", "radon"}
    # derived + sorted, never hand-listed
    assert list(tools) == sorted(tools)


def test_wrapper_shapes_are_typed_and_carry_prefixes():
    shapes = derive_wrapper_shapes()
    assert shapes and all(isinstance(s, WrapperShape) for s in shapes)
    # every shape carries at least one prefix (the WrapperShape invariant)
    assert all(s.axis_prefixes for s in shapes)
    # ruff + bandit emit prefixes; radon (prefix-less) is a tool but not a shape
    assert {s.tool_name for s in shapes} == {"ruff", "bandit"}


def test_a_new_wrapper_auto_appears():
    mods = (_Mod("_ruff", "ruff", {"quality": frozenset({"E"})}),
            _Mod("_mypy", "mypy", {"types": frozenset({"MX"})}))
    assert set(external_tools(mods)) == {"mypy", "ruff"}
    shape_tools = {s.tool_name for s in derive_wrapper_shapes(mods)}
    assert shape_tools == {"ruff", "mypy"}


def test_prefixless_external_tool_is_a_tool_but_not_a_shape():
    mods = (_Mod("_radon", "radon", {}),)   # external, no prefixes
    assert external_tools(mods) == ("radon",)
    assert derive_wrapper_shapes(mods) == ()


def test_summary_external_tools_match_doctor_derivation():
    summ = wrapper_shapes_summary()
    assert summ["ready"] is True
    assert set(summ["external_tools"]) == set(external_tools())
    assert set(summ["shape_tools"]) <= set(summ["external_tools"])
