# agency-scaffold: v1
"""panel — multi-expert business analysis, first-class (Spec 294).

A native reimplementation of SuperClaude's Business Panel: nine strategic
thinkers, three interaction modes (discussion · debate · socratic), decidable
content-based mode selection. Like `thinking`/`intent`, it is DECIDABLE — it
produces a structured multi-expert critique SCAFFOLD (framework lenses +
signature questions); the orchestrator (or an LLM driver) fills the voices.

Use when: a strategy / plan / business decision needs stress-testing through
multiple expert frameworks before committing — disruption, competition,
systems, risk, communication.
Triggers:
- A strategic plan or business model to evaluate
- A high-stakes or controversial decision to challenge
- A learning goal that needs Socratic, framework-driven questioning
Red flags:
- One-framework analysis of a multi-stakeholder decision → convene the panel
- Calling a strategy sound with no challenge → run convene in debate mode
"""
from __future__ import annotations

import re

from ...capability import CapabilityBase, verb
from ...ontology import OntologyExtension


# The 9 experts — name · framework · lens (analytical focus) · signature question
# · trigger terms (for relevance-based selection). Extracted from SuperClaude's
# MODE_Business_Panel + sc-business-panel-experts, authored as native data.
_EXPERTS = [
    {"name": "Christensen", "framework": "Disruptive Innovation · Jobs-to-be-Done",
     "lens": "What job is this hired to do; is it sustaining or disruptive?",
     "question": "Before claiming innovation — what job is the customer hiring this to do?",
     "triggers": ["innovation", "disrupt", "product", "customer", "job", "market", "new"]},
    {"name": "Porter", "framework": "Five Forces · Value Chain · Generic Strategies",
     "lens": "Industry structure and defensibility of advantage.",
     "question": "If this succeeds, what in the industry structure stops competitors copying it?",
     "triggers": ["competition", "industry", "advantage", "moat", "strategy", "rivals", "margin"]},
    {"name": "Drucker", "framework": "Management by Objectives · Innovation Principles",
     "lens": "Who is the customer and what do they value; effectiveness over efficiency.",
     "question": "Who is the customer, and what do they consider value?",
     "triggers": ["management", "objective", "customer", "purpose", "effective", "organization"]},
    {"name": "Godin", "framework": "Permission Marketing · Purple Cow · Tribes",
     "lens": "Remarkability and whether a tribe will choose to spread it.",
     "question": "Is this remarkable enough that the tribe chooses to spread it?",
     "triggers": ["marketing", "brand", "audience", "tribe", "remarkable", "story", "growth"]},
    {"name": "Kim & Mauborgne", "framework": "Blue Ocean · Value Innovation (ERRC)",
     "lens": "Uncontested market space via Eliminate-Reduce-Raise-Create.",
     "question": "Where is the blue ocean — what to eliminate, reduce, raise, create?",
     "triggers": ["blue ocean", "differentiation", "value", "uncontested", "niche", "new market"]},
    {"name": "Collins", "framework": "Good-to-Great · Flywheel · Hedgehog",
     "lens": "Disciplined flywheel momentum and what you can be best at.",
     "question": "Does this turn the flywheel, and is it the Hedgehog you can be best in the world at?",
     "triggers": ["scale", "discipline", "excellence", "flywheel", "growth", "execution", "great"]},
    {"name": "Taleb", "framework": "Antifragility · Black Swan · Via Negativa",
     "lens": "Exposure to disorder — fragility, robustness, or gain from volatility.",
     "question": "How does this gain from disorder, and where is the hidden black-swan fragility?",
     "triggers": ["risk", "uncertainty", "fragile", "volatility", "downside", "black swan", "robust"]},
    {"name": "Meadows", "framework": "Systems Thinking · Leverage Points",
     "lens": "Feedback loops, stocks/flows, and where leverage actually sits.",
     "question": "Where are the leverage points and feedback loops in this system?",
     "triggers": ["system", "feedback", "leverage", "loop", "dynamics", "incentive", "structure"]},
    {"name": "Doumont", "framework": "Structured Communication · Trees-Maps-Theorems",
     "lens": "Whether the message is structured for least-effort audience grasp.",
     "question": "Is the message structured so the audience grasps it with least effort?",
     "triggers": ["communicate", "message", "clarity", "present", "explain", "document", "audience"]},
]

# Decidable mode selection (SuperClaude content-analysis framework).
_DEBATE_TRIGGERS = ("controversial", "risk", "decision", "trade-off", "tradeoff",
                    "challenge", "competing", "high-stakes", "conflict")
_SOCRATIC_TRIGGERS = ("learn", "understand", "develop", "capability", "how", "why",
                      "teach", "explore")

_BALANCED = {"Christensen", "Porter", "Drucker", "Taleb", "Meadows"}


class PanelCapability(CapabilityBase):
    name = "panel"
    home = "memory"   # produces strategic-analysis provenance
    ontology = OntologyExtension(
        nodes={"Panel": ["subject", "mode"]},
        enums={("Panel", "mode"): {"discussion", "debate", "socratic"}},
    )

    @verb(role="act")
    def experts(self) -> dict:
        """The 9-expert roster — name · framework · lens · signature question.

        Returns: ``{count, experts: [...]}``.
        chain_next: panel.convene(subject) to apply the panel to a subject.
        """
        return {"count": len(_EXPERTS),
                "experts": [{k: e[k] for k in ("name", "framework", "lens", "question")}
                            for e in _EXPERTS]}

    def _select_mode(self, text: str) -> str:
        low = text.lower()
        if any(t in low for t in _DEBATE_TRIGGERS):
            return "debate"
        if any(re.search(rf"\b{re.escape(t)}\b", low) for t in _SOCRATIC_TRIGGERS):
            return "socratic"
        return "discussion"

    def _select_experts(self, text: str, focus: str) -> list[dict]:
        if focus == "full":
            return list(_EXPERTS)
        low = text.lower()
        scored = [(sum(1 for t in e["triggers"] if t in low), e) for e in _EXPERTS]
        relevant = [e for n, e in scored if n > 0]
        if len(relevant) >= 3:
            relevant.sort(key=lambda e: -sum(1 for t in e["triggers"] if t in low))
            return relevant[:5]
        # too little signal → the balanced default set
        return [e for e in _EXPERTS if e["name"] in _BALANCED]

    @verb(role="effect")
    def convene(self, subject: str, mode: str = "auto", focus: str = "balanced") -> dict:
        """Convene the panel on a ``subject`` — emit a mode-appropriate
        multi-expert critique scaffold + record it (Spec 294).

        ``mode="auto"`` selects discussion / debate / socratic from the
        subject's content (decidable triggers). ``focus="full"`` convenes all
        nine experts; otherwise the most relevant 3-5 (or a balanced default).

        Inputs: subject (str — the plan/decision/document to analyse),
                mode (auto|discussion|debate|socratic),
                focus (balanced|full).
        Returns: ``{panel_id, subject, mode, experts, analysis, synthesis}``.
        chain_next: fill each lens/question; debate → re-convene as discussion.
        """
        if mode not in ("auto", "discussion", "debate", "socratic"):
            mode = "auto"
        chosen_mode = self._select_mode(subject) if mode == "auto" else mode
        experts = self._select_experts(subject, focus)
        if chosen_mode == "socratic":
            analysis = [{"expert": e["name"], "framework": e["framework"],
                         "question": e["question"]} for e in experts]
            synthesis = "Answer each expert's question, then re-convene to synthesise."
        elif chosen_mode == "debate":
            analysis = []
            for i, e in enumerate(experts):
                other = experts[(i + 1) % len(experts)]
                analysis.append({
                    "expert": e["name"], "framework": e["framework"],
                    "challenges": other["name"],
                    "prompt": f"{e['name']} ({e['framework']}) stress-tests the subject "
                              f"and challenges {other['name']}'s framing: {e['lens']}"})
            synthesis = "Extract the insight from each productive disagreement."
        else:  # discussion
            analysis = [{"expert": e["name"], "framework": e["framework"],
                         "prompt": f"{e['name']} analyses through {e['framework']}: {e['lens']}"}
                        for e in experts]
            synthesis = "Identify convergent themes + complementary perspectives across frameworks."
        panel_id = self.ctx.record_and_serve("Panel", {
            "subject": subject[:200], "mode": chosen_mode})
        return {"panel_id": panel_id, "subject": subject, "mode": chosen_mode,
                "experts": [e["name"] for e in experts],
                "analysis": analysis, "synthesis": synthesis}
