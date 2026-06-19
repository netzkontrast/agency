"""Spec 021 — the engine Monitor channel.

Claude Code's plugin system supports ``monitors/monitors.json`` — each entry is
a long-running shell command whose stdout lines are delivered to the agent as
notifications. Rather than one monitor process per capability (11 caps -> 11
processes the agent must correlate), the engine owns a SINGLE monitor surface:
capabilities emit ``MonitorEvent``s through it, a ``tail -F`` on one log file
fans them in. Same shape as ``search/get_schema/execute`` exposing ONE wire
surface for N tools (GOALS.md goal #4).

This module is the substrate. Spec 022 (jules-monitor) is the first consumer;
future emitters (e.g. ``delegate.fan_out`` completion) plug in with zero
``monitors.json`` change.

Design choices (from the spec's Open Questions):
- ``kind`` is an OPEN string, not a closed enum — new capabilities extend it
  freely; ``CANONICAL_KINDS`` documents the so-far set for the agent's benefit.
- No engine-side rate limit in v1 — emit-callers choose what's worth surfacing
  (the dispatch-decision principle: don't emit unless it's actually new info).
- Each event is ONE JSON dict on ONE line, capped at ``_MAX_EVENT_BYTES`` so a
  POSIX append stays atomic (no interleaving from concurrent writers).
- The log is a SLOG, not the graph: bounded, ephemeral, rotated. Durable
  provenance lives in Memory; this stream is live notification only.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, replace

# Rotate the live log once it reaches this size; single-file history.
_ROTATE_BYTES = 1_000_000  # 1 MB
# POSIX guarantees atomic appends only for writes <= PIPE_BUF (typically 4096).
# Keeping each event line under this bound avoids interleaved bytes when two
# processes append to the same log (spec Open Question #4).
_MAX_EVENT_BYTES = 4096
_TRUNCATION_MARKER = "...[truncated]"

# Canonical-so-far event kinds. NOT a closed enum — emitters may use other
# strings; this tuple is documentation the agent can lean on when filtering.
CANONICAL_KINDS = (
    "state_transition",
    "fanout_complete",
    "warning",
    "info",
    "recovery",
    "completed",
    "server_start",
    "server_stop",
)


@dataclass(frozen=True)
class MonitorEvent:
    """One notification fanned onto the engine monitor channel.

    Frozen so an emitted event can't be mutated after the fact; serialized as a
    single compact JSON dict (one line) for the ``tail -F`` delivery model.
    """

    source: str           # capability name (e.g. "jules", "delegate", "engine")
    kind: str             # event kind — see CANONICAL_KINDS (open string)
    message: str          # one-line human/agent-readable summary
    intent_id: str = ""   # serving intent, if any
    ts: float = 0.0       # unix ts; auto-filled on emit when 0.0

    def to_json(self) -> str:
        """Serialize to a single compact JSON line (no embedded newline)."""
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def from_json(cls, line: str) -> "MonitorEvent":
        """Parse one JSONL line back into a ``MonitorEvent``."""
        return cls(**json.loads(line))


def resolve_monitor_log_path(
    db_path: str | None = None, explicit: str | None = None
) -> str:
    """Resolve where the monitor log lives, mirroring Spec 020's DB resolver.

    Order: ``explicit`` arg > ``AGENCY_MONITOR_LOG`` env > sibling of the
    session DB (``<db dir>/monitor.log`` — keeps the SLOG next to the graph) >
    ``./.agency/monitor.log`` when that dir exists > ``~/.agency-monitor.log``.

    Inputs: db_path (the resolved session DB path, if any; ``:memory:`` is
            ignored), explicit (an explicit override path).
    Returns: a path string; the directory is created lazily on first emit, so
             calling this never touches the filesystem.
    """
    if explicit:
        return explicit
    env = os.environ.get("AGENCY_MONITOR_LOG")
    if env:
        return env
    if db_path and db_path != ":memory:":
        d = os.path.dirname(os.path.abspath(db_path))
        if d:
            return os.path.join(d, "monitor.log")
    cwd_agency = os.path.join(os.getcwd(), ".agency")
    if os.path.isdir(cwd_agency):
        return os.path.join(cwd_agency, "monitor.log")
    return os.path.expanduser("~/.agency-monitor.log")


class MonitorEmitter:
    """Append-only JSONL writer for the engine monitor channel.

    Lazy: nothing is created until the first ``emit`` (so ``Engine(":memory:")``
    in install/test paths stays side-effect-free). Idempotent rotation: when the
    live log reaches ``rotate_bytes`` it is atomically renamed to ``<log>.1``
    (overwriting any older ``.1``); the next append recreates a fresh live file.
    """

    def __init__(self, path: str, rotate_bytes: int = _ROTATE_BYTES) -> None:
        self.path = path
        self.rotate_bytes = rotate_bytes

    def emit(self, event: MonitorEvent) -> None:
        """Append one event as a single JSON line, rotating first if oversized."""
        if event.ts == 0.0:
            event = replace(event, ts=time.time())
        line = event.to_json()
        if len(line.encode("utf-8")) > _MAX_EVENT_BYTES:
            event = replace(event, message=self._fit_message(event))
            line = event.to_json()
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.maybe_rotate()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def maybe_rotate(self) -> None:
        """Rotate the live log to ``<log>.1`` when it reaches the threshold.

        Safe to call any time (e.g. on engine lifespan enter). ``os.replace`` is
        atomic and overwrites an existing ``.1``; missing file is a no-op.
        """
        try:
            if os.path.getsize(self.path) >= self.rotate_bytes:
                os.replace(self.path, self.path + ".1")
        except FileNotFoundError:
            pass

    def _fit_message(self, event: MonitorEvent) -> str:
        """Truncate ``message`` so the FULL serialized JSON line fits the budget.

        Measures the *serialized* size, not the raw message bytes: escapable
        characters (``"``, ``\\``, control chars) expand under ``json.dumps``
        (e.g. a run of quotes nearly doubles), so clipping raw UTF-8 could still
        overflow ``_MAX_EVENT_BYTES`` after escaping. Binary-search the kept
        character count against the actual serialized line length.
        """
        def fits(n: int) -> bool:
            candidate = event.message[:n] + _TRUNCATION_MARKER
            size = len(replace(event, message=candidate).to_json().encode("utf-8"))
            return size <= _MAX_EVENT_BYTES

        if not fits(0):
            # Degenerate: source/kind/intent_id alone exceed the budget. Drop the
            # message entirely; nothing more we can clip without losing metadata.
            return _TRUNCATION_MARKER
        lo, hi = 0, len(event.message)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if fits(mid):
                lo = mid
            else:
                hi = mid - 1
        return event.message[:lo] + _TRUNCATION_MARKER
