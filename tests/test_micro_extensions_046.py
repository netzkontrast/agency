"""Spec 046 — micro-extensions: branch.commit_smart (F-C) + develop.estimate (F-D)."""
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    try:
        yield e
    finally:
        e.memory.close()


@pytest.fixture
def iid(engine):
    i = engine.intent.capture("dev", "a change", "done")
    engine.intent.confirm(i)
    return i


def _call(e, iid, cap, verb, **kw):
    res, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


def test_commit_smart_infers_type_and_scope_from_paths(engine, iid):
    out = _call(engine, iid, "branch", "commit_smart",
                summary="Add the parser", paths="agency/capabilities/analyze/_main.py")
    assert out["message"] == "feat(analyze): add the parser"
    assert out["type"] == "feat" and out["scope"] == "analyze"


def test_commit_smart_type_inference(engine, iid):
    docs = _call(engine, iid, "branch", "commit_smart", summary="Update guide", paths="docs/x.md")
    assert docs["type"] == "docs"
    tests = _call(engine, iid, "branch", "commit_smart", summary="cover edge", paths="tests/test_x.py")
    assert tests["type"] == "test"
    fix = _call(engine, iid, "branch", "commit_smart", summary="Fix the crash on empty input")
    assert fix["type"] == "fix"


def test_estimate_is_decidable_and_monotonic(engine, iid):
    small = _call(engine, iid, "develop", "estimate", loc=20, files=1, tests=1)
    large = _call(engine, iid, "develop", "estimate", loc=800, files=12, tests=10)
    assert small["bucket"] == "S" and large["bucket"] == "XL"
    assert large["points"] > small["points"]            # monotonic in size
    assert large["confidence"] < small["confidence"]    # confidence shrinks with size
    # deterministic: same inputs → same output
    assert _call(engine, iid, "develop", "estimate", loc=20, files=1, tests=1) == small


def test_estimate_handles_zero_and_negative(engine, iid):
    z = _call(engine, iid, "develop", "estimate")
    assert z["bucket"] == "S" and z["points"] == 0.0
    neg = _call(engine, iid, "develop", "estimate", loc=-5)
    assert neg["points"] == 0.0                         # clamped, no crash
