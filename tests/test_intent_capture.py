"""Spec 176 Slice 2 — SessionStart intent-capture contract invariants.

The engine-side capture core the SessionStart hook drives: every session SERVES
an Intent, capture never blocks (pure graph write), it is idempotent across
re-entry, declines fall back to auto_ad_hoc, and AGENCY_INTENT reflects the
resolved id. A templated capture writes one Artefact per turn.
"""
from __future__ import annotations

import os

from agency._intent_capture import (capture_degraded, capture_session_intent,
                                     open_intent_id)
from agency._typed_shapes_wave1 import IntentCapture
from agency.engine import Engine
from agency.toolresult import Codes


def _fresh():
    return Engine(":memory:")


def test_capture_degraded_code_exists():
    assert Codes.CAPTURE_DEGRADED == "capture_degraded"


def test_auto_ad_hoc_fallback_mints_a_servable_intent():
    e = _fresh()
    try:
        assert open_intent_id(e.memory) == ""        # nothing open yet
        cap = capture_session_intent(e, source="auto_ad_hoc", captured_at="t0")
        assert isinstance(cap, IntentCapture)
        assert cap.source == "auto_ad_hoc"
        assert cap.intent_id.startswith("intent:")
        # the minted Intent is now the open session intent
        assert open_intent_id(e.memory) == cap.intent_id
    finally:
        e.memory.close()


def test_idempotent_across_re_entry():
    e = _fresh()
    try:
        first = capture_session_intent(e, captured_at="t0")
        # second call in the same session must NO-OP onto the same Intent
        second = capture_session_intent(e, captured_at="t1")
        assert second.intent_id == first.intent_id
        assert second.turns == 0 and second.artefact_ids == ()
        # exactly one Intent was minted (no re-prompt duplicate)
        assert len(e.memory.find("Intent")) == 1
    finally:
        e.memory.close()


def test_agency_intent_env_reflects_the_captured_id():
    e = _fresh()
    prev = os.environ.get("AGENCY_INTENT")
    try:
        cap = capture_session_intent(e, captured_at="t0")
        assert os.environ["AGENCY_INTENT"] == cap.intent_id
    finally:
        if prev is None:
            os.environ.pop("AGENCY_INTENT", None)
        else:
            os.environ["AGENCY_INTENT"] = prev
        e.memory.close()


def test_templated_capture_writes_one_artefact_per_turn():
    e = _fresh()
    try:
        turns = ("purpose: ship 176", "deliverable: capture core",
                 "acceptance: invariants green")
        cap = capture_session_intent(e, source="sessionstart", captured_at="t0",
                                     purpose="ship 176",
                                     deliverable="capture core",
                                     acceptance="invariants green",
                                     turns=turns)
        # the write-per-turn contract: one Artefact per captured turn
        assert cap.turns == len(turns)
        assert len(cap.artefact_ids) == len(turns)
        # each Artefact SERVES the Intent (no orphans)
        served = {a["id"] for a in e.memory.nodes_serving(cap.intent_id, "Artefact")}
        assert set(cap.artefact_ids) <= served
    finally:
        e.memory.close()


def test_real_purpose_supersedes_ad_hoc_source():
    e = _fresh()
    try:
        cap = capture_session_intent(e, source="manual", captured_at="t0",
                                     purpose="real work", deliverable="d",
                                     acceptance="a")
        assert cap.source == "manual"
    finally:
        e.memory.close()


def test_capture_degraded_payload_is_resumable():
    payload = capture_degraded("intent:x", "t0", "sessionstart",
                               ("a:1", "a:2", "a:3"))
    assert payload["code"] == Codes.CAPTURE_DEGRADED
    assert payload["resumable"] is True
    assert payload["turns"] == 3
