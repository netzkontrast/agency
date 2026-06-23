---
name: config
description: "Use when you need to read or change an agency config value (e.g. frugal.level, a"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# config capability

Config exposes get / set / list over the unified config resolver so an agent or the CLI can inspect and change agency configuration without hand-editing the file. Precedence is env over file over default; secrets stay env-only and are never written to the file. Thin by design — all logic lives in agency._config; these verbs are the user-facing surface over it.

## When to use

- "what is <key> set to / where does its value come from"
- "set <key> to <value>" / "turn frugal to lite"
- "list all config and their sources"

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `get` | act | Resolve a config key to its live value + source. | [details](#get) |
| `list` | act | Every registered config key → value + source, plus validation issues. | [details](#list) |
| `set` | act | Persist a config value to ``.agency/config.yaml``, then re-resolve it. | [details](#set) |

## Example

```bash
await call_tool('capability_config_get', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Writing a secret such as an API key → config refuses; set the env var instead.

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`config-usage`** (usage): use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'config-usage', 'inputs': {}, 'intent_id': '…'})`

## get

Resolve a config key to its live value + source.

Parameters: `(key: 'str')`.

## list

Every registered config key → value + source, plus validation issues.

Parameters: `()`.

## set

Persist a config value to ``.agency/config.yaml``, then re-resolve it.

Parameters: `(key: 'str', value: 'str')`.
