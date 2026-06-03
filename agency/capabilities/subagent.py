"""subagent — subagent-driven-development as a composition.

Dispatch a worker as a child Lifecycle (via `delegate`), then run a TWO-STAGE
gated review over that child
(via `gate`): spec-review first, then quality-review. The child is `done` only
when BOTH gates pass — a verified join. A failing spec-review pauses the child at
input-required and the quality stage is skipped.

The review verdicts are inputs (the gate predicate's `passed`), so the discipline
is judgment-as-code and records real Gate provenance. The worker `driver` is any
local capability/verb (the local-subagent driver) or `jules` (remote).
"""
from __future__ import annotations

from ..capability import CapabilityBase, verb


class SubagentCapability(CapabilityBase):
    name = "subagent"
    home = "lifecycle"

    @verb(role="effect")
    def develop(self, driver: str, driver_verb: str, item: dict,
                spec_passed: bool, quality_passed: bool,
                spec_evidence: str = "", quality_evidence: str = "") -> dict:
        """Dispatch a worker child via delegate, then gate it spec-review→quality-review; done iff both pass.

        Inputs: driver (capability name), driver_verb (str), item (dict
                — task payload), spec_passed (bool), quality_passed (bool),
                spec_evidence/quality_evidence (str, optional).
        Returns: ``{result: {child, done, spec, quality}}``.
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
