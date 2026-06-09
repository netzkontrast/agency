# agency-scaffold: v1
"""music production drivers — Spec 115.

Real disk-writing + SQLite-backed implementations of the StateDriver +
DBDriver Protocols. Counterparts to the in-memory `FakeStateDriver` +
`FakeDBDriver` in `drivers.py`.

- `FileStateDriver`: writes the bitwize-canonical layout under
  ``{content_root}/artists/{artist}/albums/{genre}/{slug}/``. Reads the
  templates already vendored at ``agency/capabilities/music/templates/``
  and renders them to disk at album/track creation time. Uses
  ``MusicConfig`` (loaded from `.agency/music-config.yaml` per-project)
  to know where to write.
- `SqliteDBDriver`: stdlib `sqlite3` backend for the catalogue cluster.
  Per-project DB at `.agency/music.db` by default; overridable via
  `db.path` in config. Implements the full DBDriver Protocol (7 typed
  methods + the 007 `cursor()` shim).
- `production_drivers(config)`: factory bundle symmetric to
  ``fake_drivers()`` — pass to ``Engine(..., drivers=production_drivers(cfg))``
  for a real-binding music engine.

CI never installs sqlite3 dev libs (stdlib only) and never touches the
filesystem outside tmp_path fixtures. Tests pin to `/tmp/.../music-test-*`.
"""
from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
from typing import Any

from .config import MusicConfig


# ─────────────────────────────── FileStateDriver ───────────────────────────────
class FileStateDriver:
    """Disk-writing StateDriver — bitwize-canonical layout.

    Layout (matches bitwize verbatim):

        {content_root}/
        ├── IDEAS.md
        └── artists/{artist}/albums/{genre}/{album-slug}/
            ├── README.md           (from templates/album.md)
            ├── RESEARCH.md         (documentary only)
            ├── SOURCES.md          (documentary only)
            ├── promo/{platform}.md (created on first promo_copy)
            └── tracks/{NN}-{slug}.md

    Production usage::

        cfg = MusicConfig.load()
        engine = Engine(drivers=production_drivers(cfg))
    """

    def __init__(self, config: MusicConfig | None = None,
                 templates_dir: str | None = None) -> None:
        self.config = config or MusicConfig.defaults()
        # The bundled templates ship at agency/capabilities/music/templates/
        if templates_dir:
            self._templates_dir = Path(templates_dir)
        else:
            self._templates_dir = Path(__file__).parent / "templates"
        self._session: dict = {}
        # In-memory mirrors for read-side fast-paths; the disk is canonical
        # but we cache the index so list_albums / list_tracks don't scan
        # the filesystem on every call.
        self._albums_cache: dict[str, dict] | None = None
        self._ideas: list[dict] = []
        self._tweet_counter = 0

    # ── path helpers ──
    def _content_root(self) -> Path:
        return Path(self.config.content_root).expanduser()

    def _album_root(self, artist: str, genre: str, slug: str) -> Path:
        return (self._content_root() / "artists" / self._slugify(artist)
                / "albums" / self._slugify(genre) / self._slugify(slug))

    @staticmethod
    def _slugify(text: str) -> str:
        bad = (" ", "/", "\\", ".", ",", "!", "?", "'", "\"", "(", ")", "[", "]")
        s = text.lower().strip()
        for ch in bad:
            s = s.replace(ch, "-")
        while "--" in s:
            s = s.replace("--", "-")
        return s.strip("-")

    def _render_template(self, name: str) -> str:
        tpl = self._templates_dir / f"{name}.md"
        if not tpl.is_file():
            return ""
        return tpl.read_text(encoding="utf-8")

    # ── 007 baseline ──
    def get(self, key: str) -> dict | None:
        """Read a state key — the FileStateDriver uses disk paths AS the key.

        ``key`` is a path RELATIVE to the content_root (e.g.
        ``albums/{slug}/README.md``). Returns ``{body: str}`` for files,
        ``None`` for missing.
        """
        path = (self._content_root() / key).expanduser()
        if not path.is_file():
            return None
        return {"body": path.read_text(encoding="utf-8")}

    def put(self, key: str, value: dict) -> None:
        """Write a state value to disk.

        ``value`` MAY carry a ``body`` key (the file content) — if so it's
        written verbatim. Other shapes fall back to a JSON dump.
        """
        path = (self._content_root() / key).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        if "body" in value:
            path.write_text(value["body"], encoding="utf-8")
        else:
            import json
            path.write_text(json.dumps(value, indent=2), encoding="utf-8")
        # Idea-key auto-mirror (matches the fake's behaviour)
        if key.startswith("idea:") and "idea_id" in value:
            self._ideas[:] = [i for i in self._ideas
                              if i.get("idea_id") != value["idea_id"]]
            self._ideas.append(dict(value))

    # ── 094 Slice 2 — ideas ──
    def list_ideas(self, status: str = "") -> list[dict]:
        if not status:
            return [dict(i) for i in self._ideas]
        return [dict(i) for i in self._ideas if i.get("status") == status]

    def update_idea(self, idea_id: str, fields: dict) -> None:
        for i in self._ideas:
            if i.get("idea_id") == idea_id:
                i.update(fields)
                return

    # ── 094 Slice 2 — album CRUD ──
    def create_album_root(self, artist: str, genre: str, slug: str,
                          title: str = "", type: str = "thematic") -> str:
        """Create the canonical bitwize album dir + render README.md + tracks/.

        Documentary albums (``type == 'documentary'``) get RESEARCH.md +
        SOURCES.md rendered too.
        """
        artist_use = artist or self.config.artist_name or "artist"
        album_root = self._album_root(artist_use, genre, slug)
        tracks_dir = album_root / "tracks"
        tracks_dir.mkdir(parents=True, exist_ok=True)
        # README.md
        readme = album_root / "README.md"
        body = self._render_template("album")
        if body:
            readme.write_text(body, encoding="utf-8")
        # Documentary supplements
        if type == "documentary":
            for tpl_name, dest in (("research", "RESEARCH.md"),
                                    ("sources", "SOURCES.md")):
                content = self._render_template(tpl_name)
                if content:
                    (album_root / dest).write_text(content, encoding="utf-8")
        # Artist seed README on first album for this artist
        artist_dir = (self._content_root() / "artists"
                      / self._slugify(artist_use))
        artist_readme = artist_dir / "README.md"
        if not artist_readme.exists():
            artist_body = self._render_template("artist")
            if artist_body:
                artist_readme.parent.mkdir(parents=True, exist_ok=True)
                artist_readme.write_text(artist_body, encoding="utf-8")
        # Genre seed README on first album in this genre
        genre_dir = artist_dir / "albums" / self._slugify(genre)
        genre_readme = genre_dir / "README.md"
        if not genre_readme.exists():
            genre_body = self._render_template("genre")
            if genre_body:
                genre_readme.parent.mkdir(parents=True, exist_ok=True)
                genre_readme.write_text(genre_body, encoding="utf-8")
        self._albums_cache = None     # invalidate
        return str(album_root.relative_to(self._content_root()))

    def find_album(self, query: str) -> list[dict]:
        albums = self._scan_albums()
        if not query:
            return list(albums.values())
        if query in albums:
            return [albums[query]]
        q = query.lower()
        return [a for a in albums.values()
                if q in a["slug"].lower() or q in a.get("title", "").lower()]

    def list_albums(self) -> list[dict]:
        return list(self._scan_albums().values())

    def _scan_albums(self) -> dict[str, dict]:
        if self._albums_cache is not None:
            return self._albums_cache
        out: dict[str, dict] = {}
        root = self._content_root() / "artists"
        if root.is_dir():
            for artist_dir in root.iterdir():
                if not artist_dir.is_dir():
                    continue
                albums_dir = artist_dir / "albums"
                if not albums_dir.is_dir():
                    continue
                for genre_dir in albums_dir.iterdir():
                    if not genre_dir.is_dir():
                        continue
                    for album_dir in genre_dir.iterdir():
                        if not album_dir.is_dir():
                            continue
                        slug = album_dir.name
                        out[slug] = {
                            "slug": slug,
                            "artist": artist_dir.name,
                            "genre": genre_dir.name,
                            "title": slug.replace("-", " ").title(),
                            "type": "thematic",
                            "status": "draft",
                            "root": str(album_dir.relative_to(self._content_root())),
                        }
        self._albums_cache = out
        return out

    def rename_album(self, old_slug: str, new_slug: str) -> dict:
        albums = self._scan_albums()
        if old_slug not in albums:
            return {"success": False, "error": "NOT_FOUND",
                    "old_slug": old_slug}
        old_root = self._content_root() / albums[old_slug]["root"]
        new_root = old_root.parent / new_slug
        if not old_root.exists():
            return {"success": False, "error": "NOT_FOUND",
                    "old_slug": old_slug}
        shutil.move(str(old_root), str(new_root))
        self._albums_cache = None
        return {"success": True, "old_slug": old_slug, "new_slug": new_slug,
                "title": albums[old_slug].get("title", new_slug),
                "tracks_updated": 0}

    # ── 094 Slice 2 — tracks ──
    def create_track(self, album: str, slug: str, title: str,
                     body: str = "") -> str:
        album_dir = self._find_album_dir(album)
        if album_dir is None:
            raise FileNotFoundError(f"album '{album}' not found")
        tracks_dir = album_dir / "tracks"
        tracks_dir.mkdir(exist_ok=True)
        track_file = tracks_dir / f"{slug}.md"
        if body:
            track_file.write_text(body, encoding="utf-8")
        else:
            tpl = self._render_template("track")
            if tpl:
                track_file.write_text(tpl, encoding="utf-8")
        return f"track:{slug}"

    def list_tracks(self, album: str) -> list[dict]:
        album_dir = self._find_album_dir(album)
        if album_dir is None:
            return []
        tracks_dir = album_dir / "tracks"
        if not tracks_dir.is_dir():
            return []
        out = []
        for f in sorted(tracks_dir.iterdir()):
            if f.suffix == ".md":
                slug = f.stem
                out.append({
                    "track_id": f"track:{slug}",
                    "album": album,
                    "slug": slug,
                    "title": slug.replace("-", " ").title(),
                    "status": "draft",
                    "body": f.read_text(encoding="utf-8") if f.is_file() else "",
                })
        return out

    def update_track_field(self, album: str, track: str, field: str,
                           value: str) -> None:
        # FileStateDriver stores track state in the markdown frontmatter.
        # For Slice 1 v1 we keep a simple side-car JSON; richer frontmatter
        # editing belongs in a future slice (uses a real markdown parser).
        album_dir = self._find_album_dir(album)
        if album_dir is None:
            return
        meta = album_dir / "tracks" / f"{track}.meta.json"
        import json
        data = json.loads(meta.read_text()) if meta.is_file() else {}
        data[field] = value
        meta.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def rename_track(self, album: str, old_slug: str,
                     new_slug: str) -> dict:
        album_dir = self._find_album_dir(album)
        if album_dir is None:
            return {"success": False, "error": "NOT_FOUND",
                    "album_slug": album, "old_slug": old_slug}
        old_file = album_dir / "tracks" / f"{old_slug}.md"
        new_file = album_dir / "tracks" / f"{new_slug}.md"
        if not old_file.is_file():
            return {"success": False, "error": "NOT_FOUND",
                    "album_slug": album, "old_slug": old_slug}
        shutil.move(str(old_file), str(new_file))
        return {"success": True, "album_slug": album,
                "old_slug": old_slug, "new_slug": new_slug,
                "title": new_slug.replace("-", " ").title()}

    def _find_album_dir(self, album_slug: str) -> Path | None:
        albums = self._scan_albums()
        info = albums.get(album_slug)
        if not info:
            return None
        return self._content_root() / info["root"]

    # ── 094 Slice 2 — aggregates + session ──
    def album_progress(self, album: str) -> dict:
        tracks = self.list_tracks(album)
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
        """Read bundled reference / data files.

        ``kind`` is the subdir under ``data/`` (e.g. ``reference``, ``genres``);
        ``slug`` is the path inside that subdir (e.g. ``mastering/loudness.md``).
        Returns ``{kind, slug, body}`` with empty body on miss.
        """
        data_dir = Path(__file__).parent / "data"
        target = data_dir / kind / slug
        if not target.exists() and not target.with_suffix(".md").exists():
            return {"kind": kind, "slug": slug, "body": ""}
        if target.is_file():
            return {"kind": kind, "slug": slug,
                    "body": target.read_text(encoding="utf-8")}
        # Try .md suffix
        md = target.with_suffix(".md")
        if md.is_file():
            return {"kind": kind, "slug": slug,
                    "body": md.read_text(encoding="utf-8")}
        # Directory — list children
        return {"kind": kind, "slug": slug,
                "body": "\n".join(sorted(p.name for p in target.iterdir()))}

    def list_keys(self, prefix: str = "") -> list[str]:
        """List state keys matching prefix. For FileStateDriver this scans
        the content_root for matching paths."""
        root = self._content_root()
        if not root.is_dir():
            return []
        out = []
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            rel = str(p.relative_to(root))
            if not prefix or rel.startswith(prefix):
                out.append(rel)
        return sorted(out)


# ─────────────────────────────── SqliteDBDriver ───────────────────────────────
class SqliteDBDriver:
    """SQLite-backed DBDriver — stdlib `sqlite3`, no external deps.

    Per the user directive replaces Postgres as the agency default.
    Per-project DB at `.agency/music.db` by default; configurable via
    `db.path` in `.agency/music-config.yaml`.
    """

    def __init__(self, config: MusicConfig | None = None,
                 db_path: str | None = None) -> None:
        self.config = config or MusicConfig.defaults()
        path = db_path or self.config.db_path
        if path != ":memory:":
            db_file = Path(path).expanduser()
            db_file.parent.mkdir(parents=True, exist_ok=True)
            path = str(db_file)
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        cur = self._conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                album        TEXT NOT NULL,
                body         TEXT NOT NULL,
                platform     TEXT NOT NULL DEFAULT 'x',
                status       TEXT NOT NULL DEFAULT 'draft',
                scheduled_at TEXT,
                posted_at    TEXT,
                created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                slug         TEXT PRIMARY KEY,
                album        TEXT NOT NULL,
                title        TEXT,
                status       TEXT NOT NULL DEFAULT 'draft',
                explicit     INTEGER NOT NULL DEFAULT 0,
                created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        for stmt in (
            "CREATE INDEX IF NOT EXISTS idx_tweets_album ON tweets(album)",
            "CREATE INDEX IF NOT EXISTS idx_tweets_status ON tweets(status)",
            "CREATE INDEX IF NOT EXISTS idx_tweets_album_status ON tweets(album, status)",
            "CREATE INDEX IF NOT EXISTS idx_tracks_album ON tracks(album)",
        ):
            cur.execute(stmt)
        self._conn.commit()
        cur.close()

    def cursor(self):
        return self._conn.cursor()

    def create_tweet(self, album: str, body: str, scheduled_at: str,
                     platform: str = "x") -> int:
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO tweets (album, body, scheduled_at, platform) "
            "VALUES (?, ?, ?, ?)",
            (album, body, scheduled_at, platform))
        tid = cur.lastrowid
        self._conn.commit()
        cur.close()
        return tid

    def update_tweet(self, tweet_id: int, fields: dict) -> None:
        if not fields:
            return
        sets = ", ".join(f"{k} = ?" for k in fields)
        params = list(fields.values()) + [tweet_id]
        cur = self._conn.cursor()
        cur.execute(f"UPDATE tweets SET {sets} WHERE id = ?", params)
        self._conn.commit()
        cur.close()

    def delete_tweet(self, tweet_id: int) -> None:
        cur = self._conn.cursor()
        cur.execute("DELETE FROM tweets WHERE id = ?", (tweet_id,))
        self._conn.commit()
        cur.close()

    def list_tweets(self, album: str = "", status: str = "",
                    limit: int = 100) -> list[dict]:
        cur = self._conn.cursor()
        clauses, params = [], []
        if album:
            clauses.append("album = ?")
            params.append(album)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)
        cur.execute(f"SELECT * FROM tweets{where} ORDER BY id LIMIT ?",
                    params)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def search_tweets(self, query: str, limit: int = 50) -> list[dict]:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM tweets WHERE LOWER(body) LIKE ? "
            "ORDER BY id LIMIT ?",
            (f"%{query.lower()}%", limit))
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    def tweet_stats(self, album: str = "") -> dict:
        cur = self._conn.cursor()
        if album:
            cur.execute(
                "SELECT status, COUNT(*) as c FROM tweets WHERE album = ? "
                "GROUP BY status", (album,))
        else:
            cur.execute(
                "SELECT status, COUNT(*) as c FROM tweets GROUP BY status")
        rows = cur.fetchall()
        cur.close()
        total = sum(r["c"] for r in rows)
        by_status = {r["status"]: r["c"] for r in rows}
        return {"album": album or "*", "total": total,
                "by_status": by_status}

    def sync_album_tweets(self, album: str,
                          tweets: list[dict]) -> dict:
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM tweets WHERE album = ?",
                    (album,))
        existing = cur.fetchone()["c"]
        cur.execute("DELETE FROM tweets WHERE album = ?", (album,))
        for t in tweets:
            self.create_tweet(
                album=album, body=t.get("body", ""),
                scheduled_at=t.get("scheduled_at", ""),
                platform=t.get("platform", "x"))
        return {"album": album, "removed": existing,
                "created": len(tweets)}


# ─────────────────────────────── factory ───────────────────────────────
def production_drivers(config: MusicConfig | None = None) -> dict[str, Any]:
    """Production driver bundle — symmetric to ``fake_drivers()``.

    Wires real FileStateDriver + SqliteDBDriver alongside the deterministic
    Fake* drivers for Text/Audio/Cloud (which don't have production
    counterparts in this spec; they ship in a future slice when ffmpeg /
    pyloudnorm / boto3 extras land).
    """
    from .drivers import FakeAudioDriver, FakeCloudDriver, FakeTextDriver
    cfg = config or MusicConfig.load()
    return {
        "music_state": FileStateDriver(cfg),
        "music_text":  FakeTextDriver(),
        "music_audio": FakeAudioDriver(),
        "music_db":    SqliteDBDriver(cfg),
        "music_cloud": FakeCloudDriver(),
    }
