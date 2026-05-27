"""gate — a reusable, programmatic gate predicate.

The hard-gate predicate as a first-class capability verb, callable by any
capability or skill via `ctx.call`. Where `lifecycle_gate` (the engine tool) asks
a human via `ctx.elicit`, `gate.check` records a *computed* gate outcome on a
Lifecycle: a PASSED edge when it passes, a BLOCKED_ON edge + an `input-required`
pause when it fails — so a failed gate is provenance and the run halts for
re-entry. This is what `subagent-driven-development` (spec-review then
quality-review) and a verified `delegate.join` compose with.
"""
from __future__ import annotations

from ..capability import CapabilityBase, verb


class GateCapability(CapabilityBase):
    name = "gate"
    home = "lifecycle"   # uses the core Gate node + PASSED/BLOCKED_ON edges — no extension needed

    @verb(role="transform")
    def check(self, lifecycle_id: str, name: str, passed: bool, evidence: str = "") -> dict:
        "Record a gate outcome on a Lifecycle: PASSED, or BLOCKED_ON + an input-required pause on failure."
        g = self.ctx.record("Gate", {"name": name, "passed": bool(passed), "evidence": evidence})
        self.ctx.link(lifecycle_id, g, "PASSED" if passed else "BLOCKED_ON")
        if not passed:
            self.ctx.memory.update(lifecycle_id, {"state": "input-required"})
        return {"result": {"passed": bool(passed), "gate": g}}
