"""novel.character_knowledge — Character-knowledge cluster — knowledge ledger + anachronism audit + provenance (Spec 131).

Spec 286 P3 — extracted verbatim from ``novel/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single NovelCapability.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult, Codes


class CharacterKnowledgeMixin:
    """Character-knowledge cluster — knowledge ledger + anachronism audit + provenance (Spec 131)."""

    @verb(role="effect")
    def record_character_learns(self, character_id: str, fact: str,
                                  scene_id: str) -> ToolResult:
        """Mint a KnownFact + KNOWS + LEARNED_IN edges (effect).

        Inputs: character_id (any node id — Character ontology lands in
                Spec 123 Slice 2; for now any id works), fact (freeform),
                scene_id (existing Scene).
        Returns: ``{fact_id, character_id, scene_id}``.
        chain_next: ``novel.what_does_X_know_as_of`` to verify.
        """
        if self.ctx.recall(character_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND,
                f"character_id={character_id!r} not found")
        if self.ctx.recall(scene_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene_id={scene_id!r} not found")
        fid = self.ctx.record("KnownFact", {
            "character": character_id, "fact": fact,
        })
        self.ctx.link(character_id, fid, "KNOWS")
        self.ctx.link(fid, scene_id, "LEARNED_IN")
        self.ctx.link(fid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "fact_id": fid, "character_id": character_id,
            "scene_id": scene_id,
        })

    @verb(role="transform")
    def what_does_X_know_as_of(self, character_id: str,
                                  scene_id: str) -> ToolResult:
        """List facts the character has learned ≤ the scene's narrative position (transform).

        Narrative-position is approximated by the chapter number of the
        LEARNED_IN scene vs the target scene. When chapter numbers tie,
        scene-creation order within the chapter is the tie-breaker.

        Inputs: character_id, scene_id.
        Returns: ``{facts: [{fact_id, fact, learned_in_scene}]}``.
        chain_next: feed into ``prompt.assemble_scene_brief``'s pov_card.
        """
        target = self.ctx.recall(scene_id)
        if target is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene_id={scene_id!r} not found")
        target_chapter = (self.ctx.recall(target.get("chapter", "")) or {}
                          ).get("number", 0)
        # Walk KNOWS to get the character's facts.
        facts: list[dict] = []
        for f in self.ctx.neighbors(character_id, "KNOWS", direction="out"):
            # LEARNED_IN scene of this fact.
            learned = self.ctx.neighbors(f.get("id", ""), "LEARNED_IN",
                                           direction="out")
            if not learned:
                continue
            ls = learned[0]
            l_chapter = (self.ctx.recall(ls.get("chapter", "")) or {}
                         ).get("number", 0)
            if l_chapter <= target_chapter:
                facts.append({
                    "fact_id": f.get("id"),
                    "fact": f.get("fact"),
                    "learned_in_scene": ls.get("id"),
                })
        return ToolResult.success(data={"facts": facts})

    @verb(role="transform")
    def flag_anachronistic_reference(self, scene_id: str,
                                       character_id: str,
                                       fact_text: str) -> ToolResult:
        """Check if the character knows the fact yet (transform).

        Walks the character's KNOWS to find a matching fact; if found,
        compares LEARNED_IN scene's chapter number to the target scene's.
        When LEARNED_IN's chapter > target's chapter → anachronism (the
        character references something they haven't learned yet).

        Inputs: scene_id (the scene that references the fact),
                character_id, fact_text (the fact body to match).
        Returns: ``{anachronism, expected_learned_in?, no_record?}``.
        chain_next: revise the scene OR add a `record_character_learns`
                    earlier in the manuscript.
        """
        target = self.ctx.recall(scene_id)
        if target is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene_id={scene_id!r} not found")
        target_chapter_node = self.ctx.recall(target.get("chapter", ""))
        target_chapter = (target_chapter_node or {}).get("number", 0)
        target_title = (target_chapter_node or {}).get("title", "")
        # Find a KnownFact for this character whose body matches.
        for f in self.ctx.neighbors(character_id, "KNOWS", direction="out"):
            if (f.get("fact") or "").strip() != fact_text.strip():
                continue
            learned = self.ctx.neighbors(f.get("id", ""), "LEARNED_IN",
                                           direction="out")
            if not learned:
                continue
            ls = learned[0]
            l_chapter_node = self.ctx.recall(ls.get("chapter", ""))
            l_chapter = (l_chapter_node or {}).get("number", 0)
            l_title = (l_chapter_node or {}).get("title", "")
            anachronism = l_chapter > target_chapter
            return ToolResult.success(data={
                "anachronism": anachronism,
                "expected_learned_in": (f"Ch {l_chapter}: {l_title}"
                                          if l_title else
                                          f"scene {ls.get('id', '?')}"),
            })
        # No record of this character ever learning the fact.
        return ToolResult.success(data={
            "anachronism": False, "no_record": True,
        })

    @verb(role="transform")
    def audit_novel_provenance(self, novel_id: str) -> ToolResult:
        """Aggregate the provenance graph census for the serving intent (transform, xcap to analyze).

        Routes through ``analyze.graph`` to surface a node-type census
        + verb summary. The audit catches which cluster caps have
        SERVED the novel's intent across the session.

        Inputs: novel_id (validated for NOT_FOUND only).
        Returns: ``{novel_id, census, capabilities}``.
        chain_next: revise the storyform per surfaced gaps.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        # analyze.graph returns a census + typed listing for the current intent.
        result = self.ctx.call("analyze", "graph",
                                node_type="Invocation", limit=200)
        census = (result or {}).get("census") or {}
        nodes = (result or {}).get("nodes") or []
        caps = sorted({n.get("capability", "") for n in nodes
                       if n.get("capability")})
        return ToolResult.success(data={
            "novel_id": novel_id,
            "census": census,
            "capabilities": caps,
        })
