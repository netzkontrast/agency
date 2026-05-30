"""delegate — agent orchestration: fan-out + quota + join.

The keystone primitive the capability roadmap flagged. **An agent IS a Lifecycle
parameterization** — so fanning out a task means opening one *child Lifecycle* per
unit of work (each `SERVES` the intent and is `DISPATCHED_TO` the driver agent),
dispatching the driver, and edging the child Lifecycle to the driver Invocation it
`DRIVES`. A quota caps how many children are admitted; `join` reduces over the
children's Lifecycle state (dispatched ≠ done — children start `working` until
verified). `jules` is the first driver; any capability/verb can drive.

Built on `ctx.spawn`, so every child dispatch is a recorded Invocation and the
whole delegation is a connected provenance subgraph.
"""
from __future__ import annotations

from ..capability import CapabilityBase, verb
from ..ontology import OntologyExtension


def _phase(idx: int, name: str, produces: list[str], gate: str = "") -> dict:
    p: dict = {"index": idx, "name": name, "produces": produces}
    if gate:
        p["gate"] = gate
    return p


# The dispatch-decision skill: the token-economics heuristic, walked as a
# Lifecycle template every time the orchestrator considers a fan-out. Doctrine
# about Jules's behaviour lives in AGENCY_PROTOCOL.md; this skill is about
# the orchestrator's decision, so it lives here on `delegate` (the capability
# that owns the dispatch abstraction) — not on the protocol doc.
_DISPATCH_DECISION_SKILL = {
    "name": "dispatch-decision",
    "kind": "discipline",
    "phases": [
        _phase(1, "estimate-shape", [
            "file_count",          # int — files the orchestrator has NOT seen
            "exploration_needed",  # bool — repeated grep/find through unfamiliar subtree
            "parallelism",         # int — sibling tasks that would dispatch together
            "est_duration_min",    # int — wall-clock when done inline
        ]),
        _phase(2, "apply-heuristic", [
            "recommendation",      # "inline" | "dispatch"
            "rationale",           # one-paragraph why
        ]),
        _phase(3, "assemble-bash-hints", [
            "bash_hints",          # list[str] — grep/sed/find cmds; empty when inline
        ]),
        _phase(4, "decide", ["decision"], gate="hard"),  # "inline" | "dispatch"
    ],
}


class DelegateCapability(CapabilityBase):
    name = "delegate"
    home = "lifecycle"
    ontology = OntologyExtension(
        nodes={"Delegation": ["driver", "driver_verb", "count", "quota"]},
        edges={"DELEGATES_TO", "REDUCES_INTO"},
        skills={"dispatch-decision": _DISPATCH_DECISION_SKILL},
    )

    @verb(role="transform")
    def dispatch_decision(self, file_count: int = 0, exploration_needed: bool = False,
                          parallelism: int = 1, est_duration_min: int = 0) -> dict:
        """Apply the dispatch-vs-inline heuristic and return a recommendation.

        Decision logic (pure; no provenance writes — the heuristic itself is
        a transform, and the `dispatch-decision` skill walk records the
        provenance via Phase.invoke bindings if the caller chooses to walk it).

        Dispatch wins when ANY of:
        - file_count >= 4 (context the orchestrator has not yet loaded);
        - exploration_needed (repeated grep/find through unfamiliar subtree);
        - parallelism >= 3 (fan-out amortises the per-dispatch boilerplate);
        - est_duration_min >= 15 AND the orchestrator has higher-leverage
          work waiting.

        Otherwise: inline. Dispatch costs ~700 tokens of preamble + the
        review-cycle wake budget; that overhead only pays off on the
        context-heavy / parallel / long-running shape.

        Returns ``{recommendation, rationale, triggers}`` where ``triggers``
        is the subset of criteria that fired.
        """
        triggers: list[str] = []
        if file_count >= 4:
            triggers.append("file_count>=4")
        if exploration_needed:
            triggers.append("exploration_needed")
        if parallelism >= 3:
            triggers.append("parallelism>=3")
        if est_duration_min >= 15:
            triggers.append("est_duration_min>=15")

        if triggers:
            rec = "dispatch"
            rationale = (
                f"context-heavy / parallel / long-running shape "
                f"(triggers: {', '.join(triggers)}); dispatch overhead amortises."
            )
        else:
            rec = "inline"
            rationale = (
                "clear in-context task; dispatch overhead (~700 tokens preamble "
                "+ review-cycle) exceeds inline cost."
            )
        return {"recommendation": rec, "rationale": rationale, "triggers": triggers}

    @verb(role="transform")
    def dispatch_bash_hints(self, paths: str = "", symbols: str = "") -> dict:
        """Compose the bash-hint context block for a dispatch prompt.

        When the orchestrator decides to dispatch (per ``dispatch_decision``),
        hand the agent the exact bash commands that surface the right files
        — cheap on orchestrator tokens (no file contents quoted), fast for
        the agent (no flailing).

        ``paths`` and ``symbols`` are comma-separated. Empty → empty hints.
        Returns ``{hints: [str], block: str}`` where ``block`` is the
        ready-to-paste markdown.
        """
        ps = [s.strip() for s in paths.split(",") if s.strip()] if paths else []
        ss = [s.strip() for s in symbols.split(",") if s.strip()] if symbols else []
        hints: list[str] = []
        for p in ps:
            hints.append(f"find {p} -type f | head -50")
        for s in ss:
            hints.append(f"grep -rn '{s}' agency/ tests/ 2>/dev/null | head -30")
        if not hints:
            return {"hints": [], "block": ""}
        body = "\n".join(hints)
        block = (
            "Context — read these first, in this order:\n\n"
            f"```bash\n{body}\n```\n"
        )
        return {"hints": hints, "block": block}

    @verb(role="effect")
    def fan_out(self, driver: str, driver_verb: str, items: list, quota: int = 8) -> dict:
        """Open one child Lifecycle per item (capped at `quota`), dispatch the driver
        for each, and record a Delegation that DELEGATES_TO every child. Children
        start `working` (dispatched ≠ done)."""
        if quota < 0:                                          # negative slicing would over-admit
            return {"result": {"error": "quota must be >= 0", "quota": quota}}
        nonmap = [it for it in items if not isinstance(it, dict)]
        if nonmap:                                             # each item is unpacked as driver kwargs
            return {"result": {"error": "every item must be a mapping of driver kwargs",
                               "offending": nonmap[:3]}}
        admitted = items[:quota]
        d = self.ctx.record("Delegation", {"driver": driver, "driver_verb": driver_verb,
                                            "count": len(admitted), "quota": quota})
        self.ctx.link(d, self.ctx.intent_id, "SERVES")
        aid = f"agent:{driver}"
        if self.ctx.recall(aid) is None:
            self.ctx.record("Agent", {"runtime": "delegated"}, node_id=aid)
        children = []
        for item in admitted:
            lc = self.ctx.record("Lifecycle", {"state": "working", "phase": 0})
            self.ctx.link(lc, self.ctx.intent_id, "SERVES")
            self.ctx.link(lc, aid, "DISPATCHED_TO")        # an agent IS a Lifecycle parameterization
            self.ctx.link(d, lc, "DELEGATES_TO")
            result, inv = self.ctx.spawn(driver, driver_verb, **item)
            self.ctx.link(lc, inv, "DRIVES")               # the child Lifecycle drives its dispatch
            children.append({"lifecycle": lc, "result": result})
        return {"result": {"delegation": d, "dispatched": len(admitted),
                           "skipped": len(items) - len(admitted), "children": children}}

    @verb(role="act")
    def join(self, delegation: str) -> dict:
        """Reduce a delegation over its children's Lifecycle state (dispatched ≠
        done): tally states, record a REDUCES_INTO reduction. `done` only when every
        child Lifecycle is `completed`. Writes a reduction, so it is an `act`, not a
        pure read."""
        if not self.ctx.memory.g.query(                        # no cross-intent reductions
                "MATCH (d:Delegation)-[:SERVES]->(i:Intent) WHERE d.id = $d AND i.id = $i RETURN i",
                {"d": delegation, "i": self.ctx.intent_id}):
            return {"result": {"error": "delegation does not serve the current intent",
                               "delegation": delegation}}
        rows = self.ctx.memory.g.query(
            "MATCH (d:Delegation)-[:DELEGATES_TO]->(lc:Lifecycle) WHERE d.id = $id RETURN lc",
            {"id": delegation})
        states: dict[str, int] = {}
        for r in rows:
            s = r["lc"]["properties"].get("state", "?")
            states[s] = states.get(s, 0) + 1
        children = len(rows)
        done = children > 0 and states.get("completed", 0) == children
        red = self.ctx.record("Artefact", {"kind": "reduction", "children": children})
        self.ctx.link(delegation, red, "REDUCES_INTO")
        self.ctx.link(red, self.ctx.intent_id, "SERVES")
        return {"result": {"children": children, "states": states, "done": done, "reduction": red}}
