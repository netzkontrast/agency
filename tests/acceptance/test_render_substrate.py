"""Acceptance — render substrate and response envelope (Spec 023 / 146 / 154).

Converted from tests/test_render.py, tests/test_render_folder.py,
tests/test_response_prefix_discipline.py.

Dropped (implementation / structural / not observable behaviour):
- test_render_folder_files_exist: structural check that render template files
  exist on disk — a filesystem layout invariant, not wire behaviour.
- test_skill_md_template_loads_from_file, test_command_md_template_loads_from_file,
  test_step_doc_template_loads_from_file: test internal template module imports
  and substitute calls — implementation details.
- test_format_snippet_bash_surface_uses_cli_syntax: tests an internal rendering
  mode (surface="bash") that is not reachable via the wire.
- test_format_snippet_bash_uses_python_m_cli_not_bare_agency: same internal
  bash-surface mode.
- ResponseEnvelope.to_dict rejects non-dict prefix or body: construction-time
  TypeError is implementation detail of the dataclass, not observable behaviour.
- test_agency_welcome_prefix_is_byte_stable (_find_tool introspection via
  FastMCP internals): covered by the wire-level welcome prefix stability
  scenario in test_welcome.py.
- capture_body_overflow_rejects_negative_budget / zero_budget / handle_total
  variants: implementation invariants; the observable behaviour (truncation,
  prefix stability) is covered.
"""
from __future__ import annotations

import asyncio
import json
import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine
from agency.disclosure import parse_slices, render_verb
from agency._envelope import (
    ResponseEnvelope,
    canonical_json,
    capability_set_hash,
    capture_body_overflow,
)

scenarios("features/render_substrate.feature")


# ── test data ─────────────────────────────────────────────────────────────────

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
    "recommended doctrine shape."
)

NAME = "lifecycle_jules_review_comment"
ROLE = "effect"

_CHAR_COUNTER = len  # 1 char ≈ 1 token for envelope tests


# ── shared Given override ─────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="render_engine")
def _fresh_render_engine():
    return Engine(":memory:")


# ── when — parse_slices ───────────────────────────────────────────────────────

@when("I parse a compliant verb docstring", target_fixture="slices")
def _parse_compliant():
    return parse_slices(COMPLIANT_DOC)


@when("I parse a legacy verb docstring without markers", target_fixture="slices")
def _parse_legacy():
    return parse_slices(LEGACY_DOC)


# ── then — parse_slices compliant ────────────────────────────────────────────

@then("the brief is the first-paragraph one-liner without newlines")
def _brief_one_liner(slices):
    assert slices["brief"].startswith("Compose an @jules-style PR review-comment body")
    assert "\n" not in slices["brief"]


@then("inputs contains the declared parameter names")
def _inputs_params(slices):
    assert "body (str)" in slices["inputs"]
    assert "intent_id (str)" in slices["inputs"]


@then("returns contains the declared return shape")
def _returns_shape(slices):
    assert slices["returns"].startswith("{text, tail_appended}")


@then("chain_next contains the declared next call")
def _chain_next(slices):
    assert "github.add_issue_comment" in slices["chain_next"]


# ── then — parse_slices legacy ───────────────────────────────────────────────

@then("the brief is the first paragraph")
def _brief_first_para(slices):
    assert slices["brief"].startswith("Spawn a remote Jules session")


@then("inputs returns and chain_next are all empty")
def _empty_markers(slices):
    assert slices["inputs"] == ""
    assert slices["returns"] == ""
    assert slices["chain_next"] == ""


# ── when — render_verb depth axis ────────────────────────────────────────────

@when("I render a compliant docstring at brief depth", target_fixture="brief_output")
def _render_brief():
    return render_verb(NAME, ROLE, COMPLIANT_DOC, surface="mcp",
                       depth="brief", format="markdown")


@when("I render a compliant docstring at standard depth", target_fixture="standard_output")
def _render_standard():
    return render_verb(NAME, ROLE, COMPLIANT_DOC, surface="mcp",
                       depth="standard", format="markdown")


@when("I render a compliant docstring at deep depth", target_fixture="deep_output")
def _render_deep():
    return render_verb(NAME, ROLE, COMPLIANT_DOC, surface="mcp",
                       depth="deep", format="markdown")


@when("I render the same docstring at deep depth", target_fixture="deep_output_2")
def _render_deep_2():
    return render_verb(NAME, ROLE, COMPLIANT_DOC, surface="mcp",
                       depth="deep", format="markdown")


# ── then — brief depth ───────────────────────────────────────────────────────

@then("the output contains the verb name and role")
def _name_role_in_brief(brief_output):
    assert NAME in brief_output
    assert ROLE in brief_output


@then("the output contains the one-line brief")
def _brief_text(brief_output):
    assert "Compose an @jules-style PR review-comment body" in brief_output


@then("the output does not contain Inputs or Returns")
def _no_inputs_returns_in_brief(brief_output):
    assert "Inputs:" not in brief_output
    assert "Returns:" not in brief_output


# ── then — standard depth ────────────────────────────────────────────────────

@then("the output contains Inputs")
def _has_inputs(standard_output):
    assert "Inputs:" in standard_output


@then("the output contains Returns")
def _has_returns(standard_output):
    assert "Returns:" in standard_output


@then("the output does not contain chain_next")
def _no_chain_next(standard_output):
    assert "chain_next:" not in standard_output


# ── then — deep depth ────────────────────────────────────────────────────────

@then("the output contains chain_next")
def _has_chain_next(deep_output):
    assert "chain_next:" in deep_output


@then("the output contains the body detail")
def _has_body_detail(deep_output):
    assert "Idempotent" in deep_output


# ── then — size comparison ────────────────────────────────────────────────────

@then("the brief output is less than half the size of the deep output")
def _brief_smaller(brief_output, deep_output_2):
    assert len(brief_output) < len(deep_output_2) // 2, (
        f"brief ({len(brief_output)}) should be <half of deep ({len(deep_output_2)})")


# ── when — json format ───────────────────────────────────────────────────────

@when("I render a compliant docstring in json format at standard depth",
      target_fixture="json_output")
def _render_json():
    return render_verb(NAME, ROLE, COMPLIANT_DOC, surface="mcp",
                       depth="standard", format="json")


@then("the result is a dict with name role brief inputs and returns")
def _json_shape(json_output):
    assert isinstance(json_output, dict)
    for key in ("name", "role", "brief", "inputs", "returns"):
        assert key in json_output


# ── when — snippet format ─────────────────────────────────────────────────────

@when("I render a compliant docstring in snippet format at standard depth",
      target_fixture="snippet_output")
def _render_snippet():
    return render_verb(NAME, ROLE, COMPLIANT_DOC, surface="mcp",
                       depth="standard", format="snippet")


@when("I render a legacy docstring in snippet format at standard depth",
      target_fixture="legacy_snippet_output")
def _render_legacy_snippet():
    return render_verb(NAME, ROLE, LEGACY_DOC, surface="mcp",
                       depth="standard", format="snippet")


@then("the result contains a code block with call_tool")
def _snippet_code_block(snippet_output):
    assert "```" in snippet_output
    assert "call_tool(" in snippet_output


@then("the argument keys are the parsed input names not raw prose")
def _snippet_arg_keys(snippet_output):
    assert '"body": ...' in snippet_output
    assert '"intent_id": ...' in snippet_output
    assert "(str)" not in snippet_output


@then("the snippet contains _TODO and get_schema")
def _legacy_todo(legacy_snippet_output):
    assert "_TODO" in legacy_snippet_output
    assert "get_schema" in legacy_snippet_output


@then("the call_tool argument is a dict not a set")
def _legacy_dict_arg(legacy_snippet_output):
    import ast
    code = legacy_snippet_output.split("```python")[1].split("```")[0].strip()
    tree = ast.parse(code)
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and getattr(n.func, "id", "") == "call_tool")
    assert isinstance(call.args[1], ast.Dict), (
        f"call_tool's 2nd arg must be a Dict, got {type(call.args[1]).__name__}")


# ── when — registered descriptions ───────────────────────────────────────────

@when("a client lists all capability tools", target_fixture="cap_tools_info")
def _list_cap_tools(render_engine):
    async def _run():
        mcp = render_engine.build_mcp(codemode=False)
        tools_list = await mcp._list_tools()
        return {t.name: t for t in tools_list}
    return asyncio.run(_run()), render_engine


@then("each tool description is the brief slice of its docstring")
def _descriptions_are_brief(cap_tools_info):
    tools, eng = cap_tools_info
    from agency.disclosure import parse_slices
    heavy = "lifecycle_jules_dispatch"
    assert heavy in tools, f"verb {heavy} not registered"
    described = tools[heavy].description or ""
    src_doc = eng.registry.get("jules").verbs["dispatch"]["fn"].__doc__ or ""
    brief = parse_slices(src_doc)["brief"]
    assert brief, "source docstring must yield a non-empty brief"
    assert described == brief


@then("the cumulative tight descriptions are less than half the legacy full-docstring total")
def _descriptions_save_tokens(cap_tools_info):
    tools, eng = cap_tools_info
    from agency.capability import is_cap_tool
    cap_tools = {n: t for n, t in tools.items() if is_cap_tool(n)}
    tight = sum(len(t.description or "") for t in cap_tools.values())
    legacy = 0
    for cap_name in eng.registry.names():
        for _verb, spec in eng.registry.get(cap_name).verbs.items():
            doc = (spec["fn"].__doc__ or "").strip()
            legacy += len(doc)
    assert tight < legacy // 2, (
        f"tight={tight} legacy={legacy}; tight should be <half of legacy")


# ── when — ResponseEnvelope ───────────────────────────────────────────────────

@when("I create an envelope with separate prefix and body",
      target_fixture="envelope")
def _make_envelope():
    return ResponseEnvelope(prefix={"a": 1, "b": 2}, body={"c": 3})


@then("to_dict returns all keys from both halves")
def _to_dict_merged(envelope):
    d = envelope.to_dict()
    assert d["a"] == 1 and d["b"] == 2 and d["c"] == 3


@then("overlapping keys raise a ValueError")
def _overlapping_raises():
    env = ResponseEnvelope(prefix={"x": 1}, body={"x": 2})
    with pytest.raises(ValueError, match="overlap"):
        env.to_dict()


@when("I create an envelope with prefix keys and body keys",
      target_fixture="keyed_envelope")
def _make_keyed_envelope():
    return ResponseEnvelope(prefix={"alpha": 1, "beta": 2},
                             body={"gamma": 3, "delta": 4})


@then("canonical_json output has all prefix keys before body keys")
def _prefix_first(keyed_envelope):
    blob = canonical_json(keyed_envelope)
    decoded = json.loads(blob, object_pairs_hook=list)
    keys = [k for k, _ in decoded]
    prefix_keys = sorted(keyed_envelope.prefix.keys())
    body_keys = sorted(keyed_envelope.body.keys())
    assert keys == prefix_keys + body_keys


@then("the serialization is deterministic regardless of insertion order")
def _deterministic(keyed_envelope):
    a = ResponseEnvelope(prefix={"z": 1, "a": 2}, body={"y": 3, "b": 4})
    b = ResponseEnvelope(prefix={"a": 2, "z": 1}, body={"b": 4, "y": 3})
    assert canonical_json(a) == canonical_json(b)


@then("canonical_json uses compact separators")
def _compact_seps(keyed_envelope):
    blob = canonical_json(keyed_envelope)
    assert ", " not in blob and ": " not in blob


# ── when — prefix hash ────────────────────────────────────────────────────────

@when("I create two envelopes with the same prefix but different bodies",
      target_fixture="same_prefix_envs")
def _same_prefix():
    a = ResponseEnvelope(prefix={"capability_set_hash": "abc"}, body={"intent_id": "i1"})
    b = ResponseEnvelope(prefix={"capability_set_hash": "abc"}, body={"intent_id": "i2"})
    return a, b


@then("the prefix hashes are equal")
def _same_prefix_hash(same_prefix_envs):
    a, b = same_prefix_envs
    assert a.prefix_hash() == b.prefix_hash()


@when("I create two envelopes with different prefixes",
      target_fixture="diff_prefix_envs")
def _diff_prefix():
    a = ResponseEnvelope(prefix={"capability_set_hash": "abc"}, body={})
    b = ResponseEnvelope(prefix={"capability_set_hash": "xyz"}, body={})
    return a, b


@then("the prefix hashes differ")
def _diff_prefix_hash(diff_prefix_envs):
    a, b = diff_prefix_envs
    assert a.prefix_hash() != b.prefix_hash()


# ── when — capture_body_overflow ─────────────────────────────────────────────

@when("I capture body overflow with a budget larger than the body",
      target_fixture="overflow_fit_result")
def _overflow_fits():
    env = ResponseEnvelope(
        prefix={"schema_version": 1},
        body={"intents": 3, "last_intent": "intent:x"})
    return capture_body_overflow(env, max_body_tokens=10_000, counter=_CHAR_COUNTER)


@then("the returned envelope body is unchanged")
def _body_unchanged(overflow_fit_result):
    assert overflow_fit_result.envelope.body == {"intents": 3, "last_intent": "intent:x"}


@then("the overflow handle is None")
def _handle_none(overflow_fit_result):
    assert overflow_fit_result.handle is None


@when("I capture body overflow with a budget smaller than the body",
      target_fixture="overflow_truncate_result")
def _overflow_truncates():
    env = ResponseEnvelope(prefix={"schema_version": 1}, body={"transcript": "X" * 500})
    return capture_body_overflow(env, max_body_tokens=80, counter=_CHAR_COUNTER)


@then("the returned envelope body contains _overflow_preview and _overflow_handle")
def _overflow_shape(overflow_truncate_result):
    body = overflow_truncate_result.envelope.body
    assert "_overflow_preview" in body
    assert "_overflow_handle" in body


@then("the overflow handle reports truncated True")
def _handle_truncated(overflow_truncate_result):
    assert overflow_truncate_result.handle is not None
    assert overflow_truncate_result.handle.truncated is True


@then("the prefix is byte-identical to the original prefix")
def _prefix_stable_overflow(overflow_truncate_result):
    original = {"schema_version": 1}
    assert overflow_truncate_result.envelope.prefix == original
