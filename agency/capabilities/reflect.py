"""reflect — durable, scope-tagged cross-session memory.

The reference migration to the class form: a `CapabilityBase` subclass whose
verb-methods reach the graph through `self.ctx`. It OWNS its ontology fragment (a
`Reflection` node type + a closed `scope` enum + the `OBSERVED_DURING` edge), and
demonstrates that adding a capability is adding a file. The functional
`Capability` form remains equally valid for other capabilities.
"""
from __future__ import annotations

from ..capability import CapabilityBase, verb
from ..ontology import OntologyExtension

REFLECT_SCOPES = {"observation", "reflection", "project", "technical", "user", "world"}


class ReflectCapability(CapabilityBase):
    name = "reflect"
    home = "memory"
    ontology = OntologyExtension(
        nodes={"Reflection": ["scope", "text"]},
        enums={("Reflection", "scope"): REFLECT_SCOPES},
        edges={"OBSERVED_DURING", "INFORMS"},
    )

    @verb(role="act")
    def note(self, scope: str, text: str) -> dict:
        "Write a scope-tagged insight node; edged OBSERVED_DURING + SERVES the intent."
        rid = self.ctx.record("Reflection", {"scope": scope, "text": text})
        self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        self.ctx.link(rid, self.ctx.intent_id, "SERVES")     # so the note surfaces in provenance
        return {"result": rid}

    @verb(role="act")
    def batch_note(self, scope: str, texts: list) -> dict:
        """Bulk version of ``note``: one Reflection node per text. Returns
        ``{ids, count}``. Closes the gap that made ``jules-self-improvement``
        only fold the first observation per walk — a real loop ingests N
        observations from ``dogfood.collect`` in one Phase-2 invocation."""
        ids: list[str] = []
        for t in texts or []:
            if not t:
                continue
            rid = self.ctx.record("Reflection", {"scope": scope, "text": t})
            self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
            self.ctx.link(rid, self.ctx.intent_id, "SERVES")
            ids.append(rid)
        return {"ids": ids, "count": len(ids)}

    @verb(role="transform")
    def recall(self, scope: str = "") -> dict:
        "Retrieve reflections, newest first, optionally filtered by scope."
        rows = sorted(self.ctx.find("Reflection"), key=lambda p: p["vfrom"], reverse=True)
        out = [{"scope": r["scope"], "text": r["text"]}
               for r in rows if not scope or r.get("scope") == scope]
        return {"result": out}

    @verb(role="transform")
    def search(self, query: str) -> dict:
        "Keyword search over reflection text (deterministic substring match)."
        q = (query or "").lower()
        out = [{"scope": r["scope"], "text": r["text"]}
               for r in self.ctx.find("Reflection") if q in r["text"].lower()]
        return {"result": out}
