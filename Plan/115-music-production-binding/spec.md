---
spec_id: "115"
slug: music-production-binding
status: draft
last_updated: 2026-06-09
owner: "@agency"
depends_on: ["093", "094", "097"]
affects:
  - agency/capabilities/music/drivers_production.py    # NEW: FileStateDriver + SqliteDBDriver
  - agency/capabilities/music/config.py                # NEW: config loader
  - agency/capabilities/music/migrations/db_init.py    # extended: dialect-aware schema
  - agency/capabilities/music/templates/promo/         # NEW: 6 promo platform templates ported
  - agency/capabilities/music/templates/research.md    # NEW: research template ported
  - agency/capabilities/music/templates/sources.md     # NEW: sources template ported
  - agency/capabilities/music/_main.py                 # NEW: 4 production-binding verbs
  - tests/test_music_production.py                     # NEW: disk-roundtrip tests
  - examples/music_setup.py                            # NEW: new-album demo runner
domain: music / production / persistence
wave: 8
parent_spec: "093"
---

# Spec 115 — Music Production Binding

## Why

Specs 094-100 shipped the music capability as a library — 97 verbs across 7 cluster
slices, all backed by in-memory `FakeStateDriver` + `FakeDBDriver` + `FakeCloudDriver`.
Tests pass; no disk is written; no Postgres runs. Users cannot actually use the
capability to manage their own music projects until a **production-binding layer**
exists.

This spec ships that layer:

1. **`FileStateDriver`** — a real disk-writing implementation of the StateDriver
   Protocol. Writes the bitwize-canonical layout (`{content_root}/artists/{artist}/
   albums/{genre}/{slug}/`) using the templates already vendored in
   `agency/capabilities/music/templates/`.
2. **`SqliteDBDriver`** — replaces Postgres with stdlib `sqlite3`. The bitwize
   catalogue cluster uses Postgres; per user directive we ship SQLite as the
   default agency backend (zero external dep, file-per-project, fits the
   `.agency/` substrate).
3. **Config layer** — `.agency/music-config.yaml` (per-project) with an optional
   `~/.agency-music/config.yaml` global fallback. Same shape as bitwize's
   `~/.bitwize-music/config.yaml` for compatibility.
4. **4 net-new production-binding verbs** — `get_config`, `load_override`,
   `get_reference`, `format_clipboard` — covering the bitwize MCP functions that
   are required for setup/config flows but were deferred during 094-100.
5. **2 net-new templates** — `research.md` + `sources.md` ported verbatim from
   bitwize (097/099 Followup deferred these).
6. **6 promo platform templates** — `campaign.md`, `facebook.md`, `instagram.md`,
   `tiktok.md`, `twitter.md`, `youtube.md` — ported verbatim from
   `bitwize/templates/promo/`.
7. **`new_album` walkable skill** — mirrors bitwize's `new-album` setup flow:
   parse-args → validate-genre → create_album → render-templates → confirm.

## Bitwize MCP function coverage audit

Bitwize ships **110 MCP-registered tool functions** across 15 handler modules. After
Specs 094-100 we've ported 97 verbs; this spec adds the remaining 4 that production
binding REQUIRES. The deferred handfuls (clipboard formatting, version queries,
session-restore variants) are either covered by agency primitives (`skills` cap,
`agency_doctor`, `resume_session`) or out-of-scope (`migrate_audio_layout` is a
one-shot migration; `check_venv_health` is bitwize-specific).

### Coverage matrix (4 new verbs vs 13 unmapped bitwize fns)

| Bitwize fn | Agency target | Status |
|---|---|---|
| `get_config` | NEW `music.get_config` (this spec) | will ship |
| `load_override` | NEW `music.load_override` (this spec) | will ship |
| `get_reference` | NEW `music.get_reference` (this spec) | will ship |
| `format_for_clipboard` | NEW `music.format_clipboard` (this spec) | will ship |
| `get_album_full` | covered by `album_progress` + `find_album` | shipped |
| `get_track` | covered by `list_tracks` (single-track filter) | shipped |
| `list_track_files` | covered by `list_tracks` body | shipped |
| `list_skills` | covered by `agency.skills.list` | substrate |
| `get_skill` | covered by `agency.skills.get` | substrate |
| `get_plugin_version` | covered by `agency_doctor` | substrate |
| `get_python_command` | not needed (we're a Python plugin already) | out-of-scope |
| `check_venv_health` | covered by `agency_doctor` | substrate |
| `cleanup_legacy_venvs` | bitwize-specific maintenance | out-of-scope |
| `migrate_audio_layout` | bitwize-specific one-shot | out-of-scope |
| `generate_album_sampler` | DEFERRED to a future audio slice | out-of-scope here |

Per the user directive ("go through every bitwize MCP function"): 97 ported + 4
new in this spec + 6 substrate-covered + 3 out-of-scope = **110 accounted for**.

## Done When

- [ ] `FileStateDriver` implements all 16 StateDriver Protocol methods + writes
  to disk per the bitwize canonical layout (audited against
  `bitwize/servers/.../handlers/album_ops.py:create_album_structure`).
- [ ] `SqliteDBDriver` implements all 7 DBDriver method-delta + the 007 `cursor()`
  shim, using stdlib `sqlite3`. Per-project DB at `.agency/music.db` by default.
- [ ] `migrations/db_init.py` is dialect-aware: detects sqlite3 vs psycopg2 cursor
  type and emits the right `SERIAL`/`AUTOINCREMENT` + `TIMESTAMPTZ`/`TEXT` flavour.
- [ ] `MusicConfig` dataclass loads from `.agency/music-config.yaml` (per-project)
  with optional `~/.agency-music/config.yaml` global fallback; `AGENCY_MUSIC_HOME`
  env-var override. Required fields: `artist.name`, `paths.content_root`. All
  other fields have sensible defaults.
- [ ] `production_drivers(config)` factory returns a driver bundle wiring
  `FileStateDriver(config)` + `SqliteDBDriver(config)` + the existing
  `FakeTextDriver` + `FakeAudioDriver` + `FakeCloudDriver`. Symmetric counterpart
  to `fake_drivers()`.
- [ ] 4 NEW verbs ship on `MusicCapability`: `get_config` (transform),
  `load_override` (transform), `get_reference` (transform), `format_clipboard`
  (transform). All driver-light; route through StateDriver's `read_data` + new
  `read_config` method.
- [ ] 2 NEW templates ported verbatim: `templates/research.md` + `templates/sources.md`
  from `bitwize/templates/`.
- [ ] 6 NEW promo platform templates ported verbatim:
  `templates/promo/{campaign,facebook,instagram,tiktok,twitter,youtube}.md` from
  `bitwize/templates/promo/`.
- [ ] `new_album` walkable skill (5-phase: parse-args → validate-genre → check-existing
  → create-structure → confirm) ships in `ontology.py`.
- [ ] `tests/test_music_production.py` ships:
  - `test_file_state_driver_writes_canonical_layout` — creates album, asserts
    disk tree matches bitwize spec (README.md + tracks/ + RESEARCH.md/SOURCES.md
    when documentary)
  - `test_file_state_driver_renders_templates` — README contents match
    `templates/album.md` body
  - `test_sqlite_db_driver_round_trip` — db_init → create_tweet → list_tweets →
    delete_tweet through a real `:memory:` SQLite connection
  - `test_sqlite_db_driver_handles_disk_path` — uses tmp_path-based SQLite file
  - `test_db_init_dialect_detection` — SQLite + Postgres-stub branches both
    execute their statements
  - `test_config_loads_per_project_with_global_fallback` — both layers + env-var override
  - `test_production_drivers_factory_wires_all_five` — `production_drivers(cfg)`
    returns the bundle; each driver isinstance-checks against its Protocol
  - `test_new_album_skill_walks_through_confirm` — 5-phase walk to hard elicit
  - `test_get_config_returns_loaded_yaml_shape` — verb returns the config dict
  - `test_load_override_reads_user_file` — verb returns body or empty dict
  - `test_get_reference_reads_data_reference_doc` — verb resolves
    `data/reference/<path>` from the cap's installed location
  - `test_format_clipboard_handles_lyrics_and_style_prompts` — verb produces
    bitwize-compatible clipboard text shapes
- [ ] `examples/music_setup.py` runs end-to-end against a tmp directory: loads
  a stub config, creates an album, verifies the disk tree.
- [ ] `TODO.md` row 115 added (Partial → Shipped once tests Green).
- [ ] Optional pyproject extra: `[music-production]` carrying `pyyaml` for config
  loading (sqlite3 is stdlib, no extra needed).

## Design

### Config schema (`.agency/music-config.yaml`)

Mirrors bitwize's shape for compatibility (a bitwize user can rename their
`~/.bitwize-music/config.yaml` to `~/.agency-music/config.yaml` and it works):

```yaml
artist:
  name: "your-artist-name"
  # genres: optional preferred-genre list

paths:
  content_root: "~/music-projects"
  audio_root: "~/music-projects/audio"           # optional, defaults to {content_root}/audio
  documents_root: "~/music-projects/documents"   # optional
  overrides: "~/music-projects/overrides"        # optional
  ideas_file: "~/music-projects/IDEAS.md"        # optional, defaults to {content_root}/IDEAS.md

db:
  backend: sqlite                                 # NEW in agency — replaces bitwize's implicit Postgres
  path: ".agency/music.db"                        # per-project SQLite file by default

generation:
  service: suno                                   # optional, future LLM-driver routing
  additional_genres: []                           # custom genres beyond data/genres/

sheet_music:
  enabled: true
  page_size: "letter"
  section_headers: false

urls:                                             # optional
  soundcloud: "https://soundcloud.com/your-artist"
```

**Resolution order:**
1. `.agency/music-config.yaml` (per-project)
2. `~/.agency-music/config.yaml` (user-global)
3. `$AGENCY_MUSIC_HOME/config.yaml` (env override)
4. Defaults (defined in `MusicConfig.defaults()` dataclass field)

### FileStateDriver disk layout (must match bitwize verbatim)

```
{content_root}/
├── IDEAS.md                                      # capture_idea writes here
└── artists/
    └── {artist}/                                 # config.artist.name
        ├── README.md                             # rendered from templates/artist.md (first album)
        └── albums/
            └── {genre}/
                ├── README.md                     # rendered from templates/genre.md (first album in genre)
                └── {album-slug}/
                    ├── README.md                 # rendered from templates/album.md
                    ├── RESEARCH.md               # rendered from templates/research.md (documentary only)
                    ├── SOURCES.md                # rendered from templates/sources.md (documentary only)
                    ├── promo/                    # rendered from templates/promo/* (created on first
                    │   ├── campaign.md           #   promo_copy invocation; one file per platform)
                    │   ├── facebook.md
                    │   ├── instagram.md
                    │   ├── tiktok.md
                    │   ├── twitter.md
                    │   └── youtube.md
                    └── tracks/
                        └── {NN}-{slug}.md         # rendered from templates/track.md

{audio_root}/artists/{artist}/albums/{genre}/{album-slug}/    # lazy-created on first audio import
{documents_root}/...                                          # lazy-created on first doc import
{overrides}/                                                  # user-authored override files
```

### SqliteDBDriver shape

Uses stdlib `sqlite3` with `row_factory = sqlite3.Row` for dict-like access.
The 007 `cursor()` method returns a `sqlite3.Cursor` (already psycopg2-shaped
enough: `execute(sql, params)`, `fetchall()`, `fetchone()`, `close()`).

The 7 typed methods (`create_tweet`, `update_tweet`, etc.) hand-craft SQL
strings targeting the SQLite dialect:
- `INSERT INTO tweets (...) VALUES (...) RETURNING id` — SQLite 3.35+ supports RETURNING
- `UPDATE tweets SET ... WHERE id = ?` — `?` placeholder (not `%s`)
- `SELECT ... WHERE album = ? AND status = ? LIMIT ?` — bound params
- `DELETE FROM tweets WHERE id = ?`
- Aggregates use `SELECT status, COUNT(*) FROM tweets GROUP BY status`

### Dialect-aware `db_init.py`

Detects cursor backend via `type(cur).__module__`:
- `sqlite3` → SQLite-flavored schema (`AUTOINCREMENT`, `TEXT` for timestamps)
- otherwise → Postgres-flavored (current schema preserved verbatim)

```python
def init_schema(db_driver):
    cur = db_driver.cursor()
    dialect = "sqlite" if type(cur).__module__.startswith("sqlite3") else "postgres"
    sql = _SCHEMAS[dialect]
    for stmt in _statements(sql):
        cur.execute(stmt, ())
    cur.close()
    return {"statements_executed": len(_statements(sql)),
            "dialect": dialect, "ok": True}
```

### 4 NEW production-binding verbs

| Verb | Role | Backed by | Returns |
|---|---|---|---|
| `get_config` | transform | StateDriver.read_config | `{config: dict}` |
| `load_override` | transform | StateDriver.read_data("override", name) | `{override: dict, found: bool}` |
| `get_reference` | transform | StateDriver.read_data("reference", path) | `{kind, slug, body}` |
| `format_clipboard` | transform | (driver-free) | `{text, format}` (lyrics/style-prompt formatted) |

### `new_album` walkable skill

```python
NEW_ALBUM_SKILL = {
    "name": "new-album", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "parse-args",
         "produces": ["album_name", "genre", "documentary"]},
        {"index": 2, "name": "validate-genre",
         "produces": ["genre_valid"]},
        {"index": 3, "name": "check-existing",
         "produces": ["safe_to_create"]},
        {"index": 4, "name": "create-structure",
         "produces": ["album_root", "files_created"]},
        {"index": 5, "name": "confirm",
         "produces": ["user_confirmed"], "gate": "hard"},
    ],
}
```

## Open Questions

1. **PyYAML as required dep or optional extra?** Resolution: optional `[music-production]`
   extra. Falls back to a hand-rolled subset YAML parser (or JSON) when not installed.
   Agency stays dep-pure at the core; users opt-in to production binding via
   `pip install agency[music-production]`.
2. **Per-project DB location vs `.agency/music.db`?** Resolution: per-project
   `.agency/music.db` by default (sits alongside `.agency/session.db`); user can
   override via `db.path` in config.
3. **`promo/` directory creation timing?** Bitwize creates the 6 platform files when
   `promo_copy` is first called. Same here — keeps the album dir clean until promo
   work begins.
4. **Backwards-compat with bitwize config files?** Same shape — a bitwize user can
   point `AGENCY_MUSIC_HOME` at their `~/.bitwize-music/` and it just works.

## Followup — Implementation Status (2026-06-09)

**Verdict:** Partial (Slice 1 shipped — config + drivers + 4 verbs + skill + 8 templates + 27 tests; pyproject `[music-production]` extra deferred to Slice 2).

### Done (Slice 1 — `claude/spec-115-music-production-binding`)
- **`MusicConfig` dataclass** (`config.py`) with `MusicConfig.load()` resolving from `.agency/music-config.yaml` → `~/.agency-music/config.yaml` → `$AGENCY_MUSIC_HOME/config.yaml` → defaults. Bitwize-shape compatible (`artist.name`, `paths.{content_root,audio_root,documents_root,overrides,ideas_file}`, `db.{backend,path}`, `generation.additional_genres`, `sheet_music.{enabled,page_size}`). Pure-stdlib YAML fallback parser when PyYAML isn't installed.
- **`FileStateDriver`** (`drivers_production.py`) — full StateDriver Protocol implementation: writes the bitwize-canonical disk layout (`{content_root}/artists/{artist}/albums/{genre}/{slug}/` with `README.md` + `tracks/` + documentary supplements + artist + genre seed READMEs). Reads vendored templates from `agency/capabilities/music/templates/`. Implements all 16 Protocol methods incl. `list_keys` (Spec 097 Slice 2).
- **`SqliteDBDriver`** (`drivers_production.py`) — stdlib `sqlite3` backend, replaces Postgres per user directive. Per-project DB at `.agency/music.db` by default (configurable). All 7 typed methods (`create_tweet`/`update_tweet`/`delete_tweet`/`list_tweets`/`search_tweets`/`tweet_stats`/`sync_album_tweets`) + 007 `cursor()` shim. Embedded schema ensures idempotent init on first use.
- **`production_drivers(config)` factory** — symmetric counterpart to `fake_drivers()`. Wires `FileStateDriver` + `SqliteDBDriver` + the existing fake Text/Audio/Cloud drivers (production binding for those lands in a future slice when ffmpeg/pyloudnorm/boto3 extras ship).
- **4 NEW verbs** on `MusicCapability` (`_main.py`):
  - `get_config` (transform) — returns the loaded MusicConfig as a bitwize-shape dict.
  - `load_override` (transform) — reads `{overrides}/<name>.md` from the configured overrides dir.
  - `get_reference` (transform) — reads bundled `data/<kind>/<slug>` reference docs (the 50 vendored in Slice 094).
  - `format_clipboard` (transform) — Suno-safe clipboard formatting; two modes (lyrics: strips `[Section]` tags; style-prompt: collapses to single-line, ≤200 chars).
- **`new-album` walkable skill** added to OntologyExtension.skills: 5-phase (parse-args → validate-genre → check-existing → create-structure → confirm) ending in hard elicit. Mirrors bitwize's `new-album` skill flow but routed through agency primitives.
- **8 templates ported verbatim** from bitwize:
  - `templates/research.md` + `templates/sources.md` (Spec 099 Followup deferred)
  - `templates/promo/{campaign,facebook,instagram,tiktok,twitter,youtube}.md` (Spec 098 Followup deferred)
  - All 8 carry the Spec 060 `<!-- AGENT: ... -->` instruction block appended at EOF.
- **27 production tests** in `tests/test_music_production.py` covering: config resolution (3 paths + env override); FileStateDriver canonical layout + documentary supplements + template rendering + artist/genre seed READMEs + create_track + list_albums + find_album + rename_album; SqliteDBDriver round-trip (in-memory + persistent file) + search + stats + sync + cursor shim; production_drivers factory wiring; all 4 new verbs; new-album skill walk through hard elicit; end-to-end via `production_drivers()` with real disk + SQLite output.
- **Block-mode lint clean**: 0 violations after the 4 new verb docstring + skill addition.
- **Full suite Green**: 1011 passed, 6 skipped.

### Still to implement (deferred to Slice 2)
- **`[music-production]` pyproject.toml extra** carrying `pyyaml` for richer YAML support. The handrolled YAML fallback covers the bitwize-shape config used here, but advanced users may want comments/multiline strings.
- **Real Audio/Cloud driver production impls** — `pyloudnorm` + `ffmpeg` for audio, `boto3` for cloud. Currently `production_drivers()` wires the Fake* drivers for those; production binding lands when the `[music-audio]` + `[music-cloud]` extras ship.
- **Bitwize MCP function coverage gap-fill (3 fns)**: `format_for_clipboard` ✅ shipped; `get_album_full` ✅ covered by `album_progress` + `find_album`; `get_track` ✅ covered by `list_tracks`; `list_track_files` ✅ covered by `list_tracks` body. Remaining 3 (`migrate_audio_layout`, `cleanup_legacy_venvs`, `get_python_command`) are bitwize-specific maintenance and explicitly out-of-scope per Spec 115 §"Bitwize MCP function coverage audit".
- **`examples/music_setup.py`** end-to-end runner — design done in spec; implementation deferred to the docs PR.

### Refinement needed (given Spec 116)
- The raw SQL in `SqliteDBDriver` (Spec 115) will be replaced with SQLModel queries in Spec 116. No behavioural change; Protocol surface preserved. This is documented in Spec 116 §"Migration strategy".
- The JSON side-cars (`tracks/{slug}.meta.json`) + in-memory dicts (`_albums`, `_tracks`, `_ideas`, `_session`) on FileStateDriver will be replaced by SQLModel rows in Spec 116. Schema unification.

### Evidence
- code: `agency/capabilities/music/{config,drivers_production}.py`, `_main.py` (4 new verbs), `ontology.py` (NEW_ALBUM_SKILL); `templates/research.md` + `sources.md` + `promo/{6 platforms}.md`.
- tests: `tests/test_music_production.py` (27 tests Green); full suite Green: 1011 passed.
- lint: `plugin.lint_capability('music')` → ok=True block mode, 0 violations.
- branch: `claude/spec-115-music-production-binding`.
