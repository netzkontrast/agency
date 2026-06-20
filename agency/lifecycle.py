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

import json
from typing import Any, Optional

from ._lifecycle_events import TRANSITION_EVENT_NAME, is_durable_transition
from ._lifecycle_transitions import (
    assert_transition,
    extend_table,
    load_base_table,
)
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


#: Spec 340 — the graph override marker (the `shell.define` pattern, Spec 075):
#: an `Artefact{kind: TRANSITION_TABLE_KIND, table: <json>}` overrides the seed.
TRANSITION_TABLE_KIND = "transition-table"


class Lifecycle:
    def __init__(self, memory: Memory, monitor: Any = None):
        self.m = memory
        # Spec 344 — the Spec 021 monitor channel (engine.monitor). Optional so a
        # bare ``Lifecycle(memory)`` (no engine) still records durable graph
        # transitions; only the high-volume churn telemetry needs the channel.
        self.monitor = monitor
        # Spec 340 — the base A2A transition table (data; loaded + validated once).
        self._base_table = load_base_table()

    def _effective_table(self) -> dict:
        """The transition table `move` enforces — graph-first (an
        `Artefact{kind:"transition-table"}` override, monotone + floor-checked
        via ``extend_table``), seed fallback (Spec 340; the `shell.define`
        pattern). Read per-move so a freshly-defined override takes effect without
        a restart; moves are low-frequency, so the one query is cheap."""
        for art in self.m.query_nodes("Artefact",
                                      where={"kind": TRANSITION_TABLE_KIND}):
            raw = art.get("table")
            if not raw:
                continue
            try:
                extra = raw if isinstance(raw, dict) else json.loads(raw)
            except (ValueError, TypeError):
                continue
            return extend_table(self._base_table, extra)
        return self._base_table

    def open(self, intent_id: str, *, kind: str = "task",
             agent: str = "", parameterization: str = "") -> str:
        # Spec 339 — mint in `submitted` (was `working`): submitted = admitted/
        # queued, working = actually running. The distinction makes `whats_next`
        # accurate and matches CORE.md §3's A2A start state.
        #
        # `kind` (task | session | gate | dispatch …) and `parameterization`
        # (the 342 seam — e.g. "remote-async" for a delegated child, "session"
        # for a SessionLifecycle) are OPTIONAL props recorded only when set, so
        # legacy/default lifecycles stay byte-identical.
        props = {"state": SUBMITTED, "phase": 0}
        if kind and kind != "task":
            props["kind"] = kind
        if parameterization:
            props["parameterization"] = parameterization
        lc = self.m.record("Lifecycle", props)
        self.m.link(lc, intent_id, "SERVES")
        if agent:
            agent_id = f"agent:{agent}"
            if self.m.recall(agent_id) is None:          # reuse the Agent node; don't rewrite its history
                self.m.record("Agent", {"runtime": "cloud-async"}, node_id=agent_id)
            self.m.link(lc, agent_id, "DISPATCHED_TO")
        return lc

    def move(self, lc_id: str, to_state: str, *, evidence: str = "") -> str:
        """The SOLE state-shaped writer of ``Lifecycle.state`` (Spec 339).

        Validates ``to_state`` against the closed A2A enum, refuses a no-op, and
        enforces the A2A **transition table** (Spec 340) — an illegal edge (e.g.
        ``completed→working``, ``submitted→completed``) raises ``IllegalTransition``.
        Every accepted transition then **emits** (Spec 344): terminal/blocked
        states become durable graph ``Event``s, all transitions fan onto the
        monitor channel — because emission lives here, every former unguarded
        writer routed through ``move`` (Spec 339) emits *for free*.
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
        # Spec 340 — enforce the A2A transition table. A well-formed lifecycle
        # (any state set by `open`) must follow a legal edge; a lifecycle with no
        # state yet (pre-`open` legacy) can't be reasoned about, so it is exempt.
        if current:
            assert_transition(current, to_state, self._effective_table())
        self.m.update(lc_id, {"state": to_state})
        self._emit_transition(lc_id, current or "", to_state, evidence)
        return to_state

    def _emit_transition(self, lc_id: str, from_state: str, to_state: str,
                         evidence: str) -> None:
        """Broadcast a transition (Spec 344). Terminal/blocked transitions become
        durable graph ``Event``s (reusing the Spec 076 node + ``OBSERVED_DURING``
        edge); EVERY transition also fans onto the Spec 021 monitor channel as
        telemetry. Split by class so high-volume churn never bloats the graph
        (panel B4 — preserving the Spec 336 win)."""
        intent_id = ""
        serving = self.m.neighbors(lc_id, "SERVES", direction="out")
        if serving:
            intent_id = serving[0].get("id", "")
        if is_durable_transition(to_state):
            # Reuse Spec 076: a new *kind* of Event, exactly as Spec 156 records
            # `loop_detected`. `from_state`/`to_state` (not `from`/`to` — both are
            # graphqlite reserved words). `session` is required → the origin tag.
            eid = self.m.record("Event", {
                "name": TRANSITION_EVENT_NAME, "session": "lifecycle",
                "lifecycle": lc_id, "from_state": from_state,
                "to_state": to_state, "evidence": evidence})
            if intent_id:
                self.m.link(eid, intent_id, "OBSERVED_DURING")
            self.m.link(eid, lc_id, "OBSERVED_DURING")
        if self.monitor is not None:
            from ._monitor import MonitorEvent
            self.monitor.emit(MonitorEvent(
                source="lifecycle", kind="transition",
                message=f"{from_state or '∅'}→{to_state}",
                intent_id=intent_id))

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
