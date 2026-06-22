"""Acceptance — skill authoring grounding context (Spec 374 Slice 1).

The grounding builder (`skill_generator.ground`) reads a capability's live
surface — verbs, signatures (sans injected params), docstrings, ontology — into
a structured dict. Pure + deterministic; the no-host fallback an author reads by
hand. Assertions derive from the live registry (rule 8 — no snapshotted lists).
"""
from __future__ import annotations

import json

from pytest_bdd import parsers, scenarios, then, when


scenarios("features/skill_author.feature")

GROUND_CAP = "analyze"


def _ground(engine, iid, capability):
    raw, _ = engine.registry.invoke(
        engine.memory, iid, "skill_generator", "ground", capability=capability)
    return raw["result"] if isinstance(raw, dict) and "result" in raw else raw


def _author(engine, iid, capability, skill_type):
    raw, _ = engine.registry.invoke(
        engine.memory, iid, "skill_generator", "author",
        capability=capability, skill_type=skill_type)
    return raw["result"] if isinstance(raw, dict) and "result" in raw else raw


class _StubHostCtx:
    """A sampling-capable host that returns a canned completion (the Driver seam
    stubbed — Spec 374 Slice 2 acceptance: "with a stub Driver")."""
    def __init__(self, text):
        self._text = text

    async def sample(self, messages, **kwargs):
        return type("_Result", (), {"text": self._text})()


# A canned, schema-valid discipline skill the stub host "samples".
_CANNED_DISCIPLINE = json.dumps({
    "name": "analyze-discipline", "kind": "discipline", "type": "discipline",
    "description": "Use when assessing a codebase for quality before shipping.",
    "common_mistakes": [
        {"symptom": "scoring opinions", "counter": "only decidable findings"}],
})


# ── When ──────────────────────────────────────────────────────────────────────

@when(parsers.parse('I ground skill authoring for the "{cap}" capability'),
      target_fixture="grounding")
def _do_ground(engine, confirmed_intent, cap):
    return _ground(engine, confirmed_intent, cap)


@when(parsers.parse('I ground skill authoring for the "{cap}" capability again'),
      target_fixture="grounding_again")
def _do_ground_again(engine, confirmed_intent, cap):
    return _ground(engine, confirmed_intent, cap)


# ── Then ──────────────────────────────────────────────────────────────────────

@then("the grounding lists exactly the live verbs of that capability")
def _lists_live_verbs(engine, grounding):
    live = set(engine.registry.get(GROUND_CAP).verbs)
    grounded = {v["name"] for v in grounding["verbs"]}
    assert grounded == live, (
        f"grounding must list exactly the live verbs; got {grounded} vs {live}")


@then("each grounded verb mirrors its live role and docstring")
def _verbs_mirror_source(engine, grounding):
    cap = engine.registry.get(GROUND_CAP)
    for v in grounding["verbs"]:
        fn = cap.verbs[v["name"]].get("fn")
        assert v["doc"] == (fn.__doc__ or ""), (
            f"verb {v['name']!r} doc must mirror the live source (one source)")
        assert v["role"] == cap.role(v["name"]), (
            f"verb {v['name']!r} role must mirror the live registry")
        assert v["signature"].startswith("("), (
            f"verb {v['name']!r} must carry a call signature")


@then("each grounded verb signature omits the injected parameters")
def _signature_omits_injected(grounding):
    # `self` / `ctx` / declared injects are engine-supplied, not author-facing —
    # an author referencing the verb never passes them, so the grounding must not
    # advertise them.
    for v in grounding["verbs"]:
        first = v["signature"].lstrip("(").split(",", 1)[0].split(":", 1)[0].strip()
        assert first not in ("self", "ctx"), (
            f"verb {v['name']!r} signature leaks an injected param: {v['signature']}")


@then("the grounding summarises the capability's ontology")
def _has_ontology(grounding):
    assert "ontology" in grounding
    for k in ("nodes", "edges", "skills"):
        assert k in grounding["ontology"], f"ontology summary missing {k!r}"


@then("the two groundings are identical")
def _deterministic(grounding, grounding_again):
    assert grounding == grounding_again, "grounding must be deterministic (A7)"


@then("the grounding result is an error naming the unknown capability")
def _error_unknown(grounding):
    assert "error" in grounding, f"expected a typed error; got {grounding!r}"
    assert "no-such-cap" in grounding["error"]


# ── Spec 374 Slice 2 — author (per-type prompt + host.sample) ─────────────────

@when(parsers.parse('I author a "{skill_type}" skill for "{cap}" with a stub '
                    'sampling host'),
      target_fixture="author_result")
def _author_with_host(engine, confirmed_intent, skill_type, cap):
    from agency._host_bridge import bind_host_context, reset_host_context
    token = bind_host_context(_StubHostCtx(_CANNED_DISCIPLINE))
    try:
        return _author(engine, confirmed_intent, cap, skill_type)
    finally:
        reset_host_context(token)


@when(parsers.parse('I author a "{skill_type}" skill for "{cap}" with no host bound'),
      target_fixture="author_result")
def _author_no_host(engine, confirmed_intent, skill_type, cap):
    return _author(engine, confirmed_intent, cap, skill_type)


@then(parsers.parse('the author result status is "{status}"'))
def _author_status(author_result, status):
    assert author_result.get("status") == status, (
        f"expected status={status!r}, got {author_result.get('status')!r} "
        f"({author_result})")


@then(parsers.parse('the draft is a schema-valid skill of type "{skill_type}"'))
def _draft_schema_valid(author_result, skill_type):
    from agency._skill_parse import parse_skill
    draft = author_result.get("draft")
    assert isinstance(draft, dict), f"expected a draft dict; got {draft!r}"
    res = parse_skill(draft)
    assert res.ok, f"draft must satisfy the 371 schema; got {res.code}: {res.message}"
    assert draft.get("type") == skill_type


@then("the prompt lists exactly the capability's live verbs")
def _prompt_lists_live_verbs(engine, author_result):
    # The grounding the prompt is built from must reference exactly the live
    # verbs (F3 anti-hallucination floor) — derived from the registry (rule 8).
    user = author_result["prompt"]["user"]
    for v in engine.registry.get(GROUND_CAP).verbs:
        assert v in user, f"prompt must reference live verb {v!r}"


@then("the prompt instructs strict JSON output")
def _prompt_strict_json(author_result):
    blob = (author_result["prompt"]["system"] + author_result["prompt"]["user"]).upper()
    assert "JSON" in blob, "the skill-creator prompt must instruct JSON output"


@then("the result carries the grounding and the per-type prompt")
def _carries_grounding_and_prompt(author_result):
    assert "grounding" in author_result and author_result["grounding"]["verbs"]
    prompt = author_result.get("prompt", {})
    assert prompt.get("system") and prompt.get("user"), (
        "no-host return must carry the system+user prompt for hand-authoring")


@then("the per-type prompt names the type's required fields")
def _prompt_names_required(author_result):
    # Derived from the single source (_TYPE_REQUIRED), not a literal — rule 2/8.
    from agency._skill_parse import _TYPE_REQUIRED
    stype = author_result["type"]
    required = _TYPE_REQUIRED.get(stype, ())
    blob = author_result["prompt"]["system"] + author_result["prompt"]["user"]
    for field in required:
        assert field in blob, (
            f"prompt for type {stype!r} must name required field {field!r}")
