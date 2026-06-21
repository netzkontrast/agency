---
spec_id: "113"
slug: research-ingestion-port
status: draft
state: inprogress
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["109", "110", "112"]
gated_by: ["109 → Shipped", "110 → Shipped", "112 → Shipped"]
affects:
  - agency/capabilities/dossier/data/imports/    # the ingested entities land here
  - tests/test_research_ingestion_port.py
source-material:
  - "Plan/_research/agency-system-import/ (447 files imported under iter-14)"
  - "Plan/_research/agency-system-import/SOURCES.md (canonical source-repos table)"
  - "Plan/_research/agency-system-import/Plan-_session-state/ (15 research sessions from 2026-05-18 surveying SuperClaude, superpowers, claude-context)"
  - "Plan/_research/agency-system-import/vision/RESEARCH-PATTERNS.md × 3 (agentic/workflow/context columns)"
  - "Plan/_research/agency-system-import/INDEX.md (10 architectural patterns identified)"
domain: substrate / research-ingestion / port-completion
wave: 9
research_first: true
---

# Spec 113 — Research-Ingestion Port (instruction-set for an MCP code-mode agent)

## Why

User directives (2026-06-07):

1. *"Create a Spec that instructs to do further Research in the repo -
   also in all Reprise the sources.md file in plan or Vision captures
   (line superclaude and superpowers etc..) … Look for Research
   documents - in Plan - because there we have additional Knowledge
   about Harness in Harness and different Context and prompt
   Engineering SOTA practices - we also want to Port - but for now -
   only copy them - and Write a Spec that ingests them once the
   critical thinking and prompt Engineering Parts Are funktional.
   Those Need to be able to instruct an Agent like you - via mcp Code
   Mode - with step by step instructions (those instructions Need to
   map back onto mcp calls)."*

2. *"The agency system is an older approach - we only use what fits
   the current Vision and goal and Architecture."*

3. *"Er nicht want to consider the Agentic Workflow context as
   Structural blueprint for the Agency Plugin… we currently use Verbs
   - Like Act, transform and so on that cleanly map into that Matrix
   Concept."*

### What changed from "complete port" to "selective port"

Per directive 2: the agency-system represents an OLDER architectural
approach. The right discipline is **selective port**: ingest the
material, surface patterns, evaluate against current vision/goal/
architecture, port ONLY what fits. Not blanket adoption.

### The 3×N matrix as structural blueprint candidate (per directive 3)

The agency-system's 3×N matrix (agentic / workflow / context columns ×
N domain rows) is a candidate structural blueprint for agency. The
existing role-tag system (act / transform / effect) appears to map
cleanly:

| Role tag | Likely column | Why |
|---|---|---|
| `act` | agentic | Skill-level action; produces an artefact + advances narrative |
| `transform` | context | Pure read/compute; queries graph + ontology |
| `effect` | workflow | Side-effecting; advances pipeline + mutates lifecycle state |

The mapping is provisional — ingestion + critical-thinking review will
sharpen it. If confirmed, agency's existing verb canon becomes a
shorthand for the matrix's column-positioning. Adoption decision is
deferred to a follow-up spec (likely Spec 114).

### What this spec produces

Iteration 14 imported source material from
`netzkontrast/the-agency-system` under
`Plan/_research/agency-system-import/` (~433 files after .py removal
in iter-15). The material includes:

- The **3×N matrix charter** + 14 vision specs (architecture)
- 15 **research session docs** surveying SuperClaude Framework,
  superpowers, claude-context, FastMCP, multi-agent patterns
- 3 **RESEARCH-PATTERNS.md** (one per column: agentic / workflow / context)
- The full **SOURCES.md** with canonical source-repos table
- 60K of code reviews + 9 phase folders + 10 numbered specs + lessons-
  learned + decisions + harness research

**This spec does NOT ingest the material now.** It captures the
instruction-set so an MCP code-mode agent can ingest it AFTER 109
(prompt), 110 (thinking), and 112 (dossier) are functional.

The spec is **agent-actionable**: every phase below is an MCP code-mode
block. Each `await call_tool(...)` maps to a concrete agency verb.

### Selective-port discipline (iter-15 sharpened — concrete checklists)

Per directive 2, every pattern surfaced during ingestion goes through
a 3-stage filter BEFORE port. Each filter is a **6-question checklist**
producing a Y/N answer; ANY N triggers "catalogue for reference, do
not port":

#### Filter 1 — Vision-fit (advances four-concepts substrate?)

- [ ] Does the pattern make ONE of the four concepts (Intent ·
      Capability · Lifecycle · Memory) more queryable, traceable, or
      composable? (cite which)
- [ ] Does it preserve the wire contract (`search` · `get_schema` ·
      `execute`)?
- [ ] Does it eliminate a doctrine violation we currently tolerate?
- [ ] Is it expressible as ontology + verbs, not as a parallel runtime?
- [ ] Does it ship with provenance writes by construction?
- [ ] Does its absence cost more than its presence?

#### Filter 2 — Goal-fit (solves a current goal?)

- [ ] Drop-in bar preserved (zero edits to load-bearing core)?
- [ ] Token economy improved (cite the metric: tokens-per-action,
      context-window-headroom, p99-latency, etc.)?
- [ ] Provenance moat strengthened (new node types recorded; new
      edges traversable)?
- [ ] Decidability increased (more checks become rule-based vs
      judgement)?
- [ ] Existing capability surface stays MECE (no overlap with current
      verbs)?
- [ ] Adds < 5% to the surface area an agent must discover?

#### Filter 3 — Architecture-fit (composes without re-arch?)

- [ ] Fits the 5-driver model (StateDriver/TextDriver/AudioDriver/
      DBDriver/CloudDriver) OR is genuinely a NEW boundary type?
- [ ] Expressible as an OntologyExtension (declarative) vs imperative
      hook?
- [ ] Composes with the walkable-skills pattern (Spec 080/081) — i.e.
      can be the body of a skill phase?
- [ ] Honours cluster-coherence (Spec 047) — lands in ONE cluster, not
      spread across 5?
- [ ] Backward-compatible with existing capability versions?
- [ ] Honours the cell-manifest pattern (if 3×N matrix is adopted —
      otherwise N/A)?

#### How filters are applied

Phase 4 of the ingestion procedure runs `thinking.apply_design_review
(depth="deep")` which delegates to `thinking.apply_full_review` over
each candidate pattern. For EACH pattern, the review produces a
**3-line verdict**:

```
Pattern: <name>
Vision-fit:        Y/N  (which concept(s) advanced; or which question failed)
Goal-fit:          Y/N  (which goal advanced; or which question failed)
Architecture-fit:  Y/N  (which compose-point; or which question failed)
PortDecision:      port | catalogue-only | needs-followup-spec
```

The verdict is recorded as a `PortVerdict` artefact node SERVES the
intent. Downstream port PRs cite the verdict.

## Done When

- [ ] Specs 109, 110, 112 all ship Green (gating condition above).
- [ ] An agent executes the 7 phases below using only MCP code-mode
      `mcp__agency__execute` blocks (no hand-coded Python files).
- [ ] After ingestion: every imported research doc has at least one
      `ResearchEntity` node SERVES the spec-113 intent; entities are
      tagged with `(taxonomy=source, tag=<repo>)` + `(taxonomy=topic,
      tag=<area>)`.
- [ ] After ingestion: a `CriticalAnalysisArtefact` (via
      `thinking.apply_design_review`) exists for the imported material;
      surfaces the 10 architectural patterns + recommends port priority.
- [ ] After ingestion: a `DossierWorkflow` Lifecycle node holds the
      pipeline state (intent → corpus → entities → contexts → snippets
      → audit).
- [ ] After ingestion: 5+ `PromptSnippet` nodes exist for the highest-
      priority patterns (3×N matrix, DNA gate-and-loader, harness-in-
      harness, phase-as-graph-node, anchor triad) — ready to feed
      future implementation prompts.
- [ ] `tests/test_research_ingestion_port.py` Green — asserts the
      entity counts + presence of the headline `CriticalAnalysisArtefact`.

## What gets ingested (the worklist)

| Source (under `Plan/_research/agency-system-import/`) | Priority | Why |
|---|---|---|
| `SOURCES.md` | P0 | Canonical source-repo URLs + reference framework docs (FastMCP, Claude Code Plugins, NCP) |
| `vision/00-charter.md` + `00.1-Overview.md` | P0 | The 3×N matrix architecture |
| `vision/specs/01-cell-manifest.md` | P0 | Strict TOML schema + derivation rules |
| `vision/specs/07-workflow-base-v1.md` | P0 | Phase-as-graph-node + graph-walker |
| `vision/specs/11-four-verb-canon.md` | P0 | The canonical verb set |
| `vision/specs/13-domain-isomorphism.md` | P1 | Isomorphism rules in depth |
| `vision/RESEARCH-PATTERNS.md` × 3 | P1 | Per-column research patterns |
| `Plan-_session-state/*-jules-research-1-context-engineering.md` | P0 | PM Agent Confidence + Subagent-Driven Dev + Merkle-DAG + Socratic Brainstorm + Project Index (25-250x token ROI patterns) |
| `Plan-_session-state/*-jules-research-2-token-efficiency.md` | P0 | Token-economy SOTA patterns |
| `Plan-_session-state/*-jules-research-3-spec-driven-dev.md` | P1 | Spec-driven development patterns |
| `Plan-_session-state/*-jules-research-4-large-context-ingestion.md` | P0 | Large-context-ingestion patterns (DIRECTLY APPLIES TO THIS SPEC's execution) |
| `Plan-_session-state/*-jules-research-5-pipeline-and-plugin.md` | P1 | Pipeline + plugin patterns |
| `Plan-_session-state/*-research-1-mcp-findings.md` | P1 | MCP-specific findings |
| `Plan-_session-state/*-research-2-skills-findings.md` | P1 | Skills-specific findings |
| `023-harness-in-harness/spec.md` | P0 | Harness-in-harness pattern |
| `122-centralized-ontology/spec.md` | P1 | Centralized ontology pattern |
| `130-shared-toolresult-envelope/spec.md` | P1 | ToolResult envelope spec |
| `132-skill-tool-hooks/spec.md` | P1 | Skill-tool hooks |
| `Plan-_research/agency-tooling-codemode/findings.md` | P0 | Code-mode survey findings |
| `Plan-_research/centralized-ontology/findings.md` | P1 | Ontology survey findings |
| `Plan-_research/graphqlite-codemode/findings.md` | P1 | GraphQLite code-mode findings |
| `INDEX.md` (authored iter-14) | P0 | Our own analysis + 10 patterns |
| `skills/theagencysystem/SKILL.md` + references | P0 | DNA gate-and-loader pattern |
| `skills/agentic/*` | P1 | 3 agentic skills (silent-fail-recovery, jules-orchestrator-discipline, context-safe-patch-handling) |
| `Plan-_lessons-learned/*` | P2 | Lessons captured |
| `Plan-_reviews/` (60K) | P2 | Code review patterns |
| `phase-{0..8}/*` | P2 | 9 phase folders |

**Plus source repos to clone fresh (per `SOURCES.md`)**:

| Repo | URL | Branch | Why clone fresh |
|---|---|---|---|
| `bitwize-music` | `https://github.com/bitwize-music-studio/claude-ai-music-skills` | `v0.91.0` | Already largely absorbed by music 093 wave; clone for any residual patterns |
| `agency` (source) | `https://github.com/netzkontrast/agency` | `claude/agency-plugin-refactor-PgMQ4` | The novel-architect / dramatica / ncp / sc-* / superpowers-* skills (more complete than what we have) |
| `superpowers-marketplace` | `https://github.com/obra/superpowers-marketplace` | `main` | 15 superpowers-* skills — full set |
| `SuperClaude_Framework` (NEW) | `https://github.com/SuperClaude-Org/SuperClaude_Framework` | `main` | The PM Agent Confidence Check pattern (25-250x token ROI per the imported research-1 doc) |
| `obra/superpowers` (NEW) | `https://github.com/obra/superpowers` | `main` | The Brainstorming + Subagent-Driven-Development + PM-style patterns |
| `claude-context` (NEW) | (per research-1 doc — find URL) | – | Merkle-DAG incremental synchronization pattern |

## How the agent executes this (MCP code-mode instructions)

Each phase below is a complete MCP code-mode block. Run them in order.
Each maps `await call_tool(...)` calls to agency verbs.

### Phase 0 — Bootstrap intent + read this spec

```python
# Phase 0: agency intent bootstrap
welcome = await call_tool("agency_welcome", {})
i = await call_tool("intent_bootstrap", {
    "purpose": "Execute Spec 113 — ingest the imported agency-system "
               "research material into the dossier + thinking + prompt "
               "capabilities so the patterns are queryable, taggable, "
               "and renderable as snippets for downstream implementation.",
    "deliverable": "ResearchEntities + ChapterContexts + PromptSnippets "
                   "+ a CriticalAnalysisArtefact, all SERVES this intent, "
                   "queryable via memory.provenance().",
    "acceptance": "tests/test_research_ingestion_port.py Green; entity "
                  "counts match the worklist priorities; the headline "
                  "CriticalAnalysisArtefact ranks the 10 patterns + "
                  "recommends port priority.",
})
intent_id = i["intent_id"]
return {"intent_id": intent_id, "welcome": welcome}
```

### Phase 1 — Capture research intent (dossier.intent_capture)

```python
# Phase 1: dossier intent capture (per Spec 112's research-prompt-optimizer
# pattern + Spec 113's worklist above)
result = await call_tool("capability_dossier_intent_capture", {
    "intent_id": intent_id,
    "seed_query": (
        "Ingest the 447 imported files from netzkontrast/the-agency-system "
        "under Plan/_research/agency-system-import/. Surface: 3×N matrix "
        "architecture, DNA gate-and-loader, phase-as-graph-node, cell-"
        "manifest, anchor triad, harness-in-harness, four-verb canon, "
        "token-economy patterns, SuperClaude PM Agent Confidence Check, "
        "superpowers Subagent-Driven Development + Brainstorming, "
        "claude-context Merkle-DAG, MCP code-mode best practices."
    ),
})
return {"research_intent_id": result["intent_yaml_recorded"]}
```

### Phase 2 — Catalog selection (dossier.catalog_list + register_module)

```python
# Phase 2: select catalog modules. Register a new domain-specific module
# for the agency-system port worklist (priorities P0/P1/P2)
all_modules = await call_tool("capability_dossier_catalog_list",
                              {"category": "A"})

await call_tool("capability_dossier_register_module", {
    "intent_id": intent_id,
    "module_slug": "agency-system-port-p0",
    "category": "A",
    "identifier": "M-AS-P0",
    "name": "the-agency-system Priority 0 patterns",
    "body": (
        "Architecture: 3×N matrix charter, cell-manifest, workflow-base-v1, "
        "four-verb canon, INDEX.md.\n"
        "Skills: theagencysystem DNA gate-and-loader.\n"
        "Research: jules-research-1 (context engineering), "
        "jules-research-2 (token efficiency), jules-research-4 "
        "(large-context-ingestion).\n"
        "Specs: 023-harness-in-harness, agency-tooling-codemode findings."
    ),
    "deps": [],
})

return {"modules_registered": ["agency-system-port-p0"],
        "base_catalog_count": len(all_modules.get("modules", []))}
```

### Phase 3 — Walk through each P0 source (dossier.ingest + chunk + extract)

```python
# Phase 3: ingest every P0 source from the worklist. Each file becomes a
# ResearchSource → chunked → entities extracted → taxonomized.
import time

P0_SOURCES = [
    ("Plan/_research/agency-system-import/SOURCES.md", "Plan/SOURCES.md", "treatise"),
    ("Plan/_research/agency-system-import/vision/00-charter.md", "vision/00-charter.md", "treatise"),
    ("Plan/_research/agency-system-import/vision/specs/01-cell-manifest.md", "01-cell-manifest", "paper"),
    ("Plan/_research/agency-system-import/vision/specs/07-workflow-base-v1.md", "07-workflow-base-v1", "paper"),
    ("Plan/_research/agency-system-import/vision/specs/11-four-verb-canon.md", "11-four-verb-canon", "paper"),
    ("Plan/_research/agency-system-import/Plan-_session-state/2026-05-18-jules-research-1-context-engineering.md", "jules-research-1-context-engineering", "interview"),
    ("Plan/_research/agency-system-import/Plan-_session-state/2026-05-18-jules-research-2-token-efficiency.md", "jules-research-2-token-efficiency", "interview"),
    ("Plan/_research/agency-system-import/Plan-_session-state/2026-05-18-jules-research-4-large-context-ingestion.md", "jules-research-4-large-context-ingestion", "interview"),
    ("Plan/_research/agency-system-import/023-harness-in-harness/spec.md", "023-harness-in-harness", "paper"),
    ("Plan/_research/agency-system-import/Plan-_research/agency-tooling-codemode/findings.md", "agency-tooling-codemode-findings", "treatise"),
    ("Plan/_research/agency-system-import/skills/theagencysystem/SKILL.md", "theagencysystem-skill", "paper"),
    ("Plan/_research/agency-system-import/INDEX.md", "agency-import-INDEX", "treatise"),
]

source_ids = []
for path, slug, kind in P0_SOURCES:
    src = await call_tool("capability_dossier_ingest_source", {
        "intent_id": intent_id,
        "source_uri": f"file://{path}",  # local file
        "slug": slug,
        "kind": kind,
        "title": slug,
    })
    sid = src["source_slug"]
    await call_tool("capability_dossier_chunk_source", {
        "intent_id": intent_id, "source_slug": sid, "chunker": "section"})
    await call_tool("capability_dossier_extract_entities", {
        "intent_id": intent_id, "source_slug": sid, "kinds": "all"})
    await call_tool("capability_dossier_auto_taxonomize_source", {
        "intent_id": intent_id, "source_slug": sid})
    source_ids.append(sid)

return {"sources_ingested": len(source_ids), "source_slugs": source_ids}
```

### Phase 4 — Apply critical thinking design review (thinking.apply_design_review)

```python
# Phase 4: thinking capability runs a full 14-method review of the
# imported corpus. Produces a CriticalAnalysisArtefact that ranks
# patterns + recommends port priority.
review = await call_tool("capability_thinking_apply_design_review", {
    "intent_id": intent_id,
    "spec_path": "Plan/_research/agency-system-import/INDEX.md",
    "depth": "deep",   # full 14 methods
})
return {"design_review_artefact_id": review["design_review_artefact_id"],
        "findings_count": len(review.get("finding_refs", []))}
```

### Phase 5 — Map entities to port-contexts (dossier.declare_context per P0 pattern)

```python
# Phase 5: each of the 10 patterns gets a Context node. Patterns are
# referenced by ResearchEntities (extracted in Phase 3) via
# CONTEXTUALIZES edges.
PATTERNS = [
    ("3x3-matrix",        "backbone",  "Architecture spine. Adopt-or-not is the meta-decision."),
    ("dna-gate-loader",   "backbone",  "Solves token flood at substrate level."),
    ("phase-graph-node",  "backbone",  "Walker pattern for all skills."),
    ("cell-manifest",     "factcheck", "Strict TOML + derivation."),
    ("anchor-triad",      "factcheck", "O(1) entity search."),
    ("harness-in-harness","backbone",  "Recursive skill execution."),
    ("four-verb-canon",   "backbone",  "Canonical verb set."),
    ("token-economy",     "factcheck", "14 SOTA discipline sources."),
    ("pm-confidence-check","factcheck", "25-250x token ROI."),
    ("subagent-driven-dev","backbone",  "Two-stage compliance+quality loop."),
]

context_ids = []
for slug, purpose, body in PATTERNS:
    ctx = await call_tool("capability_dossier_declare_context", {
        "intent_id": intent_id,
        "scope": "pattern",  # custom scope (not chapter/section/scene)
        "scope_id": slug,
        "entity_slug": "<resolved-by-infer>",
        "weight": 1.0,
        "purpose": purpose,
    })
    context_ids.append(ctx.get("context_id"))
return {"contexts_declared": len(context_ids)}
```

### Phase 6 — Render writing-assist snippets per pattern (dossier.render_snippet)

```python
# Phase 6: for each pattern's Context node, render a PromptSnippet that
# downstream implementation prompts can consume.
snippet_ids = []
for slug, purpose, _ in PATTERNS:
    snip = await call_tool("capability_dossier_render_snippet", {
        "intent_id": intent_id,
        "scope": "pattern",
        "scope_id": slug,
        "snippet_kind": "writing-assist",
        "token_budget": 800,   # tight per-pattern budget
    })
    snippet_ids.append(snip.get("snippet_id"))
return {"snippets_rendered": len(snippet_ids), "snippet_ids": snippet_ids}
```

### Phase 7 — Audit + finalize (dossier.audit + thinking.red_team)

```python
# Phase 7: reader-test simulation + adversarial review.
audit = await call_tool("capability_dossier_audit", {
    "intent_id": intent_id,
    "include_red_team": True,    # invokes thinking.red_team
})
return {"audit_id": audit["audit_id"],
        "clarity_score": audit["clarity_score"],
        "red_team_findings_count":
            len(audit.get("red_team_findings", []))}
```

### Phase 8 (post-execution check) — provenance traversal

```python
# Phase 8: confirm the provenance moat captured everything.
# Memory.provenance returns {serves, agents, artefacts, gates}.
prov = await call_tool("memory_graph_provenance",
                       {"intent_id": intent_id})

# Assert worklist invariants:
serves_labels = {p.get("__label", "") for p in prov.get("serves", [])}
artefact_kinds = {a.get("kind", "") for a in prov.get("artefacts", [])}

assertions = {
    "has_ResearchEntities": "ResearchEntity" in serves_labels,
    "has_design_review": ("design-review-artefact" in artefact_kinds OR
                          "critical-analysis-artefact" in artefact_kinds),
    "has_snippets": any(k == "writing-assist" for k in artefact_kinds),
    "has_dossier_workflow": "DossierWorkflow" in serves_labels,
}
return {"provenance_summary": {
    "serves_count": len(prov.get("serves", [])),
    "agents_count": len(prov.get("agents", [])),
    "artefacts_count": len(prov.get("artefacts", [])),
    "gates_count": len(prov.get("gates", [])),
}, "invariants": assertions}
```

## After ingestion — what becomes available

| Downstream capability | What it can do |
|---|---|
| `prompt.engineer` | Bundle the per-pattern snippets into chapter-writing prompts. The 18 frameworks (109 iter-13b) can be walked alongside. |
| `thinking.apply_design_review` | Already executed in Phase 4; the artefact is queryable for future design decisions. |
| `dossier.render_brief` | Render a "agency-system port plan" brief on demand from any subset of entities. |
| `develop.brainstorm` | Calls `thinking.apply_full_review` with the ingested patterns as context. |
| `agency_welcome` | Lists the ingested capabilities; future agents discover the worklist patterns automatically. |

## Source-clone procedure (for the deferred P0 repos)

Once Phase 7 audit passes, the agent can clone the missing source repos
per `SOURCES.md` and re-run Phases 3-7 against them. Each clone:

```python
# Phase 3-bis (per repo): clone + ingest
# Example for SuperClaude_Framework:
import subprocess
subprocess.run([
    "git", "clone", "--depth=1",
    "https://github.com/SuperClaude-Org/SuperClaude_Framework.git",
    "/tmp/SuperClaude_Framework"
], check=True)

# Then ingest the KNOWLEDGE.md (the PM Agent Confidence Check source)
src = await call_tool("capability_dossier_ingest_source", {
    "intent_id": intent_id,
    "source_uri": "file:///tmp/SuperClaude_Framework/KNOWLEDGE.md",
    "slug": "superclaude-framework-knowledge",
    "kind": "treatise",
    "title": "SuperClaude Framework KNOWLEDGE.md",
})
# ... chunk + extract + taxonomize as in Phase 3 ...
```

The 6 repos in the worklist (`bitwize-music`, `agency` source,
`superpowers-marketplace`, `SuperClaude_Framework`, `obra/superpowers`,
`claude-context`) each follow this shape.

## Walkable skill (lifecycle integration)

Per the 109/110/112 Lifecycle integration sections, this entire
8-phase procedure can be wrapped as a walkable skill
`research-ingestion-port-pass`:

```python
RESEARCH_INGESTION_PORT_PASS_SKILL = {
    "name": "research-ingestion-port-pass",
    "kind": "workflow",
    "phases": [
        {"index": 0, "name": "bootstrap",
         "produces": ["intent_id_ready"]},
        {"index": 1, "name": "intent-capture",
         "produces": ["research_intent_recorded"]},
        {"index": 2, "name": "catalog",
         "produces": ["modules_registered"]},
        {"index": 3, "name": "ingest-p0",
         "produces": ["p0_sources_ingested"]},
        {"index": 4, "name": "design-review",
         "produces": ["design_review_artefact"]},
        {"index": 5, "name": "context-mapping",
         "produces": ["patterns_contextualized"]},
        {"index": 6, "name": "snippet-render",
         "produces": ["snippets_ready"]},
        {"index": 7, "name": "audit-finalize",
         "produces": ["audit_complete"],
         "gate": "computed", "gate_verb": "dossier.audit_gate"},
        {"index": 8, "name": "human-review",
         "produces": ["port_plan_accepted"], "gate": "hard"},
    ],
}
```

The agent walks this skill via `develop.skill_walk(intent_id,
"research-ingestion-port-pass")`; each phase is the corresponding
MCP code-mode block above.

## Test plan

```python
# tests/test_research_ingestion_port.py
def test_p0_source_count_at_least_12(): ...
def test_each_source_has_chunks(): ...
def test_each_source_has_entities(): ...
def test_entities_tagged_with_source_taxonomy(): ...
def test_design_review_artefact_exists(): ...
def test_design_review_artefact_has_findings_from_8_methods_min(): ...
def test_pattern_contexts_declared_for_10_patterns(): ...
def test_snippets_rendered_under_token_budget_each(): ...
def test_audit_clarity_score_above_threshold(): ...
def test_provenance_returns_full_chain_with_serves_edges(): ...
def test_walkable_skill_walks_to_hard_gate_at_phase_8(): ...
```

## Open questions

1. **Adopt 3×N matrix architecture wholesale?** (Spec 113-bis or 114?)
   The INDEX.md flagged this as the meta-decision. Until decided, the
   ingestion captures the pattern as a `ResearchEntity` for future
   reference but does not commit the substrate to it.

2. **PM Agent Confidence Check integration**: the 2026-05-18 jules-
   research-1 doc claims 25-250x token ROI. Should agency adopt
   `intent.confidence_check` as a substrate verb? Likely yes; ship in
   a follow-up spec after Spec 113 closes.

3. **Subagent-Driven Development pattern**: superpowers' two-stage
   loop (compliance check → quality check). Already partly covered by
   `subagent` capability (Spec 011) but the two-stage discipline is
   not enforced. Follow-up spec candidate.

4. **claude-context Merkle-DAG**: the research-1 doc rates this as
   "Medium leverage — over-engineered for now". Defer indefinitely.

5. **superpowers Brainstorming skill**: superpowers ships a Socratic
   brainstorming skill. The agency `develop.brainstorm` is similar but
   lighter. Port the superpowers version as `develop.brainstorm_socratic`
   in a follow-up spec.

## Followup — Implementation Status

**Verdict (2026-06-07):** Drafted. Gating on 109+110+112 shipping.

### Done

- Authored this spec.
- 447 source files imported under
  `Plan/_research/agency-system-import/` (Iter-14).
- Worklist enumerated (12 P0 sources + 4 P1 categories).
- Phase procedure mapped to MCP code-mode `await call_tool` blocks.
- Walkable skill phase-graph designed.
- Test plan declared.

### Still

- 109 + 110 + 112 implementation PRs must land first.
- Once they do, an agent (you, me, a future Claude session) executes
  Phases 0-8 of this spec via MCP code-mode.
- After ingestion: the result feeds future spec work (likely Spec 114
  if we adopt 3×N matrix, plus 115 for PM Confidence Check, plus 116
  for Subagent-Driven Dev formalization).
