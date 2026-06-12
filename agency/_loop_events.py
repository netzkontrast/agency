"""Spec 156 Slice 1 — typed LoopEvent shape + pure loop detector.

The dogfood loop needs to know when an agent is repeating itself: 3 raw
`git commit` calls in a row, 4 identical Edit invocations, the same
spec being re-walked over and over. Slice 1 ships the typed `LoopEvent`
node shape + a pure detector that walks a stream of events and surfaces
any `(tool, target)` tuple seen ≥ 3 times within a sliding window.

Slice 2 wires the detector into the live engine's `_default_hook_handler`
so detected loops automatically appear in `dogfood.replay_events` output
(they record a `Event{name: "loop_detected"}` node). Slice 1 stays pure
+ engine-free so consumers (tests, doctor, audit) can call it on any
event sequence without an engine dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence


LoopKind = Literal["loop_detected", "loop_resolved"]
_VALID_KINDS = ("loop_detected", "loop_resolved")
_REPETITION_THRESHOLD = 3


@dataclass(frozen=True)
class LoopEvent:
    """Typed loop-detection record.

    `evidence` is a tuple of the event ids that participated in the loop
    (oldest first). At least one event id is required — an empty evidence
    tuple is a doctrine violation (no causal trail to walk back from)."""

    event_id:     str
    kind:         LoopKind
    detected_at:  str
    evidence:     tuple[str, ...]
    intent_id:    str

    def __post_init__(self) -> None:
        if self.kind not in _VALID_KINDS:
            raise ValueError(
                f"kind must be one of {_VALID_KINDS}; got {self.kind!r}")
        if not self.evidence:
            raise ValueError(
                f"evidence must cite at least one event id; got empty tuple")


def detect_loops(events: Sequence[dict], *, window: int = 5) -> list[LoopEvent]:
    """Walk `events` (chain-ordered list of dicts each with `event_id`,
    `tool`, `target`) and surface any `(tool, target)` tuple seen
    ≥ `_REPETITION_THRESHOLD` (3) times within a sliding window of size
    `window`. Events missing `tool` or `target` are skipped — they
    aren't loop candidates.

    Returns a list of `LoopEvent` records. Each loop's `evidence` field
    is the tuple of contributing event ids in chain order (oldest first).
    Multiple loops in the same stream produce multiple records.

    Pure function: no engine / no graph access. Slice 2 wires this into
    the hook handler so the loops are written back as `Event` nodes that
    appear in `dogfood.replay_events`."""
    if not events:
        return []
    out: list[LoopEvent] = []
    # Walk in chain order; for each position i, scan back `window` events
    # and count `(tool, target)` repetitions including i. When the count
    # hits the threshold, emit a LoopEvent citing the latest N events
    # that share the tuple.
    for i in range(len(events)):
        ev = events[i] or {}
        tool   = ev.get("tool")
        target = ev.get("target")
        if not tool or not target:
            continue
        # Collect matches in the window [i - window + 1, i].
        start_idx = max(0, i - window + 1)
        matches: list[str] = []
        for j in range(start_idx, i + 1):
            cand = events[j] or {}
            if cand.get("tool") == tool and cand.get("target") == target:
                matches.append(str(cand.get("event_id", "")))
        if len(matches) >= _REPETITION_THRESHOLD:
            # Only emit on the FIRST event that completes the threshold —
            # avoids one logical loop spawning N records as the agent
            # keeps repeating. We achieve this by checking whether the
            # SAME tuple already triggered a LoopEvent whose evidence is
            # a prefix of the current matches.
            if any(set(le.evidence) <= set(matches)
                   and le.evidence[0] == matches[0]
                   for le in out):
                continue
            out.append(LoopEvent(
                event_id=f"loop:{matches[-1]}",
                kind="loop_detected",
                detected_at=str(ev.get("created_at", "")),
                evidence=tuple(matches),
                intent_id=str(ev.get("intent_id", "")),
            ))
    return out
