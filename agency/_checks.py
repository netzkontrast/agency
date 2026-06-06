"""Spec 011 — structural Lifecycle checks (the auditable residue of a run).

A Lifecycle `check` is the post-hoc read over whatever a delegation/subagent
produced — same observe family as `COMPLETED ≠ done`/`verify` (CORE.md:31,33-35),
NOT a new capability's act. The one non-redundant invariant is **no orphaned
`working` children**: the depth bound is already enforced by `ctx.spawn`
(capability.py MAX_DEPTH) and quota admission is enforced at `fan_out` write
time, so both are dropped. The verdict is recorded through the existing
`gate.check` verb — no `Invariant` node label.
"""
from __future__ import annotations

from typing import Any


def orphaned_working_children(children: list[dict]) -> list[str]:
    """Pure: given child Lifecycle dicts (``{id, state}``), return the ids still
    in ``working`` (dispatched ≠ done — `delegate.fan_out` opens children
    `working`; only `subagent`/`join` move a verified child to `completed`)."""
    return [c.get("id") for c in children if c.get("state") == "working"]


def check_no_orphans(ctx: Any, delegation_id: str, lifecycle_id: str) -> dict:
    """Assert a delegation left no orphaned `working` children; record via gate.

    Inputs: ctx (CapabilityContext), delegation_id (the Delegation node from
            `delegate.fan_out`), lifecycle_id (a child Lifecycle of that
            delegation — it MUST serve the current intent, else `gate.check`
            rejects it).
    Returns: ``{ok, orphans: [id…], children: int, gate}``. ``ok`` is True iff no
             child remains `working`. The verdict is recorded as a `Gate`
             (`name="no_orphans"`) via `gate.check`; a failure pauses
             `lifecycle_id` at input-required for re-entry.
    chain_next: on ``ok=False`` walk `orphans` and resolve each before re-join.
    """
    rows = ctx.memory.g.query(
        "MATCH (d:Delegation)-[:DELEGATES_TO]->(lc:Lifecycle) WHERE d.id = $d RETURN lc",
        {"d": delegation_id})
    children = [{"id": r["lc"].get("id"),
                 "state": r["lc"]["properties"].get("state")} for r in rows]
    orphans = orphaned_working_children(children)
    ok = not orphans
    gate = ctx.call("gate", "check", lifecycle_id=lifecycle_id, name="no_orphans",
                    passed=ok, evidence=f"{len(orphans)} orphaned working child lifecycle(s)")
    return {"ok": ok, "orphans": orphans, "children": len(children), "gate": gate}
