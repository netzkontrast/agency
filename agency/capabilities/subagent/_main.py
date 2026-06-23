# agency-scaffold: v1
"""subagent — subagent-driven-development as a composition.

Subagent composes subagent-driven development: a self-contained task is dispatched into a clean context and its verified result returns to the orchestrator.

Use when: a unit of work should be composed as subagent-driven development — isolating a task to a dispatched subagent that returns a verified result.
Triggers:
- A self-contained task suited to a dispatched subagent
- Work whose context is heavy enough to isolate from the main thread
"""
from __future__ import annotations

from ...capability import ArtefactSchemas, CapabilityBase, verb
from ...ontology import OntologyExtension

# Spec 041 — the subagent-driven-development discipline (Superpowers port, agency-flavoured):
# write a crisp task spec, dispatch an implementer into a clean context, then a TWO-STAGE
# review gate — spec-fidelity (soft) then code-quality (hard). The dispatch + gates bind to
# `subagent.develop`, whose `spec_passed`/`quality_passed` inputs ARE the two stages.
_SUBAGENT_DRIVEN_SKILL = {
    "name": "subagent-driven-development",
    "kind": "discipline",
    "applies_when": {"kind": "pattern",
                     "pattern": r"subagent|isolate|clean context|two.?stage review",
                     "confidence": 0.7},
    "phases": [
        # Spec 378 — inline phase content (A1/A6) for subagent-driven development.
        {"index": 1, "name": "write-spec", "produces": ["task_spec"],
         "goal": "Write a self-contained task spec for the subagent.",
         "instructions": "Spell out the task so a fresh subagent succeeds with NO parent "
                         "context — goal, acceptance, the files in scope, and what NOT to "
                         "touch. A vague spec yields a vague implementation.",
         "freedom": "high"},
        {"index": 2, "name": "dispatch", "produces": ["implementation"],
         "verbs": ["subagent.develop"],
         "goal": "Dispatch the subagent to implement the spec.",
         "instructions": "subagent.develop the spec as a child run; the subagent returns "
                         "an implementation, not a conversation. Only the result crosses "
                         "back.",
         "freedom": "medium"},
        {"index": 3, "name": "spec-review", "produces": ["spec_passed"], "gate": "soft",
         "goal": "Check the implementation against the spec.",
         "instructions": "Verify the implementation does what the SPEC asked — scope, "
                         "acceptance. A soft gate: note gaps, but the code-review gate is "
                         "the hard one.",
         "freedom": "medium"},
        {"index": 4, "name": "code-review", "produces": ["quality_passed"], "gate": "hard",
         "goal": "Review the code for correctness + the Iron Law.",
         "instructions": "Review for correctness first, then over-engineering / duplication "
                         "(the Iron Law). Confirm this hard gate only when the code is "
                         "genuinely mergeable.",
         "freedom": "low"},
    ],
}


class SubagentCapability(CapabilityBase):
    name = "subagent"
    home = "lifecycle"
    # Spec 342 — a review-gated subagent IS the "reviewed" Lifecycle
    # parameterization: its child runs on a machine whose `in-review` state
    # inserts COMPLETED != done. `develop` opens the child reviewed and moves it
    # working→in-review→completed through the SOLE state writer (lifecycle.move)
    # only when both gates pass — so the gate path is enforced, not assumed.
    parameterization = "reviewed"
    ontology = OntologyExtension(skills={"subagent-driven-development": _SUBAGENT_DRIVEN_SKILL})
    artefact_schemas = ArtefactSchemas.from_module(__file__)

    @verb(role="effect")
    def develop(self, driver: str, driver_verb: str, item: dict,
                spec_passed: bool, quality_passed: bool,
                spec_evidence: str = "", quality_evidence: str = "") -> dict:
        """Dispatch a worker child and gate it through spec-review then quality-review (effect).

        Inputs: driver (capability name), driver_verb (str), item (dict
                — task payload), spec_passed (bool), quality_passed (bool),
                spec_evidence/quality_evidence (str, optional).
        Returns: ``{child, done, spec, quality}`` (wire shape).
        chain_next: terminal — ``done=True`` flips the child Lifecycle to
                    ``completed``; ``done=False`` leaves it ``input-required``.
        """
        # Spec 342 — dispatch the child under the "reviewed" parameterization so
        # its machine inserts the `in-review` observer state (COMPLETED != done).
        fan = self.ctx.call("delegate", "fan_out",
                            driver=driver, driver_verb=driver_verb, items=[item], quota=1,
                            parameterization="reviewed")
        child = fan["result"]["children"][0]["lifecycle"]
        spec = self.ctx.call("gate", "check", lifecycle_id=child, name="spec-review",
                            passed=bool(spec_passed), evidence=spec_evidence)["result"]
        quality = None
        if spec_passed:
            quality = self.ctx.call("gate", "check", lifecycle_id=child, name="quality-review",
                                    passed=bool(quality_passed), evidence=quality_evidence)["result"]
        done = bool(spec_passed and quality_passed)
        if done:
            # Spec 342 — drive working→in-review→completed through the SOLE state
            # writer (lifecycle.move), NOT a raw Lifecycle().close(): the reviewed
            # machine forbids working→completed directly, so this path proves both
            # gates were the route. (A failed gate already moved the child to
            # input-required via gate.check.)
            self.ctx.lifecycle.move(child, "in-review", evidence="spec+quality passed")
            self.ctx.lifecycle.move(child, "completed", evidence="verified join")
        return {"result": {"child": child, "done": done, "spec": spec, "quality": quality}}
