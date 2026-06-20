"""Spec 340 — the enforced A2A transition table (the substrate state machine).

`ontology.py::LifecycleState` constrains the *value* of `state`; this module
constrains the *transitions* between values. Once Spec 339 made `Lifecycle.move`
the SOLE writer, the column has one chokepoint — this puts a guard at it so the
A2A state machine stops being decorative (`completed→working`,
`submitted→completed` and the like are rejected, not silently written).

Pure + engine-free (like `_loop_events.py` / `_lifecycle_events.py`): the table
is **data** (`_lifecycle_data/transitions.json`, CLAUDE.md #8 — no hardcoded
branches), validated against the closed enum at load. The graph-stored override
(the `shell.define` pattern, Spec 075) is applied by the substrate at read time;
this module supplies the base table, the typed error, and the monotone +
terminal-floor extension that keeps an override safe.
"""
from __future__ import annotations

import json
from pathlib import Path

from .ontology import LIFECYCLE_STATES

# AGENCY-DRIFT: lifecycle-transitions — the base A2A table is data, not code.
# Editing the allowed edges means editing this file; the loader validates every
# state against `LIFECYCLE_STATES` so a typo is a startup error, not a silent gap.
_TABLE_PATH = Path(__file__).parent / "_lifecycle_data" / "transitions.json"


class IllegalTransition(ValueError):
    """A `Lifecycle.move` the transition table forbids (Spec 340).

    Carries ``from_state``/``to_state``/``allowed`` so the caller (or the
    AskUser re-entry loop, 343) can react without re-parsing the message.
    """

    def __init__(self, from_state: str, to_state: str, allowed):
        self.from_state = from_state
        self.to_state = to_state
        self.allowed = list(allowed)
        super().__init__(
            f"illegal lifecycle transition {from_state!r}→{to_state!r}; "
            f"allowed from {from_state!r}: {self.allowed}")


def load_base_table() -> dict[str, list[str]]:
    """Load + validate the seed transition table. Every source AND target state
    must be a valid ``LifecycleState`` (a typo in the JSON is a startup error)."""
    table = json.loads(_TABLE_PATH.read_text())
    for state, targets in table.items():
        if state not in LIFECYCLE_STATES:
            raise ValueError(
                f"transitions.json: unknown source state {state!r}; "
                f"valid: {sorted(LIFECYCLE_STATES)}")
        for t in targets:
            if t not in LIFECYCLE_STATES:
                raise ValueError(
                    f"transitions.json: unknown target {t!r} from {state!r}; "
                    f"valid: {sorted(LIFECYCLE_STATES)}")
    return {s: list(t) for s, t in table.items()}


def terminal_states(table: dict[str, list[str]]) -> set[str]:
    """States with an empty allow-list — nothing leaves them (the safety floor)."""
    return {s for s, outs in table.items() if not outs}


def extend_table(base: dict[str, list[str]], extra) -> dict[str, list[str]]:
    """Monotone + terminal-floor extension (Spec 340, panel F-2).

    The effective table is the UNION of ``base`` and ``extra`` — so a base edge
    can never be removed (monotone, ``base ⊆ effective``) — and ``extra`` may add
    new states/edges (the 342 parameterization seam, e.g. inserting ``verify``)
    but may NEVER add an out-edge to a *terminal base state* (``completed`` /
    ``canceled`` stay terminal). A violating override is rejected, not silently
    applied.
    """
    terminal = terminal_states(base)
    effective = {s: set(outs) for s, outs in base.items()}
    for s, outs in (extra or {}).items():
        outs = list(outs)
        if s in terminal and outs:                       # terminal floor — can't reopen a terminal state
            raise IllegalTransition(s, outs[0], [])
        effective.setdefault(s, set()).update(outs)
    return {s: sorted(outs) for s, outs in effective.items()}


def assert_transition(from_state: str, to_state: str,
                      table: dict[str, list[str]]) -> None:
    """Raise :class:`IllegalTransition` unless ``to_state`` is reachable from
    ``from_state`` in ``table``. Terminal states have an empty allow-list, so
    nothing leaves them."""
    allowed = table.get(from_state, [])
    if to_state not in allowed:
        raise IllegalTransition(from_state, to_state, allowed)
