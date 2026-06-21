"""Acceptance — Spec 382 §1: SARIF emit from structured findings.

Behaviour-only: SARIF validity + the rule set DERIVED from the live registry
(rule 8 — never pinned) + the truncation locator. Through analyze.sarif.
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, given, then, when

from agency.capabilities.analyze import _decay
from conftest import invoke

scenarios("features/quality_sarif.feature")


@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


@given("findings including an R5 critical with consequence and remedy",
       target_fixture="findings")
def _r5_finding():
    return [{"rule": "A001", "severity": "fail", "file": "m.py", "line": 3,
             "message": "import cycle a→b→a", "evidence": "e", "risk_code": "R5",
             "source": "Martin — ADP", "consequence": "cycles rot the build",
             "remedy": "invert the dependency"}]


@given("no findings", target_fixture="findings")
def _no_findings():
    return []


@given("10 findings", target_fixture="findings")
def _ten_findings():
    return [{"rule": "Q003", "severity": "warn", "file": f"f{i}.py", "line": i + 1,
             "message": "long fn", "evidence": "e", "risk_code": "R1",
             "source": "s", "consequence": "c", "remedy": "r"} for i in range(10)]


@when("I render SARIF", target_fixture="sarif_result")
def _render(findings, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "sarif", findings=findings)
    return result


@when(parsers.re(r"I render SARIF with max_results (?P<n>\d+)"), target_fixture="sarif_result")
def _render_capped(n, findings, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "sarif", findings=findings,
                       max_results=int(n))
    return result


def _results(sarif_result):
    return sarif_result["sarif"]["runs"][0]["results"]


@then(parsers.re(r'the SARIF version is "(?P<v>[^"]+)"'))
def _version(v, sarif_result):
    assert sarif_result["sarif"]["version"] == v, sarif_result["sarif"].get("version")


def _r5(sarif_result):
    return next(r for r in _results(sarif_result) if r["ruleId"] == "R5")


@then(parsers.re(r'the R5 result level is "(?P<level>[^"]+)"'))
def _r5_level(level, sarif_result):
    assert _r5(sarif_result)["level"] == level, _r5(sarif_result)


@then("the R5 result message carries the consequence and the remedy")
def _r5_message(sarif_result):
    text = _r5(sarif_result)["message"]["text"]
    assert "cycles rot the build" in text and "invert the dependency" in text, text


@then("the SARIF rule ids equal the live decay-risk registry")
def _rules_derived(sarif_result):
    rule_ids = {r["id"] for r in sarif_result["sarif"]["runs"][0]["tool"]["driver"]["rules"]}
    assert rule_ids == set(_decay.load_risks()), rule_ids


@then(parsers.re(r"at most (?P<n>\d+) results are emitted"))
def _capped(n, sarif_result):
    assert len(_results(sarif_result)) <= int(n), len(_results(sarif_result))


@then(parsers.re(r'the SARIF reports "(?P<text>[^"]+)"'))
def _truncation_locator(text, sarif_result):
    props = sarif_result["sarif"]["runs"][0].get("properties", {})
    assert props.get("truncated") == text, props
