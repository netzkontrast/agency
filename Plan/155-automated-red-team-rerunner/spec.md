---
spec_id: "155"
slug: automated-red-team-rerunner
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "006"
depends_on: ["006", "011", "053", "147"]
vision_goals: [6, 3]
affects:
  - tests/test_hardening.py
  - agency/capabilities/thinking/_main.py
  - scripts/red-team-rerun
---

# Spec 155 — Automated red-team re-runner

## Why

Spec 006 (core-hardening) fixed four red-team findings with 9 tests —
but red-teaming was a ONE-TIME manual pass. Spec 011 ships
`_pressure.py` (load_scenario / score_transcript / run_pressure_test)
and Spec 110 ships `thinking.red_team`, yet nothing re-runs an
adversarial sweep over the engine's invariants on a cadence. The
hardening should be a STANDING gate, not a historical event — every new
capability is new attack surface (the enforcement-blast-radius
heuristic in CLAUDE.md).

## Done When

- [ ] **`scripts/red-team-rerun`** loads the documented invariants
      (clock-seed monotonicity, pagination exhaustion guard, fail-closed
      verify, api-key-never-captured) as pressure scenarios (Spec 011)
      and asserts each still holds against the LIVE registry.
- [ ] **`thinking.red_team` chained** — for each NEW capability since
      the last run (derived from graph), generate candidate attack
      prompts via the Spec 147 Driver and record them as
      `Reflection(scope="red-team")` for human triage.
- [ ] **CI job** (Spec 053 workflow) runs the invariant sweep on every
      PR; the LLM-attack-generation step is tag-gated (needs the
      `[anthropic]` extra).
- [ ] Test: a deliberately-broken invariant fixture trips the re-runner.
- [ ] TODO row + drift clean.

## Interconnects

- **Dogfood-loop chain** (150): red-team Reflections feed
  `dogfood.parse_amendment` as a proposal source.
- **LLM-driver chain** (147): attack-prompt generation runs through it.
- Spec 011 (`_pressure`) is the scenario substrate.

## Open questions

1. Block merge on a new red-team finding, or surface-only?
   **Recommend**: surface-only for LLM-generated candidates (high false-
   positive); the DECIDABLE invariant sweep blocks.
