---
spec_id: "106"
slug: novel-catalogue-cluster
status: draft
state: inprogress
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["102", "101"]
affects:
  - agency/capabilities/novel/clusters/catalogue.py
  - agency/capabilities/novel/drivers.py        # DBDriver extensions
  - agency/capabilities/novel/ontology.py
  - agency/capabilities/novel/migrations/db_init.py
  - tests/test_novel_catalogue.py
domain: novel / catalogue / db
wave: 8
parent_spec: "101"
mvp-source:
  - "Plan/097 music-catalogue-cluster (the proven DBDriver pattern)"
  - "Plan/_research/novel-mvp-source/references/parity-table.md (alpha/critique-partner/beta-reader as novel-specific addition)"
---

# Spec 106 — Novel Catalogue Cluster

## Why

The DBDriver showcase for novels: beta-reader feedback tracking + version
log + edit-note tracking. Lighter than music's tweet DB (no social posting)
but the same psycopg2-shaped pattern.

Per the parity table, alpha-reader / critique-partner / beta-reader are
**novel-specific additions** (no music analog). This cluster is where
pre-editorial human-feedback gates live.

Also carries the **manuscript-coherence-check + series-coherence-check**
split (music's `album_coherence_check` becomes two distinct verbs in the
parity table).

## Done When

- [ ] **10 user-facing verbs ship** (see manifest).
- [ ] **1 composite gate verb** ships: `beta_feedback_gate`.
- [ ] **DBDriver extended** with 7 new methods (psycopg2-shaped fake).
- [ ] **`db_init` migration** under `migrations/` — schema for
      `beta_readers`, `beta_feedback`, `edit_notes`, `manuscript_versions`
      tables.
- [ ] **Walkable skill `beta-feedback`** ships (4 phases — assign →
      collect → triage → close).
- [ ] **`tests/test_novel_catalogue.py` Green** (~10 tests; zero Postgres
      host).
- [ ] **`TODO.md` updated** with 106 row.

## Verb manifest

| # | Verb | Role | Driver | Music analog |
|---|---|---|---|---|
| 1 | `register_beta_reader` | effect | DBDriver | (new) |
| 2 | `assign_beta_reader` | effect | DBDriver | (new) |
| 3 | `record_beta_feedback` | effect | DBDriver | `db_create_tweet` |
| 4 | `list_beta_feedback` | transform | DBDriver | `db_list_tweets` |
| 5 | `triage_feedback` | effect | DBDriver | (new) |
| 6 | `add_edit_note` | effect | DBDriver | (new) |
| 7 | `list_edit_notes` | transform | DBDriver | `db_list_tweets` |
| 8 | `manuscript_coherence_check` | transform | StateDriver | `album_coherence_check` (split A) |
| 9 | `series_coherence_check` | transform | StateDriver | `album_coherence_check` (split B) |
| 10 | `version_log` | transform | DBDriver+StateDriver | (new) |

**Internal gate**:

| # | Verb | Composes |
|---|---|---|
| G1 | `beta_feedback_gate` | open-feedback count + chapter-coverage + gate.check |

**Total: 10 user + 1 gate = 11 registered verbs.**

## Design

### DBDriver method delta

```python
class DBDriver(Boundary):
    # reused from music
    def cursor(self) -> Cursor: ...  # psycopg2-shaped

    # new methods (106)
    def register_beta_reader(self, name: str, email: str) -> int: ...
    def assign_beta_reader(self, beta_id: int, novel: str,
                           chapters: list[int]) -> None: ...
    def record_beta_feedback(self, beta_id: int, novel: str, chapter: int,
                             text: str, sentiment: str) -> int: ...
    def list_beta_feedback(self, novel: str = "",
                           sentiment: str = "") -> list[dict]: ...
    def triage_feedback(self, feedback_id: int, action: str) -> None: ...
    def add_edit_note(self, novel: str, chapter: int, text: str) -> int: ...
    def list_edit_notes(self, novel: str = "",
                        status: str = "") -> list[dict]: ...
```

### Schema (Postgres)

```sql
CREATE TABLE IF NOT EXISTS beta_readers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS beta_assignments (
    id SERIAL PRIMARY KEY,
    beta_reader INTEGER REFERENCES beta_readers(id),
    novel TEXT NOT NULL,
    chapters JSONB,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS beta_feedback (
    id SERIAL PRIMARY KEY,
    beta_reader INTEGER REFERENCES beta_readers(id),
    novel TEXT NOT NULL,
    chapter INTEGER,
    text TEXT NOT NULL,
    sentiment TEXT NOT NULL DEFAULT 'concern',
    status TEXT NOT NULL DEFAULT 'open',  -- open / triaged / addressed
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS edit_notes (
    id SERIAL PRIMARY KEY,
    novel TEXT NOT NULL,
    chapter INTEGER,
    text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS manuscript_versions (
    id SERIAL PRIMARY KEY,
    novel TEXT NOT NULL,
    version TEXT NOT NULL,
    body_hash TEXT NOT NULL,
    change_log TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Walkable skill: `beta-feedback`

```python
BETA_FEEDBACK_SKILL = {
    "name": "beta-feedback",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "assign",
         "produces": ["beta_readers_assigned"]},
        {"index": 2, "name": "collect",
         "produces": ["all_chapter_feedback_collected"],
         "gate": "computed", "gate_verb": "novel.beta_feedback_gate"},
        {"index": 3, "name": "triage",
         "produces": ["all_feedback_triaged"]},
        {"index": 4, "name": "close",
         "produces": ["beta_round_closed"],
         "gate": "hard"},
    ],
}
```

### Manuscript vs series coherence split

```python
@verb(role="transform")
def manuscript_coherence_check(self, novel: str) -> ToolResult:
    """Within-novel continuity: timeline, names, world-rules, character
    voice. Reads chapters + character notes via StateDriver; emits a
    findings report (NOT a gate — informational)."""

@verb(role="transform")
def series_coherence_check(self, series: str) -> ToolResult:
    """Across-series arc + canon. Checks character-arc continuity,
    world-rule consistency, timeline alignment between novels. Reads
    every novel in the series."""
```

## Test plan

```python
# tests/test_novel_catalogue.py — ~10 tests (zero Postgres host)
def test_catalogue_cluster_discovers_all_verbs(): ...
def test_register_beta_reader_returns_id(): ...
def test_assign_beta_reader_links_to_novel_and_chapters(): ...
def test_record_beta_feedback_inserts_with_sentiment_enum_check(): ...
def test_list_beta_feedback_filters_by_novel_and_sentiment(): ...
def test_triage_feedback_flips_status(): ...
def test_add_edit_note_inserts_with_default_open_status(): ...
def test_version_log_aggregates_versions(): ...
def test_manuscript_coherence_check_returns_findings(): ...
def test_series_coherence_check_aggregates_across_novels(): ...
def test_beta_feedback_skill_walks_through_gate(): ...
def test_catalogue_verb_fails_typed_when_db_driver_missing(): ...
```

## Complex-novel extensions (iteration 2)

The catalogue cluster grows three new TRANSFORM verbs for complex-novel
diagnostics (no schema changes — the new verbs read the ontology nodes
102 declares):

| # | Verb | Reads | Reports |
|---|---|---|---|
| 11 | `arc_coverage_report` | `Arc` + `ArcPhase` nodes | per-Character: phases-covered / phases-pending / phases-skipped |
| 12 | `cast_hierarchy_report` | `Faction` / `House` / `Family` nodes | tree-render of faction → house → family → character with member counts |
| 13 | `worldbuilding_coverage` | `World` + sub-schema nodes | gap report: cultures-defined / cultures-mentioned-but-undefined; same for religions, languages, magic systems |

These verbs DO NOT gate — they inform the human-curator pass at the
review-discipline phase. (Gates that consume them live in 108.)

### Series-level coherence (`series_coherence_check` extended)

The existing `series_coherence_check` (verb 9) gains a 4-axis report when
the novel set has `Volume` / `Part` / `Book` hierarchy:

1. **Character age math**: a character born in year X must be the right
   age in every subsequent novel's `story_time`
2. **WorldAxiom consistency**: no `CONTRADICTS` edges between axioms
   defined across novels in the same series
3. **Timeline alignment**: no event in Novel N's `story_time` happens
   AFTER the same event referenced in Novel N+1
4. **Cast carryover**: dead characters do not appear in later novels'
   `story_time > death_time`

Each axis emits its own findings array; a `WARN` (not a `FAIL`) blocks
nothing but feeds the publication-director skill.

## Draft-variant experimentation (iteration 3)

Real writers experiment: "what if I rewrote this chapter from another
POV?", "what if the antagonist wins this scene?", "what if I cut chapter
17 entirely?" The design supports this through **graph-branch variants**
without leaving the substrate:

### `DraftVariant` node

```python
# Added to 102's consolidated ontology (iteration 3):
DraftVariant     (slug, chapter, parent_draft, hypothesis, status,
                  body, branch_at, branched_by)
# branch_at: ISO timestamp of when this variant was forked
# parent_draft: the Draft this variant branches from
# hypothesis: agent's note on what's being explored
# status: experimental | promoted | abandoned
```

### Two new effect verbs (in 106)

```python
@verb(role="effect")
def branch_draft_variant(self, novel: str, chapter: int,
                         hypothesis: str) -> ToolResult:
    """Fork a chapter into a DraftVariant for experimentation. The
    variant lives alongside the main draft; both are in the graph;
    verbs that read 'the draft' read the main unless variant_slug
    is passed."""

@verb(role="effect")
def promote_draft_variant(self, variant_slug: str) -> ToolResult:
    """Promote a variant to be the main draft. Records a REVISES edge
    from the new main back to the old main (provenance preserved); the
    old main becomes 'archived' status."""
```

### Walkable skill: `experiment-pass` (new)

```python
EXPERIMENT_PASS_SKILL = {
    "name": "experiment-pass",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "branch",
         "produces": ["variant_created"]},
        {"index": 2, "name": "draft-variant",
         "produces": ["variant_body_written"]},
        {"index": 3, "name": "compare",
         "produces": ["variant_metrics_compared"]},
        {"index": 4, "name": "decide",
         "produces": ["variant_decision_made"],
         "gate": "hard"},   # human chooses: promote / archive / keep-both
    ],
}
```

Test asserts that branching does NOT break the provenance moat —
`memory.provenance(intent_id)` returns both the main draft AND the
variant tree.

## Beta-reader engagement schema (iteration 5)

Extends the catalogue schema with structured per-chapter polling +
reading-session tracking. Three new nodes (declared in 102's
consolidated ontology):

```python
BetaPoll       (beta_reader, novel, chapter, question, response,
                response_time_minutes, submitted_at)
ReadingSession (beta_reader, novel, start_chapter, end_chapter,
                started_at, ended_at, dropoff: bool)
SpoilerScope   (beta_reader, novel, last_chapter_submitted_feedback_on)
```

### Three new effect verbs

```python
@verb(role="effect")
def record_beta_poll(self, beta_id: int, novel: str, chapter: int,
                     question: str, response: str,
                     response_time_minutes: int) -> ToolResult: ...

@verb(role="effect")
def record_reading_session(self, beta_id: int, novel: str,
                           start_chapter: int, end_chapter: int,
                           dropoff: bool = False) -> ToolResult: ...

@verb(role="effect")
def update_spoiler_scope(self, beta_id: int, novel: str,
                         last_chapter: int) -> ToolResult: ...
```

### One new transform verb

```python
@verb(role="transform")
def engagement_dashboard(self, novel: str) -> ToolResult:
    """Per-chapter aggregate: average engagement, response-time, dropoff
    count. Surfaces the load-bearing 'high-dropoff' signal for
    developmental editing."""
```

### `list_beta_feedback` extended

Accepts `spoiler_aware: bool = False` parameter. When True, returns ONLY
feedback for chapters in the BetaReader's `SpoilerScope.last_chapter_
submitted_feedback_on` range — prevents late-chapter spoilers when
beta is still on chapter 5.

## Open questions

1. **Coherence-check as gate or report?** Report (transform), per the
   parity table — "manuscript_coherence_check + series_coherence_check"
   are diagnostic, not blocking. The actual gate ships in 108.
2. **Beta-feedback retention**: no auto-expire. Manual `triage` flips
   status. v2 may add `archive_old_feedback`.
3. **Series modeling**: 102 declares `Series` node. 106's
   `series_coherence_check` iterates novels via the StateDriver +
   `novel.series_slug` field. No separate Series-feedback table needed.

## Followup — Implementation Status (2026-06-09)

**Slice 1 SHIPPED** on branch `claude/spec-102-novel-lifecycle` (PR #80).

### Done in Slice 1

1 graph-only coherence verb: `manuscript_coherence_check(novel_id)` —
walks Chapter nodes CHAPTER_OF the novel, reports gaps in [1..max].

5 tests in `tests/test_novel_catalogue.py`.

### Deferred to Slice 2+

DBDriver protocol + 9 DBDriver-backed verbs (beta reader registry,
edit notes, version log, series_coherence) + composite
beta_feedback_gate + per-cluster file split.
