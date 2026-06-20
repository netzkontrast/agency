"""Lifecycle — the task/agent state-machine substrate (the Lifecycle PILLAR).

Peer to ``intent.py`` and ``memory.py``: the engine holds one ``Lifecycle``
(``engine.lifecycle``) and capabilities reach it via ``ctx.lifecycle`` (Spec 339).
It is NOT a capability — it is the pillar substrate. Verb frame:
**open · move · close** (write) + **status** (read). States align with A2A tasks.
An *agent* is a Lifecycle parameterization (a who-session), linked DISPATCHED_TO.

Spec 339 hardening: ``open`` mints ``submitted`` (was ``working``); ``move`` is a
general **state-shaped** transition and the **sole writer** of ``Lifecycle.state``
(it validates the target against the closed enum and refuses a no-op); ``close``
drives to a terminal state through ``move``. The full A2A transition table (340),
transition events (344), and parameterization (342) build on this frame.

Lifecycle state mutates in place (so SERVES/DISPATCHED_TO edges stay stable);
append-only bi-temporality is demonstrated on Intent (see intent.py).
"""
from __future__ import annotations

from typing import Optional

from .memory import Memory
from .ontology import LIFECYCLE_STATES, LifecycleState

# A2A-aligned task states. Spec 286 #8 — `LifecycleState` (ontology.py) is the
# single source; these module-level names are its `.value` (plain strings) so
# graph storage `{"state": WORKING}` stays a plain string — zero storage/wire
# change.
SUBMITTED = LifecycleState.SUBMITTED.value
WORKING = LifecycleState.WORKING.value
INPUT_REQUIRED = LifecycleState.INPUT_REQUIRED.value
AUTH_REQUIRED = LifecycleState.AUTH_REQUIRED.value
COMPLETED = LifecycleState.COMPLETED.value
FAILED = LifecycleState.FAILED.value
CANCELED = LifecycleState.CANCELED.value

# Outcomes `close` may drive to — the terminal/failure states a unit of work
# ends in (the table's `failed` is retry-able via an explicit re-open, but as a
# *close outcome* it is a valid ending).
CLOSE_OUTCOMES = {COMPLETED, FAILED, CANCELED}


class Lifecycle:
    def __init__(self, memory: Memory):
        self.m = memory

    def open(self, intent_id: str, agent: Optional[str] = None) -> str:
        # Spec 339 — mint in `submitted` (was `working`): submitted = admitted/
        # queued, working = actually running. The distinction makes `whats_next`
        # accurate and matches CORE.md §3's A2A start state.
        lc = self.m.record("Lifecycle", {"state": SUBMITTED, "phase": 0})
        self.m.link(lc, intent_id, "SERVES")
        if agent:
            agent_id = f"agent:{agent}"
            if self.m.recall(agent_id) is None:          # reuse the Agent node; don't rewrite its history
                self.m.record("Agent", {"runtime": "cloud-async"}, node_id=agent_id)
            self.m.link(lc, agent_id, "DISPATCHED_TO")
        return lc

    def move(self, lc_id: str, to_state: str, *, evidence: str = "") -> str:
        """The SOLE state-shaped writer of ``Lifecycle.state`` (Spec 339).

        Validates ``to_state`` against the closed A2A enum and refuses a no-op.
        The full transition-table guard (340) and transition events (344) layer
        on top of this one chokepoint.
        """
        # AGENCY-DRIFT: lifecycle-state-writer — the ONE legitimate site that
        # writes Lifecycle.state. A new `update({"state": ...})` / `record(
        # "Lifecycle"/"SessionLifecycle", ...)` elsewhere is drift (Spec 340 guard).
        if to_state not in LIFECYCLE_STATES:
            raise ValueError(
                f"unknown lifecycle state {to_state!r}; "
                f"valid: {sorted(LIFECYCLE_STATES)}")
        current = (self.m.recall(lc_id) or {}).get("state")
        if current == to_state:
            raise ValueError(
                f"no-op transition: lifecycle {lc_id!r} is already {to_state!r}")
        self.m.update(lc_id, {"state": to_state})
        return to_state

    def close(self, lc_id: str, *, outcome: str = COMPLETED, evidence: str = "") -> str:
        """Drive a lifecycle to a terminal outcome through ``move`` (Spec 339).

        ``outcome`` must be a terminal/failure state; the Spec 328 completion
        ``Gate`` recording lands in a later slice.
        """
        if outcome not in CLOSE_OUTCOMES:
            raise ValueError(
                f"close outcome must be terminal ({sorted(CLOSE_OUTCOMES)}); "
                f"got {outcome!r}")
        return self.move(lc_id, outcome, evidence=evidence)

    def status(self, lc_id: str) -> Optional[str]:
        props = self.m.recall(lc_id)
        return props.get("state") if props else None
