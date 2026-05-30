"""Phase 1 RED — `agency/render.py` cleaves a verb's docstring into render
slices keyed by (surface, depth, format).

Done When (subset, Spec 023 §Done When):
- render(node, surface, depth, format) is the single entry point
- non-compliant docstrings get a (mcp, standard, markdown) fallback slice
- the four axes compose orthogonally
"""
from __future__ import annotations

import json

import pytest

from agency.render import render_verb, parse_slices


COMPLIANT_DOC = (
    "Compose an @jules-style PR review-comment body with the mandatory "
    "review-cycle handshake tail (AGENCY_PROTOCOL.md §9).\n\n"
    "Inputs: body (str), intent_id (str).\n"
    "Returns: {text, tail_appended}.\n"
    "chain_next: github.add_issue_comment(body=text).\n\n"
    "The tail instructs Jules to reply_to_pr_comments after pushing — without\n"
    "it the session is blind to the push. Idempotent.\n"
)

LEGACY_DOC = (
    "Spawn a remote Jules session (external effect). Returns id/url/state. "
    "Param completeness: the default require_plan_approval=True is the "
    "recommended doctrine shape the watcher's review_and_approve_plan "
    "WatchEvent is built for."
)

NAME = "capability_jules_review_comment"
ROLE = "effect"


# ---- parse_slices ----------------------------------------------------------


def test_parse_slices_extracts_brief_from_first_paragraph():
    s = parse_slices(COMPLIANT_DOC)
    assert s["brief"].startswith("Compose an @jules-style PR review-comment body")
    # one line; no newlines in the brief
    assert "\n" not in s["brief"]


def test_parse_slices_extracts_inputs_returns_chain_next():
    s = parse_slices(COMPLIANT_DOC)
    assert "body (str)" in s["inputs"]
    assert s["returns"].startswith("{text, tail_appended}")
    assert "github.add_issue_comment" in s["chain_next"]


def test_parse_slices_empty_markers_when_legacy_doc():
    s = parse_slices(LEGACY_DOC)
    # legacy doc has no markers; brief still extracted; other fields empty
    assert s["brief"].startswith("Spawn a remote Jules session")
    assert s["inputs"] == ""
    assert s["returns"] == ""
    assert s["chain_next"] == ""


def test_parse_slices_handles_empty_docstring():
    s = parse_slices("")
    assert s == {"brief": "", "inputs": "", "returns": "", "chain_next": "", "body": ""}


# ---- render_verb: depth axis ----------------------------------------------


def test_depth_brief_emits_name_role_brief_only():
    out = render_verb(NAME, ROLE, COMPLIANT_DOC,
                      surface="mcp", depth="brief", format="markdown")
    assert NAME in out
    assert ROLE in out
    assert "Compose an @jules-style PR review-comment body" in out
    # brief MUST NOT include Inputs/Returns/chain_next
    assert "Inputs:" not in out
    assert "Returns:" not in out
    assert "chain_next:" not in out


def test_depth_standard_adds_inputs_and_returns():
    out = render_verb(NAME, ROLE, COMPLIANT_DOC,
                      surface="mcp", depth="standard", format="markdown")
    assert "Inputs:" in out
    assert "Returns:" in out
    # chain_next is depth=deep only
    assert "chain_next:" not in out


def test_depth_deep_adds_chain_next_and_body():
    out = render_verb(NAME, ROLE, COMPLIANT_DOC,
                      surface="mcp", depth="deep", format="markdown")
    assert "chain_next:" in out
    assert "Idempotent" in out


# ---- render_verb: format axis ---------------------------------------------


def test_format_json_returns_dict_with_structured_fields():
    out = render_verb(NAME, ROLE, COMPLIANT_DOC,
                      surface="mcp", depth="standard", format="json")
    assert isinstance(out, dict)
    assert out["name"] == NAME
    assert out["role"] == ROLE
    assert "brief" in out
    assert "inputs" in out
    assert "returns" in out


def test_format_snippet_emits_code_block_with_call_signature():
    out = render_verb(NAME, ROLE, COMPLIANT_DOC,
                      surface="mcp", depth="standard", format="snippet")
    assert isinstance(out, str)
    assert "```" in out
    assert "call_tool(" in out
    assert NAME in out


def test_format_snippet_bash_surface_uses_cli_syntax():
    out = render_verb(NAME, ROLE, COMPLIANT_DOC,
                      surface="bash", depth="standard", format="snippet")
    assert "agency" in out  # the CLI binary
    assert "execute" in out or "search" in out


# ---- render_verb: legacy fallback -----------------------------------------


def test_legacy_doc_falls_back_to_brief_without_crashing():
    # The fallback slice for non-compliant docstrings is (mcp, standard,
    # markdown) per Spec 023 Done When. brief still extracted; inputs/
    # returns empty.
    out = render_verb(NAME, ROLE, LEGACY_DOC,
                      surface="mcp", depth="brief", format="markdown")
    assert "Spawn a remote Jules session" in out

    # standard depth on a legacy doc still renders — no Inputs: line shown
    # when empty (don't emit empty sections)
    out2 = render_verb(NAME, ROLE, LEGACY_DOC,
                      surface="mcp", depth="standard", format="markdown")
    assert "Inputs:" not in out2  # empty → omitted
    assert "Returns:" not in out2


# ---- token-economy sanity (not the formal budget gate; that's Phase 7) ----


def test_brief_markdown_is_significantly_smaller_than_deep():
    brief = render_verb(NAME, ROLE, COMPLIANT_DOC,
                        surface="mcp", depth="brief", format="markdown")
    deep = render_verb(NAME, ROLE, COMPLIANT_DOC,
                       surface="mcp", depth="deep", format="markdown")
    assert len(brief) < len(deep) // 2, (
        f"brief should be <half of deep; got brief={len(brief)} deep={len(deep)}"
    )
