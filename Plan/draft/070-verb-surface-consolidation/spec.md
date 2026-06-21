---
spec_id: "070"
slug: verb-surface-consolidation
status: draft
state: draft
last_updated: 2026-06-06
owner: "@agency"
serves_intent: "intent:97534079"
parent: "066"
fulfils: "CORE.md §Skills — progressive disclosure / surface_size"
depends_on: ["067", "068"]
affects:
  - agency/capabilities/jules/             # the heaviest surface (22 verbs)
  - tests/test_verb_consolidation.py        # NEW
estimated_jules_sessions: 0
domain: meta
wave: 5
---

# Spec 070 — Verb-surface consolidation (audit + collapse)

## Why

Readability and token cost both scale with verb count: 69 verbs across 14
capabilities, with `jules` carrying 22. Spec 067's `surface_size` rule flags
capabilities over the budget. This spec is the **audit-then-implement** pass (the
049 model) that collapses genuine near-duplicates behind one verb + a param —
fewer things to discover, read, document, and lint.

## Done When

- [ ] **Audit** every capability's verbs for near-duplicates; record the verdict
  per verb (KEEP / MERGE-INTO / SPLIT-CAP) as a report (the 049 model). Candidate
  merges to evaluate (NOT pre-decided): `jules.status`/`status_all`,
  `jules.patch`/`patch_body`/`apply_patch`, `reflect.note`/`batch_note`.
- [ ] **Collapse** the approved merges behind one verb + a discriminating param,
  alias-and-deprecate the old verb names.
- [ ] Each touched capability drops to/below the Spec 067 `surface_size` budget OR
  carries an explicit justification; flip `surface_size` to BLOCK where clean.
- [ ] `tests/test_verb_consolidation.py`: merged verb covers both old behaviours;
  deprecated aliases still resolve; provenance (SERVES) unchanged.
- [ ] `pytest -n auto -m "not e2e"` green; `check-drift` clean.

## Migration

Alias-and-deprecate per collapsed verb (old name → new verb+param for one minor).
No behaviour lost — the merge is a superset.

## Evidence

- `Plan/049-…/naming-audit-report.md` §1 (the 69-verb / per-cap counts).
- `CORE.md` §Skills (progressive disclosure); Spec 067 `surface_size`.

## Followup — Implementation Status (2026-06-12)

**Verdict:** Drafted (backlog / WARN-accepted / cluster-master). Tracked
in TODO.md's Verdicts row; no Slice 1 commitment beyond the spec body.
For the autonomous-completion goal stop condition (2), this spec is
classified as drafted-by-doctrine, not pending-implementation.

