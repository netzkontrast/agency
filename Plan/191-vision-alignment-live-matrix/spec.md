---
spec_id: "191"
slug: vision-alignment-live-matrix
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "072"
depends_on: ["072", "149", "182", "084"]
vision_goals: [6, 4]
affects:
  - docs/vision/SPEC-VISION-ALIGNMENT.md
  - scripts/derive-docs
  - tests/test_vision_matrix_derived.py
---

# Spec 191 — live vision-alignment matrix

## Why

Spec 072 (core-vision-alignment) produced the doctrine + the
SPEC-VISION-ALIGNMENT.md matrix — but the matrix is HAND-MAINTAINED and
"Last reviewed 2026-06-03", already stale. With `vision_goals:`
frontmatter on every spec (Spec 149) and the derived-doc engine, the
matrix should regenerate from source: each spec's Goal mapping comes
from its frontmatter, each Goal's status comes from its specs'
shipped/draft state. The matrix becomes a derived view, never stale.

## Done When

- [ ] **`scripts/derive-docs` regenerates the matrix** from every
      spec's `vision_goals:` frontmatter + live status (Spec 149).
- [ ] **Each Goal's status (✅/⚠️/🔴) is computed** from the
      shipped-fraction of its specs, not hand-asserted.
- [ ] **The "three biggest GAPS" section is derived** — the Goals with
      the lowest shipped-fraction.
- [ ] **`check-doc-drift` gates the matrix** against the frontmatter.
- [ ] Test: flip a spec's status → the matrix Goal status recomputes;
      drift catches a stale matrix.
- [ ] TODO row + drift clean.

## Interconnects

- **Drift-derivation chain** (149): the matrix is the flagship derived
  doc.
- Spec 182 (cluster audit) + Spec 084 (graph census) supply inputs.

## Open questions

1. Keep the prose gap analysis or fully derive? **Recommend**: derive
   the table + Goal status; keep a short hand-written "why this gap
   matters" note per 🔴 Goal (judgement the script can't write).
