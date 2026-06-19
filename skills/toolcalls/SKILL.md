---
name: toolcalls
description: "Use when reviewing what a session actually did — which tool calls ran, how often,"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# toolcalls capability

Every pre/post tool call (Bash/Read/Edit/…) is captured in FULL into a local, gitignored `.agency/toolcalls.db` — OFF the durable provenance graph, so the graph stays the moat (Intents/Invocations/Gates) while **no capture data is lost** (Spec 336 S2). This capability is the clear, discoverable surface over that store: inspect the top calls by frequency × cost, read recent calls in full, and export the session's top calls + responses with new-spec suggestions — the dogfooding fold-back loop for Goal 6, where lessons become specs, made automatic.

## When to use

- "what did this session DO / which commands ran the most / what was expensive"
- end-of-session review of the top tool calls and responses
- pruning the ephemeral capture once it has been distilled

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `export` | effect | Distil the session's tool calls into a durable export — the top calls + responses + new-spec SUGGESTIONS (the dogfooding fold-back, Goal 6). | [details](references/export.md) |
| `prune` | effect | Clear the ephemeral capture store (after it has been distilled/exported). | [details](references/prune.md) |
| `recent` | act | The most recent captured tool calls, in FULL (read-only). | [details](references/recent.md) |
| `stats` | act | Capture counts broken down by phase and tool (read-only). | [details](references/stats.md) |
| `top` | act | The top captured tool-call shapes by frequency × payload cost (read-only). | [details](references/top.md) |

## Example

```bash
await call_tool('capability_toolcalls_export', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Reaching into session.db or analyze.graph for tool-call stats → they live in the ephemeral toolcalls.db now, not the graph
- Truncating the captured payload → it is stored in FULL by policy via keep_full

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`toolcalls-usage`** (usage): use-effect → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'toolcalls-usage', 'inputs': {}, 'intent_id': '…'})`
