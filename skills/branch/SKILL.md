---
name: branch
description: "Use when a development branch is ready to wrap up and its state must be detected to merge, open a PR, or report what blocks completion."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# branch capability

Branch inspects the working tree and remote state and finishes the branch the appropriate way — merge when clean, a PR when review is needed, or a clear report of what blocks completion.

## When to use

- A feature branch whose work appears complete
- Uncertainty whether a branch should merge or open a PR

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `assess` | transform | Read the branch state (ahead/behind/dirty) and recommend merge/pr/keep/discard. | [details](references/assess.md) |
| `commit_smart` | transform | Compose a conventional-commit message from a change summary + the changed paths (Spec 046 F-C — decidable, no LLM). | [details](references/commit_smart.md) |
| `finish` | effect | Finish the branch by the chosen action (merge/pr/keep/discard) and record the outcome. | [details](references/finish.md) |

## Example

```bash
await call_tool('capability_branch_assess', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-writing a commit message → compose it with capability_branch_commit_smart
- Merging a branch without reading its state → run capability_branch_assess first

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`branch-usage`** (usage): use-transform → use-effect → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'branch-usage', 'inputs': {}, 'intent_id': '…'})`
