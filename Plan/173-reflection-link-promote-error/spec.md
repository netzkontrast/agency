---
spec_id: "173"
slug: reflection-link-promote-error
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "058"
depends_on: ["058", "150", "159", "149"]
vision_goals: [2, 6]
affects:
  - agency/_lints/_reflection_links.py
  - tests/test_reflection_link_error.py
---

# Spec 173 — reflection-link lint promotion to error

## Why

Spec 058 ships a WARN-only `_check_reflection_links` lint (a Reflection
write must link BOTH SERVES + OBSERVED_DURING) and migrated the audit
sites. The dogfood-loop closure (Spec 150) makes Reflections
load-bearing — the amendment classifier reads them — so an unlinked
Reflection is now a silent provenance hole that breaks the loop. The
lint should promote to error.

## Done When

- [ ] **Full sweep** — every Reflection write links both edges
      (migration audit, derived).
- [ ] **Lint promotes WARN → error** once the live registry is clean.
- [ ] **Spec 150's classifier requires the OBSERVED_DURING edge** to
      attribute a proposal — the promotion guarantees it exists.
- [ ] **Spec 159's `note(auto_scope)` writes both edges.**
- [ ] Test: an unlinked Reflection trips the error lint; live registry
      clean; classifier attributes a proposal to its source.
- [ ] TODO row + drift clean.

## Interconnects

- **Dogfood-loop chain** (150/159): makes the loop's provenance whole.
- Spec 058 is the parent; Spec 171 the parallel promotion.
- **Drift-derivation chain** (149).

## Open questions

1. Promote before or after the sweep? **Recommend**: after — the
   non-negotiable promotion rule (zero known violations first).
