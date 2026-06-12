"""Spec 195 Slice 3 — monotone invariant verification for replay chains.

Spec 195 Slice 2 ships `dogfood.replay_events(for_intent_id)` which
returns events ordered with each event's `prior_event_id` pointing at
the previous event's id. Slice 3 ships the typed verifier that proves
the invariant holds on a given replay output, plus clock-skew detection.

Pure functions; no engine dependency; safe to call from any consumer
(tests, doctor, audit). Returns typed `InvariantReport` so callers
branch on the typed code rather than parsing free text.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class InvariantReport:
    """Typed verifier result.

    `monotone_ok` = True iff every non-first event's `prior_event_id`
    equals the previous event's `event_id` (the chain is a singly-linked
    list end-to-end).

    `breaks` enumerates the (index, prior_observed, prior_expected)
    triples where the chain is broken. Each break is one entry; a long
    contiguous mismatch produces consecutive entries.

    `clock_skew_ok` = True iff every event's `created_at` (when present)
    is greater-than-or-equal to the previous event's. Missing
    `created_at` is treated as 'no claim' — counted as OK.
    """

    monotone_ok:    bool = True
    clock_skew_ok:  bool = True
    breaks:         list[tuple[int, str, str]] = field(default_factory=list)
    clock_skews:   list[tuple[int, str, str]] = field(default_factory=list)
    events_checked: int = 0


def verify_monotone(events: Sequence[dict]) -> InvariantReport:
    """Walk a `dogfood.replay_events` output; return the typed
    InvariantReport. An empty sequence yields `monotone_ok=True,
    events_checked=0` — trivially valid.

    For each event at index i >= 1:
      - expected_prior = events[i - 1].get("event_id", "")
      - observed_prior = events[i].get("prior_event_id", "")
      - if they differ → record break (i, observed_prior, expected_prior)

    For each event at index i >= 1:
      - prev_created = events[i - 1].get("created_at", "")
      - curr_created = events[i].get("created_at", "")
      - if both non-empty AND curr_created < prev_created → record skew
    """
    rep = InvariantReport()
    rep.events_checked = len(events)
    for i in range(1, len(events)):
        ev = events[i] or {}
        prev = events[i - 1] or {}
        expected_prior = str(prev.get("event_id", ""))
        observed_prior = str(ev.get("prior_event_id", ""))
        if observed_prior != expected_prior:
            rep.monotone_ok = False
            rep.breaks.append((i, observed_prior, expected_prior))
        prev_created = str(prev.get("created_at", ""))
        curr_created = str(ev.get("created_at", ""))
        if prev_created and curr_created and curr_created < prev_created:
            rep.clock_skew_ok = False
            rep.clock_skews.append((i, curr_created, prev_created))
    return rep
