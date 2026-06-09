# agency-scaffold: v1
"""music drivers — the five external I/O boundaries the music capability reaches
through, as Spec-002 ``Driver`` protocols (Option B: typed, named methods; the
uniform contract is the RETURN TYPE via the wrapping verb, not a ``dispatch(op)``).

Each driver is a marker ``Boundary`` exposing its own typed methods (the ``jules.py``
``create/get/list`` shape). The capability resolves them via ``ctx.get_driver(name)``
(Spec 002's ``DriverRegistry``) — so the music capability edits NO file under
``agency/engine.py`` and a host binds real drivers while tests bind deterministic fakes.

This module ships BOTH the Protocols (the contract) and small deterministic FAKES (so
``tests/test_music_*`` runs with no ffmpeg / Postgres / R2 / network). A real
deployment registers production drivers via
``Engine(..., drivers={"music_state": RealStateDriver(), ...})``.

Migrated from ``examples/music_drivers.py`` under Spec 094 (music graduates
from ``examples/`` into a first-class cluster). The legacy module remains as a
deprecation re-export shim for one spec cycle.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from agency.capability import Driver


# ─────────────────────────── the five Driver protocols ───────────────────────────
@runtime_checkable
class StateDriver(Driver, Protocol):
    """Album/track state persistence (bitwize's unified state cache).

    Spec 094 Slice 2 extends the surface with 14 new methods that mirror the
    bitwize-music handler shape (graph-canonical in agency; on-disk reads/writes
    behind the driver). A real production driver writes the bitwize-shaped
    ``artists/{artist}/albums/{genre}/{slug}/`` tree; the fake holds an in-memory
    dict so tests run hermetically.
    """
    # ── 007 baseline (unchanged) ──
    def get(self, key: str) -> dict | None: ...
    def put(self, key: str, value: dict) -> None: ...

    # ── 094 Slice 2 — lifecycle method delta ──
    def list_ideas(self, status: str = "") -> list[dict]: ...
    def update_idea(self, idea_id: str, fields: dict) -> None: ...
    def create_album_root(self, artist: str, genre: str, slug: str,
                          title: str = "", type: str = "thematic") -> str: ...
    def find_album(self, query: str) -> list[dict]: ...
    def list_albums(self) -> list[dict]: ...
    def create_track(self, album: str, slug: str, title: str,
                     body: str = "") -> str: ...
    def list_tracks(self, album: str) -> list[dict]: ...
    def update_track_field(self, album: str, track: str, field: str,
                           value: str) -> None: ...
    def rename_album(self, old_slug: str, new_slug: str) -> dict: ...
    def rename_track(self, album: str, old_slug: str,
                     new_slug: str) -> dict: ...
    def album_progress(self, album: str) -> dict: ...
    def get_session(self) -> dict: ...
    def update_session(self, fields: dict) -> None: ...
    def resolve_path(self, kind: str, **vars) -> str: ...
    def read_data(self, kind: str, slug: str) -> dict: ...


@runtime_checkable
class TextDriver(Driver, Protocol):
    """Pure text analysis (syllables, pronunciation) — no external process."""
    def syllables(self, word: str) -> int: ...


@runtime_checkable
class AudioDriver(Driver, Protocol):
    """Loudness/mastering — stands in for pyloudnorm + ffmpeg."""
    def read_loudness(self, path: str) -> float: ...
    def run_ffmpeg(self, args: list[str]) -> dict: ...


@runtime_checkable
class DBDriver(Driver, Protocol):
    """A psycopg2-shaped cursor source (catalogue DB), no Postgres host required."""
    def cursor(self): ...


@runtime_checkable
class CloudDriver(Driver, Protocol):
    """Object storage / CDN (R2) + URL checks."""
    def url_head(self, url: str) -> int: ...
    def r2_put(self, key: str, data: bytes) -> dict: ...


# ─────────────────────────────── deterministic fakes ───────────────────────────────
class FakeStateDriver:
    """In-memory StateDriver fake.

    Spec 094 Slice 2: ports the bitwize ``state_cache.json`` shape — albums
    keyed by slug, tracks per album, ideas list, session dict — into a
    deterministic in-memory store. Production binds a real disk-backed driver
    that mirrors the bitwize ``artists/{artist}/albums/{genre}/{slug}/`` tree;
    the fake skips disk and keeps the same surface for tests.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}
        self._albums: dict[str, dict] = {}
        self._tracks: dict[str, list[dict]] = {}      # album_slug → [track,…]
        self._ideas: list[dict] = []                  # ordered for stable list
        self._session: dict = {}
        self._counter = 0

    # ── 007 baseline ──
    def get(self, key: str) -> dict | None:
        return self._store.get(key)

    def put(self, key: str, value: dict) -> None:
        self._store[key] = dict(value)
        # Mirror idea writes into the structured ideas list so list_ideas /
        # update_idea see them. Production driver writes both surfaces too
        # (state_cache.json plus IDEAS.md). The mirror is keyed by `idea_id`
        # to keep updates idempotent.
        if key.startswith("idea:") and "idea_id" in value:
            self._ideas[:] = [
                i for i in self._ideas
                if i.get("idea_id") != value["idea_id"]
            ]
            self._ideas.append(dict(value))

    # ── 094 Slice 2: ideas ──
    def list_ideas(self, status: str = "") -> list[dict]:
        if not status:
            return [dict(i) for i in self._ideas]
        return [dict(i) for i in self._ideas if i.get("status") == status]

    def update_idea(self, idea_id: str, fields: dict) -> None:
        for i in self._ideas:
            if i.get("idea_id") == idea_id:
                i.update(fields)
                return

    # ── 094 Slice 2: album CRUD ──
    def create_album_root(self, artist: str, genre: str, slug: str,
                          title: str = "", type: str = "thematic") -> str:
        root = f"artists/{artist}/albums/{genre}/{slug}"
        self._albums[slug] = {
            "slug": slug, "artist": artist, "genre": genre,
            "title": title or slug, "type": type, "status": "draft",
            "root": root,
        }
        self._tracks.setdefault(slug, [])
        return root

    def find_album(self, query: str) -> list[dict]:
        if not query:
            return [dict(a) for a in self._albums.values()]
        # exact-slug match first, then substring (both directions)
        if query in self._albums:
            return [dict(self._albums[query])]
        q = query.lower()
        return [dict(a) for a in self._albums.values()
                if q in a["slug"].lower() or a["slug"].lower() in q
                or q in a["title"].lower()]

    def list_albums(self) -> list[dict]:
        return [dict(a) for a in self._albums.values()]

    def rename_album(self, old_slug: str, new_slug: str) -> dict:
        if old_slug not in self._albums:
            return {"success": False, "error": "NOT_FOUND",
                    "old_slug": old_slug}
        album = self._albums.pop(old_slug)
        album["slug"] = new_slug
        album["root"] = album["root"].rsplit("/", 1)[0] + "/" + new_slug
        self._albums[new_slug] = album
        self._tracks[new_slug] = self._tracks.pop(old_slug, [])
        return {"success": True, "old_slug": old_slug, "new_slug": new_slug,
                "title": album["title"], "tracks_updated": len(self._tracks[new_slug])}

    # ── 094 Slice 2: tracks ──
    def create_track(self, album: str, slug: str, title: str,
                     body: str = "") -> str:
        self._counter += 1
        track_id = f"track:{self._counter}"
        self._tracks.setdefault(album, []).append({
            "track_id": track_id, "album": album, "slug": slug,
            "title": title, "status": "draft", "body": body,
        })
        return track_id

    def list_tracks(self, album: str) -> list[dict]:
        return [dict(t) for t in self._tracks.get(album, [])]

    def update_track_field(self, album: str, track: str, field: str,
                           value: str) -> None:
        for t in self._tracks.get(album, []):
            if t["slug"] == track:
                t[field] = value
                return

    def rename_track(self, album: str, old_slug: str,
                     new_slug: str) -> dict:
        for t in self._tracks.get(album, []):
            if t["slug"] == old_slug:
                t["slug"] = new_slug
                return {"success": True, "album_slug": album,
                        "old_slug": old_slug, "new_slug": new_slug,
                        "title": t["title"]}
        return {"success": False, "error": "NOT_FOUND",
                "album_slug": album, "old_slug": old_slug}

    # ── 094 Slice 2: aggregates + session ──
    def album_progress(self, album: str) -> dict:
        tracks = self._tracks.get(album, [])
        by_status: dict[str, int] = {}
        for t in tracks:
            by_status[t["status"]] = by_status.get(t["status"], 0) + 1
        completed = by_status.get("mastered", 0)
        pct = (100 * completed // len(tracks)) if tracks else 0
        return {"album_slug": album, "track_count": len(tracks),
                "tracks_completed": completed,
                "completion_percentage": pct,
                "tracks_by_status": by_status}

    def get_session(self) -> dict:
        return dict(self._session)

    def update_session(self, fields: dict) -> None:
        self._session.update(fields)

    def resolve_path(self, kind: str, **vars) -> str:
        templates = {
            "album": "artists/{artist}/albums/{genre}/{slug}",
            "track": "artists/{artist}/albums/{genre}/{album}/tracks/{slug}.md",
            "artist": "artists/{artist}",
            "genre": "artists/{artist}/albums/{genre}",
            "ideas": "IDEAS.md",
        }
        tpl = templates.get(kind, "")
        try:
            return tpl.format(**vars)
        except KeyError:
            return tpl

    def read_data(self, kind: str, slug: str) -> dict:
        # Stub — production reads `data/{kind}/{slug}.{md,yaml}`. Slice 1's
        # vendored genres + reference docs back this in the real driver.
        return {"kind": kind, "slug": slug, "body": ""}


class FakeTextDriver:
    _VOWELS = "aeiouy"

    def syllables(self, word: str) -> int:
        """A deterministic syllable heuristic (vowel-group count, ≥ 1) — driver-free
        text math, no external pronunciation dictionary."""
        w = word.lower().strip()
        count, prev_vowel = 0, False
        for ch in w:
            is_vowel = ch in self._VOWELS
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if w.endswith("e") and count > 1:        # silent trailing 'e'
            count -= 1
        return max(1, count)


class FakeAudioDriver:
    """Returns a fixed loudness so a mastering verb is deterministic in tests."""
    def __init__(self, loudness: float = -14.0) -> None:
        self._loudness = loudness
        self.ffmpeg_calls: list[list[str]] = []

    def read_loudness(self, path: str) -> float:
        return self._loudness

    def run_ffmpeg(self, args: list[str]) -> dict:
        self.ffmpeg_calls.append(list(args))
        return {"ok": True, "args": list(args)}


class _FakeCursor:
    def __init__(self, rows: list[tuple]) -> None:
        self._rows = rows

    def execute(self, sql: str, params: tuple = ()) -> None:
        self._sql = sql

    def fetchall(self) -> list[tuple]:
        return list(self._rows)

    def close(self) -> None:
        pass


class FakeDBDriver:
    def __init__(self, rows: list[tuple] | None = None) -> None:
        self._rows = rows or [("track-1", "mastered"), ("track-2", "draft")]

    def cursor(self):
        return _FakeCursor(self._rows)


class FakeCloudDriver:
    """`url_head` is real (stdlib-shaped); `r2_put` reports DEPENDENCY_MISSING when
    unconfigured, so the verb returns a typed failure instead of importing boto3."""
    def __init__(self, configured: bool = False, head_status: int = 200) -> None:
        self._configured = configured
        self._head_status = head_status

    def url_head(self, url: str) -> int:
        return self._head_status

    def r2_put(self, key: str, data: bytes) -> dict:
        if not self._configured:
            return {"ok": False, "error": "DEPENDENCY_MISSING"}
        return {"ok": True, "key": key, "bytes": len(data)}


def fake_drivers() -> dict[str, object]:
    """The driver bundle a test passes to ``Engine(..., drivers=fake_drivers())``."""
    return {
        "music_state": FakeStateDriver(),
        "music_text": FakeTextDriver(),
        "music_audio": FakeAudioDriver(),
        "music_db": FakeDBDriver(),
        "music_cloud": FakeCloudDriver(),
    }
