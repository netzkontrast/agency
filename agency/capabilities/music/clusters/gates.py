# agency-scaffold: v1
"""music gates cluster — cross-cutting computed gates + validation + health.

Spec 100 — 4 top-level verbs (validate_album · validate_sections · diagnose +
the 5 composite release/pre-gen gates) plus the 007 gates (pregen_check ·
release_check · music_health). These gates COMPOSE the other clusters' verbs
via ``ctx.call`` / sibling calls, so they live in their own cross-cutting
cluster. Relocated VERBATIM from ``_main.py`` per Spec 094 design §"Module
layout" (Spec 286 Phase 3).

Pure relocation — same decorator args, signatures, bodies, provenance.
"""
from __future__ import annotations

from agency.capability import requires_driver, verb
from agency.toolresult import ToolResult, Codes

from ._base import _MusicBase


class GatesCluster(_MusicBase):
    # ───────── gate cluster (computed predicates via gate.check) ─────────
    @verb(role="effect")
    def pregen_check(self, lifecycle_id: str, concept_ready: bool = False,
                     rights_clear: bool = False) -> ToolResult:
        """Computed `pre-generation` gate — machine-checkable predicate (Spec 094).

        Not the human ship-it confirm — that stays on an `elicit`/`lifecycle_gate`.
        Passes only when the concept is complete AND rights are cleared; a fail
        records BLOCKED_ON + flips the lifecycle to
        ``input-required`` via ``gate.check`` and returns a typed ``GATE_FAILED``. The
        terminal human "ready?" stays an ``elicit``/``lifecycle_gate``.

        Inputs: lifecycle_id (the Lifecycle serving the intent), concept_ready,
                rights_clear (the computed predicate inputs).
        Returns: ``{gate: "pre-generation", passed: True}`` on success; typed ``GATE_FAILED`` otherwise.
        chain_next: on PASSED, proceed to generation; on fail, resolve the missing inputs then re-check.
        """
        missing = [n for n, ok in (("concept", concept_ready), ("rights", rights_clear))
                   if not ok]
        passed = not missing
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id, name="pre-generation",
                      passed=passed, evidence="ready" if passed else f"missing: {missing}")
        if not passed:
            return ToolResult.failure(Codes.GATE_FAILED, f"pre-generation blocked; missing: {missing}")
        return ToolResult.success(data={"gate": "pre-generation", "passed": True})

    @verb(role="effect")
    @requires_driver("music_db", as_="db")
    def release_check(self, lifecycle_id: str, album: str = "", *, db) -> ToolResult:
        """Computed `release-qa` gate: every track mastered (read via the DBDriver).
        Records PASSED/BLOCKED_ON on the lifecycle via ``gate.check``; returns a typed
        ``GATE_FAILED`` + pauses the lifecycle when not ready.

        Inputs: lifecycle_id (the Lifecycle serving the intent), album.
        Returns: ``{album, gate: "release-qa", passed: True}`` on success; typed ``GATE_FAILED`` otherwise.
        chain_next: on PASSED, ``music.publish_asset`` the release; on fail, master the
        blocking tracks then re-check.
        """
        cur = db.cursor()
        cur.execute("SELECT slug, status FROM tracks WHERE album = %s", (album,))
        rows = cur.fetchall()
        cur.close()
        unmastered = [r[0] for r in rows if r[1] != "mastered"]
        passed = not unmastered
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id, name="release-qa",
                      passed=passed,
                      evidence="all mastered" if passed else f"unmastered: {unmastered}")
        if not passed:
            return ToolResult.failure(
                Codes.GATE_FAILED, f"release-qa blocked: {len(unmastered)} unmastered: {unmastered}")
        return ToolResult.success(data={"album": album, "gate": "release-qa", "passed": True})

    # ════════════════════════════════════════════════════════════════════════
    # Spec 100 — gates cluster: 4 NEW top-level verbs + 5 composite gate verbs
    # (3 already shipped: pregen_check + release_check from 007, music_health from 007).
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="transform")
    @requires_driver("music_state", as_="state")
    def validate_album(self, album: str, *, state) -> ToolResult:
        """Validate album file presence + mirror-path consistency via StateDriver (transform).

        Inputs: album (slug).
        Returns: ``{album, files_present, mirror_paths_ok, issues}``.
        chain_next: ``music.validate_sections`` for per-track structure.
        """
        found = state.find_album(query=album)
        issues = []
        if not found:
            issues.append(f"album '{album}' not found")
        # Verify track presence
        tracks = state.list_tracks(album)
        if not tracks:
            issues.append(f"album '{album}' has no tracks")
        return ToolResult.success(data={"album": album,
                                        "files_present": bool(found),
                                        "track_count": len(tracks),
                                        "mirror_paths_ok": not issues,
                                        "issues": issues})

    @verb(role="transform")
    @requires_driver("music_text", as_="text")
    def validate_sections(self, album: str,
                           lyrics: str = "", *, text) -> ToolResult:
        """Validate lyric section structure across an album (transform).

        Delegates to the 095 TextDriver `validate_sections`. Aggregates
        findings across all track bodies if `lyrics` is empty.

        Inputs: album, lyrics (optional — empty = read all album tracks).
        Returns: ``{album, ok, findings, track_count}``.
        chain_next: revise bad-tagged sections.

        ``music_text`` is decorator-injected (always required). The
        ``music_state`` driver is fetched inline only on the empty-lyrics
        branch (a conditional second dependency), so it stays on the raw
        ``_require_drv`` 2-tuple helper.
        """
        if lyrics:
            report = text.validate_sections(lyrics)
            return ToolResult.success(data={"album": album,
                                            "ok": report["ok"],
                                            "findings": report["findings"],
                                            "track_count": 1})
        # Iterate all tracks via StateDriver
        state, _fail2 = self._require_drv("music_state")
        if _fail2: return _fail2
        all_findings = []
        tracks = state.list_tracks(album)
        for t in tracks:
            body = t.get("body", "")
            if body:
                report = text.validate_sections(body)
                for f in report["findings"]:
                    f["track"] = t["slug"]
                    all_findings.append(f)
        return ToolResult.success(data={"album": album,
                                        "ok": not all_findings,
                                        "findings": all_findings,
                                        "track_count": len(tracks)})

    @verb(role="transform")
    def diagnose(self) -> ToolResult:
        """Composite driver-free health probe (transform).

        Inputs: none.
        Returns: ``{ok, drivers_wired, verbs_count, skills_count}``.
        chain_next: register missing drivers.
        """
        # Inline introspection — driver-free
        wanted = ("music_state", "music_text", "music_audio",
                  "music_db", "music_cloud")
        drv_reg = self.ctx.drivers
        wired = ([d for d in wanted if drv_reg is not None and drv_reg.has(d)]
                 if drv_reg is not None else [])
        return ToolResult.success(data={
            "ok": True,
            "drivers_wired": wired,
            "drivers_missing": [d for d in wanted if d not in wired],
            "verbs_count": len(self.ctx.registry._caps["music"].verbs),
            "skills_count": len(self.ctx.ontology.skills),
        })

    # ── 5 composite gate verbs — called by pre-generation-full + release-qa-full skills ──

    @verb(role="effect")
    @requires_driver("music_state", as_="state")
    def concept_gate(self, lifecycle_id: str, album: str, *, state) -> ToolResult:
        """Pre-generation gate: concept exists for the album (effect).

        Passes iff the album's slug resolves AND a concept artefact has been
        produced. The latter is a heuristic check on the graph (look for any
        Artefact with kind=album-concept SERVES the intent that opened the
        lifecycle).

        Inputs: lifecycle_id, album.
        Returns: ``{gate, passed, evidence}`` or typed GATE_FAILED.
        chain_next: ``music.conceptualize`` if no concept yet.
        """
        found = state.find_album(query=album)
        passed = bool(found)
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="concept", passed=passed,
                      evidence=(f"album '{album}' resolved" if passed else
                                f"album '{album}' not found"))
        if not passed:
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"concept: album '{album}' not found")
        return ToolResult.success(data={"gate": "concept", "passed": True,
                                        "album": album})

    @verb(role="effect")
    def lyrics_pregen_gate(self, lifecycle_id: str, album: str,
                            lyrics: str = "") -> ToolResult:
        """Composite lyrics pre-generation gate — chains the lyric gates (effect).

        Composes prosody + pronunciation + repetition + explicit (Spec 095) +
        name-exposure (Spec 119) sub-gates. Passes iff all pass. The
        name-exposure sub-gate is a no-op pass for rosterless projects (empty
        ``name_exposure.blocklist``). The lifecycle_id is reused for each
        sub-gate so the audit trail is unified.

        Inputs: lifecycle_id, album, lyrics (the lyric body to check).
        Returns: ``{gate, passed, sub_gates}`` or typed GATE_FAILED.
        chain_next: revise lyrics until all 4 sub-gates pass.
        """
        if not lyrics.strip():
            self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                          name="lyrics-pregen", passed=False,
                          evidence="empty lyrics")
            return ToolResult.failure(Codes.GATE_FAILED,
                                      "lyrics-pregen: empty lyrics")
        results = {}
        errors = {}
        # Sub-gate composition — each records its own gate.check; failures
        # bubble up but we attempt every sub-gate so audit sees all signals.
        for sub_name, sub_verb in (
                ("prosody", "prosody_gate"),
                ("pronunciation", "pronunciation_gate"),
                ("repetition", "repetition_gate"),
                ("explicit", "explicit_gate"),
                # Spec 119 — additive 5th sub-gate. Empty roster → no-op pass,
                # so the composite verdict is unchanged for rosterless projects.
                ("name_exposure", "name_exposure_gate")):
            try:
                sub_res = self.ctx.call("music", sub_verb,
                                        lifecycle_id=lifecycle_id,
                                        lyrics=lyrics)
                results[sub_name] = (sub_res or {}).get("passed", False)
            except Exception as e:
                # Narrowed evidence (Round 1 attempt-3 sc-analyze): a config
                # bug (DriverMissing) was indistinguishable from a semantic
                # fail. Record the exception class so the audit trail can
                # distinguish them.
                results[sub_name] = False
                errors[sub_name] = f"{type(e).__name__}: {e}"
        all_passed = all(results.values())
        # Record the composite outcome
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="lyrics-pregen", passed=all_passed,
                      evidence=f"sub: {results}"
                               + (f" errors: {errors}" if errors else ""))
        if not all_passed:
            failed = [k for k, v in results.items() if not v]
            return ToolResult.failure(
                Codes.GATE_FAILED, f"lyrics-pregen: failed sub-gates: {failed}")
        return ToolResult.success(data={"gate": "lyrics-pregen",
                                        "passed": True,
                                        "sub_gates": results})

    @verb(role="effect")
    @requires_driver("music_state", as_="state")
    def audio_release_gate(self, lifecycle_id: str,
                            album: str, *, state) -> ToolResult:
        """Composite audio-release gate — every track QC-passed (effect).

        Passes iff every track in the album has status=mastered (per the
        StateDriver) AND no track's QC checklist returns a `fail`.

        Inputs: lifecycle_id, album.
        Returns: ``{gate, passed, mastered_count, qc_failures}`` or GATE_FAILED.
        chain_next: master the unmastered + fix QC fails.
        """
        tracks = state.list_tracks(album)
        unmastered = [t["slug"] for t in tracks
                      if t.get("status") != "mastered"]
        passed = not unmastered and bool(tracks)
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="audio-release", passed=passed,
                      evidence=(f"all {len(tracks)} mastered" if passed else
                                f"unmastered: {unmastered}"))
        if not passed:
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"audio-release: {len(unmastered)} unmastered: {unmastered}")
        return ToolResult.success(data={"gate": "audio-release",
                                        "passed": True,
                                        "mastered_count": len(tracks),
                                        "qc_failures": []})

    @verb(role="effect")
    @requires_driver("music_state", as_="state")
    @requires_driver("music_db", as_="db")
    def catalogue_gate(self, lifecycle_id: str,
                        album: str, *, state, db) -> ToolResult:
        """Catalogue-synced gate — streaming URLs + tweets ready (effect).

        Passes iff at least 1 streaming URL is recorded AND at least 1
        scheduled tweet exists for the album.

        Both drivers are decorator-injected (stacked ``@requires_driver``).
        ``music_state`` is the OUTER decorator so its DEPENDENCY_MISSING is
        returned first — preserving the prior state-then-db check order.

        Inputs: lifecycle_id, album.
        Returns: ``{gate, passed, streaming_urls, scheduled_tweets}``.
        chain_next: ``music.update_streaming_url`` and ``music.db_create_tweet``.
        """
        url_count = len(state.list_keys(prefix=f"streaming:{album}:"))
        scheduled = db.list_tweets(album=album, status="scheduled")
        passed = url_count > 0 and len(scheduled) > 0
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="catalogue", passed=passed,
                      evidence=(f"{url_count} urls + {len(scheduled)} scheduled tweets"
                                if passed else
                                f"{url_count} urls, {len(scheduled)} scheduled"))
        if not passed:
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"catalogue: {url_count} urls, {len(scheduled)} tweets")
        return ToolResult.success(data={"gate": "catalogue",
                                        "passed": True,
                                        "streaming_urls": url_count,
                                        "scheduled_tweets": len(scheduled)})

    @verb(role="effect")
    @requires_driver("music_cloud", as_="cloud")
    def promo_gate(self, lifecycle_id: str,
                    album: str, *, cloud) -> ToolResult:
        """Promo-drafted gate — at least 1 promo asset exists (effect).

        Passes iff at least 1 published-asset is recorded for the album in
        the cloud store.

        Inputs: lifecycle_id, album.
        Returns: ``{gate, passed, asset_count}`` or typed GATE_FAILED.
        chain_next: ``music.publish_asset`` or ``music.upload_promo_video``.
        """
        assets = cloud.r2_list(prefix=f"{album}/")
        passed = len(assets) > 0
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="promo", passed=passed,
                      evidence=(f"{len(assets)} assets" if passed else
                                "no assets"))
        if not passed:
            return ToolResult.failure(
                Codes.GATE_FAILED,
                f"promo: no published assets for album '{album}'")
        return ToolResult.success(data={"gate": "promo", "passed": True,
                                        "asset_count": len(assets)})

    # ───────── health cluster (transform, driver-free) ─────────
    @verb(role="transform")
    def music_health(self) -> ToolResult:
        """Self-check the music capability (transform, driver-free) — report which Driver seams are wired.

        Produces a deterministic readiness report listing wired vs. missing driver seams.
        Inputs: none.
        Returns: ``{ok, drivers_wired, drivers_missing}``.
        chain_next: register any missing driver via ``Engine(..., drivers=…)``.
        """
        wanted = ("music_state", "music_text", "music_audio", "music_db", "music_cloud")
        wired = [d for d in wanted if self.ctx.drivers is not None and self.ctx.drivers.has(d)]
        return ToolResult.success(data={"ok": True, "drivers_wired": wired,
                                        "drivers_missing": [d for d in wanted if d not in wired]})
