"""prompt.assembly — Dynamic prompt assembly (Spec 127).

Spec 286 P3 — extracted verbatim from ``prompt/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single PromptCapability.

Walks the graph for a Scene (or Chapter) and composes a bounded prompt with
sourced provenance. Pure transform; no LLM call; no driver dep —
fake-friendly for CI.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agency.capability import verb
from agency.toolresult import ToolResult

from ._base import _CHARS_PER_TOKEN, _approx_tokens


class AssemblyMixin:
    """Spec 127 — Dynamic prompt assembly (1 verb)."""

    @verb(role="act")
    def assemble_scene_brief(self, scene_id: str,
                              max_tokens: int = 4000,
                              section_budget: int = 320) -> ToolResult:
        """Compose a Novelcrafter-style scene brief from graph state (act).

        Walks Scene → Chapter → Novel → Storyform, then for each section
        (storyform / pov_card / scene_cast / world_rules / continuity /
        foreshadowing / voice_constraints) calls a private composer that
        truncates to ``section_budget``. Sections render in priority order
        (storyform highest, voice_constraints lowest); when ``max_tokens``
        binds, lower-priority sections drop with a ``truncated`` flag.

        Inputs: scene_id (graph id of a Scene node), max_tokens (total cap),
                section_budget (per-section cap).
        Returns: ``{prompt, sections, token_count, sources, truncated,
                  brief_id}`` — ``brief_id`` is the Artefact node id
                  recorded for provenance. ``{error: 'NOT_FOUND', ...}``
                  when scene_id doesn't resolve.
        chain_next: hand ``prompt`` to a generation driver; on return,
                    record the scene body back to the graph (Spec 130
                    scene-writer skill phase 5).
        """
        ctx = _BriefContext.from_scene(self.ctx, scene_id)
        if ctx.error:
            return ToolResult.success(data={
                "error": ctx.error, "scene_id": scene_id,
            })

        sections: dict[str, str] = {}
        sources: list[dict] = []
        truncated: list[str] = []
        running_total = 0

        # Section composition order — earlier = higher priority on budget bind.
        composers = [
            ("storyform", _compose_storyform),
            ("pov_card", _compose_pov_card),
            ("scene_cast", _compose_scene_cast),
            ("world_rules", _compose_world_rules),
            ("continuity", _compose_continuity),
            ("foreshadowing", _compose_foreshadowing),
            ("voice_constraints", _compose_voice_constraints),
        ]
        for name, composer in composers:
            text, src = composer(ctx, self)
            tokens = _approx_tokens(text)
            if tokens > section_budget:
                text = _truncate_to_tokens(text, section_budget)
                tokens = _approx_tokens(text)
                truncated.append(name)
            if running_total + tokens > max_tokens:
                truncated.append(name)
                continue
            sections[name] = text
            for s in src:
                sources.append({**s, "contributed": name})
            running_total += tokens

        prompt_body = _render_brief(sections)
        # Provenance: record the brief Artefact + SERVES intent.
        aid = self.ctx.record("Artefact", {
            "kind": "scene-brief",
            "scene_id": scene_id,
            "token_count": running_total,
            "section_count": len(sections),
            "truncated_count": len(truncated),
        })
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "prompt": prompt_body,
            "sections": sections,
            "token_count": running_total,
            "sources": sources,
            "truncated": truncated,
            "brief_id": aid,
        })


# ─────────────────────────── Spec 127 brief assembly ───────────────────────────
# Pure helpers — graph walk + fragment composition; no driver, no LLM,
# no filesystem; runs in CI on a bare graph.


@dataclass
class _BriefContext:
    """Graph-resolved context for an assemble_scene_brief call.

    Holds the Scene + Chapter + Novel + (optional) Storyform property dicts
    + a parsed NCP scope when the Storyform's body carries one. Composers
    read from this dataclass; errors short-circuit at the entry verb.
    """
    scene: dict
    chapter: dict
    novel: dict
    storyform_scope: dict
    _ctx: Any = None
    error: str | None = None

    @classmethod
    def from_scene(cls, ctx, scene_id: str) -> "_BriefContext":
        scene = ctx.recall(scene_id)
        if scene is None or "chapter" not in scene:
            return cls(scene={}, chapter={}, novel={}, storyform_scope={},
                       _ctx=ctx, error="NOT_FOUND")
        chapter_id = scene.get("chapter")
        chapter = ctx.recall(chapter_id) or {}
        novel_id = chapter.get("novel")
        novel = ctx.recall(novel_id) if novel_id else {}
        # Inject the novel's id into the novel props dict so composers can read
        # it without a separate lookup.
        if novel and novel_id:
            novel = {**novel, "id": novel_id}
        storyform_scope: dict = {}
        if novel_id:
            # Find a Storyform for this novel; pick the most-recent body.
            for sf in ctx.find("Storyform"):
                if sf.get("novel") == novel_id and sf.get("body"):
                    try:
                        import json as _json
                        ncp = _json.loads(sf["body"])
                        storyform_scope = _ncp_to_scope(ncp)
                    except (ValueError, TypeError):
                        pass
                    break
        return cls(scene=scene, chapter=chapter, novel=novel or {},
                   storyform_scope=storyform_scope, _ctx=ctx)


def _ncp_to_scope(ncp: dict) -> dict:
    """Flatten the relevant NCP storyform fields into a fragments_for scope."""
    story = ncp.get("storyform") or {}
    mc = (story.get("throughlines") or {}).get("mc") or {}
    return {
        "throughline": "mc",      # default: scene serves MC
        "class_id": mc.get("class_id"),
        "concern_id": mc.get("concern_id"),
        "problem_id": mc.get("problem_id"),
        "solution_id": mc.get("solution_id"),
        "crucial_element_id": story.get("crucial_element_id"),
    }


def _compose_storyform(bctx: _BriefContext, cap) -> tuple[str, list[dict]]:
    """Compose the storyform section via prompt.fragments_for (Spec 129)."""
    scope = dict(bctx.storyform_scope)
    # Drop None values — `fragments_for` treats them as "skip this key".
    scope = {k: v for k, v in scope.items() if v}
    if not scope:
        return ("(no storyform on this novel yet — Spec 103/120 surface unused)",
                [])
    tool_result = cap.fragments_for(scope=scope, max_tokens=1500)
    data = getattr(tool_result, "data", tool_result) or {}
    fragments = data.get("fragments", []) if isinstance(data, dict) else []
    parts: list[str] = []
    sources: list[dict] = []
    for f in fragments:
        parts.append(f"- **{f['canonical_id']}** ({f['kind']}): {f['text']}")
        sources.append({"node_id": f["canonical_id"], "kind": f["kind"]})
    body = "\n".join(parts) if parts else "(no fragments authored for this scope)"
    return body, sources


def _compose_pov_card(bctx: _BriefContext, _cap) -> tuple[str, list[dict]]:
    """Spec 131 upgrade — adds POV-knows subsection when scene declares
    `pov_character_id` and the character has KnownFacts learned by this
    narrative position."""
    pov = bctx.scene.get("pov") or "unset"
    lines = [
        f"POV: {pov}",
        f"Scene slug: {bctx.scene.get('slug', '')}",
    ]
    sources: list[dict] = [
        {"node_id": bctx.scene.get("id", ""), "kind": "Scene"}]
    pov_character_id = bctx.scene.get("pov_character_id") or ""
    scene_id = bctx.scene.get("id", "")
    if pov_character_id and scene_id and bctx._ctx:
        try:
            from agency.capabilities.novel._main import NovelCapability
            novel_cap = NovelCapability(bctx._ctx)
            result = novel_cap.what_does_X_know_as_of(
                character_id=pov_character_id, scene_id=scene_id)
            facts = (getattr(result, "data", result) or {}).get("facts", [])
        except Exception:
            facts = []
        if facts:
            lines.append("")
            lines.append("POV knows (as of this narrative position):")
            for f in facts:
                lines.append(f"- {f['fact']}")
                sources.append({"node_id": f["fact_id"],
                                 "kind": "KnownFact"})
    return "\n".join(lines), sources


def _compose_scene_cast(bctx: _BriefContext, _cap) -> tuple[str, list[dict]]:
    cast = bctx.scene.get("cast") or ""
    if not cast:
        return ("(no scene_cast tracked yet — Spec 123 PsychProfile/Character "
                "ontology pending)", [])
    return f"Cast in scene: {cast}", [
        {"node_id": bctx.scene.get("id", ""), "kind": "Scene"}]


def _compose_world_rules(bctx: _BriefContext, _cap) -> tuple[str, list[dict]]:
    """Spec 132 upgrade — scans scene text against registered codex triggers."""
    sources: list[dict] = []
    novel_id = (bctx.novel or {}).get("id", "")
    if not novel_id:
        return ("(no novel context — world_rules skipped)", sources)
    # Gather scannable text: chapter body + scene cast + scene slug.
    scan_text = " ".join([
        bctx.chapter.get("body", "") or "",
        bctx.chapter.get("title", "") or "",
        bctx.scene.get("slug", "") or "",
        bctx.scene.get("cast", "") or "",
    ])
    if not scan_text.strip():
        return ("(no scene/chapter text to scan — world_rules skipped)",
                sources)
    matches: list[dict] = []
    try:
        from agency.capabilities.novel._main import NovelCapability
        novel_cap = NovelCapability(bctx._ctx) if bctx._ctx else None
        if novel_cap is not None:
            result = novel_cap.match_codex_entries(
                novel_id=novel_id, text=scan_text)
            matches = (getattr(result, "data", result) or {}).get(
                "matches", [])
    except Exception:
        matches = []
    if not matches:
        return ("(no codex entries match this scene's text — "
                "register entries via novel.create_codex_entry)",
                sources)
    parts = ["World facts in scope (auto-matched by trigger):"]
    for m in matches:
        parts.append(f"- **{m['name']}** ({m['kind']}): {m['body']}")
        sources.append({"node_id": m["entry_id"], "kind": "CodexEntry"})
    return "\n".join(parts), sources


def _compose_continuity(bctx: _BriefContext, _cap) -> tuple[str, list[dict]]:
    """Spec 128 upgrade — reads StoryTimeEvent graph for the continuity slice."""
    chapter_n = bctx.chapter.get("number", "?")
    scene_id = bctx.scene.get("id", "")
    sources: list[dict] = [
        {"node_id": bctx.chapter.get("id", ""), "kind": "Chapter"}]
    # Probe the novel cap for story-time events up to this scene's anchor.
    try:
        from agency.capabilities.novel._main import NovelCapability
        novel_cap = NovelCapability(bctx._ctx)
        result = novel_cap.list_story_events_up_to(scene_id=scene_id)
        events = (getattr(result, "data", result) or {}).get("events", [])
    except Exception:
        events = []
    if not events:
        return (f"Story-time anchor: chapter {chapter_n}. "
                f"(no StoryTimeEvent anchors recorded yet — author "
                f"hasn't anchored this scene)", sources)
    parts = [f"Story-time anchor: chapter {chapter_n}.",
             "Events known by this scene's story-time:"]
    for ev in events:
        parts.append(f"- [{ev['when_story']}] {ev['label']}")
        sources.append({"node_id": ev["event_id"], "kind": "StoryTimeEvent"})
    return "\n".join(parts), sources


def _compose_foreshadowing(_bctx: _BriefContext, _cap) -> tuple[str, list[dict]]:
    return ("(foreshadowing obligations — Spec 123 PlantedElement pending; "
            "no Chekhov's-gun report)", [])


def _compose_voice_constraints(bctx: _BriefContext, _cap) -> tuple[str, list[dict]]:
    pov = bctx.scene.get("pov") or ""
    tense_hint = {
        "first": "first-person past unless the chapter outline says otherwise",
        "second": "second-person — carry the unsettling intimacy",
        "third-limited": "third-limited, deep, anchored to the POV's interiority",
        "third-omniscient": "third-omniscient — knowing-narrator distance",
    }.get(pov, "match the established novel voice")
    return f"Voice: {tense_hint}.", [
        {"node_id": bctx.scene.get("id", ""), "kind": "Scene"}]


def _truncate_to_tokens(text: str, budget: int) -> str:
    """Cut to ≈ budget cl100k tokens (4-chars/token heuristic) + ellipsis."""
    max_chars = max(0, budget * _CHARS_PER_TOKEN - 3)
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


_SECTION_TITLES = {
    "storyform": "Storyform position",
    "pov_card": "POV card",
    "scene_cast": "Scene cast",
    "world_rules": "World rules in scope",
    "continuity": "Continuity / story-time",
    "foreshadowing": "Foreshadowing obligations",
    "voice_constraints": "Voice + craft constraints",
}


def _render_brief(sections: dict) -> str:
    """Render the SceneBrief as structured markdown (per Open Q1)."""
    parts: list[str] = ["# Scene brief\n"]
    for name in _SECTION_TITLES:
        if name in sections:
            parts.append(f"## {_SECTION_TITLES[name]}\n\n{sections[name]}\n")
    return "\n".join(parts)
