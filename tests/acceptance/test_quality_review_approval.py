"""Acceptance — Spec 380 develop.review: subagent judgment + final approval elicit.

The interactive review runs the judgment pass (fulfilled by a SUBAGENT — no
external LLM) and then ELICITS the human to approve/reject the LLM-proposed
judgment findings before they merge. Deterministic: the subagent reply is
injected as `host_completion` (the Spec 279 resume rail), and the elicit verdict
is injected via a fake host Context bound through `bind_host_context`.
"""
from __future__ import annotations

import json

from pytest_bdd import parsers, scenarios, given, then, when

from agency._host_bridge import bind_host_context, reset_host_context
from agency.capabilities.analyze._quality import _FUNC_LOC_LIMIT
from conftest import invoke

scenarios("features/quality_review_approval.feature")


@given("an engine and confirmed intent", target_fixture="engine_iid")
def _engine_iid(engine, iid):
    return engine, iid


class _Accepted:
    """A FastMCP-shaped accepted elicitation result (has `.data`)."""
    def __init__(self, data):
        self.data = data


def _bind_elicit_host(decision: str, request):
    """Bind a fake host Context whose elicit returns `decision` ('approve'/'reject')."""
    class _Ctx:
        async def elicit(self, message, response_type=None):
            return _Accepted(decision)
    token = bind_host_context(_Ctx())
    request.addfinalizer(lambda: reset_host_context(token))


def _fixture(tmp_path) -> str:
    over = _FUNC_LOC_LIMIT + 10
    (tmp_path / "m.py").write_text(
        "def big():\n    total = 0\n" + "    total += 1\n" * over + "    return total\n")
    return str(tmp_path)


def _judgment_reply(path: str) -> dict:
    return {"text": json.dumps([
        {"risk_code": "R2", "file": f"{path}/m.py", "line": 1,
         "message": "this unit changes for several unrelated reasons",
         "source": "Fowler — Refactoring — Divergent Change",
         "consequence": "edits ripple across unrelated features",
         "remedy": "split the unit along its change axes"}])}


# ── approve / reject ─────────────────────────────────────────────────────────

@given(parsers.parse('a fixture file and a host that will {decision}'),
       target_fixture="setup")
def _fixture_and_host(decision, tmp_path, request):
    _bind_elicit_host("approve" if decision == "approve" else "reject", request)
    return {"dir": _fixture(tmp_path)}


@when("develop.review runs with a subagent judgment reply", target_fixture="review")
def _run_review(setup, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "develop", "review",
                       scope=setup["dir"], host_completion=_judgment_reply(setup["dir"]))
    return result


@then("the review includes the approved judgment risk_code")
def _includes_judgment(review):
    codes = {f.get("risk_code") for f in review["findings"]}
    assert "R2" in codes, codes


@then("the review excludes the judgment risk_code")
def _excludes_judgment(review):
    codes = {f.get("risk_code") for f in review["findings"]}
    assert "R2" not in codes, codes


@then("the decidable finding is still present")
def _decidable_present(review):
    codes = {f.get("risk_code") for f in review["findings"]}
    assert "R1" in codes, codes


@then("the judgment is recorded as approved")
def _recorded_approved(review):
    assert review["judgment"]["approved"] is True
    assert review["judgment"]["proposed"] >= 1


@then("the judgment is recorded as not approved")
def _recorded_not_approved(review):
    assert review["judgment"]["approved"] is False
    assert review["judgment"]["proposed"] >= 1


# ── no backend → subagent delegate envelope ──────────────────────────────────

@given("a fixture file and no inference backend", target_fixture="setup")
def _fixture_no_backend(tmp_path, request, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    token = bind_host_context(None)                      # no sampling/elicit host
    request.addfinalizer(lambda: reset_host_context(token))
    return {"dir": _fixture(tmp_path)}


@when("develop.review runs with no completion", target_fixture="review")
def _run_review_no_completion(setup, engine_iid):
    engine, iid = engine_iid
    result, _ = invoke(engine, iid, "develop", "review", scope=setup["dir"])
    return result


@then(parsers.parse('it returns a delegate envelope hinting "{hint}"'))
def _delegate_subagent(review, hint):
    env = review.get("llm_delegate")
    assert env is not None and env.get("kind") == "llm_delegate", review
    assert env.get("model_hint") == hint, env