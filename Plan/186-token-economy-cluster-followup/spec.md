---
spec_id: "186"
slug: token-economy-cluster-followup
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "066"
depends_on: ["066", "146", "187", "149"]
vision_goals: [1]
affects:
  - Plan/066-token-economy-cluster/spec.md
  - tests/test_token_economy_goal.py
---

# Spec 186 — token-economy cluster, output-side charter

## Why

Spec 066 is the token-economy cluster master — a "lint-first program to
make the system cheaper to read/write/discover". Its goal→lint-rule map
covers NAMES and DISCOVERY (067/068) but stops at the input/discovery
boundary. The enhancement charter's gap #1 (output-side token economy)
is the missing half: the master should be extended with the output-side
goal→lint-rule map (response-prefix stability, overflow capture, field
projection) so the cluster's charter is complete end to end.

## Done When

- [ ] **Spec 066 master gains an output-side section** mapping the
      output-economy goals to their lint rules: prefix-stability (146),
      overflow-capture (154), `--fields` projection (160).
- [ ] **The cluster's "GOAL MET" verdict is re-derived** to include the
      output side (Spec 149) — not re-pinned.
- [ ] **One goal-test** asserts the output-economy invariants hold on
      the live registry (`wire_tok` relationships, not magic numbers —
      rule 8).
- [ ] TODO row + drift clean.

## Interconnects

- **Output-budget chain** (146/154/160): this is their cluster charter.
- Spec 187 (output-side lint rules) is the executable companion.

## Open questions

1. Re-open the cluster intent or a new one? **Recommend**: extend the
   existing `intent:97534079` (same goal, now whole) — supersede the
   "GOAL MET" verdict with "GOAL MET (input+output)".
