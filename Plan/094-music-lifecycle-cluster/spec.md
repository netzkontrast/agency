---
spec_id: "094"
slug: music-lifecycle-cluster
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["007", "093"]
affects:
  - agency/capabilities/music/__init__.py
  - agency/capabilities/music/ontology.py
  - agency/capabilities/music/drivers.py
  - agency/capabilities/music/clusters/lifecycle.py
  - agency/capabilities/music/data/
  - tests/test_music_lifecycle.py
  - examples/music.py                # deleted
  - examples/music_drivers.py        # deleted
  - tests/test_agency.py             # remove music smoke (1116-1153)
  - docs/vision/CAPABILITY-CLUSTERS.md  # one-paragraph doctrine exception
  - CLAUDE.md                        # one-line exception note
domain: music / lifecycle
wave: 7
parent_spec: "093"
---

# Spec 094 — Music Lifecycle Cluster (the migration)

## Why

The first child of Spec 093 — and the migration that places music in
`agency/capabilities/music/`. Lifecycle is the right starter cluster because:

1. **It owns the ontology root.** Album/Track/Idea are the nodes every other
   cluster decorates (lyrics attach to Track, mastering reports attach to
   Album, tweets reference Album). Lifecycle MUST land first.
2. **It's stateful but driver-light.** Only StateDriver touches external work
   (filesystem/state). The other drivers stay unused at this layer — perfect
   for proving the migration without the heavier audio/DB plumbing.
3. **It carries the doctrine exception.** The CLAUDE.md + CAPABILITY-CLUSTERS.md
   notes land in this PR (the "music graduates from examples/" announcement).

bitwize ships ~22 lifecycle tools across `core` (the largest handler module),
`content`, `album_ops`, `ideas`, `rename`, `status`, `skills`, and `maintenance`.
094 ports them into a coherent lifecycle cluster with the conceptualizer skill
preserved and the long-tail (resume/session/rebuild) wired.

## Done When

- [ ] **The migration is complete:**
  - `agency/capabilities/music/__init__.py` declares `MusicCapability` with the
    cluster's verbs imported from `clusters/lifecycle.py`.
  - `agency/capabilities/music/ontology.py` carries the consolidated
    `OntologyExtension` (Album/Track/Idea + Tweet/SheetMusic stubs for future
    children + Genre/Reference data nodes + the `album-concept` skill).
  - `agency/capabilities/music/drivers.py` carries the five Driver protocols
    (moved from `examples/music_drivers.py`).
  - `examples/music.py` becomes a **deprecation re-export shim** for one
    spec cycle (panel-mandated by Wiegers): `from agency.capabilities.music
    import MusicCapability  # deprecated since spec 094, will be removed in
    spec 110 or when no external import survives a grep — whichever first`.
    `examples/music_drivers.py` is similarly shimmed.
  - `tests/test_agency.py:1116-1153` (music smoke) is **deleted**; replaced
    by `tests/test_music_lifecycle.py` (the migration's home).
- [ ] **Lifecycle verbs ship:** the cluster carries ~14 verbs covering bitwize's
  22 lifecycle tools (some merge — e.g. find/list/resume into discovery). See
  "Verb manifest" below.
- [ ] **`conceptualize` + `album-concept` skill are preserved verbatim** (no
  behavioural regression vs 007).
- [ ] **The 7-phase album-conceptualizer walks Green** via
  `develop.skill_walk(intent_id, "album-concept")`; phase 7 pauses on a hard
  `elicit` gate.
- [ ] **Drop-in bar:** ZERO edits under `agency/engine.py`, `agency/registry.py`,
  `agency/ontology.py` (the core extension mechanism). `git diff` confirms.
- [ ] **`scripts/check-drift` Green** after install regen; no orphans in
  `bin/agency-music-*` / `skills/music/references/`.
- [ ] **`docs/vision/CAPABILITY-CLUSTERS.md`** gains a paragraph noting music's
  graduation from `examples/`; **CLAUDE.md** gains the one-line exception.
- [ ] **`TODO.md`** row added for 094, 093 row updated to "Partial" with the
  first child shipped.
- [ ] **Tests:** `tests/test_music_lifecycle.py` (~12) covering: discovery,
  ontology merge, conceptualize artefact, walk to hard gate, set_album_status
  enum rejection, capture_idea + promote_idea provenance, find_album fallback
  + missing-driver degradation, rename_album with mirror-path side effect via
  StateDriver. Full suite Green via `scripts/test-cap music`.

## Verb manifest (cluster slice)

| # | Verb | Role | Driver | bitwize tool(s) absorbed | Notes |
|---|---|---|---|---|---|
| 1 | `conceptualize` | act | (driver-free) | — | kept verbatim from 007 |
| 2 | `capture_idea` | effect | StateDriver | `create_idea` | kept from 007 |
| 3 | `promote_idea` | effect | StateDriver | `promote_idea`, `update_idea` | also flips Idea status → `promoted` |
| 4 | `list_ideas` | transform | StateDriver | `get_ideas` | filters by status |
| 5 | `create_album` | effect | StateDriver | `create_album_structure` | the album-root creator |
| 6 | `find_album` | transform | StateDriver | `find_album`, `list_albums` | name + fuzzy match |
| 7 | `set_album_status` | effect | StateDriver | `update_album_status` | kept from 007; enum-checked |
| 8 | `create_track` | effect | StateDriver | `create_track` | adds to album |
| 9 | `list_tracks` | transform | StateDriver | `list_tracks`, `list_track_files` | |
| 10 | `set_track_status` | effect | StateDriver | `update_track_field` | enum-checked |
| 11 | `rename_album` | effect | StateDriver | `rename_album` | mirrors paths via StateDriver |
| 12 | `rename_track` | effect | StateDriver | `rename_track` | mirrors paths |
| 13 | `album_progress` | transform | StateDriver | `get_album_progress`, `get_album_full` | renders progress JSON |
| 14 | `resume_session` | transform | StateDriver | `get_session`, `update_session`, `resolve_path` | restores last-album context |

**Total: 14 verbs covering 22 bitwize tools.** The collapse comes from
merging discover-style helpers (`find_album` absorbs `list_albums`,
`list_track_files` folds into `list_tracks`, session reads consolidate).

## Design

### Module layout

```
agency/capabilities/music/
├── __init__.py                # MusicCapability + module docstring → SkillDoc
├── ontology.py                # the OntologyExtension (consolidated)
├── drivers.py                 # the five Driver protocols
├── clusters/
│   ├── __init__.py
│   └── lifecycle.py           # the 14 verbs (this spec)
├── data/                      # static reference data (genres etc.)
│   ├── genres/                # stub for now; 095+ fill in
│   └── reference/             # stub for now; 095+ fill in
└── migrations/                # one-shot install ops (db_init, etc.)
    └── __init__.py
```

### Driver method delta (StateDriver only — others wait)

```python
class StateDriver(Boundary):
    # existing 007 methods preserved
    def put(self, key: str, value: dict) -> None: ...
    def get(self, key: str) -> dict | None: ...

    # new methods (094)
    def list_ideas(self, status: str = "") -> list[dict]: ...
    def update_idea(self, idea_id: str, fields: dict) -> None: ...
    def create_album_root(self, artist: str, genre: str, slug: str) -> str: ...
    def find_album(self, query: str) -> list[dict]: ...
    def list_albums(self) -> list[dict]: ...
    def create_track(self, album: str, slug: str, title: str) -> str: ...
    def list_tracks(self, album: str) -> list[dict]: ...
    def update_track_field(self, album: str, track: str, field: str, value: str) -> None: ...
    def rename_album(self, old_slug: str, new_slug: str) -> dict: ...   # returns paths-moved manifest
    def rename_track(self, album: str, old_slug: str, new_slug: str) -> dict: ...
    def album_progress(self, album: str) -> dict: ...
    def get_session(self) -> dict: ...
    def update_session(self, fields: dict) -> None: ...
    def resolve_path(self, kind: str, **vars) -> str: ...
    def read_data(self, kind: str, slug: str) -> dict: ...  # for static data files
```

All new methods carry a fake implementation in `fake_drivers()` (deterministic,
no filesystem write outside a tmp_path fixture).

### Ontology consolidation

```python
music_ontology = OntologyExtension(
    nodes={
        "Album": {"status", "type", "genre", "slug", "artist", "target_lufs",
                  "theme", "created_at"},
        "Track": {"status", "slug", "album", "syllables", "readability",
                  "lyrics_path"},
        "Idea": {"text", "status", "captured_at", "promoted_to_album"},
        # stubs for future children
        "Tweet": {"album", "body", "scheduled_at", "status", "platform"},
        "SheetMusic": {"album", "source_audio", "format", "body", "published_url"},
        "Genre": {"slug", "name", "mastering_target_lufs", "suno_tips",
                  "reference_artists"},
        "Reference": {"kind", "slug", "body"},
    },
    enums={
        ("Album", "status"): {"draft", "in-production", "mastered", "released"},
        ("Album", "type"): ALBUM_TYPES,    # preserved from 007
        ("Track", "status"): {"draft", "recorded", "mixed", "mastered"},
        ("Idea", "status"): {"new", "promoted", "dropped"},
        ("Tweet", "status"): {"draft", "scheduled", "posted", "archived"},
    },
    skills=[ALBUM_CONCEPT_SKILL],         # kept verbatim from 007
    artefacts=["album-concept"],          # kept; children add the rest
)
```

### The album-concept skill (preserved)

The 7-phase conceptualizer (foundation → concept → sonic → structure → art →
practical → confirmation) walks unchanged. Phase 7 is a HARD gate via
`elicit`/`lifecycle_gate`. `tests/test_music_lifecycle.py` re-verifies the walk.
**Primary actor:** human-curator (the user); agent assists by populating
each phase's `produces` keys but does not auto-advance phase 7.

### Ontology versioning rule (panel-added, iteration 2 / Newman)

Within the 094–100 wave, the music ontology is **purely additive**:
- new nodes may be added (098 adds `PromoTemplate`, 099 adds
  `ResearchClaim` + `VerificationRecord`, 096 adds `MasteringPreset`)
- new fields on existing nodes are added with optional defaults (no
  required-field additions to existing nodes)
- no field renames; no node renames; no enum value removals
- closed enum values may only be EXTENDED, never reduced

This invariant is asserted by `tests/test_music_ontology_additive.py`
(introduced in 094): a snapshot of the consolidated ontology after 094
ships becomes the baseline; subsequent specs in the wave assert their
extension is strictly additive to that baseline. After 100 ships, the
invariant relaxes (ontology evolution becomes the same as any other
agency cap).

### Doctrine notes (the migration's quiet load)

#### `CLAUDE.md` patch (one line under "Surface")

Current:
> Domain capabilities live in `examples/` (e.g. `examples/music.py`), loaded
> via `Engine(..., extra_capabilities=[…])` — the bootstrapping harness stays
> minimal.

Becomes:
> Domain capabilities live in `examples/` (loaded via `Engine(...,
> extra_capabilities=[…])`) — *except `music`, which graduated to
> `agency/capabilities/music/` per Spec 093 after the proof-of-contract slice
> (007) shipped*. Future unproven domain caps continue to land in `examples/`
> first.

#### `docs/vision/CAPABILITY-CLUSTERS.md` paragraph

A two-sentence appendix at the end of the "example extension" section noting
that music's graduation is a one-off (the contract proved itself; the
graduation is earned, not granted by default), and that the graduation
discriminator is the drop-in bar (zero engine edits).

## Test plan

```python
# tests/test_music_lifecycle.py — ~12 tests
def test_music_capability_discovers_all_lifecycle_verbs(): ...
def test_ontology_merges_strictly_on_core_engine(): ...
def test_conceptualize_returns_album_concept_artefact_with_produces_edge(): ...
def test_album_concept_skill_walks_to_phase_7_hard_gate_and_pauses(): ...
def test_set_album_status_rejects_unknown_status(): ...
def test_capture_idea_records_idea_node_and_serves_intent(): ...
def test_promote_idea_flips_status_and_links_to_album(): ...
def test_find_album_fuzzy_match_returns_ranked_results(): ...
def test_rename_album_emits_mirrored_path_manifest_via_state_driver(): ...
def test_album_progress_aggregates_track_statuses(): ...
def test_resume_session_restores_last_album_context(): ...
def test_lifecycle_verb_fails_typed_when_state_driver_missing(): ...
```

## Open questions

1. **Should `conceptualize` move into the lifecycle cluster file, or stay at
   the cap root?** Recommend cluster file (`clusters/lifecycle.py`) — root-level
   verbs become a tangle. The cap root only re-exports.
2. **`list_albums` vs `find_album` — separate or merged?** Merged into
   `find_album(query)` with `query=""` returning all. Cleaner surface.
3. **Session/resume — verb or just StateDriver method?** Verb (`resume_session`)
   because it's a discoverable surface for the agent; the driver method does
   the work.

## Followup

(Populated when the PR ships.)
