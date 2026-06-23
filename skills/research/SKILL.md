---
name: research
description: "Use when an open question needs cited evidence from multiple sources — driving a research question through a lead, fan-out specialists, and an adversarial verifier."
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
| `lead` | act | Scope a research question and plan specialists, minting a Research node. | [details](references/lead.md) |
| `record_ingested_source` | effect | Record an ``ingested-source`` Artefact (SERVES intent + PRODUCES edge). | [details](references/record_ingested_source.md) |
| `specialist` | act | Run one bounded sub-search, recording Citations under the research_id. | [details](references/specialist.md) |
| `verify` | act | Adversarially check citations, emitting a Verification node. | [details](references/verify.md) |

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
  1. **plan** — Plan the research — lead question + specialist lenses.
     Frame the research question sharply and pick the specialist lenses (sources/angles) to fan out across. A vague question fans out into noise.
  2. **fan-out** — Fan out and record every citation.
     Run each specialist lens; record EVERY source as a Citation node (the report must survive the session). Capture the evidence, not just conclusions.
  3. **verify** — Adversarially verify the claims.
     Cross-check the claims against their citations; flag the unsupported ones. Verification is what separates research from a confident guess.
  4. **publish** — Publish the cited report.
     Synthesise the verified findings into a cited report. Confirm this gate only when every load-bearing claim carries a citation.

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_research_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_research_ingest_gdoc", {"intent_id": iid})
await call_tool("capability_research_lead", {"intent_id": iid})
await call_tool("capability_research_record_ingested_source", {"intent_id": iid})
await call_tool("capability_research_specialist", {"intent_id": iid})
await call_tool("capability_research_verify", {"intent_id": iid})
```
