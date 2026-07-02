"""novel.reveal — reveal-discipline & reader-steering (Spec 139).

"Lesersteuerung als oberstes Prinzip": what must the reader know when, what
may they NOT know when, through what do they learn it? Three independent
knowledge horizons (reader / POV / antagonist) each carry ``RevealRule``s;
the multiplicity-veil holds until its chapter; deliberate Iser-Leerstellen
are registered first-class so later lint never "fixes" an intentional gap.
Complements Spec 131 (in-world character knowledge) and Spec 138 (naming
FORM) — this is reveal TIMING.
"""
from __future__ import annotations

import re

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

AUDIENCE_TIER = {"reader", "pov", "antagonist"}
REVEAL_CHANNEL = {"glitch", "log", "sensory", "dialogue", "metaphor",
                  "narration", ""}
LEERSTELLE_KIND = {"fragmented-perspective", "contradictory-footnote",
                   "temporal-scramble", "pronoun-shift"}
READER_LAYER = {"narratological", "phenomenological", "operative"}

#: Default multiplicity-veil terms (the KP clinical set).
DEFAULT_VEIL_TERMS = "DID,Alter,Fragment,ANP,EP,TSDP"

#: Signal lexica for the reader-function audit (documented heuristics —
#: a tag fires when its countable signal is present; layers may overlap).
_PHENOMENOLOGICAL = {"smell", "taste", "cold", "warm", "rough", "ache",
                     "hum", "sting", "glare", "damp", "salt", "iron"}
_NARRATOLOGICAL_RE = re.compile(
    r"(?m)^\s*(\[log\b|footnote|\d{2}:\d{2}|---)", re.IGNORECASE)
_OPERATIVE_RE = re.compile(r"\?|…|\.\.\.")


class RevealMixin:
    """Reveal cluster — tiers, veil, Leerstellen, the reveal gate."""

    def _rules(self, novel_id: str) -> list[dict]:
        return [r for r in self.ctx.find("RevealRule")
                if r.get("novel") == novel_id]

    def _scene_chapter_number(self, scene: dict) -> int:
        ch = self.ctx.recall(scene.get("chapter", "")) or {}
        return int(ch.get("number", 0))

    @verb(role="effect")
    def set_reveal_rule(self, novel_id: str, fact: str, tier: str,
                        may_know_from_chapter: int, must_not_before: int = 0,
                        channel: str = "", rationale: str = "",
                        fact_node_id: str = "") -> ToolResult:
        """Mint/update a ``RevealRule`` — upsert keyed by (novel, fact, tier)
        (effect).

        Inputs: novel_id, fact (freeform or a node-ref), tier
                (reader|pov|antagonist), may_know_from_chapter,
                must_not_before (0 = use may_know_from_chapter as the floor),
                channel (glitch|log|sensory|dialogue|metaphor|narration),
                rationale, fact_node_id (when the fact IS a node).
        Returns: ``{rule_id, tier, may_know_from_chapter, was_update}``.
        chain_next: ``novel.check_reveal_timing(scene_id, fact)`` while
                    drafting; ``novel.reveal_timeline_report``.
        """
        if tier not in AUDIENCE_TIER:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"tier={tier!r} not in {sorted(AUDIENCE_TIER)}")
        if channel not in REVEAL_CHANNEL:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"channel={channel!r} not in {sorted(REVEAL_CHANNEL)}")
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        props = {"novel": novel_id, "fact": fact, "tier": tier,
                 "may_know_from_chapter": may_know_from_chapter,
                 "must_not_before": must_not_before, "channel": channel,
                 "rationale": rationale, "fact_node_id": fact_node_id}
        existing = next((r for r in self._rules(novel_id)
                         if r.get("fact") == fact and r.get("tier") == tier),
                        None)
        if existing is not None:
            self.ctx.memory.update(existing["id"], props)
            rid, was_update = existing["id"], True
        else:
            rid = self.ctx.record("RevealRule", props)
            self.ctx.link(rid, self.ctx.intent_id, "SERVES")
            if fact_node_id and self.ctx.recall(fact_node_id) is not None:
                self.ctx.link(rid, fact_node_id, "GOVERNS_REVEAL")
            was_update = False
        return ToolResult.success(data={
            "rule_id": rid, "novel_id": novel_id, "fact": fact, "tier": tier,
            "may_know_from_chapter": may_know_from_chapter,
            "must_not_before": must_not_before, "channel": channel,
            "was_update": was_update})

    @verb(role="transform")
    def check_reveal_timing(self, scene_id: str, fact: str) -> ToolResult:
        """Check one scene against every tier's rule for a fact (transform).
        A violation fires when the fact appears in the scene body and the
        scene's chapter precedes the tier's floor (``must_not_before``, else
        ``may_know_from_chapter``).

        Inputs: scene_id, fact.
        Returns: ``{ok, violations: [{tier, rule_id, floor, chapter}],
                 no_rule?}``.
        chain_next: move the reveal later, or adjust the rule.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene {scene_id!r} not found")
        ch_node = self.ctx.recall(scene.get("chapter", "")) or {}
        novel_id = ch_node.get("novel", "")
        rules = [r for r in self._rules(novel_id) if r.get("fact") == fact]
        if not rules:
            return ToolResult.success(data={"ok": True, "no_rule": True,
                                            "violations": []})
        number = self._scene_chapter_number(scene)
        present = fact.lower() in scene.get("body", "").lower()
        violations = []
        if present:
            for r in rules:
                floor = int(r.get("must_not_before") or 0) or \
                    int(r.get("may_know_from_chapter") or 0)
                if number < floor:
                    violations.append({
                        "tier": r.get("tier"), "rule_id": r["id"],
                        "floor": floor, "chapter": number,
                        "verdict": "premature-reveal"})
        return ToolResult.success(data={
            "ok": not violations, "violations": violations})

    @verb(role="transform")
    def reveal_timeline_report(self, novel_id: str,
                               tier: str = "") -> ToolResult:
        """The per-tier "who knows what when" map (transform) — every rule
        sorted by ``may_know_from_chapter`` (the KP §6.2 Reveal-Timeline).

        Inputs: novel_id, tier (optional filter).
        Returns: ``{timeline: [{fact, tier, may_know_from_chapter,
                 must_not_before, channel}], by_tier}``.
        chain_next: ``novel.reveal_gate(novel_id)`` before publication.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        rules = self._rules(novel_id)
        if tier:
            rules = [r for r in rules if r.get("tier") == tier]
        rules.sort(key=lambda r: int(r.get("may_know_from_chapter") or 0))
        by_tier: dict[str, int] = {}
        for r in rules:
            by_tier[r.get("tier", "")] = by_tier.get(r.get("tier", ""), 0) + 1
        return ToolResult.success(data={
            "timeline": [{"fact": r.get("fact"), "tier": r.get("tier"),
                          "may_know_from_chapter":
                              int(r.get("may_know_from_chapter") or 0),
                          "must_not_before":
                              int(r.get("must_not_before") or 0),
                          "channel": r.get("channel", "")} for r in rules],
            "by_tier": by_tier})

    @verb(role="transform")
    def check_veil(self, novel_id: str,
                   veil_term_set: str = DEFAULT_VEIL_TERMS,
                   hold_until_chapter: int = 13) -> ToolResult:
        """The multiplicity-veil scan (transform): any scene/chapter body
        before ``hold_until_chapter`` containing a veil term is a breach.
        Timing complement to Spec 138's naming-form check.

        Inputs: novel_id, veil_term_set (csv), hold_until_chapter.
        Returns: ``{passed, breaches: [{chapter, term, where}]}``.
        chain_next: re-channel the leak into glitch/sensory, re-run.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        terms = [t.strip() for t in veil_term_set.split(",") if t.strip()]
        breaches: list[dict] = []
        for c in self.ctx.neighbors(novel_id, "CHAPTER_OF"):
            number = int(c.get("number", 0))
            if number >= hold_until_chapter:
                continue
            bodies = [("chapter", c.get("body", ""))]
            bodies += [("scene", s.get("body", ""))
                       for s in self.ctx.neighbors(c["id"], "SCENE_OF",
                                                   direction="in")]
            for where, body in bodies:
                for term in terms:
                    if re.search(rf"\b{re.escape(term)}\b", body or ""):
                        breaches.append({"chapter": number, "term": term,
                                         "where": where})
        return ToolResult.success(data={
            "passed": not breaches, "breaches": breaches})

    @verb(role="effect")
    def record_leerstelle(self, scene_id: str, kind: str,
                          note: str = "") -> ToolResult:
        """Register a DELIBERATE Iser gap (effect) — so a reviewer sees the
        indeterminacy is intentional, not a defect.

        Inputs: scene_id, kind (fragmented-perspective |
                contradictory-footnote | temporal-scramble | pronoun-shift),
                note.
        Returns: ``{leerstelle_id, scene_id, kind}``.
        chain_next: ``novel.leerstellen_report(novel_id)``.
        """
        if kind not in LEERSTELLE_KIND:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"kind={kind!r} not in {sorted(LEERSTELLE_KIND)}")
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene {scene_id!r} not found")
        ch = self.ctx.recall(scene.get("chapter", "")) or {}
        lid = self.ctx.record("Leerstelle", {
            "novel": ch.get("novel", ""), "scene_id": scene_id,
            "kind": kind, "note": note})
        self.ctx.link(lid, scene_id, "HAS_GAP")
        self.ctx.link(lid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "leerstelle_id": lid, "scene_id": scene_id, "kind": kind})

    @verb(role="transform")
    def leerstellen_report(self, novel_id: str) -> ToolResult:
        """List the registered deliberate gaps (transform).

        Inputs: novel_id.
        Returns: ``{gaps: [{leerstelle_id, scene_id, kind, note}], count,
                 by_kind}``.
        chain_next: hand the list to the editorial pipeline as
                    do-not-fix context.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        gaps = [g for g in self.ctx.find("Leerstelle")
                if g.get("novel") == novel_id]
        by_kind: dict[str, int] = {}
        for g in gaps:
            by_kind[g.get("kind", "")] = by_kind.get(g.get("kind", ""), 0) + 1
        return ToolResult.success(data={
            "gaps": [{"leerstelle_id": g["id"],
                      "scene_id": g.get("scene_id", ""),
                      "kind": g.get("kind", ""), "note": g.get("note", "")}
                     for g in gaps],
            "count": len(gaps), "by_kind": by_kind})

    @verb(role="transform")
    def reader_function_audit(self, scene_id: str) -> ToolResult:
        """Tag which Iser reader-layers a scene serves (transform): does it
        give the reader something to ASSEMBLE, not just consume? Layers are
        countable-signal heuristics and may overlap.

        Inputs: scene_id.
        Returns: ``{layers: [narratological|phenomenological|operative],
                 signals: {layer: count}}``.
        chain_next: a scene serving NO layer is pure exposition — revise.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene {scene_id!r} not found")
        body = scene.get("body", "")
        low_words = set(re.findall(r"[a-z']+", body.lower()))
        signals = {
            "narratological": len(_NARRATOLOGICAL_RE.findall(body)),
            "phenomenological": len(low_words & _PHENOMENOLOGICAL),
            "operative": len(_OPERATIVE_RE.findall(body)),
        }
        return ToolResult.success(data={
            "layers": sorted(k for k, v in signals.items() if v > 0),
            "signals": signals})

    @verb(role="transform")
    def reveal_gate(self, novel_id: str,
                    veil_term_set: str = DEFAULT_VEIL_TERMS,
                    hold_until_chapter: int = 13) -> ToolResult:
        """Composite pre-publication discipline (transform): passes IFF no
        scene breaches a tier floor for any ruled fact AND the veil holds.

        Inputs: novel_id, veil_term_set, hold_until_chapter.
        Returns: ``{passed, timing_violations, veil}``.
        chain_next: fix the listed leaks; the Spec 122 editorial pipeline.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        timing_violations: list[dict] = []
        chapters = {c["id"] for c in self.ctx.neighbors(novel_id,
                                                        "CHAPTER_OF")}
        scenes = [s for s in self.ctx.find("Scene")
                  if s.get("chapter") in chapters and s.get("body")]
        for rule in self._rules(novel_id):
            fact = rule.get("fact", "")
            for s in scenes:
                res = self.check_reveal_timing(s["id"], fact)
                if res.ok and not res.data.get("ok", True):
                    for v in res.data["violations"]:
                        timing_violations.append(dict(v, scene_id=s["id"],
                                                      fact=fact))
        veil = self.check_veil(novel_id, veil_term_set,
                               hold_until_chapter).data
        return ToolResult.success(data={
            "passed": not timing_violations and veil.get("passed", True),
            "timing_violations": timing_violations, "veil": veil})
