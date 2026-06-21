"""Acceptance — loop goal coaching (Spec 363; frame_goal / critique_goal).

The goal IS a root Intent (reuse intent.capture); context_sources bind argv-safe;
critique surfaces goal-rubric.md findings, advisory (never blocks).
"""
from __future__ import annotations

import json
import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine

scenarios("features/loop_goal.feature")


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def box():
    return {}


@given("a fresh agency engine in code-mode", target_fixture="engine")
def _eng(engine):
    return engine


@when(parsers.parse('I frame a goal "{statement}" done "{done}" with a file context source'),
      target_fixture="box")
def _frame_file(engine, statement, done):
    from agency._loop import frame_goal
    return {"result": frame_goal(engine, statement, done,
                                 context_sources=[{"file": "./inputs/notes.md"}])}


@when("I frame a goal with a shell-string cmd context source", target_fixture="box")
def _frame_shell(engine):
    from agency._loop import frame_goal
    out = {}
    try:
        out["result"] = frame_goal(engine, "Produce X", "every step done",
                                   context_sources=[{"cmd": "ls ./inputs; rm -rf /"}])
    except ValueError as exc:
        out["error"] = str(exc)
    return out


@then(parsers.parse('the goal\'s root Intent has purpose "{statement}" and acceptance "{done}"'))
def _intent_fields(engine, box, statement, done):
    node = engine.memory.recall(box["result"]["goal_id"])
    assert node.get("purpose") == statement, node
    assert node.get("acceptance") == done, node


@then("the context source is stored as a structured file entry")
def _src_stored(engine, box):
    node = engine.memory.recall(box["result"]["goal_id"])
    sources = json.loads(node.get("context_sources") or "[]")
    assert sources and sources[0].get("file"), sources


@then("framing is rejected as not an argv array")
def _rejected(box):
    assert "error" in box and "argv" in box["error"].lower(), box


@given(parsers.parse('a framed goal "{statement}" done "{done}" with no context'),
       target_fixture="box")
def _framed_no_ctx(engine, statement, done):
    from agency._loop import frame_goal
    return {"result": frame_goal(engine, statement, done)}


@given(parsers.parse('a framed goal "{statement}" done "{done}" with a file context'),
       target_fixture="box")
def _framed_ctx(engine, statement, done):
    from agency._loop import frame_goal
    return {"result": frame_goal(engine, statement, done,
                                 context_sources=[{"file": "./inputs/notes.md"}])}


@when("I critique the goal", target_fixture="box")
def _critique(engine, box):
    from agency._loop import critique_goal
    box["critique"] = critique_goal(engine, box["result"]["goal_id"])
    return box


@then(parsers.parse("critique flags {dimension} citing the goal rubric"))
def _flags_dim(box, dimension):
    key = dimension.strip().replace("-", "_").replace(" ", "_")
    matches = [f for f in box["critique"]["findings"] if f["dimension"] == key]
    assert matches, (key, box["critique"]["findings"])
    assert all(f["rubric"] == "goal-rubric.md" for f in matches)


@then("critique flags the unfalsifiable done-state")
def _flags_done(box):
    assert any(f["dimension"] == "falsifiable_done" for f in box["critique"]["findings"]), box["critique"]


@then("critique flags missing context sources")
def _flags_ctx(box):
    assert any(f["dimension"] == "gather_vs_assume" for f in box["critique"]["findings"]), box["critique"]


@then("critique does not block")
def _no_block(box):
    assert isinstance(box["critique"], dict) and "findings" in box["critique"]


@then("critique returns no findings")
def _no_findings(box):
    assert box["critique"]["findings"] == [], box["critique"]
