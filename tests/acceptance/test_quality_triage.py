"""Acceptance — Spec 381 §4: triage (suppression + acknowledgement).

Behaviour-only: the WRITE side is an intent judgment (intent.triage records a
Suppression/Acknowledgement on the intent ontology, SUPPRESSES crosses to the
analyze Finding); the scan-time scoring READ is an analyze concern (a finding
matching a live Suppression is excluded; an expired one resurfaces — keep-both).
"""
from __future__ import annotations

import time

from pytest_bdd import parsers, scenarios, given, then, when

from conftest import invoke

scenarios("features/quality_triage.feature")


@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


def _finding_dict(risk, file):
    return {"rule": "Q003", "severity": "warn", "file": file, "line": 1,
            "message": "m", "evidence": "e", "risk_code": risk,
            "source": "s", "consequence": "c", "remedy": "r"}


@given(parsers.re(r'a recorded R3 finding in "(?P<file>[^"]+)"'), target_fixture="finding_id")
def _recorded_finding(file, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "manage", "create", label="Finding",
                       props=_finding_dict("R3", file))
    return result["id"]


@given(parsers.re(r'a live Suppression for risk "(?P<risk>[^"]+)" pattern "(?P<pat>[^"]+)"'))
def _live_suppression(risk, pat, engine_iid):
    engine, iid = engine_iid
    invoke(engine, iid, "manage", "create", label="Suppression",
           props={"risk": risk, "glob": pat, "reason": "test"})


@given(parsers.re(r'an expired Suppression for risk "(?P<risk>[^"]+)" pattern "(?P<pat>[^"]+)"'))
def _expired_suppression(risk, pat, engine_iid):
    engine, iid = engine_iid
    invoke(engine, iid, "manage", "create", label="Suppression",
           props={"risk": risk, "glob": pat, "reason": "test",
                  "expires": time.time() - 86400})


@when(parsers.re(r'I triage it with action "(?P<action>[^"]+)" and reason "(?P<reason>[^"]+)"'),
      target_fixture="triage_result")
def _do_triage(action, reason, finding_id, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "intent", "triage",
                       finding_id=finding_id, action=action, reason=reason)
    return result


@when(parsers.re(r'I score findings of an R3 in "(?P<f1>[^"]+)" and an R1 in "(?P<f2>[^"]+)"'),
      target_fixture="scored")
def _score_two(f1, f2, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "score",
                       findings=[_finding_dict("R3", f1),
                                 {**_finding_dict("R1", f2), "severity": "fail"}],
                       preset="balanced")
    return result


@when(parsers.re(r'I score findings of an R3 in "(?P<f1>[^"]+)"'), target_fixture="scored")
def _score_one(f1, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "score",
                       findings=[_finding_dict("R3", f1)], preset="balanced")
    return result


# ── write-side assertions ──────────────────────────────────────────────────────

@then(parsers.re(r'a Suppression records risk "(?P<risk>[^"]+)", pattern "(?P<pat>[^"]+)", and the reason'))
def _suppression_recorded(risk, pat, engine_iid):
    engine, _ = engine_iid
    sups = engine.memory.find("Suppression")
    assert any(s.get("risk") == risk and s.get("glob") == pat and s.get("reason")
               for s in sups), f"no matching Suppression in {sups}"


@then("the Suppression SUPPRESSES the finding")
def _suppresses_edge(finding_id, engine_iid):
    engine, _ = engine_iid
    rows = engine.memory.g.query(
        "MATCH (s:Suppression)-[:SUPPRESSES]->(f) WHERE f.id = $fid RETURN s",
        {"fid": finding_id}) or []
    assert rows, "no SUPPRESSES edge to the finding"


@then("the finding node still exists")
def _finding_exists(finding_id, engine_iid):
    engine, _ = engine_iid
    assert engine.memory.recall(finding_id) is not None


@then(parsers.re(r'an Acknowledgement records risk "(?P<risk>[^"]+)" and the reason'))
def _ack_recorded(risk, engine_iid):
    engine, _ = engine_iid
    acks = engine.memory.find("Acknowledgement")
    assert any(a.get("risk") == risk and a.get("reason") for a in acks), \
        f"no matching Acknowledgement in {acks}"


# ── read-side (scoring) assertions ─────────────────────────────────────────────

@then(parsers.re(r"(?P<n>\d+) finding is suppressed at scan time"))
def _n_suppressed(n, scored):
    assert scored.get("suppressed") == int(n), scored


@then(parsers.re(r"only (?P<n>\d+) finding is scored"))
def _only_n_scored(n, scored):
    assert scored["scored_findings"] == int(n), scored


@then(parsers.re(r"(?P<n>\d+) finding is scored"))
def _n_scored(n, scored):
    assert scored["scored_findings"] == int(n), scored


@then(parsers.re(r"(?P<n>\d+) suppression is reported expired"))
def _n_expired(n, scored):
    assert scored.get("expired_suppressions") == int(n), scored
