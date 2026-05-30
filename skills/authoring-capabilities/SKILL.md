---
name: authoring-capabilities
description: Use when authoring a new agency capability or extending an
  existing one — before writing the file. The discipline runs scaffold
  then lint behind a hard gate; lint must pass before commit.
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Read
  - Write
  - Edit
  - Bash
---

# authoring-capabilities

Three steps; lint gate before commit.

## 1. Research
Read [`docs/vision/CAPABILITY-AUTHORING.md`](../../docs/vision/CAPABILITY-AUTHORING.md)
— the unified doctrine. T1 summary: every verb has Spec-016-Hint-#7
markers (`Inputs:` / `Returns:` / `chain_next:`), role-tagged
`act` / `transform` / `effect`, first sentence ≤120 chars.

## 2. Scaffold
```python
await call_tool("capability_develop_scaffold_capability",
                {"name": "my-cap", "kind": "light"})
```
Kinds: `light` (≤3 verbs, no ontology data) · `medium` (owns ontology
fragment) · `heavy` (folder-form per Hint #1, ≥3 sibling files).
Emits `# agency-scaffold: v1` marker on line 1 — `plugin.lint_capability`
reads it to block-on-violation rather than warn.

## 3. Lint (hard gate)
```python
await call_tool("capability_plugin_lint_capability", {"name": "my-cap"})
```
Five rule families: structural · role_tag · render_slice ·
consumer_contract · token_budget. Mode `block` + `ok: False` → fix
before commit. Mode `warn` → legacy grandfathering (no marker).
