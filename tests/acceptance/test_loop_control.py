"""Acceptance — the loop termination evaluator (Spec 366; ported from looper).

`agency/_loop.py::control_evaluate` is the pure guard consulted before each move:
it ports looper's run-loop.py termination logic (max_revisions, max_iterations,
no_progress, budget) into one function returning {permit, stop_reason}.
"""
from __future__ import annotations

from pytest_bdd import given, parsers, scenarios, then, when

scenarios("features/loop_control.feature")


def _parse_kv(params: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for part in params.replace(" and ", ", ").split(","):
        part = part.strip()
        if not part:
            continue
        key, value = part.rsplit(" ", 1)
        out[key.strip()] = int(value)
    return out


@given(parsers.re(r"a loop control with (?P<params>.+)"), target_fixture="control_box")
def _control(params):
    kv = _parse_kv(params)
    control: dict = {}
    for k in ("max_iterations", "max_revisions", "no_progress_stall"):
        if k in kv:
            control[k] = kv[k]
    if "wall_clock_min" in kv:
        control["budget"] = {"wall_clock_min": kv["wall_clock_min"]}
    return {"control": control}


@when(parsers.re(r"I evaluate control with (?P<params>.+)"), target_fixture="result_box")
def _evaluate(control_box, params):
    from agency._loop import control_evaluate
    kv = _parse_kv(params)
    progress = {
        "iterations": kv.get("iterations", 0),
        "revisions": kv.get("revisions", 0),
        "stalled": kv.get("stalled", 0),
        "elapsed_min": kv.get("elapsed", 0),
    }
    return {"result": control_evaluate(control_box["control"], progress)}


@then("the move is permitted")
def _permitted(result_box):
    r = result_box["result"]
    assert r["permit"] is True, r
    assert r["stop_reason"] == "", r


@then(parsers.parse('the move is denied with stop_reason "{reason}"'))
def _denied(result_box, reason):
    r = result_box["result"]
    assert r["permit"] is False, r
    assert r["stop_reason"] == reason, r
