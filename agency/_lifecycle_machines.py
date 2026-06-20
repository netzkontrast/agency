"""Spec 345 — machine registry for the generic state-machine substrate.

Reads machines.json at first access, resolves `derives` chains, validates
the terminal floor per-machine. Does NOT import from ontology.py so that
ontology.py can safely import the live _all_states set (no circular import).
"""
from __future__ import annotations

import json
from pathlib import Path

# AGENCY-DRIFT: lifecycle-machines — adding a machine = entry in machines.json
# or a register_machine() call. Sites that enumerate machine names are tagged here.
_MACHINES_PATH = Path(__file__).parent / "_lifecycle_data" / "machines.json"

_registry: dict[str, dict] | None = None

# Live mutable set of all states across all registered machines.
# ontology.py imports this reference; register_machine() updates it in
# place so subsequently-constructed Ontology instances widen automatically.
_all_states: set[str] = set()


def _ensure_loaded() -> dict[str, dict]:
    global _registry
    if _registry is None:
        _registry = json.loads(_MACHINES_PATH.read_text())
        for defn in _registry.values():
            _all_states.update(defn.get("states", []))
    return _registry


def resolve_machine(name: str) -> dict:
    """Resolve a named machine to its effective definition.

    Returns {initial: str, states: set[str], transitions: dict[str,list[str]],
    terminal: set[str]}. Applies the `derives` chain — a derived machine's
    states/transitions are the monotone union (base <= effective) + replace deltas.
    Terminal floor is validated at resolve time.
    Raises ValueError for unknown machines or floor violations.
    """
    reg = _ensure_loaded()
    if name not in reg:
        raise ValueError(
            f"unknown machine {name!r}; registered: {sorted(reg)}")
    defn = reg[name]
    if "derives" not in defn:
        return _normalise(name, defn)
    base = resolve_machine(defn["derives"])
    return _apply_delta(name, base, defn)


def _normalise(name: str, defn: dict) -> dict:
    states: set[str] = set(defn.get("states", []))
    raw = defn.get("transitions", {})
    transitions: dict[str, list[str]] = {s: sorted(t) for s, t in raw.items()}
    terminal: set[str] = set(defn.get(
        "terminal", [s for s, t in transitions.items() if not t]))
    initial: str = defn.get("initial", "")
    _validate_floor(name, initial, states, transitions, terminal)
    return {"initial": initial, "states": states,
            "transitions": transitions, "terminal": terminal}


def _apply_delta(name: str, base: dict, delta: dict) -> dict:
    states: set[str] = set(base["states"])
    transitions: dict[str, list[str]] = {s: list(t)
                                          for s, t in base["transitions"].items()}
    for s in delta.get("add_states", []):
        states.add(s)
    for src, changes in delta.get("replace", {}).items():
        states.add(src)
        if isinstance(changes, list):
            transitions[src] = sorted(changes)
        else:
            existing = set(transitions.get(src, []))
            existing -= set(changes.get("remove", []))
            existing |= set(changes.get("add", []))
            transitions[src] = sorted(existing)
    terminal: set[str] = {s for s, t in transitions.items() if not t}
    initial: str = base["initial"]
    _validate_floor(name, initial, states, transitions, terminal)
    return {"initial": initial, "states": states,
            "transitions": transitions, "terminal": terminal}


def _validate_floor(name: str, initial: str, states: set[str],
                    transitions: dict, terminal: set[str]) -> None:
    if initial not in states:
        raise ValueError(
            f"machine {name!r}: initial {initial!r} not in "
            f"states {sorted(states)}")
    for t in terminal:
        if transitions.get(t):
            raise ValueError(
                f"machine {name!r}: terminal state {t!r} has outgoing "
                f"transitions (floor violated)")


def all_machine_states() -> set[str]:
    """Union of all registered machines' states."""
    _ensure_loaded()
    return set(_all_states)


def register_machine(name: str, defn: dict) -> None:
    """Register a machine definition at runtime.

    Called by domain capabilities and by tests. Validates the floor via
    resolve_machine, then adds to the registry and widens _all_states so
    subsequently-constructed Ontology instances accept these states.
    """
    reg = _ensure_loaded()
    reg[name] = defn
    _all_states.update(defn.get("states", []))
