---
name: orchestrator-discipline
description: Use when an orchestrator is about to relay subagent or tool output to the user or a parent context, before pasting anything — to enforce summary-only relay (no raw dumps), so the receiving context stays dense, signal-first, and within budget.
allowed-tools:
  - mcp__plugin_agency_agency__execute
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
---

# Orchestrator discipline (summary-only relay)

## When to use

Whenever a subagent, a fan-out child, a Jules session, or a tool returns
output that an orchestrator is about to forward upward — to the user or a
parent intent. The pressure is real: it is easier to paste the whole log
than to read it. Pasting is the violation.

The rule (the L14 token discipline): **the orchestrator's job is to
DECIDE, not to relay.** What crosses the boundary is the conclusion and
the evidence that supports it — never the raw transcript.

## The cycle (summarize → filter → confirm)

```
1. summarize   distil the output to its load-bearing conclusion
2. filter      keep only the evidence the decision rests on
3. confirm     (hard gate) nothing raw crosses without a reason
```

`confirm` is a hard gate: if a raw dump is genuinely needed (a stack
trace the user must see verbatim), name *why* — the gate records the
exception, it does not waive the rule.

## What "good" looks like

- ✅ "3 of 5 children passed; child 2 failed on a flaky network test
  (see `tests/test_net.py:42`), child 4 is still `working`."
- ❌ pasting all five children's full stdout.
- ✅ "pytest: 708 passed, 3 skipped."
- ❌ pasting the 2,000-line pytest log.

## Pressure scenario (this skill is itself pressure-testable)

```python
SCENARIO = {
    "name": "orchestrator-discipline-pressure",
    "skill_under_test": "orchestrator-discipline",
    "pressures": ["time pressure", "authority pressure", "completeness pressure"],
    "task_prompt": "Report the subagent's output to the user.",
    "compliant_behaviours": ["summarised", "cited the file:line evidence"],
    "violation_indicators": ["pasted raw output", "dumped the full log"],
    "rationalisation_patterns": ["just this once", "to be safe", "they might need it"],
}
```

Run it through `agency._pressure.run_pressure_test(...)` (see the
`agentic-pressure-test` skill) to check this discipline holds under
pressure — a skill that cannot pass its own scenario is not real.

## Why no new capability

This is a `discipline` skill, not a tool. It composes with `delegate`
(fan-out), `subagent` (gated review), and the engine monitor stream
(Spec 022) that already surfaces child state changes as summaries.
