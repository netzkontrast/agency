"""music — an EXAMPLE out-of-tree domain capability: the clustered Capability +
Boundary/Driver contract on a real domain (Spec 007).

Music is the reference clustered domain capability: album conceptualization plus one representative verb per cluster (text, audio/mastering, catalogue DB, content/promo, state, cloud), each reaching external work through an injected Spec-002 Driver and recording provenance — so a release audit is one graph traversal.

Use when: conceptualizing or producing an album — turning an idea into a gated concept, mastering to a target loudness, drafting promo copy, or auditing a release — as the reference for how an out-of-tree clustered domain capability extends agency.
Triggers:
- An album idea that needs a structured, gated concept before production
- A music production step (master, promo, lyric analysis) that should be recorded as provenance
- A reference for how a clustered domain capability reaches external tools via Drivers
Red flags:
- Shelling out to ffmpeg/Postgres/R2 directly → route through a Spec-002 Driver via ctx.get_driver
- Producing a document without an artefact → set data['artefact'] so the Registry records PRODUCES
"""
from __future__ import annotations

from agency.capability import CapabilityBase, DriverMissing, verb
from agency.ontology import OntologyExtension
from agency.toolresult import ToolResult

ALBUM_TYPES = {"documentary", "narrative", "thematic", "character-study",
               "collection", "ost"}
ALBUM_STATUS = {"draft", "in-production", "mastered", "released"}
TRACK_STATUS = {"draft", "recorded", "mixed", "mastered"}

_VOWELS = "aeiouy"


def _syllables(word: str) -> int:
    """A deterministic, driver-free syllable heuristic (vowel-group count, ≥ 1)."""
    w = word.lower().strip()
    count, prev_vowel = 0, False
    for ch in w:
        is_vowel = ch in _VOWELS
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if w.endswith("e") and count > 1:
        count -= 1
    return max(1, count) if w else 0


# the conceptualizer: a 7-phase gated planning skill (foundation → … → confirmation),
# ending in a HARD confirm gate. The engine's skill walker walks it one phase at a time.
ALBUM_CONCEPT_SKILL = {
    "name": "album-concept",
    "kind": "conceptualizer",
    "phases": [
        {"index": 1, "name": "foundation",
         "produces": ["artist", "genre", "type", "scale", "theme", "true_story"]},
        {"index": 2, "name": "concept",
         "produces": ["key_subjects", "emotional_core", "why"]},
        {"index": 3, "name": "sonic",
         "produces": ["references", "production_style", "vocal_approach",
                      "instrumentation", "mood", "target_duration"]},
        {"index": 4, "name": "structure",
         "produces": ["tracklist", "sequencing", "energy_map"]},
        {"index": 5, "name": "art",
         "produces": ["visual_concept", "palette", "symbols"]},
        {"index": 6, "name": "practical",
         "produces": ["album_title", "track_titles", "research_needs",
                      "explicit", "distributor_genres"]},
        {"index": 7, "name": "confirmation",
         "produces": ["user_confirmed"], "gate": "hard"},
    ],
}

# Two gated, walkable workflow skills (CORE.md:57-62) — computed predicates advance
# the early phases; the terminal "ship it?" is a HARD human gate.
PRE_GENERATION_SKILL = {
    "name": "pre-generation", "kind": "gate",
    "phases": [
        {"index": 1, "name": "concept-ready", "produces": ["concept_complete"]},
        {"index": 2, "name": "rights-clear", "produces": ["rights_ok"]},
        {"index": 3, "name": "approve", "produces": ["approved"], "gate": "hard"},
    ],
}
RELEASE_QA_SKILL = {
    "name": "release-qa", "kind": "gate",
    "phases": [
        {"index": 1, "name": "mastered", "produces": ["all_tracks_mastered"]},
        {"index": 2, "name": "metadata", "produces": ["metadata_complete"]},
        {"index": 3, "name": "ship", "produces": ["released"], "gate": "hard"},
    ],
}


def conceptualize(artist: str, title: str, type: str,
                  theme: str = "", tracklist: str = "") -> dict:
    "Render an album-concept document (act). `type` must be a known album type."
    if type not in ALBUM_TYPES:
        raise ValueError(f"type={type!r} not in {sorted(ALBUM_TYPES)}")
    body = (f"# {title}\n\n**Artist:** {artist}  \n**Type:** {type}\n\n"
            f"## Theme\n{theme}\n\n## Tracklist\n{tracklist}\n")
    return {"result": body, "artefact": {
        "kind": "album-concept", "artist": artist, "title": title,
        "type": type, "body": body}}


music_ontology = OntologyExtension(
    nodes={"Album": ["artist", "title", "type", "status", "genre", "slug", "target_lufs"],
           "Track": ["title", "status", "slug"],
           "Tweet": ["text"], "Idea": ["text"], "SheetMusic": ["title"]},
    enums={("Album", "type"): ALBUM_TYPES,
           ("Album", "status"): ALBUM_STATUS,
           ("Track", "status"): TRACK_STATUS},
    skills={"album-concept": ALBUM_CONCEPT_SKILL,
            "pre-generation": PRE_GENERATION_SKILL,
            "release-qa": RELEASE_QA_SKILL},
    schemas={"album-concept": ["artist", "title", "type"],
             "promo-copy": ["album", "body"],
             "mastering-report": ["album", "body"],
             "lyric-report": ["album", "body"],
             "sheet-music": ["album", "body"]},
)


class MusicCapability(CapabilityBase):
    name = "music"
    home = "capability"
    ontology = music_ontology

    # ───────── act / conceptualize cluster (preserved demo) ─────────
    @verb(role="act")
    def conceptualize(self, artist: str, title: str, type: str,
                      theme: str = "", tracklist: str = "") -> dict:
        return conceptualize(artist, title, type, theme, tracklist)

    # ───────── text cluster (transform, driver-free, deterministic) ─────────
    @verb(role="transform")
    def count_syllables(self, word: str) -> ToolResult:
        """Count syllables in a word — deterministic, driver-free text math.

        Inputs: word. Returns: ``{word, syllables}``. chain_next: ``music.lyric_report``.
        """
        return ToolResult.success(data={"word": word, "syllables": _syllables(word)})

    # ───────── lyrics cluster (act via TextDriver, produces lyric-report) ─────────
    @verb(role="act")
    def lyric_report(self, album: str, lyrics: str) -> ToolResult:
        """Analyze a lyric sheet's syllable load per line via the TextDriver (act).

        Inputs: album, lyrics. Returns a ``lyric-report`` artefact (PRODUCES edge).
        chain_next: feed the report into the mix/master step.
        """
        try:
            text = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING", "no 'music_text' driver registered")
        lines = [ln for ln in lyrics.splitlines() if ln.strip()]
        per_line = [sum(text.syllables(w) for w in ln.split()) for ln in lines]
        body = (f"# Lyric report: {album}\nlines: {len(lines)}\n"
                f"syllables/line: {per_line}\n")
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "lyric-report", "album": album, "lines": len(lines),
            "syllables_per_line": per_line, "body": body}})

    # ───────── audio/mastering cluster (effect via AudioDriver) ─────────
    @verb(role="effect")
    def master_album(self, album: str, path: str, target_lufs: float = -14.0) -> ToolResult:
        """Master an audio file to a target loudness via the AudioDriver (effect).

        Reads measured loudness, applies the gain via ffmpeg (both through the
        driver — no direct ffmpeg/pyloudnorm), and records a ``mastering-report``.
        Inputs: album, path, target_lufs. chain_next: ``music.publish_asset``.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING", "no 'music_audio' driver registered")
        measured = audio.read_loudness(path)
        gain = target_lufs - measured
        audio.run_ffmpeg(["-i", path, "-af", f"volume={gain}dB"])
        body = (f"# Mastering report: {album}\nmeasured: {measured} LUFS\n"
                f"target: {target_lufs} LUFS\ngain: {gain:+.1f} dB\n")
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "mastering-report", "album": album, "measured_lufs": measured,
            "target_lufs": target_lufs, "gain_db": gain, "body": body}})

    # ───────── catalogue DB cluster (transform via DBDriver) ─────────
    @verb(role="transform")
    def catalogue_status(self, album: str = "") -> ToolResult:
        """Read track statuses from the catalogue DB via the DBDriver (transform).

        Inputs: album. Returns ``{tracks: [{slug, status}]}``. chain_next: gate on
        all-tracks-mastered before release.
        """
        try:
            db = self.ctx.get_driver("music_db")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING", "no 'music_db' driver registered")
        cur = db.cursor()
        cur.execute("SELECT slug, status FROM tracks WHERE album = %s", (album,))
        rows = cur.fetchall()
        cur.close()
        return ToolResult.success(data={"tracks": [{"slug": r[0], "status": r[1]} for r in rows]})

    # ───────── content/promo cluster (act, produces promo-copy) ─────────
    @verb(role="act")
    def promo_copy(self, album: str, angle: str = "") -> ToolResult:
        """Draft promotional copy for an album (act, produces a ``promo-copy`` artefact).

        Inputs: album, angle. chain_next: ``music.publish_asset`` the copy.
        """
        body = f"🎵 {album} — {angle or 'out now'}. Stream it everywhere.\n"
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "promo-copy", "album": album, "angle": angle, "body": body}})

    # ───────── state cluster (effect via StateDriver) ─────────
    @verb(role="effect")
    def set_album_status(self, album: str, status: str) -> ToolResult:
        """Persist an album's production status via the StateDriver (effect).

        Inputs: album, status (one of the Album.status enum). chain_next: ``release-qa``.
        """
        if status not in ALBUM_STATUS:
            return ToolResult.failure("INVALID_ARGUMENT",
                                      f"status {status!r} not in {sorted(ALBUM_STATUS)}")
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING", "no 'music_state' driver registered")
        state.put(f"album:{album}", {"album": album, "status": status})
        return ToolResult.success(data={"album": album, "status": status})

    # ───────── cloud cluster (effect via CloudDriver) ─────────
    @verb(role="effect")
    def publish_asset(self, album: str, key: str, body: str = "") -> ToolResult:
        """Publish an album asset to object storage via the CloudDriver (effect).

        Returns ``DEPENDENCY_MISSING`` (typed) when the cloud backend is
        unconfigured — never a stringly-typed raise. Inputs: album, key, body.
        """
        try:
            cloud = self.ctx.get_driver("music_cloud")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING", "no 'music_cloud' driver registered")
        res = cloud.r2_put(key, body.encode())
        if not res.get("ok"):
            return ToolResult.failure(res.get("error", "INTERNAL"),
                                      f"cloud put failed for {key!r}")
        return ToolResult.success(data={"key": key, "bytes": res.get("bytes", 0)})

    # ───────── gate cluster (computed predicates via gate.check) ─────────
    @verb(role="effect")
    def pregen_check(self, lifecycle_id: str, concept_ready: bool = False,
                     rights_clear: bool = False) -> ToolResult:
        """Computed `pre-generation` gate (CORE.md:57-62 — a MACHINE-checkable predicate,
        not the human ship-it confirm). Passes only when the concept is complete AND
        rights are cleared; a fail records BLOCKED_ON + flips the lifecycle to
        ``input-required`` via ``gate.check`` and returns a typed ``GATE_FAILED``. The
        terminal human "ready?" stays an ``elicit``/``lifecycle_gate``.

        Inputs: lifecycle_id (the Lifecycle serving the intent), concept_ready,
                rights_clear (the computed predicate inputs).
        """
        missing = [n for n, ok in (("concept", concept_ready), ("rights", rights_clear))
                   if not ok]
        passed = not missing
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id, name="pre-generation",
                      passed=passed, evidence="ready" if passed else f"missing: {missing}")
        if not passed:
            return ToolResult.failure("GATE_FAILED", f"pre-generation blocked; missing: {missing}")
        return ToolResult.success(data={"gate": "pre-generation", "passed": True})

    @verb(role="effect")
    def release_check(self, lifecycle_id: str, album: str = "") -> ToolResult:
        """Computed `release-qa` gate: every track mastered (read via the DBDriver).
        Records PASSED/BLOCKED_ON on the lifecycle via ``gate.check``; returns a typed
        ``GATE_FAILED`` + pauses the lifecycle when not ready.

        Inputs: lifecycle_id (the Lifecycle serving the intent), album.
        chain_next: on PASSED, ``music.publish_asset`` the release; on fail, master the
        blocking tracks then re-check.
        """
        try:
            db = self.ctx.get_driver("music_db")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING", "no 'music_db' driver registered")
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
                "GATE_FAILED", f"release-qa blocked: {len(unmastered)} unmastered: {unmastered}")
        return ToolResult.success(data={"album": album, "gate": "release-qa", "passed": True})

    # ───────── sheet-music cluster (act via AudioDriver) ─────────
    @verb(role="act")
    def transcribe_sheet(self, album: str, path: str) -> ToolResult:
        """Transcribe audio to sheet music via the AudioDriver (act, produces a
        ``sheet-music`` artefact) — the transcription tool (AnthemScore-class) runs
        behind the driver, never inline.

        Inputs: album, path (the audio file). chain_next: ``music.publish_asset``.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING", "no 'music_audio' driver registered")
        audio.run_ffmpeg(["-i", path, "-f", "musicxml", f"{album}.musicxml"])
        body = f"# Sheet music: {album}\nsource: {path}\nformat: musicxml\n"
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "sheet-music", "album": album, "source": path, "body": body}})

    # ───────── mixing cluster (transform via AudioDriver) ─────────
    @verb(role="transform")
    def analyze_mix(self, album: str, path: str) -> ToolResult:
        """Analyse a mix for loudness issues via the AudioDriver (transform).

        Inputs: album, path. Returns ``{album, measured_lufs, findings}`` — decidable
        findings (too hot > -9, too quiet < -16). chain_next: ``music.master_album``.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING", "no 'music_audio' driver registered")
        loud = audio.read_loudness(path)
        findings = []
        if loud > -9:
            findings.append("too hot (clipping risk)")
        if loud < -16:
            findings.append("too quiet (below streaming target)")
        return ToolResult.success(data={"album": album, "measured_lufs": loud,
                                        "findings": findings or ["within target"]})

    # ───────── streaming cluster (transform via CloudDriver) ─────────
    @verb(role="transform")
    def verify_streaming(self, album: str, urls: str = "") -> ToolResult:
        """Verify an album's streaming links are live via the CloudDriver (transform).

        Inputs: album, urls (comma-separated). Returns ``{live, dead}``. chain_next:
        re-submit any dead links to the distributor.
        """
        try:
            cloud = self.ctx.get_driver("music_cloud")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING", "no 'music_cloud' driver registered")
        targets = [u.strip() for u in urls.split(",") if u.strip()]
        live = [u for u in targets if cloud.url_head(u) == 200]
        return ToolResult.success(data={"album": album, "live": live,
                                        "dead": [u for u in targets if u not in live]})

    # ───────── ideas cluster (effect via StateDriver, records an Idea node) ─────────
    @verb(role="effect")
    def capture_idea(self, text: str) -> ToolResult:
        """Capture a creative idea (effect) — records an ``Idea`` graph node (provenance)
        and persists it via the StateDriver.

        Inputs: text. Returns ``{idea_id, text}``. chain_next: ``music.conceptualize``
        when an idea grows into an album.
        """
        if not text.strip():
            return ToolResult.failure("INVALID_ARGUMENT", "idea text is required")
        idea_id = self.ctx.record("Idea", {"text": text})
        self.ctx.link(idea_id, self.ctx.intent_id, "SERVES")
        try:
            state = self.ctx.get_driver("music_state")
            state.put(f"idea:{idea_id}", {"text": text})
        except DriverMissing:
            pass                                          # graph node is the record of truth
        return ToolResult.success(data={"idea_id": idea_id, "text": text})

    # ───────── health cluster (transform, driver-free) ─────────
    @verb(role="transform")
    def music_health(self) -> ToolResult:
        """Self-check the music capability (transform, driver-free): which Driver seams are
        wired and a deterministic readiness report.

        Inputs: none. Returns ``{ok, drivers, verbs}``. chain_next: register any missing
        driver via ``Engine(..., drivers=…)``.
        """
        wanted = ("music_state", "music_text", "music_audio", "music_db", "music_cloud")
        wired = [d for d in wanted if self.ctx.drivers is not None and self.ctx.drivers.has(d)]
        return ToolResult.success(data={"ok": True, "drivers_wired": wired,
                                        "drivers_missing": [d for d in wanted if d not in wired]})
