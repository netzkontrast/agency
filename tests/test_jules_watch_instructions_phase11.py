"""Spec 013 Phase 11 — `INSTRUCTIONS` template update.

Per DESIGN.md `## Design — capability deltas → Spec 012 INSTRUCTIONS update`:
every per-WatchAction template names the canonical Jules tool(s) the agent
must call (per AGENCY_PROTOCOL.md §2 — prose alone leaves work in the VM).
This is the silent-fail-prevention update; the test locks in the literal
tool names so a future "tighten the prose" pass can't accidentally drop them.

Token budget: each template ≤ 480 chars (~120 tokens).
"""
from agency.capabilities.jules.watch import INSTRUCTIONS


MAX_CHARS = 480


def test_every_template_under_token_budget():
    over = {k: len(v) for k, v in INSTRUCTIONS.items() if len(v) > MAX_CHARS}
    assert not over, f"templates over {MAX_CHARS} chars: {over}"


def test_review_and_approve_plan_names_jules_verbs():
    body = INSTRUCTIONS["review_and_approve_plan"]
    assert "jules.plan" in body
    assert "jules.approve_plan" in body


def test_answer_agent_question_names_request_user_input_not_message_user():
    """AGENCY_PROTOCOL.md §4: questions through request_user_input only."""
    body = INSTRUCTIONS["answer_agent_question"]
    assert "request_user_input" in body
    # message_user only appears as the NEGATIVE example.
    assert "NEVER message_user" in body or "never use message_user" in body.lower()


def test_verify_pr_instructs_git_ls_remote_not_local_head():
    body = INSTRUCTIONS["verify_pr"]
    assert "git ls-remote" in body
    assert "local HEAD" in body
    # Review-comment tools named for the review-cycle handshake (§9).
    assert "reply_to_pr_comments" in body
    assert "read_pr_comments" in body


def test_recover_silent_fail_names_canonical_publish_pair():
    """The whole point of the spec — the silent-fail recovery instruction
    must literally name both pre_commit_instructions and submit."""
    body = INSTRUCTIONS["recover_silent_fail"]
    assert "pre_commit_instructions" in body
    assert "submit(" in body or "submit(branch_name" in body


def test_recover_apply_plan_names_github_mcp_ops():
    body = INSTRUCTIONS["recover_apply_plan"]
    assert "create_branch" in body
    assert "push_files" in body
    assert "create_pull_request" in body


def test_dispatch_fresh_names_full_must_name_canon():
    """Per DESIGN.md the dispatch_fresh template carries the FULL must-name
    canon — every canonical Jules tool the next dispatch's prompt should
    name verbatim."""
    body = INSTRUCTIONS["dispatch_fresh"]
    for tool in [
        "submit", "pre_commit_instructions", "request_user_input",
        "replace_with_git_merge_diff", "request_code_review",
    ]:
        assert tool in body, f"dispatch_fresh missing {tool!r}"


def test_inspect_and_resume_names_inspection_primitives():
    body = INSTRUCTIONS["inspect_and_resume"]
    assert "jules.activities" in body
    assert "read_file" in body
    assert "list_files" in body
    assert "plan_step_complete" in body


def test_terminal_stays_minimal():
    """Terminal is the one no-tool-nomination cell per DESIGN.md's table."""
    body = INSTRUCTIONS["terminal"]
    assert "{cause}" in body
    # No tool names should be in the terminal instruction.
    for tool in ["submit", "request_user_input", "replace_with_git_merge_diff"]:
        assert tool not in body
