# agency-scaffold: v1
"""music lyrics cluster — text/prosody transforms + composite lyric gates.

Spec 095 — 13 transforms + the lyric composite gate verbs (prosody ·
pronunciation · repetition · explicit · name-exposure), plus the 007 text
verbs (count_syllables · lyric_report). Relocated VERBATIM from ``_main.py``
per Spec 094 design §"Module layout" (Spec 286 Phase 3).

Pure relocation — same decorator args, signatures, bodies, provenance.
"""
from __future__ import annotations

from agency.capability import requires_driver, verb
from agency.toolresult import ToolResult

from ._base import (
    _MIN_RHYME_GROUPS,
    _SYLLABLE_TOLERANCE,
    _MusicBase,
    _syllables,
)


class LyricsCluster(_MusicBase):
    # ───────── text cluster (transform, driver-free, deterministic) ─────────
    @verb(role="transform")
    def count_syllables(self, word: str) -> ToolResult:
        """Count syllables in a word — deterministic, driver-free text math.

        Inputs: word. Returns: ``{word, syllables}``. chain_next: ``music.lyric_report``.
        """
        return ToolResult.success(data={"word": word, "syllables": _syllables(word)})

    # ───────── lyrics cluster (act via TextDriver, produces lyric-report) ─────────
    @verb(role="act")
    @requires_driver("music_text", as_="text")
    def lyric_report(self, album: str, lyrics: str, *, text) -> ToolResult:
        """Analyze a lyric sheet's syllable load per line via the TextDriver (act).

        Inputs: album, lyrics.
        Returns: ``{result, artefact}`` where artefact.kind = ``lyric-report`` (PRODUCES edge).
        chain_next: feed the report into the mix/master step.
        """
        lines = [ln for ln in lyrics.splitlines() if ln.strip()]
        per_line = [sum(text.syllables(w) for w in ln.split()) for ln in lines]
        body = (f"# Lyric report: {album}\nlines: {len(lines)}\n"
                f"syllables/line: {per_line}\n")
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "lyric-report", "album": album, "lines": len(lines),
            "syllables_per_line": per_line, "body": body}})

    # ════════════════════════════════════════════════════════════════════════
    # Spec 095 — lyrics cluster: 13 NEW transforms + 4 composite gate verbs
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="transform")
    @requires_driver("music_text", as_="text")
    def analyze_rhyme_scheme(self, lyrics: str, *, text) -> ToolResult:
        """Build a rhyme scheme (A/B/C labels) over the lyric lines (transform).

        Inputs: lyrics (multi-line text).
        Returns: ``{scheme, groups, self_rhymes}`` via TextDriver.rhyme_scheme.
        chain_next: ``music.prosody_gate`` for an integrated prosody check.
        """
        lines = [ln for ln in lyrics.splitlines() if ln.strip()]
        return ToolResult.success(data=text.rhyme_scheme(lines))

    @verb(role="transform")
    @requires_driver("music_text", as_="drv")
    def analyze_readability(self, text_: str, *, drv) -> ToolResult:
        """Flesch-Kincaid-shaped readability over the lyric text (transform).

        Inputs: text_ (multi-line — `text` is a builtin so kw is suffixed).
        Returns: ``{grade_level, avg_words_per_sentence, avg_syllables_per_word}``.
        chain_next: pair with ``music.analyze_rhyme_scheme`` for a full prosody view.
        """
        return ToolResult.success(data=drv.readability(text_))

    @verb(role="transform")
    @requires_driver("music_text", as_="drv")
    def check_pronunciation(self, lyrics: str, *, drv) -> ToolResult:
        """Flag words requiring forced pronunciation per the bundled guide (transform).

        Inputs: lyrics (multi-line text).
        Returns: ``{findings: [{word, suggested, severity}], count}``.
        chain_next: ``music.pronunciation_gate`` to gate the lyric-writing skill.
        """
        findings = drv.pronunciation(lyrics)
        return ToolResult.success(data={"findings": findings,
                                        "count": len(findings)})

    @verb(role="transform")
    @requires_driver("music_text", as_="drv")
    def check_homographs(self, lyrics: str, *, drv) -> ToolResult:
        """Flag words with multiple legitimate pronunciations (transform).

        Inputs: lyrics.
        Returns: ``{findings: [{word, ambiguous_readings, severity}], count}``.
        chain_next: ``music.pronunciation_gate``.
        """
        findings = drv.homographs(lyrics)
        return ToolResult.success(data={"findings": findings,
                                        "count": len(findings)})

    @verb(role="transform")
    @requires_driver("music_text", as_="drv")
    def check_streaming_lyrics(self, lyrics: str,
                                platform: str = "spotify", *, drv) -> ToolResult:
        """Check the lyric body for platform-incompatible markup (transform).

        Inputs: lyrics, platform (default ``spotify``).
        Returns: ``{platform, bracket_tags, safe, fix?}``.
        chain_next: strip bracket tags before upload if ``safe=False``.
        """
        return ToolResult.success(data=drv.streaming_safe(lyrics, platform))

    @verb(role="transform")
    @requires_driver("music_text", as_="drv")
    def check_cross_track_repetition(self, tracks: list[str], *, drv) -> ToolResult:
        """Flag lyric lines repeated across multiple album tracks (transform).

        Inputs: tracks (list of lyric bodies, one per track).
        Returns: ``{repeated_lines, track_count, examples}``.
        chain_next: ``music.repetition_gate``.
        """
        return ToolResult.success(data=drv.cross_track(tracks))

    @verb(role="transform")
    @requires_driver("music_text", as_="drv")
    def check_explicit_content(self, lyrics: str, *, drv) -> ToolResult:
        """Classify lyrics as clean / suggestive / explicit (transform).

        Inputs: lyrics.
        Returns: ``{rating, explicit_words, suggestive_words}``.
        chain_next: ``music.explicit_gate``.
        """
        return ToolResult.success(data=drv.explicit(lyrics))

    @verb(role="transform")
    @requires_driver("music_text", as_="drv")
    def extract_distinctive_phrases(self, lyrics: str,
                                     corpus: list[str] | None = None, *, drv) -> ToolResult:
        """Return novel tri-grams (not in corpus) from the lyrics (transform).

        Inputs: lyrics, corpus (list of comparison lyric bodies — defaults to []).
        Returns: ``{phrases: [...], count}``.
        chain_next: use distinctive phrases as marketing hooks.
        """
        phrases = drv.distinctive_phrases(lyrics, corpus or [])
        return ToolResult.success(data={"phrases": phrases,
                                        "count": len(phrases)})

    @verb(role="transform")
    @requires_driver("music_text", as_="drv")
    def extract_section(self, lyrics: str, label: str, *, drv) -> ToolResult:
        """Extract the body under a ``[<label>]`` section tag (transform).

        Inputs: lyrics, label (e.g. ``Verse 1``).
        Returns: ``{section, body}``.
        chain_next: pass the section body to a per-section transform.
        """
        body = drv.extract_section(lyrics, label)
        return ToolResult.success(data={"section": label, "body": body})

    @verb(role="transform")
    @requires_driver("music_text", as_="drv")
    def validate_section_structure(self, lyrics: str, *, drv) -> ToolResult:
        """Validate section tag well-formedness (Title Case in brackets) (transform).

        Inputs: lyrics.
        Returns: ``{ok, findings: [{line, tag, issue, severity}]}``.
        chain_next: fix flagged tags before the prosody pass.
        """
        return ToolResult.success(data=drv.validate_sections(lyrics))

    @verb(role="transform")
    @requires_driver("music_text", as_="drv")
    def scan_artist_names(self, lyrics: str,
                          allow: list[str] | None = None, *, drv) -> ToolResult:
        """Scan for accidental artist-name drops against the blocklist (transform).

        Inputs: lyrics, allow (allowlist of explicitly permitted artist mentions).
        Returns: ``{hits: [{name, severity, fix}], count}``.
        chain_next: replace flagged names or extend the allowlist.
        """
        hits = drv.scan_artist_names(lyrics, allow or [])
        return ToolResult.success(data={"hits": hits, "count": len(hits)})

    @verb(role="transform")
    def check_name_exposure(self, text: str,
                            roster: list[str] | None = None) -> ToolResult:
        """Scan text for forbidden roster names (driver-free, deterministic) (transform).

        Spec 119 — F6 from Spec 117. A personal/character name (alter, real
        person) must never reach a public-facing music field. Case-insensitive
        WHOLE-WORD match so "Lex" does not fire inside "lexicon". When `roster`
        is None it defaults to the project's ``name_exposure.blocklist`` from
        MusicConfig; an empty roster yields zero hits (no-op).

        Inputs: text, roster (defaults to config blocklist).
        Returns: ``{hits: [{name, count}], count, roster_size}``.
        chain_next: ``music.name_exposure_gate`` to block on a hit.
        """
        if roster is None:
            from ..config import MusicConfig
            roster = list(MusicConfig.load().name_exposure_blocklist)
        hits = self._name_exposure_hits(text, roster)
        return ToolResult.success(data={"hits": hits,
                                        "count": len(hits),
                                        "roster_size": len(roster)})

    @verb(role="transform")
    @requires_driver("music_text", as_="drv")
    def check_voice_tells(self, lyrics: str, *, drv) -> ToolResult:
        """AI-tell rule-based detector (advisory only — no gate impact) (transform).

        Inputs: lyrics.
        Returns: ``{findings: [{heuristic, severity, fix}], count}``.
        chain_next: rewrite flagged lines for idiosyncrasy.
        """
        findings = drv.voice_tells(lyrics)
        return ToolResult.success(data={"findings": findings,
                                        "count": len(findings)})

    # ── 4 composite gate verbs — called by the lyric-writing skill ──

    @verb(role="effect")
    @requires_driver("music_text", as_="drv")
    def prosody_gate(self, lifecycle_id: str, lyrics: str,
                     syllable_target: int = 0, *, drv) -> ToolResult:
        """Computed prosody gate — composes rhyme + syllable checks (effect).

        Passes iff rhyme_scheme has ≥ 2 groups (real rhyming, not all-A) AND
        (when syllable_target > 0) avg line syllables within ±2 of target.
        Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

        Inputs: lifecycle_id, lyrics, syllable_target (0 = skip).
        Returns: ``{gate, passed, evidence}`` or typed GATE_FAILED.
        chain_next: on failure, revise lyrics + re-check.
        """
        lines = [ln for ln in lyrics.splitlines() if ln.strip()]
        rhyme = drv.rhyme_scheme(lines)
        problems = []
        if rhyme["groups"] < _MIN_RHYME_GROUPS:
            problems.append(
                f"rhyme_scheme has {rhyme['groups']} group(s) "
                f"(min {_MIN_RHYME_GROUPS})")
        if syllable_target > 0:
            stats = drv.stats(lyrics)
            avg = stats["syllables"] / max(stats["lines"], 1)
            if abs(avg - syllable_target) > _SYLLABLE_TOLERANCE:
                problems.append(
                    f"avg syllables {avg:.1f} differs from target "
                    f"{syllable_target} by > {_SYLLABLE_TOLERANCE}")
        passed = not problems
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="prosody", passed=passed,
                      evidence="ok" if passed else "; ".join(problems))
        if not passed:
            return ToolResult.failure("GATE_FAILED",
                                      f"prosody: {'; '.join(problems)}")
        return ToolResult.success(data={"gate": "prosody", "passed": True,
                                        "evidence": rhyme})

    @verb(role="effect")
    @requires_driver("music_text", as_="drv")
    def pronunciation_gate(self, lifecycle_id: str,
                            lyrics: str, *, drv) -> ToolResult:
        """Computed pronunciation gate — composes pronunciation + homograph (effect).

        Passes iff zero pronunciation findings AND zero homograph findings.
        Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

        Inputs: lifecycle_id, lyrics.
        Returns: ``{gate, passed, evidence}`` or typed GATE_FAILED.
        chain_next: resolve flagged words then re-check.
        """
        prn = drv.pronunciation(lyrics)
        hom = drv.homographs(lyrics)
        passed = not prn and not hom
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="pronunciation", passed=passed,
                      evidence=("clean" if passed else
                                f"pronunciation:{len(prn)} homograph:{len(hom)}"))
        if not passed:
            return ToolResult.failure(
                "GATE_FAILED",
                f"pronunciation: {len(prn)} forced + {len(hom)} ambiguous")
        return ToolResult.success(data={"gate": "pronunciation",
                                        "passed": True,
                                        "pronunciation": prn,
                                        "homographs": hom})

    @verb(role="effect")
    @requires_driver("music_text", as_="drv")
    def repetition_gate(self, lifecycle_id: str,
                         tracks: list[str], *, drv) -> ToolResult:
        """Computed cross-track repetition gate (effect).

        Passes iff no lyric line is repeated across multiple tracks.
        Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

        Inputs: lifecycle_id, tracks (list of lyric bodies).
        Returns: ``{gate, passed, evidence}`` or typed GATE_FAILED.
        chain_next: rewrite the repeated lines on one of the tracks.
        """
        report = drv.cross_track(tracks)
        passed = report["repeated_lines"] == 0
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="repetition", passed=passed,
                      evidence=("ok" if passed else
                                f"{report['repeated_lines']} repeats"))
        if not passed:
            return ToolResult.failure(
                "GATE_FAILED",
                f"repetition: {report['repeated_lines']} cross-track repeats")
        return ToolResult.success(data={"gate": "repetition", "passed": True,
                                        "report": report})

    @verb(role="effect")
    @requires_driver("music_text", as_="drv")
    def explicit_gate(self, lifecycle_id: str, lyrics: str,
                       allow_explicit: bool = False, *, drv) -> ToolResult:
        """Computed explicit-content gate (effect).

        Passes iff rating ∈ {clean, suggestive} OR ``allow_explicit=True``.
        Records the rating on the gate's evidence so audit knows what was
        OK'd. Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

        Inputs: lifecycle_id, lyrics, allow_explicit (default False).
        Returns: ``{gate, passed, rating}`` or typed GATE_FAILED.
        chain_next: rewrite explicit words OR re-call with allow_explicit=True
                    if the release is intentionally explicit.
        """
        report = drv.explicit(lyrics)
        # `allow_explicit=True` is an override path — the gate passes BUT the
        # evidence string carries an explicit override marker so audit can
        # distinguish "clean pass" from "explicit content was OK'd". Review
        # finding: without the marker the two passes look identical.
        is_override = report["rating"] == "explicit" and allow_explicit
        passed = report["rating"] != "explicit" or allow_explicit
        evidence = f"rating={report['rating']}"
        if is_override:
            evidence += " +allow_explicit"
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="explicit", passed=passed,
                      evidence=evidence)
        if not passed:
            return ToolResult.failure(
                "GATE_FAILED",
                f"explicit: rating={report['rating']} (set allow_explicit=True "
                f"to ship)")
        return ToolResult.success(data={"gate": "explicit", "passed": True,
                                        "rating": report["rating"],
                                        "override": is_override})

    @verb(role="effect")
    def name_exposure_gate(self, lifecycle_id: str, lyrics: str,
                           roster: list[str] | None = None) -> ToolResult:
        """Computed name-exposure gate — no forbidden roster names in lyrics (effect).

        Spec 119 — F6 from Spec 117. Passes iff zero rostered personal/character
        names appear (whole-word, case-insensitive). When `roster` is None it
        defaults to the project's ``name_exposure.blocklist``; an empty roster
        yields zero hits → PASSED (no-op for rosterless projects). Records
        PASSED/BLOCKED_ON on the lifecycle via gate.check.

        Inputs: lifecycle_id, lyrics, roster (defaults to config blocklist).
        Returns: ``{gate, passed, hits}`` or typed GATE_FAILED.
        chain_next: on failure, replace the leaked name with a function/role
                    descriptor then re-check.
        """
        if roster is None:
            from ..config import MusicConfig
            roster = list(MusicConfig.load().name_exposure_blocklist)
        hits = self._name_exposure_hits(lyrics, roster)
        passed = not hits
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="name-exposure", passed=passed,
                      evidence=("clean" if passed else
                                f"leaked names: {[h['name'] for h in hits]}"))
        if not passed:
            return ToolResult.failure(
                "GATE_FAILED",
                f"name-exposure: forbidden names present: "
                f"{[h['name'] for h in hits]}")
        return ToolResult.success(data={"gate": "name-exposure",
                                        "passed": True,
                                        "hits": hits})
