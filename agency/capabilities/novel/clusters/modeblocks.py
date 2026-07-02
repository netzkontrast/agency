"""novel.modeblocks — chapter briefing & narrative-mode blocks (Spec 141).

The manuscript divides into mode-blocks — spans of chapters sharing a
narrative stance (Modus · storyform-status · bridge-frequency), each with a
per-act genre accent ("genre-bleed between acts = defect"). Crucially,
MODE-CHANGES ARE NOT STORYFORM BOUNDARIES — the KP's load-bearing distinction,
made machine-checkable here. The chapter briefing is the bridge document
between storyform-encoding and telling: ``render_chapter_briefing`` AGGREGATES
the whole 136–140 stack into the vendored 13-section template; the pre-draft
checklist gates the draft.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

NARRATIVE_MODE = {"linear-introspective", "cyclic-recursive",
                  "linear-ascending", "vortex-still", "choral", "framing"}

#: Chapters carrying the ouroboros frame duty (Genesis-Prolog / Coda ring).
OUROBOROS_CHAPTERS = {0, 1, 39, 40}


class ModeBlocksMixin:
    """Mode-block cluster — blocks, boundary checks, the chapter briefing."""

    def _blocks(self, novel_id: str) -> list[dict]:
        return sorted((b for b in self.ctx.find("ModeBlock")
                       if b.get("novel") == novel_id),
                      key=lambda b: int(b.get("from_chapter", 0)))

    def _block_of_chapter(self, novel_id: str, number: int) -> dict | None:
        return next((b for b in self._blocks(novel_id)
                     if int(b.get("from_chapter", 0)) <= number
                     <= int(b.get("to_chapter", 0))), None)

    @verb(role="effect")
    def define_mode_block(self, novel_id: str, label: str, mode: str,
                          from_chapter: int, to_chapter: int,
                          bridge_frequency_target: float = 0.0,
                          genre_accent: str = "") -> ToolResult:
        """Mint a ``ModeBlock`` — a chapter span sharing a narrative stance
        (effect).

        Inputs: novel_id, label (e.g. "Akt I — Heldinnenreise"), mode
                (linear-introspective|cyclic-recursive|linear-ascending|
                vortex-still|choral|framing), from_chapter, to_chapter,
                bridge_frequency_target (the Spec 136 soft-share target),
                genre_accent (the §11 per-act genre).
        Returns: ``{mode_block_id, label, mode}``.
        chain_next: ``novel.assign_chapter_to_block`` per chapter;
                    ``novel.mode_block_report``.
        """
        if mode not in NARRATIVE_MODE:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"mode={mode!r} not in {sorted(NARRATIVE_MODE)}")
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        bid = self.ctx.record("ModeBlock", {
            "novel": novel_id, "label": label, "mode": mode,
            "from_chapter": from_chapter, "to_chapter": to_chapter,
            "bridge_frequency_target": bridge_frequency_target,
            "genre_accent": genre_accent})
        self.ctx.link(bid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "mode_block_id": bid, "label": label, "mode": mode})

    @verb(role="effect")
    def assign_chapter_to_block(self, chapter_id: str,
                                mode_block_id: str) -> ToolResult:
        """Bind a chapter to its block via ``IN_MODE_BLOCK`` (effect).

        Inputs: chapter_id, mode_block_id.
        Returns: ``{chapter_id, mode_block_id}``.
        chain_next: ``novel.mode_block_report(novel_id)``.
        """
        _, fail = self._require_chapter(chapter_id)
        if fail is not None:
            return fail
        if self.ctx.recall(mode_block_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"block {mode_block_id!r} not found")
        self.ctx.link(chapter_id, mode_block_id, "IN_MODE_BLOCK")
        self.ctx.memory.update(chapter_id,
                               {"mode_block_id": mode_block_id})
        return ToolResult.success(data={
            "chapter_id": chapter_id, "mode_block_id": mode_block_id})

    @verb(role="transform")
    def mode_block_report(self, novel_id: str) -> ToolResult:
        """The §1 block table (transform): every block with mode / bridge
        target / genre; chapters in NO block are the unstaged surface.

        Inputs: novel_id.
        Returns: ``{blocks: [{label, mode, from_chapter, to_chapter,
                 bridge_frequency_target, genre_accent}], unstaged:
                 [chapter_number]}``.
        chain_next: ``novel.define_mode_block`` for the unstaged spans.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        blocks = self._blocks(novel_id)
        unstaged = []
        for c in self.ctx.neighbors(novel_id, "CHAPTER_OF"):
            n = int(c.get("number", 0))
            if self._block_of_chapter(novel_id, n) is None:
                unstaged.append(n)
        return ToolResult.success(data={
            "blocks": [{"label": b.get("label", ""), "mode": b.get("mode"),
                        "from_chapter": int(b.get("from_chapter", 0)),
                        "to_chapter": int(b.get("to_chapter", 0)),
                        "bridge_frequency_target":
                            float(b.get("bridge_frequency_target") or 0),
                        "genre_accent": b.get("genre_accent", "")}
                       for b in blocks],
            "unstaged": sorted(unstaged)})

    @verb(role="transform")
    def check_mode_vs_storyform_boundary(self, novel_id: str) -> ToolResult:
        """The KP's load-bearing distinction (transform): mode-changes are
        NOT storyform boundaries. A ``StoryformTransition`` whose chapter
        sits on a NON-vortex mode edge is a mislabeling — the real storyform
        turn is the Vortex, not the mode edge.

        Inputs: novel_id.
        Returns: ``{passed, violations: [{transition_id, at_chapter,
                 block_label, reason}]}``.
        chain_next: retag the transition or move the block edge.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        blocks = self._blocks(novel_id)
        set_ids = {s["id"] for s in self.ctx.find("StoryformSet")
                   if s.get("novel") == novel_id}
        violations: list[dict] = []
        for t in self.ctx.find("StoryformTransition"):
            if t.get("storyform_set_id") not in set_ids:
                continue
            at = int(t.get("at_chapter", 0))
            for b in blocks:
                edge_chapters = {int(b.get("from_chapter", 0)),
                                 int(b.get("to_chapter", 0)),
                                 int(b.get("to_chapter", 0)) + 1}
                if at in edge_chapters and b.get("mode") != "vortex-still":
                    violations.append({
                        "transition_id": t["id"], "at_chapter": at,
                        "block_label": b.get("label", ""),
                        "reason": (f"storyform transition at ch{at} sits on "
                                   f"the {b.get('mode')!r} mode edge — mode "
                                   f"changes are not storyform boundaries")})
        return ToolResult.success(data={
            "passed": not violations, "violations": violations})

    @verb(role="transform")
    def check_genre_bleed(self, novel_id: str) -> ToolResult:
        """The §11 genre-bleed rule (transform, soft): a chapter whose drafted
        ``genre_accent`` contradicts its block's accent is flagged — the
        author decides.

        Inputs: novel_id.
        Returns: ``{passed, bleeds: [{chapter_number, chapter_accent,
                 block_accent}]}``.
        chain_next: re-accent the chapter or the block.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        bleeds: list[dict] = []
        for c in self.ctx.neighbors(novel_id, "CHAPTER_OF"):
            accent = c.get("genre_accent", "")
            if not accent:
                continue
            block = self._block_of_chapter(novel_id,
                                           int(c.get("number", 0)))
            if block and block.get("genre_accent") \
                    and block["genre_accent"] != accent:
                bleeds.append({"chapter_number": int(c.get("number", 0)),
                               "chapter_accent": accent,
                               "block_accent": block["genre_accent"]})
        return ToolResult.success(data={
            "passed": not bleeds, "bleeds": bleeds})

    # ── the chapter briefing (the bridge document) ─────────────────────────

    @verb(role="act")
    def render_chapter_briefing(self, chapter_id: str) -> ToolResult:
        """Compose the 13-section chapter briefing (act) — AGGREGATES the
        whole KP stack (mode-block 141, storyform routing 136, alters/voice
        138, reveals 139, motifs/anchors/R-rules 140) into the vendored
        template; records a ``chapter-briefing`` Artefact.

        Inputs: chapter_id.
        Returns: ``{content, artefact_id, chapter_id}``.
        chain_next: fill the — slots by hand; ``novel.briefing_checklist``.
        """
        chapter, fail = self._require_chapter(chapter_id)
        if fail is not None:
            return fail
        novel_id = chapter.get("novel", "")
        number = int(chapter.get("number", 0))
        block = self._block_of_chapter(novel_id, number) or {}

        sets = [s for s in self.ctx.find("StoryformSet")
                if s.get("novel") == novel_id]
        transition = next((t for t in self.ctx.find("StoryformTransition")
                           if sets and t.get("storyform_set_id")
                           == sets[0]["id"]
                           and int(t.get("at_chapter", 0)) == number), None)
        systems = [s for s in self.ctx.find("CharacterSystem")
                   if s.get("novel") == novel_id]
        alters = (self._alters(systems[0]["id"]) if systems else [])
        rules = [r for r in self.ctx.find("ProjectRule")
                 if r.get("novel") == novel_id]
        reveals = [r for r in self.ctx.find("RevealRule")
                   if r.get("novel") == novel_id
                   and int(r.get("may_know_from_chapter") or 0) == number]
        anchors = [a for a in self.ctx.find("Anchor")
                   if a.get("novel") == novel_id]

        # The vendored template is Jinja (Spec 388); derive every declared
        # variable and default the hand-fill slots to "—" so StrictUndefined
        # never fires on an aggregator field the graph can't know yet.
        from jinja2 import Environment, meta
        tpl = self.ctx.template("chapter-briefing")
        body = tpl.template if hasattr(tpl, "template") else str(tpl)
        declared = meta.find_undeclared_variables(Environment().parse(body))
        fields = {name: "—" for name in declared}
        fields.update({
            "chapter_number": number,
            "chapter_title": chapter.get("title", ""),
            "chapter_id": chapter_id,
            "mode_block_label": block.get("label", "—"),
            "mode_block_mode": block.get("mode", "—"),
            "from_chapter": block.get("from_chapter", "—"),
            "to_chapter": block.get("to_chapter", "—"),
            "bridge_frequency_target":
                block.get("bridge_frequency_target", "—"),
            "genre_accent": block.get("genre_accent", "—"),
            "transition_kind_or_none":
                (transition or {}).get("kind", "none"),
            "speakers": ", ".join(a.get("name", "") for a in alters) or "—",
            "reader_reveals": "; ".join(r.get("fact", "")
                                        for r in reveals) or "—",
            "anchors_planted": ", ".join(
                a.get("name", "") for a in anchors
                if int(a.get("planted_chapter", 0)) == number) or "—",
            "anchors_paid_off": ", ".join(
                a.get("name", "") for a in anchors
                if int(a.get("payoff_chapter") or 0) == number) or "—",
            "open_anchors": ", ".join(
                a.get("name", "") for a in anchors
                if not int(a.get("payoff_chapter") or 0)) or "—",
        })
        fields = {k: v for k, v in fields.items() if k in declared}
        content = self.ctx.render("chapter-briefing", **fields)
        emitted = self.ctx.record("Artefact", {
            "kind": "chapter-briefing", "chapter_id": chapter_id,
            "novel": novel_id})
        self.ctx.link(emitted, self.ctx.intent_id, "SERVES")
        self.ctx.link(self.ctx.intent_id, emitted, "PRODUCES")
        return ToolResult.success(data={
            "content": content, "artefact_id": emitted,
            "chapter_id": chapter_id,
            "rule_count": len(rules)})

    @verb(role="transform")
    def briefing_checklist(self, chapter_id: str) -> ToolResult:
        """The §9 section-M pre-draft checklist (transform): what must be in
        place before this chapter drafts.

        Inputs: chapter_id.
        Returns: ``{ready, missing: [str]}`` — mode-block staged ·
                 storyform present · voice anchor exists · R-rules registered
                 · reveal rules defined · ouroboros duty (ch 0/1/39/40 need a
                 framing block).
        chain_next: resolve the missing items; ``novel.render_chapter_briefing``.
        """
        chapter, fail = self._require_chapter(chapter_id)
        if fail is not None:
            return fail
        novel_id = chapter.get("novel", "")
        number = int(chapter.get("number", 0))
        missing: list[str] = []
        if self._block_of_chapter(novel_id, number) is None:
            missing.append("mode-block: chapter is unstaged")
        if not any(s.get("novel") == novel_id
                   for s in self.ctx.find("Storyform")):
            missing.append("storyform-status: no Storyform encoded")
        if not self.ctx.find("VoiceProfile"):
            missing.append("voice-DNA: no VoiceProfile anchored")
        if not any(r.get("novel") == novel_id
                   for r in self.ctx.find("ProjectRule")):
            missing.append("R-rules: none registered (hot-polarity, "
                           "genesis-echo unchecked)")
        if not any(r.get("novel") == novel_id
                   for r in self.ctx.find("RevealRule")):
            missing.append("reveal-layer: no RevealRule defined")
        if number in OUROBOROS_CHAPTERS and not any(
                b.get("mode") == "framing" for b in self._blocks(novel_id)):
            missing.append(f"ouroboros-duty: ch{number} needs a framing "
                           f"mode-block")
        return ToolResult.success(data={
            "ready": not missing, "missing": missing})
