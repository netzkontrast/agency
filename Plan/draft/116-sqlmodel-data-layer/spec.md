---
spec_id: "116"
slug: sqlmodel-data-layer
status: draft
state: draft
last_updated: 2026-06-09
owner: "@agency"
depends_on: ["093", "115"]
affects:
  - pyproject.toml                                         # SQLModel as core dep
  - agency/data/                                           # NEW package: SQLModel models + session factory
  - agency/data/__init__.py                                # NEW: public API
  - agency/data/models.py                                  # NEW: shared base + utility mixins
  - agency/data/session.py                                 # NEW: get_session() + URL resolver
  - agency/capabilities/music/data_models.py               # NEW: music domain models (Tweet, TrackMeta, Idea, AlbumClaim)
  - agency/capabilities/music/drivers_production.py        # CHANGED: SqliteDBDriver swaps raw SQL → SQLModel
  - agency/capabilities/music/migrations/db_init.py        # CHANGED: SQLModel.metadata.create_all
  - tests/test_data_models.py                              # NEW: round-trip tests
  - tests/test_music_production.py                         # CHANGED: SqliteDBDriver via SQLModel
domain: data / persistence / refactor
wave: 8
parent_spec: "093"
---

# Spec 116 — SQLModel Data Layer Refactor

## Why

After Specs 094-100 + 115 (production binding) shipped, the music capability
persists **structured non-graph data** through three different mechanisms:

1. **Raw SQL** in `SqliteDBDriver` (Spec 115): `cur.execute("INSERT INTO
   tweets …", (...))` — fast but untyped, schema duplication between
   `db_init.py` and call sites, validation lives in the verb body.
2. **JSON side-cars** in `FileStateDriver._slugify`-derived paths
   (`tracks/{slug}.meta.json`): track status, explicit flag, etc — stored as
   loose dicts on disk.
3. **In-memory dicts** in `FakeStateDriver._albums` + `_tracks` + `_ideas` +
   `_session`: ad-hoc shapes that match the production driver by convention,
   not by contract.

Three persistence shapes for one domain. The contract drift risk is real
(already caught by reviews: `streaming:{album}:{platform}` key shape spread
across 3 verbs, `idea_id` mirror coupling between `put` + `update_idea`).

This spec replaces all three with **one typed SQLModel layer**:

- One Pydantic + SQLAlchemy declaration per domain entity (Tweet, TrackMeta,
  AlbumMeta, Idea, AlbumClaim, AlbumVerification).
- One `agency/data/session.py` session factory (per-project `.agency/music.db`
  by default; configurable URL via env / config).
- Typed `select(Tweet).where(...)` queries replace raw SQL.
- Pydantic field validators replace duck-typed dict checks at write time.
- `SQLModel.metadata.create_all(engine)` replaces the hand-rolled
  `_SCHEMAS["sqlite"|"postgres"]` map in `db_init.py`.

The **graph** stays as-is. graphqlite owns provenance (Intent, Invocation,
Lifecycle, Gate, Artefact + the SERVES / PRODUCES / PASSED / BLOCKED_ON
edges). SQLModel owns structured **domain data** that doesn't need
bi-temporal versioning or edge traversal.

> Per the user directive (2026-06-09): "SQLModel as dependency". This spec
> adds `sqlmodel` to `[project].dependencies` as a core agency dep, not an
> optional extra. The dep cost is justified by the data-layer unification
> + type-safety win.

## Done When

- [ ] **`sqlmodel` listed as a core dependency** in `pyproject.toml`
  `[project].dependencies` (alongside `fastmcp` + `graphqlite` + `httpx`).
  Pulls `pydantic` (already present) + `sqlalchemy` (new transitive).
  Documented in CLAUDE.md "Dev" section.
- [ ] **`agency/data/`** package ships:
  - `__init__.py` — public re-exports (`get_session`, `BaseModel`,
    `create_all`, the model registry).
  - `models.py` — shared `TimestampMixin` (`created_at`, `updated_at`),
    `SlugMixin` (validated slug pattern), and the `BaseModel = SQLModel`
    alias the rest of the codebase imports from.
  - `session.py` — `get_session(url: str | None = None)` factory; uses
    `sqlalchemy.engine.url.URL` to support `sqlite:///`, `postgresql://`,
    in-memory `sqlite:///:memory:`. Defaults to `.agency/music.db` in
    SQLite. Reads `AGENCY_DATA_URL` env var override.
- [ ] **`agency/capabilities/music/data_models.py`** ships the 6 music
  domain SQLModel classes:
  - `Tweet(SQLModel, table=True)` — id PK, album, body, platform, status
    (enum-constrained at field-level), scheduled_at, posted_at, created_at.
  - `TrackMeta(SQLModel, table=True)` — slug PK, album FK→AlbumMeta, title,
    status (enum), explicit (bool), created_at.
  - `AlbumMeta(SQLModel, table=True)` — slug PK, artist, genre, title,
    type (enum), status (enum), target_lufs (float), created_at.
  - `Idea(SQLModel, table=True)` — id PK, text, status (enum), promoted_to
    (nullable FK→AlbumMeta.slug), captured_at.
  - `AlbumClaim(SQLModel, table=True)` — id PK, album FK, text, source_uri,
    domain (enum), verified (enum), confidence (float), captured_at.
  - `AlbumVerification(SQLModel, table=True)` — id PK, claim FK→AlbumClaim,
    verdict (enum), verified_by, verified_at, notes.
- [ ] **`SqliteDBDriver` rewritten** to use SQLModel sessions internally:
  - `create_tweet(...)` → `with Session(engine) as s: t = Tweet(...);
    s.add(t); s.commit(); s.refresh(t); return t.id`
  - `list_tweets(album, status, limit)` → typed
    `select(Tweet).where(...).limit(...)` query
  - `tweet_stats` → `select(Tweet.status, func.count()).group_by(...)`
  - All 7 typed methods preserved (same Protocol surface; internal
    implementation refactored).
  - The 007 `cursor()` shim returns the underlying `sqlalchemy.engine.
    Connection` cursor for raw-SQL backward-compat callers.
- [ ] **`FileStateDriver` refactored** to delegate metadata persistence to
  SQLModel (instead of JSON side-cars + in-memory dicts):
  - `create_album_root` still writes the disk tree (the file layout is the
    user's deliverable); it ALSO upserts an `AlbumMeta` row.
  - `list_albums` / `find_album` query `AlbumMeta` via SQLModel (faster +
    typed than scanning the filesystem on every call).
  - `update_track_field` → SQLModel update on `TrackMeta` (replaces
    `tracks/{slug}.meta.json`).
  - `list_ideas` / `update_idea` → SQLModel query on `Idea`.
  - The streaming-URL key shape (`streaming:{album}:{platform}`) becomes a
    typed `StreamingURL(album, platform, url)` table — removes the
    private-attribute `list_keys` workaround entirely.
- [ ] **`FakeStateDriver` rewritten** to use `sqlite:///:memory:` SQLModel
  session under the hood — so the fake and the real driver share the
  same schema + query path. Tests gain real type-safety without disk I/O.
  The in-memory dict caches (`_albums`, `_tracks`, `_ideas`, `_session`)
  are removed.
- [ ] **`migrations/db_init.py` simplified** to a 3-liner:
  `SQLModel.metadata.create_all(get_session().get_bind())`. The dialect-aware
  branching from Spec 115 is no longer needed — SQLAlchemy emits the right
  dialect from the engine URL.
- [ ] **No behavioural regression on the 97 verbs**. Every test from
  test_music_*.py keeps passing — the SQLModel refactor is implementation-
  only; verb signatures + return shapes unchanged.
- [ ] **`tests/test_data_models.py` ships** (~15 tests):
  - One round-trip test per model: create → read → update → delete.
  - Enum bites per model: `Tweet.status` rejects unknown values at
    Pydantic-validation time (raises `ValidationError`).
  - FK enforcement: `TrackMeta.album` referencing a non-existent
    AlbumMeta.slug raises `IntegrityError` on commit.
  - `get_session()` URL resolution test (env override + default).
  - Migration test: `SQLModel.metadata.create_all(engine)` is idempotent.
- [ ] **`TODO.md` row 116 added** (Partial → Shipped once tests Green).
- [ ] **Doctrine note in CLAUDE.md**: a new paragraph under §"How to use the
  agency MCP" describing the two-store doctrine: graphqlite for provenance
  edges, SQLModel for structured domain data, never mix.

## Design

### Two-store doctrine

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  GRAPH (graphqlite, .agency/session.db)                                 │
│  ──────────────────────────────────────                                 │
│  Nodes: Intent, Invocation, Lifecycle, Gate, Artefact, Agent            │
│  Edges: SERVES, PRODUCES, PASSED, BLOCKED_ON, PERFORMED_BY, DERIVED_FROM│
│  PROMOTED_TO, RECORDED_FOR (the music-cap edges from Spec 094)          │
│  Purpose: provenance moat — release audit is one graph traversal.       │
│  Bi-temporal: every node has vfrom/vto for time-travel queries.         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │  domain entities reference each other
                                  │  via stable slugs / IDs, not via
                                  │  graph IDs.
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  STRUCTURED DATA (SQLModel, .agency/music.db)                           │
│  ────────────────────────────────────────────                           │
│  Tables: AlbumMeta, TrackMeta, Tweet, Idea, AlbumClaim,                 │
│          AlbumVerification, StreamingURL                                │
│  Typed Pydantic models — enum-validated at write time.                  │
│  FK constraints — relational integrity at the DB level.                 │
│  No bi-temporal versioning — these are mutable domain records.          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

A verb that creates an album writes BOTH stores:
- **Graph** records the `Album` node + `SERVES intent` edge — provenance.
- **SQLModel** upserts the `AlbumMeta` row — domain data.

Reads go to whichever store fits:
- "Which intent ordered this Album?" → graph query.
- "List all draft tracks for album X" → SQLModel query.

### Model file shape (`agency/capabilities/music/data_models.py`)

```python
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class AlbumStatus(str, Enum):
    draft = "draft"
    in_production = "in-production"
    mastered = "mastered"
    released = "released"

class AlbumMeta(SQLModel, table=True):
    __tablename__ = "album_meta"
    slug: str = Field(primary_key=True, max_length=64)
    artist: str = Field(index=True)
    genre: str = Field(index=True)
    title: str
    type: str = Field(default="thematic")
    status: AlbumStatus = Field(default=AlbumStatus.draft)
    target_lufs: float = Field(default=-14.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    tracks: list["TrackMeta"] = Relationship(back_populates="album")
    tweets: list["Tweet"] = Relationship(back_populates="album_ref")
    claims: list["AlbumClaim"] = Relationship(back_populates="album_ref")
```

### SqliteDBDriver method delta (post-refactor)

```python
class SqliteDBDriver:
    def __init__(self, config: MusicConfig | None = None,
                 db_url: str | None = None):
        from agency.data.session import get_session, get_engine
        self.config = config or MusicConfig.defaults()
        url = db_url or f"sqlite:///{self.config.db_path}"
        self._engine = get_engine(url)
        SQLModel.metadata.create_all(self._engine)

    def create_tweet(self, album, body, scheduled_at, platform="x"):
        from .data_models import Tweet
        with Session(self._engine) as s:
            t = Tweet(album=album, body=body,
                      scheduled_at=scheduled_at, platform=platform)
            s.add(t); s.commit(); s.refresh(t)
            return t.id

    def list_tweets(self, album="", status="", limit=100):
        from .data_models import Tweet
        with Session(self._engine) as s:
            stmt = select(Tweet)
            if album:  stmt = stmt.where(Tweet.album == album)
            if status: stmt = stmt.where(Tweet.status == status)
            return [t.dict() for t in s.exec(stmt.limit(limit))]
```

### Why core dep (not optional extra)

Bitwize-music ships `psycopg2-binary` as an optional extra because Postgres
is a system dep. SQLModel is **stdlib-installable** (pure Python on top of
`pydantic` + `sqlalchemy`, both wheels available everywhere). Making it a
core dep:

- Unifies the persistence story across all capabilities (not just music).
- Eliminates the "is the extra installed?" branching that bitwize has to do.
- Enables future caps (catalogue, dossier, novel-research) to use the same
  pattern without an extra-install requirement per cap.

The transitive `sqlalchemy` install is the cost. Acceptable per the user
directive ("SQLModel as dependencie").

## Migration strategy

This spec is **backwards-compatible**: the 7-method DBDriver Protocol is
preserved (signatures, return shapes, semantics). The 16-method StateDriver
Protocol is also preserved. The refactor is implementation-internal.

Migration steps:

1. Land the `agency/data/` package + base session factory (no consumers yet).
2. Land `music/data_models.py` defining the 7 SQLModel tables.
3. Refactor `SqliteDBDriver` to use SQLModel internally; tests must keep
   passing.
4. Refactor `FileStateDriver` to upsert SQLModel rows alongside disk writes;
   `find_album` / `list_albums` move to SQLModel queries (filesystem scan
   becomes a fallback for raw-disk inspection).
5. Refactor `FakeStateDriver` to use `sqlite:///:memory:` so the fake and
   real share the schema.
6. Run the full music test suite — every test must keep passing without
   change.

No existing data migration needed: this spec ships into a music capability
whose only "real" persistence (Spec 115's SqliteDBDriver) has just landed.
Empty DBs are forward-compatible.

## Open Questions

1. **Alembic for migrations?** Not in this spec. `SQLModel.metadata.create_all`
   is enough for v1; Alembic adds value when schemas evolve, which we don't
   yet need.
2. **Async session?** Not yet. The agency engine is sync (FastMCP wrappers
   are sync for verbs). Async SQLModel can land in a future slice if the
   `research` capability's verifier ever fans out concurrently.
3. **Repository pattern (separate query layer) vs models-with-query-methods?**
   Repository pattern. Each driver owns its queries; the SQLModel classes
   stay declarative.
4. **Should the graph also migrate to SQLModel?** **No**. The graph is
   bi-temporal + edge-rich + the heart of provenance. graphqlite is the
   right tool. SQLModel covers domain data only.

## Followup

(Populated when the PR ships.)
