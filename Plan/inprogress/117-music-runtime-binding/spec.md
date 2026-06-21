---
spec_id: "117"
slug: music-runtime-binding
status: draft
state: inprogress
last_updated: 2026-06-09
owner: "@agency"
depends_on: ["093", "094", "100", "115"]
affects:
  - agency/__main__.py                                  # set engine._music_production flag at the MCP entrypoint
  - agency/capabilities/music/_main.py                  # lazy driver auto-wiring (_require_drv override + autowire)
  - agency/capabilities/music/config.py                 # MusicConfig.bootstrap + config_file_exists + DEFAULT_CONFIG_YAML
  - tests/test_music_production.py                      # bootstrap + autowire on/off tests
domain: music / production / runtime
wave: 8
parent_spec: "115"
---

# Spec 117 — Music Runtime Binding (auto-wire drivers + default-config bootstrap)

## Why

Spec 115 shipped the production drivers (`FileStateDriver`, `SqliteDBDriver`,
`production_drivers()`) — but **nothing in the running plugin ever calls them.**
This spec was authored by *dogfooding*: we drove the agency `music` capability
end-to-end to produce a real 5-track EP ("Umschalten", artist *the Agency
System*, genre `dystopian-future-synth`) and recorded every place the live
runtime diverged from the mature **bitwize-music** plugin it was ported from.

The headline finding: **the music capability is library-complete but
runtime-unbound.** A fresh session calling `music.diagnose` over the installed
MCP plugin returns:

```json
{"drivers_wired": [], "drivers_missing":
  ["music_state","music_text","music_audio","music_db","music_cloud"]}
```

— so every disk- or DB-backed verb (`create_album`, `create_track`,
`set_track_status`, the catalogue/promo clusters) returns
`DEPENDENCY_MISSING` or silently no-ops. You cannot actually make an album
with the plugin as shipped.

This spec closes that runtime gap (driver auto-wiring + default-config /
fresh-repo bootstrap, per the 2026-06-09 user directive: *"set up all drivers
when we need them, and have a default config ready to set up a fresh repo if
not done yet"*) and inventories the **remaining** bitwize-parity gaps the same
dogfooding run surfaced, scoping them to follow-up specs.

## Empirical findings (grounded in the Umschalten run)

| # | Finding | Evidence | This spec |
|---|---|---|---|
| **F1** | **Production drivers are unreachable from the MCP/plugin runtime.** `__main__.main()` builds `engine = Engine(db_path)` with no `drivers=`; `production_drivers()` is referenced *only* by tests (zero call sites in `__main__`, `engine.py`, `install.py`, `cli.py`). | `agency/__main__.py:37`; `engine.py:142` (`drivers=None` default) + the `if drivers:` registration guard; `grep production_drivers agency/` → tests only | **CLOSED** |
| **F2** | **No default config / fresh-repo bootstrap.** `MusicConfig.load()` returns in-memory defaults (content_root `~/music-projects`, empty artist) but never writes a config file or creates the root; a new user has nothing to edit and no place for output. | `config.py:124` `load()` is read-only | **CLOSED** |
| **F3** | **Verbs render templates verbatim — no field substitution.** `create_album`/`create_track` write the raw bitwize template skeleton: the persisted README keeps `title: "[Album Title]"` and the track keeps `title: "[Track Title]"`; only YAML `track_number` is substituted. bitwize fills title/album/track-number into frontmatter + tables. | `_main.py` `create_album`/`create_track` `state.put(...)` / `state.create_track(...)` write `tpl.template` unmodified (only the `track_number:` line is patched) | **CLOSED (Slice 2)** |
| **F4** | **Status persists to a `.meta.json` sidecar, not frontmatter.** `set_track_status` → `FileStateDriver.update_track_field` writes `tracks/NN-slug.meta.json` (`{"status": ...}`) and explicitly defers real frontmatter editing "to a future slice"; the markdown `Status` row stays `Not Started`. bitwize has no sidecars — status is the single source of truth in the track. | `drivers_production.py` `update_track_field` (sidecar write + deferral comment) | **CLOSED (Slice 2)** |
| **F5** | **Track template frontmatter omits `status:`.** The vendored `track.md` frontmatter carries `title/track_number/instrumental/explicit/suno_url/sheet_music` but no `status:`. Real bitwize tracks carry `status:` in frontmatter, and the-agency-system's `validate_track.py` PostToolUse hook **hard-requires** `["title","track_number","status"]` — so an agency-rendered track *fails validation in that repo*. | `templates/track.md:1-11` vs `the-agency-system/hooks/validate_track.py:11` | **CLOSED (Slice 2)** |
| **F6** | **No project-DNA name-exposure enforcement.** `scan_artist_names` checks a configured artist-name blocklist, not a project's alter/character roster. The Umschalten run leaked a personal name ("Lex") into an S4 lyric draft; nothing in the music capability flagged it (it was caught by the `theagencysystem` skill's `name_exposure` rule, which lives outside both plugins). | `_main.py scan_artist_names` (blocklist only); caught manually | **noted → Spec 119 candidate** |

Findings **F1/F2** are the runtime blockers and are closed in Slice 1.
**F3/F4/F5** are output-fidelity gaps (the rendered file is structurally
bitwize-canonical — the templates are byte-identical save a Spec 060
`<!-- AGENT -->` comment — but under-populated); they are **closed in
Slice 2** (render fidelity, below). **F6** remains a cross-cutting
authoring-safety gap → Spec 119 candidate.

## Scope (this spec)

Close **F1 + F2** with the smallest doctrine-fit change — *no engine edits*
(the drop-in-capability bar): the capability lazily wires its own production
drivers the first time a verb needs one, and `MusicConfig` bootstraps a default
config + content root when a repo has none.

## Done When

- [x] **Lazy auto-wiring.** `MusicCapability` builds `production_drivers(MusicConfig.bootstrap())`
  ONCE on first driver miss and registers the bundle on the engine's
  `DriverRegistry`, so every later verb + `diagnose` reports them wired —
  without the caller passing `Engine(..., drivers=…)`.
- [x] **Production-flag gating (bounded blast radius).** Auto-wiring fires only
  when `engine._music_production is True`; the MCP entrypoint
  (`__main__.main()`) sets it. A bare `Engine(..., drivers={})` built by a unit
  test has no flag and keeps the typed `DEPENDENCY_MISSING` contract.
- [x] **Default-config + fresh-repo bootstrap.** `MusicConfig.bootstrap()` writes
  a default `.agency/music-config.yaml` (bitwize-shape) when none exists and
  creates `content_root`; idempotent no-op when a config is already present
  (existing projects keep their bindings).
- [x] **Direct-driver sites covered.** The verbs that call `ctx.get_driver()`
  directly (`capture_idea`, `promote_idea`, `create_track`, `list_track_files`)
  auto-wire first, so disk persistence is order-independent.
- [x] **Tests.** `test_bootstrap_writes_default_config_when_absent`,
  `test_bootstrap_is_noop_when_config_present`,
  `test_autowire_disabled_keeps_dependency_missing`,
  `test_autowire_enabled_wires_production_drivers_and_writes_disk`
  (asserts disk README written under the configured root + `diagnose` flips to
  all-five-wired). Blast-radius guard
  `test_missing_driver_degrades_to_typed_failure` still green.
- [x] `TODO.md` row 117 added.
- [x] **(F3/F4/F5)** rendered-output fidelity — **shipped in Slice 2**
  (template `status:`, album/track field substitution, frontmatter-sourced
  status round-trip; no `.meta.json` sidecar).

## Design

### Lazy auto-wiring (capability-local, no engine edits)

Every music verb resolves drivers through `self._require_drv(name)` →
`ctx.get_driver(name)` → `engine.DriverRegistry.get(name)`. The fix overrides
`_require_drv` on `MusicCapability`:

```python
def _require_drv(self, name):
    if name in self._MUSIC_DRIVER_NAMES:
        reg = self.ctx.drivers
        if reg is not None and not reg.has(name):
            self._autowire_music_drivers()      # build + register the bundle once
    return super()._require_drv(name)
```

`_autowire_music_drivers()` is a no-op unless (a) a `DriverRegistry` is present
AND (b) `engine._music_production` is set AND (c) ≥1 of the five drivers is
missing. When it fires it builds `production_drivers(MusicConfig.bootstrap())`
and registers each missing driver — so the wiring is **session-persistent**
(the registry lives on the engine), `diagnose` reports the truth, and the four
direct `get_driver` sites that bypass `_require_drv` are nudged with an explicit
`_autowire_music_drivers()` call so order doesn't matter.

**Why a flag, not config-presence, gates it:** unit tests run with the agency
repo's own `.agency/` on the CWD; keying auto-wire off "a config file exists"
would leak ambient config into the test suite and flip the typed-failure
contract. The production flag is the one signal that cleanly separates the MCP
runtime from a bare test engine.

### Default-config + fresh-repo bootstrap

```python
MusicConfig.bootstrap(write_config=True, make_dirs=True)
```
- If `config_file_exists()` is False on every search path → write
  `DEFAULT_CONFIG_YAML` to `.agency/music-config.yaml` (bitwize-shape: empty
  `artist.name`, `content_root: ~/music-projects`, `db.backend: sqlite`) and
  clear the load cache.
- Then `load()` (now finds the written file) and `mkdir -p content_root`.
- Idempotent: an existing config is never clobbered.

Resolution order is unchanged (Spec 115): `.agency/music-config.yaml` →
`~/.agency-music/config.yaml` → `$AGENCY_MUSIC_HOME/config.yaml` → defaults.

## Remaining gaps → follow-up specs

- **F3/F4/F5 — render fidelity:** CLOSED in **Slice 2** (below). Template
  field substitution on render (album/track title, track number), `status:`
  in `track.md` frontmatter, and frontmatter-sourced status round-trip
  (no `.meta.json` sidecar) all landed; the-agency-system `validate_track.py`
  hook now reads a populated `status:`. Spec 118 retains only any genuinely
  remaining render polish (e.g. POV / tracklist auto-population), not F3/F4/F5.
- **Spec 119 candidate — authoring-safety (F6):** a project-DNA name/roster
  blocklist the lyric gates can enforce (the `name_exposure` rule), generalising
  `scan_artist_names` beyond the single configured artist name.

## Followup — Implementation Status (2026-06-09)

**Verdict:** Shipped (Slice 1 + Slice 2) → F1/F2 runtime binding (Slice 1) +
F3/F4/F5 render fidelity (Slice 2) shipped + tested; only F6 (name-exposure)
remains, deferred to the Spec 119 candidate.

### Done (`claude/agency-plugin-album-spec-ns8gb7`)
- `config.py` — `DEFAULT_CONFIG_YAML`, `config_file_exists()`, `bootstrap()`.
- `_main.py` — `_MUSIC_DRIVER_NAMES`, `_production_enabled()`,
  `_autowire_music_drivers()`, `_require_drv` override; autowire nudge at the
  four direct `get_driver("music_state")` sites.
- `__main__.py` — `engine._music_production = True` at the MCP entrypoint.
- `tests/test_music_production.py` — 4 new tests (bootstrap ×2, autowire on/off);
  blast-radius `test_missing_driver_degrades_to_typed_failure` re-verified.

### Evidence
- tests: focused slice green — `9 passed` (bootstrap/autowire/config +
  blast-radius); music slices green — `103 passed`
  (`test_music_production / _capability / _interop / _gates / _lifecycle`).
- drift: `scripts/check-drift` → NO DRIFT DETECTED (install clean, orphans none).
- dogfood proof: the Umschalten EP rendered to disk under
  `the-agency-system/artists/the-agency-system/albums/dystopian-future-synth/umschalten/`
  via `production_drivers` wired through the auto-wire path.

### Still
- F6 name-exposure enforcement (Spec 119 candidate).
- Real audio/cloud production drivers still fake-backed (Spec 115 Slice 2).

## Followup — Slice 2: render fidelity (F3/F4/F5) (2026-06-09)

**Verdict:** Shipped → F3/F4/F5 closed; the rendered album/track files are now
populated (not skeleton) and status is the single source of truth in the
track frontmatter.

### Done (`claude/agency-plugin-album-spec-ns8gb7`)
- **F5** — `templates/track.md` frontmatter carries `status: "Not Started"`
  (right after `track_number: 0`), parity with the bitwize source template;
  the-agency-system `validate_track.py` hook's `status` requirement is met.
- **F3** — `_main.py`: `_fill_album_body(body, artist, title, genre)` +
  `_fill_track_body(body, title, track_number)` private helpers do targeted
  string substitution into the rendered body before `state.put` /
  `state.create_track`. Album: frontmatter `title:` + H1 + `[Album Name]` +
  `[Artist Name]` + the `[Genre](/genres/[genre]/…)` link. Track: frontmatter
  `title:`, H1, and the Track Details `Track #` / `Title` rows (plus the
  existing `track_number: 0` substitution).
- **F4** — `drivers_production.py` `FileStateDriver`: added stdlib
  `_parse_frontmatter` + `_set_frontmatter_field` helpers (no YAML dep).
  `update_track_field` now edits the track `.md` frontmatter line in place
  (quoted `status: "…"`), no `.meta.json` sidecar; missing track file is a
  no-op as before. `list_tracks` sources `status` (default `"Not Started"`)
  and `title` from the parsed frontmatter (slug-title fallback). `album_progress`
  (derived from `list_tracks`) now reflects real statuses. The GRAPH Track-node
  status enum stays lowercase `{draft,recorded,mixed,mastered}`; only the
  rendered FILE frontmatter carries the value written by `set_track_status`.

### Evidence
- tests: 3 new in `tests/test_music_production.py` —
  `test_create_track_renders_title_and_status_into_frontmatter`,
  `test_set_track_status_round_trips_through_frontmatter_no_sidecar`,
  `test_create_album_substitutes_title_artist_genre_into_readme` — RED→GREEN.
  Required music slices green: `106 passed`
  (`test_music_production / _capability / _lifecycle / _interop / _gates`).
- drift: `scripts/check-drift` → NO DRIFT DETECTED.
- blast radius: fake-driver `list_tracks`/`set_track_status`/`album_progress`
  tests (`test_music_lifecycle`, `test_music_audio`) untouched — the change is
  isolated to `FileStateDriver`; FakeStateDriver path unchanged, no expectation
  edits needed.
