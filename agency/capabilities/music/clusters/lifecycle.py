# agency-scaffold: v1
"""music lifecycle cluster — ideas · albums · tracks · session (Spec 286 P3).

The lifecycle verbs (conceptualize · capture_idea · promote_idea · list_ideas ·
create_album · find_album · set_album_status* · create_track · list_tracks ·
set_track_status · rename_album · rename_track · album_progress ·
resume_session) relocate VERBATIM from ``_main.py`` into this mixin per Spec 094
design §"Module layout". ``set_album_status`` lives in the StateCluster (its
own state-driver banner); the rest land here.

Pure relocation — same decorator args, signatures, bodies, provenance.
"""
from __future__ import annotations

from agency.capability import DriverMissing, requires_driver, verb
from agency.toolresult import ToolResult, Codes

from ..ontology import IDEA_STATUS, TRACK_STATUS
from ._base import (
    STREAMING_TARGET_LUFS,
    _MusicBase,
    _fill_album_body,
    _fill_track_body,
    _slugify,
    _validate_album_type,
    conceptualize as _conceptualize_fn,
)


class LifecycleCluster(_MusicBase):
    # ───────── act / conceptualize cluster (preserved demo) ─────────
    @verb(role="act")
    def conceptualize(self, artist: str, title: str, type: str,
                      theme: str = "", tracklist: str = "") -> dict:
        """Render an album-concept document for a known album ``type`` (act).

        Inputs: artist, title, type (one of ``ALBUM_TYPES``), theme, tracklist.
        Returns: ``{result, artefact}`` where artefact.kind = ``album-concept``.
        chain_next: ``music.lyric_report`` for prosody analysis, then ``music.master_album``.
        """
        return _conceptualize_fn(artist, title, type, theme, tracklist)

    # ───────── ideas cluster (effect via StateDriver, records an Idea node) ─────────
    @verb(role="effect")
    def capture_idea(self, text: str) -> ToolResult:
        """Capture a creative idea (effect) — record an Idea node, persist via StateDriver.

        Inputs: text.
        Returns: ``{idea_id, text, status}``.
        chain_next: ``music.promote_idea`` when an idea grows into an album.
        """
        if not text.strip():
            return ToolResult.failure(Codes.INVALID_ARGUMENT, "idea text is required")
        idea_id = self.ctx.record_and_serve("Idea", {"text": text, "status": "new"})
        self._autowire_music_drivers()    # Spec 117: wire-on-need before the direct get
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
        """Promote an Idea to an Album, recording the Album + PROMOTED_TO edge (effect).

        Inputs: idea_id, artist, title, genre, type.
        Returns: ``{idea_id, album_id, album_slug, status}``.
        chain_next: ``music.conceptualize`` to draft the album concept.
        """
        if (fail := _validate_album_type(type)) is not None:
            return fail
        # Validate the idea actually exists — silently promoting a non-existent
        # idea_id would orphan the PROMOTED_TO edge (review finding).
        idea_node = self.ctx.recall(idea_id)
        if idea_node is None:
            return ToolResult.failure(
                Codes.NOT_FOUND, f"idea_id={idea_id!r} not found")
        slug = _slugify(title)
        album_id = self.ctx.record_and_serve("Album", {
            "artist": artist, "title": title, "type": type,
            "status": "draft", "genre": genre, "slug": slug,
            "target_lufs": STREAMING_TARGET_LUFS,
        })
        self.ctx.link(idea_id, album_id, "PROMOTED_TO")
        # Graph-canonical status flip (CLAUDE.md rule 2) — the StateDriver
        # mirror below is the disk projection; the graph is the truth.
        self.ctx.update(idea_id, {"status": "promoted"})
        self._autowire_music_drivers()    # Spec 117: wire-on-need before the direct get
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
        if status and status not in IDEA_STATUS:
            return ToolResult.failure(
                Codes.INVALID_ARGUMENT,
                f"status={status!r} not in {sorted(IDEA_STATUS)}")
        state, _fail = self._require_drv("music_state")
        if _fail: return _fail
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
        if (fail := _validate_album_type(type)) is not None:
            return fail
        state, _fail = self._require_drv("music_state")
        if _fail: return _fail
        slug = _slugify(title)
        # Graph-canonical record FIRST (CLAUDE.md rule 2).
        album_id = self.ctx.record_and_serve("Album", {
            "artist": artist, "title": title, "type": type,
            "status": "draft", "genre": genre, "slug": slug,
            "target_lufs": STREAMING_TARGET_LUFS,
        })
        # Driver maintains the on-disk mirror (production); fake stores in-memory.
        root = state.create_album_root(artist=artist, genre=genre, slug=slug,
                                       title=title, type=type)
        # Render the album README from the template; artist seed on first album.
        album_tpl = self.ctx.template("album")
        if album_tpl is not None:
            body = _fill_album_body(album_tpl.template, artist=artist,
                                    title=title, genre=genre)
            state.put(f"{root}/README.md", {"body": body})
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
    @requires_driver("music_state", as_="state")
    def find_album(self, query: str = "", *, state) -> ToolResult:
        """Find albums by slug / fuzzy match via the StateDriver (transform).

        Inputs: query (slug-exact wins; substring then; ``""`` returns all).
        Returns: ``{albums: […], count, query}``.
        chain_next: ``music.album_progress`` on a found slug.
        """
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
            return ToolResult.failure(Codes.INVALID_ARGUMENT,
                                      "new_slug must be non-empty")
        state, _fail = self._require_drv("music_state")
        if _fail: return _fail
        result = state.rename_album(old_slug=old_slug, new_slug=new_slug)
        if not result.get("success"):
            return ToolResult.failure(result.get("error", "NOT_FOUND"),
                                      f"rename_album {old_slug!r} failed")
        return ToolResult.success(data=result)

    @verb(role="transform")
    @requires_driver("music_state", as_="state")
    def album_progress(self, album: str, *, state) -> ToolResult:
        """Album progress aggregate via the StateDriver (transform).

        Inputs: album (slug).
        Returns: ``{album_slug, track_count, tracks_completed, completion_percentage, tracks_by_status}``.
        chain_next: ``music.release_check`` once completion_percentage = 100.
        """
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
        track_id = self.ctx.record_and_serve("Track", {
            "title": title, "status": "draft", "slug": slug,
        })
        # Resolve the album graph node by slug so the RECORDED_FOR edge
        # actually lands (review finding: declared edge was dormant-surface).
        # `ctx.find(label)` returns properties dicts where ``id`` is the
        # agency node-id (memory.py:62-69 round-trips it via upsert_node).
        album_node = next((a for a in self.ctx.find("Album")
                           if a.get("slug") == album), None)
        if album_node is not None:
            self.ctx.link(track_id, album_node["id"], "RECORDED_FOR")
        self._autowire_music_drivers()    # Spec 117: wire-on-need before the direct get
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
        body = _fill_track_body(body, title=title, track_number=track_number)
        state.create_track(album=album, slug=slug, title=title, body=body)
        return ToolResult.success(data={"track_id": track_id,
                                        "track_slug": slug,
                                        "album": album,
                                        "track_number": track_number,
                                        "title": title})

    @verb(role="transform")
    @requires_driver("music_state", as_="state")
    def list_tracks(self, album: str, *, state) -> ToolResult:
        """List tracks for an album via the StateDriver (transform).

        Inputs: album (slug).
        Returns: ``{album, tracks: [{slug, title, status, …}], count}``.
        chain_next: ``music.album_progress`` for the aggregate view.
        """
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
                Codes.INVALID_ARGUMENT,
                f"status={status!r} not in {sorted(TRACK_STATUS)}")
        state, _fail = self._require_drv("music_state")
        if _fail: return _fail
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
            return ToolResult.failure(Codes.INVALID_ARGUMENT,
                                      "new_slug must be non-empty")
        state, _fail = self._require_drv("music_state")
        if _fail: return _fail
        result = state.rename_track(album=album, old_slug=old_slug,
                                    new_slug=new_slug)
        if not result.get("success"):
            return ToolResult.failure(result.get("error", "NOT_FOUND"),
                                      f"rename_track {old_slug!r} failed")
        return ToolResult.success(data=result)

    # ───────── 094 Slice 2: session ─────────
    @verb(role="transform")
    @requires_driver("music_state", as_="state")
    def resume_session(self, *, state) -> ToolResult:
        """Restore the last-album context via the StateDriver (transform).

        Inputs: none.
        Returns: ``{session: {last_album?, last_track?, last_phase?, pending_actions?}}``.
        chain_next: ``music.album_progress`` on ``session.last_album`` if set.
        """
        return ToolResult.success(data={"session": state.get_session()})
