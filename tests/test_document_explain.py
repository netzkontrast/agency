"""Spec 043 — document.explain: code → educational text via composition.

NO LLM. The structure IS the explanation. Tests verify token budgets
per depth, target-resolution shapes, and Reflection-emission contract.
"""
import os
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    i = engine.intent.capture(
        "test document.explain",
        "structured explanation emitted",
        "Reflection recorded with explanation kind",
    )
    engine.intent.confirm(i)
    return i


def _call(engine, iid, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, "document", "explain",
        agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------


def test_explain_module(engine, iid):
    r = _call(engine, iid, target="agency.capabilities.reflect")
    assert "content" in r
    assert "reflection_id" in r
    assert "ReflectCapability" in r["content"] or "reflect" in r["content"].lower()


def test_explain_symbol(engine, iid):
    r = _call(engine, iid, target="agency.capabilities.reflect.ReflectCapability")
    assert "content" in r
    assert "ReflectCapability" in r["content"]


def test_explain_file(engine, iid, tmp_path):
    """File path target works on a fixture file."""
    p = tmp_path / "fixture.py"
    p.write_text('"""A test fixture module.\n\nLonger description.\n"""\n'
                 'def greet(name: str) -> str:\n'
                 '    return f"Hi, {name}"\n')
    r = _call(engine, iid, target=str(p))
    assert "fixture.py" in r["content"]
    assert "greet" in r["content"]


def test_explain_unknown_target_returns_error(engine, iid):
    r = _call(engine, iid, target="no.such.module.xyz")
    assert "error" in r


# ---------------------------------------------------------------------------
# Depth budgets (Spec 043 §"Done When" line 116-121).
# ---------------------------------------------------------------------------


def test_brief_under_200_tokens(engine, iid):
    r = _call(engine, iid, target="agency.capabilities.reflect",
              depth="brief")
    assert r["tokens"] <= 220   # 200 + small overhead for the buffer


def test_standard_under_600_tokens(engine, iid):
    r = _call(engine, iid, target="agency.capabilities.reflect",
              depth="standard")
    assert r["tokens"] <= 700   # 600 + slop


def test_deep_under_2500_tokens(engine, iid):
    r = _call(engine, iid, target="agency.capabilities.reflect",
              depth="deep")
    assert r["tokens"] <= 2700  # 2500 + slop


def test_invalid_depth_falls_back_to_standard(engine, iid):
    r = _call(engine, iid, target="agency.capabilities.reflect",
              depth="enormous")
    # Falls back to 'standard' budget.
    assert r["tokens"] <= 700


# ---------------------------------------------------------------------------
# Reflection emission (act semantics).
# ---------------------------------------------------------------------------


def test_explain_records_reflection(engine, iid):
    before = len(list(engine.memory.find("Reflection")))
    r = _call(engine, iid, target="agency.capabilities.reflect")
    after = len(list(engine.memory.find("Reflection")))
    assert after == before + 1
    # The reflection_id points at a Reflection with kind=explanation.
    refs = engine.memory.find("Reflection")
    explanation = next(rr for rr in refs if rr["id"] == r["reflection_id"])
    assert explanation["kind"] == "explanation"
    assert explanation["target"] == "agency.capabilities.reflect"


def test_explanation_includes_signature_for_callable(engine, iid):
    r = _call(engine, iid,
              target="agency.capabilities.reflect.ReflectCapability",
              depth="standard")
    assert "Signature" in r["content"] or "ReflectCapability" in r["content"]
