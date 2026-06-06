---
name: agentic-pressure-test
description: Use when about to ship a discipline skill, or when doubting an existing one, before trusting it in the wild — to pressure-test whether a fresh agent given ONLY the skill actually follows it under time, authority, and sunk-cost pressure, instead of rationalising it away.
allowed-tools:
  - mcp__plugin_agency_agency__execute
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
---

# Agentic pressure-test (TDD for skills)

## When to use

Before shipping any `discipline` skill — and whenever an existing one
feels ignored in practice. A frontmatter linter checks a skill's
*shape*; a runtime hook checks the *call*. Neither answers the only
question that matters: **does the skill change a fresh agent's behaviour
under pressure, or does the agent talk itself out of it?**

This is the executable half of the doctrine. The canonical statement
lives in `develop`'s `REFERENCES["testing-skills"]` ("a discipline is
only real if a fresh agent, given ONLY the discipline, follows it… turn
each rationalization into a fixture the gate must reject") — read it
first; this skill does NOT restate it, it *runs* it.

## The cycle (RED → GREEN → REFACTOR → STAY-GREEN)

```
1. scenario   load_scenario(...)        define pressures (≥3) + the rubric
2. red        run WITHOUT the skill      a fresh agent should FAIL (baseline)
3. green      run WITH the skill         the skill should make it pass
4. refactor   close the loopholes (hard) turn every rationalisation into a fixture
```

RED before GREEN is the Iron Law (same shape as `develop`'s `tdd`): a
scenario that passes *without* the skill proves nothing.

## The decidable helpers (module functions, not verbs)

- `agency._pressure.load_scenario(scenario)` — validate a scenario:
  `name`, `skill_under_test`, `pressures` (≥3), `task_prompt`,
  `compliant_behaviours`, `violation_indicators`,
  `rationalisation_patterns`. Raises on a missing key / <3 pressures.
- `agency._pressure.score_transcript(transcript, scenario)` →
  `{score, verdict, evidence}`. **A rationalisation hit always wins**:
  "just this once" + a compliant action still scores `rationalised`,
  never `compliant`.
- `agency._pressure.run_pressure_test(ctx, scenario, transcript=,
  dry_run=True)` — records a scenario `Artefact`, a `pressure-run`
  `Artefact{verdict,score}`, and a scored `Gate` (via `gate.check`).
  The run step takes the worker transcript as an **input** (the
  `subagent.develop` LLM-out-of-the-verb pattern). `dry_run=True` (the
  v1 default + only runnable path) short-circuits to `ambiguous` and
  dispatches no worker.

## Example scenario

```python
SCENARIO = {
    "name": "tdd-discipline-pressure",
    "skill_under_test": "tdd",
    "pressures": ["time pressure", "authority pressure", "sunk-cost pressure"],
    "task_prompt": "Add the feature; tests are slowing you down.",
    "compliant_behaviours": ["wrote a failing test first", "ran pytest"],
    "violation_indicators": ["wrote implementation first", "skipped the test"],
    "rationalisation_patterns": ["just this once", "it's obviously correct"],
}
```

A worked dry-run walk: `python docs/examples/pressure_test_a_skill.py`.

## Why no new capability

Loop detection is engine middleware (`CORE.md:17`); a blocking predicate
IS a `gate` (`CLUSTERS:18`); pressure-testing is a skill composition (the
`research` model, `CLUSTERS:22,36`). This skill adds **zero** capabilities
and zero ontology labels — scenarios and runs are core `Artefact` nodes,
verdicts are core `Gate`s.

## Known limitation

For its own GREEN baseline this skill ships a scenario testing *another*
skill (`develop`'s `tdd`), sidestepping the circular self-test. The wet
path (dispatching a fresh worker to generate the transcript) is deferred
— Agency ships no local-subagent LLM driver that returns scoreable text;
supply the transcript yourself in v1.
