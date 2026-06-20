"""Spec 344 — typed ``LifecycleEvent`` shape + transition-class classifier.

Mirrors ``_loop_events.py`` (Spec 156): a pure, engine-free record so tests /
doctor / audit can build and assert a transition without an engine. Emission
itself lives in the substrate ``Lifecycle.move`` (the SOLE state writer, Spec
339) — this module only *types* the record and decides which sink a transition
uses.

**The B4 split (Spec 344).** Spec 336 (SHIPPED) moved high-volume capture OFF
the graph because ``Event``s were ~95% of ``session.db`` bloat. A graph ``Event``
per ``move`` (per child, per retry) would re-introduce it. So a transition's sink
depends on its class:

- **terminal/blocked** (``→completed·failed·canceled·input-required·auth-required``)
  → a durable graph ``Event`` (low-volume, real provenance: "the state it reached").
- **intermediate churn** (``submitted→working`` …) → the Spec 021 monitor channel
  only (high-volume telemetry, never the graph).
"""
from __future__ import annotations

from dataclasses import dataclass

from .ontology import LifecycleState

# Spec 344 panel B4 — the durable set is terminal ∪ blocked. Derived from the
# LifecycleState enum (Spec 286 #8 — single source), never a hand-listed copy.
TERMINAL_STATES = frozenset({
    LifecycleState.COMPLETED.value,
    LifecycleState.FAILED.value,
    LifecycleState.CANCELED.value,
})
BLOCKED_STATES = frozenset({
    LifecycleState.INPUT_REQUIRED.value,
    LifecycleState.AUTH_REQUIRED.value,
})
DURABLE_STATES = TERMINAL_STATES | BLOCKED_STATES

#: The name every lifecycle-transition Event carries — the ``kind`` discriminator
#: a consumer (``manage.timeline``, the 341 observe suite) filters on, exactly as
#: Spec 156's loop-detector records ``name:"loop_detected"``.
TRANSITION_EVENT_NAME = "lifecycle_transition"


def is_durable_transition(to_state: str) -> bool:
    """True iff a transition INTO ``to_state`` is durable graph provenance
    (terminal or blocked) rather than intermediate churn (Spec 344 B4)."""
    return to_state in DURABLE_STATES


@dataclass(frozen=True)
class LifecycleEvent:
    """Typed lifecycle-transition record (mirrors ``LoopEvent``, Spec 156).

    Pure + engine-free. ``from_state``/``to_state`` (not ``from``/``to`` — both
    are graphqlite-Cypher reserved words) name the transition; ``at`` is the
    recorded-at stamp the consumer orders by.
    """

    event_id: str
    lifecycle_id: str
    from_state: str
    to_state: str
    intent_id: str
    at: str
    evidence: str = ""

    @property
    def durable(self) -> bool:
        """Whether THIS transition belongs on the durable graph (Spec 344 B4)."""
        return is_durable_transition(self.to_state)
