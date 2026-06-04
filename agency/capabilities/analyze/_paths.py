"""Spec 048 — analyze.paths axis.

Surfaces intent-shape patterns that suggest a missing specialized
capability would shorten the intent→artefact path. Three rules:

  IP001 (info) — long sub-intent chain: a root intent's tree reaches
         ≥ 5 levels deep. The agent fragmented the work; consider a
         composite verb that does the chain in one call.
  IP002 (warn) — long verb sequence per intent: ≥ 12 Invocations
         serving one intent. Strongest candidate for a specialized
         capability.
  IP003 (info) — repeated verb pattern: the same verb fires ≥ 4 times
         under one intent. Candidate for a batched/fan-out replacement.

NO LLM judgement. NO refactoring. This module surfaces SHAPES; humans
decide what to ship.
"""
from __future__ import annotations

from ._findings import Finding, make_finding


SEVERITY: dict[str, str] = {
    "IP001": "info",
    "IP002": "warn",
    "IP003": "info",
}

_LONG_CHAIN_DEPTH = 5
_LONG_VERB_SEQUENCE = 12
_REPEATED_VERB_THRESHOLD = 4


def _walk_descendants(memory, root_id: str, max_depth: int = 32) -> list[str]:
    """BFS over PARENT_INTENT edges (downward), returning every descendant id
    (excluding the root). Capped at max_depth levels for safety."""
    out: list[str] = []
    frontier = [root_id]
    depth = 0
    while frontier and depth < max_depth:
        rows = memory.g.query(
            "MATCH (c:Intent)-[:PARENT_INTENT]->(p:Intent) "
            "WHERE p.id IN $ids RETURN c",
            {"ids": frontier})
        next_frontier = [r["c"]["properties"]["id"] for r in rows]
        if not next_frontier:
            break
        out.extend(next_frontier)
        frontier = next_frontier
        depth += 1
    return out


def _chain_depth(memory, root_id: str) -> int:
    """Maximum levels under root_id in the PARENT_INTENT tree."""
    descendants = _walk_descendants(memory, root_id)
    if not descendants:
        return 0
    # Count levels: each BFS frontier step is one level.
    levels = 0
    frontier = [root_id]
    visited = {root_id}
    while frontier:
        rows = memory.g.query(
            "MATCH (c:Intent)-[:PARENT_INTENT]->(p:Intent) "
            "WHERE p.id IN $ids RETURN c",
            {"ids": frontier})
        next_frontier = [r["c"]["properties"]["id"]
                          for r in rows if r["c"]["properties"]["id"] not in visited]
        if not next_frontier:
            break
        visited.update(next_frontier)
        frontier = next_frontier
        levels += 1
    return levels


def _invocations_for(memory, intent_id: str) -> list[dict]:
    """All Invocation nodes whose SERVES edge points to this intent."""
    rows = memory.g.query(
        "MATCH (inv:Invocation)-[:SERVES]->(i:Intent) "
        "WHERE i.id = $iid RETURN inv",
        {"iid": intent_id})
    return [r["inv"]["properties"] for r in rows]


def _user_root_intents(memory) -> list[dict]:
    """User-owned intents with no PARENT_INTENT edge OUT — the session roots."""
    rows = memory.g.query(
        "MATCH (i:Intent) WHERE i.owner = $o RETURN i",
        {"o": "user"})
    out: list[dict] = []
    for r in rows:
        props = r["i"]["properties"]
        # Filter to roots: those whose parent_intent_id is empty or absent.
        if not props.get("parent_intent_id"):
            out.append(props)
    return out


def scan(memory, root_intent_id: str = "",
         max_paths: int = 10) -> list[Finding]:
    """Spec 048 analyze.paths scan.

    With ``root_intent_id`` set, scans only that root's tree. Empty
    means "every user-owned root intent in the graph, capped at
    ``max_paths``".
    """
    findings: list[Finding] = []
    if root_intent_id:
        roots = [memory.recall(root_intent_id)]
        roots = [r for r in roots if r]
    else:
        roots = _user_root_intents(memory)[:max_paths]
    for root in roots:
        root_id = root["id"]
        # IP001 — chain depth.
        depth = _chain_depth(memory, root_id)
        if depth >= _LONG_CHAIN_DEPTH:
            findings.append(make_finding(
                rule="IP001", severity=SEVERITY["IP001"],
                file=root_id, line=1,
                message=f"intent chain {depth} levels deep — composite-verb candidate",
                evidence=f"{root_id} → ({depth} levels)",
            ))
        # IP002 — invocation count per intent (root + descendants).
        all_ids = [root_id, *_walk_descendants(memory, root_id)]
        for iid in all_ids:
            invs = _invocations_for(memory, iid)
            if len(invs) >= _LONG_VERB_SEQUENCE:
                verbs = " → ".join(
                    f"{i.get('capability', '?')}.{i.get('verb', '?')}"
                    for i in invs[:6])
                findings.append(make_finding(
                    rule="IP002", severity=SEVERITY["IP002"],
                    file=iid, line=1,
                    message=f"{len(invs)} invocations serving {iid} — "
                            "specialized-capability candidate",
                    evidence=verbs + (" → ..." if len(invs) > 6 else ""),
                ))
            # IP003 — repeated verb (>= 4 hits of same verb).
            counts: dict[str, int] = {}
            for i in invs:
                key = f"{i.get('capability', '?')}.{i.get('verb', '?')}"
                counts[key] = counts.get(key, 0) + 1
            for verb_key, n in counts.items():
                if n >= _REPEATED_VERB_THRESHOLD:
                    findings.append(make_finding(
                        rule="IP003", severity=SEVERITY["IP003"],
                        file=iid, line=1,
                        message=f"verb {verb_key!r} invoked {n}× under {iid} "
                                "— batched-replacement candidate",
                        evidence=f"{verb_key} ×{n}",
                    ))
    return findings
