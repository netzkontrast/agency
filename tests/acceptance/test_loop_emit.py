"""Acceptance — loop spec + emission (Spec 368, graph → portable artefacts).

compile() projects the spine loop into looper's loop.resolved.json shape (the
same contract the ported runner reads); emit() renders the portable workspace as
anchored documents. Validation reuses jsonschema against loop.v1 + the reviewer-
only rule. The document.sync round-trip is a documented followup.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine

scenarios("features/loop_emit.feature")


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


def _goal(engine):
    from agency._loop import frame_goal
    gid = frame_goal(engine,
                     "Produce an agent workflow map for ACME from their manual process",
                     "A LOOP.md the client can run, every step mapped to a tool or human, nothing TBD")["goal_id"]
    engine.intent.confirm(gid)
    return gid


@given("a fully-specified loop on the spine", target_fixture="box")
def _full_loop(engine):
    from agency._loop import open_loop, add_criterion, add_member
    gid = _goal(engine)
    lid = open_loop(engine, gid, max_iterations=8, max_revisions=3)["loop_id"]
    add_criterion(engine, lid, "programmatic", check=["true"], expect="exit_zero")
    add_criterion(engine, lid, "judge", rubric="every step has an owner", cid="covers-goal")
    add_member(engine, lid, "judge", scope="both", family="codex")
    return {"loop_id": lid}


@given("an under-specified loop with only a reviewer member", target_fixture="box")
def _under_loop(engine):
    from agency._loop import open_loop, add_member
    gid = _goal(engine)
    lid = open_loop(engine, gid, max_iterations=8)["loop_id"]
    add_member(engine, lid, "reviewer", scope="plan")
    return {"loop_id": lid}


@when("I compile the loop", target_fixture="box")
def _compile(engine, box):
    from agency._loop import compile as loop_compile
    box["compiled"] = loop_compile(engine, box["loop_id"])
    return box


@when("I emit the loop to a temp directory", target_fixture="box")
def _emit(engine, box, tmp_path):
    from agency._loop import emit
    box["out"] = tmp_path / "out"
    box["emitted"] = emit(engine, box["loop_id"], str(box["out"]))
    return box


@then("the resolved spec is valid")
def _valid(box):
    assert box["compiled"]["valid"] is True, box["compiled"]["findings"]


@then("it contains criteria_by_id and council_by_id with the inlined judge rubric")
def _maps(box):
    resolved = box["compiled"]["resolved"]
    assert "covers-goal" in resolved["criteria_by_id"], resolved["criteria_by_id"]
    assert resolved["criteria_by_id"]["covers-goal"]["rubric"] == "every step has an owner"
    assert resolved["council_by_id"], resolved["council_by_id"]


@then("every council member invoke is an argv array, never a shell string")
def _argv(box):
    for entry in box["compiled"]["resolved"]["council"]:
        assert isinstance(entry["invoke"], list) and entry["invoke"], entry
        assert all(isinstance(t, str) for t in entry["invoke"]), entry


@then("loop.yaml, loop.resolved.json, LOOP.md, RUN_IN_SESSION.md, README.md and loop-workspace exist")
def _files_exist(box):
    out = box["out"]
    for name in ("loop.yaml", "loop.resolved.json", "LOOP.md", "RUN_IN_SESSION.md", "README.md"):
        assert (out / name).exists(), f"missing {name}"
    assert (out / "loop-workspace").is_dir()


@then("each rendered markdown carries an agency-node anchor on its first line")
def _anchored(box):
    out = box["out"]
    for name in ("LOOP.md", "RUN_IN_SESSION.md", "README.md"):
        first = (out / name).read_text(encoding="utf-8").splitlines()[0]
        assert first.startswith("<!-- agency-node:"), (name, first)


@then("it is not valid and returns a reviewer-only-rule finding")
def _invalid(box):
    assert box["compiled"]["valid"] is False, box["compiled"]
    msgs = " ".join(f["message"] for f in box["compiled"]["findings"])
    assert "verdict_source" in msgs, box["compiled"]["findings"]
