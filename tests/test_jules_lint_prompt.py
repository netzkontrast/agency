"""Phase 3 RED→GREEN — `jules.lint_prompt` transform verb.

Per Plan/013-…/IMPLEMENTATION-PLAN.md Phase 3 + DESIGN.md `## Design —
the skill set` skill 2: the predicate verb the Spec 013 protocol-preamble
skill walks to gate dispatches.

The verb wraps the pure `_jules_preambles.lint_must_name(...)` predicate
so it auto-wires through the engine (MCP / bash CLI / Skills) like
every other Capability verb.
"""
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "lint dispatch prompts",
        "ok=True iff prompt names canonical tools",
        "ok flips True only when all must_name present",
    )
    engine.intent.confirm(intent)
    return intent


def _call(engine, iid, verb, **kw):
    res, _inv = engine.registry.invoke(
        engine.memory, iid, "jules", verb, agent_id="agent:jules", **kw
    )
    return res


def test_lint_prompt_ok_when_full_canon_present(engine, iid):
    text = (
        "Run pre_commit_instructions() then submit(branch_name=...). "
        "If stuck use request_user_input. Use replace_with_git_merge_diff "
        "and request_code_review before submit."
    )
    res = _call(engine, iid, "lint_prompt", text=text)
    assert res["ok"] is True
    assert res["missing"] == []


def test_lint_prompt_flags_missing_publish_tool(engine, iid):
    text = "Open a PR when you are done."
    res = _call(engine, iid, "lint_prompt", text=text)
    assert res["ok"] is False
    assert "submit" in res["missing"]
    assert "pre_commit_instructions" in res["missing"]


def test_lint_prompt_accepts_must_name_override(engine, iid):
    """Caller can scope the predicate via a comma-separated must_name."""
    text = "Run pre_commit_instructions() then submit(...)."
    res = _call(engine, iid, "lint_prompt", text=text,
                must_name="pre_commit_instructions,submit")
    assert res["ok"] is True
    assert res["missing"] == []


def test_lint_prompt_extras_reports_tools_outside_caller_set(engine, iid):
    """`extras` carries canonical tools named but not in caller's must_name."""
    text = (
        "pre_commit_instructions then submit. Also use "
        "replace_with_git_merge_diff."
    )
    res = _call(engine, iid, "lint_prompt", text=text,
                must_name="pre_commit_instructions,submit")
    assert res["ok"] is True
    assert "replace_with_git_merge_diff" in res["extras"]


def test_lint_prompt_empty_must_name_falls_back_to_canon(engine, iid):
    """Empty must_name should be equivalent to the default canon path."""
    text = "x"
    res_a = _call(engine, iid, "lint_prompt", text=text)
    res_b = _call(engine, iid, "lint_prompt", text=text, must_name="")
    assert res_a == res_b


# ---------------------------------------------------------------------------
# jules.review_comment — review-cycle handshake (AGENCY_PROTOCOL.md §9).
# ---------------------------------------------------------------------------


def test_review_comment_appends_handshake_tail(engine, iid):
    body = "Verdict: changes-requested. Fix the test."
    res = _call(engine, iid, "review_comment", body=body)
    assert "reply_to_pr_comments" in res["text"]
    assert res["tail_appended"] is True
    assert body in res["text"]


def test_review_comment_is_idempotent(engine, iid):
    body_with_tail = _call(engine, iid, "review_comment", body="x")["text"]
    res2 = _call(engine, iid, "review_comment", body=body_with_tail)
    # The tail must not duplicate.
    assert res2["text"].count("reply_to_pr_comments") == 1
    assert res2["tail_appended"] is False
