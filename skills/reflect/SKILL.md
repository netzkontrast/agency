---
name: reflect
description: "Reflect is the cross-session memory surface: scope-tagged notes recorded as graph nodes, recalled by scope or by semantic similarity against prior observations. Use when durable, scope-tagged memory must cross sessions — recording an insight, or recalling prior observations by scope or semantic similarity."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# reflect capability

Reflect is the cross-session memory surface: scope-tagged notes recorded as graph nodes, recalled by scope or by semantic similarity against prior observations.

## When to use

- A lesson that should outlive the current session
- A question whose answer may live in prior reflections
- Repeated rediscovery of something already learned

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `batch_note` | act | Bulk version of ``note``: one Reflection node per text. | [details](references/batch_note.md) |
| `note` | act | Write a scope-tagged insight node; edged OBSERVED_DURING + SERVES the intent. | [details](references/note.md) |
| `recall` | transform | Retrieve reflections, newest first, optionally filtered by scope. | [details](references/recall.md) |
| `recall_semantic` | transform | Semantic top-k recall over Reflection nodes; backend-injectable. | [details](references/recall_semantic.md) |
| `search` | transform | Keyword search over reflection text (deterministic substring match). | [details](references/search.md) |
| `synthesize_session` | act | Produce a session-reflection artefact at session close (act). | [details](references/synthesize_session.md) |

## Example

```bash
await call_tool('capability_reflect_batch_note', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Re-learning a past lesson → search prior notes via capability_reflect_recall_semantic
- Letting an insight evaporate at session end → capability_reflect_note it

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`reflect-usage`** (usage): use-transform → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'reflect-usage', 'inputs': {}, 'intent_id': '…'})`
