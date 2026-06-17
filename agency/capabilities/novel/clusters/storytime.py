"""novel.storytime — Story-time / narrative-time cluster — events, reveals, narrative beats (Spec 128).

Spec 286 P3 — extracted verbatim from ``novel/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single NovelCapability.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult


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
                "NOT_FOUND", f"novel_id={novel_id!r} not found")
        eid = self.ctx.record_and_serve("StoryTimeEvent", {
            "novel": novel_id, "label": label, "when_story": when_story,
        })
        out: dict = {"event_id": eid, "label": label,
                     "when_story": when_story}
        if scene_id:
            if self.ctx.recall(scene_id) is None:
                return ToolResult.failure(
                    "NOT_FOUND", f"scene_id={scene_id!r} not found")
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
                "NOT_FOUND", f"event_id={event_id!r} not found")
        if self.ctx.recall(scene_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
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
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
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
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
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
                "NOT_FOUND", f"scene_id={scene_id!r} not found")
        # Spec 282 Workstream C — validate ALL preconditions BEFORE any write,
        # so a bad predecessor never leaves an orphan NarrativeBeat node (the
        # create-node-then-fail-edge partial write). The node + its PRECEDES
        # edge land together or not at all.
        if predecessor_id and self.ctx.recall(predecessor_id) is None:
            return ToolResult.failure(
                "NOT_FOUND",
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

    @verb(role="transform")
    def narrative_order(self, novel_id: str) -> ToolResult:
        """Topo-sort over PRECEDES for the canonical narrative reading order (transform).

        Inputs: novel_id.
        Returns: ``{beats: [{beat_id, label, scene_id}]}`` ordered so every
                 predecessor appears before its successor.
        chain_next: author's checklist for the manuscript's narrative spine.
        """
        if self.ctx.recall(novel_id) is None:
            return ToolResult.failure(
                "NOT_FOUND", f"novel_id={novel_id!r} not found")
        beats = [b for b in self.ctx.find("NarrativeBeat")
                  if b.get("novel") == novel_id]
        # Build predecessor map by querying PRECEDES.
        edges = []
        for a_props, b_props in self.ctx.edge_pairs(
                "PRECEDES", "NarrativeBeat", "NarrativeBeat"):
            a_id = a_props.get("id")
            b_id = b_props.get("id")
            if a_id and b_id:
                edges.append((a_id, b_id))
        # Kahn's algorithm over the beats of THIS novel.
        beat_ids = {b.get("id") for b in beats}
        in_degree = {bid: 0 for bid in beat_ids}
        successors: dict = {bid: [] for bid in beat_ids}
        for a, b in edges:
            if a in beat_ids and b in beat_ids:
                in_degree[b] += 1
                successors[a].append(b)
        queue = [bid for bid, d in in_degree.items() if d == 0]
        order: list[str] = []
        while queue:
            n = queue.pop(0)
            order.append(n)
            for s in successors[n]:
                in_degree[s] -= 1
                if in_degree[s] == 0:
                    queue.append(s)
        beat_by_id = {b.get("id"): b for b in beats}
        return ToolResult.success(data={
            "beats": [
                {"beat_id": bid,
                 "label": beat_by_id[bid].get("label"),
                 "scene_id": beat_by_id[bid].get("scene")}
                for bid in order if bid in beat_by_id
            ],
        })
