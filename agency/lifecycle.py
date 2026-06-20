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

from . import _events
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
#: Stored at ONE deterministic node id so `move` reads the override with an
#: O(1) `recall` instead of scanning every `Artefact` (Jules review, Spec 340).
TRANSITION_TABLE_NODE_ID = "artefact:lifecycle-transition-table"

#: Spec 349b — the lifecycle transition event name on the pillar event bus.
LIFECYCLE_TRANSITION_EVENT = "lifecycle:transition"


def _monitor_transition(monitor, from_state: str, to_state: str,
                        intent_id: str) -> None:
    """Fan one lifecycle transition onto the Spec 021 monitor channel (the single
    source both the bus subscriber and the engine-less fallback call — rule 2)."""
    if monitor is None:
        return
    from ._monitor import MonitorEvent
    monitor.emit(MonitorEvent(
        source="lifecycle", kind="transition",
        message=f"{from_state or '∅'}→{to_state}", intent_id=intent_id))


def _emit_monitor_on_transition(engine, event: dict) -> str:
    """Spec 349b bus subscriber — the lifecycle's transition telemetry now flows
    through the pillar event bus (`agency/_events.py`) instead of a hardcoded
    `self.monitor.emit` (Jules review: decouple the monitor from `move`). Other
    capabilities subscribe to `lifecycle:transition` the same way."""
    _monitor_transition(getattr(engine, "monitor", None),
                        event.get("from_state", ""), event.get("to_state", ""),
                        event.get("intent_id", ""))
    return ""


# Register at import (idempotent by (event, name) — a reload never double-fires).
_events.subscribe(LIFECYCLE_TRANSITION_EVENT, _emit_monitor_on_transition,
                  name="lifecycle.monitor")


class Lifecycle:
    def __init__(self, memory: Memory, monitor: Any = None, engine: Any = None):
        self.m = memory
        # Spec 344 — the Spec 021 monitor channel (engine.monitor). Optional so a
        # bare ``Lifecycle(memory)`` (no engine) still records durable graph
        # transitions; only the high-volume churn telemetry needs the channel.
        self.monitor = monitor
        # Spec 349b — the owning engine, so a transition can fan onto the pillar
        # event bus (`_events.run(engine, ...)`). ``None`` in bare unit tests →
        # the monitor fallback keeps Spec 344 telemetry working.
        self.engine = engine
        # Spec 340 — the base A2A transition table (data; loaded + validated once).
        self._base_table = load_base_table()

    def _effective_table(self) -> dict:
        """The transition table `move` enforces — graph-first (an
        `Artefact{kind:"transition-table"}` override at ``TRANSITION_TABLE_NODE_ID``,
        monotone + floor-checked via ``extend_table``), seed fallback (Spec 340;
        the `shell.define` pattern). Read per-move via an O(1) ``recall`` on the
        fixed node id (NOT a full `Artefact` scan — Jules review) so a
        freshly-defined override takes effect without a restart."""
        art = self.m.recall(TRANSITION_TABLE_NODE_ID)
        raw = art.get("table") if art else None
        if not raw:
            return self._base_table
        try:                                     # an UNPARSEABLE override → seed
            extra = raw if isinstance(raw, dict) else json.loads(raw)
        except (ValueError, TypeError):
            return self._base_table
        # A floor/monotonicity violation (`IllegalTransition`, a ValueError
        # subclass) MUST propagate — never silently swallowed back to the seed.
        return extend_table(self._base_table, extra)

    def open(self, intent_id: str, *, kind: str = "task",
             agent: str = "", parameterization: str = "",
             machine: str = "a2a") -> str:
        # Spec 339 — mint in `submitted` (was `working`): submitted = admitted/
        # queued, working = actually running. The distinction makes `whats_next`
        # accurate and matches CORE.md §3's A2A start state.
        #
        # `kind` (task | session | gate | dispatch …) and `parameterization`
        # (the 342 seam — e.g. "remote-async" for a delegated child, "session"
        # for a SessionLifecycle) are OPTIONAL props recorded only when set, so
        # legacy/default lifecycles stay byte-identical.
        # Spec 345 — per-machine initial state; default machine "a2a" → SUBMITTED (byte-identical)
        from ._lifecycle_machines import resolve_machine as _resolve_machine
        _m = _resolve_machine(machine)
        props: dict = {"state": _m["initial"], "phase": 0}
        if machine != "a2a":
            props["machine"] = machine
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
        node = self.m.recall(lc_id) or {}
        current = node.get("state")
        machine_name = node.get("machine", "a2a")

        # Spec 345: per-machine state + transition validation.
        # A2A branch reuses _effective_table() for graph-override support (Spec 340);
        # other machines use resolve_machine() from the seed registry.
        if machine_name == "a2a":
            valid_states = LIFECYCLE_STATES
            table = self._effective_table()
        else:
            from ._lifecycle_machines import resolve_machine as _resolve_machine
            _m = _resolve_machine(machine_name)
            valid_states = _m["states"]
            table = _m["transitions"]

        if to_state not in valid_states:
            raise ValueError(
                f"unknown state {to_state!r} for machine {machine_name!r}; "
                f"valid: {sorted(valid_states)}")
        if current == to_state:
            raise ValueError(
                f"no-op transition: lifecycle {lc_id!r} is already {to_state!r}")
        # A well-formed lifecycle (any state set by `open`) must follow a legal
        # edge; a lifecycle with no state yet (pre-`open` legacy) is exempt.
        if current:
            assert_transition(current, to_state, table)
        self.m.update(lc_id, {"state": to_state})
        self._emit_transition(lc_id, current or "", to_state, evidence)
        return to_state

    def _emit_transition(self, lc_id: str, from_state: str, to_state: str,
                         evidence: str) -> None:
        """Broadcast a transition (Spec 344 + 349b). Terminal/blocked transitions
        become durable graph ``Event``s (the lifecycle's intrinsic provenance —
        recorded inline, memory-only); EVERY transition is then fanned onto the
        **pillar event bus** (`lifecycle:transition`, Spec 349b) — the monitor
        telemetry is now a bus SUBSCRIBER, not a hardcoded call, so other
        capabilities can react to transitions the same way. Split by class so
        high-volume churn never bloats the graph (panel B4 — Spec 336 win)."""
        intent_id = ""
        serving = self.m.neighbors(lc_id, "SERVES", direction="out")
        if serving:
            intent_id = serving[0].get("id", "")
        # Spec 347 — frugal stamp: active discipline level at transition time.
        # Single source: _frugal.frugal_level() (Spec 332); never redefined here.
        try:
            from ._frugal import frugal_level as _frugal_level
            fl = _frugal_level()
        except Exception:
            fl = ""
        if is_durable_transition(to_state):
            # Reuse Spec 076: a new *kind* of Event, exactly as Spec 156 records
            # `loop_detected`. `from_state`/`to_state` (not `from`/`to` — both are
            # graphqlite reserved words). `session` is required → the origin tag.
            eid = self.m.record("Event", {
                "name": TRANSITION_EVENT_NAME, "session": "lifecycle",
                "lifecycle": lc_id, "from_state": from_state,
                "to_state": to_state, "evidence": evidence, "frugal": fl})
            if intent_id:
                self.m.link(eid, intent_id, "OBSERVED_DURING")
            self.m.link(eid, lc_id, "OBSERVED_DURING")
        ev = {"lifecycle_id": lc_id, "from_state": from_state,
              "to_state": to_state, "intent_id": intent_id, "evidence": evidence,
              "durable": is_durable_transition(to_state), "frugal": fl}
        if self.engine is not None:
            _events.run(self.engine, LIFECYCLE_TRANSITION_EVENT, ev)
        else:                                    # bare Lifecycle(memory, monitor) — no bus
            _monitor_transition(self.monitor, from_state, to_state, intent_id)

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
