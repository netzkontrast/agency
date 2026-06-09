# agency-scaffold: v1
"""thinking — critical-thinking capability (Spec 110).

Eight founding methods + new ones for adversarial review (red-team) and
recursive questioning (socratic). Each method is a transform that returns a
scaffold (step-by-step instructions + output schema) the agent fills out.
Methods compose: apply_full_review chains them in sequence to produce a
critical-analysis document.

Use when: a goal / spec / design needs structured rigor before commit; a
binding decision needs tradeoff + premortem + red-team; an assumption stack
needs surfacing + classification.
Triggers:
- About to commit to a decision: run apply_decision_discipline first
- About to merge a complex spec: run apply_full_review
- Suspect a load-bearing assumption is unstated: run assumptions
Red flags:
- Hand-rolling decision rationales without the discipline → call thinking verbs
- Claiming a steelman without testing the inverse → call inversion + steelman
"""
from ._main import ThinkingCapability

__all__ = ["ThinkingCapability"]
