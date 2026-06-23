"""Spec 390 D2 — param_shapes substrate: surface a param's required nested
object/array shape in the wire description (the get_schema-visible surface), so a
fresh agent sees `context: [{id, text}]` instead of a bare `any[]`.

Mirrors Spec 284's projected-enum surfacing (`param_enums` → "Enums:" hint);
`param_shapes` folds a "Shapes:" hint into the tool description the same way.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _wired_tool(mcp, name: str):
    for provider in getattr(mcp, "providers", ()):
        for key, tool in getattr(provider, "_components", {}).items():
            if key.startswith("tool:") and getattr(tool, "name", "") == name:
                return tool
    return None


def test_wire_surfaces_param_shape_in_description() -> None:
    eng = Engine(tempfile.mktemp(suffix=".db"))
    mcp = eng.build_mcp(codemode=True)
    try:
        tool = _wired_tool(mcp, "capability_discover_ask")
        assert tool is not None
        desc = tool.description or ""
        # the get_schema-visible description names the param's nested shape …
        assert "Shapes:" in desc, desc
        assert "context" in desc and "{id, text}" in desc, desc
    finally:
        eng.memory.close()


def test_param_shapes_does_not_reject_rich_input_at_the_wire() -> None:
    # Shapes is a documentation hint (description-only) — it must NOT add wire-level
    # validation; a well-formed context list still flows through and the verb runs.
    eng = Engine(tempfile.mktemp(suffix=".db"))
    mcp = eng.build_mcp(codemode=True)
    try:
        iid = eng.intent.capture("spec 390", "param shapes", "verified")
        eng.intent.confirm(iid)
        res, _ = eng.registry.invoke(
            eng.memory, iid, "discover", "ask",
            context=[{"id": "a", "text": "Option A"}, {"id": "b", "text": "Option B"}])
        assert res.get("payload") or res.get("question_id") or res.get("ok", True) is not False, res
    finally:
        eng.memory.close()
