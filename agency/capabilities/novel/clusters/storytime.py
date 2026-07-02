"""novel.storytime — Story-time / narrative-time cluster — events, reveals, narrative beats (Spec 128).

Spec 286 P3 — extracted verbatim from ``novel/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single NovelCapability.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult, Codes


class StoryTimeMixin:
    """Story-time / narrative-time cluster — events, reveals, narrative beats (Spec 128)."""

    @verb(role="effect")
    def record_story_event(self, novel_id: str, label: str,
                            when_story: str,
                            scene_id: str = "") -> ToolResult:
        """Mint a StoryTimeEvent + optional HAPPENS_AT edge from a scene (effect).

        ``when_story`` is a plain string by design (Open Q1) — the author
        owns sortability. Lexicographic sort is the slice contract for
        ``list_story_events_up_to``.

        Inputs: novel_id, label (short event name), when_story (sortable
                string), scene_id (optional — when supplied, mints
                Scene-HAPPENS_AT->Event edge).
        Returns: ``{event_id, label, when_story, scene_id?}``.
        chain_next: ``novel.reveal_in_scene`` for foreshadow/payoff.
        """
        if self.ctx.recall(novel_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"novel_id={novel_id!r} not found")
        eid = self.ctx.record_and_serve("StoryTimeEvent", {
            "novel": novel_id, "label": label, "when_story": when_story,
        })
        out: dict = {"event_id": eid, "label": label,
                     "when_story": when_story}
        if scene_id:
            if self.ctx.recall(scene_id) is None:
                return ToolResult.failure(
                    Codes.NOT_FOUND, f"scene_id={scene_id!r} not found")
            self.ctx.link(scene_id, eid, "HAPPENS_AT")
            out["scene_id"] = scene_id
        return ToolResult.success(data=out)

    @verb(role="effect")
    def reveal_in_scene(self, event_id: str, scene_id: str) -> ToolResult:
        """Add the REVEALED_IN edge (event disclosed by this scene) (effect).

        Inputs: event_id (existing StoryTimeEvent), scene_id (existing Scene).
        Returns: ``{event_id, scene_id}``.
        chain_next: ``novel.list_reveals_in(scene_id)`` to verify.
        """
        if self.ctx.recall(event_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"event_id={event_id!r} not found")
        if self.ctx.recall(scene_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene_id={scene_id!r} not found")
        self.ctx.link(event_id, scene_id, "REVEALED_IN")
        return ToolResult.success(data={
            "event_id": event_id, "scene_id": scene_id,
        })

    @verb(role="transform")
    def list_story_events_up_to(self, scene_id: str) -> ToolResult:
        """Story-time slice: events with ``when_story`` ≤ this scene's anchor (transform).

        The scene's anchor is the ``when_story`` of any StoryTimeEvent the
        scene HAPPENS_AT. If the scene has multiple, takes the latest. No
        anchor → empty list (the scene has no story-time reference frame
        yet).

        Inputs: scene_id.
        Returns: ``{anchor_when, events: [{event_id, label, when_story}]}``.
        chain_next: ``prompt.assemble_scene_brief`` consumes this for the
                    continuity section.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene_id={scene_id!r} not found")
        anchors = self.ctx.neighbors(scene_id, "HAPPENS_AT", direction="out")
        if not anchors:
            return ToolResult.success(data={
                "anchor_when": None, "events": [],
            })
        anchor_when = max(a.get("when_story", "") for a in anchors)
        novel_id = (self.ctx.recall(scene.get("chapter", "")) or {}
                    ).get("novel", "")
        events = [
            {"event_id": ev.get("id"), "label": ev.get("label"),
             "when_story": ev.get("when_story")}
            for ev in self.ctx.find("StoryTimeEvent")
            if ev.get("novel") == novel_id
            and (ev.get("when_story") or "") <= anchor_when
        ]
        events.sort(key=lambda e: e["when_story"] or "")
        return ToolResult.success(data={
            "anchor_when": anchor_when, "events": events,
        })

    @verb(role="transform")
    def list_reveals_in(self, scene_id: str) -> ToolResult:
        """List events this scene discloses (transform).

        Walks REVEALED_IN edges incoming on the scene (so an Event points
        to a Scene as its reveal point).

        Inputs: scene_id.
        Returns: ``{reveals: [{event_id, label, when_story}]}``.
        chain_next: author's checklist for "is the reveal landing here?".
        """
        if self.ctx.recall(scene_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene_id={scene_id!r} not found")
        reveals = self.ctx.neighbors(scene_id, "REVEALED_IN", direction="in")
        return ToolResult.success(data={
            "reveals": [
                {"event_id": r.get("id"), "label": r.get("label"),
                 "when_story": r.get("when_story")}
                for r in reveals
            ],
        })

    @verb(role="effect")
    def mark_narrative_beat(self, scene_id: str, beat_label: str,
                             predecessor_id: str = "") -> ToolResult:
        """Mint a NarrativeBeat + optional PRECEDES edge from a predecessor (effect).

        Inputs: scene_id, beat_label (e.g. "opening-image" or
                "inciting-incident"), predecessor_id (optional — links the
                new beat into the narrative-order DAG).
        Returns: ``{beat_id, scene_id, label}``.
        chain_next: ``novel.narrative_order(novel_id)`` to read topo-sort.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene_id={scene_id!r} not found")
        # Spec 282 Workstream C — validate ALL preconditions BEFORE any write,
        # so a bad predecessor never leaves an orphan NarrativeBeat node (the
        # create-node-then-fail-edge partial write). The node + its PRECEDES
        # edge land together or not at all.
        if predecessor_id and self.ctx.recall(predecessor_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND,
                f"predecessor_id={predecessor_id!r} not found")
        novel_id = (self.ctx.recall(scene.get("chapter", "")) or {}
                    ).get("novel", "")
        bid = self.ctx.record_and_serve("NarrativeBeat", {
            "novel": novel_id, "label": beat_label, "scene": scene_id,
        })
        if predecessor_id:
            self.ctx.link(predecessor_id, bid, "PRECEDES")
        return ToolResult.success(data={
            "beat_id": bid, "scene_id": scene_id, "label": beat_label,
        })

    # ── Spec 238 — story-time graph queries ─────────────────────────────────

    @verb(role="transform")
    def narrative_order(self, novel_id: str) -> ToolResult:
        """The narrative order DERIVED as a typed path over PRECEDES
        (transform) — a topological order of the beat DAG, never an ad-hoc
        property sort. A PRECEDES cycle is a typed TEMPORAL_CYCLE failure
        naming the trapped node ids.

        Inputs: novel_id.
        Returns: ``{order: [beat_id], beats: [{beat_id, label, scene_id}],
                 edges_traversed}`` — ``order`` is the id path (Spec 238),
                 ``beats`` the enriched Spec-128 reading-order shape.
        chain_next: ``novel.story_time_query`` for the contradiction scan.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        beats = [b for b in self.ctx.find("NarrativeBeat")
                 if b.get("novel") == novel_id]
        ids = {b["id"] for b in beats}
        succ: dict[str, set] = {i: set() for i in ids}
        indeg = {i: 0 for i in ids}
        edges = 0
        for b in beats:
            for nxt in self.ctx.neighbors(b["id"], "PRECEDES",
                                          direction="out"):
                if nxt["id"] in ids:
                    succ[b["id"]].add(nxt["id"])
                    indeg[nxt["id"]] += 1
                    edges += 1
        order: list[str] = []
        frontier = sorted(i for i in ids if indeg[i] == 0)
        while frontier:
            n = frontier.pop(0)
            order.append(n)
            for m in sorted(succ[n]):
                indeg[m] -= 1
                if indeg[m] == 0:
                    frontier.append(m)
        if len(order) != len(ids):
            trapped = sorted(ids - set(order))
            return ToolResult.failure(
                Codes.TEMPORAL_CYCLE,
                f"PRECEDES cycle among {trapped}")
        beat_by_id = {b["id"]: b for b in beats}
        return ToolResult.success(data={
            "order": order,
            "beats": [{"beat_id": bid,
                       "label": beat_by_id[bid].get("label"),
                       "scene_id": beat_by_id[bid].get("scene")}
                      for bid in order],
            "edges_traversed": edges})

    @verb(role="transform")
    def story_time_query(self, novel_id: str) -> ToolResult:
        """The continuity scan (transform): every StoryTimeEvent + beat, and
        SURFACED temporal contradictions — an event whose scene-order
        (HAPPENS_AT) contradicts its ``when_story`` ordering is returned in
        ``contradictions``, never silently sorted around.

        Inputs: novel_id.
        Returns: ``{events, beats, contradictions: [{earlier, later,
                 reason}], coverage}`` — coverage 1.0 on an empty scope
                 (vacuous truth).
        chain_next: fix the contradicting when_story anchors; re-run.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        events = [ev for ev in self.ctx.find("StoryTimeEvent")
                  if ev.get("novel") == novel_id]
        beats = [b["id"] for b in self.ctx.find("NarrativeBeat")
                 if b.get("novel") == novel_id]
        chapters = {c["id"]: int(c.get("number", 0))
                    for c in self.ctx.neighbors(novel_id, "CHAPTER_OF")}
        # narrative position of each event = the chapter of a scene that
        # HAPPENS_AT it (earliest when several).
        narrative_pos: dict[str, int] = {}
        for ev in events:
            pos = [chapters.get((self.ctx.recall(s.get("chapter", ""))
                                 or {}).get("id",
                                            s.get("chapter", "")),
                                chapters.get(s.get("chapter", ""), 0))
                   for s in self.ctx.neighbors(ev["id"], "HAPPENS_AT",
                                               direction="in")]
            if pos:
                narrative_pos[ev["id"]] = min(pos)
        contradictions: list[dict] = []
        anchored = [ev for ev in events if ev["id"] in narrative_pos
                    and ev.get("when_story")]
        for i, e1 in enumerate(anchored):
            for e2 in anchored[i + 1:]:
                w1, w2 = e1["when_story"], e2["when_story"]
                n1 = narrative_pos[e1["id"]]
                n2 = narrative_pos[e2["id"]]
                # story-time says e1 before e2 but BOTH scenes sit in the
                # same direction? Only flag a hard inversion of anchors.
                if w1 < w2 and n1 > n2 and n1 != n2:
                    contradictions.append({
                        "earlier": e1["id"], "later": e2["id"],
                        "reason": f"when_story {w1!r} < {w2!r} but scene "
                                  f"order ch{n1} > ch{n2}"})
                elif w2 < w1 and n2 > n1:
                    contradictions.append({
                        "earlier": e2["id"], "later": e1["id"],
                        "reason": f"when_story {w2!r} < {w1!r} but scene "
                                  f"order ch{n2} > ch{n1}"})
        total = len(events)
        visited = len(narrative_pos)
        coverage = (visited / total) if total else 1.0
        return ToolResult.success(data={
            "events": [{"event_id": ev["id"], "label": ev.get("label", ""),
                        "when_story": ev.get("when_story", "")}
                       for ev in events],
            "beats": beats,
            "contradictions": contradictions,
            "coverage": round(coverage, 3)})

    @verb(role="transform")
    def events_pov_witnessed(self, character_id: str,
                             before_when: str = "") -> ToolResult:
        """The POV knowledge intersection (transform): events REVEALED_IN a
        scene the character fronts (``pov_character_id``), optionally cut to
        those with ``when_story`` < ``before_when``. |witnessed| ≤ |all|.

        Inputs: character_id, before_when (optional when_story ceiling).
        Returns: ``{events: [{event_id, label, when_story}], total_events}``.
        chain_next: compare against Spec 131's KnownFact ledger.
        """
        if self.ctx.recall(character_id) is None:
            return ToolResult.failure(
                Codes.UNKNOWN_CHARACTER,
                f"character {character_id!r} not found")
        out = []
        all_events = self.ctx.find("StoryTimeEvent")
        for ev in all_events:
            scenes = self.ctx.neighbors(ev["id"], "REVEALED_IN",
                                        direction="out")
            if not any(s.get("pov_character_id") == character_id
                       for s in scenes):
                continue
            if before_when and not (ev.get("when_story", "")
                                    < before_when):
                continue
            out.append({"event_id": ev["id"],
                        "label": ev.get("label", ""),
                        "when_story": ev.get("when_story", "")})
        out.sort(key=lambda e: e["when_story"])
        return ToolResult.success(data={
            "events": out, "total_events": len(all_events)})
