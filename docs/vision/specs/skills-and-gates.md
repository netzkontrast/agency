---
slug: spec-skills-and-gates
type: spec
status: ready
summary: Skills are atomic, gated, progressively-disclosed Lifecycle step-graphs — a graph of atomic Capability steps + Gates walked step-by-step via code-mode, NOT a monolith loaded wholesale. Gates / intent-verification / askuser are ctx.elicit steps; the Lifecycle pauses at input-required, the answer resumes it, the outcome is recorded as a Gate. Proven: a real ctx.elicit round-trip.
---

# Skills & gates

> **Status: specced; proven where noted.** The engine proves the gate
> mechanism with a real `ctx.elicit` round-trip recorded to the provenance graph.

## A skill is a Lifecycle step-graph, not a monolith

In v4 a "skill" is **not** a monolithic SKILL.md loaded wholesale. A skill is a
**Lifecycle template: a graph of atomic Capability steps + Gates**, walked
step-by-step via code-mode. Each step discloses only the *next* instruction
(`search → get_schema → execute`), so tokens are paid **per atomic step**, not
for the whole skill.

The chain *is* an executable dataflow graph: a step's output feeds the next.
Because every `call_tool` records an Invocation, the executable chain mirrors
itself into the durable provenance graph (a transform feeding an agent, both
edged to the Intent).

**Proven:** an `execute` block lints three candidate skills with
`capability_plugin_lint_skill` (`transform`), then dispatches the cleanest via
`capability_jules_dispatch` (the agent). Many in-sandbox calls return ONE small
delta; the chain appears as a connected provenance subgraph (`lint_skill,
lint_skill, lint_skill, dispatch`, plus the agent and the artefact).

## Gates / intent-verification / askuser are `elicit` steps

A step can:

- `ctx.elicit(prompt, response_type=...)` — ask the agent or human a one-line
  question and get a **typed** answer (askuser-in-the-flow);
- `ctx.sample(...)` — ask the caller's LLM;
- `ctx.report_progress(...)` — stream progress.

A gate that needs a human is **just an `elicit`**: the Lifecycle pauses at
`input-required`, a tiny prompt streams out, the answer resumes the chain, and
the outcome is recorded as a `Gate` node (`PASSED` or blocked). **"askuser" is
therefore not a special case — it is one node in the chain.** Hard gates must
pass to advance; advisory gates surface a warning and never block.

**Proven:** `lifecycle_gate(question, intent_id, lifecycle_id, ctx)` calls
`await ctx.elicit("Approve release?", response_type=["approve","reject"])`; an
elicitation handler returns `approve`; the Lifecycle records a `human-confirm`
Gate `PASSED`, visible in `provenance(intent).gates`.

## Token efficiency

Three mechanisms compound:

1. **Progressive disclosure** — only the next step's instruction loads.
2. **Code-mode deltas** — many tool calls run in-sandbox; only the final small
   delta (+ `elided_ref` handles for large payloads) crosses into context.
3. **`project(query, budget)`** — reads return ranked, budgeted deltas, never raw
   history.

## Interactions

- A skill step-graph is a Lifecycle parameterization (see
  [lifecycle.md](lifecycle.md)); its steps are Capability invocations (see
  [capability.md](capability.md)); its record lives in Memory (see
  [memory.md](memory.md)); every step `SERVES` the Intent.
- The same mechanism expresses domain hard gates (a pre-action check),
  intent-confirmation phases (an Intent
  `confirm` gate), and human source-verification (a `validate` + `confirm` gate)
  — all as `elicit` steps recorded as `Gate` nodes.
