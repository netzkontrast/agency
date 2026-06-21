---
spec_id: "105"
slug: novel-research-cluster
status: draft
state: inprogress
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["102", "101", "044"]
affects:
  - agency/capabilities/novel/clusters/research.py
  - agency/capabilities/novel/ontology.py       # ResearchClaim, VerificationRecord reused from 099
  - agency/capabilities/novel/data/reference/research-domains.yaml
  - tests/test_novel_research.py
domain: novel / research / delegation
wave: 8
parent_spec: "101"
mvp-source:
  - "Plan/_research/novel-mvp-source/references/parity-table.md (10 researchers-* verbatim carry-over)"
  - "Plan/099 music-research-cluster (the proven pattern)"
---

# Spec 105 — Novel Research Cluster

## Why

Per the imported Novel-Craft Parity Table: **researcher subroles carry
over verbatim from music** — domain research is medium-agnostic. 105 ports
099's design pattern with the 10-domain registry retuned for novels:

- **historical** · **biographical** · **forensic** · **scientific** ·
  **geographic** · **cultural** · **occupational** · **mythological** ·
  **journalism** · **primary-source**
- + `document-hunter` + `verify-sources` (verbatim carry-over)
- + `researchers-verifier` (verbatim carry-over)

Like 099, 105 delegates the heavy lifting to `agency.research` (Spec 044:
`lead` / `specialist` / `verify`) and adds music-domain-style mapping.

## Done When

- [ ] **8 user-facing verbs ship** (research-scope, dispatch-research,
      capture-claim, verify-sources, list-claims, pending-verifications,
      human-signoff, document-hunt — mirror 099's verb set).
- [ ] **1 composite gate verb** ships: `verify_gate` (called by 108's
      `pre-draft` skill phase).
- [ ] **Domain registry** at `data/reference/research-domains.yaml`
      carries the 10 novel-domain configurations.
- [ ] **ResearchClaim + VerificationRecord nodes** reused from 099's
      ontology (declared in 102's consolidated extension).
- [ ] **Walkable skill `research-workflow` ships** (5 phases — verbatim
      adapted from 099).
- [ ] **`scripts/test-cap novel`** Green for novel-research tests.
- [ ] **`TODO.md` updated** with 105 row.

## Verb manifest

Mirrors 099 verbatim (every verb name preserved):

| # | Verb | Role | Delegate / Driver |
|---|---|---|---|
| 1 | `research_scope` | act | (delegate to scope-research lead) |
| 2 | `dispatch_research` | effect | agency.research.lead + agency.research.specialist × N |
| 3 | `capture_claim` | effect | (graph) — records `ResearchClaim` node SERVES intent |
| 4 | `verify_sources` | effect | agency.research.verify + TextDriver |
| 5 | `list_claims` | transform | (graph) — filter by novel/status |
| 6 | `pending_verifications` | transform | (graph) — aggregates `pending` claims |
| 7 | `human_signoff` | effect | (graph) + `elicit` |
| 8 | `document_hunt` | effect | agency.research.specialist (role="web", domain-prompted) |

**Internal gate**:

| # | Verb | Composes |
|---|---|---|
| G1 | `verify_gate` | list_claims(verified="pending") count + gate.check (BLOCKED_ON if > 0) |

**Total: 8 user + 1 gate = 9 registered verbs.**

## Design

### Domain registry (`data/reference/research-domains.yaml`)

```yaml
domains:
  historical:
    description: archives, contemporary accounts, timeline reconstruction
    preferred_sources: [archive.org, jstor, loc.gov, gutenberg.org]
    verifier_strictness: medium
    typical_novels: [historical fiction, alt-history, period thrillers]
  biographical:
    description: personal backgrounds, interviews, motivations
    preferred_sources: [linkedin, wikipedia, biography.com, oralhistory.org]
    verifier_strictness: low
    typical_novels: [biographical fiction, literary]
  forensic:
    description: crime-scene procedures, autopsy reports, investigative methodology
    preferred_sources: [doj.gov, fbi.gov, gianthoptodd.com, pubmed]
    verifier_strictness: high
    typical_novels: [thriller, crime, police procedural]
  scientific:
    description: physics, biology, chemistry; lab procedures
    preferred_sources: [pubmed, arxiv, nature, science]
    verifier_strictness: high
    typical_novels: [hard SF, technothriller, medical fiction]
  geographic:
    description: regional setting, climate, flora/fauna, languages
    preferred_sources: [nationalgeographic, openstreetmap, ethnologue]
    verifier_strictness: medium
    typical_novels: [literary, travel, regional]
  cultural:
    description: religious / ethnic / folk practices; festivals; food
    preferred_sources: [encyclopedia, jstor, owned-by-community-orgs]
    verifier_strictness: high
    typical_novels: [diaspora, multicultural, magical realism]
  occupational:
    description: trade-specific procedures (military, medical, legal, blue-collar)
    preferred_sources: [trade-magazines, professional-bodies]
    verifier_strictness: medium
    typical_novels: [procedural, workplace, war]
  mythological:
    description: world religions, folklore, mythology
    preferred_sources: [sacred-texts.com, encyclopedia-mythica, jstor]
    verifier_strictness: low
    typical_novels: [fantasy, magical realism, retelling]
  journalism:
    description: news coverage of real events the novel fictionalizes
    preferred_sources: [nytimes, propublica, reuters, ap]
    verifier_strictness: medium
    typical_novels: [literary, ripped-from-headlines thriller]
  primary_source:
    description: subject's own words — letters, diaries, blogs (for living people)
    preferred_sources: [twitter, github, archive.org, blog-archives]
    verifier_strictness: high
    typical_novels: [biographical, historical-figure-as-protagonist]
```

### Delegation pattern

Verbatim from 099's iteration-6 corrected pattern:

```python
@verb(role="effect")
def dispatch_research(self, question: str, domains: str = "all",
                      novel: str = "") -> ToolResult:
    """Drive agency.research.lead → N agency.research.specialist calls →
    agency.research.verify. Maps novel's 10 domains onto the shipped
    {codebase|prior-reflections|doc-corpus|web} role enum via
    domain-prompted queries.
    """
    state = self.ctx.get_driver("music_state")
    domain_registry = state.read_data("research-domain", "all")
    selected = (list(domain_registry["domains"].keys()) if domains == "all"
                else [d.strip() for d in domains.split(",")])

    lead = self.ctx.call("research", "lead",
                         question=question, depth="standard")
    research_id = lead["research_id"]

    for novel_domain in selected:
        cfg = domain_registry["domains"][novel_domain]
        role = "web" if cfg.get("preferred_sources") else "doc-corpus"
        domain_query = (f"[domain={novel_domain}] {question}\n"
                        f"Preferred sources: {cfg.get('preferred_sources', [])}\n"
                        f"Style: {cfg.get('description', '')}")
        result = self.ctx.call("research", "specialist",
                               research_id=research_id, role=role,
                               query=domain_query, k=cfg.get("k", 5))
        for cite in result.get("citations", []):
            claim_id = self.ctx.record("ResearchClaim", {
                "text": cite.get("snippet", ""),
                "source_uri": cite.get("uri", ""),
                "domain": novel_domain,
                "confidence": cite.get("confidence", 0.5),
                "verified": "pending",
                "captured_at": int(time.time())})
            self.ctx.link(claim_id, self.ctx.intent_id, "SERVES")
            if novel:
                hits = state.find_novel(novel)
                if hits:
                    self.ctx.link(claim_id, hits[0]["id"], "RELATES_TO")

    self.ctx.call("research", "verify", research_id=research_id)
    return ToolResult.success(data={"research_id": research_id,
                                    "novel": novel,
                                    "domain_count": len(selected)})
```

### Walkable skill: `research-workflow`

5 phases, verbatim from 099:
- scope → dispatch-specialists → collect → verify → human-signoff (hard).

## Test plan

```python
# tests/test_novel_research.py — ~8 tests
def test_research_cluster_discovers_all_verbs(): ...
def test_dispatch_research_delegates_to_agency_research(): ...
def test_dispatch_research_handles_all_10_novel_domains(): ...
def test_capture_claim_records_ResearchClaim_node_with_captured_at(): ...
def test_verify_sources_flips_claim_status(): ...
def test_pending_verifications_filters_by_novel_and_status(): ...
def test_document_hunt_specializes_to_primary_source_domain(): ...
def test_research_workflow_skill_pauses_on_human_signoff_hard_gate(): ...
def test_verify_gate_blocks_when_pending_claims_remain(): ...
```

## Research-prompt-optimizer pattern (iteration 12 — critical-thinking pass)

Per the imported `Plan/_research/novel-mvp-source/research-prompt-
optimizer/agentic-tool-catalog.md`, the agency ecosystem ships a
5-tool research-brief discipline. iter-12 ports the **Phase 0 intent
capture** + **catalog list** + **brief audit** verbs to the novel
research cluster, bringing the rigor of the research-prompt-optimizer
to per-novel research before ingestion runs.

### The 5-phase research-prompt-optimizer pattern

| Phase | Tool | Kind | Brought to novel |
|---|---|---|---|
| 1 — Intent capture | `research_intent_capture(seed_query)` | LLM-needed | ✓ `research_intent_capture` (105 iter-12) |
| 2 — Brief render | `research_brief_render(intent, modules)` | Decidable | maps to `chapter_research_brief` (105 iter-10 existing) |
| 3 — Brief audit | `research_brief_audit(brief)` | LLM-needed | ✓ `research_brief_audit` (105 iter-12) |
| 4 — Finalize | `research_brief_finalize(brief, zip)` | Decidable | maps to `export_full_archive` (107 iter-9 existing) |
| 5 — Catalog | `research_catalog_list(category)` | Decidable | ✓ `research_catalog_list` (105 iter-12) |

### Three new verbs in 105 (iter-12)

```python
@verb(role="act")
def research_intent_capture(self, novel: str,
                            seed_query: str) -> ToolResult:
    """Phase 0 of the iter-10 pipeline (was previously implicit).
    Turn a free-form seed query into a structured intent YAML:
    {topic, sub_topics, depth, deliverable, success_criteria,
     deadline, audience}.

    The intent drives the ingestion + extraction stages — it tells
    extract_entities WHICH entity kinds matter, tells
    chapter_research_brief what shape the output should take, and
    feeds the A/B/C module-catalog (next verb).

    Path A (rule-based): parses the seed_query for key terms +
    matches against the A/B/C × M01-M12 catalog modules to seed
    the intent.

    Path B (LLM-assisted): routes through the `llm` driver for
    richer intent extraction. Opt-in via [novel-llm] extra or
    per-call llm=True parameter.

    Records ResearchIntent node SERVES the parent intent."""

@verb(role="transform")
def research_catalog_list(self, category: str = "") -> ToolResult:
    """Per the agentic-tool-catalog A/B/C × M01-M12 module taxonomy:
    A = foundational research modules (4-axis primary sources)
    B = extension modules (cross-domain synthesis)
    C = synthesis modules (writer-facing briefs)
    M01-M12 = specific module identifiers (per the upstream catalog)

    Returns the catalog modules matching the category filter. Used by
    chapter_research_brief to select which modules apply per chapter.

    Catalog source: data/reference/research-modules/catalog.yaml
    (ships in 102 base PR — verbatim from the imported catalog)."""

@verb(role="effect")
def research_brief_audit(self, brief_artefact_slug: str) -> ToolResult:
    """Reader-test simulation: can a fresh reader locate task,
    constraints, deliverable, success criteria from the brief?

    Uses the `llm` driver if bound; falls back to rule-based check
    that searches for the 4 mandatory headings (Task, Constraints,
    Deliverable, Success Criteria).

    Records a BriefAudit node with {found_sections, missing_sections,
    clarity_score, recommended_revisions}. The 105's
    `chapter-context-build` walkable skill consumes the audit
    findings at its confirmation phase."""
```

### Three new nodes (declared in 102's consolidated extension)

```python
ResearchIntent  (slug, novel, seed_query, topic, sub_topics,
                 depth, deliverable, success_criteria,
                 deadline, audience, generated_by)
CatalogModule   (slug, category, identifier, name, body, deps)
                # category: A | B | C
                # identifier: M01..M12 (or extended)
BriefAudit      (slug, brief_artefact, found_sections,
                 missing_sections, clarity_score,
                 recommended_revisions, audited_at, audited_by)
```

### Catalog data file (ships with 102 base PR)

`agency/capabilities/novel/data/reference/research-modules/catalog.yaml`
holds the A/B/C × M01-M12 module definitions. Verbatim from the
imported `Plan/_research/novel-mvp-source/research-prompt-optimizer/
agentic-tool-catalog.md` §1.4 (the 36 catalog entries).

### Walkable skill update — `research-ingest-pipeline` now 6 phases

Iter-10's 5-phase skill is extended with Phase 0 intent capture at
the front:

```python
RESEARCH_INGEST_PIPELINE_SKILL_v2 = {
    "name": "research-ingest-pipeline",
    "kind": "workflow",
    "phases": [
        {"index": 0, "name": "intent-capture",
         "produces": ["research_intent_recorded"]},
        {"index": 1, "name": "source-upload",
         "produces": ["source_registered"]},
        {"index": 2, "name": "chunk",
         "produces": ["chunks_created"]},
        {"index": 3, "name": "extract",
         "produces": ["entities_extracted"],
         "gate": "computed", "gate_verb": "novel.entity_extraction_gate"},
        {"index": 4, "name": "taxonomize",
         "produces": ["entities_taxonomized"]},
        {"index": 5, "name": "brief-audit",
         "produces": ["briefs_audited"],
         "gate": "computed", "gate_verb": "novel.brief_audit_gate"},
        {"index": 6, "name": "human-review",
         "produces": ["sources_human_curated"], "gate": "hard"},
    ],
}
```

Phase 0 + Phase 5 are the iter-12 additions; the rest are iter-10
verbatim. New computed gate `brief_audit_gate` ensures every research
brief passes reader-test simulation before human review.

### Why this matters

Without intent capture (Phase 0), the iter-10 ingestion runs without
direction — pulling everything from a source instead of the relevant
shape. The intent YAML focuses extraction: a novel about "the ethics
of artificial general intelligence" with sub-topic "consequentialist
vs deontological frameworks" produces TARGETED entities (Mill, Kant,
Bostrom, Yudkowsky), not the universe of AI-ethics writing.

Without brief audit (Phase 5), briefs render but their CLARITY is
unverified — the writer downloads a 50-page brief that's structurally
incoherent. The audit catches this BEFORE the writer wastes time
reading.

The catalog (M01-M12) provides reusable module templates so a brief
covers known shapes (historical-context, primary-sources, opposing-
views, contemporary-debate, etc.) — the writer doesn't have to
remember what a "complete" brief looks like.

## Complex research → world-ontology workflows (iteration 10)

Per user directive (2026-06-07): *"we Need Complex Research World
Ontology Workflows — to ingest background Research (Physics, Philosophy,
etc...) and we Need a way to map those into Chapters. Also a way to
rebuild it into entities tagged to address specific aspects we can
directly use as prompt snippet for writing assist."*

This extends the cluster from "claim verification" (ResearchClaim per
099) to **research-informed writing assistance**: bring in long-form
research material, extract structured entities, map them to chapters,
and rebuild as prompt snippets the LLM-driver consumes during chapter
drafting.

### Four-stage pipeline

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────┐    ┌────────────────────┐
│ Stage 1: INGEST     │ →  │ Stage 2: EXTRACT     │ →  │ Stage 3: MAP    │ →  │ Stage 4: RENDER    │
│ research sources    │    │ entities + taxonomy  │    │ to chapters     │    │ prompt snippets    │
│ (PDFs, books, URLs) │    │ (concept / mechanism │    │ (declared or    │    │ for writing-assist │
│                     │    │  / quote / etc.)     │    │  inferred)      │    │                    │
└─────────────────────┘    └──────────────────────┘    └─────────────────┘    └────────────────────┘
     ResearchSource             ResearchEntity            ChapterContext         PromptSnippet
     ResearchChunk              EntityTag                                       (entity_refs[])
                                EntityRelation
```

### Stage 1 — Ingest research sources (4 verbs)

```python
@verb(role="effect")
def ingest_research_source(self, novel: str, source_uri: str,
                           kind: str = "paper",
                           title: str = "",
                           author: str = "",
                           year: int = 0) -> ToolResult:
    """Upload a research source for the novel. URI may be a URL (fetched
    via web), a local path (read via StateDriver), or an S3/R2 key
    (fetched via CloudDriver). Creates a ResearchSource node with
    ingestion_status='pending'. Returns source_slug."""

@verb(role="effect")
def chunk_research_source(self, source_slug: str,
                          chunker: str = "paragraph") -> ToolResult:
    """Walk the source body; produce ResearchChunk nodes. Chunker
    options: paragraph (default — splits on \\n\\n), section (splits on
    # heading), or sliding (overlapping window for long-form). Updates
    ingestion_status='chunked'."""

@verb(role="transform")
def list_research_sources(self, novel: str,
                          kind: str = "",
                          status: str = "") -> ToolResult: ...

@verb(role="effect")
def reingest_source(self, source_slug: str,
                    new_uri: str = "") -> ToolResult:
    """Re-ingest a source (e.g. a revised paper). Old chunks marked
    `superseded`; new chunks created; entities re-extracted with
    SUPERSEDES edges back to the old entities."""
```

### Stage 2 — Extract entities + taxonomy (5 verbs)

```python
@verb(role="effect")
def extract_entities(self, source_slug: str,
                     kinds: str = "all") -> ToolResult:
    """Walk every ResearchChunk in the source; extract entities.
    kinds: 'all' (default), or comma-separated subset (concept,
    mechanism, definition, example, counterexample, lineage, theorem,
    anecdote, quote, analogy, empirical-fact).

    Two extraction paths:
    - Path A (default — rule-based): pattern-match for known shapes
      (Definition: "X is defined as Y"; Quote: "...quotation marks...";
      Mechanism: "Process: A → B → C")
    - Path B (LLM-assisted): routes through the `llm` driver to
      extract semantically — better recall on free-form prose. Opt-in
      via [novel-llm] extra or per-call llm=True parameter.

    Records ResearchEntity nodes + EXTRACTED_FROM edges. Updates
    source.ingestion_status='extracted'."""

@verb(role="effect")
def taxonomize_entity(self, entity_slug: str,
                      taxonomy: str = "subject",
                      tag: str = "") -> ToolResult:
    """Add an EntityTag to an entity. Multiple tags per (entity,
    taxonomy) allowed. Common taxonomies: subject, discipline, era,
    author, applicability, mood."""

@verb(role="effect")
def auto_taxonomize_source(self, source_slug: str) -> ToolResult:
    """Run rule-based + optional LLM-assisted taxonomy across every
    entity from the source. Reads the source.kind + source.title +
    source.author to seed default tags (e.g. a Kant book auto-tags
    `discipline=philosophy`, `era=enlightenment`, `author=kant`)."""

@verb(role="effect")
def link_entities(self, source_entity_slug: str,
                  target_entity_slug: str,
                  relation_kind: str) -> ToolResult:
    """Declare an EntityRelation between two entities. relation_kind:
    depends-on / contradicts / illustrates / refines / derives-from /
    inspired-by."""

@verb(role="transform")
def list_entities(self, source: str = "",
                  kind: str = "",
                  tag: str = "",
                  taxonomy: str = "") -> ToolResult:
    """Query entities by source / kind / tag / taxonomy. Returns
    {entities: [{slug, kind, name, body, tags, relations}]}. Body
    capped at ~200 chars for list views; full body via get_entity."""
```

### Stage 3 — Map entities to chapters (4 verbs)

```python
@verb(role="effect")
def declare_chapter_context(self, novel: str, chapter: int,
                            entity_slug: str,
                            weight: float = 1.0,
                            purpose: str = "backbone") -> ToolResult:
    """Declare that a chapter needs an entity. purpose options:
    - backbone: foundational; the chapter's thematic spine relies on this
    - flavor: surface detail; cited or referenced
    - factcheck: verifiable claim the chapter makes
    - counterpoint: an entity the chapter ARGUES AGAINST
    - metaphor-source: source for the chapter's metaphor system

    Creates ChapterContext node + CONTEXTUALIZES edge with
    declared_or_inferred='declared'."""

@verb(role="transform")
def infer_chapter_context(self, novel: str,
                          chapter: int) -> ToolResult:
    """Auto-suggest entities relevant to a chapter. Reads:
    - The chapter's beats (102 Beat nodes)
    - The chapter's POV character (their declared interests via Character.
      voice_signature tags)
    - The chapter's outline_position (act 1 / midpoint / act 3 has
      different research density profiles)
    - The chapter's existing prose body (if drafted) — extracts terms
      that match entity names/tags

    Returns ranked {entity_slug, score, suggested_purpose} list with
    declared_or_inferred='inferred'. Does NOT write — the agent reviews
    and selectively `declare_chapter_context`s the accepted suggestions."""

@verb(role="transform")
def chapter_research_brief(self, novel: str,
                           chapter: int,
                           format: str = "markdown") -> ToolResult:
    """Render the full research brief for a chapter. Includes:
    - Every ChapterContext entity grouped by purpose
    - Each entity's body + tags + key relations
    - Source attribution (which ResearchSource per entity)
    - Quote snippets ready for inclusion as epigraphs

    format: markdown (default) | json | prompt-bundle
    The artefact kind is 'research-brief'."""

@verb(role="transform")
def context_coverage_report(self, novel: str) -> ToolResult:
    """For the whole novel: which chapters have research context declared
    (or inferred) vs which are research-light. Identifies entities
    referenced in MULTIPLE chapters (indicates a load-bearing concept)
    vs entities used once (incidental). Used by 108's pre-draft gate
    when novel.research_density='heavy' is declared."""
```

### Stage 4 — Render prompt snippets for writing-assist (3 verbs)

```python
@verb(role="transform")
def build_writing_prompt_snippet(self, novel: str, chapter: int,
                                  scene: str = "",
                                  snippet_kind: str = "writing-assist",
                                  token_budget: int = 1500) -> ToolResult:
    """The headline writing-assist verb. Given a chapter (and optionally
    a specific scene), bundle relevant entities into a prompt snippet
    the LLM driver consumes during chapter_draft_assisted (104).

    Snippet kinds:
    - writing-assist: general drafting context (all relevant entities)
    - dialogue-prompt: entities a character would reference in dialogue
    - description-prompt: entities for sensory/spatial description
    - exposition-prompt: backbone entities for exposition passages
    - metaphor-prompt: metaphor-source entities

    Ranking:
    - 1. weight (ChapterContext.weight, declared) — highest priority
    - 2. inferred relevance (semantic similarity if llm available;
         else tag-overlap)
    - 3. recency (entities tagged with current chapter's scene_time)

    Output is the rendered snippet body (markdown — bullets per entity
    + relations + source attribution). Cap at token_budget. Returns
    PromptSnippet node id + body.

    Used by 104's chapter_draft_assisted: passes the snippet body as
    the LLM context prefix."""

@verb(role="effect")
def cache_prompt_snippet(self, novel: str, chapter: int,
                         scene: str,
                         snippet_kind: str) -> ToolResult:
    """Materialize a built snippet as a PromptSnippet node. Caches the
    build to avoid recomputation when the same chapter is drafted
    repeatedly. The cache invalidates when ChapterContext changes."""

@verb(role="transform")
def list_prompt_snippets(self, novel: str,
                         chapter: int = 0,
                         snippet_kind: str = "") -> ToolResult:
    """Discover existing cached snippets."""
```

### Walkable skill: `research-ingest-pipeline` (5 phases)

The full pipeline as a walkable workflow:

```python
RESEARCH_INGEST_PIPELINE_SKILL = {
    "name": "research-ingest-pipeline",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "source-upload",
         "produces": ["source_registered"]},
        {"index": 2, "name": "chunk",
         "produces": ["chunks_created"]},
        {"index": 3, "name": "extract",
         "produces": ["entities_extracted"],
         "gate": "computed", "gate_verb": "novel.entity_extraction_gate"},
        {"index": 4, "name": "taxonomize",
         "produces": ["entities_taxonomized"]},
        {"index": 5, "name": "human-review",
         "produces": ["sources_human_curated"], "gate": "hard"},
    ],
}
```

### Walkable skill: `chapter-context-build` (4 phases)

Per-chapter context-mapping workflow:

```python
CHAPTER_CONTEXT_BUILD_SKILL = {
    "name": "chapter-context-build",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "infer-candidates",
         "produces": ["candidates_listed"]},
        {"index": 2, "name": "declare-context",
         "produces": ["contexts_declared"]},
        {"index": 3, "name": "build-snippet",
         "produces": ["snippet_built"]},
        {"index": 4, "name": "confirmation",
         "produces": ["context_locked"], "gate": "hard"},
    ],
}
```

### TextDriver method delta

```python
class TextDriver(Boundary):
    # iteration-10 additions for research-entity work
    def chunk_text(self, body: str,
                   strategy: str = "paragraph") -> list[dict]: ...
    def extract_definitions(self, chunk: str) -> list[dict]: ...
    def extract_quotes(self, chunk: str) -> list[dict]: ...
    def extract_mechanisms(self, chunk: str) -> list[dict]: ...
    def tag_entity_auto(self, entity_body: str,
                        seed_tags: dict) -> list[dict]: ...
    def rank_entities_for_chapter(self, chapter_body: str,
                                  entity_pool: list[dict]) -> list[tuple]: ...
        # returns [(entity_slug, score), …] sorted by relevance
    def render_prompt_snippet(self, entities: list[dict],
                              snippet_kind: str,
                              token_budget: int) -> str: ...
```

### Integration with 104 prose

`chapter_draft_assisted` (104 Path B) gains an `inject_prompt_snippet`
parameter:

```python
# In 104 — extended call signature:
@verb(role="act")
def chapter_draft_assisted(self, novel: str, chapter: int,
                           outline_beats: str = "",
                           inject_prompt_snippet: bool = True
                           ) -> ToolResult:
    """Path A scaffold; Path B with LLM. When inject_prompt_snippet=True
    and a PromptSnippet exists for this chapter, prepend the snippet's
    body to the LLM prompt as context. The snippet replaces the
    `voice_notes` slot in the existing prompt template."""
```

### Integration with 105 base dispatch_research

The existing `dispatch_research` verb (105 base) can OPTIONALLY feed
its citations into the entity-extraction stage:

```python
@verb(role="effect")
def materialize_claims_as_entities(self, research_id: str) -> ToolResult:
    """For every ResearchClaim produced by dispatch_research, create a
    ResearchEntity (kind='quote' or 'empirical-fact') so claims can
    flow into the entity → context → snippet pipeline. Bridges the
    099-pattern (claim verification) with the iter-10 pattern
    (writing assist)."""
```

### Test plan

```python
# tests/test_novel_research_ontology.py — ~16 tests
def test_ingest_research_source_creates_source_node(): ...
def test_chunk_research_source_paragraph_strategy(): ...
def test_chunk_research_source_section_strategy(): ...
def test_extract_entities_path_a_rule_based_definitions(): ...
def test_extract_entities_path_b_routes_through_llm_when_bound(): ...
def test_taxonomize_entity_records_entitytag_node(): ...
def test_auto_taxonomize_source_seeds_from_metadata(): ...
def test_link_entities_records_relation_edge(): ...
def test_declare_chapter_context_records_node_with_purpose(): ...
def test_infer_chapter_context_ranks_by_score(): ...
def test_chapter_research_brief_renders_markdown(): ...
def test_chapter_research_brief_renders_prompt_bundle(): ...
def test_build_writing_prompt_snippet_caps_at_token_budget(): ...
def test_build_writing_prompt_snippet_respects_snippet_kind(): ...
def test_cache_prompt_snippet_invalidates_on_context_change(): ...
def test_research_ingest_pipeline_walks_to_human_review_gate(): ...
def test_chapter_context_build_pauses_on_confirmation_hard_gate(): ...
def test_materialize_claims_bridges_099_into_iter10(): ...
def test_chapter_draft_assisted_consumes_snippet_when_present(): ...
```

### Performance notes

- Entity extraction (Path A rule-based) ≤ 20ms per ResearchChunk
- Path B (LLM-assisted) is opt-in; latency depends on LLM driver
- Chapter-context inference ≤ 50ms per chapter (depends on entity pool size)
- Prompt-snippet build ≤ 30ms per snippet (cached after first build)
- `chapter_research_brief` for a 100-entity novel ≤ 200ms

### Doctrine notes

1. **Entities are NOT translations of source prose.** ADR-1's
   no-translation rule applies: entity bodies preserve source language;
   `extract_language` is run on entity body during extraction. A
   German-source entity in a German-canon novel keeps both German.
   An English-source entity in a German-canon novel STAYS English; the
   author decides how to integrate it (paraphrase / quote / footnote).

2. **AI-use disclosure (ADR-7) tracks entity provenance.** Every
   ResearchEntity carries `generated_by`: `human` (manually extracted),
   `agent` (rule-based extraction), `llm` (Path B extraction).
   The AI-use report (104) factors entity-derived prose into its
   per-source breakdown.

3. **No prompt-snippet leaks canon prose.** Prompt snippets are
   research entities + author-curated body fields. They do NOT include
   the novel's draft prose. This preserves the "canon prose is not
   training data" discipline that protects the author's voice.

## Genre-conditional dispatch (iteration 3)

A novel's `Novel.genres: list[str]` field implies which research domains
matter MOST. The cluster ships a transform helper:

```python
@verb(role="transform")
def suggest_domains_for_genre(self, genre: str) -> ToolResult:
    """Map genre → recommended research domains. Reads
    data/reference/research-domains.yaml where each domain declares
    typical_novels: list[str]. Returns a ranked-by-relevance domain list
    that dispatch_research consumes as its default `domains` arg.
    """
```

Examples:
- `historical fiction` → [historical, biographical, cultural, geographic]
- `thriller` → [forensic, occupational, scientific, journalism]
- `hard SF` → [scientific, occupational, geographic]
- `fantasy` → [mythological, historical (real-world inspiration), cultural]
- `literary` → [biographical, cultural, geographic, occupational]

Multi-genre novels get the UNION (no dedup beyond exact-match).

## Open questions

1. **Research domain registry — closed enum or open set?** Closed for v1
   (same as music). Adding a domain is a small YAML + ontology change.
2. **Pre-draft gate**: 108's `pre-draft` skill calls `verify_gate` to
   enforce "no drafting until research is human-confirmed". Tested via
   the E2E in 108.
3. **Web specialist gap**: Spec 044 reserved the slot but doesn't bind a
   default. 105 inherits — production binds via `[research-web]`; CI
   stubs `{citations: [], summary: ""}`.

## Followup — Implementation Status (2026-06-09)

**Slice 1 SHIPPED** on branch `claude/spec-102-novel-lifecycle` (PR #80).

### Done in Slice 1

3 graph-only research verbs in `agency/capabilities/novel/_main.py`:
- `capture_claim(text, source_uri, domain)` (effect): records a
  `NovelClaim` node with SERVES edge to the intent; validates `domain`
  against `RESEARCH_DOMAINS` enum (10 novel-domain set).
- `list_claims(verified="")` (transform): filter by verification status;
  `INVALID_ARGUMENT` on unknown status.
- `pending_verifications()` (transform): aggregates pending claims
  grouped by domain.

Ontology delta:
- `NovelClaim` node with schema `["text", "source_uri", "domain"]`
- `CLAIM_VERIFIED` enum constraining `("NovelClaim", "verified")`
  values: pending / confirmed / refuted / needs-source
- `RESEARCH_DOMAINS` enum (10 novel-domain set, parallel to music's 099):
  historical / scientific / cultural / geographical / linguistic /
  philosophical / religious / political / technological / biographical

`tests/test_novel_research.py` NEW: 9 tests covering verb registration,
NovelClaim node + enum bite, capture_claim happy path + invalid domain,
list_claims filter + invalid verified, pending_verifications aggregate.

### Deferred to Slice 2+

- 5 delegating verbs (`research_scope`, `dispatch_research`,
  `verify_sources`, `document_hunt`, `human_signoff`) — these call
  `ctx.call("research", …)` and need a wired agency.research stack
  with a research-bearing intent.
- Composite `verify_gate` (composes `list_claims(verified="pending")`
  count + `gate.check`; BLOCKED_ON when > 0).
- `research-workflow` 5-phase walkable skill (verbatim from 099 but
  novel-targeted).
- `data/reference/research-domains.yaml` data port (10 domain configs
  with preferred sources and verification heuristics).
- Verification record node + edge wiring for evidence chains.

### Done When status

3 of 7 Done-When boxes ticked (3 of 8 verbs; NovelClaim ontology;
9 tests of the ~12 target). The remaining 4 (delegating verbs +
composite gate + walkable skill + domains data) gate on agency.research
wiring against a research-bearing novel intent.

(Populated when the PR ships.)
