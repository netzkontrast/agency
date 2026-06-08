---
spec_id: "108"
slug: novel-gates-cluster
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["102", "103", "104", "105", "106", "107", "101"]
affects:
  - agency/capabilities/novel/clusters/gates.py
  - agency/capabilities/novel/ontology.py
  - tests/test_novel_gates.py
  - tests/test_novel_e2e.py    # carries the master 101 end-to-end gate
domain: novel / gates / lifecycle
wave: 8
parent_spec: "101"
mvp-source:
  - "Plan/_research/novel-mvp-source/prior-specs/014-gates-and-revision.md"
  - "Plan/_research/novel-mvp-source/references/parity-table.md (pre-drafting-gate, publication-director)"
  - "Plan/100 music-gates-cluster (the proven composite-gate pattern)"
---

# Spec 108 — Novel Gates Cluster

## Why

The lifecycle binder — composes cross-cluster predicates into the
canonical novel-pipeline gates:

- **`pre-draft`**: storyform complete + research verified + outline locked
  → ready to draft chapter 1
- **`beta-ready`**: all chapters drafted + revisions resolved → ready for
  beta readers
- **`query-ready`**: manuscript rendered + query letter + synopsis drafted
  → ready to query agents
- **`publish-ready`**: cover art ready + manuscript final + metadata
  complete → ready to ship

Per the imported `014-gates-and-revision.md`, the pre-drafting gate is
the load-bearing one — it enforces the "no drafting until structure +
research are locked" discipline that makes the rest of the pipeline trust
its inputs.

Also carries the **101 E2E provenance test** that flips 101 → Shipped.

## Done When

- [ ] **6 user-facing verbs ship** (pre-draft / beta-ready / query-ready /
      publish-ready + validate-structure + novel-health).
- [ ] **4 composite gate verbs ship** (one per pre-draft phase composing
      cross-cluster predicates).
- [ ] **4 walkable skills ship**: `pre-draft`, `beta-ready`, `query-ready`,
      `publish-ready`. Each terminates in a hard `elicit` gate.
- [ ] **E2E test ships** at `tests/test_novel_e2e.py` — drives the full
      pipeline through `pre-draft → draft chapter 1 → revise → beta-feedback
      → publish_package` and asserts `eng.memory.provenance(intent_id)`
      returns the full chain (matches the Memory.provenance shape:
      `{serves, agents, artefacts, gates}` — corrected per music
      iteration-6).
- [ ] **101 master row flips to Shipped** once 108 ships Green.
- [ ] **`TODO.md` updated** with 108 row.

## Verb manifest

| # | Verb | Role | Driver / Backing |
|---|---|---|---|
| 1 | `pre_draft_check` | effect | StateDriver+gate.check (composite) |
| 2 | `beta_ready_check` | effect | StateDriver+DBDriver+gate.check |
| 3 | `query_ready_check` | effect | StateDriver+FormatDriver+gate.check |
| 4 | `publish_ready_check` | effect | StateDriver+FormatDriver+CloudDriver+gate.check |
| 5 | `validate_structure` | transform | StateDriver |
| 6 | `novel_health` | transform | (driver-free) |

**Internal composite gate verbs**:

| # | Verb | Composes | Walks |
|---|---|---|---|
| G1 | `storyform_complete_gate` | `novel.novel_coherence_check` (103) + gate.check | `pre-draft` phase 1 |
| G2 | `research_verified_gate` | `novel.verify_gate` (105) + gate.check | `pre-draft` phase 2 |
| G3 | `revisions_resolved_gate` | beta_feedback open count + edit_notes open count + gate.check | `beta-ready` phase 2 |
| G4 | `publication_assets_gate` | manuscript-rendered + cover-art-ready + metadata-complete + gate.check | `publish-ready` phase 3 |

**Total: 6 user + 4 gate = 10 registered verbs.**

## Design

### Walkable skill: `pre-draft` (4 phases)

```python
PRE_DRAFT_SKILL = {
    "name": "pre-draft",
    "kind": "gate",
    "phases": [
        {"index": 1, "name": "storyform-complete",
         "produces": ["storyform_coherent"],
         "gate": "computed", "gate_verb": "novel.storyform_complete_gate"},
        {"index": 2, "name": "research-verified",
         "produces": ["all_claims_human_confirmed"],
         "gate": "computed", "gate_verb": "novel.research_verified_gate"},
        {"index": 3, "name": "outline-locked",
         "produces": ["outline_complete"]},
        {"index": 4, "name": "ready-to-draft",
         "produces": ["approved"], "gate": "hard"},
    ],
}
```

**Primary actor**: agent (composes predicates); human confirms "draft chapter 1" at phase 4.

### Walkable skill: `beta-ready`, `query-ready`, `publish-ready`

Each: 3-4 phases ending in a hard `elicit` gate. Predicates compose
cross-cluster state via `ctx.call` (matches music's pattern; uses
unwrapped dict access per `capability.py:138`).

### Composite gate verb (E2E example)

```python
@verb(role="effect")
def pre_draft_check(self, lifecycle_id: str, novel: str = "") -> ToolResult:
    """Composite pre-draft gate. Reads cross-cluster state:
      - Storyform completeness (103's novel_coherence_check)
      - Research verification (105's verify_gate)
      - Outline state (102's lifecycle)
    Records PASSED/BLOCKED_ON via gate.check. ctx.call returns unwrapped
    dict (capability.py:138) — direct indexing, no .data wrapping.
    """
    state = self.ctx.get_driver("music_state")
    novel_data = state.find_novel(novel)[0]

    # Read predicates from cluster state:
    storyform = self.ctx.call("novel", "novel_coherence_check",
                              lifecycle_id=lifecycle_id, work_id=novel)
    storyform_ok = storyform.get("passed") is True

    research = self.ctx.call("novel", "pending_verifications", novel=novel)
    research_ok = research["pending_count"] == 0

    outline_ok = novel_data.get("outline_status") == "locked"

    missing = []
    if not storyform_ok: missing.append("storyform")
    if not research_ok: missing.append("research")
    if not outline_ok: missing.append("outline")

    passed = not missing
    self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                  name="pre-draft", passed=passed,
                  evidence="all green" if passed else f"missing: {missing}")
    if not passed:
        return ToolResult.failure("GATE_FAILED",
                                  f"pre-draft blocked; missing: {missing}")
    return ToolResult.success(data={"novel": novel, "gate": "pre-draft",
                                    "passed": True})
```

### The 101 E2E test

```python
# tests/test_novel_e2e.py — drives the full pipeline + asserts provenance
def test_novel_full_pipeline_records_complete_provenance_chain(fake_drivers):
    eng = Engine(":memory:", drivers=fake_drivers())
    intent_id = eng.intent.capture_and_confirm(
        purpose="novel X", deliverable="release",
        acceptance="verify provenance", owner="user")
    invoke = lambda cap, verb, **kw: eng.registry.invoke(
        eng.memory, intent_id, cap, verb, agent_id="agent:e2e", **kw)[0]

    # Mint a lifecycle for the gate calls (capability.py:138 pattern; per
    # iteration-6 fix in music — direct memory.record, no helper method):
    lifecycle_id = eng.memory.record("Lifecycle",
                                     {"state": "working", "phase": 0,
                                      "name": "novel-pipeline"})
    eng.memory.link(lifecycle_id, intent_id, "SERVES")

    # 1. lifecycle
    invoke("novel", "capture_idea", text="novel X")
    invoke("novel", "create_novel", author="Author", title="X",
           genre="literary", premise="A story.")

    # 2. storyform (103) — write the NCP first, then validate
    state = eng.registry.get_driver("music_state")
    state.write_ncp("X", {"storyform": {...}, "players": [...], "scenes": [...]})
    invoke("novel", "novel_coherence_check", lifecycle_id=lifecycle_id,
           work_id="X")

    # 3. research (105)
    invoke("novel", "dispatch_research", question="X facts",
           domains="historical", novel="X")
    invoke("novel", "verify_sources", novel="X")

    # 4. pre-draft gate — should pass once steps 2+3 are green
    pre_draft = invoke("novel", "pre_draft_check",
                       lifecycle_id=lifecycle_id, novel="X")
    assert pre_draft.get("passed") is True

    # 5. prose (104)
    invoke("novel", "chapter_report", chapter=1, body="...")

    # 6. catalogue (106)
    invoke("novel", "register_beta_reader", name="Bob", email="b@e.com")
    invoke("novel", "record_beta_feedback", beta_id=1, novel="X",
           chapter=1, text="loved it", sentiment="praise")

    # 7. manuscript (107)
    invoke("novel", "render_manuscript", novel="X", format="manuscript")

    # 8. THE HEADLINE — provenance shape per Memory.provenance
    # (memory.py:243 — returns {serves, agents, artefacts, gates}):
    prov = eng.memory.provenance(intent_id)
    serves_labels = {p.get("__label", "") for p in prov["serves"]}
    assert "Invocation" in serves_labels
    assert "ResearchClaim" in serves_labels
    artefact_kinds = {a.get("kind", "") for a in prov["artefacts"]}
    assert "premise" in artefact_kinds or "novel-readme" in artefact_kinds
    assert "draft" in artefact_kinds
    assert "manuscript" in artefact_kinds
    gate_names = {g.get("name", "") for g in prov["gates"]}
    assert "pre-draft" in gate_names
    assert len(prov["serves"]) >= 10
    assert len(prov["artefacts"]) >= 4
```

## Test plan (cluster-local)

```python
# tests/test_novel_gates.py — ~10 tests
def test_gates_cluster_discovers_all_verbs(): ...
def test_pre_draft_blocks_when_storyform_incoherent(): ...
def test_pre_draft_blocks_when_research_pending(): ...
def test_pre_draft_blocks_when_outline_not_locked(): ...
def test_pre_draft_passes_when_all_green(): ...
def test_beta_ready_blocks_on_unrevised_chapters(): ...
def test_query_ready_blocks_without_synopsis(): ...
def test_publish_ready_blocks_without_cover_art(): ...
def test_validate_structure_reports_missing_files_without_blocking(): ...
def test_pre_draft_skill_walks_through_2_computed_gates(): ...
def test_publish_ready_skill_pauses_on_hard_ship_gate(): ...
```

## Complex-novel extensions (iteration 2)

The cluster grows three additional gate verbs + one walkable skill for
complex novels. All are **opt-in** — they fire only when the novel's
frontmatter declares the relevant complexity field (`pov_count > 1`,
`outline_hierarchy includes "volume"`, `subplot_count > 0`).

### Additional gate verbs

| # | Verb | Composes | Walks |
|---|---|---|---|
| G5 | `pov_balance_gate` | `novel.pov_balance_check` (104) + gate.check (BLOCKED if any POV > 40% unless first-person-protagonist) | `beta-ready` phase 2 (opt-in for multi-POV novels) |
| G6 | `subplot_resolution_gate` | per-Subplot `novel_coherence_check` (103) + cross-storyform consistency + gate.check | `pre-draft` phase 1 alongside `storyform_complete_gate` |
| G7 | `timeline_continuity_gate` | reads `Chapter.story_time` across the novel; flags chronological gaps + duplicate timestamps + impossible character-age math | `beta-ready` phase 2 |
| G8 | `world_canon_gate` | reads `WorldAxiom` nodes + scenes' `ENCODES` edges; flags axioms with `CONTRADICTS` edges and scenes that violate hard-canon axioms | `pre-draft` (opt-in for worldbuilt novels) |

### Additional walkable skill: `series-publish-ready`

For multi-volume series:

```python
SERIES_PUBLISH_READY_SKILL = {
    "name": "series-publish-ready",
    "kind": "gate",
    "phases": [
        {"index": 1, "name": "all-volumes-rendered",
         "produces": ["all_volumes_have_manuscript_artefact"]},
        {"index": 2, "name": "series-coherence",
         "produces": ["series_coherence_clean"],
         "gate": "computed", "gate_verb": "novel.series_coherence_check"},
        {"index": 3, "name": "boxset-rendered",
         "produces": ["boxset_artefact_ready"]},
        {"index": 4, "name": "series-publish",
         "produces": ["series_released"], "gate": "hard"},
    ],
}
```

### Complex-novel fixture (used by the E2E test path 2)

Lands at `tests/fixtures/novel/complex_novel/` and carries:

```
complex_novel/
├── novel.yaml                  # outline_hierarchy: ["volume", "book", "chapter", "scene"]
                                # pov_count: 5
                                # multilingual: true
                                # canon_language: "de"
                                # subplot_count: 2
                                # genres: ["literary", "historical"]
├── volumes/
│   ├── vol-1/
│   │   ├── volume.yaml         # number: 1, title, word_count_target
│   │   └── books/
│   │       ├── book-1/
│   │       │   ├── book.yaml
│   │       │   └── chapters/
│   │       │       └── ch01.yaml  # canon_language: "de", pov_character: ...,
│   │       │                       # narrative_order: 1, story_time: "1899-04-12"
│   │       └── book-2/
│   │           └── ...
│   ├── vol-2/...
│   └── vol-3/...
├── characters/
│   ├── protagonist.yaml         # archetype: Protagonist; voice_signature_by_phase
│   ├── antagonist.yaml
│   ├── pov-2.yaml
│   ├── pov-3.yaml
│   └── pov-4.yaml
├── world/
│   ├── cultures/{c1.yaml, c2.yaml}
│   ├── religions/{r1.yaml}
│   ├── languages/{l1.yaml}
│   ├── magic_systems/{m1.yaml}     # hard_or_soft: hard
│   └── axioms/{a1-a4.yaml}
├── storyforms/
│   ├── main.ncp.json
│   ├── subplot-1.ncp.json
│   └── subplot-2.ncp.json
└── research/
    └── claims.yaml             # 8 claims, all human-confirmed
```

**Invariants the fixture proves**:

| Invariant | Verb that asserts it |
|---|---|
| Volume/Book/Chapter hierarchy navigable | `list_volumes` → `list_books_in_volume` → `list_chapters_in_book` returns 3 → 6 → 24 |
| Multi-POV ≤ 40% concentration | `pov_balance_check`: each of 5 POVs is between 15-25% |
| Multi-Storyform integrity | `novel_coherence_check` returns `{main: PASS, subplot-1: PASS, subplot-2: PASS}` |
| Multilingual: chapters DE, no translations | `extract_language` per-chapter returns `de`; no `translation-draft` artefacts exist |
| WorldAxiom + Canon edges | `world_canon_gate` PASS (no CONTRADICTS edges between axioms) |
| Timeline alignment | `timeline_continuity_gate` PASS (no chronological gaps > 30 days unmotivated) |
| Series-level coherence | `series_coherence_check` PASS across the 3 volumes |
| Provenance moat | full chain returned by `eng.memory.provenance(intent_id)` |

### Extended E2E test (complex-novel run)

`tests/test_novel_e2e.py` ships TWO end-to-end paths:

1. **Simple novel** — the existing pipeline (capture → conceptualize →
   research → storyform-build → pre-draft → draft → revise → beta →
   manuscript-pass). Asserts the 4 base gates fire.

2. **Complex novel** — opts in via:
   - `outline_hierarchy = ["volume", "book", "chapter", "scene"]`
   - 3 volumes, each with 2 books, each with 8 chapters
   - 5 POV characters
   - 2 subplot Storyforms (each its own 4-throughline argument)
   - Worldbuilding: 2 cultures + 1 religion + 1 magic system + 4
     WorldAxioms
   - Series-level: 2 novels in the series, character carryover

   Asserts ALL 8 gates fire (4 base + G5 pov_balance + G6 subplot_
   resolution + G7 timeline_continuity + G8 world_canon), the series-
   publish-ready skill walks to its hard gate, and the provenance moat
   returns the full multi-Storyform chain.

The complex-novel test asserts the design holds — every iteration-2
node + gate participates in the trace.

## Open questions

1. **Pre-draft enforcement strictness**: H1-H12 from the kohaerenz Hard
   Rules are STRICT (FAIL); the approach/concern check from the
   decidability matrix is WARN (passes with warning). 108's
   `storyform_complete_gate` PASSES iff every FAIL-strict check passes;
   WARN-level checks emit findings but don't block.
2. **Beta-feedback gate threshold**: `beta_ready_check` blocks when
   `open` beta-feedback count > 0. Per-novel override (`beta_threshold`)
   in followup.
3. **Validate-structure as gate vs report?** Report (transform) — matches
   music's pattern.

## Followup

(Populated when the PR ships. 101 row flips to Shipped when 108 lands
Green.)
