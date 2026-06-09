# agency-scaffold: v1
"""music — clustered domain capability (Spec 093 master / Spec 094 lifecycle migration).

Music graduates from ``examples/music.py`` into a first-class folder-form
capability under ``agency/capabilities/music/`` (Spec 094). The CLAUDE.md +
docs/vision/CAPABILITY-CLUSTERS.md doctrine exception is documented in those
files; music remains the **reference clustered domain capability** but is no
longer "third-party example" — it's the substrate's first creative-production
domain.

This module hosts the migrated 007 verb surface (``conceptualize`` + 10
cluster-representative verbs) PLUS the 11 NEW lifecycle verbs from Spec 094
Slice 2 (``promote_idea``, ``list_ideas``, ``create_album``, ``find_album``,
``create_track``, ``list_tracks``, ``set_track_status``, ``rename_album``,
``rename_track``, ``album_progress``, ``resume_session``) — 26 verbs total.
The per-cluster file split (Spec 094 design §"Module layout") is intentionally
deferred to Specs 095-100: each cluster spec moves its slice of verbs from
``_main.py`` into the dedicated ``clusters/<name>.py`` module as it ships,
keeping behavioural contracts and provenance unchanged through the migration.

Use when: conceptualizing or producing an album — turning an idea into a gated concept, mastering to a target loudness, drafting promo copy, or auditing a release — as the reference for how a first-class clustered domain capability extends agency.
Triggers:
- An album idea that needs a structured, gated concept before production
- A music production step (master, promo, lyric analysis) that should be recorded as provenance
- A reference for how a clustered domain capability reaches external tools via Drivers
Red flags:
- Shelling out to ffmpeg/Postgres/R2 directly → route through a Spec-002 Driver via ctx.get_driver
- Producing a document without an artefact → set data['artefact'] so the Registry records PRODUCES
"""
from __future__ import annotations

from agency.capability import CapabilityBase, DriverMissing, RenderTemplates, verb
from agency.toolresult import ToolResult

from .ontology import (
    ALBUM_STATUS,
    ALBUM_TYPES,
    IDEA_STATUS,
    TRACK_STATUS,
    music_ontology,
)

_VOWELS = "aeiouy"
_SLUG_BAD = (" ", "/", "\\", ".", ",", "!", "?", "'", "\"", "(", ")", "[", "]")


def _slugify(text: str) -> str:
    """Deterministic slugifier — lowercase, replace non-alnum with hyphen, collapse."""
    s = text.lower().strip()
    for ch in _SLUG_BAD:
        s = s.replace(ch, "-")
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


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


class MusicCapability(CapabilityBase):
    name = "music"
    home = "capability"
    ontology = music_ontology
    render_templates = RenderTemplates.from_module(__file__)

    # ───────── act / conceptualize cluster (preserved demo) ─────────
    @verb(role="act")
    def conceptualize(self, artist: str, title: str, type: str,
                      theme: str = "", tracklist: str = "") -> dict:
        """Render an album-concept document (act); ``type`` must be a known album type.

        Inputs: artist, title, type (one of ``ALBUM_TYPES``), theme, tracklist.
        Returns: ``{result, artefact}`` where artefact.kind = ``album-concept``.
        chain_next: ``music.lyric_report`` for prosody analysis, then ``music.master_album``.
        """
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

        Inputs: album, lyrics.
        Returns: ``{result, artefact}`` where artefact.kind = ``lyric-report`` (PRODUCES edge).
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
        Inputs: album, path, target_lufs.
        Returns: ``{result, artefact}`` where artefact.kind = ``mastering-report`` with measured_lufs, target_lufs, gain_db.
        chain_next: ``music.publish_asset``.
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

        Inputs: album.
        Returns: ``{tracks: [{slug, status}]}``.
        chain_next: gate on all-tracks-mastered before release.
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

        Inputs: album, angle.
        Returns: ``{result, artefact}`` where artefact.kind = ``promo-copy``.
        chain_next: ``music.publish_asset`` the copy.
        """
        body = f"🎵 {album} — {angle or 'out now'}. Stream it everywhere.\n"
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "promo-copy", "album": album, "angle": angle, "body": body}})

    # ───────── state cluster (effect via StateDriver) ─────────
    @verb(role="effect")
    def set_album_status(self, album: str, status: str) -> ToolResult:
        """Persist an album's production status via the StateDriver (effect).

        Inputs: album, status (one of the Album.status enum).
        Returns: ``{album, status}`` echoing the persisted record.
        chain_next: ``release-qa``.
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
        unconfigured — never a stringly-typed raise.
        Inputs: album, key, body.
        Returns: ``{key, bytes}`` on success.
        chain_next: ``music.verify_streaming`` once distributor links propagate.
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
            return ToolResult.failure("GATE_FAILED", f"pre-generation blocked; missing: {missing}")
        return ToolResult.success(data={"gate": "pre-generation", "passed": True})

    @verb(role="effect")
    def release_check(self, lifecycle_id: str, album: str = "") -> ToolResult:
        """Computed `release-qa` gate: every track mastered (read via the DBDriver).
        Records PASSED/BLOCKED_ON on the lifecycle via ``gate.check``; returns a typed
        ``GATE_FAILED`` + pauses the lifecycle when not ready.

        Inputs: lifecycle_id (the Lifecycle serving the intent), album.
        Returns: ``{album, gate: "release-qa", passed: True}`` on success; typed ``GATE_FAILED`` otherwise.
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
        """Transcribe audio → sheet music via AudioDriver (act); produces sheet-music artefact.

        The transcription tool (AnthemScore-class) runs behind the driver, never inline.
        Inputs: album, path (the audio file).
        Returns: ``{result, artefact}`` where artefact.kind = ``sheet-music`` with source path.
        chain_next: ``music.publish_asset``.
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

        Inputs: album, path.
        Returns: ``{album, measured_lufs, findings}`` — decidable findings (too hot > -9, too quiet < -16).
        chain_next: ``music.master_album``.
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

        Inputs: album, urls (comma-separated).
        Returns: ``{album, live, dead}`` partitioning the URLs by HEAD-status.
        chain_next: re-submit any dead links to the distributor.
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
        """Capture a creative idea (effect) — record an Idea node, persist via StateDriver.

        Inputs: text.
        Returns: ``{idea_id, text, status}``.
        chain_next: ``music.promote_idea`` when an idea grows into an album.
        """
        if not text.strip():
            return ToolResult.failure("INVALID_ARGUMENT", "idea text is required")
        idea_id = self.ctx.record("Idea", {"text": text, "status": "new"})
        self.ctx.link(idea_id, self.ctx.intent_id, "SERVES")
        try:
            state = self.ctx.get_driver("music_state")
            state.put(f"idea:{idea_id}", {"idea_id": idea_id, "text": text,
                                          "status": "new"})
        except DriverMissing:
            pass                                          # graph node is the record of truth
        return ToolResult.success(data={"idea_id": idea_id, "text": text,
                                        "status": "new"})

    # ───────── 094 Slice 2: ideas lifecycle (promote_idea, list_ideas) ─────────
    @verb(role="effect")
    def promote_idea(self, idea_id: str, artist: str, title: str,
                     genre: str, type: str = "thematic") -> ToolResult:
        """Promote an Idea → Album (effect); record Album + PROMOTED_TO edge.

        Inputs: idea_id, artist, title, genre, type.
        Returns: ``{idea_id, album_id, album_slug, status}``.
        chain_next: ``music.conceptualize`` to draft the album concept.
        """
        if type not in ALBUM_TYPES:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"type={type!r} not in {sorted(ALBUM_TYPES)}")
        # Validate the idea actually exists — silently promoting a non-existent
        # idea_id would orphan the PROMOTED_TO edge (review finding).
        idea_node = self.ctx.recall(idea_id)
        if idea_node is None:
            return ToolResult.failure(
                "NOT_FOUND", f"idea_id={idea_id!r} not found")
        slug = _slugify(title)
        album_id = self.ctx.record("Album", {
            "artist": artist, "title": title, "type": type,
            "status": "draft", "genre": genre, "slug": slug,
            "target_lufs": -14.0,
        })
        self.ctx.link(album_id, self.ctx.intent_id, "SERVES")
        self.ctx.link(idea_id, album_id, "PROMOTED_TO")
        # Graph-canonical status flip (CLAUDE.md rule 2) — the StateDriver
        # mirror below is the disk projection; the graph is the truth.
        self.ctx.update(idea_id, {"status": "promoted"})
        try:
            state = self.ctx.get_driver("music_state")
            state.update_idea(idea_id, {"status": "promoted",
                                        "promoted_to_album": slug})
            state.create_album_root(artist=artist, genre=genre, slug=slug,
                                    title=title, type=type)
        except DriverMissing:
            pass
        return ToolResult.success(data={"idea_id": idea_id, "album_id": album_id,
                                        "album_slug": slug, "status": "promoted"})

    @verb(role="transform")
    def list_ideas(self, status: str = "") -> ToolResult:
        """List captured ideas via the StateDriver (transform) — filter by status.

        Inputs: status (one of ``IDEA_STATUS`` or ``""`` for all).
        Returns: ``{ideas: [{idea_id, text, status, …}], count}``.
        chain_next: ``music.promote_idea`` to turn a "new" idea into an album.
        """
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_state' driver registered")
        ideas = state.list_ideas(status=status)
        return ToolResult.success(data={"ideas": ideas, "count": len(ideas)})

    # ───────── 094 Slice 2: album lifecycle (create / find / progress) ─────────
    @verb(role="effect")
    def create_album(self, artist: str, title: str, genre: str,
                     type: str = "thematic") -> ToolResult:
        """Create an album root + render the canonical templates (effect).

        Records an ``Album`` graph node, calls StateDriver.create_album_root for
        the disk layout (production); the README is rendered from the bitwize-
        ported ``album`` template (Spec 094 §"Template porting"). Optional
        ``artist`` page renders on first album for this artist.

        Inputs: artist, title, genre, type (default ``thematic``).
        Returns: ``{album_id, album_slug, album_root, artist_seeded, title}``.
        chain_next: ``music.create_track`` for each track in the tracklist.
        """
        if type not in ALBUM_TYPES:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"type={type!r} not in {sorted(ALBUM_TYPES)}")
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_state' driver registered")
        slug = _slugify(title)
        # Graph-canonical record FIRST (CLAUDE.md rule 2).
        album_id = self.ctx.record("Album", {
            "artist": artist, "title": title, "type": type,
            "status": "draft", "genre": genre, "slug": slug,
            "target_lufs": -14.0,
        })
        self.ctx.link(album_id, self.ctx.intent_id, "SERVES")
        # Driver maintains the on-disk mirror (production); fake stores in-memory.
        root = state.create_album_root(artist=artist, genre=genre, slug=slug,
                                       title=title, type=type)
        # Render the album README from the template; artist seed on first album.
        album_tpl = self.ctx.template("album")
        if album_tpl is not None:
            state.put(f"{root}/README.md", {"body": album_tpl.template})
        artist_seeded = False
        if not state.find_album(query=f"artist:{artist}"):
            artist_tpl = self.ctx.template("artist")
            if artist_tpl is not None:
                state.put(f"artists/{_slugify(artist)}/README.md",
                          {"body": artist_tpl.template})
                artist_seeded = True
        return ToolResult.success(data={"album_id": album_id,
                                        "album_slug": slug,
                                        "album_root": root,
                                        "artist_seeded": artist_seeded,
                                        "title": title})

    @verb(role="transform")
    def find_album(self, query: str = "") -> ToolResult:
        """Find albums by slug / fuzzy match via the StateDriver (transform).

        Inputs: query (slug-exact wins; substring then; ``""`` returns all).
        Returns: ``{albums: […], count, query}``.
        chain_next: ``music.album_progress`` on a found slug.
        """
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_state' driver registered")
        albums = state.find_album(query=query)
        return ToolResult.success(data={"albums": albums,
                                        "count": len(albums),
                                        "query": query})

    @verb(role="effect")
    def rename_album(self, old_slug: str, new_slug: str) -> ToolResult:
        """Rename an album, mirroring paths via the StateDriver (effect).

        Inputs: old_slug, new_slug.
        Returns: ``{success, old_slug, new_slug, title, tracks_updated}``.
        chain_next: ``music.album_progress`` to verify state preserved.
        """
        if not new_slug.strip():
            return ToolResult.failure("INVALID_ARGUMENT",
                                      "new_slug must be non-empty")
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_state' driver registered")
        result = state.rename_album(old_slug=old_slug, new_slug=new_slug)
        if not result.get("success"):
            return ToolResult.failure(result.get("error", "NOT_FOUND"),
                                      f"rename_album {old_slug!r} failed")
        return ToolResult.success(data=result)

    @verb(role="transform")
    def album_progress(self, album: str) -> ToolResult:
        """Album progress aggregate via the StateDriver (transform).

        Inputs: album (slug).
        Returns: ``{album_slug, track_count, tracks_completed, completion_percentage, tracks_by_status}``.
        chain_next: ``music.release_check`` once completion_percentage = 100.
        """
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_state' driver registered")
        return ToolResult.success(data=state.album_progress(album=album))

    # ───────── 094 Slice 2: track lifecycle ─────────
    @verb(role="effect")
    def create_track(self, album: str, title: str,
                     track_number: int = 0) -> ToolResult:
        """Create a track in an album, rendered from the bitwize ``track`` template (effect).

        Records a ``Track`` graph node, edges ``Track RECORDED_FOR Album``, persists
        via the StateDriver.

        Inputs: album (slug), title, track_number (0-padded to 2 digits in the slug).
        Returns: ``{track_id, track_slug, album, track_number, title}``.
        chain_next: ``music.set_track_status`` as the track progresses.
        """
        slug = _slugify(title)
        if track_number > 0:
            slug = f"{track_number:02d}-{slug}"
        # Graph node first (CLAUDE.md rule 2)
        track_id = self.ctx.record("Track", {
            "title": title, "status": "draft", "slug": slug,
        })
        self.ctx.link(track_id, self.ctx.intent_id, "SERVES")
        # Resolve the album graph node by slug so the RECORDED_FOR edge
        # actually lands (review finding: declared edge was dormant-surface).
        # `ctx.find(label)` returns properties dicts where ``id`` is the
        # agency node-id (memory.py:62-69 round-trips it via upsert_node).
        album_node = next((a for a in self.ctx.find("Album")
                           if a.get("slug") == album), None)
        if album_node is not None:
            self.ctx.link(track_id, album_node["id"], "RECORDED_FOR")
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.success(data={"track_id": track_id,
                                            "track_slug": slug,
                                            "album": album,
                                            "track_number": track_number,
                                            "title": title})
        track_tpl = self.ctx.template("track")
        body = track_tpl.template if track_tpl is not None else ""
        if body and "track_number: 0" in body:
            body = body.replace("track_number: 0",
                                f"track_number: {track_number}")
        state.create_track(album=album, slug=slug, title=title, body=body)
        return ToolResult.success(data={"track_id": track_id,
                                        "track_slug": slug,
                                        "album": album,
                                        "track_number": track_number,
                                        "title": title})

    @verb(role="transform")
    def list_tracks(self, album: str) -> ToolResult:
        """List tracks for an album via the StateDriver (transform).

        Inputs: album (slug).
        Returns: ``{album, tracks: [{slug, title, status, …}], count}``.
        chain_next: ``music.album_progress`` for the aggregate view.
        """
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_state' driver registered")
        tracks = state.list_tracks(album=album)
        return ToolResult.success(data={"album": album, "tracks": tracks,
                                        "count": len(tracks)})

    @verb(role="effect")
    def set_track_status(self, album: str, track: str,
                         status: str) -> ToolResult:
        """Persist a track's production status via the StateDriver (effect).

        Inputs: album (slug), track (slug), status (one of ``TRACK_STATUS``).
        Returns: ``{album, track, status}``.
        chain_next: ``music.list_tracks`` to verify, then ``music.album_progress``.
        """
        if status not in TRACK_STATUS:
            return ToolResult.failure(
                "INVALID_ARGUMENT",
                f"status={status!r} not in {sorted(TRACK_STATUS)}")
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_state' driver registered")
        state.update_track_field(album=album, track=track,
                                 field="status", value=status)
        return ToolResult.success(data={"album": album, "track": track,
                                        "status": status})

    @verb(role="effect")
    def rename_track(self, album: str, old_slug: str,
                     new_slug: str) -> ToolResult:
        """Rename a track within an album, mirroring paths via the StateDriver (effect).

        Inputs: album, old_slug, new_slug.
        Returns: ``{success, album_slug, old_slug, new_slug, title}``.
        chain_next: ``music.list_tracks`` to verify.
        """
        if not new_slug.strip():
            return ToolResult.failure("INVALID_ARGUMENT",
                                      "new_slug must be non-empty")
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_state' driver registered")
        result = state.rename_track(album=album, old_slug=old_slug,
                                    new_slug=new_slug)
        if not result.get("success"):
            return ToolResult.failure(result.get("error", "NOT_FOUND"),
                                      f"rename_track {old_slug!r} failed")
        return ToolResult.success(data=result)

    # ───────── 094 Slice 2: session ─────────
    @verb(role="transform")
    def resume_session(self) -> ToolResult:
        """Restore the last-album context via the StateDriver (transform).

        Inputs: none.
        Returns: ``{session: {last_album?, last_track?, last_phase?, pending_actions?}}``.
        chain_next: ``music.album_progress`` on ``session.last_album`` if set.
        """
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_state' driver registered")
        return ToolResult.success(data={"session": state.get_session()})

    # ════════════════════════════════════════════════════════════════════════
    # Spec 095 — lyrics cluster: 13 NEW transforms + 4 composite gate verbs
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="transform")
    def analyze_rhyme_scheme(self, lyrics: str) -> ToolResult:
        """Build a rhyme scheme (A/B/C labels) over the lyric lines (transform).

        Inputs: lyrics (multi-line text).
        Returns: ``{scheme, groups, self_rhymes}`` via TextDriver.rhyme_scheme.
        chain_next: ``music.prosody_gate`` for an integrated prosody check.
        """
        try:
            text = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        lines = [ln for ln in lyrics.splitlines() if ln.strip()]
        return ToolResult.success(data=text.rhyme_scheme(lines))

    @verb(role="transform")
    def analyze_readability(self, text_: str) -> ToolResult:
        """Flesch-Kincaid-shaped readability over the lyric text (transform).

        Inputs: text_ (multi-line — `text` is a builtin so kw is suffixed).
        Returns: ``{grade_level, avg_words_per_sentence, avg_syllables_per_word}``.
        chain_next: pair with ``music.analyze_rhyme_scheme`` for a full prosody view.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        return ToolResult.success(data=drv.readability(text_))

    @verb(role="transform")
    def check_pronunciation(self, lyrics: str) -> ToolResult:
        """Flag words requiring forced pronunciation per the bundled guide (transform).

        Inputs: lyrics (multi-line text).
        Returns: ``{findings: [{word, suggested, severity}], count}``.
        chain_next: ``music.pronunciation_gate`` to gate the lyric-writing skill.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        findings = drv.pronunciation(lyrics)
        return ToolResult.success(data={"findings": findings,
                                        "count": len(findings)})

    @verb(role="transform")
    def check_homographs(self, lyrics: str) -> ToolResult:
        """Flag words with multiple legitimate pronunciations (transform).

        Inputs: lyrics.
        Returns: ``{findings: [{word, ambiguous_readings, severity}], count}``.
        chain_next: ``music.pronunciation_gate``.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        findings = drv.homographs(lyrics)
        return ToolResult.success(data={"findings": findings,
                                        "count": len(findings)})

    @verb(role="transform")
    def check_streaming_lyrics(self, lyrics: str,
                                platform: str = "spotify") -> ToolResult:
        """Check the lyric body for platform-incompatible markup (transform).

        Inputs: lyrics, platform (default ``spotify``).
        Returns: ``{platform, bracket_tags, safe, fix?}``.
        chain_next: strip bracket tags before upload if ``safe=False``.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        return ToolResult.success(data=drv.streaming_safe(lyrics, platform))

    @verb(role="transform")
    def check_cross_track_repetition(self, tracks: list[str]) -> ToolResult:
        """Flag lyric lines repeated across multiple album tracks (transform).

        Inputs: tracks (list of lyric bodies, one per track).
        Returns: ``{repeated_lines, track_count, examples}``.
        chain_next: ``music.repetition_gate``.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        return ToolResult.success(data=drv.cross_track(tracks))

    @verb(role="transform")
    def check_explicit_content(self, lyrics: str) -> ToolResult:
        """Classify lyrics as clean / suggestive / explicit (transform).

        Inputs: lyrics.
        Returns: ``{rating, explicit_words, suggestive_words}``.
        chain_next: ``music.explicit_gate``.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        return ToolResult.success(data=drv.explicit(lyrics))

    @verb(role="transform")
    def extract_distinctive_phrases(self, lyrics: str,
                                     corpus: list[str] | None = None) -> ToolResult:
        """Return novel tri-grams (not in corpus) from the lyrics (transform).

        Inputs: lyrics, corpus (list of comparison lyric bodies — defaults to []).
        Returns: ``{phrases: [...], count}``.
        chain_next: use distinctive phrases as marketing hooks.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        phrases = drv.distinctive_phrases(lyrics, corpus or [])
        return ToolResult.success(data={"phrases": phrases,
                                        "count": len(phrases)})

    @verb(role="transform")
    def extract_section(self, lyrics: str, label: str) -> ToolResult:
        """Extract the body under a ``[<label>]`` section tag (transform).

        Inputs: lyrics, label (e.g. ``Verse 1``).
        Returns: ``{section, body}``.
        chain_next: pass the section body to a per-section transform.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        body = drv.extract_section(lyrics, label)
        return ToolResult.success(data={"section": label, "body": body})

    @verb(role="transform")
    def validate_section_structure(self, lyrics: str) -> ToolResult:
        """Validate section tag well-formedness (Title Case in brackets) (transform).

        Inputs: lyrics.
        Returns: ``{ok, findings: [{line, tag, issue, severity}]}``.
        chain_next: fix flagged tags before the prosody pass.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        return ToolResult.success(data=drv.validate_sections(lyrics))

    @verb(role="transform")
    def scan_artist_names(self, lyrics: str,
                          allow: list[str] | None = None) -> ToolResult:
        """Scan for accidental artist-name drops against the blocklist (transform).

        Inputs: lyrics, allow (allowlist of explicitly permitted artist mentions).
        Returns: ``{hits: [{name, severity, fix}], count}``.
        chain_next: replace flagged names or extend the allowlist.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        hits = drv.scan_artist_names(lyrics, allow or [])
        return ToolResult.success(data={"hits": hits, "count": len(hits)})

    @verb(role="transform")
    def check_voice_tells(self, lyrics: str) -> ToolResult:
        """AI-tell rule-based detector (advisory only — no gate impact) (transform).

        Inputs: lyrics.
        Returns: ``{findings: [{heuristic, severity, fix}], count}``.
        chain_next: rewrite flagged lines for idiosyncrasy.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        findings = drv.voice_tells(lyrics)
        return ToolResult.success(data={"findings": findings,
                                        "count": len(findings)})

    # ── 4 composite gate verbs — called by the lyric-writing skill ──

    @verb(role="effect")
    def prosody_gate(self, lifecycle_id: str, lyrics: str,
                     syllable_target: int = 0) -> ToolResult:
        """Computed prosody gate — composes rhyme + syllable checks (effect).

        Passes iff rhyme_scheme has ≥ 2 groups (real rhyming, not all-A) AND
        (when syllable_target > 0) avg line syllables within ±2 of target.
        Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

        Inputs: lifecycle_id, lyrics, syllable_target (0 = skip).
        Returns: ``{gate, passed, evidence}`` or typed GATE_FAILED.
        chain_next: on failure, revise lyrics + re-check.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        lines = [ln for ln in lyrics.splitlines() if ln.strip()]
        rhyme = drv.rhyme_scheme(lines)
        problems = []
        if rhyme["groups"] < 2:
            problems.append("rhyme_scheme is all-one-group (no actual rhyming)")
        if syllable_target > 0:
            stats = drv.stats(lyrics)
            avg = stats["syllables"] / max(stats["lines"], 1)
            if abs(avg - syllable_target) > 2:
                problems.append(
                    f"avg syllables {avg:.1f} differs from target "
                    f"{syllable_target} by > 2")
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
    def pronunciation_gate(self, lifecycle_id: str,
                            lyrics: str) -> ToolResult:
        """Computed pronunciation gate — composes pronunciation + homograph (effect).

        Passes iff zero pronunciation findings AND zero homograph findings.
        Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

        Inputs: lifecycle_id, lyrics.
        Returns: ``{gate, passed, evidence}`` or typed GATE_FAILED.
        chain_next: resolve flagged words then re-check.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        prn = drv.pronunciation(lyrics)
        hom = drv.homographs(lyrics)
        passed = not prn and not hom
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="pronunciation", passed=passed,
                      evidence=(f"clean" if passed else
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
    def repetition_gate(self, lifecycle_id: str,
                         tracks: list[str]) -> ToolResult:
        """Computed cross-track repetition gate (effect).

        Passes iff no lyric line is repeated across multiple tracks.
        Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

        Inputs: lifecycle_id, tracks (list of lyric bodies).
        Returns: ``{gate, passed, evidence}`` or typed GATE_FAILED.
        chain_next: rewrite the repeated lines on one of the tracks.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
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
    def explicit_gate(self, lifecycle_id: str, lyrics: str,
                       allow_explicit: bool = False) -> ToolResult:
        """Computed explicit-content gate (effect).

        Passes iff rating ∈ {clean, suggestive} OR ``allow_explicit=True``.
        Records the rating on the gate's evidence so audit knows what was
        OK'd. Records PASSED/BLOCKED_ON on the lifecycle via gate.check.

        Inputs: lifecycle_id, lyrics, allow_explicit (default False).
        Returns: ``{gate, passed, rating}`` or typed GATE_FAILED.
        chain_next: rewrite explicit words OR re-call with allow_explicit=True
                    if the release is intentionally explicit.
        """
        try:
            drv = self.ctx.get_driver("music_text")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_text' driver registered")
        report = drv.explicit(lyrics)
        passed = report["rating"] != "explicit" or allow_explicit
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="explicit", passed=passed,
                      evidence=f"rating={report['rating']}")
        if not passed:
            return ToolResult.failure(
                "GATE_FAILED",
                f"explicit: rating={report['rating']} (set allow_explicit=True "
                f"to ship)")
        return ToolResult.success(data={"gate": "explicit", "passed": True,
                                        "rating": report["rating"]})

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
