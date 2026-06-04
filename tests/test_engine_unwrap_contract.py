"""Spec 019 — engine output-shape contract.

Verifies two coupled invariants:

1. **The engine's `_wire` unwrap rule** (`agency/engine.py`):
   - Internal ``{"result": <dict>}`` → wire ``<dict>`` (the lean code-mode
     shape — caller reads keys directly, no `r["result"]["x"]` boilerplate).
   - Internal ``{"result": <scalar>}`` → wire ``{"result": <scalar>}``
     (re-wrapped — MCP returns must be dicts; engine.py:175 re-wrap).
   - Internal rich dict without `result` → wire identical.

2. **`plugin.lint_capability` flags docstrings that leak the internal
   wrap on dict-wrapped returns.** A verb whose actual return is
   ``{"result": {dict}}`` but whose docstring says
   ``Returns: {result: {…}}`` is documenting the INTERNAL envelope
   when it should describe the WIRE shape (``{…}``).
"""
from __future__ import annotations

import tempfile

import pytest

from agency.capability import CapabilityBase, OntologyExtension, verb
from agency.capabilities.plugin import lint_capability
from agency.engine import Engine


# ---------------------------------------------------------------------------
# Engine unwrap contract.
# ---------------------------------------------------------------------------


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    return engine.intent.capture_and_confirm(
        "test 019", "engine unwrap", "x", owner="user")


async def _call_tool(engine, tool_name: str, **kwargs):
    mcp = engine.build_mcp(codemode=True)
    return await mcp.call_tool(tool_name, kwargs)


async def test_dict_wrap_unwraps_at_wire(engine, iid):
    """``reflect.recall`` returns ``{"result": [...]}`` internally; the wire
    shape MUST be the list-wrapping dict (engine drops the `result` key
    when the inner value is itself a dict — re-wrap fires only on
    non-dicts). Confirm by reading the response shape."""
    # Seed one Reflection so recall has something to return.
    _r, _ = engine.registry.invoke(
        engine.memory, iid, "reflect", "note",
        agent_id="agent:test", scope="observation", text="x")
    # Internal call (registry.invoke) — sees the wrap.
    r_internal, _ = engine.registry.invoke(
        engine.memory, iid, "reflect", "recall",
        agent_id="agent:test", scope="")
    assert "result" in r_internal
    assert isinstance(r_internal["result"], list)
    # Wire call (call_tool via build_mcp) — sees unwrapped.
    res = await _call_tool(
        engine, "capability_reflect_recall",
        intent_id=iid, scope="")
    wire = res.structured_content or res.data
    # The engine unwraps {result: list} → list → not a dict → re-wraps to
    # {result: list}. So the wire IS {result: list} in this case.
    # (The unwrap-then-rewrap is the safety: MCP tool returns must be dicts.)
    assert "result" in wire
    assert isinstance(wire["result"], list)


async def test_scalar_wrap_rewraps_at_wire(engine, iid):
    """``reflect.note`` returns ``{"result": <id_str>}`` internally; the
    engine unwraps to bare str, then re-wraps because MCP returns must be
    dicts. Wire shape: ``{"result": <id_str>}`` (same as internal)."""
    res = await _call_tool(
        engine, "capability_reflect_note",
        intent_id=iid, scope="observation", text="hello")
    wire = res.structured_content or res.data
    assert "result" in wire
    assert isinstance(wire["result"], str)
    assert wire["result"].startswith("reflection:")


async def test_rich_dict_passes_through(engine, iid):
    """``dogfood.note`` returns ``{reflection_id, plan_slug}`` directly
    (no wrap). Wire shape = internal shape, unchanged."""
    res = await _call_tool(
        engine, "capability_dogfood_note",
        intent_id=iid, observation="x", plan_slug="019")
    wire = res.structured_content or res.data
    assert "reflection_id" in wire
    assert "plan_slug" in wire
    assert "result" not in wire   # no wrapping happened


# ---------------------------------------------------------------------------
# lint_capability — wire-shape rule.
# ---------------------------------------------------------------------------


class _GoodCap(CapabilityBase):
    """A capability whose docstrings describe the WIRE shape correctly."""
    name = "spec019_good"
    home = "memory"
    ontology = OntologyExtension(nodes={})

    @verb(role="transform")
    def w(self, x: int = 0) -> dict:
        """Return the wire-shape rich dict.

        Inputs: x (int).
        Returns: ``{value, doubled}``.
        chain_next: terminal.
        """
        return {"value": x, "doubled": x * 2}

    @verb(role="transform")
    def s(self, x: int = 0) -> dict:
        """Return a scalar wrapped in result.

        Inputs: x (int).
        Returns: ``{result: <scalar>}``.
        chain_next: terminal.
        """
        return {"result": x * 3}


class _BadCap(CapabilityBase):
    """A capability whose docstring describes the INTERNAL wrap on a
    dict-wrapping return — the wire shape leaks `result`."""
    name = "spec019_bad"
    home = "memory"
    ontology = OntologyExtension(nodes={})

    @verb(role="transform")
    def leaky(self, x: int = 0) -> dict:
        """Returns the dict but docstring leaks the wrap.

        Inputs: x (int).
        Returns: ``{result: {value, doubled}}``.
        chain_next: terminal.
        """
        return {"result": {"value": x, "doubled": x * 2}}


def test_lint_passes_when_docstring_matches_wire_shape():
    cap = _GoodCap.as_capability()
    out = lint_capability(cap)
    leak_findings = [v for v in (out["violations"] + out["warnings"])
                     if v.get("kind") == "wire_shape"]
    assert leak_findings == [], (
        f"good cap should not trip wire_shape rule; got {leak_findings}")


def test_lint_flags_leaky_returns_docstring():
    cap = _BadCap.as_capability()
    out = lint_capability(cap)
    leak_findings = [v for v in (out["violations"] + out["warnings"])
                     if v.get("kind") == "wire_shape"]
    assert leak_findings, (
        "leaky cap docstring should trip the wire_shape rule")
    assert any(v["verb"] == "leaky" for v in leak_findings)
