---
name: delegate
description: "Use when a task might be better handled by a subagent (local, Jules, or another driver) and the choice to dispatch versus stay inline must be weighed, then work fanned out and the results joined."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# delegate capability

Delegate weighs the token-economics and safety signals of dispatching, fans a task out to one or more drivers, and reduces their results back into a single answer.

## When to use

- A task large or parallelizable enough to consider delegating
- Several independent sibling tasks that could run concurrently
- Uncertainty whether to dispatch a subagent or work inline

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `dispatch_bash_hints` | transform | Compose the bash-hint context block for a dispatch prompt. | [details](references/dispatch_bash_hints.md) |
| `dispatch_decision` | transform | Apply the dispatch-vs-inline heuristic and return a recommendation. | [details](references/dispatch_decision.md) |
| `fan_out` | effect | Open one child Lifecycle per item (capped at `quota`), dispatch the driver for each, and record a Delegation that DELEGATES_TO every child. | [details](references/fan_out.md) |
| `join` | act | Reduce a delegation over its children's Lifecycle state. | [details](references/join.md) |

## Example

```bash
await call_tool('capability_delegate_dispatch_bash_hints', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Dispatching without weighing the cost → check capability_delegate_dispatch_decision first
- Spawning siblings then losing their results → reduce with capability_delegate_join

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`dispatch-decision`** (discipline): estimate-tokens-and-cache → estimate-shape → apply-heuristic → assemble-bash-hints → decide
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'dispatch-decision', 'inputs': {}, 'intent_id': '…'})`
  1. **estimate-tokens-and-cache** — Estimate the token + cost-model signals (S1, S6–S11).
     Estimate the return-token size, whether the task mutates / is read-only, any driver hint, and the cache signals (context overlap, cache warmth, local-budget relevance). These feed the cost half of the heuristic.
  2. **estimate-shape** — Estimate the work-shape signals (S2–S5).
     Count the unfamiliar files, whether repeated exploration is needed, parallel siblings, and the inline wall-clock. These are the work-shape inputs.
  3. **apply-heuristic** — Apply the eleven-signal heuristic.
     Run the two disqualifiers FIRST, then score the signals → a recommendation + driver + rationale + which signals fired. Name the signals; don't hand-wave the call.
  4. **assemble-bash-hints** — Assemble bash hints for the chosen path.
     If dispatching, assemble the grep/sed/find hints the worker needs to find its way; leave empty when the call is inline.
  5. **decide** — Commit to inline vs dispatch.
     State the final decision (inline | dispatch) with its driver. Confirm this gate only when the rationale is grounded in the fired signals, not a hunch.
- **`dispatching-parallel-agents`** (discipline): partition → dispatch → join → synthesize
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'dispatching-parallel-agents', 'inputs': {}, 'intent_id': '…'})`
  1. **partition** — Split the work into independent domains.
     Identify 2+ NON-overlapping problem domains that can proceed without shared state. First confirm dispatch beats inline (walk dispatch-decision) — parallelism only pays when the domains are genuinely independent.
  2. **dispatch** — Fan out one worker per domain.
     delegate.fan_out a worker per independent domain; each gets a self-contained task and does not coordinate mid-flight.
  3. **join** — Collect every worker's result.
     delegate.join — wait for ALL workers; collect results + failures. A partial join is a failed fan-out, not a success.
  4. **synthesize** — Merge the results into one coherent output.
     Reconcile the workers' outputs and resolve conflicts at the seams. Confirm this gate only when the merged result is coherent — not merely concatenated.
