# agency-scaffold: v1
"""music audio cluster — mastering / mixing / QC / sheet-music / promo-video.

Spec 096 — 16 audio verbs + 2 composite gate verbs (measure · qc), plus the
007 audio verbs (master_album · analyze_mix · transcribe_sheet). All route
through the AudioDriver — never inline ffmpeg/pyloudnorm. Relocated VERBATIM
from ``_main.py`` per Spec 094 design §"Module layout" (Spec 286 Phase 3).

Pure relocation — same decorator args, signatures, bodies, provenance.
"""
from __future__ import annotations

from agency.capability import requires_driver, verb
from agency.toolresult import ToolResult

from ._base import STREAMING_TARGET_LUFS, _MusicBase


class AudioCluster(_MusicBase):
    # ───────── audio/mastering cluster (effect via AudioDriver) ─────────
    @verb(role="effect")
    @requires_driver("music_audio", as_="audio")
    def master_album(self, album: str, path: str, target_lufs: float = STREAMING_TARGET_LUFS, *, audio) -> ToolResult:
        """Master an audio file to a target loudness via the AudioDriver (effect).

        Reads measured loudness, applies the gain via ffmpeg (both through the
        driver — no direct ffmpeg/pyloudnorm), and records a ``mastering-report``.
        Inputs: album, path, target_lufs.
        Returns: ``{result, artefact}`` where artefact.kind = ``mastering-report`` with measured_lufs, target_lufs, gain_db.
        chain_next: ``music.publish_asset``.
        """
        measured = audio.read_loudness(path)
        gain = target_lufs - measured
        audio.run_ffmpeg(["-i", path, "-af", f"volume={gain}dB"])
        body = (f"# Mastering report: {album}\nmeasured: {measured} LUFS\n"
                f"target: {target_lufs} LUFS\ngain: {gain:+.1f} dB\n")
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "mastering-report", "album": album, "measured_lufs": measured,
            "target_lufs": target_lufs, "gain_db": gain, "body": body}})

    # ───────── sheet-music cluster (act via AudioDriver) ─────────
    @verb(role="act")
    @requires_driver("music_audio", as_="audio")
    def transcribe_sheet(self, album: str, path: str, *, audio) -> ToolResult:
        """Transcribe audio to sheet music via AudioDriver, producing a sheet-music artefact (act).

        The transcription tool (AnthemScore-class) runs behind the driver, never inline.
        Inputs: album, path (the audio file).
        Returns: ``{result, artefact}`` where artefact.kind = ``sheet-music`` with source path.
        chain_next: ``music.publish_asset``.
        """
        audio.run_ffmpeg(["-i", path, "-f", "musicxml", f"{album}.musicxml"])
        body = f"# Sheet music: {album}\nsource: {path}\nformat: musicxml\n"
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "sheet-music", "album": album, "source": path, "body": body}})

    # ───────── mixing cluster (transform via AudioDriver) ─────────
    @verb(role="transform")
    @requires_driver("music_audio", as_="audio")
    def analyze_mix(self, album: str, path: str, *, audio) -> ToolResult:
        """Analyse a mix for loudness issues via the AudioDriver (transform).

        Inputs: album, path.
        Returns: ``{album, measured_lufs, findings}`` — decidable findings (too hot > -9, too quiet < -16).
        chain_next: ``music.master_album``.
        """
        loud = audio.read_loudness(path)
        findings = []
        if loud > -9:
            findings.append("too hot (clipping risk)")
        if loud < -16:
            findings.append("too quiet (below streaming target)")
        return ToolResult.success(data={"album": album, "measured_lufs": loud,
                                        "findings": findings or ["within target"]})

    # ════════════════════════════════════════════════════════════════════════
    # Spec 096 — audio cluster: 16 NEW verbs + 2 composite gate verbs
    # (3 already shipped from 007 Slice 1: master_album, analyze_mix, transcribe_sheet)
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="effect")
    @requires_driver("music_audio", as_="audio")
    def master_audio(self, album: str, path: str,
                     target_lufs: float = STREAMING_TARGET_LUFS,
                     preset: str = "", *, audio) -> ToolResult:
        """Master a single track via AudioDriver, producing a mastering-report (effect).

        Inputs: album, path, target_lufs, preset.
        Returns: ``{result, artefact}`` with input/output paths + gain.
        chain_next: ``music.qc_audio`` to verify.
        """
        rep = audio.master(path=path, target_lufs=target_lufs, preset=preset)
        body = (f"# Mastered: {album}\ninput: {path}\noutput: {rep['output']}\n"
                f"target: {target_lufs} LUFS\nmeasured: {rep['measured_lufs']} LUFS\n"
                f"gain: {rep['gain_db']:+.1f} dB\npreset: {preset or 'default'}\n")
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "mastering-report", "album": album, "body": body,
            **rep}})

    @verb(role="effect")
    @requires_driver("music_audio", as_="audio")
    def master_with_reference(self, album: str, path: str,
                               reference: str, *, audio) -> ToolResult:
        """Master `path` to match `reference` album loudness (effect).

        Inputs: album, path, reference (the reference WAV path).
        Returns: ``{result, artefact}`` mastering-report.
        chain_next: ``music.album_coherence_check`` to verify match.
        """
        rep = audio.master_to_reference(path=path, reference=reference)
        body = (f"# Mastered to reference: {album}\ninput: {path}\n"
                f"reference: {reference}\noutput: {rep['output']}\n"
                f"matched LUFS: {rep['target_lufs']}\n")
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "mastering-report", "album": album, "body": body,
            **rep}})

    @verb(role="effect")
    @requires_driver("music_audio", as_="audio")
    def polish_audio(self, album: str, path: str, *, audio) -> ToolResult:
        """Per-track polish pass via AudioDriver (effect).

        Inputs: album, path.
        Returns: ``{album, input, output}``.
        chain_next: ``music.master_audio`` once polished.
        """
        out = audio.polish_full(path=path)
        return ToolResult.success(data={"album": album, "input": path,
                                        "output": out})

    @verb(role="effect")
    @requires_driver("music_audio", as_="audio")
    def polish_album(self, album: str, paths: list[str], *, audio) -> ToolResult:
        """Album-wide polish pass — applies polish to every track (effect).

        Inputs: album, paths (list of track WAV paths).
        Returns: ``{album, polished: [...], count}``.
        chain_next: ``music.polish_and_master_album`` or per-track master.
        """
        polished = [audio.polish_full(p) for p in paths]
        return ToolResult.success(data={"album": album, "polished": polished,
                                        "count": len(polished)})

    @verb(role="effect")
    @requires_driver("music_audio", as_="audio")
    def polish_and_master_album(self, album: str, paths: list[str],
                                  target_lufs: float = STREAMING_TARGET_LUFS, *, audio) -> ToolResult:
        """Run the combined polish + master pipeline, producing a mastering-report (effect).

        Inputs: album, paths, target_lufs.
        Returns: ``{result, artefact}`` with per-track gain summary.
        chain_next: ``music.qc_audio`` per output.
        """
        outputs = []
        for p in paths:
            polished = audio.polish_full(p)
            rep = audio.master(polished, target_lufs=target_lufs)
            outputs.append({"input": p, "polished": polished,
                            "output": rep["output"],
                            "gain_db": rep["gain_db"]})
        body = (f"# Polish + master pipeline: {album}\n"
                f"tracks: {len(outputs)}\n"
                f"target LUFS: {target_lufs}\n")
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "mastering-report", "album": album, "body": body,
            "outputs": outputs}})

    @verb(role="effect")
    @requires_driver("music_audio", as_="audio")
    def fix_dynamic_track(self, album: str, path: str,
                          target_dr: float = 8.0, *, audio) -> ToolResult:
        """Dynamic range fixer — applies compression/expansion (effect).

        Inputs: album, path, target_dr (default 8.0).
        Returns: ``{album, path, measured_dr, target_dr, applied, output}``.
        chain_next: ``music.qc_audio`` to verify.
        """
        return ToolResult.success(data={"album": album,
                                        **audio.dynamic_fix(path,
                                                            target_dr=target_dr)})

    @verb(role="effect")
    @requires_driver("music_state", as_="state")
    def reset_mastering(self, album: str, *, state) -> ToolResult:
        """Revert all master/polish state for an album (effect).

        Delegates to ``music.set_track_status`` per track so each flip records
        its own Invocation in provenance (review finding: direct StateDriver
        writes lose the per-track audit trail). The sibling verb also enforces
        the ``TRACK_STATUS`` enum at write time.

        Inputs: album (slug).
        Returns: ``{album, reset, tracks_reset}``.
        chain_next: re-run ``music.polish_and_master_album``.
        """
        reset = 0
        for t in state.list_tracks(album):
            if t.get("status") == "mastered":
                # Sibling verb call — records Invocation, validates enum.
                self.ctx.call("music", "set_track_status",
                              album=album, track=t["slug"],
                              status="recorded")
                reset += 1
        return ToolResult.success(data={"album": album, "reset": True,
                                        "tracks_reset": reset})

    @verb(role="effect")
    @requires_driver("music_audio", as_="audio")
    def render_codec_preview(self, album: str, path: str,
                              codec: str = "aac", *, audio) -> ToolResult:
        """Render a streaming-codec preview via AudioDriver (effect).

        Inputs: album, path, codec (one of aac/opus/mp3).
        Returns: ``{album, path, codec, output, bitrate_kbps}``.
        chain_next: ``music.publish_asset`` the preview.
        """
        return ToolResult.success(data={"album": album,
                                        **audio.codec_preview(path, codec=codec)})

    @verb(role="transform")
    @requires_driver("music_audio", as_="audio")
    def measure_album_signature(self, album: str,
                                  paths: list[str], *, audio) -> ToolResult:
        """Spectral signatures for an album's tracks via AudioDriver (transform).

        Inputs: album, paths.
        Returns: ``{album, signatures: [{path, centroid_hz, …}], count}``.
        chain_next: ``music.album_coherence_check``.
        """
        sigs = [audio.measure_signature(p) for p in paths]
        return ToolResult.success(data={"album": album, "signatures": sigs,
                                        "count": len(sigs)})

    @verb(role="transform")
    @requires_driver("music_audio", as_="audio")
    def album_coherence_check(self, album: str,
                               paths: list[str], *, audio) -> ToolResult:
        """Cross-track tonal coherence report via AudioDriver (transform).

        Inputs: album, paths.
        Returns: ``{album, coherent, avg_distance, outliers, track_count}``.
        chain_next: ``music.album_coherence_correct`` if outliers found.
        """
        return ToolResult.success(data={"album": album,
                                        **audio.coherence_report(paths)})

    @verb(role="effect")
    @requires_driver("music_audio", as_="audio")
    def album_coherence_correct(self, album: str, paths: list[str],
                                  target: dict | None = None, *, audio) -> ToolResult:
        """Apply coherence corrections to bring outliers in line (effect).

        Inputs: album, paths, target (e.g. ``{centroid_hz: 2500}``).
        Returns: ``{album, applied_to, target, ok}``.
        chain_next: ``music.album_coherence_check`` to verify.
        """
        return ToolResult.success(data={"album": album,
                                        **audio.apply_coherence(
                                            paths, target=target or {})})

    @verb(role="transform")
    @requires_driver("music_audio", as_="audio")
    def analyze_audio(self, album: str, path: str, *, audio) -> ToolResult:
        """General spectral + loudness probe via AudioDriver (transform).

        Inputs: album, path.
        Returns: ``{album, loudness_lufs, signature: {…}}``.
        chain_next: ``music.qc_audio`` for the full QC pass.
        """
        return ToolResult.success(data={"album": album,
                                        "loudness_lufs": audio.read_loudness(path),
                                        "signature": audio.measure_signature(path)})

    @verb(role="transform")
    @requires_driver("music_audio", as_="audio")
    def qc_audio(self, album: str, path: str, *, audio) -> ToolResult:
        """7-point QC checklist via AudioDriver (transform).

        Inputs: album, path.
        Returns: ``{album, path, rows: {…}, summary}``.
        chain_next: ``music.qc_gate`` for the gating composite.
        """
        return ToolResult.success(data={"album": album,
                                        **audio.qc_checklist(path)})

    @verb(role="transform")
    @requires_driver("music_audio", as_="audio")
    def mono_fold_check(self, album: str, path: str, *, audio) -> ToolResult:
        """Phase-cancellation check via AudioDriver (transform).

        Inputs: album, path.
        Returns: ``{album, path, cancellation_db, phase_safe}``.
        chain_next: rebalance the mix on phase_safe=False.
        """
        return ToolResult.success(data={"album": album,
                                        **audio.mono_fold(path)})

    @verb(role="effect")
    @requires_driver("music_audio", as_="drv")
    def generate_promo_videos(self, album: str, audio: str, art: str,
                               template: str = "", *, drv) -> ToolResult:
        """Render a vertical promo video via AudioDriver (effect).

        Inputs: album, audio (track path), art (cover-art path), template.
        Returns: ``{result, artefact}`` promo-video artefact.
        chain_next: ``music.publish_asset`` the video.
        """
        out = drv.render_promo_video(audio=audio, art=art, template=template)
        body = f"# Promo video: {album}\noutput: {out}\ntemplate: {template or 'default'}\n"
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "promo-video", "album": album, "track": audio,
            "output_path": out, "body": body}})

    @verb(role="effect")
    @requires_driver("music_audio", as_="drv")
    def create_songbook(self, album: str,
                         tracks: list[str], *, drv) -> ToolResult:
        """LilyPond → PDF songbook render via AudioDriver (effect).

        Inputs: album, tracks (list of track titles or musicxml paths).
        Returns: ``{result, artefact}`` sheet-music artefact (PDF stub).
        chain_next: ``music.publish_asset`` the songbook.
        """
        out = drv.render_songbook(tracks=tracks)
        body = f"# Songbook: {album}\noutput: {out}\ntrack count: {len(tracks)}\n"
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "sheet-music", "album": album,
            "output_path": out, "body": body}})

    # ── 2 composite gate verbs — called by the mastering skill ──

    @verb(role="effect")
    @requires_driver("music_audio", as_="drv")
    def measure_gate(self, lifecycle_id: str, path: str,
                      min_lufs: float = -20.0,
                      max_lufs: float = -8.0, *, drv) -> ToolResult:
        """Computed measure gate — composes loudness probe + range check (effect).

        Passes iff measured loudness ∈ [min_lufs, max_lufs] (i.e. within the
        sensible streaming-target window).

        Inputs: lifecycle_id, path, min_lufs, max_lufs.
        Returns: ``{gate, passed, measured_lufs}`` or typed GATE_FAILED.
        chain_next: on failure, ``music.master_audio`` to adjust.
        """
        measured = drv.read_loudness(path)
        passed = min_lufs <= measured <= max_lufs
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="measure", passed=passed,
                      evidence=f"measured={measured:.1f} LUFS, range=[{min_lufs},{max_lufs}]")
        if not passed:
            return ToolResult.failure(
                "GATE_FAILED",
                f"measure: {measured:.1f} LUFS outside [{min_lufs}, {max_lufs}]")
        return ToolResult.success(data={"gate": "measure", "passed": True,
                                        "measured_lufs": measured})

    @verb(role="effect")
    @requires_driver("music_audio", as_="drv")
    def qc_gate(self, lifecycle_id: str, path: str, *, drv) -> ToolResult:
        """Computed QC gate — composes 7-point QC checklist (effect).

        Passes iff zero ``fail`` rows in the 7-point checklist.
        ``warn`` rows are PASS-with-evidence (gate records the warn count).

        Inputs: lifecycle_id, path.
        Returns: ``{gate, passed, summary, rows}`` or typed GATE_FAILED.
        chain_next: on failure, fix the failing rows + re-check.
        """
        report = drv.qc_checklist(path)
        failed_rows = [r for r, s in report["rows"].items() if s == "fail"]
        warned = [r for r, s in report["rows"].items() if s == "warn"]
        passed = not failed_rows
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="qc", passed=passed,
                      evidence=(f"summary={report['summary']}, "
                                f"warns={len(warned)}, fails={len(failed_rows)}"))
        if not passed:
            return ToolResult.failure(
                "GATE_FAILED",
                f"qc: {len(failed_rows)} failing rows: {failed_rows}")
        return ToolResult.success(data={"gate": "qc", "passed": True,
                                        "summary": report["summary"],
                                        "rows": report["rows"]})
