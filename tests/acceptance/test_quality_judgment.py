"""Acceptance — Spec 380 §judgment: the LLM judgment pass (the wet-corpus unblock).

The judgment pass produces the reasoning-heavy decay findings (R2/R3/R6/T1–T6)
the decidable scanners cannot. It routes through `complete_or_delegate` (Spec 352
OpenRouter free-first → driver → MCP host-sampling → Spec 279 host-delegate), so
no API key is required — inside Claude Code the host runs inference and resumes
via `host_completion`. These scenarios verify the behaviour deterministically by
injecting a frozen `host_completion` (the resume rail wins over every backend),
so the test never makes a network call; the real-model path is the same code.
"""
from __future__ import annotations

import json

from pytest_bdd import parsers, scenarios, given, then, when

from agency.capabilities.analyze import _decay, _review
from conftest import invoke

scenarios("features/quality_judgment.feature")


@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


def _reply(*findings: dict) -> dict:
    """A frozen host_completion (the Spec 279 resume shape) carrying a JSON-array
    reply in `text` — exactly what the host hands back after running inference."""
    return {"text": json.dumps(list(findings))}


# ── scenario 1: parse + filter (hallucination + Iron-Law guards) ─────────────

@given("a frozen LLM reply citing a real risk, a hallucinated code, and an "
       "incomplete one", target_fixture="reply")
def _frozen_reply():
    # R2 is judgment-only + Iron-Law-complete (survives); R99 is not a real risk
    # (hallucination — dropped); R3 is real but missing consequence/remedy
    # (Iron-Law-incomplete — dropped at the source, the Wiegers gate).
    return _reply(
        {"risk_code": "R2", "file": "x.py", "line": 5, "message": "god object",
         "source": "Martin — Single Responsibility", "consequence": "change ripples",
         "remedy": "split the responsibilities into cohesive units"},
        {"risk_code": "R99", "file": "x.py", "line": 1, "message": "made up",
         "source": "s", "consequence": "c", "remedy": "r"},
        {"risk_code": "R3", "file": "x.py", "line": 2, "message": "incomplete",
         "source": "s", "consequence": "", "remedy": ""},
    )


@when("the judgment pass runs over a code unit with that reply",
      target_fixture="judged")
def _run_judgment(reply):
    findings, delegate = _review.judgment(
        [("x.py", "class Big:\n    pass\n")], _decay.load_risks(),
        host_completion=reply)
    return {"findings": findings, "delegate": delegate}


@then("only the real, Iron-Law-complete finding survives")
def _one_survives(judged):
    codes = [f.risk_code for f in judged["findings"]]
    assert codes == ["R2"], codes


@then("it carries a risk_code, a Source, a Consequence, and a Remedy")
def _iron_law(judged):
    f = judged["findings"][0]
    assert f.risk_code == "R2"
    assert f.source and f.consequence and f.remedy


# ── scenario 2: graceful degradation → delegate envelope ─────────────────────

@when("the judgment pass runs with no driver, host, or completion",
      target_fixture="judged")
def _run_no_backend(monkeypatch):
    # Guarantee branch 5 (delegate) regardless of the dev machine's env — no
    # OpenRouter free call, no Anthropic driver.
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    findings, delegate = _review.judgment(
        [("x.py", "class Big:\n    pass\n")], _decay.load_risks())
    return {"findings": findings, "delegate": delegate}


@then("it produces no judgment findings")
def _no_findings(judged):
    assert judged["findings"] == []


@then(parsers.parse('it returns an "{kind}" envelope for the host to fulfil'))
def _delegate_envelope(judged, kind):
    assert judged["delegate"] is not None
    assert judged["delegate"].get("kind") == kind


# ── scenario 3: analyze.review merges judgment + decidable ────────────────────

@given("a fixture file that trips a decidable rule", target_fixture="fixture_dir")
def _fixture_dir(tmp_path):
    from agency.capabilities.analyze._quality import _FUNC_LOC_LIMIT
    over = _FUNC_LOC_LIMIT + 10
    (tmp_path / "m.py").write_text(
        "def big():\n    total = 0\n" + "    total += 1\n" * over + "    return total\n")
    return str(tmp_path)


@when("analyze.review runs over it with a judgment reply for the same file",
      target_fixture="review")
def _review_with_judgment(engine_iid, fixture_dir):
    engine, iid = engine_iid
    reply = _reply(
        {"risk_code": "R2", "file": f"{fixture_dir}/m.py", "line": 1,
         "message": "the function owns too many responsibilities",
         "source": "Martin — Single Responsibility",
         "consequence": "every change risks the whole unit",
         "remedy": "extract cohesive helpers"})
    result, _ = invoke(engine, iid, "analyze", "review",
                       path=fixture_dir, host_completion=reply)
    return result


@then("the merged findings include the judgment risk_code")
def _has_judgment(review):
    codes = {f.get("risk_code") for f in review["findings"]}
    assert "R2" in codes, codes


@then("the decidable finding is still present")
def _has_decidable(review):
    codes = {f.get("risk_code") for f in review["findings"]}
    assert "R1" in codes, codes
