# agency-scaffold: v1
"""discover ontology — Spec 307 consolidated OntologyExtension (locked surface).

Registers the WHOLE intent-pillar program's node/edge/enum/schema surface ONCE
(Spec 307 §"The ontology"), so the 17 child specs (309-325) populate node
*instances* without ever re-touching the schema. ``Citation`` is deliberately
NOT redeclared — the ``GROUNDS`` edge reuses the ``research`` capability's
existing ``Citation`` node (Spec 044), per CLAUDE.md's no-duplicate rule.

The ``guided-discovery`` walkable skill slot is populated by Spec 323; until
then the engine's derived ``discover-usage`` walk (Spec 081) stands.
"""
from __future__ import annotations

from agency.ontology import OntologyExtension


# ─────────────────────────── enums (Spec 307) ───────────────────────────
AMBIGUITY_KIND = {
    "underspecified", "conflicting", "vague-scope",
    "missing-acceptance", "unstated-assumption",
}
FEASIBILITY_VERDICT = {"go", "no-go", "refine"}
SCOPE_SIDE = {"in", "out"}
TURN_KIND = {
    "describe", "configure", "constrain", "ground", "clarify", "confirm",
}


# ─────────────────────────── nodes (Spec 307) ───────────────────────────
# label -> required fields. The 7 program node types; children record instances.
_NODES: dict[str, list[str]] = {
    "DiscoverySession": ["seed", "status", "clarity_score"],
    "ElicitationTurn": ["beat", "kind", "question", "answer"],
    "ClarificationQuestion": ["text", "options", "ambiguity_kind"],
    "ScopeBoundary": ["item", "side"],
    "AcceptanceCriterion": ["text", "gherkin", "measurable"],
    "FeasibilitySignal": ["verdict", "rationale"],
    "IntentRefinement": ["trigger", "before", "after"],
}


# ─────────────────────────── edges (Spec 307) ───────────────────────────
# GROUNDS reuses research's Citation node (no redeclare); REFINES pairs with the
# substrate SUPERSEDED_BY edge in agency/memory.py.
_EDGES: set[str] = {
    "ELICITS",      # DiscoverySession  → ElicitationTurn
    "DISCOVERED",   # DiscoverySession  → Intent
    "CLARIFIES",    # ClarificationQuestion → Intent
    "GROUNDS",      # Citation          → Intent (research's Citation)
    "BOUNDS",       # ScopeBoundary     → Intent
    "VALIDATES",    # AcceptanceCriterion → Intent
    "REFINES",      # IntentRefinement  → Intent
}


# ─────────────────── schemas (Spec 292 Document/artefact) ───────────────────
# name -> required fields. Field lists are sensible defaults (CLAUDE.md #8 —
# definable, not frozen); children may widen. The schema NAME set is the locked
# Spec 307 surface.
_SCHEMAS: dict[str, list[str]] = {
    "discovery-session": ["seed", "status"],
    "elicitation-turn": ["beat", "kind"],
    "scope-boundary": ["item", "side"],
    "acceptance-criteria": ["text", "gherkin"],
    "feasibility-probe": ["verdict", "rationale"],
    "intent-brief": ["purpose", "deliverable", "acceptance"],
}


discover_ontology = OntologyExtension(
    nodes=_NODES,
    edges=_EDGES,
    enums={
        ("ClarificationQuestion", "ambiguity_kind"): AMBIGUITY_KIND,
        ("ElicitationTurn", "kind"): TURN_KIND,
        ("ScopeBoundary", "side"): SCOPE_SIDE,
        ("FeasibilitySignal", "verdict"): FEASIBILITY_VERDICT,
    },
    schemas=_SCHEMAS,
)
