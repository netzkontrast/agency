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

- [ ] **`scripts/derive-docs` regenerates from live sources** —
      idempotent; outputs deterministic ordering:
      - **per-spec test counts** from `pytest --collect-only -q`
        keyed by `affects:` test files (count + collected node ids);
      - **per-spec verb lists** from the live registry, filtered by
        the capability the spec owns;
      - **alignment-matrix Goal column** from each spec's
        `vision_goals:` frontmatter (NEW field, backfilled);
      - **per-spec Followup status sections** (Spec 269) for shipped
        specs;
      - **slash-command family** (Spec 148 derive) from the live skill
        registry.
- [ ] **Derived zones use HTML-comment fences** —
      `<!-- derived:<section-id> -->` … `<!-- /derived:<section-id> -->`;
      `derive-docs` only writes between fences; hand-prose untouched.
- [ ] **`scripts/check-doc-drift` extension** — fails CI when a derived
      zone's rendered content does not match `derive-docs --dry-run`
      output (hashes source → compares to rendered). Exit 0 = clean;
      exit 1 = stale with a diff hint.
- [ ] **`vision_goals: [int, ...]` frontmatter required on every spec**
      — backfill script reads the existing alignment matrix as the
      seed; check-doc-drift fails when missing (Spec 158 pattern).
- [ ] **SkillDoc bodies re-derive** (Spec 080/081) on the same run —
      no SkillDoc literal that duplicates a docstring; the Spec 163
      derive engine is the SOURCE.
- [ ] **Acceptance invariants** (rule 8):
      - `derive-docs --dry-run` is idempotent (running twice yields
        zero diff)
      - reordering capabilities does not change the rendered output
        (stable sort)
      - a verb-rename PR has exactly one derived-doc commit produced by
        `derive-docs --write` (no hand-edit; lint enforces this)
- [ ] **Failure modes** — `derive-docs` rejects on (a) ambiguous source
      (two specs claim the same verb) with `Codes.DERIVE_AMBIGUOUS`;
      (b) missing frontmatter with `Codes.DERIVE_MISSING_GOAL`; (c) a
      derived zone where the fence is malformed with
      `Codes.DERIVE_FENCE_BROKEN`.
- [ ] Test: mutate a verb name → `derive-docs --write` produces a TODO
      row + SkillDoc update in one pass; `check-doc-drift` was red
      before, green after. A second `derive-docs --dry-run` returns
      empty diff (idempotence).
- [ ] **TODO row + drift clean.**

## Worked example (Given/When/Then)

```text
Given:  spec 042 ships verb `analyze.run_quality`; row shows count "33"
When:   a new test fixture for analyze adds 3 tests
Then:   derive-docs renders count "36" in row 042's derived zone
        AND check-doc-drift fails CI until the row updates

Given:  a new capability `<cap>` ships with zero existing tests
When:   derive-docs runs
Then:   per-spec verb list renders the new verbs
        AND a "no tests yet" warning surfaces in the row
        AND Spec 169 coverage gate fails

Given:  TWO specs claim verb X in their derivation source
When:   derive-docs runs
Then:   exits with Codes.DERIVE_AMBIGUOUS naming both specs;
        no partial write
```

## Interconnects

- Anchors the **drift-derivation chain** the charter declares.
- Spec 146 (output-prefix) consumes `prefix_stability` as a derived
  field in `agency_doctor`.
- Spec 150 (dogfood classifier) emits amendment proposals as derived
  TODO-row deltas this script renders.
- Spec 148 (slash family) generates per-skill commands from the same
  derivation pass.
- Spec 080/081 SkillDoc derive is the precedent this generalizes.
- Spec 191 (live vision matrix) is the matrix consumer.
- Spec 259 (derive-docs self-test) is the meta-coverage spec.
- Spec 269 (Followup status derived) is the per-spec consumer.
- Spec 151 (Codes coverage) supplies the failure-mode error codes.

## Open questions

1. **Run `derive-docs` in a pre-commit hook or only in CI?**
   **Recommend**: CI gate (`check-doc-drift`) + an opt-in
   `scripts/derive-docs --write` for local use — matches the existing
   check-drift / --update split.
2. **What if a derived zone's source rotates faster than CI?** (e.g.
   live test count differs across runners.) **Recommend**: stamp the
   source git-sha; the gate compares against the stamped version, not
   the live count.
3. **Backwards compatibility on existing TODO.md.** **Recommend**:
   backfill the fences in a single migration commit; subsequent
   commits gate strictly. A "transitional" mode (one cycle) WARN-only.
