"""Spec 164 Slice 1 — typed VerifyResult shape."""
from __future__ import annotations

import pytest

from agency._wet_verify import VerifyResult


def test_construct_scaffold_result():
    r = VerifyResult.scaffold(
        phase_id="phase:tdd:1", accepted=True,
        rationale="failing test exists", evidence_refs=("reflection:abc",))
    assert r.matcher == "scaffold"
    assert r.accepted is True
    assert r.evidence_refs == ("reflection:abc",)


def test_construct_wet_result():
    r = VerifyResult.wet(
        phase_id="phase:write-spec:2", accepted=False,
        rationale="spec missing acceptance criteria",
        evidence_refs=("artefact:spec-184",))
    assert r.matcher == "wet"
    assert r.accepted is False


def test_rationale_capped_at_200_chars():
    with pytest.raises(ValueError):
        VerifyResult(phase_id="phase:x", accepted=True,
                      rationale="a" * 201, matcher="scaffold")


def test_invalid_matcher_kind_rejected():
    with pytest.raises(ValueError):
        VerifyResult(phase_id="phase:x", accepted=True,
                      rationale="r", matcher="bogus")


def test_evidence_refs_must_be_node_ids():
    """A node id has the form `<label>:<id>`; bare strings without `:`
    are silent-rotting hints that we don't accept."""
    with pytest.raises(ValueError):
        VerifyResult(phase_id="phase:x", accepted=True,
                      rationale="r",
                      evidence_refs=("not-an-id",),
                      matcher="scaffold")


def test_to_dict_round_trips():
    r = VerifyResult.scaffold(
        phase_id="phase:tdd:1", accepted=True, rationale="ok",
        evidence_refs=("reflection:abc",))
    d = r.to_dict()
    assert d == {"phase_id": "phase:tdd:1", "accepted": True,
                 "rationale": "ok", "evidence_refs": ["reflection:abc"],
                 "matcher": "scaffold"}


def test_scaffold_factory_truncates_rationale():
    """scaffold() truncates rationale at 200 (no ValueError raised)."""
    r = VerifyResult.scaffold(
        phase_id="phase:x", accepted=False, rationale="a" * 500)
    assert len(r.rationale) == 200


def test_wet_factory_truncates_rationale():
    """wet() truncates rationale at 200."""
    r = VerifyResult.wet(
        phase_id="phase:x", accepted=True, rationale="b" * 500)
    assert len(r.rationale) == 200


def test_spec164_invariant_default_matcher_is_scaffold():
    """The invariant 'when no LLM driver, matcher == scaffold' is built
    into the dataclass default: any caller that doesn't explicitly
    request `wet` gets `scaffold` — including subclasses and tooling."""
    r = VerifyResult(phase_id="phase:x", accepted=True, rationale="r")
    assert r.matcher == "scaffold"


def test_frozen_dataclass_blocks_mutation():
    """Frozen dataclasses prevent reassignment — the typed shape can't
    be mutated post-construction (rule 8 + Spec 002 boundary discipline)."""
    r = VerifyResult.scaffold(
        phase_id="phase:x", accepted=True, rationale="r")
    with pytest.raises(Exception):              # FrozenInstanceError
        r.accepted = False                                       # type: ignore[misc]
