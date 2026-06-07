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
             "lyric-report": ["album", "body"]},
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
