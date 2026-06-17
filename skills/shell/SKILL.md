---
name: shell
description: "Use when running a host CLI command whose output should be token-filtered and recorded — an allowlisted command, a reusable template, or a pure output filter."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# shell capability

Shell is a token-efficient host-command boundary: allowlisted execution, output filtering, and definable templates that bundle a command with its token-saving filter.

## When to use

- A bash command whose full output would flood the context
- A common command rerun often enough to template
- Host output that needs trimming before it crosses back

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `define` | act | Define a named shell template (command + output filter + doc) in the graph. | [details](references/define.md) |
| `filter` | transform | Filter text to a token-bounded slice — pure, no execution (hook-ready). | [details](references/filter.md) |
| `run` | effect | Run an ALLOWLISTED command (or a named template), FILTER its output, record it. | [details](references/run.md) |
| `templates` | transform | Discover named query templates — built-in seeds ∪ graph-defined (Spec 075). | [details](references/templates.md) |

## Example

```bash
await call_tool('capability_shell_define', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Dumping a long command's full output → trim it via capability_shell_filter
- Re-composing the same command and filter → save it with capability_shell_define

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`shell-usage`** (usage): use-transform → use-effect → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'shell-usage', 'inputs': {}, 'intent_id': '…'})`
