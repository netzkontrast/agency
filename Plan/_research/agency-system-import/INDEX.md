# the-agency-system Comprehensive Import — Index + Architectural Insights

> Iteration 14 (2026-06-07). User directive: *"Look into the agency
> system repo and extract Everything there is… that can help - also
> the Skill creator skill. Maybe Even all skills from the skills dir
> - so that we can Port it torougly. You also Need to Scan Plan and
> Vision Folders - for more Source Material regarding Everything the
> agency repo want to achive."*
>
> **446 files imported** under `Plan/_research/agency-system-import/`
> covering: vision (all specs), all skills (theagencysystem +
> agentic + jules + music + novel), workflow + context + agentic
> column folders, Plan/_research/ + _lessons-learned + _reviews +
> decisions + harness, 9 phase-folders, key 1xx specs (016/022/023/
> 100/102/105/111/122/130/132).

## What's in here

```
agency-system-import/
├── vision/                      # The 3xN matrix architecture (CHARTER)
│   ├── 00-charter.md            # ← THE LOAD-BEARING DOC
│   ├── 00.1-Overview.md
│   ├── 03-architecture.md
│   ├── specs/                   # 14 numbered specs (01-cell-manifest
│   │                             # through 14-progressive-disclosure)
│   ├── agentic/                 # agentic column vision
│   ├── context/                 # context column vision
│   └── workflow/                # workflow column vision
├── skills/                      # All ported skills
│   ├── agentic/                 # 3 agentic skills
│   ├── theagencysystem/         # The DNA gate-and-loader pattern
│   ├── jules/                   # Jules orchestration
│   ├── music/                   # ~55 music skills (bitwize source)
│   └── novel/                   # (empty placeholder)
├── workflow/                    # Meta-row workflow column
│   ├── meta/                    # The "workflow workflow" — bootstrap
│   ├── jules/                   # Jules workflow column
│   └── _runner/                 # Pipeline runner (the walker)
├── agentic/                     # Agentic column root
│   ├── _harness/                # The harness-in-harness pattern
│   └── jules/                   # Jules agentic column
├── context/                     # Context column root
│   ├── _shared/                 # Shared schemas (cell, gate, tool_result)
│   ├── _store/                  # SQLite-backed Store
│   ├── _drivers/                # FS + Protocol drivers
│   ├── _hooks/                  # pre/post tool-use hooks
│   └── jules/                   # Jules context column
├── Plan-_research/              # Original Plan/_research from
│                                 # the-agency-system (research briefs,
│                                 # findings, agency repo analysis,
│                                 # graphqlite-codemode etc)
├── Plan-_lessons-learned/       # Captured lessons
├── Plan-_reviews/               # Code reviews (largest folder — 60K)
├── Plan-decisions/              # ADRs
├── Plan-harness/                # Harness-related plans
└── phase-0..8/                  # 9 phase folders
                                  # (foundation-cleanup → anchor-triad →
                                  #  hook-chain → github-sink → context-mode
                                  #  → ontology+graph → quality-loop →
                                  #  domain-handlers → operational-hardening)
```

## The headline insight: 3×N Matrix architecture

From `vision/00-charter.md` — the single most important doc in the
imported set.

### The matrix

```
                ┌───────────────┬───────────────┬───────────────┐
                │   agentic     │   workflow    │   context     │
                │ (skills +     │ (pipelines +  │ (graph +      │
                │  MCP + harness│  handoffs +   │  frontmatter +│
                │  -in-harness) │  gates)       │  templates +  │
                │               │               │  schemas +    │
                │               │               │  search +     │
                │               │               │  pandoc)      │
┌───────────────┼───────────────┼───────────────┼───────────────┤
│ music         │ agentic/music │ workflow/music│ context/music │
├───────────────┼───────────────┼───────────────┼───────────────┤
│ novel         │ agentic/novel │ workflow/novel│ context/novel │
├───────────────┼───────────────┼───────────────┼───────────────┤
│ jules         │ agentic/jules │ workflow/jules│ context/jules │
├───────────────┼───────────────┼───────────────┼───────────────┤
│ workflow      │ agentic/      │ workflow/     │ context/      │
│ (meta-row)    │ workflow      │ workflow      │ workflow      │
│               │ (workflow-    │ (scaffold     │ (cell-shape   │
│               │  author skill)│  pipeline)    │  templates)   │
└───────────────┴───────────────┴───────────────┴───────────────┘
```

### Three rules

1. **Column isomorphism**: every cell in column X has the same
   canonical shape (enforced by `cell-manifest.schema.json`)
2. **Row isomorphism**: every row's three cells share naming, ontology
   types, and handoff verbs
3. **Name-driven discovery**: knowing a row's name lets an agent
   discover all three cells via the graph

**Why this matters for our novel/dossier/prompt work**: our current
specs treat capabilities as independent silos. The agency-system
model is that EVERY domain has THREE faces (agentic + workflow +
context) and the substrate enforces isomorphism. This is more
opinionated than agency's current `Capability` model but solves the
"how do I find the right verb" discoverability problem completely.

## Other patterns worth porting

### Pattern 1: The DNA gate-and-loader (theagencysystem skill)

`skills/theagencysystem/SKILL.md` — a single skill that:
1. Gates on context ("is this really the agency-system project?")
2. Reads `references/resolver.yaml` + `state-axis.md` if yes
3. Resolves `(function × state × layer)` to a minimum DNA snippet
4. Injects ONLY the needed snippet into the running skill

**Application**: novel can do the same — instead of dumping the full
Dramatica ontology into prompts, gate-and-load resolves which
`(throughline × scene × character)` cell is active and loads only
those snippets. This is the iter-11 prompt-engineer's token-budget
discipline taken to the ontology level.

### Pattern 2: Phase-as-graph-node (Spec 07-v1)

The v1 rewrite of workflow base moves phases from filesystem markdown
to **graph nodes**: `Phase{id, row, body_ref}` with `PRECEDES` edges.
The pipeline runner becomes a graph-walker.

**Application**: this is the substrate-level version of what our 102's
walkable skills do. Spec 080/081 already moves in this direction;
Spec 07-v1 of the-agency-system is the full architectural commit.

### Pattern 3: Cell manifest derivation (Spec 01)

Every cell has ONE required boot file: `manifest.toml`. The strict
form contains ONLY what cannot be derived from `(row, column)`. The
harness derives the rest deterministically.

**Application**: our `OntologyExtension` could ship as a derived
cell-manifest. The capability author writes the strict bits; the
substrate derives skill names, verb prefixes, schema paths.

### Pattern 4: Harness-in-harness (agentic column)

The `agentic/_harness/` folder. The harness is a system that hosts
sub-harnesses recursively — each row's agentic cell can declare its
own sub-harness for skill execution.

**Application**: relates to Spec 023's harness-in-harness work in
the-agency-system Plan/023/. May be how to wire iter-11's framework-
walks into a coherent skill-execution loop.

### Pattern 5: Anchor triad (Plan 104 + 112)

`104-tool-search-anchor-triad` and `112-context-anchor-triad`. Each
tool/context entity has an anchor triad — a 3-element identity
(presumably (row, column, slug) or similar) — that enables search
without substring matching.

**Application**: instead of `agency:help` doing string search across
skill names, anchor triads let us query "find every cell whose row=
novel and column=context" in O(1).

### Pattern 6: Token-economy (multiple specs)

Recurring theme across the imported specs:
- Spec 01: strict manifests, derived names → token economy
- Spec 14: progressive-disclosure roadmap
- Plan 105: toon-serializer (token-optimized output)
- Plan 116: bash-output compression
- Plan 120: smart-compaction checkpoints
- Plan 121: contextignore-hardblock

**Application**: our iter-11 prompt-engineer token budgets are a small
slice of a broader token-economy discipline the-agency-system has
formalized.

### Pattern 7: Quality-score telemetry + loop detection (Plan 118 + 119)

Every tool call produces a quality score; loops are detected via the
score history. Plan 120 then checkpoints when scores degrade.

**Application**: 110's `score_prompt_output` is one slice. The
broader quality-loop-with-checkpoints discipline could inform 108's
gate philosophy.

### Pattern 8: Frustration-log protocol (Plan 138)

When the agent reports frustration, a structured log captures it as
provenance — feeds the "lessons learned" pipeline.

**Application**: agency could ship `reflect.frustration` as an effect
verb; feeds `dogfood.observe`. This is the missing-piece between
"observation" and "lesson learned".

### Pattern 9: Watcher SDK composability (Plan 137)

The `watcher` pattern (PR activity watching, etc.) is exposed as an
SDK — composable across all rows.

**Application**: our Jules subscription pattern is a slice; this
extends to all monitoring needs.

### Pattern 10: Evidence snapshot helper (Plan 139)

When a plan's evidence is captured, a helper snapshots the full
provenance window at that point.

**Application**: relates to our reflect.synthesize + provenance moat;
this is the formalized helper.

## Key vision specs (read these first)

| # | Title | Why it matters |
|---|---|---|
| 00 | charter | THE matrix + 3 rules |
| 00.1 | overview | charter successor (probably more current) |
| 03 | architecture | full architectural commitments |
| 01 | cell-manifest | strict TOML schema; derivation rules |
| 02 | tool-result-envelope | standard ToolResult shape |
| 03 | sidecar-metadata | per-call metadata sidecar pattern |
| 04 | phase-state-envelope | phase state shape |
| 05 | gate-yaml | gate declaration shape |
| 06 | agentic-base | agentic column base layer |
| 07-v1 | workflow-base-v1 | graph-walker rewrite |
| 08-v1 | context-base-v1 | Store + drivers + hooks |
| 09 | crossover-matrix-review | how rows interact |
| 11 | four-verb-canon | THE verb canon (probably `act / transform / effect / view`?) |
| 12 | vocabulary | shared vocabulary |
| 13 | domain-isomorphism | isomorphism rules in depth |
| 14 | progressive-disclosure | the disclosure roadmap |

## Spec areas to deeply mine

When implementing the novel/prompt/thinking/dossier specs, deeply
mine these import folders:

- `Plan-_research/agency-tooling-codemode/` — code-mode tool surface
- `Plan-_research/centralized-ontology/` — ontology centralization
- `Plan-_research/graphqlite-codemode/` — graph query in code-mode
- `Plan-_reviews/` — code review patterns + canonical critiques
- `vision/specs/07-workflow-base-v1.md` — phase-as-graph-node
- `vision/specs/08-context-base-v1.md` — context Store design
- `vision/specs/09-crossover-matrix-review.md` — cross-row dispatch
- `vision/specs/11-four-verb-canon.md` — the verb canon
- `phase-5-ontology-and-graph-wave-d/` — ontology + graph wave

## What does NOT need direct porting

- Music skills (we already have music spec 093 wave that absorbs them)
- Jules-specific orchestration (we already have jules cap)
- Most numbered Plan/0xx specs (they're domain implementation details)

## Implications for the novel spec set (101-112)

After this import, the novel spec set should consider:

1. **Adopt the 3×N matrix** for the novel rows (agentic/workflow/
   context). Currently novel has 7 clusters under one capability;
   the matrix model would split into 3 capability faces × 7 rows.
   This is a significant re-architecture decision.

2. **Cell-manifest schema** could replace OntologyExtension for novel
   capability cells. More opinionated; more derivable.

3. **DNA gate-and-loader** pattern for chapter-context resolution —
   the iter-10 ChapterContext could BE a gate that resolves
   `(throughline × scene × character)` to the snippet to load.

4. **Phase-as-graph-node** for novel walkable skills — already moving
   this direction per Spec 080/081.

5. **Anchor triad** for novel verb discovery — `(row=novel,
   column=agentic, slug=chapter-drafter)` finds the skill in O(1).

6. **Token economy** more aggressively — 14 sources of discipline
   instead of just the prompt-snippet token budget.

These are NOT iter-13 changes to push; they're meta-architecture
considerations for a future agency 2.0 or a separate novel-substrate
spec.

## Next step

Consider authoring a Spec 113 — "Adopt 3×N matrix architecture" — as
a META spec that informs all future capability design. It would
formalize:
- Cell-manifest schema
- Row + column registration
- Cross-row dispatch (per vision spec 09)
- Four-verb canon (per vision spec 11)
- Token-economy discipline (per vision specs 01 + 14)

This would be a substantial architecture commitment beyond the
current capability-per-folder pattern. May or may not align with
agency's current design philosophy — the user should decide.

For now, the imported source material under `Plan/_research/
agency-system-import/` is available for any implementer to reference.
