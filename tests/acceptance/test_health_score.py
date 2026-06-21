"""Acceptance — Spec 381: Health Score (computed, preset-weighted).

Behaviour-only: the score is asserted as a RELATIONSHIP across presets and a
computed value from live findings (rule 8 — never a pinned snapshot). Exercised
through the analyze.score verb (the capability surface).
"""
from __future__ import annotations

from pytest_bdd import parsers, scenarios, given, then, when

from conftest import invoke

scenarios("features/health_score.feature")


# ── fixtures ──────────────────────────────────────────────────────────────────

@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


def _findings(severity: str, n: int = 1, risk_code: str = "") -> list[dict]:
    """n wire-shape findings of one severity (fail=critical / warn=warning /
    info=suggestion)."""
    return [{"rule": "X", "severity": severity, "file": "a.py", "line": i + 1,
             "message": "m", "evidence": "e", "risk_code": risk_code,
             "source": "", "consequence": "c", "remedy": "r"} for i in range(n)]


# ── score per preset ──────────────────────────────────────────────────────────

@given("findings of 1 critical, 2 warning, and 3 suggestion", target_fixture="findings")
def _mixed_findings():
    return _findings("fail", 1) + _findings("warn", 2) + _findings("info", 3)


@given("findings of 10 critical", target_fixture="findings")
def _ten_critical():
    return _findings("fail", 10)


@when(parsers.re(r'I score them under "(?P<preset>[^"]+)"'), target_fixture="scored")
def _score_under(preset, findings, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "score", findings=findings, preset=preset)
    return result


@then(parsers.re(r"the health score is (?P<value>\d+)"))
def _score_is(value, scored):
    assert scored["score"] == int(value), f"expected {value}, got {scored['score']}"


@then('the same findings score strictly lower under "strict"')
def _lower_under_strict(scored, findings, engine_iid):
    engine, iid = engine_iid
    strict, _ = invoke(engine, iid, "analyze", "score", findings=findings, preset="strict")
    assert strict["score"] < scored["score"], (strict["score"], scored["score"])


@then('the same findings score strictly higher under "legacy-friendly"')
def _higher_under_legacy(scored, findings, engine_iid):
    engine, iid = engine_iid
    legacy, _ = invoke(engine, iid, "analyze", "score", findings=findings,
                       preset="legacy-friendly")
    assert legacy["score"] > scored["score"], (legacy["score"], scored["score"])


# ── leverage ──────────────────────────────────────────────────────────────────

@given('a recurring "R1" warning four times and a one-off "R2" critical',
       target_fixture="findings")
def _leverage_findings():
    return _findings("warn", 4, risk_code="R1") + _findings("fail", 1, risk_code="R2")


@when(parsers.re(r'I rank fixes by leverage under "(?P<preset>[^"]+)"'),
      target_fixture="scored")
def _rank_leverage(preset, findings, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "analyze", "score", findings=findings, preset=preset)
    return result


@then(parsers.re(r'the top-leverage fix has risk_code "(?P<code>[^"]+)"'))
def _top_leverage_is(code, scored):
    top = scored.get("top_leverage") or []
    assert top, "top_leverage is empty"
    assert top[0].get("risk_code") == code, f"top={top[0]!r}"
