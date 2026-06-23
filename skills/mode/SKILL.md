---
name: mode
description: "Use when the way of working should shift for the task at hand — discovery,"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# mode capability

A native reimplementation of SuperClaude's behavioral modes: postures that change HOW the agent operates. Decidable (like `panel`/`thinking`): trigger-term overlap selects the mode; activation returns the posture's behavioral rules and records a `ModeActivation` node, so a session's adopted postures are provenance.

## When to use

- A vague or exploratory request that needs discovery before building
- A meta-cognitive ask: inspect reasoning, reflect on a failed approach
- A multi-tool or multi-step operation that needs routing or phasing
- A brevity-constrained context that needs compressed output

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `activate` | effect | Activate a behavioral posture — return its rules + record provenance (Spec 295). | [details](references/activate.md) |
| `detect` | act | Rank the behavioral modes by decidable trigger overlap with ``context`` (read-only). | [details](references/detect.md) |
| `list` | act | The behavioral-mode roster — name · purpose · behaviors · triggers. | [details](references/list.md) |

## Example

```bash
await call_tool('capability_mode_activate', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Diving into build on a vague request → activate brainstorming first
- Repeating a failed approach → activate introspection to inspect the reasoning

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`mode-selection`** (discipline): assess → detect → activate → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'mode-selection', 'inputs': {}, 'intent_id': '…'})`
  1. **assess** — Assess the work context.
     Read the situation — what kind of work is this (design, build, debug, review)? The context drives which session mode fits.
  2. **detect** — Detect the candidate modes.
     Surface the modes that match the context; usually 1–2 are plausible. Don't force a mode the work doesn't call for.
  3. **activate** — Activate the chosen mode.
     Switch to the selected mode and record the ModeShift — the mode biases which disciplines + verbs you reach for next.
  4. **confirm** — Confirm the mode with its rationale.
     State WHY this mode fits the context. Confirm this gate only with a rationale grounded in the assessed work, not a default.
