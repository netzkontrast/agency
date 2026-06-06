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
            `delegate.fan_out` — it MUST serve the current intent), lifecycle_id
            (the Lifecycle to gate — it MUST be a child of `delegation_id`).
    Returns: ``{ok, orphans: [node_id…], children: int, gate}``; or
             ``{error, …}`` when the delegation does not serve the current intent
             or the lifecycle is not one of its children (mirrors
             `delegate.join`'s cross-intent guard — the verdict is NOT recorded
             against an unrelated run). ``ok`` is True iff no child remains
             `working`; the verdict is recorded as a `Gate` (`name="no_orphans"`)
             via `gate.check`; a failure pauses `lifecycle_id` at input-required.
    chain_next: on ``ok=False`` walk `orphans` and resolve each before re-join.
    """
    # Guard 1 — the delegation must serve the current intent (or its amended
    # chain), exactly like `delegate.join`. Without this, a cross-intent or
    # typo'd delegation_id would pause/pass the current run on unrelated state.
    chain = list(ctx.memory._intent_chain(ctx.intent_id))
    if not ctx.memory.g.query(
            "MATCH (d:Delegation)-[:SERVES]->(i:Intent) WHERE d.id = $d AND i.id IN $ids RETURN i",
            {"d": delegation_id, "ids": chain}):
        return {"error": "delegation does not serve the current intent (or its amended chain)",
                "delegation": delegation_id}
    # Guard 2 — the gated lifecycle MUST be a child of THIS delegation (the spec
    # requirement). gate.check's intent guard alone would accept a sibling
    # delegation's child or the parent lifecycle.
    if not ctx.memory.g.query(
            "MATCH (d:Delegation)-[:DELEGATES_TO]->(lc:Lifecycle) WHERE d.id = $d AND lc.id = $lc RETURN lc",
            {"d": delegation_id, "lc": lifecycle_id}):
        return {"error": "lifecycle is not a child of the delegation",
                "delegation": delegation_id, "lifecycle_id": lifecycle_id}

    rows = ctx.memory.g.query(
        "MATCH (d:Delegation)-[:DELEGATES_TO]->(lc:Lifecycle) WHERE d.id = $d RETURN lc",
        {"d": delegation_id})
    # The Agency node id lives in properties["id"]; r["lc"]["id"] is GraphQLite's
    # internal row id (unusable for ctx.recall). Read the former so `orphans`
    # are walkable.
    children = [{"id": r["lc"]["properties"].get("id"),
                 "state": r["lc"]["properties"].get("state")} for r in rows]
    orphans = orphaned_working_children(children)
    ok = not orphans
    gate = ctx.call("gate", "check", lifecycle_id=lifecycle_id, name="no_orphans",
                    passed=ok, evidence=f"{len(orphans)} orphaned working child lifecycle(s)")
    return {"ok": ok, "orphans": orphans, "children": len(children), "gate": gate}
