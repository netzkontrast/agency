"""novel.voice — POV voice profiles, the per-character voice signature (Spec 134).

Spec 122's ``check_voice_consistency`` treats the manuscript as ONE voice;
multi-POV novels need per-POV signatures. A ``VoiceProfile`` (one per
character, ``VOICE_OF`` edge) carries the targets; ``score_voice_match``
computes an equal-weighted 0–100 deviation score (OQ2); ``check_pov_voice``
gates a scene against its ``pov_character_id``'s profile;
``voice_drift_report`` / ``voice_drift_gate`` audit the manuscript. Voice
drift is SOFT by doctrine — taboo words are the one hard violation (OQ3:
the character literally said something they wouldn't).
"""
from __future__ import annotations

import re

from agency.capability import verb
from agency.toolresult import Codes, ToolResult

#: Default per-scene pass threshold (spec §Done When — documented tunable).
VOICE_PASS_THRESHOLD = 70

#: Auto-derivation needs this many drafted scenes (OQ1) — below it the
#: author authors the targets directly.
AUTO_DERIVE_MIN_SCENES = 5

_PROFILE_FIELDS = ("vocabulary_floor", "sentence_avg_target",
                   "sentence_avg_stddev", "taboo_words", "signature_phrases",
                   "formality_target", "contractions")

_CONTRACTION_RE = re.compile(r"\b\w+'\w+\b")


def _sentences(body: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]+", body) if s.strip()]


def _words(body: str) -> list[str]:
    return re.findall(r"[A-Za-z']+", body.lower())


def _avg_sentence_len(body: str) -> float:
    sents = _sentences(body)
    if not sents:
        return 0.0
    return sum(len(s.split()) for s in sents) / len(sents)


def _csv(value) -> list[str]:
    return [w.strip().lower() for w in str(value or "").split(",")
            if w.strip()]


class VoiceMixin:
    """Voice cluster — per-character voice profiles + drift checks."""

    def _voice_profile(self, character_id: str) -> dict | None:
        return next((p for p in self.ctx.find("VoiceProfile")
                     if p.get("character") == character_id), None)

    def _character_scenes(self, character_id: str) -> list[dict]:
        return [s for s in self.ctx.find("Scene")
                if s.get("pov_character_id") == character_id]

    @verb(role="effect")
    def create_voice_profile(self, character_id: str,
                             vocabulary_floor: float = 0.0,
                             sentence_avg_target: float = 0.0,
                             sentence_avg_stddev: float = 0.0,
                             taboo_words: str = "",
                             signature_phrases: str = "",
                             formality_target: str = "medium",
                             contractions: bool = True) -> ToolResult:
        """Mint (or overwrite) the character's ``VoiceProfile`` + ``VOICE_OF``
        edge (effect). One profile per character.

        Unset sentence targets are DERIVED from the character's already-
        drafted scenes when ≥ 5 carry bodies (rule 8 — computed defaults,
        not snapshots); below that the author authors them directly.

        Inputs: character_id, vocabulary_floor (min unique-word ratio),
                sentence_avg_target/-stddev, taboo_words (csv),
                signature_phrases (csv), formality_target (low|medium|high),
                contractions (bool).
        Returns: ``{profile_id, character_id, derived_from_scenes}``.
        chain_next: ``novel.check_pov_voice(scene_id)`` per drafted scene.
        """
        if self.ctx.recall(character_id) is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"character_id={character_id!r} not found")
        derived_from = 0
        if not sentence_avg_target:
            bodies = [s.get("body", "") for s in
                      self._character_scenes(character_id) if s.get("body")]
            if len(bodies) >= AUTO_DERIVE_MIN_SCENES:
                avgs = [_avg_sentence_len(b) for b in bodies]
                mean = sum(avgs) / len(avgs)
                var = sum((a - mean) ** 2 for a in avgs) / len(avgs)
                sentence_avg_target = round(mean, 2)
                sentence_avg_stddev = round(max(var ** 0.5, 1.0), 2)
                derived_from = len(bodies)
        props = {
            "character": character_id,
            "vocabulary_floor": vocabulary_floor,
            "sentence_avg_target": sentence_avg_target,
            "sentence_avg_stddev": sentence_avg_stddev,
            "taboo_words": taboo_words,
            "signature_phrases": signature_phrases,
            "formality_target": formality_target,
            "contractions": contractions,
        }
        existing = self._voice_profile(character_id)
        if existing is not None:
            self.ctx.memory.update(existing["id"], props)
            pid = existing["id"]
        else:
            pid = self.ctx.record("VoiceProfile", props)
            self.ctx.link(pid, character_id, "VOICE_OF")
            self.ctx.link(pid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "profile_id": pid, "character_id": character_id,
            "derived_from_scenes": derived_from,
        })

    @verb(role="effect")
    def update_voice_profile(self, character_id: str, **fields) -> ToolResult:
        """Partial update of any profile field (effect).

        Inputs: character_id + any of vocabulary_floor / sentence_avg_target /
                sentence_avg_stddev / taboo_words / signature_phrases /
                formality_target / contractions.
        Returns: ``{profile_id, updated: [fields]}``.
        chain_next: ``novel.score_voice_match`` to re-measure.
        """
        prof = self._voice_profile(character_id)
        if prof is None:
            return ToolResult.failure(
                Codes.NOT_FOUND,
                f"no VoiceProfile for {character_id!r} — create it first")
        updates = {k: v for k, v in fields.items() if k in _PROFILE_FIELDS}
        if updates:
            self.ctx.memory.update(prof["id"], updates)
        return ToolResult.success(data={
            "profile_id": prof["id"], "updated": sorted(updates)})

    @verb(role="transform")
    def get_voice_profile(self, character_id: str) -> ToolResult:
        """Read the character's voice profile (transform).

        Inputs: character_id.
        Returns: the profile dict (all fields) or NOT_FOUND.
        chain_next: ``novel.score_voice_match(character_id, body)``.
        """
        prof = self._voice_profile(character_id)
        if prof is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"no VoiceProfile for {character_id!r}")
        return ToolResult.success(data=dict(prof))

    @verb(role="transform")
    def score_voice_match(self, character_id: str, body: str) -> ToolResult:
        """Score prose against the character's profile — 0–100, equal-weighted
        across the SET fields (transform; OQ2 v1). Taboo hits are hard
        violations (OQ3); empty fields are skipped, never penalised.

        Inputs: character_id, body (the prose to score).
        Returns: ``{score, deviations: [{field, target, actual, severity}]}``.
        chain_next: revise the prose, or ``novel.update_voice_profile`` if
                    the profile itself is wrong.
        """
        prof = self._voice_profile(character_id)
        if prof is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"no VoiceProfile for {character_id!r}")
        words = _words(body)
        components: list[float] = []
        deviations: list[dict] = []

        target = float(prof.get("sentence_avg_target") or 0)
        stddev = float(prof.get("sentence_avg_stddev") or 0)
        if target > 0:
            actual = _avg_sentence_len(body)
            spread = max(stddev, 1.0)
            comp = max(0.0, 1.0 - abs(actual - target) / (2 * spread))
            components.append(comp)
            if comp < 1.0:
                deviations.append({"field": "sentence_avg", "target": target,
                                   "actual": round(actual, 2),
                                   "severity": "soft"})

        floor = float(prof.get("vocabulary_floor") or 0)
        if floor > 0 and words:
            ratio = len(set(words)) / len(words)
            components.append(min(1.0, ratio / floor))
            if ratio < floor:
                deviations.append({"field": "vocabulary_floor",
                                   "target": floor,
                                   "actual": round(ratio, 3),
                                   "severity": "soft"})

        taboo = _csv(prof.get("taboo_words"))
        if taboo:
            hits = sorted({w for w in words if w in taboo})
            components.append(0.0 if hits else 1.0)
            if hits:
                deviations.append({"field": "taboo_words", "target": "absent",
                                   "actual": ",".join(hits),
                                   "severity": "hard"})

        phrases = _csv(prof.get("signature_phrases"))
        if phrases:                                   # opt-in field
            low = body.lower()
            found = [p for p in phrases if p in low]
            components.append(1.0 if found else 0.5)  # absence is a nudge
            if not found:
                deviations.append({"field": "signature_phrases",
                                   "target": ",".join(phrases),
                                   "actual": "none present",
                                   "severity": "soft"})

        if prof.get("contractions") is False:
            has = bool(_CONTRACTION_RE.search(body))
            components.append(0.0 if has else 1.0)
            if has:
                deviations.append({"field": "contractions", "target": False,
                                   "actual": True, "severity": "soft"})

        score = round(100 * (sum(components) / len(components))) \
            if components else 100
        return ToolResult.success(data={
            "score": score, "deviations": deviations})

    @verb(role="transform")
    def check_pov_voice(self, scene_id: str) -> ToolResult:
        """Gate a scene's body against its POV character's profile
        (transform). Reads ``Scene.pov_character_id`` + ``Scene.body``.

        Inputs: scene_id.
        Returns: ``{passed, score, deviations, character_id}`` — pass
                 threshold 70 (``VOICE_PASS_THRESHOLD``).
        chain_next: revise the scene, or ``novel.voice_drift_report`` for
                    the manuscript view.
        """
        scene = self.ctx.recall(scene_id)
        if scene is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"scene_id={scene_id!r} not found")
        char = scene.get("pov_character_id", "")
        if not char:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"scene {scene_id!r} has no pov_character_id")
        scored = self.score_voice_match(char, scene.get("body", ""))
        if not scored.ok:
            return scored
        data = scored.data
        return ToolResult.success(data={
            "passed": data["score"] >= VOICE_PASS_THRESHOLD,
            "score": data["score"], "deviations": data["deviations"],
            "character_id": char,
        })

    def _novel_pov_scenes(self, novel_id: str) -> list[dict]:
        chapters = {c["id"] for c in self.ctx.neighbors(novel_id, "CHAPTER_OF")}
        return [s for s in self.ctx.find("Scene")
                if s.get("chapter") in chapters
                and s.get("pov_character_id")]

    @verb(role="transform")
    def voice_drift_report(self, novel_id: str) -> ToolResult:
        """Full-manuscript voice audit (transform): every POV scene scored
        against its character's profile, worst-first per character; the
        bottom 10% manuscript-wide flagged as outliers.

        Inputs: novel_id.
        Returns: ``{by_character: {character_id: [{scene_id, score}]},
                 manuscript_outliers: [{scene_id, score}]}``.
        chain_next: revise the outlier scenes; ``novel.voice_drift_gate``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        by_char: dict[str, list[dict]] = {}
        scored_all: list[dict] = []
        for s in self._novel_pov_scenes(novel_id):
            char = s["pov_character_id"]
            if self._voice_profile(char) is None:
                continue
            res = self.score_voice_match(char, s.get("body", ""))
            row = {"scene_id": s["id"], "score": res.data["score"]}
            by_char.setdefault(char, []).append(row)
            scored_all.append(row)
        for rows in by_char.values():
            rows.sort(key=lambda r: r["score"])
        scored_all.sort(key=lambda r: r["score"])
        n_out = max(1, len(scored_all) // 10) if scored_all else 0
        return ToolResult.success(data={
            "by_character": by_char,
            "manuscript_outliers": scored_all[:n_out],
        })

    @verb(role="transform")
    def voice_drift_gate(self, novel_id: str,
                         min_score: int = VOICE_PASS_THRESHOLD) -> ToolResult:
        """Composite gate: passes IFF every POV scene with a profiled
        character scores ≥ ``min_score`` (transform). The editorial-pipeline
        Slice-2 hook to ``line_gate``.

        Inputs: novel_id, min_score (default 70).
        Returns: ``{passed, checked, failing: [{scene_id, character_id,
                 score}]}``.
        chain_next: revise failing scenes, re-run; ``novel.line_gate``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        failing: list[dict] = []
        checked = 0
        for s in self._novel_pov_scenes(novel_id):
            char = s["pov_character_id"]
            if self._voice_profile(char) is None:
                continue
            checked += 1
            res = self.score_voice_match(char, s.get("body", ""))
            if res.data["score"] < min_score:
                failing.append({"scene_id": s["id"], "character_id": char,
                                "score": res.data["score"]})
        return ToolResult.success(data={
            "passed": not failing, "checked": checked, "failing": failing})
