"""delegate — agent orchestration: fan-out + quota + join.

The keystone primitive the capability roadmap flagged. An agent is a Lifecycle
parameterization; `jules` is one *driver* (a single remote async worker).
`delegate` generalizes it: fan a task out across N children (each child is an
invocation of a driver capability/verb), capped by a quota, then join on the
results. Built entirely on `ctx.spawn` — so every child is a recorded Invocation
that SERVES the intent, and the delegation is a connected provenance subgraph.

`jules` is the first driver: `fan_out(capability="jules", verb="dispatch", items=…)`
spawns one remote session per item. Any capability/verb can be the driver.
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
        """Fan a task out across children: invoke the driver capability/verb once
        per item (capped at `quota`), each a child Invocation SERVING the intent;
        record a Delegation node with a DELEGATES_TO edge to every child."""
        admitted = items[:quota]
        d = self.ctx.record("Delegation", {"driver": driver, "driver_verb": driver_verb,
                                            "count": len(admitted), "quota": quota})
        self.ctx.link(d, self.ctx.intent_id, "SERVES")
        children = []
        for item in admitted:
            result, inv = self.ctx.spawn(driver, driver_verb, **item)
            self.ctx.link(d, inv, "DELEGATES_TO")
            children.append(result)
        return {"result": {"delegation": d, "dispatched": len(admitted),
                           "skipped": len(items) - len(admitted), "children": children}}

    @verb(role="transform")
    def join(self, delegation: str) -> dict:
        """Join a delegation: gather its children and reduce them into one summary
        artefact (`REDUCES_INTO`). The reduction is itself provenance."""
        rows = self.ctx.memory.g.query(
            "MATCH (d:Delegation)-[:DELEGATES_TO]->(inv) WHERE d.id = $id RETURN inv",
            {"id": delegation})
        children = len(rows)
        red = self.ctx.record("Artefact", {"kind": "reduction", "children": children})
        self.ctx.link(delegation, red, "REDUCES_INTO")
        self.ctx.link(red, self.ctx.intent_id, "SERVES")
        return {"result": {"children": children, "reduction": red}}
