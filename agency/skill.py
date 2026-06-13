"""Micro-step skill walker.

A skill is a Lifecycle of ordered Phases (a schema a capability contributes, e.g.
the `develop` or `plugin` skills). The walker is the complete implementation of
"real micro-step skills":

- **Progressive disclosure / token efficiency:** `current()` returns ONLY the
  current phase's spec (its required outputs) — never the whole skill.
- **Strict per-phase validation:** `submit()` rejects a phase whose required
  outputs are missing.
- **Hard gate:** a phase marked `gate: hard` (e.g. a skill's final approve phase)
  blocks at `input-required` until an explicit confirmation — the elicit gate.
- **Provenance:** every phase is recorded as a `Phase` node, edged into the
  `Skill` run (`HAS_PHASE`), the intent (`SERVES`), and the prior phase
  (`PRECEDES`). A skill run IS provenance.
"""
from __future__ import annotations

from typing import Optional

from .memory import Memory


class SkillRun:
    def __init__(self, memory: Memory, intent_id: str, schema: dict, registry=None):
        # Spec 152 Slice 2 — validate the schema at the parse boundary so
        # malformed phases fail fast at SkillRun construction with a typed
        # `Codes.*` instead of crashing mid-walk on `phase["produces"]`.
        from ._skill_parse import parse_skill
        _res = parse_skill(schema)
        if not _res.ok:
            raise ValueError(
                f"skill schema invalid ({_res.code}): {_res.message}")
        self.memory = memory
        self.intent_id = intent_id
        self.schema = schema
        self.phases = schema["phases"]
        self.registry = registry            # wire it to EXECUTE `invoke` phases; omit to walk by hand
        self.i = 0
        self.skill_id = memory.record("Skill", {"name": schema["name"], "kind": schema["kind"]})
        memory.link(self.skill_id, intent_id, "SERVES")
        self._prev_phase: Optional[str] = None

    @classmethod
    def resume(cls, memory: Memory, intent_id: str, schema: dict,
               skill_id: str, registry=None) -> "SkillRun":
        """Rebind to an EXISTING Skill run (Spec 018 Win 1 resume contract).

        A fresh `SkillRun.__init__` mints a new Skill node; resume instead
        reconstructs the walker's position from the append-only graph: the
        count of recorded `Phase` nodes IS the next phase index (a paused
        hard gate records a Gate, not a Phase, so the gate phase is exactly
        the one we re-enter). The skill_id is the cross-call/cross-session
        bridge (Spec 020 central DB)."""
        self = cls.__new__(cls)
        self.memory = memory
        self.intent_id = intent_id
        self.schema = schema
        self.phases = schema["phases"]
        self.registry = registry
        self.skill_id = skill_id
        rows = memory.g.query(
            "MATCH (s:Skill)-[:HAS_PHASE]->(p:Phase) WHERE s.id = $sid RETURN p",
            {"sid": skill_id})
        recorded = [r["p"]["properties"] for r in rows]
        self.i = len(recorded)
        self._prev_phase = (
            max(recorded, key=lambda p: p.get("index", 0)).get("id")
            if recorded else None)
        return self

    @property
    def done(self) -> bool:
        return self.i >= len(self.phases)

    def current(self) -> Optional[dict]:
        """Progressive disclosure: only the current phase's spec (required outputs)."""
        if self.done:
            return None
        p = self.phases[self.i]
        return {"index": p["index"], "name": p["name"], "produces": list(p["produces"]),
                "inputs": list(p.get("inputs", [])), "gate": p.get("gate")}

    def submit(self, outputs: Optional[dict] = None, confirmed: bool = False) -> dict:
        """Advance one phase. An executable phase (`invoke`) runs a REAL capability
        verb (recorded as an Invocation) and uses its output to satisfy the schema;
        a plain phase consumes the submitted `outputs`. Execution is opt-in: an
        `invoke` phase runs the verb only when a `registry` was wired — without one
        it degrades to a plain document phase, so a discipline stays walkable by
        hand. Missing required outputs raise; a hard gate pauses at `input-required`
        until confirmed."""
        if self.done:
            raise RuntimeError("skill run already complete")
        p = self.phases[self.i]
        outputs = dict(outputs or {})
        inv_id = None
        if "invoke" in p and self.registry is not None:
            spec = p["invoke"]
            args = {k: outputs[k] for k in p.get("inputs", []) if k in outputs}
            result, inv_id = self.registry.invoke(
                self.memory, self.intent_id, spec["capability"], spec["verb"], **args)
            val = result.get("result", result) if isinstance(result, dict) else result
            outputs[p["produces"][0]] = val                  # real tool output satisfies the schema
        missing = [f for f in p["produces"] if outputs.get(f) in (None, "")]
        if missing:
            raise ValueError(f"phase {p['name']!r} missing required outputs: {missing}")
        # Codex C3 (skill.py:72): an unconfirmed hard gate previously returned
        # `input-required` but wrote no Gate / blocked-state to the graph —
        # auditors could not see WHY a run paused. Fix: record a
        # `Gate{passed:False, paused:True}` + `BLOCKED_ON` edge from the
        # SkillRun to the Gate before returning, so the pause is provenance.
        # On the confirmed re-submission path, record a symmetric
        # `Gate{passed:True}` + `PASSED` edge so the resume is also
        # provenance — the append-only graph carries both halves of the
        # block→resume cycle.
        if p.get("gate") == "hard" and not confirmed:
            blocked_id = self.memory.record("Gate", {
                "name": p["name"], "passed": False, "paused": True,
                "evidence": f"hard gate at phase {p['name']!r} awaiting confirmation",
            })
            self.memory.link(self.skill_id, blocked_id, "BLOCKED_ON")
            self.memory.link(blocked_id, self.intent_id, "SERVES")
            # Spec 282 Workstream H — the pause must tell the caller HOW to
            # resume: the exact `resume_from` value (the PHASE NAME, not the
            # gate node id) + the outputs to supply. The bare `blocked_on:
            # gate-id` left callers guessing (the ingest hit this).
            return {"status": "input-required", "phase": p["name"], "gate": "hard",
                    "blocked_on": blocked_id,
                    "resume_from": p["name"],
                    "resume_with": list(p["produces"]),
                    "hint": (f"resume with resume_from={p['name']!r} and supply "
                             f"{list(p['produces'])} (resume_from is the PHASE "
                             f"NAME, not the gate id {blocked_id!r})")}
        if p.get("gate") == "hard" and confirmed:
            passed_id = self.memory.record("Gate", {
                "name": p["name"], "passed": True, "paused": False,
                "evidence": f"hard gate at phase {p['name']!r} confirmed",
            })
            self.memory.link(self.skill_id, passed_id, "PASSED")
            self.memory.link(passed_id, self.intent_id, "SERVES")
        phase_id = self.memory.record("Phase", {
            "skill": self.schema["name"], "index": p["index"], "name": p["name"],
            "produces": ",".join(p["produces"]),
        })
        self.memory.link(self.skill_id, phase_id, "HAS_PHASE")
        self.memory.link(phase_id, self.intent_id, "SERVES")
        if self._prev_phase:
            self.memory.link(self._prev_phase, phase_id, "PRECEDES")
        if inv_id:
            self.memory.link(phase_id, inv_id, "PRECEDES")   # the phase owns its real invocation
        self._prev_phase = phase_id
        self.i += 1
        # Spec 018 Win 1: surface the post-phase outputs map (incl. a real
        # invoke phase's tool result) so the atomic walker can accumulate
        # them into its `outputs` / `partial_outputs` contract. Additive —
        # the pause path above returns before here, so a paused phase never
        # leaks its placeholder produces into the accumulated outputs.
        return {"status": "completed" if self.done else "working",
                "phase": p["name"], "outputs": outputs}

