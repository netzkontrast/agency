---
name: discover
description: "Use when a fresh or vague intent needs guided discovery BEFORE work begins —"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# discover capability



## When to use

- An underspecified ask arrives and the WHY is captured, not discovered
- An intent has no measurable acceptance criteria yet
- Work is about to start against an unconfirmed or ungrounded intent

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `acceptance` | transform | Derive testable, Gherkin-shaped acceptance criteria from the Intent (transform). | [details](references/acceptance.md) |
| `ask` | transform | Build ONE well-formed AskUserQuestion payload from DERIVED options (transform). | [details](references/ask.md) |
| `clarify` | act | Resolve a draft Intent's ambiguities, folding each answer back (act). | [details](references/clarify.md) |
| `clarity` | transform | Score a captured Intent's clarity / readiness (transform, read-only). | [details](references/clarity.md) |
| `interview` | act | Run the adaptive elicitation interview → a DRAFT Intent (act). | [details](references/interview.md) |
| `scope` | act | Elicit in-/out-of-scope boundaries (act). | [details](references/scope.md) |
| `status` | transform | Smoke verb — report the registered ``discover`` ontology surface. | [details](references/status.md) |

## Example

```bash
await call_tool('capability_discover_acceptance', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Starting work against an unconfirmed intent → run ``discover.interview`` first
- Inventing AskUser options instead of deriving them from evidence → ``discover.ground``
- Treating a one-line seed as a finished intent → walk ``guided-discovery``

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`discover-usage`** (usage): use-transform → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'discover-usage', 'inputs': {}, 'intent_id': '…'})`
