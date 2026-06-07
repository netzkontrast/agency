<!-- agency-generated: v1 -->
---
name: intent
description: Use when examining a goal before committing to an approach — decomposing it, surfacing its assumptions, stress-testing it with a premortem, or weighing trade-offs.
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# intent capability

Intent is the reasoning capability: it turns the human-owned goal into structured critical-thinking scaffolds — decomposition, assumption-surfacing, premortem, first-principles, inversion, steelman, second-order, and trade-off analysis — each a deterministic method an agent fills in against the current intent.

## When to use

- A goal whose approach is unclear and needs structured decomposition
- A plan resting on unstated assumptions worth surfacing
- A decision between options that needs an explicit trade-off pass
- A risky course where a premortem would expose failure modes early

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `assumptions` | transform | Surface + classify the implicit assumptions a goal rests on (load-bearing vs not). | [details](references/assumptions.md) |
| `decompose` | transform | Decompose a goal into MECE sub-problems — the structured break-down method. | [details](references/decompose.md) |
| `first_principles` | transform | Strip a goal to fundamental truths and rebuild — bypassing inherited assumptions. | [details](references/first_principles.md) |
| `inversion` | transform | Invert the goal — ask what would GUARANTEE failure, then avoid exactly that. | [details](references/inversion.md) |
| `premortem` | transform | Premortem — assume the goal FAILED, reason backward to causes + mitigations. | [details](references/premortem.md) |
| `second_order` | transform | Trace second- and third-order consequences — 'and then what?' past the first effect. | [details](references/second_order.md) |
| `steelman` | transform | Build the STRONGEST version of the opposing or alternative position. | [details](references/steelman.md) |
| `suggests` | transform | Project the serving intent + the last verb's state to the next applicable skill (Spec 026 Part B — Intent owns the intent→skill projection; a RECOMMENDATION, not a dispatch). | [details](references/suggests.md) |
| `tradeoffs` | transform | Build an explicit trade-off matrix — options × criteria — for a decision. | [details](references/tradeoffs.md) |

## Example

```bash
await call_tool('capability_intent_assumptions', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Committing to an approach without surfacing assumptions → capability_intent_assumptions
- Shipping a risky plan unexamined → run capability_intent_premortem first

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`critical-thinking`** (discipline): frame → surface → stress-test → weigh → decide
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'critical-thinking', 'inputs': {}, 'intent_id': '…'})`
