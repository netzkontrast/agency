"""Acceptance — Spec 382 §2/§3: the quality CI gate.

Behaviour-only: analyze.gate records an auditable Gate from score/critical
thresholds (documented tunable budgets); gate.verdict reads the latest Gate by
name so CI can exit non-zero on a block.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, given, then, when

from conftest import invoke

scenarios("features/quality_gate.feature")


@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


@when(parsers.re(r'I run the quality gate for mode "(?P<mode>[^"]+)" with score '
                 r'(?P<score>\d+) and (?P<crit>\d+) criticals'),
      target_fixture="gate_result")
def _run_gate(mode, score, crit, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "gate",
                       mode=mode, score=int(score), critical=int(crit))
    return result


@given(parsers.re(r'a recorded quality gate for mode "(?P<mode>[^"]+)" with score '
                  r'(?P<score>\d+) and (?P<crit>\d+) criticals'))
def _recorded_gate(mode, score, crit, engine_iid):
    engine, iid = engine_iid
    invoke(engine, iid, "analyze", "gate",
           mode=mode, score=int(score), critical=int(crit))


@when(parsers.re(r'I read the gate verdict for "(?P<name>[^"]+)"'),
      target_fixture="verdict")
def _read_verdict(name, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "gate", "verdict", name=name)
    return result


@then("the gate is blocked")
def _gate_blocked(gate_result):
    assert gate_result["blocked"] is True, gate_result


@then("the gate passes")
def _gate_passes(gate_result):
    assert gate_result["passed"] is True and gate_result["blocked"] is False, gate_result


@then(parsers.re(r'a Gate node "(?P<name>[^"]+)" records passed false with the score in its evidence'))
def _gate_node(name, gate_result, engine_iid):
    engine, _ = engine_iid
    gates = [g for g in engine.memory.find("Gate") if g.get("name") == name]
    assert gates, f"no Gate {name!r}"
    g = gates[-1]
    assert g.get("passed") is False, g
    assert "60" in str(g.get("evidence", "")), g


@then("the verdict is blocked")
def _verdict_blocked(verdict):
    assert verdict["blocked"] is True, verdict


@then("the verdict is not found and not blocked")
def _verdict_absent(verdict):
    assert verdict["found"] is False and verdict["blocked"] is False, verdict
