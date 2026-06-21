---
spec_id: "155"
slug: automated-red-team-rerunner
status: draft
state: inprogress
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
      and asserts each still holds against the LIVE registry. Returns a
      typed `RedTeamReport{invariants_checked: int, invariants_held: int,
      new_caps_attacked: list[str], reflections_emitted: list[NodeId],
      duration_s: float}`.
- [ ] **`thinking.red_team` chained** — for each NEW capability since
      the last run (derived from graph diff, not a hand list), generate
      candidate attack prompts via the Spec 147 Driver and record them
      as `Reflection(scope="red-team")` for human triage.
- [ ] **CI job** (Spec 053 workflow) runs the invariant sweep on every
      PR; the LLM-attack-generation step is tag-gated (needs the
      `[anthropic]` extra).
- [ ] **Measurable invariants** (rule 8):
      (a) `invariants_held == invariants_checked` on `main` (CI gate);
      (b) `set(capabilities_attacked) ⊇ set(capabilities_added_since_
      last_run)` — every NEW cap touched by at least one scenario;
      (c) red-team-reflection count is monotone non-decreasing over time
      (history persists in the graph, not in the repo);
      (d) zero `Reflection(scope="red-team", severity="exploit")` open
      on `main` — exploits gate the merge, candidates surface only.
- [ ] Test: a deliberately-broken invariant fixture trips the re-runner.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  capability `analyze` ships a new verb since last red-team run
When:   scripts/red-team-rerun executes against the live registry
Then:   RedTeamReport.new_caps_attacked includes "analyze";
        thinking.red_team generates ≥ 1 attack prompt for the new verb;
        each prompt records a Reflection(scope="red-team", severity=
        "candidate"); CI passes (candidates surface, don't block)

Given:  the clock-seed monotonicity invariant is deliberately broken in a fixture
When:   the invariant sweep runs
Then:   RedTeamReport.invariants_held < invariants_checked;
        CI fails with Codes.RED_TEAM_INVARIANT_BROKEN naming the scenario
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| LLM attack-prompt false positive | Driver invents non-exploit "attack" | severity classification + invariant (d) | candidates surface, only `exploit`-tagged Reflections block; human triages |
| Driver unavailable in CI | `[anthropic]` extra not installed | tag-gated job — skipped not failed | DRY invariant sweep still runs as the default gate |
| Stale baseline | "new cap" diff drifts vs. graph reality | derive baseline from graph timestamp, not file mtime | invariant (b) over the live graph |
| Reflection flood | every PR generates dozens of candidates | dedupe by (cap, scenario_kind) hash; cap per-run | bounded budget; oldest unresolved candidates auto-archive |

## Interconnects

- **Dogfood-loop chain** (150): red-team Reflections feed
  `dogfood.parse_amendment` as a proposal source.
- **LLM-driver chain** (147): attack-prompt generation runs through it.
- Spec 011 (`_pressure`) is the scenario substrate.
- Spec 156 (wet pressure path) is the sibling wet-execution of the
  same scenario substrate — red-team rerun loads, wet-pressure scores.
- Spec 151 (Codes coverage) supplies `Codes.RED_TEAM_INVARIANT_BROKEN`.
- Spec 157 (architecture-drift gate) hosts the standing CI presence —
  red-team is one of its standing invariants.

## Open questions

1. Block merge on a new red-team finding, or surface-only?
   **Recommend**: surface-only for LLM-generated candidates (high false-
   positive); the DECIDABLE invariant sweep blocks.
2. Re-run cadence — every PR, nightly, or on capability add?
   **Recommend**: invariant sweep every PR (cheap, DRY); LLM-attack
   generation on capability-add + nightly (costs tokens).

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion` as part of
the wave-1 typed-shape batch-2 (intent:2219e694; engine-driven tdd walk).

### Done — Slice 1 (typed shape)

Typed frozen dataclass + `__post_init__` invariants in
`agency/_typed_shapes_wave1_part2.py`; tests in
`tests/test_typed_shapes_wave1_part2.py` (17 tests total across the
8-spec batch). Slice 2 wires each shape into its consuming runtime
(red-team rerunner, CLI projection, derive audit, wrapper modules,
networkx metric, axis registry, migration walker, ref audit).

### Still — Slice 2+

See the spec's main "Done When" + "Still" sections.

