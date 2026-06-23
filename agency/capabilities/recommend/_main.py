# agency-scaffold: v1
"""recommend — request → capability routing, first-class (Spec 298).

A native reimplementation of SuperClaude's `sc-recommend`: given a free-text
request, recommend the most suitable agency capability + verb to use. Reads the
LIVE registry (capabilities · verbs · skills) — a core agency feature — and
scores by decidable token overlap. Distinct from `search` (keyword tool lookup):
this routes an intent to a recommended call with a rationale.

Use when: you have a goal in words and want the right agency verb to reach for,
or you are unsure which capability owns a task.
Triggers:
- A free-text request that should map to a capability + verb
- Uncertainty about which agency surface to use for a task
- Routing a user's ask to the most suitable starting verb
Red flags:
- Guessing a verb name from memory → recommend.route(request) first
- Reaching for a raw tool when a capability verb fits → check the recommendation
"""
from __future__ import annotations

import re

from ...capability import ArtefactSchemas, CapabilityBase, verb
from ..._capture import keep_full
from ...ontology import OntologyExtension

_STOP = {"the", "a", "an", "to", "of", "and", "for", "in", "on", "with", "my",
         "this", "that", "it", "is", "i", "we", "do", "how", "can", "please"}


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", text.lower()) if t and t not in _STOP}


# Spec 301 Slice 2 — the walkable discipline (superpowers' signature): frame the
# request, rank the capability surface, select one, confirm behind a hard gate.
# Mirrors the recommend verb flow (route → ranked recommendations).
_CAPABILITY_ROUTING_SKILL = {
    "name": "capability-routing", "kind": "discipline",
    "phases": [
        {"index": 1, "name": "frame", "produces": ["request"],
         "goal": "Frame the request to route.",
         "instructions": "State what the user is trying to do in terms the capability "
                         "registry can match — the underlying need, not their phrasing.",
         "freedom": "medium"},
        {"index": 2, "name": "rank", "produces": ["recommendations"],
         "goal": "Rank the candidate capabilities.",
         "instructions": "Score the live capability surface against the framed request; "
                         "produce a ranked shortlist with why each made it.",
         "freedom": "low"},
        {"index": 3, "name": "select", "produces": ["chosen"],
         "goal": "Select the best-fit capability.",
         "instructions": "Pick the top candidate that actually serves the need; a high "
                         "rank on a wrong-shaped capability still loses.",
         "freedom": "medium"},
        {"index": 4, "name": "confirm", "produces": ["rationale"], "gate": "hard",
         "goal": "Confirm the route with its rationale.",
         "instructions": "State why this capability beats the alternatives for THIS "
                         "request. Confirm only with a grounded rationale.",
         "freedom": "low"},
    ],
}


class RecommendCapability(CapabilityBase):
    name = "recommend"
    home = "capability"   # reads the registry to route a request
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = OntologyExtension(
        nodes={"Recommendation": ["request", "capability"]},
        skills={"capability-routing": _CAPABILITY_ROUTING_SKILL},
    )

    def _usage_counts(self) -> dict:
        """Per-capability invocation frequency from the provenance graph (Spec
        298 follow-up) — how often each capability has actually been used. A
        live signal read from the Invocation nodes, not a static weight."""
        counts: dict = {}
        for inv in self.ctx.find("Invocation"):
            cap = inv.get("capability")
            if cap:
                counts[cap] = counts.get(cap, 0) + 1
        return counts

    def _vocab(self) -> dict:
        """Per-capability token vocabulary from names + verbs + skills + gist."""
        vocab = {}
        for cap_name in self.ctx.registry.names():
            cap = self.ctx.registry.get(cap_name)
            toks = set(_tokens(cap_name))
            verbs = getattr(cap, "verbs", {}) or {}
            for vn in verbs:
                toks |= _tokens(vn)
            skills = getattr(getattr(cap, "ontology", None), "skills", {}) or {}
            for sk in skills:
                toks |= _tokens(str(sk))
            gist = ""
            sd = getattr(cap, "skill_doc", None)
            if sd is not None:
                gist = (getattr(sd, "overview", "") or "")
                toks |= _tokens(gist)
            vocab[cap_name] = {"tokens": toks, "verbs": sorted(verbs), "gist": gist}
        return vocab

    @verb(role="effect")
    def route(self, request: str, top: int = 5) -> dict:
        """Recommend the capability + verb best matched to a free-text
        ``request`` (Spec 298).

        Scores every live capability by token overlap between the request and
        its (name + verbs + skills + gist) vocabulary; suggests the verb whose
        own name best matches; records a ``Recommendation`` node SERVING the
        intent.

        Scored capabilities are ranked by relevance first, then by graph usage
        frequency (the follow-up signal): among equally-relevant capabilities,
        the more-used one wins — the live provenance graph breaks ties.

        Inputs: request (str — what you want to do), top (int — how many).
        Returns: ``{request, top, recommendations: [{capability, verb, score,
                   usage, why}]}``.
        chain_next: call the recommended ``capability.verb`` via execute.
        """
        req = _tokens(request)
        vocab = self._vocab()
        usage = self._usage_counts()
        scored = []
        for cap_name, v in vocab.items():
            overlap = req & v["tokens"]
            if not overlap:
                continue
            # suggested verb: the one whose name shares the most request tokens.
            best_verb, best_n = (v["verbs"][0] if v["verbs"] else ""), -1
            for vn in v["verbs"]:
                n = len(req & _tokens(vn))
                if n > best_n:
                    best_verb, best_n = vn, n
            why = (v["gist"].split(".")[0] or cap_name)[:100]
            scored.append({"capability": cap_name, "verb": best_verb,
                           "score": len(overlap), "usage": usage.get(cap_name, 0),
                           "why": why, "_matched": sorted(overlap)})
        # relevance is primary; graph usage frequency breaks ties (Spec 298 f/u).
        scored.sort(key=lambda r: (-r["score"], -r["usage"], r["capability"]))
        scored = scored[:top]
        top_cap = scored[0]["capability"] if scored else ""
        if top_cap:
            self.ctx.record_and_serve("Recommendation",
                                      {"request": keep_full(request, label="recommend request"), "capability": top_cap})
        return {"request": request, "top": top_cap, "recommendations": scored}
