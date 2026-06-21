---
spec_id: "186"
slug: token-economy-cluster-followup
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "066"
depends_on: ["066", "146", "187", "149"]
vision_goals: [1]
affects:
  - Plan/draft/066-token-economy-cluster/spec.md
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
      overflow-capture (154), `--fields` projection (160). The mapping
      is a typed `OutputEconomyRow{goal: str, lint_rule: str, spec_id: str,
      live_status: Literal["warn","error","derived"]}` table — derived,
      never hand-pinned.
- [ ] **The cluster's "GOAL MET" verdict is re-derived** to include the
      output side (Spec 149) — not re-pinned. The derivation reads the
      live status of each row and computes `verdict = "GOAL MET (input+
      output)" if all rows live, "PARTIAL" otherwise`.
- [ ] **One goal-test** asserts the output-economy invariants hold on
      the live registry: `cache_read_input_tokens > 0` after warmup,
      `overflow_count == 0 OR every overflow has a recall_handle`,
      `fields_projection_works on every CLI verb` (rule 8 relationships,
      not magic numbers).
- [ ] **Failure mode coverage**: the spec lists at least three ways the
      output side regresses (prefix interpolation, silent truncation,
      unprojectable shape) with the detecting lint named for each.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  spec 066 master before this enhancement (input/discovery rows only)
        AND specs 146, 154, 160 each shipped with their lint rule
When:   the derive-docs script regenerates the cluster charter
Then:   the charter renders an output-side section with rows for each of
        146/154/160, the verdict line reads "GOAL MET (input+output)"
        when all three lints are live, and the goal-test passes asserting
        cache_read_input_tokens > 0 on the second discovery call

Given:  Spec 154 ships overflow-capture but the lint is still WARN
When:   the cluster verdict re-derives
Then:   verdict reads "PARTIAL" and the row's live_status == "warn",
        no hand edit required
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Stale verdict | charter hand-edited after a lint flip | `check-doc-drift` compares verdict to live row status | regenerate via `derive-docs`; reject hand edits in CI |
| Hidden regression | a new verb ships without a row in the table | `OutputEconomyRow` count < cap-touching-output count | the lint enforces a row per output-side cap |
| Pinned counts creep back | someone writes "verdict requires ≥ 1503 cache tokens" | rule-8 lint flags magic numbers in the charter | the goal-test only asserts relationships |

## Interconnects

- **Output-budget chain** (146/154/160): this is their cluster charter.
- Spec 187 (output-side lint rules) is the executable companion.
- Spec 193 (capstone) is the end-to-end proof that consumes this charter.
- Spec 149 (derived docs) regenerates the charter; Spec 191 (vision matrix)
  reads the cluster verdict for the Goal-1 row.
- Spec 147 (AnthropicDriver) is the consumer whose cache behavior the
  invariants measure.

## Open questions

1. Re-open the cluster intent or a new one? **Recommend**: extend the
   existing `intent:97534079` (same goal, now whole) — supersede the
   "GOAL MET" verdict with "GOAL MET (input+output)".
2. Should the output-side section be its OWN cluster master? **Recommend**:
   no — the four-concept canon names ONE token economy goal; splitting
   it would fragment the verdict. Keep one master with input+output rows.
3. How is the live_status field populated? **Recommend**: read each
   lint's runtime state via `agency_doctor.lints[<rule>].level` —
   never hand-encode in the charter.
