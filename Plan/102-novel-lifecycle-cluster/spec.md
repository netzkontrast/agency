---
spec_id: "102"
slug: novel-lifecycle-cluster
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["101", "093", "094"]
affects:
  - agency/capabilities/novel/__init__.py
  - agency/capabilities/novel/ontology.py
  - agency/capabilities/novel/drivers.py
  - agency/capabilities/novel/clusters/lifecycle.py
  - agency/capabilities/novel/templates/
  - agency/capabilities/novel/data/
  - tests/test_novel_lifecycle.py
domain: novel / lifecycle
wave: 8
parent_spec: "101"
mvp-source:
  - "Plan/_research/novel-mvp-source/templates/ (11 files — port verbatim)"
  - "Plan/_research/novel-mvp-source/prior-specs/010-on-disk-layout.md"
  - "Plan/_research/novel-mvp-source/prior-specs/011-handlers-core.md"
---

# Spec 102 — Novel Lifecycle Cluster (foundation + migration)

## Why

The first child of Spec 101 — and the foundation that lands the novel
capability folder under `agency/capabilities/novel/`. Like music's Spec
094, 102 carries:

- The consolidated `OntologyExtension` (all nodes/edges/enums/templates/
  schemas declared additively; children attach to it)
- The five Driver protocols (reused from music; new methods this child
  needs)
- The novel-concept walkable skill (10-phase conceptualizer)
- The 11 templates ported VERBATIM from the-agency-system
- The base lifecycle verbs (Novel/Series/Chapter/Scene CRUD, idea capture,
  status flips, resume/session)

This spec also lands the **decision to host the Dramatica ontology +
NCP schema as static data** under `agency/capabilities/novel/data/` so
103's coherence checks have a stable read source.

## Done When

- [ ] `agency/capabilities/novel/{__init__.py,ontology.py,drivers.py,
      clusters/lifecycle.py}` exists; `NovelCapability(CapabilityBase)`
      registers.
- [ ] 11 templates ported VERBATIM from
      `Plan/_research/novel-mvp-source/templates/` to
      `agency/capabilities/novel/templates/`; declared on
      `OntologyExtension.templates` (Spec 060 substrate). Test asserts
      `ctx.template(name).template` for each name returns a non-empty
      body that matches the imported source.
- [ ] **Data assets ported under `agency/capabilities/novel/data/`**:
      - `data/dramatica/ontology.json` (304 entries; read by 103 verbs)
      - `data/schemas/ncp-schema-v1.3.0.json` (NCP validation)
      - `data/dramatica/scenarios.json` (12 scenarios; 6 novel + 6 lyric)
      - `data/reference/research-domains.yaml` (10 domains — copied from
        099 + tweaked for novels)
- [ ] **14 user-facing verbs ship** (see "Verb manifest").
- [ ] **StateDriver extended** with the 14 new methods listed below;
      deterministic fake.
- [ ] **`novel-concept` walkable skill** ships as the 10-phase
      conceptualizer (modeled on music's `album-concept` 7-phase pattern
      but extended with dramatica-seed + outline-shape phases).
- [ ] **pytest markers extended** (per 094-style fix): `_AUTO_MARKER_
      PATTERNS` gains `(re.compile(r"test_novel_"), "novel")` (single
      marker for now; cluster subdivisions can come later).
- [ ] **`tests/test_novel_lifecycle.py` Green** (~12 tests).
- [ ] **`TODO.md` updated** with 102 row.

## Verb manifest

| # | Verb | Role | Driver | Notes |
|---|---|---|---|---|
| 1 | `conceptualize` | act | (driver-free) | Renders the work+premise artefact pair via templates |
| 2 | `capture_idea` | effect | StateDriver | Records an `Idea` (renaming music's Idea node — same shape) |
| 3 | `promote_idea` | effect | StateDriver | Idea → Novel transition |
| 4 | `list_ideas` | transform | StateDriver | Filter by status |
| 5 | `create_novel` | effect | StateDriver | Creates novel root + renders the 8 startup templates |
| 6 | `find_novel` | transform | StateDriver | Fuzzy + filter |
| 7 | `set_novel_status` | effect | StateDriver | Enum-checked |
| 8 | `create_chapter` | effect | StateDriver | Renders chapter.md template |
| 9 | `list_chapters` | transform | StateDriver | |
| 10 | `create_scene` | effect | StateDriver | Renders scene.md template |
| 11 | `set_chapter_status` | effect | StateDriver | Enum-checked |
| 12 | `rename_novel` | effect | StateDriver | Mirror-paths via StateDriver |
| 13 | `novel_progress` | transform | StateDriver | Word-count + beat-completion + chapter-status aggregate |
| 14 | `resume_session` | transform | StateDriver | Restores last-novel context |

**Total: 14 verbs.**

## Design

### Module layout

```
agency/capabilities/novel/
├── __init__.py              # NovelCapability + module docstring → SkillDoc
├── ontology.py              # the consolidated OntologyExtension
├── drivers.py               # the 5 Driver protocols + fake_drivers()
├── clusters/
│   ├── __init__.py
│   └── lifecycle.py         # the 14 verbs (this spec)
├── templates/               # 11 .md/.json ported verbatim
└── data/
    ├── dramatica/
    │   ├── ontology.json    # 304-entry Dramatica ontology
    │   └── scenarios.json   # 12 NCP scenarios
    ├── schemas/
    │   └── ncp-schema-v1.3.0.json
    └── reference/
        └── research-domains.yaml
```

### StateDriver method delta

```python
class StateDriver(Boundary):
    # reused from music
    def put(self, key: str, value: dict) -> None: ...
    def get(self, key: str) -> dict | None: ...
    def read_data(self, kind: str, slug: str) -> dict: ...

    # new methods (102)
    def create_novel_root(self, author: str, genre: str, slug: str) -> str: ...
    def find_novel(self, query: str) -> list[dict]: ...
    def list_novels(self) -> list[dict]: ...
    def create_chapter(self, novel: str, slug: str, number: int) -> str: ...
    def list_chapters(self, novel: str) -> list[dict]: ...
    def create_scene(self, chapter: str, slug: str, pov: str) -> str: ...
    def set_chapter_status(self, novel: str, chapter: str, status: str) -> None: ...
    def rename_novel(self, old_slug: str, new_slug: str) -> dict: ...
    def novel_progress(self, novel: str) -> dict: ...
    def get_session(self) -> dict: ...
    def update_session(self, fields: dict) -> None: ...
    def read_ncp(self, novel: str) -> dict: ...
    def write_ncp(self, novel: str, ncp: dict) -> None: ...
    def list_ideas(self, status: str = "") -> list[dict]: ...
```

### `novel-concept` walkable skill (10 phases)

```python
NOVEL_CONCEPT_SKILL = {
    "name": "novel-concept",
    "kind": "conceptualizer",
    "phases": [
        {"index": 1, "name": "premise",
         "produces": ["logline", "central_question"]},
        {"index": 2, "name": "genre",
         "produces": ["genre", "subgenre", "tone"]},
        {"index": 3, "name": "audience",
         "produces": ["target_reader", "comp_titles"]},
        {"index": 4, "name": "pov",
         "produces": ["pov_choice", "narrator_voice"]},
        {"index": 5, "name": "setting",
         "produces": ["world", "time_period", "geography"]},
        {"index": 6, "name": "characters-core",
         "produces": ["protagonist_seed", "antagonist_seed",
                      "supporting_seeds"]},
        {"index": 7, "name": "dramatica-seed",
         "produces": ["resolve_intent", "growth_intent",
                      "approach_intent", "mental_sex_intent"]},
        {"index": 8, "name": "outline-shape",
         "produces": ["act_structure", "midpoint_intent",
                      "ending_intent"]},
        {"index": 9, "name": "series-hypothesis",
         "produces": ["standalone_or_series", "series_arc"]},
        {"index": 10, "name": "confirmation",
         "produces": ["user_confirmed"], "gate": "hard"},
    ],
}
```

**Primary actor**: human-curator (the user); agent assists by populating
each phase's `produces` keys but does NOT auto-advance phase 10.

### Ontology declaration (with iteration-2 complexity extensions)

The base schema (Spec 101) plus iteration-2 additions for complex novels.
**All iteration-2 nodes are optional** — simple novels need only the base set.

**Base set** (simple novel: Novel → Chapter → Scene):
- Novel, Series, Chapter, Scene, Character, Beat, Idea (declared in
  Spec 101's consolidated extension)
- Novel.outline_hierarchy: `["chapter", "scene"]` (default)

**Iteration-2 additions** (complex novel — opt-in via
`Novel.outline_hierarchy` or per-novel frontmatter):

```python
# Volume/Part/Book hierarchy (ADR-5):
Volume      (slug, series, number, title, word_count)
Part        (slug, volume, number, title)
Book        (slug, part_or_volume, number, title, word_count)

# Worldbuilding sub-graph (ADR-4):
World       (slug, novel, body_uri)
Culture     (slug, world, body)
Religion    (slug, world, body)
Language    (slug, world, body, written_script)
MagicSystem (slug, world, body, hard_or_soft)
Politics    (slug, world, body)
Economy     (slug, world, body)
Geography   (slug, world, body)
Bestiary    (slug, world, body)
WorldAxiom  (slug, world, text, severity)        # hard / soft canon
Canon       (slug, novel, axiom, scene_or_chapter)  # ENCODES edges

# Large-cast hierarchy:
Faction     (slug, novel, body)
House       (slug, faction, name, sigil)
Family      (slug, house_or_faction, name, members)

# Character arc tracking (ADR-6):
Arc         (slug, character, novel_or_series, phases)
ArcPhase    (arc, position, growth_state, voice_signature_version)

# Non-linear narrative (ADR-3):
# Scene gains: narrative_order (manuscript position) + story_time
# (in-world timestamp); same for Chapter

# Multilingual (ADR-1):
# Chapter.canon_language: str (e.g. "de", "en"); never translated.
# CharacterSpeechLanguage: closed enum {de, en, fr, …} on Character node.
```

Closed enums added in iter-2:
- `(Arc, growth_state)`: `seed / setback / commitment / crisis / change / mastery`
- `(WorldAxiom, severity)`: `hard / soft` — hard axioms are inviolable;
  soft are bendable for dramatic effect
- `(MagicSystem, hard_or_soft)`: `hard / soft` — Sanderson's distinction
- `(Language, written_script)`: `latin / cyrillic / arabic / kanji /
  invented / pictographic`

Edges added in iter-2:
- `ENCODES` (Scene → WorldAxiom) — Scene establishes or relies on a Canon fact
- `BELONGS_TO` (Character → Faction / House / Family)
- `INHABITS` (Character → Culture)
- `WORSHIPS` (Character → Religion)
- `SPEAKS` (Character → Language)
- `WIELDS` (Character → MagicSystem)
- `CONTRADICTS` (WorldAxiom → WorldAxiom) — series-coherence flag

(Full schema declared in 102's ontology.py; children attach their own
nodes additively per ADR-5.)

### Pytest markers

`tests/conftest.py` gains:
```python
(re.compile(r"test_novel_"), "novel"),
```
(One marker per cluster — `novel_lifecycle`, `novel_storyform`, etc — is a
v2 enhancement; for now `novel` is sufficient and matches the 094-style
single-marker approach.)

## Test plan

```python
# tests/test_novel_lifecycle.py — ~12 tests
def test_novel_capability_discovers_all_lifecycle_verbs(): ...
def test_ontology_merges_strictly_on_core_engine(): ...
def test_all_11_templates_registered_and_non_empty(): ...
def test_dramatica_ontology_loaded_from_data_assets(): ...
def test_ncp_schema_validates_a_well_formed_ncp(): ...
def test_conceptualize_renders_premise_artefact_with_produces_edge(): ...
def test_novel_concept_skill_walks_to_phase_10_hard_gate(): ...
def test_set_novel_status_rejects_unknown_status(): ...
def test_capture_idea_records_idea_node_serves_intent(): ...
def test_promote_idea_flips_status_and_links_to_novel(): ...
def test_rename_novel_emits_mirrored_path_manifest(): ...
def test_resume_session_restores_last_novel_context(): ...
```

## Implementation guidance (iteration 3) — First-PR scope

102 is the foundation spec; its PR carries the heaviest scope of any
child. Use this prioritized scope to keep the first PR tractable
(target: ~600 LoC implementation + ~200 LoC tests). Defer everything
below the cutoff to follow-up PRs.

### First-PR scope (MUST land in 102's initial PR)

1. **The module skeleton** (`__init__.py` + `ontology.py` + `drivers.py`
   + `clusters/__init__.py`).
2. **`OntologyExtension` declaration** — full schema (base + iteration-2
   nodes). Even nodes whose verbs aren't yet implemented MUST be declared
   so children can attach.
3. **11 templates ported VERBATIM** from
   `Plan/_research/novel-mvp-source/templates/` to
   `agency/capabilities/novel/templates/`. No content edits.
4. **Data assets ported VERBATIM**:
   - `data/dramatica/ontology.json` (304 entries)
   - `data/dramatica/scenarios.json` (12 scenarios)
   - `data/schemas/ncp-schema-v1.3.0.json` (from
     `legacy-skills/ncp-author/upstream/schema/`)
   - `data/reference/research-domains.yaml`
5. **Base lifecycle verbs (1-7)**: `conceptualize`, `capture_idea`,
   `promote_idea`, `list_ideas`, `create_novel`, `find_novel`,
   `set_novel_status`. Cover the simple-novel happy path.
6. **`novel-concept` walkable skill** (the 10-phase conceptualizer).
7. **`tests/test_novel_lifecycle.py`** — 12 tests focused on the
   simple-novel happy path + the doctrine-exception assertions (zero
   engine edits, ontology merges strictly).
8. **pytest marker addition** to `conftest.py`.

### Second-PR scope (DEFERRED — opens follow-up PR after 102 base lands)

- Chapter / Scene / Beat verbs (8-14)
- Iteration-2 Volume/Part/Book lifecycle verbs (`create_volume`,
  `create_part`, `create_book`) — gated on `outline_hierarchy`
  declaration
- Iteration-2 World sub-schema effect verbs (`create_culture`,
  `create_religion`, `create_language`, `create_magic_system`, …)
- Iteration-2 Faction / House / Family / Arc / ArcPhase verbs
- Complex-novel fixture tests (multi-volume, multi-POV, multi-subplot)
- The `novel-concept` skill's iteration-2 phases (dramatica-seed,
  outline-shape, series-hypothesis — currently phases 7-9)

### Build order within the first PR

1. Declare `OntologyExtension` first (no behaviour, just structure).
2. Implement StateDriver method delta with fake.
3. Port templates + data assets (file copies).
4. Implement verbs 1-7 in `clusters/lifecycle.py`.
5. Implement `novel-concept` skill phase-graph.
6. Write tests covering each verb + the skill walk.
7. Run `scripts/test-cap novel` Green.
8. Run install regen + commit.

### Risk register (first PR)

| Risk | Mitigation |
|---|---|
| Ontology merge fails because a node label already exists in core | Use namespacing — every novel-specific label is unique (Novel, Series, Storyform, etc.) |
| Template port fails because mustache `{{var}}` syntax conflicts with `string.Template` `$var` | Use `template.template` (raw body access) until Spec 060 mustache support lands; document as Open Q |
| `data/dramatica/ontology.json` size (304 entries, ~50KB) bloats wheel | Acceptable — under the 100KB threshold for data assets |
| 102's StateDriver method count grows past the music 094 baseline (which had 14) | Acceptable — novels need richer state ops; document the delta in the followup |

## Open questions

1. **Idea node — Novel-specific or reuse music's `Idea` label?** Reuse the
   label (it's already in the core ontology via 094 music). Add an
   optional `kind` field to distinguish music vs novel ideas.
2. **NCP round-trip granularity**: 102 ships read/write of the top-level
   `{storyform, players, scenes, metadata}` blocks. Storybeat/Moment-level
   modification ships in 103.
3. **Templates: substituter vs raw?** Templates use `{{var}}` mustache
   placeholders (per the imported source). `ctx.template(name).template`
   returns the raw string; the agent substitutes inline. Acceptable for
   v1; `string.Template` migration is a followup.

## Followup

(Populated when the PR ships.)
