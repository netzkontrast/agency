"""novel.prose — Prose cluster — driver-free prose analysis + editorial pipeline + craft gates (Spec 104/122).

Spec 286 P3 — extracted verbatim from ``novel/_main.py``; behaviour-frozen
relocation into a cluster mixin composed into the single NovelCapability.
"""
from __future__ import annotations

from agency.capability import verb
from agency.toolresult import ToolResult
from .._main import (
    CONTENT_WARNINGS,
    FILTER_WORDS,
    FILTER_WORD_DENSITY_THRESHOLD,
    FLOWERY_ATTRIBUTIONS,
    PLAIN_ATTRIBUTIONS,
    TELLING_VERBS,
    _SENSITIVITY_LEXICON,
    _SENTENCE_STARTERS,
    _count_sentences,
    _levenshtein,
    _syllables_word,
    _word_tokens,
)


class ProseMixin:
    """Prose cluster — driver-free prose analysis + editorial pipeline + craft gates (Spec 104/122)."""

    @verb(role="transform")
    def count_words(self, body: str) -> ToolResult:
        """Word + char counter (transform, driver-free).

        Inputs: body. Returns: ``{word_count, char_count}``.
        chain_next: ``novel.analyze_readability`` for prosody metrics.
        """
        return ToolResult.success(data={
            "word_count": len(_word_tokens(body)),
            "char_count": len(body.strip()),
        })

    @verb(role="transform")
    def analyze_readability(self, body: str) -> ToolResult:
        """Flesch Reading Ease for prose (transform, driver-free).

        Score 0-100; conversational lands ~60-70. Formula:
        206.835 − 1.015 × (words/sentences) − 84.6 × (syllables/words).
        Inputs: body (non-empty). Returns: ``{flesch, words, sentences,
        syllables}``.
        chain_next: ``novel.check_filter_words`` for show-don't-tell pass.
        """
        if not body.strip():
            return ToolResult.failure(
                "INVALID_ARGUMENT", "body is empty")
        words = _word_tokens(body)
        word_n = len(words)
        sent_n = _count_sentences(body)
        syll_n = sum(_syllables_word(w) for w in words)
        flesch = (206.835
                  - 1.015 * (word_n / max(sent_n, 1))
                  - 84.6 * (syll_n / max(word_n, 1)))
        return ToolResult.success(data={
            "flesch": round(flesch, 2),
            "words": word_n,
            "sentences": sent_n,
            "syllables": syll_n,
        })

    @verb(role="transform")
    def check_filter_words(self, body: str,
                            threshold: float = FILTER_WORD_DENSITY_THRESHOLD
                            ) -> ToolResult:
        """Filter-word density check (transform, show-don't-tell).

        Scans for canonical filter words (really / just / very / etc.).
        Density = filter-count / total-words; passes when ≤ threshold.

        Inputs: body, threshold (default 0.05).
        Returns: ``{passed, filter_count, total_words, density, offenders}``.
        chain_next: ``novel.set_chapter_status`` once density is in range.
        """
        words_lower = [w.lower() for w in _word_tokens(body)]
        total = len(words_lower)
        offenders = [w for w in words_lower if w in FILTER_WORDS]
        density = (len(offenders) / total) if total else 0.0
        return ToolResult.success(data={
            "passed": density <= threshold,
            "filter_count": len(offenders),
            "total_words": total,
            "density": round(density, 4),
            "offenders": sorted(set(offenders)),
        })

    @verb(role="transform")
    def scan_proper_nouns(self, body: str) -> ToolResult:
        """Extract proper nouns (Title-Case words, sentence-starter words filtered) (transform).

        Catches character + place names for continuity / world-bible
        cross-reference. Filters out common sentence-starter words
        ("The", "She", "Then", etc.) which would be Title-Case at
        position 1 of every sentence — a false-positive source.

        Inputs: body.
        Returns: ``{proper_nouns: [sorted unique], count}``.
        chain_next: ``novel.check_continuity`` (Slice 3+) for the cross-check.
        """
        nouns: set[str] = set()
        for w in body.split():
            w_clean = w.strip(".,;:!?\"'()")
            if (w_clean and w_clean[0].isupper()
                    and w_clean[1:].islower()
                    and w_clean.lower() not in _SENTENCE_STARTERS):
                nouns.add(w_clean)
        return ToolResult.success(data={
            "proper_nouns": sorted(nouns),
            "count": len(nouns),
        })

    @verb(role="transform")
    def check_dialogue_attribution(self, body: str) -> ToolResult:
        """Dialogue-tag check — plain ('said') vs flowery (transform).

        Counts plain attributions (`said`/`asked`/etc.) vs flowery ones
        (`exclaimed`/`muttered`/etc.). Strunk & White: invisible is
        better. Passes when `flowery_count == 0`.

        Inputs: body.
        Returns: ``{passed, plain_count, flowery_count, flowery_hits}``.
        chain_next: revise flowery hits then re-check.
        """
        words = [w.lower() for w in _word_tokens(body)]
        plain = [w for w in words if w in PLAIN_ATTRIBUTIONS]
        flowery = [w for w in words if w in FLOWERY_ATTRIBUTIONS]
        return ToolResult.success(data={
            "passed": len(flowery) == 0,
            "plain_count": len(plain),
            "flowery_count": len(flowery),
            "flowery_hits": sorted(set(flowery)),
        })

    @verb(role="transform")
    def check_show_dont_tell(self, body: str) -> ToolResult:
        """Telling-verb scan — interior-monologue tells (transform).

        Distinct from ``check_filter_words`` (which scans adverbs).
        Flags ``felt``/``realized``/``noticed``/etc. — verbs that
        NARRATE emotion instead of dramatizing it.

        Inputs: body.
        Returns: ``{passed, tell_count, tells}``.
        chain_next: rewrite tells into action / sensory detail.
        """
        words = [w.lower() for w in _word_tokens(body)]
        hits = [w for w in words if w in TELLING_VERBS]
        return ToolResult.success(data={
            "passed": len(hits) == 0,
            "tell_count": len(hits),
            "tells": sorted(set(hits)),
        })

    @verb(role="transform")
    def check_content_warnings(self, body: str) -> ToolResult:
        """Content-warning category scanner (transform, driver-free).

        Scans body for canonical content-warning keyword stems
        (violence / sex / substance / death / self-harm). Returns
        matched categories so publishers + reviewers can flag in
        front-matter.

        Inputs: body.
        Returns: ``{warnings: [categories], hits: {category: [keywords]}}``.
        chain_next: add to manuscript front-matter or trigger
                    sensitivity-reader workflow (Slice 3).
        """
        words_lower = {w.lower() for w in _word_tokens(body)}
        warnings: list[str] = []
        hits: dict[str, list[str]] = {}
        for category, lexicon in CONTENT_WARNINGS.items():
            matched = sorted(words_lower & lexicon)
            if matched:
                warnings.append(category)
                hits[category] = matched
        return ToolResult.success(data={
            "warnings": sorted(warnings),
            "hits": hits,
        })

    @verb(role="transform")
    def check_voice_consistency(self, bodies: list[str],
                                  z_threshold: float = 2.0) -> ToolResult:
        """Per-chapter voice-signature outlier check (transform).

        Computes a 3-feature signature per body (avg sentence length /
        filter-word density / flowery-attribution density), then flags
        any chapter whose feature z-score exceeds ``z_threshold`` (default
        2.0 — the documented tunable per spec Open Q1).

        Inputs: bodies (list[str] — one per chapter, in order),
                z_threshold (float — std deviations).
        Returns: ``{passed, signatures, outliers: [{index, feature, z}]}``.
        chain_next: ``novel.line_gate`` for per-chapter line-level scrutiny.
        """
        sigs: list[dict] = []
        for b in bodies:
            tokens = _word_tokens(b)
            total = len(tokens) or 1
            sentences = [s for s in b.split(".") if s.strip()]
            avg_sl = (sum(len(_word_tokens(s)) for s in sentences)
                      / max(1, len(sentences)))
            filter_density = sum(1 for w in tokens
                                  if w.lower() in FILTER_WORDS) / total
            flowery_density = sum(1 for w in tokens
                                   if w.lower() in FLOWERY_ATTRIBUTIONS) / total
            sigs.append({
                "avg_sentence_length": round(avg_sl, 2),
                "filter_density": round(filter_density, 4),
                "flowery_density": round(flowery_density, 4),
            })
        outliers: list[dict] = []
        if len(sigs) >= 3:
            for feat in ("avg_sentence_length", "filter_density",
                         "flowery_density"):
                vals = [s[feat] for s in sigs]
                mean = sum(vals) / len(vals)
                var = sum((v - mean) ** 2 for v in vals) / len(vals)
                std = var ** 0.5
                if std == 0:
                    continue
                for i, v in enumerate(vals):
                    z = abs(v - mean) / std
                    if z > z_threshold:
                        outliers.append({"index": i, "feature": feat,
                                          "z": round(z, 2)})
        return ToolResult.success(data={
            "passed": not outliers,
            "signatures": sigs,
            "outliers": outliers,
        })

    @verb(role="transform")
    def check_pov_consistency(self, novel_id: str) -> ToolResult:
        """Per-chapter POV uniformity check across scenes (transform).

        Walks each chapter's Scene nodes via SCENE_OF and groups POV
        values. A chapter with > 1 distinct POV (excluding scenes that
        declare ``pov=""``) is a flagged break.

        Inputs: novel_id.
        Returns: ``{passed, per_chapter: [{chapter_id, povs, mixed}]}``.
        chain_next: ``novel.line_gate``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        per_chapter: list[dict] = []
        any_mixed = False
        for c in sorted(chapters, key=lambda c: c.get("number", 0)):
            cid = c.get("id", "")
            scenes = self.ctx.neighbors(cid, "SCENE_OF")
            povs = sorted({s.get("pov") for s in scenes if s.get("pov")})
            mixed = len(povs) > 1
            if mixed:
                any_mixed = True
            per_chapter.append({
                "chapter_id": cid, "number": c.get("number", 0),
                "povs": povs, "mixed": mixed,
            })
        return ToolResult.success(data={
            "passed": not any_mixed,
            "per_chapter": per_chapter,
        })

    @verb(role="transform")
    def check_continuity(self, novel_id: str) -> ToolResult:
        """Cross-chapter proper-noun continuity check (transform).

        Scans each chapter body for proper nouns; flags two patterns:
        (1) names appearing in exactly ONE chapter (likely typos or
        deleted characters), (2) close-distance spelling pairs (e.g.
        Lara/Laura — Levenshtein ≤ 2 + both ≥ 4 chars).

        Inputs: novel_id.
        Returns: ``{passed, single_chapter: [{name, chapter}], close_pairs}``.
        chain_next: ``novel.copy_gate``.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(
            self.ctx.neighbors(novel_id, "CHAPTER_OF"),
            key=lambda c: c.get("number", 0))
        registry: dict[str, set[int]] = {}
        for c in chapters:
            body = c.get("body", "") or ""
            scan_result = self.check_scan_proper_nouns_helper(body)
            for name in scan_result:
                registry.setdefault(name, set()).add(c.get("number", 0))
        all_names = sorted(registry.keys())
        single_chapter = [
            {"name": n, "chapter": next(iter(registry[n]))}
            for n in all_names if len(registry[n]) == 1
        ]
        close_pairs: list[dict] = []
        for i, a in enumerate(all_names):
            for b in all_names[i + 1:]:
                if len(a) >= 4 and len(b) >= 4 and _levenshtein(a, b) <= 2:
                    close_pairs.append({"a": a, "b": b})
        return ToolResult.success(data={
            "passed": not single_chapter and not close_pairs,
            "single_chapter": single_chapter,
            "close_pairs": close_pairs,
        })

    def check_scan_proper_nouns_helper(self, body: str) -> list[str]:
        """Same scan as `scan_proper_nouns` verb — extracted for in-process reuse."""
        tokens = body.split()
        return sorted({t.strip(".,!?;:") for t in tokens
                       if t and t[0].isupper() and t.strip(".,!?;:").isalpha()
                       and t.strip(".,!?;:") not in _SENTENCE_STARTERS})

    @verb(role="transform")
    def check_sensitivity(self, body: str) -> ToolResult:
        """Sensitivity-topic advisory scan (transform, WARN-severity).

        Extends content-warnings with a documented sensitivity lexicon
        covering mental-health, identity, and trauma-adjacent terms.
        Always passes — sensitivity is informational, not blocking
        (the spec's "exact-severity discipline" — advisory checks never
        gate). Emits ``warnings`` array for the editorial report.

        Inputs: body.
        Returns: ``{passed: True, warnings: [{category, term}]}``.
        chain_next: ``novel.developmental_gate`` (advisory only).
        """
        words = {w.lower() for w in _word_tokens(body)}
        warnings: list[dict] = []
        for category, terms in _SENSITIVITY_LEXICON.items():
            for term in terms:
                if term in words:
                    warnings.append({"category": category, "term": term})
        return ToolResult.success(data={
            "passed": True, "warnings": warnings,
        })

    @verb(role="act")
    def chapter_report_full(self, chapter_id: str) -> ToolResult:
        """Full editorial dashboard for one chapter (act).

        Runs every prose check over the chapter's body and aggregates the
        verdicts; records a ``chapter-report`` Artefact + SERVES intent.

        Inputs: chapter_id.
        Returns: ``{chapter_id, checks: {...}, artefact_id}``.
        chain_next: ``novel.line_gate`` to roll up to a manuscript verdict.
        """
        chapter = self.ctx.recall(chapter_id)
        if chapter is None:
            return ToolResult.failure(
                "NOT_FOUND", f"chapter_id={chapter_id!r} not found")
        body = chapter.get("body", "") or ""
        checks = {
            "readability": self.ctx.call("novel", "analyze_readability",
                                          body=body),
            "filter_words": self.ctx.call("novel", "check_filter_words",
                                           body=body),
            "show_dont_tell": self.ctx.call("novel", "check_show_dont_tell",
                                             body=body),
            "dialogue_attribution": self.ctx.call(
                "novel", "check_dialogue_attribution", body=body),
            "content_warnings": self.ctx.call(
                "novel", "check_content_warnings", body=body),
            "sensitivity": self.ctx.call("novel", "check_sensitivity",
                                          body=body),
        }
        aid = self.ctx.record("Artefact", {
            "kind": "chapter-report",
            "chapter_id": chapter_id,
        })
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        return ToolResult.success(data={
            "chapter_id": chapter_id,
            "checks": checks,
            "artefact_id": aid,
        })

    @verb(role="effect")
    def developmental_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: structure-level editorial readiness (effect).

        Combines storyform coherence + chapter contiguity + at-least-one
        outlined chapter. Mirrors music's lyric-gate composition pattern.

        Inputs: novel_id.
        Returns: ``{passed, checks}`` or typed GATE_FAILED.
        chain_next: ``novel.line_gate`` once developmental edits are done.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        coh = self.ctx.call("novel", "manuscript_coherence_check",
                             novel_id=novel_id)
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        checks = {
            "chapter_contiguity": bool(coh.get("passed")),
            "has_chapters": bool(chapters),
            "storyform_present": bool([
                s for s in self.ctx.find("Storyform")
                if s.get("novel") == novel_id
            ]),
        }
        if not all(checks.values()):
            return ToolResult.failure(
                "GATE_FAILED",
                f"developmental: missing "
                f"{[k for k, v in checks.items() if not v]}")
        return ToolResult.success(data={"passed": True, "checks": checks})

    @verb(role="effect")
    def line_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: prose-level editorial readiness (effect).

        Every chapter must pass filter-word density + show-don't-tell +
        dialogue attribution thresholds. POV consistency across scenes
        is required too. The exact-severity discipline: advisory
        (sensitivity) does NOT block; structural failures do.

        Inputs: novel_id.
        Returns: ``{passed, checks, per_chapter}`` or typed GATE_FAILED.
        chain_next: ``novel.copy_gate`` once line edits are done.
        """
        _, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        chapters = sorted(
            self.ctx.neighbors(novel_id, "CHAPTER_OF"),
            key=lambda c: c.get("number", 0))
        per_chapter: list[dict] = []
        all_pass = True
        for c in chapters:
            body = c.get("body", "") or ""
            fw = self.ctx.call("novel", "check_filter_words", body=body)
            sdt = self.ctx.call("novel", "check_show_dont_tell", body=body)
            da = self.ctx.call("novel", "check_dialogue_attribution",
                                body=body)
            ok = (fw.get("passed") and sdt.get("passed")
                  and da.get("passed"))
            if not ok:
                all_pass = False
            per_chapter.append({
                "chapter_id": c.get("id", ""),
                "number": c.get("number", 0),
                "filter_words": fw.get("passed"),
                "show_dont_tell": sdt.get("passed"),
                "dialogue_attribution": da.get("passed"),
                "passed": ok,
            })
        pov = self.ctx.call("novel", "check_pov_consistency",
                             novel_id=novel_id)
        all_pass = all_pass and pov.get("passed", False)
        checks = {
            "all_chapters_line_clean": all([c["passed"] for c in per_chapter]),
            "pov_consistent": pov.get("passed", False),
        }
        if not all_pass:
            return ToolResult.failure(
                "GATE_FAILED",
                f"line: {[k for k, v in checks.items() if not v]}")
        return ToolResult.success(data={
            "passed": True, "checks": checks, "per_chapter": per_chapter,
        })

    @verb(role="effect")
    def copy_gate(self, novel_id: str) -> ToolResult:
        """Composite gate: surface-level editorial readiness (effect).

        Continuity (proper-noun registry) + content warnings DECLARED
        on the novel + readability in genre band (advisory). Continuity
        + content-warning declaration are blocking; readability emits
        warning only.

        Inputs: novel_id.
        Returns: ``{passed, checks, warnings}`` or typed GATE_FAILED.
        chain_next: ``novel.publish_ready_gate``.
        """
        novel, fail = self._require_novel(novel_id)
        if fail is not None:
            return fail
        cont = self.ctx.call("novel", "check_continuity", novel_id=novel_id)
        cw_declared = bool(novel.get("content_warnings"))
        chapters = self.ctx.neighbors(novel_id, "CHAPTER_OF")
        readability_warnings: list[str] = []
        for c in chapters:
            body = c.get("body", "") or ""
            if not body:
                continue
            r = self.ctx.call("novel", "analyze_readability", body=body)
            flesch = r.get("flesch_reading_ease", 60.0)
            if flesch < 50 or flesch > 90:
                readability_warnings.append(
                    f"chapter {c.get('number', '?')}: flesch={flesch}")
        checks = {
            "continuity_clean": cont.get("passed", False),
            "content_warnings_declared": cw_declared,
        }
        if not all(checks.values()):
            return ToolResult.failure(
                "GATE_FAILED",
                f"copy: {[k for k, v in checks.items() if not v]}")
        return ToolResult.success(data={
            "passed": True, "checks": checks,
            "readability_warnings": readability_warnings,
        })
