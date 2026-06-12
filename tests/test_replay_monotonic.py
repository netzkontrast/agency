"""Spec 195 Slice 3 — monotone invariant on replay chains.

Slice 2 ships `dogfood.replay_events`; Slice 3 ships the verifier that
proves the chain is intact (monotone) and clock-skew-free. Wired through
the engine surface end-to-end in the tdd skill walk for Spec 195 Slice 3.
"""
from __future__ import annotations

import pytest

from agency._replay_invariants import InvariantReport, verify_monotone


def test_verify_monotone_accepts_complete_chain():
    """A walk where every non-first event.prior_event_id matches the
    previous event.event_id passes the invariant."""
    events = [
        {"event_id": "event:a", "prior_event_id": ""},
        {"event_id": "event:b", "prior_event_id": "event:a"},
        {"event_id": "event:c", "prior_event_id": "event:b"},
    ]
    rep = verify_monotone(events)
    assert rep.monotone_ok is True
    assert rep.breaks == []
    assert rep.events_checked == 3


def test_verify_monotone_flags_broken_link():
    """A mismatch between observed prior_event_id and the previous
    event's event_id is recorded as a break."""
    events = [
        {"event_id": "event:a", "prior_event_id": ""},
        {"event_id": "event:b", "prior_event_id": "event:WRONG"},
    ]
    rep = verify_monotone(events)
    assert rep.monotone_ok is False
    assert rep.breaks == [(1, "event:WRONG", "event:a")]


def test_verify_monotone_empty_sequence_is_trivially_ok():
    """An empty replay is trivially monotone (no claims to break)."""
    rep = verify_monotone([])
    assert rep.monotone_ok is True
    assert rep.events_checked == 0


def test_verify_monotone_single_event_is_trivially_ok():
    """A single-event replay has no chain to verify; trivially ok."""
    rep = verify_monotone([{"event_id": "event:x", "prior_event_id": ""}])
    assert rep.monotone_ok is True
    assert rep.events_checked == 1


def test_verify_monotone_clock_skew_detected():
    """When a later event's `created_at` precedes its predecessor's,
    flag the clock skew. Doesn't break the chain invariant — just
    surfaces a graph-time anomaly the dogfood loop should reflect on."""
    events = [
        {"event_id": "event:a", "prior_event_id": "",
         "created_at": "2026-06-12T09:00:00Z"},
        {"event_id": "event:b", "prior_event_id": "event:a",
         "created_at": "2026-06-12T08:59:59Z"},      # earlier!
    ]
    rep = verify_monotone(events)
    assert rep.monotone_ok is True
    assert rep.clock_skew_ok is False
    assert len(rep.clock_skews) == 1
    assert rep.clock_skews[0][0] == 1


def test_verify_monotone_missing_created_at_ok():
    """When `created_at` is absent on either side, no skew claim is
    made — events without timestamps don't fail the invariant."""
    events = [
        {"event_id": "event:a", "prior_event_id": ""},
        {"event_id": "event:b", "prior_event_id": "event:a"},
    ]
    rep = verify_monotone(events)
    assert rep.clock_skew_ok is True
    assert rep.clock_skews == []


def test_verify_monotone_live_replay_via_engine():
    """End-to-end: drive `dogfood.replay_events` then verify the live
    output through the new invariant module. Proves Slice 3 is
    composable with Slice 2 without the engine touching the verifier."""
    import tempfile
    from agency.engine import Engine
    e = Engine(tempfile.mktemp(suffix=".db"))
    iid = e.intent.capture("slice3", "monotone live invariant", "verify")
    e.intent.confirm(iid)
    import os
    os.environ["AGENCY_INTENT"] = iid
    for cmd in ["git commit -m a", "git push", "pytest tests/"]:
        e.dispatch_hook({
            "hook_event_name": "PreToolUse", "tool_name": "Bash",
            "session_id": "s", "tool_input": {"command": cmd},
        })
    replay, _ = e.registry.invoke(
        e.memory, iid, "dogfood", "replay_events",
        agent_id="agent:test", for_intent_id=iid, limit=100)
    rep = verify_monotone(replay["events"])
    assert rep.monotone_ok is True, (
        f"live replay's monotone chain is broken: {rep.breaks}")
    assert rep.events_checked == 3
    e.memory.close()
