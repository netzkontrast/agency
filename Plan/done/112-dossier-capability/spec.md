---
spec_id: "112"
slug: dossier-capability
status: draft
state: done
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["001", "002", "020", "044", "047", "054", "060", "076", "079", "080", "081", "092", "109"]
affects:
  - agency/capabilities/dossier/
  - tests/test_dossier_*.py
source-material:
  - "Plan/_research/novel-mvp-source/research-prompt-optimizer/ (research-prompt-optimizer 5-phase pattern)"
  - "Plan/_research/novel-mvp-source/research-prompt-optimizer/agentic-tool-catalog.md (A/B/C × M01-M12 module catalog)"
  - "Spec 105 iter-10 (novel research cluster's 4-stage research-entity ontology — generalized into a first-class capability)"
domain: capability / research-dossier / corpus
wave: 8
research_first: false
---

# Spec 112 — `dossier` Capability (research-dossier + corpus)

## Why

User directive (2026-06-07): *"Those Research Parts - Need to be its
own capability - that Feed into Research agents - so that we can
freely combine capabilities - novel is only the First one to make use
of the Research capability."*

The novel spec set's iter-10 (research-entity ontology) + iter-12
(research-prompt-optimizer ports) are a general pattern that any
domain capability needs: **bring background research into a structured,
queryable, chapter/scene/section-mappable, prompt-snippet-renderable
form**.

This pattern is reusable across:
- **novel** (current consumer) — research → chapters
- **music** (next consumer) — research → tracks (e.g. concept-album
  research informing lyrics)
- **screenplay** (future) — research → scenes
- **journalism / longform** (future) — research → article sections
- **academic / report-writing** (future) — research → report chapters
- **legal-brief** (future) — research → case-brief sections

Spec 112 promotes the pattern to a first-class agency capability
`dossier` under `agency/capabilities/dossier/`. It **feeds INTO the
existing `research` capability** (Spec 044: `lead`/`specialist`/
`verify`) — the dossier capability handles intent capture, brief
authoring, corpus ingestion, entity extraction, and prompt-snippet
rendering. The research capability handles outbound search +
verification.

## Architecture

```
USER REQUEST
     ↓
┌────────────────────────────────────┐
│ dossier capability (Spec 112)        │
│                                    │
│  Stage 0: intent_capture           │
│  Stage 1: ingest_source            │
│  Stage 2: chunk + extract_entities │
│  Stage 3: taxonomize + relate      │
│  Stage 4: map_context              │
│  Stage 5: render_snippet           │
│  Stage 6: audit                    │
└────────────────────────────────────┘
     ↓                              ↑
     │ delegates outbound search to │ produces entities feeding back
     ↓                              │
┌────────────────────────────────────┐
│ research capability (Spec 044)     │
│                                    │
│  • lead (mint Research node)       │
│  • specialist (4 roles: codebase/  │
│      prior-reflections/doc-corpus/ │
│      web)                          │
│  • verify (cross-check claims)     │
└────────────────────────────────────┘
     ↓
DOMAIN CAPABILITY (novel/music/screenplay/...)
     ↓
PromptSnippet → engineer_writing_prompt (prompt capability, Spec 109)
              → LLM-assisted drafting in domain cap (novel/music/...)
```

## Done When

- [ ] `agency/capabilities/dossier/` registers `DossierCapability` with
      drop-in bar (zero engine edits).
- [ ] 20 user-facing verbs ship (4 intent/audit + 4 corpus + 5
      entity + 4 mapping/snippet + 3 catalog). See manifest.
- [ ] 3 internal gate verbs.
- [ ] 4 walkable skills (`dossier-intent-pass` / `corpus-ingest-pass` /
      `entity-mapping-pass` / `snippet-render-pass`).
- [ ] Ontology + schemas + edges declared (see Design).
- [ ] Templates ship under `agency/capabilities/dossier/templates/`
      (brief-skeleton / intent-yaml / module-catalog-entry /
      entity-card / snippet-skeleton).
- [ ] Data assets ship under `agency/capabilities/dossier/data/` —
      A/B/C × M01-M12 module catalog (verbatim from imported
      `agentic-tool-catalog.md`).
- [ ] Cross-capability surface: dossier calls `research.specialist`
      for outbound search (delegation pattern); novel (Spec 105 iter-10)
      refactored to DELEGATE its research-entity verbs to `dossier.*`
      via `ctx.call`.
- [ ] `tests/test_dossier_capability.py` Green (~22 tests).
- [ ] `TODO.md` updated with 112 row.

## Verb manifest

### 1. Intent + audit cluster (4 verbs)

| # | Verb | Role | Lineage |
|---|---|---|---|
| 1 | `intent_capture` | act | research-prompt-optimizer Phase 1 |
| 2 | `audit` | effect | research-prompt-optimizer Phase 3 (reader-test) |
| 3 | `finalize` | effect | research-prompt-optimizer Phase 5 |
| 4 | `dispatch_research_via_dossier` | effect | delegates to `research.lead` + `research.specialist` × N |

### 2. Corpus cluster (4 verbs)

| # | Verb | Role | Lineage |
|---|---|---|---|
| 5 | `ingest_source` | effect | novel iter-10 Stage 1 |
| 6 | `chunk_source` | effect | novel iter-10 Stage 1 |
| 7 | `list_sources` | transform | novel iter-10 |
| 8 | `reingest_source` | effect | novel iter-10 |

### 3. Entity cluster (5 verbs)

| # | Verb | Role | Lineage |
|---|---|---|---|
| 9 | `extract_entities` | effect | novel iter-10 Stage 2 |
| 10 | `taxonomize_entity` | effect | novel iter-10 Stage 2 |
| 11 | `auto_taxonomize_source` | effect | novel iter-10 Stage 2 |
| 12 | `link_entities` | effect | novel iter-10 Stage 2 |
| 13 | `list_entities` | transform | novel iter-10 Stage 2 |

### 4. Mapping + snippet cluster (4 verbs)

| # | Verb | Role | Lineage |
|---|---|---|---|
| 14 | `declare_context` | effect | novel iter-10 Stage 3 (renamed from chapter-specific to generic) |
| 15 | `infer_context` | transform | novel iter-10 Stage 3 |
| 16 | `render_brief` | transform | research-prompt-optimizer Phase 2 + novel iter-10 chapter_research_brief generalized |
| 17 | `render_snippet` | transform | novel iter-10 Stage 4 (build_writing_prompt_snippet generalized) |

### 5. Catalog cluster (3 verbs)

| # | Verb | Role | Lineage |
|---|---|---|---|
| 18 | `catalog_list` | transform | research-prompt-optimizer module catalog |
| 19 | `catalog_get_module` | transform | retrieve specific module |
| 20 | `register_module` | effect | add domain-specific module (e.g. novel adds chapter-mapping module) |

**Internal composite gate verbs**:

| # | Verb | Walks |
|---|---|---|
| G1 | `audit_gate` | `dossier-intent-pass` phase 4 |
| G2 | `entity_extraction_gate` | `corpus-ingest-pass` phase 3 |
| G3 | `context_coverage_gate` | `entity-mapping-pass` phase 3 |

**Total: 20 user + 3 gate = 23 registered verbs.**

## Design

### Module layout

```
agency/capabilities/dossier/
├── __init__.py              # DossierCapability + module docstring → SkillDoc
├── ontology.py              # OntologyExtension
├── clusters/
│   ├── __init__.py
│   ├── intent.py            # intent + audit + finalize + dispatch (1-4)
│   ├── corpus.py            # corpus ingestion (5-8)
│   ├── entities.py          # entity extraction + taxonomy (9-13)
│   ├── mapping.py           # context + snippet (14-17)
│   └── catalog.py           # catalog (18-20)
├── templates/
│   ├── brief-skeleton.md
│   ├── intent-yaml.md
│   ├── module-catalog-entry.md
│   ├── entity-card.md
│   └── snippet-skeleton.md
└── data/
    ├── reference/
    │   └── module-catalog.yaml      # verbatim from imported
    │                                  # agentic-tool-catalog A/B/C × M01-M12
    └── schemas/
        ├── intent.schema.json
        ├── dossier.schema.json
        └── entity.schema.json
```

### Ontology (consolidated `OntologyExtension`)

```python
dossier_ontology = OntologyExtension(
    nodes={
        # Intent + audit layer:
        "ResearchIntent":      ["seed_query", "topic", "deliverable",
                                "success_criteria"],
        "ResearchBrief":       ["intent", "body_uri"],
        "BriefAudit":          ["brief", "clarity_score",
                                "missing_sections"],

        # Corpus layer:
        "ResearchSource":      ["slug", "kind", "title", "author",
                                "body_uri", "ingestion_status"],
        "ResearchChunk":       ["slug", "source", "position", "body"],

        # Entity layer:
        "ResearchEntity":      ["slug", "source_chunk", "kind", "name",
                                "body", "confidence", "generated_by"],
        "EntityTag":           ["slug", "entity", "taxonomy", "tag"],
        "EntityRelation":      ["slug", "source_entity", "target_entity",
                                "kind"],

        # Mapping layer:
        "Context":             ["slug", "scope", "scope_id",
                                "entity", "weight", "purpose"],
                                # scope: chapter | section | scene | page |
                                #        custom — domain-agnostic

        # Snippet layer:
        "PromptSnippet":       ["slug", "context_refs", "snippet_kind",
                                "body", "entity_refs", "generated_at"],

        # Catalog layer:
        "CatalogModule":       ["slug", "category", "identifier",
                                "name", "body", "deps"],
    },
    enums={
        ("ResearchSource", "kind"): {"paper", "book", "treatise",
                                      "lecture-transcript", "interview",
                                      "dataset", "image-set"},
        ("ResearchSource", "ingestion_status"): {"pending", "chunked",
                                                 "extracted", "indexed"},
        ("ResearchChunk", "chunk_kind"): {"paragraph", "section",
                                          "quote", "figure-caption"},
        ("ResearchEntity", "kind"): {"concept", "mechanism", "definition",
                                     "example", "counterexample",
                                     "lineage", "theorem", "anecdote",
                                     "quote", "analogy", "empirical-fact"},
        ("EntityRelation", "kind"): {"depends-on", "contradicts",
                                     "illustrates", "refines",
                                     "derives-from", "inspired-by"},
        ("Context", "purpose"): {"backbone", "flavor", "factcheck",
                                 "counterpoint", "metaphor-source"},
        ("PromptSnippet", "snippet_kind"): {"writing-assist",
                                            "dialogue-prompt",
                                            "description-prompt",
                                            "exposition-prompt",
                                            "metaphor-prompt"},
        ("CatalogModule", "category"): {"A", "B", "C"},
    },
    edges={
        "RENDERS_FROM",            # ResearchBrief → ResearchIntent
        "AUDITS_BRIEF",            # BriefAudit → ResearchBrief
        "EXTRACTED_FROM",          # ResearchEntity → ResearchChunk
        "TAGGED_AS",               # ResearchEntity → EntityTag
        "RELATES_TO_ENTITY",       # EntityRelation source → target
        "CONTEXTUALIZES",          # Context → ResearchEntity
        "BUNDLES",                 # PromptSnippet → ResearchEntity
        "DERIVED_FROM_MODULE",     # ResearchBrief → CatalogModule
    },
    skills={
        "dossier-intent-pass":   DOSSIER_INTENT_PASS_SKILL,
        "corpus-ingest-pass":  CORPUS_INGEST_PASS_SKILL,
        "entity-mapping-pass": ENTITY_MAPPING_PASS_SKILL,
        "snippet-render-pass": SNIPPET_RENDER_PASS_SKILL,
    },
    schemas={
        "intent-yaml":      ["topic", "deliverable", "success_criteria"],
        "research-brief":   ["intent_ref", "body"],
        "entity-card":      ["kind", "name", "body"],
        "snippet":          ["snippet_kind", "body", "entity_refs"],
    },
    templates={
        "brief-skeleton":         None,
        "intent-yaml":            None,
        "module-catalog-entry":   None,
        "entity-card":            None,
        "snippet-skeleton":       None,
    },
)
```

### 4 walkable skills (one per layer)

```python
DOSSIER_INTENT_PASS_SKILL = {
    "name": "dossier-intent-pass", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "intent-capture",
         "produces": ["intent_yaml_recorded"]},
        {"index": 2, "name": "module-select",
         "produces": ["catalog_modules_chosen"]},
        {"index": 3, "name": "brief-render",
         "produces": ["brief_body_rendered"]},
        {"index": 4, "name": "audit",
         "produces": ["audit_findings"],
         "gate": "computed", "gate_verb": "dossier.audit_gate"},
        {"index": 5, "name": "finalize",
         "produces": ["brief_finalized"], "gate": "hard"},
    ],
}

CORPUS_INGEST_PASS_SKILL = {
    "name": "corpus-ingest-pass", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "source-upload",
         "produces": ["source_registered"]},
        {"index": 2, "name": "chunk",
         "produces": ["chunks_created"]},
        {"index": 3, "name": "extract",
         "produces": ["entities_extracted"],
         "gate": "computed", "gate_verb": "dossier.entity_extraction_gate"},
        {"index": 4, "name": "taxonomize",
         "produces": ["entities_taxonomized"]},
        {"index": 5, "name": "human-review",
         "produces": ["sources_human_curated"], "gate": "hard"},
    ],
}

ENTITY_MAPPING_PASS_SKILL = {
    "name": "entity-mapping-pass", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "infer-candidates",
         "produces": ["candidates_listed"]},
        {"index": 2, "name": "declare-context",
         "produces": ["contexts_declared"]},
        {"index": 3, "name": "coverage",
         "produces": ["coverage_verified"],
         "gate": "computed", "gate_verb": "dossier.context_coverage_gate"},
        {"index": 4, "name": "confirmation",
         "produces": ["mapping_locked"], "gate": "hard"},
    ],
}

SNIPPET_RENDER_PASS_SKILL = {
    "name": "snippet-render-pass", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "select-context",
         "produces": ["context_refs_chosen"]},
        {"index": 2, "name": "select-kind",
         "produces": ["snippet_kind_chosen"]},
        {"index": 3, "name": "render",
         "produces": ["snippet_body_rendered"]},
        {"index": 4, "name": "review",
         "produces": ["snippet_accepted"], "gate": "hard"},
    ],
}
```

### Integration with `research` capability (Spec 044)

The brief capability **delegates outbound search to `research`**:

```python
@verb(role="effect")
def dispatch_research_via_dossier(self, brief_id: str,
                                 specialists: str = "all") -> ToolResult:
    """Brief capability's primary handshake with the research capability.

    Reads the ResearchBrief body + ResearchIntent. For each module
    declared in the brief, dispatches a research.specialist call with
    the module's preferred specialist role + query template.

    Per the 044 contract:
    - research.lead mints a Research node SERVES the intent
    - research.specialist runs per-role searches (codebase /
      prior-reflections / doc-corpus / web)
    - research.verify cross-checks claims

    Citations returned by research.specialist become ResearchEntity
    candidates — fed back into the brief capability's
    extract_entities for taxonomy + context mapping."""
    research_id = self.ctx.call("research", "lead",
                                 question=brief_intent_topic)
    for module in selected_modules:
        for role in module["preferred_roles"]:
            result = self.ctx.call("research", "specialist",
                                    research_id=research_id["research_id"],
                                    role=role,
                                    query=module["query_template"])
            # Materialize citations as ResearchEntities
            for cite in result.get("citations", []):
                entity_id = self.ctx.record("ResearchEntity", {...})
    self.ctx.call("research", "verify",
                   research_id=research_id["research_id"])
```

### Integration with `prompt` capability (Spec 109)

`render_snippet` produces PromptSnippet nodes that
`prompt.engineer` consumes. The handshake:

```python
# In brief capability:
snippet_id = self.ctx.record("PromptSnippet", {
    "body": ..., "snippet_kind": "writing-assist", "entity_refs": [...]
})

# In domain capability (novel, music, ...):
instance = self.ctx.call("prompt", "engineer",
                          builder="chapter",
                          entity_id=f"{novel}:ch{chapter}",
                          context_refs=[snippet_id],   # ← brief snippet
                          ...)
```

### Integration with `thinking` capability (Spec 110)

`dossier.audit` can call `thinking.red_team` for adversarial brief
review:

```python
@verb(role="effect")
def audit(self, brief_id: str,
          include_red_team: bool = False) -> ToolResult:
    """Reader-test simulation. include_red_team=True invokes
    thinking.red_team on the brief for adversarial review (catches
    biased framing, missing counter-evidence, etc.)."""
    audit_findings = self._reader_test(brief_id)
    if include_red_team:
        rt = self.ctx.call("thinking", "red_team",
                            subject=f"brief:{brief_id}")
        audit_findings["red_team_findings"] = rt["attacks"]
    return ToolResult.success(data={"audit_id": ..., **audit_findings})
```

## Migration from novel iter-10 (Spec 105) to brief

Spec 105 (novel research cluster) iter-10 verbs become thin
wrappers / delegations to `brief.*`:

| 105 verb | becomes |
|---|---|
| `research_intent_capture` | wraps `dossier.intent_capture` (sets domain=novel) |
| `ingest_research_source` | wraps `dossier.ingest_source` |
| `chunk_research_source` | wraps `dossier.chunk_source` |
| `extract_entities` | wraps `dossier.extract_entities` |
| `taxonomize_entity` | wraps `dossier.taxonomize_entity` |
| `auto_taxonomize_source` | wraps `dossier.auto_taxonomize_source` |
| `link_entities` | wraps `dossier.link_entities` |
| `declare_chapter_context` | wraps `dossier.declare_context` (scope=chapter) |
| `infer_chapter_context` | wraps `dossier.infer_context` (scope=chapter) |
| `chapter_research_brief` | wraps `dossier.render_brief` (scope_id=chapter) |
| `build_writing_prompt_snippet` | wraps `dossier.render_snippet` |
| `research_brief_audit` | wraps `dossier.audit` |
| `research_catalog_list` | wraps `dossier.catalog_list` |

The novel-specific behaviors (e.g. inferring context from Chapter.beat
nodes) ride OVER the `dossier` capability — the brief returns generic
findings; novel's wrapper adds the domain-specific scoring.

## Why this matters

- **Reusability**: music, screenplay, journalism, legal, academic
  capabilities can each adopt `brief` without re-implementing
  research-prep machinery
- **Provenance**: ResearchEntity nodes SERVE the parent intent — a
  novel's research entities AND a music album's research entities
  share the same audit surface
- **Feed-into-research**: `dossier.dispatch_research_via_dossier`
  delegates outbound search to `research.specialist` — the brief
  capability handles the prep + post-processing; research handles the
  actual search
- **Catalog ecology**: the A/B/C × M01-M12 module catalog is a shared
  reference. Domain caps (novel/music) can register additional
  modules (chapter-mapping, lyric-mapping). The catalog ecology
  grows organically.

## Lifecycle integration (Workflows Core)

User directive (2026-06-07): *"It might also have to be integrated with
Workflows Core capability (lifecycle)."*

Each of the 4 walkable skills (`dossier-intent-pass`, `corpus-ingest-pass`,
`entity-mapping-pass`, `snippet-render-pass`) creates a **Lifecycle**
node per the Spec 080/081 contract. The Lifecycle:

- SERVES the parent intent
- Holds accumulated stage outcomes (intent_yaml → modules → brief →
  entities → contexts → snippets)
- Records gate.check ledger entries at each computed gate
- Pauses on hard gates via `elicit`/`lifecycle_gate`

The four stages compose into a single **DossierWorkflow** Lifecycle
that holds the full ingest-to-snippet pipeline state:

```python
# New node added to ontology (iter-13b):
DossierWorkflow  (slug, intent_ref, scope_ref,
                  intent_yaml_ref, source_refs: list,
                  entity_refs: list, context_refs: list,
                  snippet_refs: list,
                  current_stage, status)
                  # current_stage: intent | corpus | entity | mapping |
                  #                snippet | done
                  # status: working | paused | complete | abandoned
```

The agent can RESUME a DossierWorkflow across sessions — the
Lifecycle records where the pipeline paused (e.g. waiting on
human_review at corpus stage).

### Cross-cap Lifecycle composition

A novel chapter's research uses ALL THREE caps via composed
Lifecycles:

```
DossierWorkflow Lifecycle
  ├─→ Stage 1: dossier.intent_capture
  │     ├─→ thinking.red_team Lifecycle (adversarial brief audit)
  │     └─→ produces: ResearchBrief
  ├─→ Stage 2: dispatch_research_via_dossier
  │     ├─→ research.lead + research.specialist × N (per Spec 044)
  │     └─→ produces: Citations → ResearchEntities
  ├─→ Stage 3: dossier.extract_entities + taxonomize
  ├─→ Stage 4: dossier.declare_context (scope=chapter)
  ├─→ Stage 5: dossier.render_snippet
  │     └─→ produces: PromptSnippet
  └─→ Stage 6: handoff to prompt.engineer
         └─→ prompt-engineering-pass Lifecycle
                └─→ produces: PromptInstance → LLM call → Draft
```

Each cap's Lifecycle SERVES the same parent intent — the full
pipeline is one traversal of `memory.provenance(intent_id)`.

## Failure modes (iter-15 panel fix — Nygard)

### `dispatch_research_via_dossier` cascade legs

| Leg | Failure mode | Driver returns | Verb returns |
|---|---|---|---|
| `research.lead` raises | research not bootable | propagated `BoundaryFailed` | `ToolResult.failure(BOUNDARY_FAILED, "research.lead failed: <msg>")` |
| `research.specialist` × N — partial failure (some succeed, some fail) | `2/N raise` | per-call failure handled | `ToolResult.success(data={research_id, partial=true, succeeded: [...], failed: [...]})` — partial commit; entities created for successful legs only |
| All `research.specialist` calls fail | `N/N raise` | all raised | `ToolResult.failure(BOUNDARY_FAILED, "all specialist calls failed; cascade aborted; no entities created")` |
| `research.verify` raises after entities recorded | post-entity verification fail | propagated | `ToolResult.success(data={research_id, entities_count, verify_failed: true, manual_verification_required: true})` — keep the entities; flag manual verify |
| Network mid-cascade | partial state | retried 1× per leg | falls into "partial failure" path above |
| LLM driver missing for Path B in `extract_entities` | DriverMissing | catches | falls back to Path A rule-based; emits warning |
| LLM driver timeout (Path B) | TimeoutError | catches | falls back to Path A; records `metric: dossier.extract.path=a_fallback` |

**Idempotency**: re-running `dispatch_research_via_dossier` with the
same `brief_id` is idempotent — entity creation checks for existing
EntityTag(`source=research:<research_id>`) and skips dedupes.

### `extract_entities` failure modes

| Failure mode | Behaviour |
|---|---|
| Empty source body | returns `ToolResult.success(data={entities_count: 0, warnings: ["source body empty"]})` — no failure |
| Source body too large (>1MB) | chunks anyway; emits warning; may produce many ResearchChunk nodes |
| Unparseable encoding | returns `ToolResult.failure(INVALID_ARGUMENT, "source body not UTF-8 decodable")` |
| Path B LLM timeout | falls back to Path A; emits warning |
| Path B response in wrong format | falls back to Path A; emits warning |
| All entity kinds yielded 0 entities | `success(data={entities_count: 0, status: "low-yield"})` + WARN metric |

## Test plan

```python
# tests/test_dossier_capability.py — ~22 tests
def test_capability_registers_with_drop_in_bar(): ...
def test_intent_capture_records_research_intent_node(): ...
def test_audit_returns_clarity_score(): ...
def test_dispatch_via_brief_delegates_to_research_lead_and_specialist(): ...
def test_dispatch_via_brief_materializes_citations_as_entities(): ...
def test_ingest_source_creates_source_node_pending(): ...
def test_chunk_source_creates_research_chunk_nodes(): ...
def test_extract_entities_path_a_rule_based(): ...
def test_extract_entities_path_b_routes_through_llm(): ...
def test_taxonomize_entity_creates_tag_node(): ...
def test_link_entities_creates_relation_edge(): ...
def test_declare_context_records_node_with_purpose(): ...
def test_infer_context_ranks_candidates_by_score(): ...
def test_render_brief_produces_artefact_with_renders_from_edge(): ...
def test_render_snippet_caps_at_token_budget(): ...
def test_catalog_list_returns_36_modules_from_yaml(): ...
def test_register_module_adds_domain_specific(): ...
def test_brief_intent_pass_skill_walks_through_audit_gate(): ...
def test_corpus_ingest_pass_skill_walks_through_extraction_gate(): ...
def test_entity_mapping_pass_skill_walks_through_coverage_gate(): ...
def test_snippet_render_pass_skill_pauses_on_hard_gate(): ...
def test_audit_with_red_team_calls_thinking_red_team(): ...
```

## Open questions

1. **Domain-extension pattern**: a domain cap (novel) extending
   `Context.scope` enum to add "chapter" — needs to declare it via
   OntologyExtension (widen-only). v1 supports this; documented in
   the migration spec.
2. **Per-domain catalog modules**: a domain cap may register
   additional CatalogModule nodes via `register_module` — but the
   base 36 (A/B/C × M01-M12) ship with `brief`.
3. **research → brief feedback loop**: when `research.specialist`
   produces citations, dossier.extract_entities materializes them as
   ResearchEntities. The reverse (brief sends signal back to
   research about which citations were USEFUL) is a v2 enhancement.
4. **Multi-novel / multi-domain shared corpus**: a writer with both a
   novel AND a music album in the same world (transmedia) can share
   a corpus. v1 scopes corpus per-intent; v2 may add multi-intent
   sharing.

## Followup

(Populated when the PR ships.)
