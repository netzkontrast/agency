---
spec_id: "120"
slug: novel-storyform-completion
status: draft
last_updated: 2026-06-09
owner: "@agency"
depends_on: ["103", "101"]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_storyform*.py
domain: novel / storyform / dramatica
parent_spec: "101"
mvp-source:
  - "agency/capabilities/novel/data/reference/implementation-spec-libs.md (resolve_term contract)"
  - "agency/capabilities/novel/data/reference/coherence-checks-spec.md (11-check report shape)"
  - "agency/capabilities/novel/data/reference/dramatica-decidability.md (15-row matrix)"
  - "tests/fixtures/novel/ (12 NCP oracles)"
---

# Spec 120 — Novel Storyform Completion (the remaining Dramatica engine)

## Why

Spec 103 shipped 3 of 15 decidability-matrix rows (5, 4, 11) plus the
fixtures + ontology. The remaining 9 decidable + 2 hybrid checks were
deferred behind ONE blocker, now diagnosed precisely:

**The element-id ↔ ontology gap is a KIND mismatch, not missing data.**
Fixtures reference `el.self-interest` / `el.morality`; the vendored
ontology carries them as `var.self-interest` / `var.morality`
(variations), and the dynamic pair `dp.morality-self-interest` IS
declared. In Dramatica theory the same term can appear at variation and
element level; the vendored `implementation-spec-libs.md` already
specifies the canonical fix: a kind-agnostic `resolve_term(id)` that
matches on slug across kinds.

Two retractions during 103 (quad_completeness fired on 2 fixtures;
signpost_permutation over-fired when class_id mutated) both trace to
the same root: checks need ontology lookup + check-chaining to hold the
Rec-2 exact-fail contract. This spec closes both.

## Done When

- [ ] `_resolve_term(term_id)` module helper: strips kind prefix,
      matches slug across all 304 entries; returns `(entry, exact_kind_match: bool)`.
      Memoized alongside `_load_dramatica_ontology`.
- [ ] **9 remaining decidable checks ship** (rows 1, 2, 3, 6, 7, 8, 9, 10):
      `check_dynamic_pair_reciprocity`, `check_ktad_coverage`,
      `check_quad_completeness`, `check_crucial_element_placement`,
      `check_resolve_outcome_judgment`, `check_approach_concern` (WARN),
      `check_mental_sex_problem_solving`, `check_signpost_permutation`.
- [ ] **Check-chaining**: `check_signpost_permutation` and
      `check_quad_completeness` gate on `check_throughline_partition`
      passing first (per the Slice-2 retraction lesson — the over-fire
      becomes structural, not spurious).
- [ ] **2 hybrid checks ship**: `validate_appreciations` +
      `validate_narrative_functions` already exist (Spec 105 xcap slice);
      wire them into the composite.
- [ ] **`novel_coherence_check(novel_id)` composite gate verb** — runs all
      checks, accumulates violations, records `gate.check`
      (`storyform-coherent`); report ≤ 400 tokens per
      coherence-checks-spec.md.
- [ ] **`storyform-build` 6-phase walkable skill** per Spec 103 design.
- [ ] **Exact-fail contract holds for ALL 11 fixtures**: parametrized test
      asserts each `broken_work_<row>` fails EXACTLY its named check
      under the composite (chaining makes this tractable).
- [ ] `record_storyform_decision` (dogfood xcap) fires on every check
      retraction/carve-out — per goal's tight-integration contract.
- [ ] TODO.md row updated.

## Design notes

- Graph-only continues: no TextDriver. `_resolve_term` is a module fn.
- The resolve-outcome-judgment table (row 7) is a 4-row lookup
  (Outcome × Judgment → ending type) — ship as documented in-code table.
- KTAD coverage (row 2) reads `ktad_position` from term entries.
- Report shape: PASS drops `items`; ids not labels; ≤120-char violations.

## Open questions

1. `check_approach_concern` is WARN-severity — does the composite treat
   WARN as pass-with-note or block? (Recommend: pass-with-note,
   surfaced in report `warnings` array.)
2. Does `resolve_term` exact_kind_match=False emit a violation or a
   warning? (Recommend: warning — the fixtures themselves use el. for
   var.-level terms, so strict kind would re-break the oracle suite.)

## Followup

(Populated when the PR ships.)
