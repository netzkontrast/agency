# agency-scaffold: v1
"""reflect — durable, scope-tagged cross-session memory.

Reflect is the cross-session memory surface: scope-tagged notes recorded as graph nodes, recalled by scope or by semantic similarity against prior observations.

Use when: durable, scope-tagged memory must cross sessions — recording an insight, or recalling prior observations by scope or semantic similarity.
Triggers:
- A lesson that should outlive the current session
- A question whose answer may live in prior reflections
- Repeated rediscovery of something already learned
Red flags:
- Re-learning a past lesson → search prior notes via capability_reflect_recall_semantic
- Letting an insight evaporate at session end → capability_reflect_note it
"""
from __future__ import annotations

from ...capability import (
    ArtefactSchemas, CapabilityBase, RenderTemplates, verb,
)
from ...ontology import OntologyExtension

REFLECT_SCOPES = {"observation", "reflection", "project", "technical", "user", "world"}




class ReflectCapability(CapabilityBase):
    name = "reflect"
    home = "memory"
    render_templates = RenderTemplates.from_module(__file__)
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = OntologyExtension(
        nodes={"Reflection": ["scope", "text"]},
        enums={("Reflection", "scope"): REFLECT_SCOPES},
        edges={"OBSERVED_DURING", "INFORMS"},
        # Spec 114 — session synthesis artefact schema (the closing
        # deliverable of every session-driver-pass).
        schemas={"session-reflection": ["session_lifecycle_id",
                                          "lessons",
                                          "open_questions"]},
    )

    @verb(role="act")
    def note(self, scope: str, text: str) -> dict:
        """Write a scope-tagged insight node; edged OBSERVED_DURING + SERVES the intent.

        Inputs: scope (one of observation/project/reflection/technical/user/world),
                text (str — the insight body).
        Returns: ``{result: <reflection_id>}``.
        chain_next: ``reflect.recall(scope=)`` or ``reflect.search(query=)``
                    to surface what was written.
        """
        rid = self.ctx.record("Reflection", {"scope": scope, "text": text})
        self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        self.ctx.link(rid, self.ctx.intent_id, "SERVES")     # so the note surfaces in provenance
        return {"result": rid}

    @verb(role="act")
    def batch_note(self, scope: str, texts: list) -> dict:
        """Bulk version of ``note``: one Reflection node per text.

        Inputs: scope (one of observation/project/reflection/technical/user/world),
                texts (list[str] — one Reflection per non-empty entry).
        Returns: ``{ids, count}``.
        chain_next: ``reflect.recall(scope=)`` for surfacing the batch.

        Closes the gap that made ``jules-self-improvement`` only fold the
        first observation per walk — a real loop ingests N observations
        from ``dogfood.collect`` in one Phase-2 invocation.
        """
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
        """Retrieve reflections, newest first, optionally filtered by scope.

        Inputs: scope (str — optional filter; empty returns all).
        Returns: ``{result: [{scope, text}, …]}`` newest-first.
        chain_next: terminal — caller renders/aggregates the list.
        """
        rows = sorted(self.ctx.find("Reflection"), key=lambda p: p["vfrom"], reverse=True)
        out = [{"scope": r["scope"], "text": r["text"]}
               for r in rows if not scope or r.get("scope") == scope]
        return {"result": out}

    @verb(role="transform")
    def search(self, query: str) -> dict:
        """Keyword search over reflection text (deterministic substring match).

        Inputs: query (str — case-insensitive substring).
        Returns: ``{result: [{scope, text}, …]}``.
        chain_next: ``reflect.recall_semantic`` for semantic ranking when
                    a stronger backend is wired.
        """
        q = (query or "").lower()
        out = [{"scope": r["scope"], "text": r["text"]}
               for r in self.ctx.find("Reflection") if q in r["text"].lower()]
        return {"result": out}

    @verb(role="transform", inject=["embedder"])
    def recall_semantic(self, embedder, query: str, k: int = 5,
                        scope: str = "") -> dict:
        """Semantic top-k recall over Reflection nodes; backend-injectable.

        Inputs: query (str — free text; empty → empty results),
                k (int — max results), scope (str — optional post-rank filter).
        Returns: ``{results: [{id, score, scope, text, vfrom}], embedder}``.
                 ``text`` truncated to 200 chars (Spec 023 budget); call
                 ``recall``/``search`` for full text. ``embedder`` names the
                 live backend so callers confirm which ran.
        chain_next: ``reflect.recall(scope=)`` for full text on a top match.
        """
        rows = list(self.ctx.find("Reflection"))
        if not rows or not (query or "").strip() or k <= 0:
            return {"results": [], "embedder": embedder.name}
        corpus = [r["text"] for r in rows]
        indexed = embedder.index(corpus)
        scores = embedder.score(query, indexed)
        # Sort by score desc without copying each row dict; the row stays
        # by reference and is only projected at result-shaping time.
        paired = sorted(zip(scores, rows), key=lambda p: p[0], reverse=True)
        # Drop non-positive scores — TF-IDF on an out-of-vocab query
        # returns 0.0 for every row, and slicing the top-k would
        # surface arbitrary Reflections as "matches" (Reviewer
        # finding: research.specialist then records zero-confidence
        # citations against unrelated memories).
        paired = [(s, r) for s, r in paired if float(s) > 0.0]
        if scope:
            paired = [(s, r) for s, r in paired if r.get("scope") == scope]
        out = [{
            "id": r["id"],
            "score": round(float(s), 4),
            "scope": r["scope"],
            "text": r["text"][:200],
            "vfrom": r["vfrom"],
        } for s, r in paired[:k]]
        return {"results": out, "embedder": embedder.name}

    # ════════════════════════════════════════════════════════════════════════
    # Spec 114 — session-end synthesis: closes the session-driver-pass.
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="act")
    def synthesize_session(self, session_lifecycle_id: str,
                            lessons: str = "",
                            open_questions: str = "",
                            handoff_notes: str = "") -> dict:
        """Produce a session-reflection artefact at session close (act).

        Flips the SessionLifecycle to ``archived`` + records a
        ``session-reflection`` artefact PRODUCES'd against the intent. Also
        writes a ``Reflection{scope:'reflection'}`` for the synthesis-style
        notes so they surface in future-session search.

        Inputs: session_lifecycle_id, lessons (multi-line), open_questions
                (multi-line), handoff_notes (next-session continuity).
        Returns: ``{result, artefact}`` session-reflection artefact.
        chain_next: terminal — agent closes the session.
        """
        body = (f"# Session reflection\n\n"
                f"Lifecycle: {session_lifecycle_id}\n\n"
                f"## Lessons\n{lessons}\n\n"
                f"## Open questions\n{open_questions}\n\n"
                f"## Handoff notes\n{handoff_notes}\n")
        # Also record the lessons as a regular Reflection so they surface in
        # future-session search (this is the cross-session knowledge channel).
        if lessons.strip():
            rid = self.ctx.record("Reflection", {
                "scope": "reflection",
                "text": f"Session {session_lifecycle_id}: {lessons.strip()}",
            })
            self.ctx.link(rid, self.ctx.intent_id, "SERVES")
            self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        # Archive the SessionLifecycle if it exists
        node = self.ctx.recall(session_lifecycle_id)
        if node is not None:
            self.ctx.update(session_lifecycle_id, {"status": "archived"})
        return {"result": body, "artefact": {
            "kind": "session-reflection",
            "session_lifecycle_id": session_lifecycle_id,
            "lessons": lessons,
            "open_questions": open_questions,
            "body": body,
        }}
