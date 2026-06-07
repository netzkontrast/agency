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
        {"index": 1, "name": "write-spec", "produces": ["task_spec"]},
        {"index": 2, "name": "dispatch", "produces": ["implementation"],
         "verbs": ["subagent.develop"]},
        {"index": 3, "name": "spec-review", "produces": ["spec_passed"], "gate": "soft"},
        {"index": 4, "name": "code-review", "produces": ["quality_passed"], "gate": "hard"},
    ],
}


class SubagentCapability(CapabilityBase):
    name = "subagent"
    home = "lifecycle"
    ontology = OntologyExtension(skills={"subagent-driven-development": _SUBAGENT_DRIVEN_SKILL})
    artefact_schemas = ArtefactSchemas.from_module(__file__)

    @verb(role="effect")
    def develop(self, driver: str, driver_verb: str, item: dict,
                spec_passed: bool, quality_passed: bool,
                spec_evidence: str = "", quality_evidence: str = "") -> dict:
        """Dispatch a worker child via delegate, then gate it spec-review→quality-review; done iff both pass.

        Inputs: driver (capability name), driver_verb (str), item (dict
                — task payload), spec_passed (bool), quality_passed (bool),
                spec_evidence/quality_evidence (str, optional).
        Returns: ``{child, done, spec, quality}`` (wire shape).
        chain_next: terminal — ``done=True`` flips the child Lifecycle to
                    ``completed``; ``done=False`` leaves it ``input-required``.
        """
        fan = self.ctx.call("delegate", "fan_out",
                            driver=driver, driver_verb=driver_verb, items=[item], quota=1)
        child = fan["result"]["children"][0]["lifecycle"]
        spec = self.ctx.call("gate", "check", lifecycle_id=child, name="spec-review",
                            passed=bool(spec_passed), evidence=spec_evidence)["result"]
        quality = None
        if spec_passed:
            quality = self.ctx.call("gate", "check", lifecycle_id=child, name="quality-review",
                                    passed=bool(quality_passed), evidence=quality_evidence)["result"]
        done = bool(spec_passed and quality_passed)
        if done:
            self.ctx.memory.update(child, {"state": "completed"})    # verified join: both gates passed
        return {"result": {"child": child, "done": done, "spec": spec, "quality": quality}}
