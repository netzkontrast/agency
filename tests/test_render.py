"""Phase 1 RED — `agency/render.py` cleaves a verb's docstring into render
slices keyed by (surface, depth, format).

Done When (subset, Spec 023 §Done When):
- render(node, surface, depth, format) is the single entry point
- non-compliant docstrings get a (mcp, standard, markdown) fallback slice
- the four axes compose orthogonally
"""
from __future__ import annotations

import ast
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


def test_parse_slices_terminal_chain_next_without_trailing_newline():
    # Finding 4 (Codex, PR #12): a docstring whose final marker block is at
    # end-of-string with NO trailing blank line. The lookahead must anchor on
    # \Z too, else the marker text stays stuck in `body` and the marker slice
    # comes back empty.
    doc = "Do a thing.\n\nchain_next: foo.bar()"
    s = parse_slices(doc)
    assert s["chain_next"] == "foo.bar()"
    # the marker text must NOT leak into body
    assert "chain_next" not in s["body"]
    assert "foo.bar()" not in s["body"]


def test_parse_slices_terminal_inputs_and_returns_without_trailing_newline():
    # Same EOF-anchor defect for Inputs:/Returns: as the final block.
    assert parse_slices("Do.\n\nInputs: a (str), b (int)")["inputs"] == "a (str), b (int)"
    assert parse_slices("Do.\n\nReturns: {x, y}")["returns"] == "{x, y}"


def test_parse_slices_full_marker_run_terminal_chain_next():
    # All three markers in order, the run ending at EOF on chain_next with no
    # trailing newline — every slice captured, nothing left in body.
    doc = "Do.\n\nInputs: a (str).\nReturns: x.\nchain_next: foo.bar()"
    s = parse_slices(doc)
    assert s["inputs"].startswith("a (str)")
    assert s["returns"].startswith("x")
    assert s["chain_next"] == "foo.bar()"
    assert s["body"] == ""


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


def test_standard_depth_exposes_full_legacy_body():
    # Finding 6 (Codex, PR #12): a legacy (markerless) multi-paragraph
    # docstring keeps paragraphs 2+ in `body`. Spec 023 says the standard
    # fallback should expose the whole docstring — it must not collapse to
    # the first sentence only.
    legacy3 = (
        "First paragraph one-liner gist.\n\n"
        "Second paragraph with crucial elaboration.\n\n"
        "Third paragraph with even more detail."
    )
    brief = render_verb(NAME, ROLE, legacy3,
                        surface="mcp", depth="brief", format="markdown")
    standard = render_verb(NAME, ROLE, legacy3,
                           surface="mcp", depth="standard", format="markdown")
    # brief stays a one-liner; standard exposes the rest of the body
    assert "Second paragraph" not in brief
    assert "Second paragraph" in standard
    assert "Third paragraph" in standard


def test_standard_depth_keeps_compliant_body_deep_only():
    # Guard the other side of Finding 6: when markers DO exist, `body` stays
    # deep-only so `standard` remains token-tight. (COMPLIANT_DOC's body is
    # the "The tail instructs Jules… Idempotent." trailer.)
    standard = render_verb(NAME, ROLE, COMPLIANT_DOC,
                           surface="mcp", depth="standard", format="markdown")
    assert "Idempotent" not in standard
    deep = render_verb(NAME, ROLE, COMPLIANT_DOC,
                       surface="mcp", depth="deep", format="markdown")
    assert "Idempotent" in deep


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


def test_format_snippet_mcp_renders_valid_python_dict_with_named_keys():
    # Finding 5 (Codex, PR #12): the snippet must interpolate parsed input
    # NAMES as dict keys, not the raw `Inputs:` prose. `Inputs: body (str),
    # intent_id (str)` previously produced `{ body (str), intent_id (str) }`
    # which is not valid Python.
    out = render_verb(NAME, ROLE, COMPLIANT_DOC,
                      surface="mcp", depth="standard", format="snippet")
    assert '"body": ...' in out
    assert '"intent_id": ...' in out
    # the raw prose / type hints must NOT bleed into the snippet
    assert "(str)" not in out
    # the interpolated dict literal must be valid, parseable Python
    dict_literal = out[out.index("{"):out.rindex("}") + 1]
    parsed = ast.literal_eval(dict_literal)
    assert parsed == {"body": ..., "intent_id": ...}


def test_format_snippet_falls_back_to_placeholder_when_no_inputs():
    # R4 (Codex review of 660d7f5): the original Finding-5 fix landed
    # `{...}` as the empty-inputs placeholder, but `{...}` is a set
    # containing Ellipsis — NOT a dict. call_tool's second arg must be a
    # Mapping; passing a set fails at runtime. Empty-inputs falls back
    # to `{}` (empty dict). LEGACY_DOC has no Inputs: marker.
    out = render_verb(NAME, ROLE, LEGACY_DOC,
                      surface="mcp", depth="standard", format="snippet")
    assert "{}" in out
    assert "{...}" not in out, "`{...}` is a set-of-Ellipsis, not a valid dict params mapping"


def test_format_snippet_bash_surface_uses_cli_syntax():
    out = render_verb(NAME, ROLE, COMPLIANT_DOC,
                      surface="bash", depth="standard", format="snippet")
    assert "agency" in out  # the CLI binary
    assert "execute" in out or "search" in out


def test_format_snippet_bash_uses_python_m_cli_not_bare_agency():
    # Finding 9 (Codex, PR #12): the `agency` console script points at the
    # MCP server (agency.__main__:main), not the CLI. The bash snippet must
    # invoke `python -m agency.cli` to actually reach `execute`.
    out = render_verb(NAME, ROLE, COMPLIANT_DOC,
                      surface="bash", depth="standard", format="snippet")
    assert "python -m agency.cli" in out
    assert "agency --db" not in out  # must not call the bare console script


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
