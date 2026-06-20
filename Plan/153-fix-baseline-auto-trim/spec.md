---
spec_id: "1535"
slug: fix-baseline-auto-trim
status: drafted
owner: "@agency"
depends_on: ["153-template-schema-coverage-closure"]
affects:
  - scripts/check_schema_coverage.py
domain: core
wave: 2
---

# Spec 153 Slice 5 — deferred-tag gate (`--fix-baseline` auto-trim)

## Why

The baseline file (`Plan/_planning/schema-coverage-baseline.txt`) is manually trimmed when labels graduate from uncovered → covered. Slice 5 automates: `check_schema_coverage --strict --baseline` already flags `fixed_uncovered`, but there's no CI auto-trim. Add a `--fix-baseline` flag that rewrites the baseline in-place (remove fixed, warn on new). This eliminates the manual "trim 5 entries each batch" step.

## Done When

- [ ] `scripts/check_schema_coverage.py` accepts `--fix-baseline`.
- [ ] When `--fix-baseline` is provided alongside `--baseline <path>`:
  - If `fixed_uncovered` is not empty, the labels are removed from the baseline file. The file is rewritten in place, preserving existing comments and empty lines where possible.
  - If `new_uncovered` is not empty, a warning is printed to stdout.
  - The script exits 0 if there are no new uncovered labels, or 1 if there are new uncovered labels.
- [ ] No changes to the `agency` core module (only the CLI shim is affected).
- [ ] `scripts/check-drift` passes.
- [ ] `pytest tests/` passes.

## Evidence

- `scripts/check_schema_coverage.py --baseline Plan/_planning/schema-coverage-baseline.txt --fix-baseline` modifies the file when there are fixed schemas.
- `git diff` shows the expected file modifications.

## Self-Review

- [ ] Pre-commit instructions followed.
- [ ] Does not modify `agency/_schema_coverage.py`.
