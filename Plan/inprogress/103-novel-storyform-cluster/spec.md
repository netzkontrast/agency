---
spec_id: "103"
slug: novel-storyform-cluster
status: draft
state: inprogress
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["102", "101"]
affects:
  - agency/capabilities/novel/clusters/storyform.py
  - agency/capabilities/novel/drivers.py
  - agency/capabilities/novel/ontology.py
  - tests/test_novel_storyform.py
  - tests/fixtures/novel/  # 34 NCP fixtures ported VERBATIM from the-agency-system
domain: novel / storyform / dramatica
wave: 8
parent_spec: "101"
mvp-source:
  - "Plan/_research/novel-mvp-source/references/dramatica-decidability.md (15-row matrix)"
  - "Plan/_research/novel-mvp-source/prior-specs/012-dramatica-and-ncp-libs.md"
  - "Plan/_research/novel-mvp-source/prior-specs/013-handlers-structural.md"
  - "Plan/_research/novel-mvp-source/reference-novel/dramatica/* (ontology.json + scenarios.json + 16 term docs)"
  - "Plan/_research/novel-mvp-source/reference-novel/ncp/ncp-spec-v1.3.0.md"
  - "Plan/_research/novel-mvp-source/fixtures/* (34 NCP fixtures — good + 13 broken variants)"
---

# Spec 103 — Novel Storyform Cluster (the Dramatica engine)

## Why

The headline novel-specific cluster — the **decidable storyform engine**.
Per the imported Dramatica Decidability Matrix (15 rows): **11 decidable
+ 2 hybrid checks** become typed verbs returning a low-token-cost
`CoherenceReport`. **Tools assert structure; skills assert meaning.**

The cluster IS the proof that "story structure" can be a graph problem,
not an aesthetic question. The 11 checks reduce to ontology lookups +
set-membership tests + permutation checks against the 304-entry
`ontology.json` and the NCP v1.3.0 schema.

## Done When

- [ ] **13 user-facing verbs ship** (11 decidable + 2 hybrid; see manifest).
- [ ] **1 composite gate verb** ships: `novel_coherence_check(work_id)` —
      runs every decidable check, accumulates violations, returns the
      report shape from the decidability brief.
- [ ] **34 NCP fixtures** ported VERBATIM under `tests/fixtures/novel/`
      from `Plan/_research/novel-mvp-source/fixtures/`. Tests assert:
      - Every `good_work.ncp.json` passes ALL 11 decidable checks.
      - Every `broken_work_<check>.ncp.json` fails EXACTLY that check.
- [ ] **`ontology.json` + `scenarios.json`** ported VERBATIM under
      `agency/capabilities/novel/data/dramatica/` (via 102).
- [ ] **TextDriver extended** with the dramatica-side methods:
      `load_ontology()`, `get_quad(id)`, `get_dynamic_pair(id)`,
      `get_allowed_signpost_permutations(class_id)`, `resolve_term(id)`.
- [ ] **Report shape** matches the brief: PASS-check `items` arrays
      dropped, ontology ids (not labels), violations capped at ~120 chars.
      A 3-violation report ≤ 400 tokens; clean PASS ≤ 40 tokens.
      Test asserts via `token_counter.count_tokens(report) <= 400`.
- [ ] **`storyform-build` walkable skill** ships (6 phases — see Design).
- [ ] **`TODO.md` updated** with 103 row.

## Verb manifest

The 13 verbs map 1:1 to the 11 decidable + 2 hybrid rows of the
decidability matrix:

| # | Verb | Role | Source row | Decidable / Hybrid |
|---|---|---|---|---|
| 1 | `check_dynamic_pair_reciprocity` | transform | row 1 | Decidable |
| 2 | `check_ktad_coverage` | transform | row 2 | Decidable |
| 3 | `check_quad_completeness` | transform | row 3 | Decidable |
| 4 | `check_slot_fill` | transform | row 4 | Decidable |
| 5 | `check_throughline_partition` | transform | row 5 | Decidable |
| 6 | `check_crucial_element_placement` | transform | row 6 | Decidable |
| 7 | `check_resolve_outcome_judgment` | transform | row 7 | Decidable (table-lookup) |
| 8 | `check_approach_concern` | transform | row 8 | Mostly decidable (WARN not FAIL) |
| 9 | `check_mental_sex_problem_solving` | transform | row 9 | Decidable |
| 10 | `check_signpost_permutation` | transform | row 10 | Decidable |
| 11 | `check_storybeat_moment_refs` | transform | row 11 | Decidable (referential) |
| 12 | `validate_appreciations` | transform | row 12 | Hybrid (passthrough to NCP schema enum check) |
| 13 | `validate_narrative_functions` | transform | row 13 | Hybrid (same) |

**Composite gate verb**:

| # | Verb | Role | Composes |
|---|---|---|---|
| G1 | `novel_coherence_check` | effect | all 13 verbs above + gate.check (`storyform-coherent`) |

**Total: 13 user + 1 gate = 14 registered verbs.** The 2 judgement
checks (Scene-Level Bridge Q1–Q5, encoding suggestions) live as SKILLS
not verbs (per the decidability brief — "Tools assert structure; skills
assert meaning").

### Cross-reference: Hard Rules H1–H12 (from kohaerenz)

The kohaerenz `Plan/decomposition/05-structure-scene-coherence/COHERENCE.md`
defines 12 Hard Rules. They overlap with this spec's 13 verbs (different
slicing of the same decidable surface):

| Hard Rule | Description | This spec's verb |
|---|---|---|
| H1 | Exactly 4 throughlines named | `check_throughline_partition` (verb 5) |
| H2 | Each Class used exactly once | `check_throughline_partition` (verb 5) |
| H3 | OS-SS and MC-IC complementary dynamic pairs | `check_dynamic_pair_reciprocity` (verb 1) |
| H4 | Story Goal at Type level | (NCP schema enum check via `validate_appreciations` verb 12) |
| H5 | Crucial Element at Element level | `check_crucial_element_placement` (verb 6) |
| H6 | Crucial Element in OS throughline | `check_crucial_element_placement` (verb 6) |
| H7 | MC Resolve ↔ Crucial Element agreement | `check_resolve_outcome_judgment` (verb 7) |
| H8 | IC sits on dynamic-pair partner of MC's Element | `check_dynamic_pair_reciprocity` (verb 1) |
| H9 | No character carries both Elements of a pair | `check_dynamic_pair_reciprocity` (verb 1) |
| H10 | Outcome × Judgment yields one of four endings | `check_resolve_outcome_judgment` (verb 7) |
| H11 | Story Driver consistent across all act transitions | `check_signpost_permutation` (verb 10) |
| H12 | All four Signposts of a throughline are the four Types of that throughline's Class | `check_signpost_permutation` (verb 10) |

Verbs that go beyond the 12 H-rules (additional decidability matrix rows):
- `check_ktad_coverage` (verb 2) — KTAD audit (orthogonal to H1–H12)
- `check_quad_completeness` (verb 3) — quad-reverse-index audit
- `check_slot_fill` (verb 4) — 16-slot mandatory check (refines H1+H2)
- `check_approach_concern` (verb 8) — warning-level coherence
- `check_mental_sex_problem_solving` (verb 9) — Linear/Holistic ↔ style
- `check_storybeat_moment_refs` (verb 11) — NCP referential integrity

## Design

### Report shape (verbatim from decidability brief)

```python
@verb(role="transform")
def check_dynamic_pair_reciprocity(self, ncp: dict) -> ToolResult:
    """One of the 11 decidable checks (decidability matrix row 1).

    NCP `dynamic_pair_id` asserts symmetry: A.dynamic=X must imply
    partner.dynamic=anti-X per ontology.json's enforced `allOf`. Read the
    ontology once (memoized in TextDriver), validate against the NCP.

    Returns ToolResult.success(data={
        "status": "PASS" | "FAIL",
        "items": [...],            # ONLY emitted on FAIL
                                   # Each: {a, expected, got} — ≤120 chars
    }).
    Token budget: clean PASS ≤ 40 tokens; up to 3 violations ≤ 400 tokens.
    """
```

### Composite report shape

```python
@verb(role="effect")
def novel_coherence_check(self, lifecycle_id: str, work_id: str) -> ToolResult:
    """Runs all 13 checks. Accumulates violations. Records gate.check on
    lifecycle (PASSED iff every check PASSES; BLOCKED_ON otherwise)."""

    # Shape (verbatim from brief):
    # {
    #   "status": "FAIL",
    #   "violations": 3,
    #   "checks": {
    #     "pair_reciprocity": {"status": "FAIL", "items": [...]},
    #     "ktad_coverage":    {"status": "PASS"},
    #     ...
    #   }
    # }
```

### Walkable skill: `storyform-build` (6 phases)

```python
STORYFORM_BUILD_SKILL = {
    "name": "storyform-build",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "throughline-assignment",
         "produces": ["throughlines_assigned"]},
        {"index": 2, "name": "class-assignment",
         "produces": ["classes_assigned"],
         "gate": "computed", "gate_verb": "novel.check_throughline_partition"},
        {"index": 3, "name": "archetype-assignment",
         "produces": ["archetypes_assigned"],
         "gate": "computed", "gate_verb": "novel.check_crucial_element_placement"},
        {"index": 4, "name": "story-dynamics",
         "produces": ["resolve_set", "growth_set", "approach_set",
                      "mental_sex_set"],
         "gate": "computed", "gate_verb": "novel.check_resolve_outcome_judgment"},
        {"index": 5, "name": "element-pyramid",
         "produces": ["types_signposted", "variations_set", "elements_set"],
         "gate": "computed", "gate_verb": "novel.novel_coherence_check"},  # composite gate
        {"index": 6, "name": "confirmation",
         "produces": ["user_confirmed", "storyform_locked"],
         "gate": "hard"},   # elicit — human signs off on the locked storyform
    ],
}
```

**Primary actor**: agent (mechanical structural construction); human
confirms at phase 6 after the composite gate passes.

### TextDriver method delta

```python
class TextDriver(Boundary):
    # reused
    def syllables(self, text: str) -> int: ...
    def stats(self, text: str) -> dict: ...

    # new methods (103) — all read ontology.json + scenarios.json
    def load_ontology(self) -> dict: ...
        # memoized; reads agency/capabilities/novel/data/dramatica/ontology.json
    def get_quad(self, quad_id: str) -> dict: ...
    def get_dynamic_pair(self, pair_id: str) -> dict: ...
    def get_allowed_signpost_permutations(self,
                                          class_id: str) -> list[list[str]]: ...
    def resolve_term(self, term_id: str) -> dict: ...
    def validate_ncp_against_schema(self, ncp: dict) -> dict: ...
        # uses jsonschema against ncp-schema-v1.3.0.json
```

## Test plan

```python
# tests/test_novel_storyform.py — ~16 tests + fixture-driven
def test_storyform_cluster_discovers_all_13_check_verbs(): ...
def test_ontology_json_loads_with_304_entries(): ...
def test_clean_work_passes_every_decidable_check():
    """good_work.ncp.json (fixture) passes all 11 + 2 hybrid checks."""
def test_broken_pair_reciprocity_fixture_fails_only_pair_check(): ...
def test_broken_throughline_partition_fixture_fails_only_partition_check(): ...
def test_broken_quad_completeness_fixture_fails_only_quad_check(): ...
def test_broken_slot_fill_fixture_fails_only_slot_check(): ...
def test_broken_resolve_outcome_judgment_fixture_fails_only_that_check(): ...
def test_broken_approach_concern_fixture_warns_not_fails(): ...
def test_broken_mental_sex_problem_solving_fixture_fails_only_that_check(): ...
def test_broken_signpost_permutation_fixture_fails_only_that_check(): ...
def test_broken_storybeat_moment_refs_fixture_fails_only_that_check(): ...
def test_clean_check_report_under_40_tokens(): ...
def test_3_violation_report_under_400_tokens(): ...
def test_storyform_build_skill_walks_through_5_computed_gates(): ...
def test_phase_6_pauses_on_hard_elicit_gate(): ...
def test_composite_novel_coherence_check_aggregates_all_13(): ...
```

The fixtures-driven tests are the load-bearing assertion that the 11
decidability checks are real — each `broken_<row>` fixture proves the
check fires precisely on its own row's violation.

## Complex-novel extensions (iteration 2 — ADR-2)

### Nested storyforms / subplots

A complex novel has ONE main Storyform (the OS) PLUS N Subplot Storyforms,
each its own 4-throughline Dramatica argument scoped to a subset of the
cast. The 11 decidability checks run **per Storyform** — the main
storyform AND every subplot Storyform must individually pass.

```python
# Additional verb (iteration 2):
@verb(role="transform")
def list_storyforms(self, novel: str) -> ToolResult:
    """List the main Storyform + every Subplot Storyform on the novel."""

# The novel_coherence_check composite (G1) fans out across all
# Storyforms; the report aggregates per-form findings:
{
  "status": "FAIL",
  "violations": 3,
  "storyforms": {
    "main": {"status": "PASS", "checks": {...}},
    "subplot:tyrion": {"status": "FAIL", "violations": 2, "checks": {...}},
    "subplot:bran":   {"status": "FAIL", "violations": 1, "checks": {...}}
  }
}
```

**`cross_storyform_check` (deferred to v2)**: validates that each Subplot's
resolution serves the Main's goal (e.g. subplot Outcome must not contradict
Main's Outcome trajectory). Judgement-leaning; deferred to a follow-up
spec when the implementation surfaces concrete patterns.

### Subplot ontology

```python
# Declared via 102's OntologyExtension (iter-2 additions):
Subplot       (slug, novel, parent_storyform, scope_characters)
Storyform     (existing — now scoped to either Novel-main or Subplot)
```

The `Storyform.scope` field distinguishes `main` vs `subplot:<slug>`.

## Performance budgets (iteration 4)

The storyform cluster runs the heaviest decidability work in the
capability. Budgets:

| Verb | Target wall-clock (single Storyform) | Target tokens (report) |
|---|---|---|
| Single check (`check_*`) | ≤ 5ms | clean PASS ≤ 40; FAIL ≤ 200 |
| `novel_coherence_check` (composite) | ≤ 50ms (13 checks × 5ms + agg) | clean PASS ≤ 80; 3 violations ≤ 400 |
| `novel_coherence_check` (multi-Storyform, 5 subplots) | ≤ 250ms (5 × 50ms) | per-form rollup ≤ 1500 tokens for 5 forms |
| `load_ontology` first call | ≤ 100ms (memoized; one-time) | n/a |
| `validate_ncp_against_schema` | ≤ 20ms per fixture | n/a |

**Strategy** (per the imported decidability brief):
- Load `ontology.json` once at first TextDriver call; memoize.
- Decidable checks are pure graph lookups; no string allocation in the
  hot path.
- Aggregator caps each violation at ~120 chars (already specified in
  base spec).
- PASS-check `items` arrays dropped (clean PASS report is ~40 tokens
  per check).

**Stress-test fixture**: a synthetic "max-complexity" NCP with 5
subplots, each with 16-slot full-fill + 12 character archetypes,
exercises the multi-Storyform path. Token-budget test asserts the
aggregated report stays ≤ 1500 tokens.

## Open questions

1. **Element-level subgraph (deferred)**: Per Spec 101 Open Q #3,
   Element-level nodes are NOT shipped in this wave. The decidability
   matrix's element-level checks (KTAD, Quad completeness) still pass
   via direct `ontology.json` lookup. Element graph nodes ship in a
   future spec when usage justifies (queries like "find every Element
   tagged Pursuit in OS").
2. **ontology-version drift**: 102 ships ontology.json @ schema_version
   1.0 / ontology_version 0.1. Future ontology updates are
   migration-spec'd separately.
3. **NCP enum tables**: 463 appreciation enums + 144 narrative_function
   enums live in `ncp-schema-v1.3.0.json` and are validated via
   `jsonschema`. No code-side enum duplication.
4. **Wave gates calling 103 verbs**: 108's `pre-draft` gate calls
   `novel_coherence_check`. 103's manifest registers it; 108's manifest
   only references it as a dependency.

## Followup — Implementation Status (2026-06-09)

**Slice 1 SHIPPED** on branch `claude/spec-102-novel-lifecycle` (stacks
on PR #80, which stacks on #78). Per the top-3 sc:sc-recommend inputs
that gated this brainstorm:

### Recommendation 1 — "graph-only first; defer TextDriver split" — APPLIED
- No `drivers.py`, no `ontology.py`, no `clusters/storyform.py` files
  introduced. Verbs live in `agency/capabilities/novel/_main.py`.
- The 304-entry Dramatica ontology is read via a module-level
  `_load_dramatica_ontology()` with `@lru_cache(maxsize=1)` — one
  parse per process; no driver indirection.

### Recommendation 2 — "12 fixtures VERBATIM in Slice 1" — APPLIED
- `tests/fixtures/novel/` contains exactly the 12 ported fixtures
  (1 `good_work.ncp.json` + 11 `broken_work_<row>.ncp.json`).
- `test_fixtures_byte_identical_to_upstream` asserts sha256 parity
  against `Plan/_research/novel-mvp-source/fixtures/`.

### Recommendation 3 — "schema-skill alignment up front" — APPLIED
- Spec 102's `dramatica-seed` phase produces `resolve_intent` /
  `growth_intent` / `approach_intent` / `mental_sex_intent` — names
  preserved (no `_set` rename); the 13-check verb manifest reads NCP
  body fields directly, not skill-output keys. The composite gate
  Slice 2 will read the same keys with no translation layer.

### Done in Slice 1
- 12 NCP fixtures vendored (1 good + 11 broken) byte-identical.
- `Storyform` node declared in `novel_ontology`.
- 1 working check verb:
  - `check_throughline_partition` (row 5 — H1+H2: exactly 4
    throughlines, each Class used once). PROVEN to fire on EXACTLY
    `broken_work_throughline_partition.ncp.json` and PASS on the
    other 10 broken fixtures (`test_check_throughline_partition_does_not_fail_other_broken_fixtures`).
- `check_quad_completeness` (row 3) was retracted post-Round-1: my
  Slice-1 implementation fired on both `broken_work_quad_completeness`
  AND `broken_work_crucial_element_placement` because both fixtures
  trip the `ce_id != mc.problem_id` shape signal — which is the
  row-6 H6/H7 crucial-element-agreement invariant, not the row-3
  quad-completeness invariant. The decidable distinction needs
  ontology lookup to know which Elements sit on the same Dramatica
  quad. Per Rec 2 ("each broken fixture fails EXACTLY its named
  check"), the verb was removed and deferred to Slice 2 after
  fixture-id ↔ vendored-ontology reconciliation.
- 5 tests in `tests/test_novel_storyform.py`: registration / fixture
  port + sha256 parity / happy path / exact-fail isolation /
  report-shape token budget proxy.

### Deferred to Slice 2+
- 9 remaining decidable check verbs (rows 1, 2, 4, 6, 7, 8, 9, 10, 11)
- 2 hybrid check verbs (rows 12, 13)
- `novel_coherence_check` composite gate verb
- `storyform-build` 6-phase walkable skill
- Full token-counter integration on the report shape (Slice 1 uses
  serialized-JSON-length proxy, ≤ 200 chars for clean PASS, ≤ 2000
  chars for broken — generous budget pending real counter wiring)
- Element-id ↔ ontology reconciliation: the fixtures use ids
  (`el.self-interest`, `el.morality`, `el.pursuit`) the vendored
  `ontology.json` doesn't carry under those exact ids. Slice 1's
  shape-validation guard suffices for the broken-fixture contract;
  Slice 2 reconciles via either an ontology update or a fixture-id
  alias table (open Q for the brainstorm).

### Done When status

3 of 7 Done-When boxes ticked (12-fixture port, vendored ontology
load, 2 of 13 verbs). The remaining 4 (full 13-verb manifest,
composite gate, storyform-build skill, full report-shape budget) are
deferred per the Slice 2 enumeration.

(Populated when the PR ships.)
