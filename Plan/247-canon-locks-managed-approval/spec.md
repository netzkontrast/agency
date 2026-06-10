---
spec_id: "247"
slug: canon-locks-managed-approval
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "137"
depends_on: ["137", "150", "147", "176"]
vision_goals: [2, 6]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_canon_locks_approval.py
---

# Spec 247 — canon locks: approval workflow + dogfood pipe

## Why

Spec 137 ships CANON_STATUS + Lock + the source-hierarchy + canon-gate.
Today `set_canon_status` and `record_lock` are one-call writes. Real
projects need an APPROVAL workflow (propose → review → canon) that
mirrors the [V]→[K] discipline. With Spec 176 SessionStart capture +
Spec 150 dogfood loop, approval requests become tracked Intents that
classify into amendment proposals if approved → applied.

## Done When

- [ ] **`propose_canon(...)`** + **`approve_canon(lock_id)`** workflow —
      a proposal is `proposal` until approved; approval mints the [K] Lock.
- [ ] **Approval requests as captured Intents** (Spec 176) — provenance
      of who-decided-what.
- [ ] **Amendments via Spec 150** when patterns recur.
- [ ] Test: full propose→approve→canon flow on a fixture.
- [ ] TODO row + drift clean.

## Interconnects

- **Dogfood-loop chain** (150) · Spec 176 (intent capture).
- Spec 137 is the substrate.
