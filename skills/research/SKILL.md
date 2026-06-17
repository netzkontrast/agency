---
name: research
description: "Research runs a question through a lead that scopes it, specialists that gather evidence, and a verifier that adversarially checks claims before publishing. Use when an open question needs cited evidence from multiple sources — driving a research question through a lead, fan-out specialists, and an adversarial verifier."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# research capability

Research runs a question through a lead that scopes it, specialists that gather evidence, and a verifier that adversarially checks claims before publishing.

## When to use

- A question whose answer needs cited, cross-checked sources
- A claim that should be verified before it is trusted
- A topic too broad for a single lookup

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `ingest_gdoc` | transform | Compose a subagent dispatch contract that ingests a Google Doc to disk. | [details](references/ingest_gdoc.md) |
| `lead` | act | Scope a research question + plan specialists; mints a Research node. | [details](references/lead.md) |
| `record_ingested_source` | effect | Record an ``ingested-source`` Artefact (SERVES intent + PRODUCES edge). | [details](references/record_ingested_source.md) |
| `specialist` | act | One bounded sub-search; records Citations under the research_id. | [details](references/specialist.md) |
| `verify` | act | Adversarial citation check; emits a Verification node. | [details](references/verify.md) |

## Example

```bash
await call_tool('capability_research_ingest_gdoc', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Trusting a single source → cross-check with capability_research_verify
- Answering an open question from memory → run capability_research_lead

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`deep-research`** (discipline): plan → fan-out → verify → publish
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'deep-research', 'inputs': {}, 'intent_id': '…'})`
