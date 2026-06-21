---
name: adr
description: "Use when an architectural decision must be RECORDED as a first-class,"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# adr capability



## When to use

- A spec or design makes a choice whose rationale would otherwise be lost
- "Why did we decide X (and not Y)?" needs a durable, traversable answer
- An ADR must be validated against the WH(Y) format before approval

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `draft` | act | DRAFT — record a WH(Y) ``Decision`` (status ``proposed``) ``PART_OF`` the theme, SERVING the intent (SPEC-001-A). | [details](references/draft.md) |
| `theme` | act | THEME — get-or-create a thematic-living ADR for one architecture ``layer`` (the ported Master ADR). | [details](references/theme.md) |
| `validate` | transform | VALIDATE — run the decidable WH(Y) rules over a Decision; return findings + an ``ok`` flag. | [details](references/validate.md) |

## Example

```bash
await call_tool('capability_adr_draft', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Burying a decision in spec prose where it is lost at implementation time → draft it
- Hand-writing a Decision via `manage.create` without the WH(Y) discipline → use adr.draft
- Putting implementation detail in the decision → that belongs in the spec it REFINES

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`adr-usage`** (usage): use-transform → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'adr-usage', 'inputs': {}, 'intent_id': '…'})`
