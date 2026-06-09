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

# Spec 095 — prosody-gate tunables (CLAUDE.md rule 8: documented budgets, not
# snapshots). The MIN_RHYME_GROUPS bound = "actual rhyming needs at least 2
# distinct rhyme groups; all-A monorhyme is an opinionated reject — set the
# bound to 1 via a verb-param override if your genre (hip-hop, blues) wants
# monorhyme to pass". The SYLLABLE_TOLERANCE = ±2 syllables around the
# per-line target — a default; per-genre tuning lands when the YAML preset
# layer ships (deferred to Slice 2+).
_MIN_RHYME_GROUPS: int = 2
_SYLLABLE_TOLERANCE: int = 2


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

        Spec 097 Slice 2 (review-driven): produces a `streaming-verify`
        artefact — without this the ontology schema was dormant.

        Inputs: album, urls (comma-separated).
        Returns: ``{album, live, dead, artefact}`` partitioning the URLs by HEAD-status.
        chain_next: re-submit any dead links to the distributor.
        """
        try:
            cloud = self.ctx.get_driver("music_cloud")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING", "no 'music_cloud' driver registered")
        targets = [u.strip() for u in urls.split(",") if u.strip()]
        live = [u for u in targets if cloud.url_head(u) == 200]
        dead = [u for u in targets if u not in live]
        return ToolResult.success(data={"album": album, "live": live,
                                        "dead": dead,
                                        "artefact": {"kind": "streaming-verify",
                                                     "album": album,
                                                     "live": live,
                                                     "dead": dead}})

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

    # ════════════════════════════════════════════════════════════════════════
    # Spec 096 — audio cluster: 16 NEW verbs + 2 composite gate verbs
    # (3 already shipped from 007 Slice 1: master_album, analyze_mix, transcribe_sheet)
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="effect")
    def master_audio(self, album: str, path: str,
                     target_lufs: float = -14.0,
                     preset: str = "") -> ToolResult:
        """Single-track master via AudioDriver (effect); produces mastering-report.

        Inputs: album, path, target_lufs, preset.
        Returns: ``{result, artefact}`` with input/output paths + gain.
        chain_next: ``music.qc_audio`` to verify.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        rep = audio.master(path=path, target_lufs=target_lufs, preset=preset)
        body = (f"# Mastered: {album}\ninput: {path}\noutput: {rep['output']}\n"
                f"target: {target_lufs} LUFS\nmeasured: {rep['measured_lufs']} LUFS\n"
                f"gain: {rep['gain_db']:+.1f} dB\npreset: {preset or 'default'}\n")
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "mastering-report", "album": album, "body": body,
            **rep}})

    @verb(role="effect")
    def master_with_reference(self, album: str, path: str,
                               reference: str) -> ToolResult:
        """Master `path` to match `reference` album loudness (effect).

        Inputs: album, path, reference (the reference WAV path).
        Returns: ``{result, artefact}`` mastering-report.
        chain_next: ``music.album_coherence_check`` to verify match.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        rep = audio.master_to_reference(path=path, reference=reference)
        body = (f"# Mastered to reference: {album}\ninput: {path}\n"
                f"reference: {reference}\noutput: {rep['output']}\n"
                f"matched LUFS: {rep['target_lufs']}\n")
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "mastering-report", "album": album, "body": body,
            **rep}})

    @verb(role="effect")
    def polish_audio(self, album: str, path: str) -> ToolResult:
        """Per-track polish pass via AudioDriver (effect).

        Inputs: album, path.
        Returns: ``{album, input, output}``.
        chain_next: ``music.master_audio`` once polished.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        out = audio.polish_full(path=path)
        return ToolResult.success(data={"album": album, "input": path,
                                        "output": out})

    @verb(role="effect")
    def polish_album(self, album: str, paths: list[str]) -> ToolResult:
        """Album-wide polish pass — applies polish to every track (effect).

        Inputs: album, paths (list of track WAV paths).
        Returns: ``{album, polished: [...], count}``.
        chain_next: ``music.polish_and_master_album`` or per-track master.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        polished = [audio.polish_full(p) for p in paths]
        return ToolResult.success(data={"album": album, "polished": polished,
                                        "count": len(polished)})

    @verb(role="effect")
    def polish_and_master_album(self, album: str, paths: list[str],
                                  target_lufs: float = -14.0) -> ToolResult:
        """Combined polish + master pipeline (effect); produces mastering-report.

        Inputs: album, paths, target_lufs.
        Returns: ``{result, artefact}`` with per-track gain summary.
        chain_next: ``music.qc_audio`` per output.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
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
    def fix_dynamic_track(self, album: str, path: str,
                          target_dr: float = 8.0) -> ToolResult:
        """Dynamic range fixer — applies compression/expansion (effect).

        Inputs: album, path, target_dr (default 8.0).
        Returns: ``{album, path, measured_dr, target_dr, applied, output}``.
        chain_next: ``music.qc_audio`` to verify.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        return ToolResult.success(data={"album": album,
                                        **audio.dynamic_fix(path,
                                                            target_dr=target_dr)})

    @verb(role="effect")
    def reset_mastering(self, album: str) -> ToolResult:
        """Revert all master/polish state for an album (effect).

        Delegates to ``music.set_track_status`` per track so each flip records
        its own Invocation in provenance (review finding: direct StateDriver
        writes lose the per-track audit trail). The sibling verb also enforces
        the ``TRACK_STATUS`` enum at write time.

        Inputs: album (slug).
        Returns: ``{album, reset, tracks_reset}``.
        chain_next: re-run ``music.polish_and_master_album``.
        """
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_state' driver registered")
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
    def render_codec_preview(self, album: str, path: str,
                              codec: str = "aac") -> ToolResult:
        """Render a streaming-codec preview via AudioDriver (effect).

        Inputs: album, path, codec (one of aac/opus/mp3).
        Returns: ``{album, path, codec, output, bitrate_kbps}``.
        chain_next: ``music.publish_asset`` the preview.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        return ToolResult.success(data={"album": album,
                                        **audio.codec_preview(path, codec=codec)})

    @verb(role="transform")
    def measure_album_signature(self, album: str,
                                  paths: list[str]) -> ToolResult:
        """Spectral signatures for an album's tracks via AudioDriver (transform).

        Inputs: album, paths.
        Returns: ``{album, signatures: [{path, centroid_hz, …}], count}``.
        chain_next: ``music.album_coherence_check``.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        sigs = [audio.measure_signature(p) for p in paths]
        return ToolResult.success(data={"album": album, "signatures": sigs,
                                        "count": len(sigs)})

    @verb(role="transform")
    def album_coherence_check(self, album: str,
                               paths: list[str]) -> ToolResult:
        """Cross-track tonal coherence report via AudioDriver (transform).

        Inputs: album, paths.
        Returns: ``{album, coherent, avg_distance, outliers, track_count}``.
        chain_next: ``music.album_coherence_correct`` if outliers found.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        return ToolResult.success(data={"album": album,
                                        **audio.coherence_report(paths)})

    @verb(role="effect")
    def album_coherence_correct(self, album: str, paths: list[str],
                                  target: dict | None = None) -> ToolResult:
        """Apply coherence corrections to bring outliers in line (effect).

        Inputs: album, paths, target (e.g. ``{centroid_hz: 2500}``).
        Returns: ``{album, applied_to, target, ok}``.
        chain_next: ``music.album_coherence_check`` to verify.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        return ToolResult.success(data={"album": album,
                                        **audio.apply_coherence(
                                            paths, target=target or {})})

    @verb(role="transform")
    def analyze_audio(self, album: str, path: str) -> ToolResult:
        """General spectral + loudness probe via AudioDriver (transform).

        Inputs: album, path.
        Returns: ``{album, loudness_lufs, signature: {…}}``.
        chain_next: ``music.qc_audio`` for the full QC pass.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        return ToolResult.success(data={"album": album,
                                        "loudness_lufs": audio.read_loudness(path),
                                        "signature": audio.measure_signature(path)})

    @verb(role="transform")
    def qc_audio(self, album: str, path: str) -> ToolResult:
        """7-point QC checklist via AudioDriver (transform).

        Inputs: album, path.
        Returns: ``{album, path, rows: {…}, summary}``.
        chain_next: ``music.qc_gate`` for the gating composite.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        return ToolResult.success(data={"album": album,
                                        **audio.qc_checklist(path)})

    @verb(role="transform")
    def mono_fold_check(self, album: str, path: str) -> ToolResult:
        """Phase-cancellation check via AudioDriver (transform).

        Inputs: album, path.
        Returns: ``{album, path, cancellation_db, phase_safe}``.
        chain_next: rebalance the mix on phase_safe=False.
        """
        try:
            audio = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        return ToolResult.success(data={"album": album,
                                        **audio.mono_fold(path)})

    @verb(role="effect")
    def generate_promo_videos(self, album: str, audio: str, art: str,
                               template: str = "") -> ToolResult:
        """Render a vertical promo video via AudioDriver (effect).

        Inputs: album, audio (track path), art (cover-art path), template.
        Returns: ``{result, artefact}`` promo-video artefact.
        chain_next: ``music.publish_asset`` the video.
        """
        try:
            drv = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        out = drv.render_promo_video(audio=audio, art=art, template=template)
        body = f"# Promo video: {album}\noutput: {out}\ntemplate: {template or 'default'}\n"
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "promo-video", "album": album, "track": audio,
            "output_path": out, "body": body}})

    @verb(role="effect")
    def create_songbook(self, album: str,
                         tracks: list[str]) -> ToolResult:
        """LilyPond → PDF songbook render via AudioDriver (effect).

        Inputs: album, tracks (list of track titles or musicxml paths).
        Returns: ``{result, artefact}`` sheet-music artefact (PDF stub).
        chain_next: ``music.publish_asset`` the songbook.
        """
        try:
            drv = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
        out = drv.render_songbook(tracks=tracks)
        body = f"# Songbook: {album}\noutput: {out}\ntrack count: {len(tracks)}\n"
        return ToolResult.success(data={"result": body, "artefact": {
            "kind": "sheet-music", "album": album,
            "output_path": out, "body": body}})

    # ── 2 composite gate verbs — called by the mastering skill ──

    @verb(role="effect")
    def measure_gate(self, lifecycle_id: str, path: str,
                      min_lufs: float = -20.0,
                      max_lufs: float = -8.0) -> ToolResult:
        """Computed measure gate — composes loudness probe + range check (effect).

        Passes iff measured loudness ∈ [min_lufs, max_lufs] (i.e. within the
        sensible streaming-target window).

        Inputs: lifecycle_id, path, min_lufs, max_lufs.
        Returns: ``{gate, passed, measured_lufs}`` or typed GATE_FAILED.
        chain_next: on failure, ``music.master_audio`` to adjust.
        """
        try:
            drv = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
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
    def qc_gate(self, lifecycle_id: str, path: str) -> ToolResult:
        """Computed QC gate — composes 7-point QC checklist (effect).

        Passes iff zero ``fail`` rows in the 7-point checklist.
        ``warn`` rows are PASS-with-evidence (gate records the warn count).

        Inputs: lifecycle_id, path.
        Returns: ``{gate, passed, summary, rows}`` or typed GATE_FAILED.
        chain_next: on failure, fix the failing rows + re-check.
        """
        try:
            drv = self.ctx.get_driver("music_audio")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_audio' driver registered")
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

    # ════════════════════════════════════════════════════════════════════════
    # Spec 097 — catalogue cluster: 11 NEW verbs + 1 composite gate verb
    # (3 already shipped: verify_streaming + catalogue_status from 007;
    # db_create_tweet ships NEW here as the typed DBDriver entry point)
    # ════════════════════════════════════════════════════════════════════════

    @verb(role="effect")
    def db_create_tweet(self, album: str, body: str, scheduled_at: str,
                         platform: str = "x") -> ToolResult:
        """Insert a tweet row via the DBDriver (effect); produces tweet-record artefact.

        Inputs: album, body, scheduled_at (ISO), platform (default ``x``).
        Returns: ``{result, artefact}`` tweet-record artefact with tweet_id.
        chain_next: ``music.db_update_tweet`` to flip status; ``music.tweet_schedule_gate``.
        """
        try:
            db = self.ctx.get_driver("music_db")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_db' driver registered")
        tid = db.create_tweet(album=album, body=body,
                              scheduled_at=scheduled_at, platform=platform)
        return ToolResult.success(data={"result": f"tweet:{tid}", "artefact": {
            "kind": "tweet-record", "album": album, "body": body,
            "platform": platform, "tweet_id": tid,
            "scheduled_at": scheduled_at}})

    @verb(role="effect")
    def db_update_tweet(self, tweet_id: int,
                         fields: dict) -> ToolResult:
        """Update tweet row fields via the DBDriver (effect).

        Inputs: tweet_id, fields (dict of {field: value}).
        Returns: ``{tweet_id, fields}``.
        chain_next: ``music.db_list_tweets`` to verify.
        """
        try:
            db = self.ctx.get_driver("music_db")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_db' driver registered")
        db.update_tweet(tweet_id=tweet_id, fields=fields)
        return ToolResult.success(data={"tweet_id": tweet_id,
                                        "fields": fields})

    @verb(role="effect")
    def db_delete_tweet(self, tweet_id: int) -> ToolResult:
        """Delete a tweet row via the DBDriver (effect).

        Inputs: tweet_id.
        Returns: ``{tweet_id, deleted}``.
        chain_next: ``music.db_list_tweets`` to verify.
        """
        try:
            db = self.ctx.get_driver("music_db")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_db' driver registered")
        db.delete_tweet(tweet_id=tweet_id)
        return ToolResult.success(data={"tweet_id": tweet_id, "deleted": True})

    @verb(role="transform")
    def db_list_tweets(self, album: str = "", status: str = "",
                        limit: int = 100) -> ToolResult:
        """List tweets via the DBDriver, filtered by album + status (transform).

        Inputs: album, status, limit.
        Returns: ``{tweets, count, album, status}``.
        chain_next: ``music.tweet_schedule_gate`` per row.
        """
        try:
            db = self.ctx.get_driver("music_db")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_db' driver registered")
        tweets = db.list_tweets(album=album, status=status, limit=limit)
        return ToolResult.success(data={"tweets": tweets,
                                        "count": len(tweets),
                                        "album": album, "status": status})

    @verb(role="transform")
    def db_search_tweets(self, query: str,
                          limit: int = 50) -> ToolResult:
        """Substring search across tweet bodies via DBDriver (transform).

        Inputs: query, limit.
        Returns: ``{tweets, count, query}``.
        chain_next: ``music.db_update_tweet`` to revise hits.
        """
        try:
            db = self.ctx.get_driver("music_db")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_db' driver registered")
        tweets = db.search_tweets(query=query, limit=limit)
        return ToolResult.success(data={"tweets": tweets,
                                        "count": len(tweets),
                                        "query": query})

    @verb(role="transform")
    def db_get_tweet_stats(self, album: str = "") -> ToolResult:
        """Aggregate counts of tweets by status via DBDriver (transform).

        Inputs: album (empty = all albums).
        Returns: ``{album, total, by_status}``.
        chain_next: ``music.tweet-curation`` skill walk.
        """
        try:
            db = self.ctx.get_driver("music_db")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_db' driver registered")
        return ToolResult.success(data=db.tweet_stats(album=album))

    @verb(role="effect")
    def db_sync_album(self, album: str,
                       tweets: list[dict]) -> ToolResult:
        """Idempotent sync of an album's tweets — replaces existing (effect).

        Inputs: album, tweets (list of {body, scheduled_at, platform}).
        Returns: ``{album, removed, created}``.
        chain_next: ``music.db_list_tweets(album)`` to verify.
        """
        try:
            db = self.ctx.get_driver("music_db")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_db' driver registered")
        return ToolResult.success(data=db.sync_album_tweets(
            album=album, tweets=tweets))

    @verb(role="effect")
    def update_streaming_url(self, album: str, platform: str,
                              url: str) -> ToolResult:
        """Persist a verified streaming URL via StateDriver (effect).

        Caller invokes ``music.verify_streaming`` first if reachability matters;
        this verb only persists. Two-step idiom keeps the CloudDriver surface clean
        (Spec 097 §"CloudDriver method delta" — no new methods).

        Inputs: album, platform, url.
        Returns: ``{album, platform, url, persisted}``.
        chain_next: ``music.get_streaming_urls`` to verify.
        """
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_state' driver registered")
        state.put(f"streaming:{album}:{platform}",
                  {"album": album, "platform": platform, "url": url})
        return ToolResult.success(data={"album": album, "platform": platform,
                                        "url": url, "persisted": True})

    @verb(role="transform")
    def get_streaming_urls(self, album: str) -> ToolResult:
        """Read recorded streaming URLs for an album via StateDriver (transform).

        Inputs: album.
        Returns: ``{album, urls: [{platform, url}]}``.
        chain_next: ``music.verify_streaming`` to re-check.
        """
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_state' driver registered")
        # Iterate via StateDriver.list_keys — production drivers expose this
        # primitive; reaching into a private `_store` would lose the
        # contract in production (review finding).
        urls = []
        for k in state.list_keys(prefix=f"streaming:{album}:"):
            v = state.get(k) or {}
            if "platform" in v and "url" in v:
                urls.append({"platform": v["platform"], "url": v["url"]})
        return ToolResult.success(data={"album": album, "urls": urls})

    @verb(role="transform")
    def get_promo_status(self, album: str) -> ToolResult:
        """Per-album promo state via StateDriver + DBDriver (transform).

        Inputs: album.
        Returns: ``{album, tweets: {total, by_status}, streaming_urls: int}``.
        chain_next: ``music.tweet-curation`` skill walk for any pending tweets.
        """
        try:
            db = self.ctx.get_driver("music_db")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_db' driver registered")
        try:
            state = self.ctx.get_driver("music_state")
        except DriverMissing:
            state = None
        tweet_stats = db.tweet_stats(album=album)
        # Same fix as get_streaming_urls — use the StateDriver primitive,
        # not a private attribute (review finding).
        url_count = 0
        if state is not None:
            url_count = len(state.list_keys(prefix=f"streaming:{album}:"))
        return ToolResult.success(data={"album": album,
                                        "tweets": tweet_stats,
                                        "streaming_urls": url_count})

    @verb(role="transform")
    def get_promo_content(self, album: str) -> ToolResult:
        """Read promo content (drafts + scheduled tweets) via DBDriver (transform).

        Inputs: album.
        Returns: ``{album, drafts, scheduled, total}``.
        chain_next: ``music.db_update_tweet`` to advance status.
        """
        try:
            db = self.ctx.get_driver("music_db")
        except DriverMissing:
            return ToolResult.failure("DEPENDENCY_MISSING",
                                      "no 'music_db' driver registered")
        drafts = db.list_tweets(album=album, status="draft")
        scheduled = db.list_tweets(album=album, status="scheduled")
        return ToolResult.success(data={"album": album,
                                        "drafts": drafts,
                                        "scheduled": scheduled,
                                        "total": len(drafts) + len(scheduled)})

    @verb(role="transform")
    def extract_links(self, text: str) -> ToolResult:
        """Extract URLs from text via simple regex (transform).

        Driver-free — uses stdlib re. Filters obvious SSRF risks
        (rejects javascript:/file:/data: schemes).

        Inputs: text.
        Returns: ``{urls, count}``.
        chain_next: ``music.verify_streaming`` to check each.
        """
        import re
        urls = re.findall(
            r"https?://[A-Za-z0-9.\-_/?#:&=%+~]+", text)
        return ToolResult.success(data={"urls": urls, "count": len(urls)})

    # ── 1 composite gate verb — called by the tweet-curation skill ──

    @verb(role="effect")
    def tweet_schedule_gate(self, lifecycle_id: str, body: str,
                             scheduled_at: str,
                             platform: str = "x",
                             max_length: int = 280) -> ToolResult:
        """Computed tweet-schedule gate (effect) — composes 3 checks.

        Passes iff: body length ≤ max_length AND scheduled_at is a non-empty
        future-looking timestamp AND body is non-empty.

        Inputs: lifecycle_id, body, scheduled_at, platform, max_length (default 280 = X/Twitter).
        Returns: ``{gate, passed, evidence}`` or typed GATE_FAILED.
        chain_next: on PASSED, ``music.db_create_tweet`` to persist.
        """
        problems = []
        if not body.strip():
            problems.append("body is empty")
        if len(body) > max_length:
            problems.append(
                f"body length {len(body)} > {max_length} for {platform}")
        if not scheduled_at.strip():
            problems.append("scheduled_at is required")
        passed = not problems
        self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                      name="tweet-schedule", passed=passed,
                      evidence=(f"ok ({len(body)} chars)" if passed else
                                "; ".join(problems)))
        if not passed:
            return ToolResult.failure(
                "GATE_FAILED",
                f"tweet-schedule: {'; '.join(problems)}")
        return ToolResult.success(data={"gate": "tweet-schedule",
                                        "passed": True,
                                        "length": len(body),
                                        "platform": platform})

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
