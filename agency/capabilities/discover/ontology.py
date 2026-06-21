# agency-scaffold: v1
"""discover ontology — Spec 307 consolidated OntologyExtension (locked surface).

Registers the WHOLE intent-pillar program's node/edge/enum/schema surface ONCE
(Spec 307 §"The ontology"), so the 17 child specs (309-325) populate node
*instances* without ever re-touching the schema. ``Citation`` is deliberately
NOT redeclared — the ``GROUNDS`` edge reuses the ``research`` capability's
existing ``Citation`` node (Spec 044), per CLAUDE.md's no-duplicate rule.

``GUIDED_DISCOVERY_SKILL`` (Spec 322 Slice 3 / 323) is the authored discipline
that overrides the derived ``discover-usage`` default. Its final ``decide``
phase carries ``gate: "computed"`` + ``gate_verb: "clarity_gate"`` so the
clarity gate is a structural walk property, not a reviewer's hope.
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


# ───────────────────── guided-discovery skill (Spec 322 Slice 3 / 323) ──────────
# Authored discipline — overrides the derived ``discover-usage`` walk (Spec 081).
# 7 phases follow the Spec 307 §"The guided-discovery flow" diagram exactly:
# seed → elicit → ground → clarify → frame → examine → scope+acceptance → decide.
# The ``decide`` phase is a computed gate: the walker calls ``clarity_gate``
# (Spec 322 Slice 2) before confirming the Intent, making an underspecified
# Intent structurally un-confirmable via the walk (not just a human check).
GUIDED_DISCOVERY_SKILL: dict = {
    "name": "guided-discovery",
    "kind": "discipline",
    "applies_when": {
        "kind": "pattern",
        "pattern": r"new|fresh|not sure|vague|what do i want|where do i start|start",
        "confidence": 0.7,
    },
    "phases": [
        {
            "index": 1, "name": "elicit",
            "produces": ["draft_intent", "elicitation_turns"],
            "verbs": ["interview"],
        },
        {
            "index": 2, "name": "ground",
            "produces": ["citations", "feasibility_signal"],
            "verbs": ["ground", "feasibility"],
        },
        {
            "index": 3, "name": "clarify",
            "produces": ["ambiguities_resolved"],
            "verbs": ["clarify"],
        },
        {
            "index": 4, "name": "frame",
            "produces": ["sharp_intent"],
            "verbs": ["frame"],
        },
        {
            "index": 5, "name": "examine",
            "produces": ["thinking_findings"],
            "verbs": ["examine"],
        },
        {
            "index": 6, "name": "scope",
            "produces": ["scope_boundaries", "acceptance_criteria"],
            "verbs": ["scope", "acceptance"],
        },
        {
            "index": 7, "name": "decide",
            "produces": ["confirmed_intent"],
            "verbs": ["clarity"],
            "gate": "computed",
            "gate_verb": "clarity_gate",
        },
    ],
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
    skills={"guided-discovery": GUIDED_DISCOVERY_SKILL},
)
