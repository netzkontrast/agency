<!-- agency-generated: v1 -->
---
name: recommend
description: Use when you have a goal in words and want the right agency verb to reach for,
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# recommend capability

A native reimplementation of SuperClaude's `sc-recommend`: given a free-text request, recommend the most suitable agency capability + verb to use. Reads the LIVE registry (capabilities · verbs · skills) — a core agency feature — and scores by decidable token overlap. Distinct from `search` (keyword tool lookup): this routes an intent to a recommended call with a rationale.

## When to use

- A free-text request that should map to a capability + verb
- Uncertainty about which agency surface to use for a task
- Routing a user's ask to the most suitable starting verb

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `route` | effect | Recommend the capability + verb best matched to a free-text ``request`` (Spec 298). | [details](references/route.md) |

## Example

```bash
await call_tool('capability_recommend_route', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Guessing a verb name from memory → recommend.route(request) first
- Reaching for a raw tool when a capability verb fits → check the recommendation

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`recommend-usage`** (usage): use-effect → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'recommend-usage', 'inputs': {}, 'intent_id': '…'})`
