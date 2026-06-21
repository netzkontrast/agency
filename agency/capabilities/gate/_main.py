# agency-scaffold: v1
"""gate — a reusable, programmatic gate predicate.

Gate evaluates a reusable predicate and records the outcome as a Gate node edged into the lifecycle and intent, so a pass or block is auditable provenance.

Use when: a programmatic, reusable predicate must pass before work proceeds — an acceptance check recorded as a Gate in the provenance graph.
Triggers:
- A decision point that must be enforced, not assumed
- An acceptance condition that should be recorded as provenance
Red flags:
- Proceeding past a decision point on an assumption → record it with capability_gate_check
- Reading a CI/quality verdict from a bare exit code instead of auditable provenance → use capability_gate_verdict
"""
from __future__ import annotations

from ...capability import ArtefactSchemas, CapabilityBase, verb




class GateCapability(CapabilityBase):
    name = "gate"
    home = "lifecycle"   # uses the core Gate node + PASSED/BLOCKED_ON edges — no extension needed
    artefact_schemas = ArtefactSchemas.from_module(__file__)

    @verb(role="act")
    def check(self, lifecycle_id: str, name: str, passed: bool, evidence: str = "") -> dict:
        """Record a gate outcome on a Lifecycle: PASSED, or BLOCKED_ON +
        an input-required pause on failure.

        Inputs: lifecycle_id (str — the Lifecycle to gate),
                name (str — gate name), passed (bool — outcome),
                evidence (str — optional rationale).
        Returns: ``{passed, gate}`` (wire shape); on a wrong-intent
        guard fail, ``{error, lifecycle_id}``.
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
        if not self.ctx.has_edge(lifecycle_id, chain, "SERVES",
                                 src_label="Lifecycle", dst_label="Intent"):
            return {"result": {"error": "lifecycle does not serve the current intent (or its amended chain)",
                               "lifecycle_id": lifecycle_id}}
        g = self.ctx.record("Gate", {"name": name, "passed": bool(passed), "evidence": evidence})
        self.ctx.link(lifecycle_id, g, "PASSED" if passed else "BLOCKED_ON")
        if not passed and self.ctx.lifecycle.status(lifecycle_id) != "input-required":
            # Spec 339/344 — route the pause through the SOLE state writer so the
            # blocked transition emits a durable transition Event for free (the
            # guard avoids a no-op raise when a gate fails on an already-paused
            # lifecycle — same idempotency the old raw `update` had).
            self.ctx.lifecycle.move(lifecycle_id, "input-required", evidence=evidence)
        return {"result": {"passed": bool(passed), "gate": g}}

    @verb(role="act")
    def verdict(self, name: str) -> dict:
        """Read the LATEST Gate by name and report its pass/block verdict — the
        reusable CI reader (Spec 382 §2, OQ2). Named ``verdict`` because ``assert``
        is a Python keyword. READ-ONLY over the graph (records no new Gate); in CI
        the caller exits non-zero iff ``blocked`` is True.

        Inputs: name (str — the gate name, e.g. "quality:review").
        Returns: ``{name, found, passed, blocked, evidence}``; an unknown name is
        ``found=False, blocked=False`` (nothing to block on).
        chain_next: in CI, exit non-zero when ``blocked``; else proceed.
        """
        gates = [g for g in self.ctx.find("Gate") if g.get("name") == name]
        if not gates:
            return {"name": name, "found": False, "passed": None, "blocked": False}
        gates.sort(key=lambda g: g.get("vfrom", 0))
        latest = gates[-1]
        passed = bool(latest.get("passed"))
        return {"name": name, "found": True, "passed": passed,
                "blocked": not passed, "evidence": latest.get("evidence", "")}

    @verb(role="act")
    def adjudicate(self, a: str, b: str, lifecycle_id: str = "") -> dict:
        """Adjudicate two CONFLICTING concerns at a decision point by consulting
        ``doctrine.resolve`` — the priority-hierarchy winner (safety > correctness
        > maintainability > speed), recorded as a Gate (Spec 303).

        This is doctrine's real consumer: rather than guessing which concern wins
        a tradeoff, the gate delegates to the doctrine capability (recording a
        ``doctrine.resolve`` Invocation that SERVES the intent) and persists the
        verdict as auditable Gate provenance.

        Inputs: a (str — one concern), b (str — the conflicting concern),
                lifecycle_id (str — optional Lifecycle to edge the verdict onto).
        Returns: ``{result: {winner, winner_category, loser, tie, rationale,
                   gate}}``.
        chain_next: proceed with the winning concern; doctrine.cite it.
        """
        resolution = self.ctx.call("doctrine", "resolve", a=a, b=b)
        decided = not resolution.get("tie", False)
        g = self.ctx.record("Gate", {
            "name": f"conflict:{a}-vs-{b}",
            "passed": decided,
            "evidence": resolution.get("rationale", ""),
        })
        if lifecycle_id:
            chain = list(self.ctx.memory._intent_chain(self.ctx.intent_id))
            if self.ctx.has_edge(lifecycle_id, chain, "SERVES",
                                 src_label="Lifecycle", dst_label="Intent"):
                self.ctx.link(lifecycle_id, g, "PASSED" if decided else "BLOCKED_ON")
        return {"result": {
            "winner": resolution.get("winner", ""),
            "winner_category": resolution.get("winner_category", ""),
            "loser": resolution.get("loser", ""),
            "tie": resolution.get("tie", False),
            "rationale": resolution.get("rationale", ""),
            "gate": g,
        }}
