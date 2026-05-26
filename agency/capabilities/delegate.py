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


class DelegateCapability(CapabilityBase):
    name = "delegate"
    home = "lifecycle"
    ontology = OntologyExtension(
        nodes={"Delegation": ["driver", "driver_verb", "count", "quota"]},
        edges={"DELEGATES_TO", "REDUCES_INTO"},
    )

    @verb(role="effect")
    def fan_out(self, driver: str, driver_verb: str, items: list, quota: int = 8) -> dict:
        """Open one child Lifecycle per item (capped at `quota`), dispatch the driver
        for each, and record a Delegation that DELEGATES_TO every child. Children
        start `working` (dispatched ≠ done)."""
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

    @verb(role="transform")
    def join(self, delegation: str) -> dict:
        """Reduce a delegation over its children's Lifecycle state (dispatched ≠
        done): tally states, record a REDUCES_INTO reduction. `done` only when every
        child Lifecycle is `completed`."""
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
