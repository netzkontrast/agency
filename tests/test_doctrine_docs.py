"""Phase 1 RED→GREEN — the doctrine docs at repo root.

Per Plan/013-…/IMPLEMENTATION-PLAN.md Phase 1: AGENTS.md + AGENCY_PROTOCOL.md
exist at the repo root, are inherited via Jules's lexical scoping, and
carry the must-name tool list + silent-fail verification line.

If a future edit silently drops the canonical incantations these tests
will fail — the doctrine is checked, not narrated.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_MD = REPO_ROOT / "AGENTS.md"
AGENCY_PROTOCOL_MD = REPO_ROOT / "AGENCY_PROTOCOL.md"

# The canonical Jules publish/ask tools that must be named verbatim in
# the doctrine docs so a Jules session reading them via lexical scoping
# learns the exact symbol to call.
MUST_NAME_TOOLS = [
    "pre_commit_instructions",
    "submit",
    "request_user_input",
    "replace_with_git_merge_diff",
    "request_code_review",
]


def test_agents_md_exists_at_repo_root():
    assert AGENTS_MD.is_file(), f"missing: {AGENTS_MD}"


def test_agency_protocol_md_exists_at_repo_root():
    assert AGENCY_PROTOCOL_MD.is_file(), f"missing: {AGENCY_PROTOCOL_MD}"


def test_agents_md_points_at_agency_protocol():
    body = AGENTS_MD.read_text()
    assert "AGENCY_PROTOCOL.md" in body, (
        "AGENTS.md must cite AGENCY_PROTOCOL.md (split-ownership table from DESIGN.md)"
    )


def test_agency_protocol_names_every_must_name_tool():
    body = AGENCY_PROTOCOL_MD.read_text()
    missing = [t for t in MUST_NAME_TOOLS if t not in body]
    assert not missing, (
        f"AGENCY_PROTOCOL.md must name every canonical Jules tool literally; "
        f"missing: {missing}"
    )


def test_agents_md_names_every_must_name_tool():
    body = AGENTS_MD.read_text()
    missing = [t for t in MUST_NAME_TOOLS if t not in body]
    assert not missing, (
        f"AGENTS.md must name every canonical Jules tool literally so a "
        f"Mode-A dispatch inherits the canon via lexical scoping; "
        f"missing: {missing}"
    )


def test_agency_protocol_carries_silent_fail_guard():
    body = AGENCY_PROTOCOL_MD.read_text()
    assert "COMPLETED" in body and "done" in body, "must restate COMPLETED ≠ done"
    assert "git ls-remote" in body, "must instruct verification via git ls-remote"


def test_agents_md_carries_silent_fail_guard():
    body = AGENTS_MD.read_text()
    # AGENTS.md is allowed to defer detail to AGENCY_PROTOCOL.md, but it
    # must at minimum surface the verification rule (the one rule a
    # dispatching agent must internalise before reading the doctrine).
    assert "git ls-remote" in body or "AGENCY_PROTOCOL.md" in body, (
        "AGENTS.md must surface the verify-on-remote rule or point at "
        "AGENCY_PROTOCOL.md which carries it"
    )


def test_agency_protocol_documents_mode_a_and_b():
    body = AGENCY_PROTOCOL_MD.read_text()
    # Mode A/B is the dispatch-side detection (lives in DESIGN.md +
    # AGENTS.md). AGENCY_PROTOCOL is allowed to omit it OR cite it; if
    # it cites, the cite must be discoverable.
    if "Mode" in body:
        # If Mode is mentioned, both modes should be mentioned together.
        assert "Mode A" in body and "Mode B" in body or "dogfood" in body
    # otherwise the file is allowed to scope itself to the doctrine
    # only, with AGENTS.md owning the mode dispatch.


def test_agency_protocol_documents_recovery_flow():
    body = AGENCY_PROTOCOL_MD.read_text()
    assert "EMPTY" in body, "recovery probe must cite the EMPTY escape token"
    assert "patch" in body.lower(), "recovery must reference the patch-extract path"
