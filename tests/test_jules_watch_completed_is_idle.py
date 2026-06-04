"""Doctrine correction: COMPLETED in Jules is NOT terminal — it's "idle,
ball in orchestrator's court". The same value covers four situations:
  1. plan generated, awaiting approval  -> review_and_approve_plan
  2. work in VM, never submitted        -> recover_silent_fail
  3. work pushed, branch on origin      -> verify_pr
  4. genuine no-op (zero patch, no plan unapproved) -> dispatch_fresh

Before this fix, `_classify` routed case 1 to `dispatch_fresh` because
it conflated "no patch outputs" with "no work expected." The user
surfaced the misreading during the Spec 015 dispatch (commit 185251d
era — Jules sat COMPLETED + planGenerated; the classifier would have
re-dispatched instead of approving). The fix adds a `plan_unapproved`
flag the classifier checks FIRST.
"""
from agency.capabilities.jules.watch import _classify, INSTRUCTIONS


def _prev(state="IN_PROGRESS"):
    return {"state": state, "id": "sess-x"}


def _curr(state="COMPLETED", **extra):
    base = {"state": state, "id": "sess-x", "url": "https://jules.google.com/x"}
    base.update(extra)
    return base


def test_completed_with_unapproved_plan_routes_to_review_and_approve_plan():
    """Case 1: planGenerated without subsequent planApproved/codeChanges.
    Branch absent, no patch — but plan_unapproved=True forces the
    awaiting-approval route, NOT the no-op route."""
    ev = _classify(
        prev=_prev("PLANNING"),
        curr=_curr("COMPLETED", plan_steps=6),
        last_agent_msg_id=None,
        branch_on_remote=False,
        patch_summary={"files": 0, "lines": 0, "bytes": 0},
        plan_unapproved=True,
    )
    assert ev["action"] == "review_and_approve_plan"
    assert ev["evidence"]["plan_steps"] == 6
    assert "awaiting plan approval" in ev["evidence"]["completed_means"]
    # The instruction is the same template used for AWAITING_PLAN_APPROVAL —
    # surfacing the gate consistently regardless of which surface state
    # Jules reports.
    assert "approve_plan" in ev["instruction"]


def test_completed_plan_unapproved_wins_over_branch_check_only_when_branch_absent():
    """When BOTH plan_unapproved and branch_on_remote are true (Jules
    pushed but also wrote a new plan that's unapproved — rare but
    possible on multi-plan sessions), the awaiting-approval route still
    wins because Jules will not resume without approval."""
    ev = _classify(
        prev=_prev("IN_PROGRESS"),
        curr=_curr("COMPLETED", branch="feat/x", plan_steps=3),
        last_agent_msg_id=None,
        branch_on_remote=True,
        patch_summary={"files": 2, "lines": 50, "bytes": 1000},
        plan_unapproved=True,
    )
    assert ev["action"] == "review_and_approve_plan"


def test_completed_branch_on_remote_still_routes_to_verify_pr_when_no_unapproved_plan():
    """Case 3: regression — the original verify_pr path must still fire
    when plan_unapproved=False."""
    ev = _classify(
        prev=_prev("IN_PROGRESS"),
        curr=_curr("COMPLETED", branch="feat/x"),
        last_agent_msg_id=None,
        branch_on_remote=True,
        patch_summary={"files": 1, "lines": 10, "bytes": 100},
        plan_unapproved=False,
    )
    assert ev["action"] == "verify_pr"


def test_completed_silent_fail_path_unchanged_when_no_unapproved_plan():
    """Case 2: regression — recover_silent_fail must still fire when
    branch is absent BUT patch outputs > 0 AND plan is approved (or no
    plan in scope)."""
    ev = _classify(
        prev=_prev("IN_PROGRESS"),
        curr=_curr("COMPLETED"),
        last_agent_msg_id=None,
        branch_on_remote=False,
        patch_summary={"files": 3, "lines": 100, "bytes": 4000},
        plan_unapproved=False,
    )
    assert ev["action"] == "recover_silent_fail"
    assert ev["evidence"]["files"] == 3


def test_completed_genuine_noop_still_routes_to_dispatch_fresh():
    """Case 4: regression — true no-op (no plan unapproved, no patch,
    no branch) is the only case that should re-dispatch."""
    ev = _classify(
        prev=_prev("IN_PROGRESS"),
        curr=_curr("COMPLETED"),
        last_agent_msg_id=None,
        branch_on_remote=False,
        patch_summary={"files": 0, "lines": 0, "bytes": 0},
        plan_unapproved=False,
    )
    assert ev["action"] == "dispatch_fresh"


def test_plan_unapproved_default_false_preserves_legacy_callers():
    """The new parameter defaults to False so legacy callers (tests +
    `_poll_loop` callers that haven't been updated) get the pre-fix
    behavior."""
    ev = _classify(
        prev=_prev("IN_PROGRESS"),
        curr=_curr("COMPLETED"),
        last_agent_msg_id=None,
        branch_on_remote=False,
        patch_summary={"files": 0, "lines": 0, "bytes": 0},
        # No plan_unapproved kwarg.
    )
    assert ev["action"] == "dispatch_fresh"


def test_instructions_table_unchanged_for_review_and_approve_plan():
    """Sanity: the existing INSTRUCTIONS["review_and_approve_plan"]
    template is the one the new COMPLETED branch uses, so the literal
    `jules.approve_plan` mention from Spec 013 Phase 11 still applies."""
    body = INSTRUCTIONS["review_and_approve_plan"]
    assert "jules.approve_plan" in body
    assert "{plan_steps}" in body
