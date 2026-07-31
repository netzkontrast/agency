"""novel.structure — story structure templates, the pacing layer (Spec 133).

Storyform (Dramatica, Spec 103/120) answers the WHAT of meaning; this cluster
answers the WHEN of pacing: vendored beat-sheet templates (Save the Cat,
Three-Act, Hero's Journey, Story Circle, Snowflake) as data under
``novel/data/structures/``, applied to a novel as ``BeatExpectation`` nodes,
anchored scene→beat via ``FULFILS``, and measured by a position report.

Templates are DATA, not code: authors extend the set via
``.agency/structure-templates-overlay.yaml`` (the Spec 129 fragments pattern).
There is deliberately NO ``StructureTemplate`` graph node — the JSON files ARE
the templates (a node nothing mints would be dormant surface; CLAUDE.md).
"""
from __future__ import annotations

import json
from pathlib import Path

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

_STRUCTURES_DIR = Path(__file__).parent.parent / "data" / "structures"
_OVERLAY_PATH = Path(".agency") / "structure-templates-overlay.yaml"

#: |actual - target| beyond this fraction flags a beat as out_of_position.
#: Tunable pacing budget (rule 8): one act-tenth of manuscript drift.
POSITION_TOLERANCE = 0.10


def _load_structure_templates() -> dict[str, dict]:
    """Builtin JSONs ∪ the repo overlay, keyed by template_id (overlay wins).

    Loaded per call — the set is small and the overlay is cwd-relative, so a
    module cache would go stale across test repos.
    """
    templates: dict[str, dict] = {}
    for p in sorted(_STRUCTURES_DIR.glob("*.json")):
        body = json.loads(p.read_text(encoding="utf-8"))
        templates[body["template_id"]] = body
    if _OVERLAY_PATH.exists():
        import yaml
        overlay = yaml.safe_load(_OVERLAY_PATH.read_text(encoding="utf-8")) or {}
        for body in overlay.get("templates", []) or []:
            if isinstance(body, dict) and body.get("template_id"):
                templates[body["template_id"]] = body
    return templates


class StructureMixin:
    """Structure cluster — beat-sheet templates + coverage/position checks."""

    @verb(role="transform")
    def list_structure_templates(self) -> ToolResult:
        """Discover the available story-structure templates (transform).

        Inputs: none.
        Returns: ``{templates: [{template_id, name, source, beat_count}]}`` —
                 the five vendored beat sheets ∪ any
                 ``.agency/structure-templates-overlay.yaml`` additions.
        chain_next: ``novel.get_structure_template(template_id)`` for the full
                    beat list; ``novel.apply_structure`` to commit one.
        """
        rows = [{"template_id": t["template_id"], "name": t.get("name", ""),
                 "source": t.get("source", ""),
                 "beat_count": len(t.get("beats", []))}
                for t in _load_structure_templates().values()]
        rows.sort(key=lambda r: r["template_id"])
        return ToolResult.success(data={"templates": rows})

    @verb(role="transform")
    def get_structure_template(self, template_id: str) -> ToolResult:
        """Read one template's full body — every beat with its position +
        author-facing prompt (transform).

        Inputs: template_id.
        Returns: ``{template_id, name, source, beats: [{slug, name, position,
                 prompt}]}``; NOT_FOUND for an unknown id.
        chain_next: ``novel.apply_structure(novel_id, template_id)``.
        """
        t = _load_structure_templates().get(template_id)
        if t is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"no structure template {template_id!r}")
        return ToolResult.success(data=dict(t))

    @verb(role="effect")
    def apply_structure(self, novel_id: str, template_id: str) -> ToolResult:
        """Apply a structure template: mint one ``BeatExpectation`` per beat
        (effect). Idempotent on ``(novel_id, template_id)`` — and on a template
        SWITCH, anchored beats whose slug exists in the new template keep their
        scene anchor (re-targeted); every other prior expectation is retracted
        (one template per novel).

        Inputs: novel_id, template_id.
        Returns: ``{novel_id, template_id, beat_count, minted, preserved}``.
        chain_next: ``novel.anchor_beat`` per drafted scene;
                    ``novel.check_structure_coverage`` for the checklist.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        t = _load_structure_templates().get(template_id)
        if t is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"no structure template {template_id!r}")
        prior = [b for b in self.ctx.find("BeatExpectation")
                 if b.get("novel") == novel_id]
        anchored = {b.get("beat_slug"): b for b in prior if b.get("scene_id")}
        new_slugs = {b["slug"] for b in t.get("beats", [])}
        preserved = 0
        for b in prior:
            slug = b.get("beat_slug")
            if b.get("scene_id") and slug in new_slugs:
                continue                       # re-targeted below, anchor kept
            self.ctx.memory.retract(b["id"])
        minted = 0
        for beat in t.get("beats", []):
            kept = anchored.get(beat["slug"])
            if kept is not None:
                self.ctx.memory.update(kept["id"], {
                    "template_id": template_id,
                    "target_position": beat["position"],
                    "prompt": beat.get("prompt", ""),
                })
                preserved += 1
                continue
            # OQ1: blob the prompt onto the node at apply time so a later
            # template edit doesn't rewrite committed expectations.
            eid = self.ctx.record("BeatExpectation", {
                "novel": novel_id, "template_id": template_id,
                "beat_slug": beat["slug"], "beat_name": beat.get("name", ""),
                "target_position": beat["position"],
                "prompt": beat.get("prompt", ""), "scene_id": "",
            })
            self.ctx.link(eid, self.ctx.intent_id, "SERVES")
            minted += 1
        return ToolResult.success(data={
            "novel_id": novel_id, "template_id": template_id,
            "beat_count": len(t.get("beats", [])),
            "minted": minted, "preserved": preserved,
        })

    @verb(role="effect")
    def anchor_beat(self, novel_id: str, beat_slug: str,
                    scene_id: str) -> ToolResult:
        """Map a manuscript scene to a beat: ``FULFILS`` edge + the
        expectation's ``scene_id`` (effect).

        Inputs: novel_id, beat_slug (from the applied template), scene_id.
        Returns: ``{novel_id, beat_slug, scene_id, anchored}``.
        chain_next: ``novel.structure_position_report`` once several beats
                    are anchored.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        scene = self.ctx.recall(scene_id)
        if not scene:
            return ToolResult.failure(Codes.NOT_FOUND,
                                      f"no scene {scene_id!r}")
        exp = next((b for b in self.ctx.find("BeatExpectation")
                    if b.get("novel") == novel_id
                    and b.get("beat_slug") == beat_slug), None)
        if exp is None:
            return ToolResult.failure(
                Codes.NOT_FOUND,
                f"no BeatExpectation {beat_slug!r} on {novel_id!r} — "
                f"apply_structure first")
        self.ctx.memory.update(exp["id"], {"scene_id": scene_id})
        self.ctx.link(scene_id, exp["id"], "FULFILS")
        return ToolResult.success(data={
            "novel_id": novel_id, "beat_slug": beat_slug,
            "scene_id": scene_id, "anchored": True,
        })

    @verb(role="transform")
    def check_structure_coverage(self, novel_id: str) -> ToolResult:
        """The author's checklist: which beats are anchored to scenes, which
        still await one (transform).

        Inputs: novel_id.
        Returns: ``{anchored, unanchored: [{beat_slug, name,
                 target_position}]}``.
        chain_next: ``novel.anchor_beat`` for each unanchored beat.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        exps = [b for b in self.ctx.find("BeatExpectation")
                if b.get("novel") == novel_id]
        unanchored = [{"beat_slug": b.get("beat_slug"),
                       "name": b.get("beat_name", ""),
                       "target_position": b.get("target_position")}
                      for b in exps if not b.get("scene_id")]
        unanchored.sort(key=lambda u: u["target_position"] or 0)
        return ToolResult.success(data={
            "anchored": len(exps) - len(unanchored),
            "unanchored": unanchored,
        })

    @verb(role="transform")
    def structure_position_report(self, novel_id: str) -> ToolResult:
        """Target vs actual manuscript position per anchored beat (transform).

        ``actual_position`` uses cumulative word count when chapters carry
        bodies, else the chapter midpoint fraction (OQ3). A beat drifting
        beyond ``POSITION_TOLERANCE`` is flagged ``out_of_position``.

        Inputs: novel_id.
        Returns: ``{beats: [{beat_slug, target_position, actual_position,
                 out_of_position}]}``.
        chain_next: revise chapter order / re-anchor, then re-run.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(self.ctx.neighbors(novel_id, "CHAPTER_OF"),
                          key=lambda c: int(c.get("number", 0)))
        words = [len((c.get("body") or "").split()) for c in chapters]
        total_words = sum(words)
        total_chapters = len(chapters)
        chapter_index = {c["id"]: i for i, c in enumerate(chapters)}

        def _actual(scene: dict) -> float | None:
            i = chapter_index.get(scene.get("chapter", ""))
            if i is None or not total_chapters:
                return None
            if total_words:
                return (sum(words[:i]) + words[i] / 2) / total_words
            return (i + 0.5) / total_chapters

        beats = []
        for b in self.ctx.find("BeatExpectation"):
            if b.get("novel") != novel_id or not b.get("scene_id"):
                continue
            scene = self.ctx.recall(b["scene_id"]) or {}
            actual = _actual(scene)
            target = float(b.get("target_position") or 0.0)
            beats.append({
                "beat_slug": b.get("beat_slug"),
                "target_position": target,
                "actual_position": actual,
                "out_of_position": (actual is not None
                                    and abs(actual - target)
                                    > POSITION_TOLERANCE),
            })
        beats.sort(key=lambda x: x["target_position"])
        return ToolResult.success(data={"beats": beats})
