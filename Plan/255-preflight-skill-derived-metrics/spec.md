---
spec_id: "255"
slug: preflight-skill-derived-metrics
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "145"
depends_on: ["145", "149", "150", "170"]
vision_goals: [6, 4]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_preflight_metrics.py
---

# Spec 255 — preflight: derived metrics + dogfood-fed warnings

## Why

Spec 145 ships `novel-preflight` (5-phase read-only audit, <200ms on
40-chapter graph). Its `verdicts` payload is hand-shaped; over time
recurring `warnings` reveal drift patterns. Per Spec 149 the verdict
structure should derive from the audit verbs (any new audit
auto-appears). Per Spec 150 recurring warnings become amendment
proposals.

## Done When

- [ ] **Verdict structure derived from registered audit verbs** —
      adding a 6th preflight phase auto-extends the verdicts dict.
- [ ] **Recurring warnings (≥ N occurrences across scenes) feed Spec
      150** as amendment proposals.
- [ ] **`agency_doctor` reports preflight readiness** (Spec 170) — is
      every phase wired for this novel?
- [ ] **<200ms guarantee preserved** (graph-only, no LLM in the loop).
- [ ] Test: a 6th phase auto-extends; 3× warning becomes a proposal.
- [ ] TODO row + drift clean.

## Interconnects

- **Drift-derivation chain** (149) · **Dogfood-loop** (150) · Spec 170.
- Spec 145 is the parent.
