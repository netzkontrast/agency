"""Spec 162 Slice 1 — typed MatcherResult shape.

`MatcherResult{skill_id, confidence, rationale, matcher}` is the
return shape every Spec 026 matcher kind (pattern / verb_code /
llm_select) coerces to. Slice 2 will swap the matcher to `"llm"` via
the Spec 147 AnthropicDriver; today's tests pin the data shape only.
"""
from __future__ import annotations

import pytest

from agency.capabilities.skills import MatcherResult


def test_typed_shape_accepts_valid_construction():
    r = MatcherResult(
        skill_id="tdd", confidence=0.9,
        rationale="pattern:tdd matched on 'failing test first'",
        matcher="pattern")
    assert r.skill_id == "tdd"
    assert r.matcher == "pattern"
    assert 0.0 <= r.confidence <= 1.0
    assert len(r.rationale) <= 200


def test_rejects_confidence_out_of_range():
    with pytest.raises(ValueError):
        MatcherResult(skill_id="x", confidence=1.5,
                       rationale="oops", matcher="pattern")
    with pytest.raises(ValueError):
        MatcherResult(skill_id="x", confidence=-0.1,
                       rationale="oops", matcher="pattern")


def test_rejects_rationale_over_200_chars():
    with pytest.raises(ValueError):
        MatcherResult(skill_id="x", confidence=0.5,
                       rationale="a" * 201, matcher="pattern")


def test_rejects_unknown_matcher_kind():
    with pytest.raises(ValueError):
        MatcherResult(skill_id="x", confidence=0.5,
                       rationale="r", matcher="bogus")


def test_to_dict_round_trips_via_dataclass_asdict():
    r = MatcherResult(skill_id="brainstorm", confidence=0.8,
                       rationale="r", matcher="verb_code")
    d = r.to_dict()
    assert d == {"skill_id": "brainstorm", "confidence": 0.8,
                 "rationale": "r", "matcher": "verb_code"}


def test_from_legacy_translates_intent_suggests_output():
    """Adapter for the existing intent.suggests `{skill, mode, confidence,
    cue, matched_by}` return shape."""
    legacy = {"skill": "tdd", "mode": "pattern",
              "confidence": 0.7,
              "matched_by": "pattern:tdd matched on 'failing test'"}
    r = MatcherResult.from_legacy(legacy)
    assert r.skill_id == "tdd"
    assert r.matcher == "pattern"
    assert r.confidence == 0.7


def test_from_legacy_translates_llm_select_to_llm():
    """The legacy mode `llm_select` maps to the typed `llm` matcher."""
    legacy = {"skill": "x", "mode": "llm_select", "confidence": 0.9,
              "matched_by": "llm:x"}
    r = MatcherResult.from_legacy(legacy)
    assert r.matcher == "llm"


def test_from_legacy_translates_unknown_mode_to_none():
    """An unrecognised legacy mode falls through to `none`."""
    legacy = {"skill": "x", "mode": "bogus", "confidence": 0.5,
              "matched_by": "?"}
    r = MatcherResult.from_legacy(legacy)
    assert r.matcher == "none"


def test_from_legacy_clamps_confidence_to_unit_interval():
    """Legacy callers may have passed > 1.0; the adapter clamps."""
    legacy = {"skill": "x", "mode": "pattern", "confidence": 2.5,
              "matched_by": "?"}
    r = MatcherResult.from_legacy(legacy)
    assert r.confidence == 1.0


def test_from_legacy_truncates_rationale_to_200():
    """matched_by longer than 200 chars is truncated by the adapter."""
    legacy = {"skill": "x", "mode": "pattern", "confidence": 0.5,
              "matched_by": "a" * 500}
    r = MatcherResult.from_legacy(legacy)
    assert len(r.rationale) == 200


def test_invariant_when_no_llm_driver_matcher_is_not_llm():
    """Spec 162 invariant: when [anthropic] absent, a real run never
    produces matcher='llm'. Today we exercise it via the adapter; Slice 2
    will exercise it via the wet engine path."""
    # Pretend the legacy mode is pattern (the degradation fallback).
    legacy = {"skill": "x", "mode": "pattern", "confidence": 0.5,
              "matched_by": "?"}
    r = MatcherResult.from_legacy(legacy)
    assert r.matcher != "llm"
