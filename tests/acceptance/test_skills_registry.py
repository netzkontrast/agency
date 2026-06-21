"""Acceptance — skills registry behaviour.

Converted from:
  tests/test_skills_index.py        (Spec 026 — skills.index graph promotion)
  tests/test_skill_first_discovery.py (Spec 025 — skill tag wiring on verbs)
  tests/test_skills_matcher_result.py (Spec 162 — MatcherResult typed shape)

Dropped as implementation/structural (not observable behaviour):
  test_skills_api_binding.py — verifies the Anthropic Python SDK signature;
    depends on [publish] extra that CI doesn't install. Pure SDK binding
    mapping, not engine behaviour.
"""
from __future__ import annotations

import tempfile

from pytest_bdd import scenarios, then, when


scenarios("features/skills_registry.feature")


# ── helpers ──────────────────────────────────────────────────────────────────

def _call(engine, iid, cap, verb, **kw):
    res, _ = engine.registry.invoke(engine.memory, iid, cap, verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


def _verb_spec(engine, capability, verb):
    return engine.registry.get(capability).verbs[verb]


# ── When steps — skills.index ─────────────────────────────────────────────────

@when("I invoke \"skills\" \"index\"", target_fixture="index_result")
def _index_once(engine, confirmed_intent):
    return _call(engine, confirmed_intent, "skills", "index")


@when("I invoke \"skills\" \"index\" twice", target_fixture="index_result_pair")
def _index_twice(engine, confirmed_intent):
    r1 = _call(engine, confirmed_intent, "skills", "index")
    r2 = _call(engine, confirmed_intent, "skills", "index")
    return {"r1": r1, "r2": r2, "engine": engine, "iid": confirmed_intent}


# ── Then steps — skills.index ─────────────────────────────────────────────────

@then("the result reports at least one skill and one phase")
def _at_least_one(index_result):
    assert index_result["skills"] >= 1
    assert index_result["phases"] >= 1


@then("the graph census shows Skill and Phase nodes matching those counts")
def _census_matches(engine, confirmed_intent, index_result):
    census = _call(engine, confirmed_intent, "analyze", "graph")["census"]
    assert census.get("Skill", 0) == index_result["skills"]
    assert census.get("Phase", 0) == index_result["phases"]


@then("the \"skills-triage\" Skill node has kind \"discipline\"")
def _triage_kind(engine):
    node = engine.memory.recall("skill:skills-triage")
    assert node and node.get("kind") == "discipline"


@then("it has an associated Phase node linking back to the skill")
def _has_phase_node(engine):
    p1 = engine.memory.recall("phase:skills-triage:1")
    assert p1 and p1.get("skill") == "skills-triage"


@then("both calls return the same counts")
def _same_counts(index_result_pair):
    assert index_result_pair["r1"] == index_result_pair["r2"]


@then("the graph has no duplicate Skill nodes")
def _no_duplicates(index_result_pair):
    eng = index_result_pair["engine"]
    iid = index_result_pair["iid"]
    census = _call(eng, iid, "analyze", "graph")["census"]
    assert census["Skill"] == index_result_pair["r1"]["skills"]


# ── Then steps — skill tag wiring ─────────────────────────────────────────────

@then("the \"delegate\" \"fan_out\" verb carries the tag \"skill:review\"")
def _fan_out_tagged(engine):
    spec = _verb_spec(engine, "delegate", "fan_out")
    assert "tags" in spec
    assert "skill:review" in spec["tags"]


@then("the \"delegate\" \"fan_out\" verb's tags collection is a set type")
def _tags_is_set(engine):
    spec = _verb_spec(engine, "delegate", "fan_out")
    assert isinstance(spec["tags"], (set, frozenset))


@then("the \"reflect\" \"note\" verb has no skill tags")
def _note_no_skill_tags(engine):
    spec = _verb_spec(engine, "reflect", "note")
    assert "tags" in spec
    skill_tags = {t for t in spec["tags"] if t.startswith("skill:")}
    assert skill_tags == set()


@then("an extra_capability verb with a hand-written skill tag has that tag removed")
def _hand_tag_stripped(engine):
    from agency.capability import Capability
    from agency.engine import Engine
    cap = Capability(
        name="rogue",
        home="capability",
        verbs={
            "act": {
                "role": "act",
                "fn": lambda **_kw: {"result": "ok"},
                "inject": [],
                "tags": {"skill:i-made-this-up"},
            },
        },
    )
    e = Engine(tempfile.mktemp(suffix=".db"),
               extra_capabilities=[cap], _require_skill_doc=False)
    try:
        spec = _verb_spec(e, "rogue", "act")
        assert "skill:i-made-this-up" not in spec["tags"]
    finally:
        e.memory.close()


# ── When steps — MatcherResult ────────────────────────────────────────────────

@when("I build a MatcherResult with skill \"tdd\", confidence 0.9, matcher \"pattern\"",
      target_fixture="matcher_result")
def _build_valid_mr():
    from agency.capabilities.skills import MatcherResult
    return MatcherResult(skill_id="tdd", confidence=0.9,
                         rationale="pattern:tdd matched", matcher="pattern")


@when("I build a MatcherResult with confidence 1.5", target_fixture="mr_error")
def _build_over_confidence():
    from agency.capabilities.skills import MatcherResult
    try:
        MatcherResult(skill_id="x", confidence=1.5, rationale="r", matcher="pattern")
        return None
    except ValueError as e:
        return e


@when("I build a MatcherResult with a 201-character rationale", target_fixture="mr_error")
def _build_long_rationale():
    from agency.capabilities.skills import MatcherResult
    try:
        MatcherResult(skill_id="x", confidence=0.5, rationale="a" * 201, matcher="pattern")
        return None
    except ValueError as e:
        return e


@when("I build a MatcherResult with matcher \"bogus\"", target_fixture="mr_error")
def _build_bad_matcher():
    from agency.capabilities.skills import MatcherResult
    try:
        MatcherResult(skill_id="x", confidence=0.5, rationale="r", matcher="bogus")
        return None
    except ValueError as e:
        return e


@when("I build a MatcherResult from the legacy shape with skill \"tdd\" and mode \"pattern\"",
      target_fixture="matcher_result")
def _legacy_pattern():
    from agency.capabilities.skills import MatcherResult
    return MatcherResult.from_legacy({"skill": "tdd", "mode": "pattern",
                                     "confidence": 0.7,
                                     "matched_by": "pattern:tdd matched"})


@when("I build a MatcherResult from legacy with mode \"llm_select\"",
      target_fixture="matcher_result")
def _legacy_llm():
    from agency.capabilities.skills import MatcherResult
    return MatcherResult.from_legacy({"skill": "x", "mode": "llm_select",
                                     "confidence": 0.9, "matched_by": "llm:x"})


@when("I build a MatcherResult from legacy with confidence 2.5",
      target_fixture="matcher_result")
def _legacy_clamp():
    from agency.capabilities.skills import MatcherResult
    return MatcherResult.from_legacy({"skill": "x", "mode": "pattern",
                                     "confidence": 2.5, "matched_by": "?"})


# ── Then steps — MatcherResult ────────────────────────────────────────────────

@then("skill_id is \"tdd\" and confidence is within [0, 1]")
def _valid_mr(matcher_result):
    assert matcher_result.skill_id == "tdd"
    assert 0.0 <= matcher_result.confidence <= 1.0


@then("a ValueError is raised")
def _value_error(mr_error):
    assert isinstance(mr_error, ValueError), f"expected ValueError, got {mr_error!r}"


@then("skill_id is \"tdd\" and matcher is \"pattern\"")
def _legacy_ok(matcher_result):
    assert matcher_result.skill_id == "tdd"
    assert matcher_result.matcher == "pattern"


@then("the matcher is \"llm\"")
def _matcher_llm(matcher_result):
    assert matcher_result.matcher == "llm"


@then("the confidence is clamped to 1.0")
def _clamped(matcher_result):
    assert matcher_result.confidence == 1.0
