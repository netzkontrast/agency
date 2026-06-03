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

    @verb(role="act")
    def check(self, lifecycle_id: str, name: str, passed: bool, evidence: str = "") -> dict:
        """Record a gate outcome on a Lifecycle: PASSED, or BLOCKED_ON +
        an input-required pause on failure.

        Inputs: lifecycle_id (str — the Lifecycle to gate),
                name (str — gate name), passed (bool — outcome),
                evidence (str — optional rationale).
        Returns: ``{result: {passed, gate}}`` on success; on a wrong-intent
        guard fail, ``{result: {error, lifecycle_id}}``.
        chain_next: a failed gate flips the Lifecycle to ``input-required``;
                    caller resumes by re-invoking the parent verb with
                    ``confirmed=True`` (Hint #8).

        Codex C2 (capability/gate.py:25): an exact ``i.id = $iid`` match
        rejected lifecycles serving a pre-amend intent — `memory.provenance`
        deliberately walks the ``SUPERSEDED_BY`` chain (memory.py:161-175),
        but this guard didn't. A gate against an amended intent would
        incorrectly report "lifecycle does not serve the current intent"
        and silently drop the gate outcome. Fix: query the whole
        ``SUPERSEDED_BY`` chain via ``memory._intent_chain``.
        """
        chain = list(self.ctx.memory._intent_chain(self.ctx.intent_id))
        if not self.ctx.memory.g.query(
                "MATCH (l:Lifecycle)-[:SERVES]->(i:Intent) "
                "WHERE l.id = $l AND i.id IN $ids RETURN i",
                {"l": lifecycle_id, "ids": chain}):
            return {"result": {"error": "lifecycle does not serve the current intent (or its amended chain)",
                               "lifecycle_id": lifecycle_id}}
        g = self.ctx.record("Gate", {"name": name, "passed": bool(passed), "evidence": evidence})
        self.ctx.link(lifecycle_id, g, "PASSED" if passed else "BLOCKED_ON")
        if not passed:
            self.ctx.memory.update(lifecycle_id, {"state": "input-required"})
        return {"result": {"passed": bool(passed), "gate": g}}
