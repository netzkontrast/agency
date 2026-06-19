# agency-scaffold: v1
"""select — complexity-scored approach selection, first-class (Spec 296).

A native, generalized reimplementation of SuperClaude's `sc-select-tool`: score
an operation's complexity and route it to the right approach archetype —
`semantic` (structure-aware, accurate), `pattern` (fast bulk edits), or `native`
(safe default). Decidable (like `panel`/`mode`); records the choice as
provenance. Answers a different question than `delegate.dispatch_decision`
(inline-vs-dispatch): *which approach* for the operation.

Use when: an operation could be done several ways and the right approach depends
on its shape — symbol-aware vs bulk-pattern vs built-in, accuracy vs speed.
Triggers:
- A refactor/edit operation whose approach is not obvious
- A bulk transformation where speed vs precision matters
- A routing decision between structure-aware and pattern-based tooling
Red flags:
- Bulk-editing across many files with a symbol tool → route to pattern
- Renaming a symbol with blind find-replace → route to semantic
"""
from __future__ import annotations

from ..._capture import keep_full
from ...capability import CapabilityBase, verb
from ...ontology import OntologyExtension


_ARCHETYPES = {
    "semantic": "Structure-aware (symbols, types, references); accurate, slower.",
    "pattern":  "Fast bulk / regex transformations; speed over precision.",
    "native":   "Built-in tools; the safe default for middling operations.",
}

# Operation keyword indicators (decidable scoring of "semantic-ness").
_SEMANTIC = ("symbol", "rename", "refactor", "navigate", "type", "definition",
             "reference", "signature", "semantic", "extract method", "interface")
_PATTERN = ("pattern", "bulk", "replace", "regex", "across", "all occurrences",
            "mass", "find-replace", "sweep", "every file", "global")
# Direct mappings that override the score (SuperClaude "Direct Mapping").
_FORCE_SEMANTIC = ("memory", "context", "save", "persist", "cross-session")


# Spec 301 Slice 2 — the walkable discipline (superpowers' signature):
# characterize the operation, weigh the archetypes, route to one, commit behind
# a hard gate. Mirrors the select verb flow (archetypes → route).
_APPROACH_ROUTING_SKILL = {
    "name": "approach-routing", "kind": "discipline",
    "phases": [
        {"index": 1, "name": "characterize", "produces": ["operation", "scope"]},
        {"index": 2, "name": "weigh", "produces": ["candidates"]},
        {"index": 3, "name": "route", "produces": ["approach"]},
        {"index": 4, "name": "commit", "produces": ["rationale"], "gate": "hard"},
    ],
}


class SelectCapability(CapabilityBase):
    name = "select"
    home = "lifecycle"   # a routing decision parameterizing HOW work proceeds
    ontology = OntologyExtension(
        nodes={"Selection": ["operation", "approach"]},
        enums={("Selection", "approach"): set(_ARCHETYPES)},
        skills={"approach-routing": _APPROACH_ROUTING_SKILL},
    )

    @verb(role="act")
    def archetypes(self) -> dict:
        """The approach archetypes + their trade-offs.

        Inputs: (none).
        Returns: ``{count, archetypes: {name: description}}``.
        chain_next: select.route(operation) to pick one for an operation.
        """
        return {"count": len(_ARCHETYPES), "archetypes": dict(_ARCHETYPES)}

    def _score(self, operation: str, file_count: int, speed_priority: bool) -> float:
        low = operation.lower()
        score = 0.5
        score += 0.15 * sum(1 for t in _SEMANTIC if t in low)
        score -= 0.15 * sum(1 for t in _PATTERN if t in low)
        if file_count > 3:
            score += 0.1            # multi-file work rewards structural understanding
        if speed_priority:
            score -= 0.2            # speed favours the fast pattern engine
        return max(0.0, min(1.0, score))

    @verb(role="effect")
    def route(self, operation: str, file_count: int = 1,
              speed_priority: bool = False) -> dict:
        """Route an ``operation`` to an approach archetype by decidable
        complexity scoring (Spec 296).

        Computes a semantic-ness score in [0,1] from the operation's keywords,
        ``file_count``, and ``speed_priority``; direct mappings (memory/context)
        force ``semantic``. Thresholds: score >= 0.6 → semantic, <= 0.4 →
        pattern, else native. Records a ``Selection`` node SERVING the intent.

        Inputs: operation (str — what is being done), file_count (int),
                speed_priority (bool — bias toward the fast pattern engine).
        Returns: ``{operation, approach, score, confidence, rationale, fallback}``.
        chain_next: execute via the chosen approach; fall back along the chain.
        """
        low = operation.lower()
        forced = any(t in low for t in _FORCE_SEMANTIC)
        score = 1.0 if forced else self._score(operation, file_count, speed_priority)
        if score >= 0.6:
            approach, fallback = "semantic", ["pattern", "native"]
        elif score <= 0.4:
            approach, fallback = "pattern", ["semantic", "native"]
        else:
            approach, fallback = "native", ["semantic", "pattern"]
        if forced:
            rationale = "direct mapping: memory/context operations → semantic"
        else:
            rationale = (f"score={score:.2f} (semantic-ness); "
                         f"{'multi-file; ' if file_count > 3 else ''}"
                         f"{'speed-priority; ' if speed_priority else ''}"
                         f"threshold → {approach}")
        sel_id = self.ctx.record_and_serve("Selection", {
            "operation": keep_full(operation, label="selection operation"),
            "approach": approach})
        return {"operation": operation, "approach": approach,
                "score": round(score, 3),
                "confidence": round(abs(score - 0.5) * 2, 3),
                "rationale": rationale, "fallback": fallback,
                "selection_id": sel_id}
