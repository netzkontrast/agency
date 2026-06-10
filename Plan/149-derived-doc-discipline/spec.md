---
spec_id: "149"
slug: derived-doc-discipline
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "054"
depends_on: ["054", "080", "081", "146", "150"]
vision_goals: [7, 6, 4]
affects:
  - scripts/derive-docs
  - scripts/check-doc-drift
  - agency/capabilities/document/_main.py
  - tests/test_derived_doc_discipline.py
---

# Spec 149 — Derived-doc discipline (TODO + matrix + SkillDoc self-update)

## Why

Specs 054 / 080 / 081 ship drift guardrails but every existing spec
still carries HAND-AUTHORED test counts ("17 new tests + 295 green"),
hand-authored verb lists in its TODO row, and hand-authored
cross-references that rot the first time anything moves — exactly the
derivability anti-pattern CLAUDE.md rule 8 + the field-tested
"derivability audit" warn against. The status-table rows, the
alignment matrix, and the SkillDoc bodies should DERIVE from the live
registry + graph + test suite, and a lint should fail when a rendered
doc diverges from its source.

## Done When

- [ ] **`scripts/derive-docs`** regenerates, from live sources:
      - per-spec test counts (from `pytest --collect-only -q` keyed by
        the spec's `affects:` test files),
      - per-spec verb lists (from the live registry, filtered by the
        capability the spec owns),
      - the alignment-matrix Goal column (from each spec's
        `vision_goals:` frontmatter — NEW field, backfilled).
- [ ] **`TODO.md` status rows gain a `<!-- derived -->` zone** per row;
      `derive-docs` fills it; hand-prose stays in the leading cell.
- [ ] **`scripts/check-doc-drift` extension** — fails CI when a derived
      zone is stale (hashes source → compares to rendered).
- [ ] **`vision_goals:` frontmatter** added to every spec (backfill
      script reads the existing alignment matrix as the seed).
- [ ] **SkillDoc bodies re-derive** (Spec 080/081) on the same run —
      no SkillDoc literal that duplicates a docstring.
- [ ] Test: mutate a verb name, run `derive-docs`, assert the TODO row
      + SkillDoc both update; assert `check-doc-drift` was red before.
- [ ] TODO row + drift clean.

## Interconnects

- Anchors the **drift-derivation chain** the charter declares.
- Spec 146 (output-prefix) consumes `prefix_stability` as a derived
  field in `agency_doctor`.
- Spec 150 (dogfood classifier) emits amendment proposals as derived
  TODO-row deltas this script renders.
- Spec 148 (slash family) generates per-skill commands from the same
  derivation pass.
- Spec 080/081 SkillDoc derive is the precedent this generalizes.

## Open questions

1. Run `derive-docs` in a pre-commit hook or only in CI? **Recommend**:
   CI gate (`check-doc-drift`) + an opt-in `scripts/derive-docs --write`
   for local use — matches the existing check-drift / --update split.
