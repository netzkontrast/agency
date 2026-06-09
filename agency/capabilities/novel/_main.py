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


# ─────────────────────────── walkable skill ───────────────────────────
NOVEL_CONCEPT_SKILL = {
    "name": "novel-concept", "kind": "conceptualizer",
    "phases": [
        {"index": 1, "name": "premise",
         "produces": ["premise", "central_question"]},
        {"index": 2, "name": "throughlines",
         "produces": ["main_character", "objective_story",
                       "impact_character", "relationship_story"]},
        {"index": 3, "name": "structure",
         "produces": ["chapter_outline", "act_breakdown"]},
        {"index": 4, "name": "voice",
         "produces": ["pov", "tense", "narrative_distance"]},
        {"index": 5, "name": "confirmation",
         "produces": ["user_confirmed"], "gate": "hard"},
    ],
}


# ─────────────────────────── ontology ───────────────────────────
novel_ontology = OntologyExtension(
    nodes={
        # Lifecycle (Slice 1 minimum — extended in 102/103/...)
        "Novel":   ["title", "author", "status"],
        "Chapter": ["novel", "number", "title", "status"],
    },
    enums={
        ("Novel",   "status"): NOVEL_STATUS,
        ("Chapter", "status"): CHAPTER_STATUS,
    },
    edges={
        "CHAPTER_OF",       # Chapter → Novel (mirror of music's RECORDED_FOR)
    },
    skills={"novel-concept": NOVEL_CONCEPT_SKILL},
    schemas={
        "novel-concept": ["title", "premise", "central_question"],
        "chapter-report": ["novel_id", "chapter_count", "word_count_total"],
        "manuscript":     ["novel", "body", "chapter_count"],
    },
)


class NovelCapability(CapabilityBase):
    name = "novel"
    home = "capability"
    ontology = novel_ontology
    render_templates = RenderTemplates.from_module(__file__)

    def _require_novel(self, novel_id: str) -> ToolResult | None:
        """NOT_FOUND guard for verbs that only need to verify the Novel
        node exists (chapter_report, create_chapter). Returns the
        failure or None on hit. render_manuscript reads the node body so
        keeps the explicit `recall()` binding."""
        if self.ctx.recall(novel_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"novel_id={novel_id!r} not found")
        return None

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
        if (fail := self._require_novel(novel_id)) is not None:
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
        if (fail := self._require_novel(novel_id)) is not None:
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
        novel_node = self.ctx.recall(novel_id)
        if novel_node is None:
            return ToolResult.failure(
                "NOT_FOUND", f"novel_id={novel_id!r} not found")
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
