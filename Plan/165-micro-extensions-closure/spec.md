---
spec_id: "165"
slug: micro-extensions-closure
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "046"
depends_on: ["046", "081", "079", "149"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/branch/_main.py
  - agency/capabilities/develop/_main.py
  - tests/test_micro_extensions_closure.py
---

# Spec 165 — Micro-extensions closure

## Why

Spec 046 (micro-extensions-bundle) is Partial — F-C (`branch.commit_smart`)
+ F-D (`develop.estimate`) shipped, but "F-A/B/E/F (skill content +
scripts) superseded/deferred under the derive model". Rather than leave
them dangling, this spec resolves each deferred fragment explicitly:
either derive it (080/081) or formally cancel it with a pointer, so the
046 row reads clean.

## Done When

- [ ] **Each deferred fragment (F-A/B/E/F) gets an explicit verdict** —
      derived under 080/081, folded into the 079 CLI mirror, or
      cancelled-with-pointer (no silent dangling).
- [ ] **`branch.commit_smart` + `develop.estimate` gain derived
      SkillDocs** (close the derive-model gap).
- [ ] **046 TODO row flips to Shipped or Closed** once every fragment
      has a verdict (derived status, Spec 149).
- [ ] Test: every 046 fragment resolves to a live verb, a CLI command,
      or a cancellation record.
- [ ] TODO row + drift clean.

## Interconnects

- **Drift-derivation chain** (149).
- Spec 079 (CLI mirror) + Spec 081 (walkable skills) are the
  resolution surfaces.

## Open questions

1. Cancel or implement F-E/F? **Recommend**: decide per fragment from
   the live graph (is anything calling for it?); default cancel-with-
   pointer absent a consumer.
