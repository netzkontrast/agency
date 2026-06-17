---
name: thinking
description: "Use when structured rigor needed before commit; binding decisions need tradeoff + premortem + red-team; an assumption stack needs surfacing."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# thinking capability

10 method verbs (8 founding + 2 net-new: red_team + socratic) + 1 composite (apply_full_review) + 1 walkable skill (critical-thinking).

## When to use

- About to commit to a decision: run apply_decision_discipline first
- About to merge a complex spec: run apply_full_review
- Suspect a load-bearing assumption is unstated: run assumptions

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `apply_full_review` | act | Run the 8 founding methods in sequence; produce thinking-analysis artefact (act). | [details](references/apply_full_review.md) |
| `assumptions` | transform | Surface + classify implicit assumptions (load-bearing vs not) (transform). | [details](references/assumptions.md) |
| `decompose` | transform | MECE sub-problem decomposition (transform). | [details](references/decompose.md) |
| `first_principles` | transform | Strip the goal to fundamentals + reconstruct (transform). | [details](references/first_principles.md) |
| `inversion` | transform | Look for what guarantees failure rather than what guarantees success. | [details](references/inversion.md) |
| `premortem` | transform | Prospective failure analysis (transform). | [details](references/premortem.md) |
| `red_team` | transform | Adversarial review — adopt an attacker's stance + find failure paths (transform). | [details](references/red_team.md) |
| `second_order` | transform | Trace consequences N steps downstream (transform). | [details](references/second_order.md) |
| `socratic` | transform | Five-whys-deeper Socratic questioning (transform). | [details](references/socratic.md) |
| `steelman` | transform | Build the strongest possible argument against a position (transform). | [details](references/steelman.md) |
| `tradeoffs` | transform | Multi-criteria option scoring (transform). | [details](references/tradeoffs.md) |

## Example

```bash
await call_tool('capability_thinking_apply_full_review', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-rolling decision rationales without the discipline → call thinking verbs
- Claiming a steelman without testing the inverse → call inversion + steelman

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`critical-thinking-pass`** (workflow): decompose → surface-assumptions → premortem → steelman-and-inversion → synthesize
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'critical-thinking-pass', 'inputs': {}, 'intent_id': '…'})`
