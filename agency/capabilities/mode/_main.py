# agency-scaffold: v1
"""mode — behavioral modes, first-class (Spec 295).

A native reimplementation of SuperClaude's behavioral modes: postures that
change HOW the agent operates. Decidable (like `panel`/`thinking`): trigger-term
overlap selects the mode; activation returns the posture's behavioral rules and
records a `ModeActivation` node, so a session's adopted postures are provenance.

Use when: the way of working should shift for the task at hand — discovery,
self-analysis, tool-routing, multi-step orchestration, or compressed output.
Triggers:
- A vague or exploratory request that needs discovery before building
- A meta-cognitive ask: inspect reasoning, reflect on a failed approach
- A multi-tool or multi-step operation that needs routing or phasing
- A brevity-constrained context that needs compressed output
Red flags:
- Diving into build on a vague request → activate brainstorming first
- Repeating a failed approach → activate introspection to inspect the reasoning
"""
from __future__ import annotations

import re

from ...capability import CapabilityBase, verb
from ...ontology import OntologyExtension


# name · purpose · behaviors (the posture) · triggers (decidable selection)
# · flags. Extracted from SuperClaude modes/MODE_*.md, authored as native data.
_MODES = [
    {"name": "brainstorming",
     "purpose": "Collaborative discovery for vague or exploratory requests.",
     "behaviors": ["Ask probing Socratic questions before proposing.",
                   "Surface hidden + unstated requirements.",
                   "Do not assume — confirm scope with the user.",
                   "Co-create rather than prescribe."],
     "triggers": ["brainstorm", "explore", "discuss", "not sure", "maybe",
                  "possibly", "thinking about", "could we", "vague", "idea",
                  "figure out"],
     "flags": ["--brainstorm", "--bs"]},
    {"name": "introspection",
     "purpose": "Meta-cognitive self-analysis of reasoning and decisions.",
     "behaviors": ["Expose the reasoning chain, not just the conclusion.",
                   "Question your own decision logic.",
                   "Name assumptions and where they could be wrong.",
                   "Look for recurring patterns + optimization opportunities."],
     "triggers": ["analyze my reasoning", "reflect", "why did", "unexpected",
                  "error", "recurring", "meta", "introspect", "reconsider"],
     "flags": ["--introspect", "--introspection"]},
    {"name": "orchestration",
     "purpose": "Intelligent tool selection + resource-aware routing.",
     "behaviors": ["Pick the most powerful tool for each task type.",
                   "Identify independent operations to run in parallel.",
                   "Adapt the approach to resource constraints."],
     "triggers": ["multi-tool", "parallel", "performance", "resource",
                  "routing", "coordinate", "concurrent"],
     "flags": []},
    {"name": "task_management",
     "purpose": "Hierarchical organization of complex multi-step operations.",
     "behaviors": ["Decompose the work into phased tasks.",
                   "Track dependencies between steps.",
                   "Persist task state across the operation."],
     "triggers": ["multi-step", "phases", "dependencies", "refine", "polish",
                  "enhance", "delegate", "steps", "milestones"],
     "flags": ["--task-manage", "--delegate"]},
    {"name": "token_efficiency",
     "purpose": "Symbol-enhanced, compressed communication under constraints.",
     "behaviors": ["Use symbols for logic/status/technical domains.",
                   "Apply context-aware abbreviation.",
                   "Target 30-50% token reduction, preserving >=95% of meaning."],
     "triggers": ["ultracompressed", "brevity", "concise", "large-scale",
                  "context high", "compress", "terse"],
     "flags": ["--uc", "--ultracompressed"]},
]

_BY_NAME = {m["name"]: m for m in _MODES}


class ModeCapability(CapabilityBase):
    name = "mode"
    home = "lifecycle"   # a mode parameterizes HOW work proceeds
    ontology = OntologyExtension(
        nodes={"ModeActivation": ["mode"]},
        enums={("ModeActivation", "mode"): set(_BY_NAME)},
    )

    @verb(role="act")
    def list(self) -> dict:
        """The behavioral-mode roster — name · purpose · behaviors · triggers.

        Returns: ``{count, modes: [...]}``.
        chain_next: mode.detect(context) or mode.activate(mode).
        """
        return {"count": len(_MODES),
                "modes": [{k: m[k] for k in ("name", "purpose", "behaviors", "flags")}
                          for m in _MODES]}

    def _score(self, context: str) -> list[tuple[int, dict]]:
        low = context.lower()
        scored = []
        for m in _MODES:
            n = sum(1 for t in m["triggers"] if t in low)
            n += sum(1 for f in m["flags"] if f in low)
            if n:
                scored.append((n, m))
        scored.sort(key=lambda x: -x[0])
        return scored

    @verb(role="act")
    def detect(self, context: str) -> dict:
        """Rank the behavioral modes by decidable trigger overlap with
        ``context`` (read-only).

        Returns: ``{matches: [{mode, score}], top}`` (``top`` empty if none).
        chain_next: mode.activate(mode=top, context=...).
        """
        scored = self._score(context)
        return {"matches": [{"mode": m["name"], "score": n} for n, m in scored],
                "top": scored[0][1]["name"] if scored else ""}

    @verb(role="effect")
    def activate(self, mode: str = "auto", context: str = "") -> dict:
        """Activate a behavioral posture — return its rules + record provenance
        (Spec 295).

        ``mode="auto"`` resolves the top mode for ``context`` via ``detect``
        (falls back to ``brainstorming`` when nothing matches — discovery is the
        safe default for an unclear request). Records a ``ModeActivation`` node
        SERVING the intent, so adopted postures are queryable provenance.

        Inputs: mode (auto | one of the five mode names), context (str — the
                request/situation, used for auto-resolution).
        Returns: ``{mode, purpose, behaviors, flags, activation_id}`` or ``{error}``.
        chain_next: adopt the behaviors; mode.activate again as the task shifts.
        """
        if mode == "auto":
            scored = self._score(context)
            resolved = scored[0][1]["name"] if scored else "brainstorming"
        else:
            resolved = mode
        spec = _BY_NAME.get(resolved)
        if spec is None:
            return {"error": f"unknown mode {mode!r}; one of {sorted(_BY_NAME)}",
                    "mode": mode}
        activation_id = self.ctx.record_and_serve("ModeActivation", {"mode": resolved})
        return {"mode": resolved, "purpose": spec["purpose"],
                "behaviors": spec["behaviors"], "flags": spec["flags"],
                "activation_id": activation_id}
