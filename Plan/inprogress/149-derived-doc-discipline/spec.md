---
spec_id: "149"
slug: derived-doc-discipline
status: partial
state: inprogress
last_updated: 2026-06-11
owner: "@agency"
enhances: "054"
depends_on: ["054", "080", "081", "146", "150"]
vision_goals: [7, 6, 4]
affects:
  - scripts/check_vision_goals.py
  - scripts/__init__.py
  - scripts/derive_docs.py
  - Plan/_planning/vision-goals-baseline.txt
  - .github/workflows/test.yml
  - tests/acceptance/features/derive_docs.feature
  - tests/acceptance/test_derive_docs.py
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

## Followup — Implementation Status (Slice 1, 2026-06-11)

**Shipped (this PR):**
- `scripts/check_vision_goals.py` — Vision-goals frontmatter validator.
  Parses YAML frontmatter, asserts `vision_goals` is a non-empty list
  of unique integers in `{1..8}` (per `docs/vision/GOALS.md`). Pure
  functions (`parse_frontmatter`, `check_spec`, `check_tree`) +
  `GoalsCheck.run()` returning a typed `CheckReport`.
- `Plan/_planning/vision-goals-baseline.txt` — 129 existing specs that
  lack `vision_goals:` (the historical gap). Spec 054 drift-management
  pattern: tracked, not blocked. A baseline entry whose spec gains
  `vision_goals:` is surfaced as `baseline_shrinkable` so the author
  trims the baseline (closing the loop).
- `.github/workflows/test.yml` — `Vision-goals frontmatter` step now
  gates CI: a NEW spec (one not in the baseline) without
  `vision_goals: [int, ...]` fails the build. Existing 129 baseline
  specs are exempt until backfill.
- `scripts/__init__.py` — `scripts/` is now an importable package so
  its functions are testable without subprocessing the CLI.
- `PyYAML>=6.0` declared in dev deps (previously transitive via
  `jsonschema-path`).
- 18 spec tests + 1 live-tree regression test green.

## Followup — Implementation Status (Slice 2.1, 2026-06-11)

### Done — Slice 2.1 (core derivation library + CLI)

- **`scripts/derive_docs.py`** ships the pure derivation engine:
  - `parse_affects(spec_path)` — reads `affects:` from frontmatter
    (handles missing field, malformed YAML, non-string entries).
  - `parse_collect_output(text)` — `pytest --collect-only -q` output →
    `{test_file: count}` map; handles parametrized `[case-id]`
    suffixes; ignores summary lines + blank input.
  - `derive_test_counts(affects, counts)` — sums the affects-file
    counts; missing files contribute 0 (rule 8 relationship invariant).
  - `derive_spec(spec_path, counts)` → typed `Derivation(spec_id,
    test_count, affects_files)`.
  - `derive_tree(plan_root, counts)` → `DeriveReport(derivations)`
    deterministically sorted by spec_id.
- **CLI**: `python -m scripts.derive_docs [--plan-root Plan]`
  invokes `pytest --collect-only -q` against the live repo, derives
  every spec, prints the top-20 by test_count. Live tree today:
  **262 specs walked, 1745 tests counted**, Spec 094 tops at 86
  tests; Slice 1 specs (152, 154) carry 60 + 31.
- **16 tests** in `tests/test_derive_docs.py` cover affects parsing,
  collect-output parsing (incl. parametrize + empty + summary
  filtering), test-count derivation, per-spec Derivation shape,
  tree-wide rollup determinism, and a live-tree smoke test.
- Pattern matches Spec 149 Slice 1 (`scripts/check_vision_goals.py`)
  — pure functions importable as `scripts.derive_docs`, frozen
  dataclasses, deterministic sort.

### Done — Slice 2.2 (fence rewrite acceptance tests, 2026-06-20)

The fence rewrite code (`find_fence`, `rewrite_fence`,
`render_fence_content`, `apply_derivations_to_spec_text`) was already
implemented in Slice 2.1 but had no tests. Slice 2.2 closes that gap:

- **5 acceptance scenarios** in `tests/acceptance/features/derive_docs.feature`
  + `tests/acceptance/test_derive_docs.py`:
  1. Test-count fence is filled from the affects-file count (fence content
     shows "**7**"; hand prose outside unchanged).
  2. Applying derivations twice is idempotent (second pass yields no diff).
  3. An unclosed fence raises ValueError mentioning "unclosed fence".
  4. A spec with no fences is left byte-identical (no spurious writes).
  5. Live tree dry-run (`python -m scripts.derive_docs`) completes without
     error and reports at least one spec (smoke test).
- `affects:` updated to point at the new acceptance test files (replaces
  the planned-but-absent `tests/test_derive_docs.py`).
- All 5 scenarios pass; drift clean.

### Done — Slice 2.3 (derived-zone drift CI gate, 2026-06-20)

- **`spec_has_drift(text, derivation) → str | None`** — pure function: returns
  a unified-diff hint when the spec text's derived zones diverge from the
  live derivation; None when all derived zones are up-to-date or the spec
  declares no fences (opt-in model). Raises ValueError on unclosed fences.
- **`check_derivation_drift(plan_root, counts) → [(path, hint)]`** — walks
  `Plan/*/spec.md`, calls `spec_has_drift` for each, returns a list of
  `(spec_path, diff_hint)` for stale specs.
- **CLI `--check` flag** — exits 1 with a compact diff hint when any spec
  has stale derived zones; exits 0 when all are up to date (or no spec
  declares fences). Exit 0 = clean; exit 1 = stale.
- **CI step `Derived-zone drift`** added to `.github/workflows/test.yml` —
  runs `python -m scripts.derive_docs --check --plan-root Plan` on every
  push + PR. Zero regressions on the live tree (no specs currently declare
  `test-count` fences).
- **4 new acceptance scenarios** in `tests/acceptance/features/derive_docs.feature`
  + `tests/acceptance/test_derive_docs.py`:
  1. Stale fence (count 42 vs live 7) → drift detected, non-empty diff hint.
  2. Up-to-date fence (count 7 vs live 7) → no drift.
  3. Spec without fences → no drift (opt-in model).
  4. Live repo `--check` → exits 0 (smoke test).

### Done — Slice 2.4 (typed Codes, 2026-06-20)

- **`DeriveError(ValueError)`** in `scripts/derive_docs.py`: typed exception
  with a `code` attribute. Subclasses `ValueError` for backwards-compatible
  `except ValueError` sites.
- **`Codes.DERIVE_FENCE_BROKEN`** (`"derive_fence_broken"`) added to
  `agency/toolresult.py`; `find_fence()` now raises `DeriveError` instead of
  raw `ValueError`.
- **`Codes.DERIVE_AMBIGUOUS`** (`"derive_ambiguous"`) and
  **`Codes.DERIVE_MISSING_GOAL`** (`"derive_missing_goal"`) added to `Codes`
  — wired in future slices (two-specs-claim-same-verb path + missing-frontmatter
  path).
- **Acceptance scenario** updated: "an unclosed fence raises DeriveError with
  DERIVE_FENCE_BROKEN code" — asserts `isinstance(err, DeriveError)` and
  `err.code == Codes.DERIVE_FENCE_BROKEN`.

### Still — Slices 2.5+

- **Slice 2.5** — alignment-matrix Goal column from `vision_goals:` frontmatter.
- **Slice 2.6** — backfill `vision_goals:` on the 129 baseline specs.
- **Slice 2.7** — Followup-status derive (Spec 269).

### Done — Slice 2.2 (HTML-comment fence rewrite, 2026-06-12)

- **`find_fence(text, fence_id) → (inner_start, inner_end) | None`**:
  locates the FIRST `<!-- derived:<id> -->` … `<!-- /derived:<id> -->`
  fence. Returns None when the opening marker is absent; raises
  ValueError when opened-but-unclosed (Slice 2.4 promotes to
  `Codes.DERIVE_FENCE_BROKEN`).
- **`rewrite_fence(text, fence_id, new_content) → str`**: replaces ONLY
  the content between markers; hand-prose outside the fence is byte-
  preserved. Idempotent: `rewrite_fence(rewrite_fence(t, id, x), id, x)
  == rewrite_fence(t, id, x)`.
- **`render_fence_content(fence_id, derivation) → str`**: canonical
  content for a known fence kind. Slice 2.2 ships ONE kind: `test-count`
  (renders test count + affects list). Future slices add more kinds.
- **`apply_derivations_to_spec_text(text, derivation) → str`**: walks
  every known fence kind, rewrites the ones the spec opts into. Unknown
  fence ids in the source are left alone.
- **CLI `--write`**: iterates `Plan/*/spec.md`, applies the derivations
  to specs that DECLARE fences, writes them back. Specs without fences
  are no-op (opt-in).
- **8 new tests** in `tests/test_derive_docs.py` (29 total green): find /
  not-found / rewrite / idempotent / no-marker / multiple-ids / unclosed
  raises / render_test_count / apply round-trip.

> ⚠ **Drift note (reconciled 2026-06-20):** `tests/test_derive_docs.py`
> (the 29 unit tests above) was DELETED in commit `c6bebbb` (phase-c
> flat-test→Gherkin migration, "delete the 193 superseded flat tests")
> and was NOT replaced with an acceptance scenario. `scripts/derive_docs.py`
> Slice 2.1/2.2 code is still present and importable, but is currently
> **untested in-tree**. Slice 2.3 should restore coverage as a Gherkin
> acceptance scenario (rule 7) alongside the `check-doc-drift` CI gate.

### Still — Slice 2.3+

- **Slice 2.3 — `check-doc-drift` extension**: fail CI when a derived
  zone diverges from `derive_docs --dry-run` output (Spec 058
  WARN→error doctrine).
- **Slice 2.4 — typed Codes**: `DERIVE_AMBIGUOUS` (two specs claim
  the same verb), `DERIVE_MISSING_GOAL` (frontmatter gap),
  `DERIVE_FENCE_BROKEN` (malformed derived zone). Per Spec 151
  invariant b.
- **Slice 2.5 — alignment-matrix Goal column**: derive from each
  spec's `vision_goals:` (Slice 1 frontmatter); render the matrix.
- **Slice 2.6 — Backfill the 129 baseline** specs with
  `vision_goals:` derived from `docs/vision/SPEC-VISION-ALIGNMENT.md`
  + author judgement; each baseline shrink lands in its own commit.
- **Slice 2.7 — Followup status derive** (Spec 269): for shipped
  specs, render the `### Done` / `### Still` blocks from a derived
  source.

**Still (older Slice 2+ items, preserved):**
- HTML-comment fenced derived zones (`<!-- derived:<id> -->` …
  `<!-- /derived:<id> -->`) — convention to be added once the
  deriver knows what to write.
- `check-doc-drift` extension that diffs rendered vs source.

**Open Q resolutions:** Q1 — CI-gate doctrine (Spec 054 drift pattern)
landed exactly as Recommended; pre-commit hook deferred.
