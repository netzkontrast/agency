# agency-scaffold: v1
"""novel — minimum-viable-novel Slice 1 (Spec 101 master First-Principles Minimum).

Five-verb path from premise to manuscript: conceptualize → create_novel → create_chapter → chapter_report → render_manuscript, plus the novel-concept gated planning skill.

Use when: authoring a novel — turning a premise into a structured manuscript through gated concept → chapters → report → render.
Triggers:
- A novel premise needs structured planning before drafting
- A chapter needs a per-chapter report (word count, beat progress)
- A finished draft needs rendering to manuscript format
Red flags:
- Hand-rolling chapter files outside the capability → call `novel.create_chapter`
- Skipping the conceptualizer's hard gate → walk `novel-concept`
"""
from __future__ import annotations

from agency.capability import CapabilityBase, RenderTemplates, verb
from agency.ontology import OntologyExtension
from agency.toolresult import ToolResult


# ─────────────────────────── enums ───────────────────────────
NOVEL_STATUS = {"concept", "outlining", "drafting", "revising",
                "beta", "querying", "published"}
CHAPTER_STATUS = {"outlined", "drafted", "revised", "final"}
# Spec 102 — Idea lifecycle (mirrors music's IDEA_STATUS).
IDEA_STATUS = {"new", "promoted", "dropped"}


# ─────────────────────────── walkable skill ───────────────────────────
# Spec 102 §"novel-concept walkable skill (10 phases)" — extends the
# 5-phase Slice 1 skeleton with genre/audience/setting/characters-core/
# dramatica-seed/outline-shape/series-hypothesis blocks. The dramatica-seed
# phase populates the 4 dynamics that Spec 103's storyform cluster consumes.
NOVEL_CONCEPT_SKILL = {
    "name": "novel-concept", "kind": "conceptualizer",
    "phases": [
        {"index": 1, "name": "premise",
         "produces": ["logline", "central_question"]},
        {"index": 2, "name": "genre",
         "produces": ["genre", "subgenre", "tone"]},
        {"index": 3, "name": "audience",
         "produces": ["target_reader", "comp_titles"]},
        {"index": 4, "name": "pov",
         "produces": ["pov_choice", "narrator_voice"]},
        {"index": 5, "name": "setting",
         "produces": ["world", "time_period", "geography"]},
        {"index": 6, "name": "characters-core",
         "produces": ["protagonist_seed", "antagonist_seed",
                      "supporting_seeds"]},
        {"index": 7, "name": "dramatica-seed",
         "produces": ["resolve_intent", "growth_intent",
                      "approach_intent", "mental_sex_intent"]},
        {"index": 8, "name": "outline-shape",
         "produces": ["act_structure", "midpoint_intent",
                      "ending_intent"]},
        {"index": 9, "name": "series-hypothesis",
         "produces": ["standalone_or_series", "series_arc"]},
        {"index": 10, "name": "confirmation",
         "produces": ["user_confirmed"], "gate": "hard"},
    ],
}


# ─────────────────────────── ontology ───────────────────────────
novel_ontology = OntologyExtension(
    nodes={
        # Lifecycle (Slice 1 minimum — extended in 102/103/...)
        "Novel":   ["title", "author", "status"],
        "Chapter": ["novel", "number", "title", "status"],
        # Spec 102 — pre-novel idea capture (mirrors music's Idea node:
        # schema is text-only, `status` carried as an optional field
        # constrained by the IDEA_STATUS enum below — same shape music uses).
        "Idea":    ["text"],
    },
    enums={
        ("Novel",   "status"): NOVEL_STATUS,
        ("Chapter", "status"): CHAPTER_STATUS,
        ("Idea",    "status"): IDEA_STATUS,
    },
    edges={
        "CHAPTER_OF",       # Chapter → Novel (mirror of music's RECORDED_FOR)
        "PROMOTED_TO",      # Idea → Novel (mirror of music's PROMOTED_TO)
    },
    skills={"novel-concept": NOVEL_CONCEPT_SKILL},
    schemas={
        # Spec 102: logline replaces `premise` in the canonical phase name;
        # both verb args + skill produce the same field set.
        "novel-concept": ["title", "logline", "central_question"],
        "chapter-report": ["novel_id", "chapter_count", "word_count_total"],
        "manuscript":     ["novel", "body", "chapter_count"],
    },
)


class NovelCapability(CapabilityBase):
    name = "novel"
    home = "capability"
    ontology = novel_ontology
    render_templates = RenderTemplates.from_module(__file__)

    def _require_novel(self, novel_id: str) -> tuple[dict | None, ToolResult | None]:
        """NOT_FOUND guard shared by every verb taking a novel_id.

        Returns ``(node, fail)``: when the novel exists, ``node`` is the
        graph payload and ``fail`` is ``None``; when missing, ``node`` is
        ``None`` and ``fail`` is a typed ToolResult.failure the caller
        forwards.

        One source of truth for the NOT_FOUND message — keeps the error
        string drift-free across create_chapter, chapter_report, and
        render_manuscript (which previously held a hand-rolled copy).
        """
        node = self.ctx.recall(novel_id)
        if node is None:
            return None, ToolResult.failure(
                "NOT_FOUND", f"novel_id={novel_id!r} not found")
        return node, None

    @verb(role="act")
    def conceptualize(self, title: str, author: str,
                       premise: str = "",
                       central_question: str = "") -> ToolResult:
        """Render a novel-concept document (act); the first verb of the MVN flow.

        Inputs: title, author, premise, central_question.
        Returns: ``{result, artefact}`` novel-concept artefact.
        chain_next: ``novel.create_novel`` to mint the Novel node.
        """
        body = (f"# {title}\n\n**Author:** {author}\n\n"
                f"## Premise\n{premise}\n\n"
                f"## Central question\n{central_question}\n")
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "novel-concept",
                         "title": title, "premise": premise,
                         "central_question": central_question,
                         "body": body},
        })

    @verb(role="effect")
    def create_novel(self, title: str, author: str) -> ToolResult:
        """Record a Novel node SERVING the intent (effect).

        Inputs: title, author.
        Returns: ``{novel_id, title, status}``.
        chain_next: ``novel.create_chapter`` once outline is ready.
        """
        nid = self.ctx.record("Novel", {
            "title": title, "author": author, "status": "concept",
        })
        self.ctx.link(nid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "novel_id": nid, "title": title, "status": "concept",
        })

    @verb(role="effect")
    def create_chapter(self, novel_id: str, number: int,
                        title: str, body: str = "") -> ToolResult:
        """Record a Chapter graph node + CHAPTER_OF the parent Novel (effect).

        Inputs: novel_id, number (1-indexed), title, body (optional draft body).
        Returns: ``{chapter_id, novel_id, number, title, status}``.
        chain_next: ``novel.chapter_report`` to aggregate state.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        cid = self.ctx.record("Chapter", {
            "novel": novel_id, "number": number, "title": title,
            "status": "outlined", "body": body,
        })
        self.ctx.link(cid, novel_id, "CHAPTER_OF")
        self.ctx.link(cid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "chapter_id": cid, "novel_id": novel_id,
            "number": number, "title": title, "status": "outlined",
        })

    @verb(role="transform")
    def chapter_report(self, novel_id: str) -> ToolResult:
        """Read-only aggregate over the novel's chapters (transform).

        Inputs: novel_id.
        Returns: ``{novel_id, chapter_count, word_count_total, by_status}``.
        chain_next: revise chapters then ``novel.render_manuscript``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        # Find chapters of this novel
        chapters = [c for c in self.ctx.find("Chapter")
                    if c.get("novel") == novel_id]
        word_count = sum(len((c.get("body") or "").split())
                         for c in chapters)
        by_status: dict[str, int] = {}
        for c in chapters:
            s = c.get("status", "outlined")
            by_status[s] = by_status.get(s, 0) + 1
        return ToolResult.success(data={
            "novel_id": novel_id,
            "chapter_count": len(chapters),
            "word_count_total": word_count,
            "by_status": by_status,
        })

    @verb(role="act")
    def render_manuscript(self, novel_id: str) -> ToolResult:
        """Concatenate chapters into a manuscript artefact (act).

        Inputs: novel_id.
        Returns: ``{result, artefact}`` manuscript artefact with the assembled body.
        chain_next: terminal — deliver to the publishing path.
        """
        novel_node, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(
            [c for c in self.ctx.find("Chapter")
             if c.get("novel") == novel_id],
            key=lambda c: c.get("number", 0))
        title = novel_node.get("title", "Untitled")
        author = novel_node.get("author", "")
        parts = [f"# {title}\n", f"by {author}\n\n"]
        for c in chapters:
            parts.append(
                f"\n## Chapter {c.get('number', 0)}: {c.get('title', '')}\n\n"
                f"{c.get('body', '')}\n")
        body = "".join(parts)
        return ToolResult.success(data={
            "result": body,
            "artefact": {"kind": "manuscript",
                         "novel": novel_id,
                         "chapter_count": len(chapters),
                         "body": body},
        })

    # ───────────────── Spec 102 — lifecycle delta ─────────────────
    # Idea capture/promotion + novel discovery/status flip. Graph-only
    # for Slice 1; StateDriver (disk-layer) lands in a Spec-115-equivalent
    # follow-up matching music's production-binding split.

    @verb(role="effect")
    def capture_idea(self, text: str) -> ToolResult:
        """Record an Idea node SERVING the intent (effect).

        Pre-novel capture surface: free-text premise jotted before the
        gated conceptualizer runs. Default status ``new``.

        Inputs: text.
        Returns: ``{idea_id, text, status}``.
        chain_next: ``novel.promote_idea`` once the premise hardens.
        """
        iid = self.ctx.record("Idea", {"text": text, "status": "new"})
        self.ctx.link(iid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "idea_id": iid, "text": text, "status": "new",
        })

    @verb(role="transform")
    def list_ideas(self, status: str = "") -> ToolResult:
        """List captured ideas; optional status filter (transform).

        Inputs: status (one of ``IDEA_STATUS`` or ``""`` for all).
        Returns: ``{ideas: [...], count}``.
        chain_next: ``novel.promote_idea`` for any "new" idea ready to ship.
        """
        if status and status not in IDEA_STATUS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"status={status!r} not in {sorted(IDEA_STATUS)}")
        ideas = [i for i in self.ctx.find("Idea")
                 if not status or i.get("status") == status]
        return ToolResult.success(data={"ideas": ideas, "count": len(ideas)})

    @verb(role="effect")
    def promote_idea(self, idea_id: str, title: str,
                      author: str) -> ToolResult:
        """Idea → Novel transition; records PROMOTED_TO edge (effect).

        Flips the Idea's status to ``promoted``, mints a Novel node, and
        wires a PROMOTED_TO edge. Mirrors music's promote_idea / Idea-to-
        Album lineage.

        Inputs: idea_id, title, author.
        Returns: ``{idea_id, novel_id, title, status}``.
        chain_next: ``novel.create_chapter`` to start outlining.
        """
        node = self.ctx.recall(idea_id)
        if node is None:
            return ToolResult.failure(
                "NOT_FOUND", f"idea_id={idea_id!r} not found")
        nid = self.ctx.record("Novel", {
            "title": title, "author": author, "status": "concept",
        })
        self.ctx.link(nid, self.ctx.intent_id, "SERVES")
        self.ctx.link(idea_id, nid, "PROMOTED_TO")
        self.ctx.update(idea_id, {"status": "promoted"})
        return ToolResult.success(data={
            "idea_id": idea_id, "novel_id": nid,
            "title": title, "status": "concept",
        })

    @verb(role="transform")
    def find_novel(self, query: str = "") -> ToolResult:
        """Substring-match novel titles (transform, driver-free).

        Inputs: query (case-insensitive substring; ``""`` returns all).
        Returns: ``{novels: [{novel_id, title, author, status}], count}``.
        chain_next: ``novel.set_novel_status`` or ``novel.render_manuscript``.
        """
        q = query.lower()
        hits = []
        for n in self.ctx.find("Novel"):
            title = (n.get("title") or "").lower()
            if not q or q in title:
                hits.append({
                    "novel_id": n.get("id"),
                    "title": n.get("title"),
                    "author": n.get("author"),
                    "status": n.get("status"),
                })
        return ToolResult.success(data={"novels": hits, "count": len(hits)})

    @verb(role="effect")
    def set_novel_status(self, novel_id: str, status: str) -> ToolResult:
        """Flip a Novel's lifecycle status; enum-checked (effect).

        Inputs: novel_id, status (one of ``NOVEL_STATUS``).
        Returns: ``{novel_id, status}``.
        chain_next: continue per the new lifecycle phase.
        """
        if status not in NOVEL_STATUS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"status={status!r} not in {sorted(NOVEL_STATUS)}")
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        self.ctx.update(novel_id, {"status": status})
        return ToolResult.success(data={
            "novel_id": novel_id, "status": status,
        })
