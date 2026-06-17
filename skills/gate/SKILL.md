---
name: gate
description: "Use when a programmatic, reusable predicate must pass before work proceeds — an acceptance check recorded as a Gate in the provenance graph."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# gate capability

Gate evaluates a reusable predicate and records the outcome as a Gate node edged into the lifecycle and intent, so a pass or block is auditable provenance.

## When to use

- A decision point that must be enforced, not assumed
- An acceptance condition that should be recorded as provenance

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `adjudicate` | act | Adjudicate two CONFLICTING concerns at a decision point by consulting ``doctrine.resolve`` — the priority-hierarchy winner (safety > correctness > maintainability > speed), recorded as a Gate (Spec 303). | [details](references/adjudicate.md) |
| `check` | act | Record a gate outcome on a Lifecycle: PASSED, or BLOCKED_ON + an input-required pause on failure. | [details](references/check.md) |

## Example

```bash
await call_tool('capability_gate_adjudicate', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- (none documented)

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`gate-usage`** (usage): use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'gate-usage', 'inputs': {}, 'intent_id': '…'})`
