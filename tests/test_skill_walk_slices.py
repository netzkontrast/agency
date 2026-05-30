"""Spec 025 Phase 1 RED — `render_phase`: Spec 023 slices applied to phases.

A skill phase is the unit of `skill_walk` disclosure. Per Spec 025 design:
- **T1 cue** (depth=brief): ≤120-char imperative — what to do next.
  Hard-gate phases state the GATE QUESTION (contains "?").
- **T2 instruction** (depth=standard): + `produces` keys + gate type.
- **T3 reference** (depth=deep): + the heavy how-to (rare; only when needed).

Verb-bound phases (with `invoke={capability, verb}`) DELEGATE to
`render_verb` of the bound verb — never author a duplicate cue.
"""
from __future__ import annotations

import ast

import pytest

from agency.render import render_phase, render_verb
from agency.engine import Engine


def test_render_phase_t1_cue_is_short_and_imperative():
    """Phase at depth=brief renders the T1 cue: one imperative line,
    ≤120 chars, no produces/gate detail."""
    phase = {
        "index": 1, "name": "explore",
        "produces": ["questions", "assumptions"],
        "cue": "Ask probing questions to surface assumptions.",
    }
    out = render_phase(phase, depth="brief")
    assert isinstance(out, str)
    assert len(out) <= 120, f"T1 cue too long: {len(out)} chars"
    assert "Ask probing questions" in out
    # T1 carries NO produces / gate detail
    assert "questions" not in out or "Ask" in out  # the cue text itself may use the word
    assert "produces" not in out.lower()
    assert "gate" not in out.lower()


def test_render_phase_t1_hard_gate_states_a_question():
    """A hard-gate phase's T1 cue contains '?' — it asks the user/agent
    to confirm; the question is the gate."""
    phase = {
        "index": 3, "name": "confirm",
        "produces": ["user_confirmed"],
        "gate": "hard",
        "cue": "Confirm: does the design match what we agreed?",
    }
    out = render_phase(phase, depth="brief")
    assert "?" in out, (
        "hard-gate phase T1 must read as a question (the gate is the "
        f"question that pauses the walk); got: {out!r}"
    )


def test_render_phase_t2_adds_produces_and_gate():
    """depth=standard adds the data-flow contract — what this phase
    produces (keys flowing to the next phase) and whether there's a gate."""
    phase = {
        "index": 1, "name": "explore",
        "produces": ["questions", "assumptions"],
        "cue": "Ask probing questions.",
    }
    out = render_phase(phase, depth="standard")
    assert "produces" in out.lower() or "questions" in out
    assert "assumptions" in out


def test_verb_bound_phase_inherits_verb_slice():
    """A phase carrying `invoke={capability, verb}` renders via the
    BOUND verb's Spec-023 slice, not a hand-authored cue. This is the
    'never duplicate' rule from the design: the `review` skill's
    dispatch phase is bound to `delegate.fan_out` — its render is
    `render_verb(fan_out, depth=…)`, period.

    Concrete: the rendered string must contain the verb name
    `delegate.fan_out` (or its MCP tool name) — proof we delegated to
    `render_verb` rather than fabricating cue text.
    """
    e = Engine(":memory:")
    try:
        # the `review` skill (develop capability) phase 2 binds to delegate.fan_out
        develop_skills = e.registry.get("develop").ontology.skills
        review_phases = develop_skills["review"]["phases"]
        dispatch_phase = next(p for p in review_phases if p.get("invoke"))
        # sanity: this is the phase shape we expect
        assert dispatch_phase["invoke"]["capability"] == "delegate"
        assert dispatch_phase["invoke"]["verb"] == "fan_out"
        # render — should delegate to the verb's slice
        out = render_phase(dispatch_phase, depth="brief", registry=e.registry)
        assert "fan_out" in out, (
            f"verb-bound phase must inherit render_verb output of the bound "
            f"verb (delegate.fan_out); got: {out!r}"
        )
    finally:
        e.memory.close()


def test_hard_gate_phase_without_cue_still_asks_a_question():
    """R3 (Codex review of 660d7f5): the `gate="hard"` contract requires
    a question at T1 — but legacy schemas (e.g. develop.review's resolve
    phase) carry `gate="hard"` with no explicit `cue`. The fallback must
    synthesize a confirmation question, not emit `Execute the X phase.`"""
    phase = {
        "index": 3, "name": "resolve",
        "produces": ["addressed"], "gate": "hard",
        # NO cue field
    }
    out = render_phase(phase, depth="brief")
    assert "?" in out, (
        f"hard-gate cue-less fallback must read as a question (R3); got {out!r}"
    )
    assert "Execute the" not in out, (
        "the legacy 'Execute the X phase.' fallback breaks the hard-gate T1 contract"
    )


def test_snippet_empty_inputs_is_valid_callable_python():
    """R4 (Codex review of 660d7f5): `{...}` is a set containing Ellipsis,
    not a dict. `call_tool("x", set)` fails at runtime — call_tool's
    second arg must be a Mapping. The empty-inputs fallback must produce
    a valid params dict that survives ast.parse AND can be passed to
    a function expecting **kwargs."""
    DOC_NO_INPUTS = "Spawn a remote Jules session."
    out = render_verb("capability_jules_dispatch", "effect", DOC_NO_INPUTS,
                      surface="mcp", depth="standard", format="snippet")
    # must contain `{}` (empty dict), NOT `{...}` (set of Ellipsis)
    assert '{...}' not in out, f"`{{...}}` is a set-of-Ellipsis, not a dict params mapping: {out}"
    assert '{}' in out, f"empty-inputs snippet should fall back to `{{}}`; got: {out}"
    # the snippet must be parseable Python AND the params arg must be a dict
    code = out.split("```python")[1].split("```")[0].strip() if "```python" in out else ""
    assert code, f"expected a ```python``` block; got: {out!r}"
    tree = ast.parse(code)
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and getattr(n.func, "id", "") == "call_tool")
    assert isinstance(call.args[1], ast.Dict), (
        f"call_tool's second arg must be a Dict node, got {type(call.args[1]).__name__}"
    )


def test_render_phase_missing_cue_falls_back_gracefully():
    """A phase without a `cue` field (legacy, not yet migrated) renders
    a usable T1 from the phase name — never crashes, even if ugly. The
    Spec 025 lint will flag it, but the renderer must be robust."""
    phase = {"index": 1, "name": "explore", "produces": ["questions"]}
    out = render_phase(phase, depth="brief")
    assert isinstance(out, str) and out, "must render SOMETHING non-empty"
    assert "explore" in out.lower()
