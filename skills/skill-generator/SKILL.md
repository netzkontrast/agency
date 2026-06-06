<!-- agency-generated: v1 -->
---
name: skill-generator
description: Use when a deploy-ready skill should be produced in one call — a complete, CSO-clean SKILL.md generated from a description.
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# skill-generator capability

Skill_generator produces a deploy-ready skill in a single call, emitting a CSO-clean SKILL.md from a name and description.

## When to use

- A new skill needed without hand-assembling its files
- A skill idea that should become a deployable artefact

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `generate` | act | Author a SKILL.md and lint it against the CSO rules; flag if not deploy-ready. | [details](references/generate.md) |

## Example

```bash
await call_tool('capability_skill_generator_generate', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- (none documented)
