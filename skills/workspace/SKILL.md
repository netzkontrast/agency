---
name: workspace
description: "Use when work should be isolated in a git worktree with a recorded green baseline — a clean, provably-green starting point before risky changes."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# workspace capability

Workspace isolates work in a git worktree and records a green baseline, so risky changes start from a clean, provably-green point that recovery can return to.

## When to use

- Risky changes that should not touch the main working tree
- A starting point that must be provably green before edits

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `baseline` | effect | Run the baseline test command in the workspace and record the green/red result. | [details](references/baseline.md) |
| `isolate` | effect | Create an isolated git worktree on a fresh branch off `base`, recording the Workspace. | [details](references/isolate.md) |

## Example

```bash
await call_tool('capability_workspace_baseline', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- (none documented)

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`workspace-usage`** (usage): use-effect → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'workspace-usage', 'inputs': {}, 'intent_id': '…'})`

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_workspace_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_workspace_baseline", {"intent_id": iid})
await call_tool("capability_workspace_isolate", {"intent_id": iid})
```
