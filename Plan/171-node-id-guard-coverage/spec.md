---
spec_id: "171"
slug: node-id-guard-coverage
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "056"
depends_on: ["056", "058", "149", "151"]
vision_goals: [4, 2]
affects:
  - agency/_lints/_node_id_guards.py
  - tests/test_node_id_guard_coverage.py
---

# Spec 171 — node-id guard coverage promotion

## Why

Spec 056 ships `Memory.recall_typed` + a WARN-only `_check_node_id_guards`
lint and migrated the research/intent/document guards. But it stays
WARN-only — a new verb that takes a `node_id` and skips the label check
ships silently. Like Spec 058's reflection-link lint, this should
become a coverage discipline: every node-id parameter is guarded, and
the lint promotes to error once the live registry is clean.

## Done When

- [ ] **Full sweep** — every verb taking a `*_id` param that hits the
      graph routes through `recall_typed` (migration audit, derived).
- [ ] **Lint promotes WARN → error** once the live registry reports
      zero gaps (Spec 056/058 promotion pattern).
- [ ] **`agency_doctor` reports `node_id_guard_coverage`** (derived).
- [ ] Test: an unguarded node-id param trips the (now-error) lint;
      live registry clean.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 058 (reflection-link) is the promotion-pattern sibling.
- Spec 151 (codes coverage) is the parallel coverage discipline.
- **Drift-derivation chain** (149).

## Open questions

1. Promote now or after one WARN cycle? **Recommend**: after the sweep
   confirms zero gaps — never flip a lint to error with known violations.
