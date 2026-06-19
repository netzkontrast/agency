---
capability: research
pillar: capability
vision_goals: [1, 2, 4]
status: living
last_generated: 2026-06-19
sources: [44, 52, 126]
---

# research — Research runs a question through a lead that scopes it, specialists that gather evidence, and a verifier that adversarially checks claims before publishing (capability pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
Research drives an open question through a scoping lead, specialist fanout, and adversarial cross-check, producing a published finding that rests on verified cited sources rather than single-source trust.

## Verbs (generated · 5)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `research.ingest_gdoc` | transform | **source** · dest | Compose a subagent dispatch contract that ingests a Google Doc to disk. |
| `research.lead` | act | **question** · depth | Scope a research question + plan specialists; mints a Research node. |
| `research.record_ingested_source` | effect | **source_url** · **dest** · **bytes** · **lines** · **sha256** · **title** | Record an ``ingested-source`` Artefact (SERVES intent + PRODUCES edge). |
| `research.specialist` | act | **research_id** · **role** · **query** · search_root · docs_root · k | One bounded sub-search; records Citations under the research_id. |
| `research.verify` | act | **research_id** | Adversarial citation check; emits a Verification node. |

## Ontology (generated)

**Nodes:** `Research`(question, depth, started_at, status) · `Citation`(source_kind, source_url_or_path, evidence_text, confidence, claim_supported, research_id) · `ResearchClaim`(text, research_id) · `Verification`(research_id, status, started_at)
**Edges:** `CITES` · `CONTRADICTS` · `SUPPORTS` · `VERIFIES`
**Enums:** `('Research', 'status')` ∈ {blocked, fanning-out, planning, published, ready, verifying} · `('Citation', 'source_kind')` ∈ {codebase, doc-corpus, reflection, web} · `('Verification', 'status')` ∈ {fail, pass, warn}

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/research -->
