"""Phase 2 RED→GREEN — `_jules_preambles.py` Mode A/B assembler.

Per Plan/013-…/IMPLEMENTATION-PLAN.md Phase 2:
- Mode A (dogfood, `source == DISPATCH_SELF_SOURCE`): preamble only;
  no clone block (Jules inherits AGENTS.md + AGENCY_PROTOCOL.md via
  lexical scoping).
- Mode B (delegate, any other source): preamble PLUS the explicit
  READ-ONLY clone instruction + read_file pointers to both docs.
- Single `PREAMBLE` constant (not a dict registry) per Phase C panel
  must-fix #1; unknown preset names raise ValueError for forward-compat
  safety.
- `lint_must_name(text, must_name=[…])` returns the predicate the
  Phase 3 `jules.lint_prompt` verb consumes.
"""
import pytest

from agency.capabilities._jules_preambles import (
    AGENCY_CLONE_PATH,
    DISPATCH_PROTOCOL_SOURCE_URL,
    DISPATCH_SELF_SOURCE,
    PREAMBLE,
    REVIEW_COMMENT_TAIL,
    assemble,
    lint_must_name,
    review_comment,
)


# ---------------------------------------------------------------------------
# PREAMBLE — content invariants the caller can rely on.
# ---------------------------------------------------------------------------


def test_preamble_names_canonical_jules_tools():
    """Every must-name tool from AGENCY_PROTOCOL.md §2 appears literally."""
    for tool in [
        "pre_commit_instructions",
        "submit",
        "request_user_input",
        "replace_with_git_merge_diff",
        "request_code_review",
    ]:
        assert tool in PREAMBLE, f"PREAMBLE must name {tool!r} literally"


def test_preamble_points_at_both_root_docs():
    assert "AGENTS.md" in PREAMBLE
    assert "AGENCY_PROTOCOL.md" in PREAMBLE


def test_preamble_carries_verify_remote_rule():
    assert "git ls-remote" in PREAMBLE
    # And reinforces the COMPLETED-≠-done discipline.
    assert "silent-fail" in PREAMBLE.lower() or "never trust local HEAD" in PREAMBLE


# ---------------------------------------------------------------------------
# Mode A — dogfood.
# ---------------------------------------------------------------------------


def test_mode_a_omits_clone_block():
    out = assemble(
        source=DISPATCH_SELF_SOURCE,
        starting_branch="feat/x",
        prompt="do the thing",
    )
    assert "git clone" not in out, (
        "Mode A relies on Jules's lexical scoping to inherit AGENTS.md + "
        "AGENCY_PROTOCOL.md; the assembler MUST NOT prepend a clone block."
    )
    # Preamble + the user prompt should both be present.
    assert PREAMBLE in out
    assert "do the thing" in out


def test_mode_a_uses_self_source_constant():
    # If DISPATCH_SELF_SOURCE is reconfigured at the module level,
    # Mode-A detection must follow.
    out = assemble(
        source=DISPATCH_SELF_SOURCE,
        starting_branch="main",
        prompt="prompt body",
    )
    # No clone for self source.
    assert DISPATCH_PROTOCOL_SOURCE_URL not in out


# ---------------------------------------------------------------------------
# Mode B — delegate.
# ---------------------------------------------------------------------------


def test_mode_b_includes_clone_block():
    out = assemble(
        source="someone-else/their-project",
        starting_branch="feat/x",
        prompt="do the thing",
    )
    # Explicit `git clone --depth=1 <url> <path>` line — verbatim
    # incantation Jules will run.
    assert "git clone --depth=1" in out
    assert DISPATCH_PROTOCOL_SOURCE_URL in out
    assert AGENCY_CLONE_PATH in out


def test_mode_b_instructs_read_file_for_both_docs():
    out = assemble(
        source="someone-else/their-project",
        starting_branch="feat/x",
        prompt="do the thing",
    )
    assert f"read_file('{AGENCY_CLONE_PATH}/AGENTS.md')" in out
    assert f"read_file('{AGENCY_CLONE_PATH}/AGENCY_PROTOCOL.md')" in out


def test_mode_b_asserts_read_only_on_agency_clone():
    out = assemble(
        source="someone-else/their-project",
        starting_branch="feat/x",
        prompt="do the thing",
    )
    # The instruction must explicitly say the agency clone is read-only
    # so Jules doesn't try to commit/push there.
    text_low = out.lower()
    assert "read only" in text_low or "read-only" in text_low or "never" in text_low


def test_mode_b_preserves_preamble_and_user_prompt():
    out = assemble(
        source="someone-else/their-project",
        starting_branch="feat/x",
        prompt="USER PROMPT BODY",
    )
    assert PREAMBLE in out
    assert "USER PROMPT BODY" in out
    # Mode B should put the clone block BEFORE the preamble (so Jules
    # has the doctrine context ready before it reads it).
    assert out.index("git clone") < out.index(PREAMBLE)


# ---------------------------------------------------------------------------
# Preset-name forward-compat safety.
# ---------------------------------------------------------------------------


def test_unknown_preset_raises():
    with pytest.raises(ValueError, match="unknown protocol_preset"):
        assemble(
            source=DISPATCH_SELF_SOURCE,
            starting_branch="main",
            prompt="x",
            preset_name="research-pass",   # not a real preset (v1)
        )


def test_default_preset_is_agency_default():
    # Explicit default — passing no preset_name == passing "agency-default".
    out_implicit = assemble(
        source=DISPATCH_SELF_SOURCE, starting_branch="main", prompt="x",
    )
    out_explicit = assemble(
        source=DISPATCH_SELF_SOURCE, starting_branch="main", prompt="x",
        preset_name="agency-default",
    )
    assert out_implicit == out_explicit


# ---------------------------------------------------------------------------
# lint_must_name — the predicate Phase 3 wraps as `jules.lint_prompt`.
# ---------------------------------------------------------------------------


def test_lint_must_name_ok_when_all_present():
    text = (
        "Run pre_commit_instructions then submit with the branch_name and "
        "title args. If unsure, use request_user_input. Use "
        "replace_with_git_merge_diff for multiline edits and "
        "request_code_review before submit."
    )
    res = lint_must_name(text)
    assert res["ok"] is True
    assert res["missing"] == []


def test_lint_must_name_flags_missing_publish_tool():
    text = "Open a PR when you are done."   # the canonical silent-fail prompt
    res = lint_must_name(text)
    assert res["ok"] is False
    assert "submit" in res["missing"]
    assert "pre_commit_instructions" in res["missing"]


def test_lint_must_name_accepts_caller_override():
    # Caller scopes the predicate to ONLY the publish pair.
    text = "Run pre_commit_instructions() then submit(...)."
    res = lint_must_name(text, must_name=["pre_commit_instructions", "submit"])
    assert res["ok"] is True
    # `extras` reports canonical tools NOT in the caller list but still
    # named in the prompt (informational; doesn't affect ok).
    assert res["extras"] == []


def test_lint_must_name_extras_reports_tools_outside_caller_set():
    text = (
        "pre_commit_instructions then submit. Also use "
        "replace_with_git_merge_diff."
    )
    res = lint_must_name(
        text, must_name=["pre_commit_instructions", "submit"],
    )
    assert res["ok"] is True
    assert "replace_with_git_merge_diff" in res["extras"]


# ---------------------------------------------------------------------------
# review_comment — the PR review-cycle handshake (AGENCY_PROTOCOL.md §9).
# ---------------------------------------------------------------------------


def test_preamble_names_reply_to_pr_comments():
    """Every dispatch carries the doctrine that responding to PR reviews
    requires `reply_to_pr_comments` after `submit` — the wake mechanism."""
    assert "reply_to_pr_comments" in PREAMBLE
    assert "AGENCY_PROTOCOL.md §9" in PREAMBLE


def test_review_comment_tail_carries_the_wake_instruction():
    assert "reply_to_pr_comments" in REVIEW_COMMENT_TAIL
    assert "AGENCY_PROTOCOL.md §9" in REVIEW_COMMENT_TAIL


def test_review_comment_appends_tail_when_missing():
    body = "Verdict: changes-requested. Fix the off-by-one."
    out = review_comment(body)
    assert body in out
    assert REVIEW_COMMENT_TAIL.strip() in out


def test_review_comment_is_idempotent():
    body = "Verdict: changes-requested." + REVIEW_COMMENT_TAIL
    out = review_comment(body)
    # Tail should not appear twice.
    assert out.count("reply_to_pr_comments") == 1
