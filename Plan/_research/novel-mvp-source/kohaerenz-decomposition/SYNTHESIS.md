# SYNTHESIS — The Novel-Writing Capability for the Agency Plugin

> Reconciles the five slice decompositions (`01`–`05`) into **one** capability
> design for writing a novel — concretely *Kohärenz Protokoll* — on the Agency
> plugin (one FastMCP engine + one bi-temporal graph; wire contract
> `search · get_schema · execute`; four concepts Intent · Capability · Lifecycle ·
> Memory; the graph is the store, files are a rendered view).
>
> **Inputs (all API-verified PRs into `claude/dreamy-galileo-06exy`):**
> 01 Dramatica → #137 · 02 NCP → #138 · 03 Orchestration → #140 ·
> 04 Character & World → #141 · 05 Structure/Scene/Coherence → #142.
> Each slice was dispatched as a Jules session bound to a child Intent of root
> `intent:52b23adc`. Working language English; German canon prose is never translated.

---

## 1. The headline finding: the five slices already agree

The strongest result of the decomposition is **convergence without coordination**.
Five independent sessions, each reading only `PLUGIN-CONCEPTS.md` plus its own
source material, all reached the same three conclusions:

1. **Graph canonical, disk derived.** Every slice (01 storyform-subgraph, 02
   `ncp.json`-as-projection, 03 stop-treating-YAML-as-truth, 04
   YAML/NCP-as-render, 05 no-static-JSON-for-the-renderer) independently states
   that queryable narrative state must live in the bi-temporal graph and that
   files are rendered views.
2. **One documented prose exception.** All slices that touch prose (02, 03, 04)
   name the *human-authored canon document* — the German `world-bible.md`, the
   draft chapters — as the single, explicit disk-canonical exception, exactly
   parallel to the canon-docs carve-out in the plugin's own rule.
3. **The role-tag trichotomy is sufficient.** Lookups/validators are pure
   `transform`s; state mutations are `act`s; disk/external I/O and external
   research hand-off are `effect`s. No slice needed to modify the engine core to
   express its domain — every one lands through `OntologyExtension` + verbs.

That convergence **is** the load-bearing decision the brief asked us to surface
(graph-canonical vs disk-first): the evidence resolves it to **graph-canonical
with a documented prose-on-disk exception**, recorded as an ADR below.

---

## 2. The unified `novel` capability

A single domain capability — `novel` — registered via `Engine(...,
extra_capabilities=[Novel()])`, contributing one `OntologyExtension` and the verb
set below. Verbs are drawn verbatim from the five proposals and de-duplicated.

### 2.1 Verb catalogue (by role)

**`transform` (pure, deterministic, decidable — no provenance writes)**

| Verb | Origin | Does |
|---|---|---|
| `dramatica_lookup` | 01 | Query the seeded Dramatica ontology (dynamic pair, quad, hierarchy). |
| `validate_storyform` | 01 | The 12 Hard Rules H1–H12 as a decidable storyform linter. |
| `ncp_validate` | 02 | JSON-Schema (draft-07) validation of an NCP doc against the `1.3.0` shape + the vendored enums (463 appreciations, 144 narrative_functions). No theory/meaning check. |
| `select_psych_framework` | 04 | Genre/tone → recommended psychological models (e.g. `["big-five","enneagramm"]`). |
| `validate_dramatica_mapping` | 04 | Psychological traits don't contradict the assigned Dramatica role. |
| `map_genre_to_domains` | 04 | Genre (e.g. Hard-SF) → research domains (Physics, AI, …). |
| `coherence_check` | 05 | The decidable union: H1–H12, worksheet-order, canon-status referential integrity, Q1–Q5 *presence*. Emits a PASS/FAIL report; mutates nothing. |

**`act` (mutates narrative state + writes provenance to the graph)**

| Verb | Origin | Does |
|---|---|---|
| `storyform_commit_choice` | 01 | Commit one storyform choice (e.g. MC Domain = Universe) as a node/edge. |
| `set_ncp_decision` | 02 | Record a discrete NCP decision (a perspective's Domain, a storybeat) as a graph node. |
| `generate_psych_profile` | 04 | Create/update a `PsychologicalProfileNode` for a character. |
| `draft_research_brief` | 04 | Draft a domain research brief into graph state. |
| `integrate_research_findings` | 04 | Extract `WorldAxiomNode`s from returned findings; stage the `world-bible.md` diff. |
| `commit_scene_node` | 05 | Create/update `Chapter`/`Storybeat`/`Moment` nodes + their storyform edges. |

**`effect` (touches the filesystem / external world)**

| Verb | Origin | Does |
|---|---|---|
| `scaffold_novel_workspace` | 03 | Render the on-disk `novels/{author}/works/{genre}/{slug}/` layout from graph state. |
| `render_outline` / `render_status_view` | 01,05 | Render storyform / architecture-status Markdown by invoking the `transform` live (no stale `.json` sidecar). |
| `render_ncp` | 02 | Project the graph → canonical `ncp.json` on disk. |
| `render_ncp_players` | 04 | Project character graph state → NCP `players[]`. |
| `export_research_brief` | 04 | Write `research/briefs/<domain>.md` for the external `research-prompt-optimizer`. |

### 2.2 The `OntologyExtension` (one closed node/edge set)

- **Seeded vocabulary (vendored):** the Dramatica ontology —
  `maintenance/schemas/narrative-ontology/ontology.json`, **303 entries** measured
  by slice 01 (4 `class`, 16 `type`, 62 `variation`, 63 `element`, 65
  `dynamic-pair`) — loads as widen-only enums + the closed dynamic-pair edge set,
  shipped with a **`.sha` checksum sidecar** (slice 01's drift guard).
- **Authored nodes:** `Storyform`/storyform-choice, `NCPDecision`, `Character`,
  `PsychologicalProfile`, `DramaticaRole` (edge), `Domain`, `WorldAxiom`,
  `ResearchLifecycleState`, `Chapter`, `Storybeat`, `Moment`.
- **Moment edges (slice 05):** `dominant_throughline`, `signpost_ref`,
  `storypoint_element_id`, `character_arc_beat`, `theme_anchor_ref`.

---

## 3. One orchestration Lifecycle

Slice 03's `orchestrate-novel` gated skill is the spine that sequences every verb
above. The legacy 8 phases become Lifecycle states with `gate:"hard"` checkpoints;
each gate is `PASSED` or `BLOCKED_ON` + `input-required` (the AskUserQuestion loop).

```
BOOTSTRAP ──/novel-start──▶ scaffold_novel_workspace (effect)
   │  (author/genre/slug committed as act FIRST, then rendered)
INTENT ─────[gate: Intent Approval]
NARRATIVE ARCHITECTURE  ── storyform_commit_choice* → validate_storyform
   │  [gates: shape → dynamics → elements]   (progressive disclosure, slice 01+03)
CHARACTERS ── select_psych_framework → generate_psych_profile* → validate_dramatica_mapping
   │  [gate: Character Roster Approval]
WORLD & RESEARCH ── map_genre_to_domains → draft_research_brief*
   │  [gate: Research Scope Approval] → export_research_brief (effect)
   │  …await external findings… → integrate_research_findings
SCENE MATRIX ── commit_scene_node*  [gates: Act → Chapter → Scene]
DRAFTING ──[pre_drafting gate: coherence_check on Q1–Q5]──▶ (human writes German prose)
ITERATION ── coherence_check / validate_storyform on demand
```

Every state transition binds inputs/outputs as provenance; `/novel-*` commands
become Intent targets that *resume* this Lifecycle at the matching state, gated on
the requisite upstream provenance existing (slice 03).

---

## 4. The decidable/judgement split (slice 05, load-bearing for v1)

`coherence_check` ships **only the decidable subset** as a `transform`; everything
else stays a judgement-skill (LLM/human, recorded back to the graph):

- **Decidable → `transform` in v1:** all 12 Hard Rules (H1–H12); worksheet-order;
  canon-status referential integrity; Q1–Q5 **presence/completeness**;
  anti-patterns that reduce to a hard rule (AP-3≡H4, AP-5≡H2).
- **Judgement → deferred skill (v2):** semantic alignment (does the prose serve
  the theme — Q5 *meaning*); AP-1 (MC≠Protagonist justified?), AP-4
  (element too abstract), AP-6/AP-8/AP-9 (draft-divergence, mental-sex
  mischaracterisation, driver execution). These need the draft text and a model's
  judgement; they are not faked as linters.

This is exactly the "decidable vs fixture-discriminating" honesty the brief
demanded — grounded in slice 05's per-rule citations to `tasks/073/074/075/084/085/086`.

---

## 5. ADR — graph-canonical with a prose-on-disk exception

**Status:** Proposed (recommend Accepted).
**Decision:** The novel's *queryable, structured* state (storyform, NCP decisions,
characters, world axioms, scene matrix) is **canonical in the bi-temporal graph**.
On-disk artefacts under `novels/{author}/works/{genre}/{slug}/` are **rendered
views** produced by `effect` verbs. The **single exception** is human-authored
**canon prose** — the German chapter drafts and `world-bible.md` narrative body —
which is disk-canonical and round-tripped into the graph only as provenance/axiom
metadata, never overwritten by a render.
**Evidence:** unanimous, independent agreement of slices 01–05 (§1).
**Consequence for hand-edited `ncp.json`:** a bidirectional `ncp-io` reconciliation
step (slice 02) parses human saves into `act` operations so the file stays a
projection, not a shadow source of truth.

---

## 6. The Kohärenz Protokoll repo, concretely

`scaffold_novel_workspace` renders, for KP:

```
novels/netzkontrast/works/hard-sf/kohaerenz-protokoll/
├── work.md          # frontmatter: author, genre, slug (rendered from graph)
├── premise.md       # premise / central question
├── cast.md          # the cast (rendered from Character + PsychologicalProfile nodes)
├── dramatica.md     # the storyform (rendered from the storyform subgraph)
├── outline.md       # per-chapter compendium (rendered from Chapter/Storybeat/Moment)
├── ncp.json         # NCP 1.3.0 draft-07 projection (render_ncp)
├── README.md
├── chapters/        # human-authored German prose — DISK-CANONICAL (the §5 exception)
├── scenes/          # human-authored German prose — DISK-CANONICAL
├── characters/      # rendered per-character views
├── world/           # world-bible.md = canon prose; structured axioms in graph
├── revisions/
├── art/
└── research/        # exported briefs (effect) + returned findings
```

Slug rule: kebab-case, ASCII, ≤ 64. The structured root files (`work/premise/cast/
dramatica/outline/ncp`) are re-renderable; `chapters/ scenes/ world/*.md` prose is
the protected exception.

---

## 7. v1 scope cut / v2 deferred

**v1 (session-ready):** the `novel` capability with `scaffold_novel_workspace`,
the `orchestrate-novel` gated Lifecycle (slice 03), `dramatica_lookup` +
`validate_storyform`, `ncp_validate`, the decidable `coherence_check`, the
`pre_drafting` gate, and the render `effect`s. Ontology seeded from the 303-entry
file with a `.sha` sidecar.

**v2 (deferred):** the judgement coherence-skills (§4); the bidirectional
`ncp-io` reconciliation (§5); richer world-axiom contradiction-checking against
prose; the full psychological-framework library beyond the v1 OCEAN/Enneagram set.

---

## 8. Provenance

This synthesis reconciles only what the five sessions actually produced; every
claim traces to a slice `PROPOSAL.md`/`COHERENCE.md` on its PR branch (#137–#142)
or to a cited `Legacy/` source. The decomposition campaign itself is recorded in
the bi-temporal graph under root Intent `intent:52b23adc`, with one child Intent
and one Jules session per slice (see this folder's `README.md` dispatch ledger).

**Next action for the maintainer:** merge #137, #138, #140, #141, #142 (close the
slice-02 duplicate #139), then promote §5 to an ADR and §2 to a `novel` capability
spec for implementation.
