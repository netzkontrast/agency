"""Acceptance — Spec 381 §2: quality config block (tunability + validation).

Behaviour-only: the config filters findings before scoring and surfaces
validation notes (never fatal). Exercised through analyze.score(config=).
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, given, then, when

from conftest import invoke

scenarios("features/quality_config.feature")


@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


@given("findings of one R1 critical and one R2 warning", target_fixture="findings")
def _r1_r2():
    return [
        {"rule": "Q003", "severity": "fail", "file": "a.py", "line": 1,
         "message": "m", "evidence": "e", "risk_code": "R1",
         "source": "", "consequence": "c", "remedy": "r"},
        {"rule": "Q004", "severity": "warn", "file": "b.py", "line": 2,
         "message": "m", "evidence": "e", "risk_code": "R2",
         "source": "", "consequence": "c", "remedy": "r"},
    ]


@when(parsers.re(r'I score under "(?P<preset>[^"]+)" with config disabling "(?P<code>[^"]+)"'),
      target_fixture="scored")
def _score_disable(preset, code, findings, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "score",
                       findings=findings, preset=preset, config={"disable": [code]})
    return result


@when(parsers.re(r'I score under "(?P<preset>[^"]+)" with config focusing on "(?P<code>[^"]+)"'),
      target_fixture="scored")
def _score_focus(preset, code, findings, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "score",
                       findings=findings, preset=preset, config={"focus": [code]})
    return result


@when("I score with config setting both focus and disable", target_fixture="scored")
def _score_both(findings, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "score", findings=findings,
                       preset="balanced", config={"focus": ["R2"], "disable": ["R1"]})
    return result


@when(parsers.re(r'I score with config strictness "(?P<preset>[^"]+)" and no explicit preset'),
      target_fixture="scored")
def _score_strictness(preset, findings, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "score",
                       findings=findings, config={"strictness": preset})
    return result


@then(parsers.re(r"only (?P<n>\d+) finding is scored"))
def _n_scored(n, scored):
    assert scored["scored_findings"] == int(n), scored


@then("both findings are scored")
def _both_scored(scored):
    assert scored["scored_findings"] == 2, scored


@then(parsers.re(r"the score is (?P<v>\d+)"))
def _score_is(v, scored):
    assert scored["score"] == int(v), scored


@then("the config notes report the focus-and-disable conflict")
def _notes_conflict(scored):
    notes = " ".join(scored.get("config_notes") or []).lower()
    assert "focus" in notes and "disable" in notes, scored.get("config_notes")


@then(parsers.re(r'the preset used is "(?P<preset>[^"]+)"'))
def _preset_used(preset, scored):
    assert scored["preset"] == preset, scored
