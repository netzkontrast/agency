---
spec_id: "044"
slug: research-capability
status: complete
last_updated: 2026-06-03
owner: "@agency"
depends_on: [011, 016, 020, 023, 040, 043, 045]
affects:
  - agency/capabilities/research/__init__.py            # NEW heavy capability
  - agency/capabilities/research/_main.py
  - agency/capabilities/research/_lead.py               # scope-the-question + plan specialists
  - agency/capabilities/research/_specialist.py        # one sub-search + cite
  - agency/capabilities/research/_verify.py             # adversarial citation check
  - agency/capabilities/research/_web.py                # web-search boundary driver
  - skills/deep-research/SKILL.md                        # walker discipline
  - skills/deep-research/references/specialist-roles.md
  - skills/deep-research/references/verification-rules.md
  - tests/test_research_capability.py
  - tests/test_research_verify.py
estimated_jules_sessions: 3
domain: meta
wave: 2
unblocks: [novel_research_prompts_F]
---

# Spec 044 — `research` Capability (Lead + Specialists + Verifier)

## Why

Agency's `EXTENSION-PLAN.md` already names `research` as a planned
capability: *"a lead+specialists fan-out + a verifier gate;
`CITES`/`VERIFIED_BY` edges; composition: `delegate` → craft → `gate`"*.
SuperClaude ships `sc-research` (deep web research, parallel orchestration,
multi-hop reasoning, cited evidence). The Superpowers ecosystem ships a
`deep-research` skill in similar shape. Neither is graph-native — both
return rendered reports + dump citations into the parent context.

This spec ships the agency-native version:

- **Lead** verb scopes the question, decides the specialists needed
  (`web`, `codebase`, `prior-reflections`, etc.), and fans out via
  `delegate.dispatch`.
- **Specialists** each run a single bounded sub-search, emit Citation
  nodes with `evidence_text` + `source_url`/`source_path` + a
  `confidence: 0..1` score. They return short summaries; raw evidence
  goes to the graph.
- **Verifier** is a `transform` that walks Citation nodes and checks
  each for: source reachability (URLs resolve), evidence-supports-claim
  (substring/embedding match between cited text and the synthesised
  claim), and intra-citation consistency (cluster contradictions). It
  is the agency-native answer to "hallucinated citations".
- **Render** — `document.render(scope="research-report",
  intent_id=...)` projects the graph state into a cited markdown
  report. Agency-native composition: the report is rendered, not
  written.

The doctrine win is twofold: research is now a **first-class graph
record** (every claim's citation chain survives the session, queryable
via `memory_graph_provenance`), and **the verifier gate makes
verification mandatory before publish** (agency's `gate.check` precedent
from `pre_drafting_gate` in Spec 010).

This capability also **directly enables the Novel-domain research
prompts the user wants for Gemini** (audit thread, task F): a research
question about Dramatica internals, an NCP-schema edge case, or
genre-tropes for a specific subgenre flows through this capability
and emits a structured cited report Gemini's deep-research can consume
(via copy-paste of the verified prompt and report-template).

## Done When

### Folder-form capability

- [ ] `agency/capabilities/research/` exists with scaffolded skeleton
  + marker.
- [ ] `plugin.lint_capability("research")` returns `ok=True` in block mode.

### Lead verb (scope + plan fan-out)

- [ ] `research.lead(question: str, depth: str = "standard", intent_id:
  str) -> dict` (role `act`). Returns `{research_id: str,
  specialists: list[str], plan: str}`.
- [ ] Mints a `Research` node `{question, depth, started_at,
  status: "planning"}`, linked `SERVES` the intent.
- [ ] `depth` ∈ `{brief, standard, deep}`:
  - `brief` — 1 specialist (`web`), 1 verification pass, ≤ 600-token
    output.
  - `standard` — 2 specialists (`web` + `codebase` or `prior-
    reflections`), 1 verification pass, ≤ 2000 tokens.
  - `deep` — 3+ specialists, 2 verification passes, ≤ 5000 tokens.
- [ ] The planning decision uses `delegate.dispatch_decision` (Spec 040)
  to confirm fan-out makes sense (S4:parallel ≥ 3 for `deep`, etc.).
- [ ] Does NOT itself run the specialists — returns the plan; the skill
  walker triggers fan-out at the next phase.

### Specialist verb (one bounded sub-search)

- [ ] `research.specialist(research_id: str, role: str, query: str,
  intent_id: str) -> dict` (role `act`). Returns
  `{citations: int, summary: str}`.
- [ ] `role` ∈ `{web, codebase, prior-reflections, doc-corpus}`:
  - `web` — uses the `web_search` driver (new boundary, below).
  - `codebase` — agency-internal grep + AST walk over the repo.
  - `prior-reflections` — calls
    `reflect.recall_semantic(query, k=10)` (Spec 045 dependency).
  - `doc-corpus` — searches files under `docs/` for keyword matches
    + a Spec-037-style semantic rank.
- [ ] Records ≥ 1 Citation node per sub-search:
  `{source_kind: str, source_url_or_path: str, evidence_text: str,
  evidence_offset: int, confidence: float, claim_supported: str}`.
- [ ] **`confidence` computation rule** (Wiegers — every floating-point
  field has a defined origin):
  - `web` specialist: `confidence = 0.9` if cited URL resolves at
    record-time AND `evidence_text` is a verbatim substring of the
    fetched page; `0.5` if URL resolves but text is paraphrased;
    `0.2` if URL unreachable at record-time (kept for later verifier
    check). NO LLM judgement.
  - `codebase` specialist: `confidence = 1.0` (deterministic — the
    file path + offset are addressed in the repo at a specific SHA).
  - `prior-reflections` specialist: `confidence = score` returned by
    `reflect.recall_semantic` (cosine or TF-IDF similarity, 0..1).
  - `doc-corpus` specialist: same as `prior-reflections` (Spec 045
    semantic ranker).
  No specialist may invent confidence; each `source_kind` has exactly
  ONE rule. The verifier's `evidence-supports-claim` check (below) is
  the second pass — confidence is the recording-time signal, the
  verifier is the verification-time signal. They are independent.
- [ ] Citations linked: `Research --CITES--> Citation`, also
  `Citation --SUPPORTS--> ResearchClaim` (a transient claim node
  produced during synthesis; see Verify, below).
- [ ] Specialist returns truncated summaries (≤ 400 tokens); detail in
  the graph.

### Verifier verb (adversarial citation check)

- [ ] `research.verify(research_id: str) -> dict` (role `transform`).
  Returns `{ok: bool, checks: {<check_name>: {status, items?}}}`.
- [ ] Three checks (decidable, no LLM):
  - `reachability` — for each `web` Citation, HEAD the URL (cached
    per-session); fail if non-2xx.
  - `evidence-supports-claim` — for each Citation, verify the
    `evidence_text` substring or semantic match (Spec 045) is ≥ 0.5
    cosine OR substring-match of the linked `claim_supported`.
    Below threshold = fail with `score`.
  - `contradiction-cluster` — group Citations by claim; if two claims
    are linked to citations with opposing evidence (heuristic:
    semantic dissimilarity > 0.7), emit a warn with both Citation IDs.
- [ ] Emits a `Verification` node `{research_id, status, started_at,
  finished_at}` plus per-check Reflection nodes. Linked
  `Verification --VERIFIES--> Research`.
- [ ] On `status: "fail"`, `research.publish` (next phase of the
  walker) is BLOCKED via `gate.check` (Spec 010 pattern). Override
  available with `force=True` and an `OVERRIDDEN_BY` audit edge.

### Web-search boundary driver

- [ ] `agency/capabilities/research/_web.py` defines a `WebSearchClient`
  protocol with `search(query: str, k: int) -> list[dict]`.
- [ ] Default backend uses **the host environment's MCP-available web
  search if present** (e.g. the `WebSearch` tool that Claude Code
  surfaces), via a thin wrapper that exposes the same protocol.
- [ ] Test-time stub returns fixture results.
- [ ] Engine injects via `Engine(..., web_search=…)` kwarg, same pattern
  as `jules_client`/`vcs_backend`/`embedder`.

### Skill walker

- [ ] `skills/deep-research/SKILL.md` exists with the standard
  frontmatter, kebab-case name, "Use when…" trigger.
- [ ] Lifecycle template on `ResearchCapability.ontology.skills["deep-
  research"]` has six phases:
  ```
  scope → plan → fan-out → verify → render → publish(hard)
  ```
  Per phase:
  - `scope` — refine the question; output: clarified question + depth.
  - `plan` — calls `research.lead`.
  - `fan-out` — for each planned specialist, calls
    `research.specialist`; the orchestrator parallelises via
    `delegate.dispatch` (S4:parallel signal).
  - `verify` — calls `research.verify`. Hard-blocks on `status: "fail"`
    unless overridden.
  - `render` — calls `document.render(scope="research-report",
    research_id=...)` (Spec 043 dependency).
  - `publish` — hard gate; on confirm, optionally writes the rendered
    report to disk via `apply=True` semantics.

### Ontology fragment

- [ ] Nodes:
  - `Research` `[question, depth, started_at, status]` — `status` enum
    `{planning, fanning-out, verifying, ready, blocked, published}`.
  - `Citation` `[source_kind, source_url_or_path, evidence_text,
    confidence]` — `source_kind` enum `{web, codebase, reflection,
    doc-corpus}`.
  - `ResearchClaim` `[text]` — a synthesised claim during fan-out.
  - `Verification` `[research_id, status, started_at]` — `status` enum
    `{pass, warn, fail}`.
- [ ] Edges:
  - `CITES` (Research → Citation)
  - `SUPPORTS` (Citation → ResearchClaim)
  - `CONTRADICTS` (Citation ↔ Citation — emitted by the
    contradiction-cluster check)
  - `VERIFIES` (Verification → Research)
  - `OVERRIDDEN_BY` (already declared in Spec 010 — reused for force-
    publish)
- [ ] Schemas: `research-report` artefact
  `[research_id, question, claims, citations]`.
- [ ] Skills: `deep-research` (walker above).

### Tests

- [ ] `tests/test_research_capability.py` — drives the walker end-to-
  end with an injected `WebSearchClient` stub returning fixture results;
  asserts the Research → Citation → Verification graph.
- [ ] `tests/test_research_verify.py` — each of the three verifier
  checks tested in isolation (reachability mock, evidence-supports
  threshold boundary, contradiction-cluster detection).

### Novel-research prompts (audit task F integration)

- [ ] A directory `research/novel-prompts/` (NOT in
  `agency/capabilities/`) lands in this spec with **5 Gemini-deep-
  research prompts** tailored to Spec 010 work. Each prompt:
  - Is a `.md` file scoped to one Novel research question (e.g.
    "Dramatica dynamic-pair reciprocity proof", "NCP draft-07 vs
    competing narrative schemas", "agency capability patterns for
    deferred coherence checks").
  - Carries a `## Acceptance` section the user can use to verify
    Gemini's response.
  - Carries a `## How to feed into Spec 010` note explaining where
    each output would land in the Novel implementation.
- [ ] The five prompts are the SAME format the `research.publish`
  rendered report would emit — i.e. the prompts ARE valid inputs to
  this capability, AND they're useful as standalone Gemini prompts
  even before the capability ships.

## Design

### Why composition over generation (again)

`research` is the cleanest application of the doctrine. The capability
does NOT generate prose — it:

1. **Plans** — picks specialists by question shape (decidable).
2. **Fans out** — dispatches independent sub-searches (delegate).
3. **Records** — every finding is a graph node (provenance).
4. **Verifies** — decidable checks against the recorded evidence.
5. **Renders** — `document.render` projects the graph into prose.

The orchestrator (the agent walking the skill) is where any prose-level
synthesis happens, with the verified graph as input. The capability
**never writes a sentence that isn't grounded in a Citation node**.

### Token-economy through the chain

| Phase | Token cost (orchestrator's view) | Why |
|---|---|---|
| `scope` | ≤ 200 (clarifying questions) | Inline interactive |
| `plan` | ≤ 300 (specialist list + rationale) | `research.lead` returns plan summary |
| `fan-out` | ≤ 400/specialist (subagent compress) | Each specialist dispatched; raw evidence in graph |
| `verify` | ≤ 200 (pass/fail + check summaries) | Pure transform; detail in Verification node |
| `render` | ≤ 2500 (the cited report) | `document.render` enforces budget |
| `publish` | ≤ 50 (hard gate prompt) | Lifecycle gate |

Total orchestrator-context cost: ≤ 5000 tokens for `deep`. The same
research run in a naive single-prompt LLM would consume 20K+ tokens of
context. The savings come from **subagent dispatch at fan-out**
(Spec 040) + **graph storage of raw evidence** (Spec 020) + **rendered
projection** (Spec 043).

### The Novel-research prompts (task F)

The user explicitly requested deep-research prompts for Gemini to inform
Spec 010 (Novel) implementation. Five prompts land in this spec because
they're structurally identical to what `research.lead` would emit. Each:

1. Names the research question precisely.
2. Lists the specialists needed (`web`, `codebase`, `doc-corpus` over
   Dramatica references, …).
3. Specifies the verification gate (what makes the answer trustable).
4. Maps to a specific Done-When in Spec 010.

The five questions (locked in this spec; usable today):

| # | Question | Maps to Spec 010 §… |
|---|---|---|
| F1 | "What's the canonical state-of-the-art for narrative-structural validation in 2026? Compare Dramatica's NCP draft-07 against (a) Save-the-Cat beat sheets, (b) Story-Engine-style state machines, (c) academic narrative schemas (LRA, Story-Generator)." | "Source fidelity §3" |
| F2 | "Which of the deferred 11 coherence checks (Spec 010 §"The decidable coherence subset") can be made genuinely decidable by augmenting the bundled ontology with a quad reverse-index? Evidence: the shipped 303-entry ontology + dynamic-pair extracts." | "Open Question 7" |
| F3 | "What's the optimal author-facing skill-walker phase order for a novel conceptualisation skill that hard-gates pre-drafting? Compare existing implementations (Save-the-Cat 15-beat, Story Grid 5-leaf, Snowflake 10-step) against agency's `examples/music.py::album-concept` precedent." | "Skills §work-concept" |
| F4 | "Which prosodic / rhythm / pacing features of contemporary literary fiction can be characterized as **decidable transforms** (vs. judgement skills) with the same honesty as Spec 010's coherence subset? Evidence: linguistic corpora + style-analysis literature." | "Deferred §revision passes" |
| F5 | "How should the `dramatica_lookup` navigator port handle dynamic-pair edge cases beyond reciprocity (e.g. quad consistency, archetype-element pairing)? Survey the source `the-agency-system @ 0a6a9e71` plus the Dramatica.com 2020+ reference documentation." | "dramatica_lookup verb" |

Each prompt becomes a single `research/novel-prompts/F<n>-<slug>.md` file.
The agent (or Gemini directly, if the user feeds the prompt to Gemini's
Deep Research) produces a cited markdown response usable as input to
Spec 010 Loop 1+ implementation.

## Files

- **Scaffold first** via `develop.scaffold_capability(name="research",
  kind="heavy")`.
- **Create (capability):**
  - `agency/capabilities/research/__init__.py`
  - `agency/capabilities/research/_main.py`
  - `agency/capabilities/research/_lead.py`
  - `agency/capabilities/research/_specialist.py`
  - `agency/capabilities/research/_verify.py`
  - `agency/capabilities/research/_web.py`
- **Create (skill):**
  - `skills/deep-research/SKILL.md`
  - `skills/deep-research/references/specialist-roles.md`
  - `skills/deep-research/references/verification-rules.md`
- **Create (Novel research prompts — task F):**
  - `research/novel-prompts/F1-narrative-validation-sota.md`
  - `research/novel-prompts/F2-deferred-coherence-checks.md`
  - `research/novel-prompts/F3-walker-phase-order.md`
  - `research/novel-prompts/F4-decidable-style-transforms.md`
  - `research/novel-prompts/F5-dramatica-lookup-edges.md`
- **Tests:**
  - `tests/test_research_capability.py`
  - `tests/test_research_verify.py`

## Open Questions

1. **Web-search driver default.** Until Spec 040's F6 (HTTP MCP-client
   driver) ships, "web" specialists need a backend. v1 lazy-imports a
   `WebSearch` host tool if available; otherwise fails loud
   (`agency_doctor` flags the missing capability). Acceptable v1.
2. **Verifier strictness defaults.** The evidence-supports threshold is
   0.5 cosine. Should it be configurable per `depth` (brief uses 0.3,
   deep uses 0.7)? Lean yes; declared on the skill template.
3. **Citation reachability cache.** Web URLs change; today's reachability
   check is per-session. Should we persist (with a TTL) in the graph?
   v2 question.
4. **Multi-specialist same-role.** Can the same `role: web` fire twice
   in one `deep` plan (different queries)? v1 says yes; the
   `delegate.dispatch` fan-out doesn't care about role uniqueness.
5. **Should `verify` write Citation severity?** Today a Citation has
   `confidence`; verification produces pass/fail/warn. Should the
   verification result write back to the Citation node (mutating)?
   Cleaner: emit a separate `VerifiedCitation` projection node.

### Compatibility with SC's "STOP AFTER" doctrine

SC ships six commands with explicit "STOP AFTER" output-only boundaries:
`brainstorm` (stop after requirements), `research` (stop after report),
`workflow` (stop after plan), `estimate` (stop after estimation),
`spawn` (stop after decomposition), `troubleshoot` (diagnosis-first).
Agency's analogue is the **hard-gate Lifecycle phase** — same
structural intent (don't slide from analysis to action without
explicit user confirmation), different mechanism.

`research.publish` is the hard gate at the end of the `deep-research`
walker; the rendered report exists but isn't written / acted on until
the gate confirms. This is the doctrine-equivalent of SC's "STOP AFTER
RESEARCH REPORT" — implemented via the engine's gate primitive rather
than via prompt-text discipline.

## Evidence

- `EXTENSION-PLAN.md` row: `research` is the named target with
  composition `delegate → craft → gate`.
- `sc-research` summary (PR #17 subagent reports — both shallow and
  deep): SC commands the trio `tavily` (web search), `sequential`
  (multi-hop reasoning), `playwright` (browser), `serena` (cross-
  session memory), composed under `MODE_DeepResearch.md` doctrine.
  Agency-native composition omits the persona-injection layer (the
  agent walking the skill provides the judgement; agency doesn't
  inject personas in prompts).
- `deep-research` skill (Superpowers ecosystem; system-reminder listing).
- Spec 010 § "Open Question 7" and "Source fidelity §3" — the open
  Novel research questions this spec's task-F prompts target.
- Spec 020 — bi-temporal graph for durable Citation storage.
- Spec 040 — dispatch decisions on fan-out.
- Spec 043 — render the cited report.
- Spec 045 — semantic recall powers `prior-reflections` specialist + the
  contradiction-cluster heuristic.

## Followup — Implementation Status (2026-06-03)

**Verdict:** Shipped (v1 core — 3 verbs + 3 specialist roles + 2
verifier checks + 4-phase walker; web specialist defers to v2). 23
spec tests green; dogfood-validated via wire (composes Spec 040
dispatch_decision + Spec 045 reflect.recall_semantic + Spec 048
intent-chain) — a real research session emitted Citations and the
verifier returned `ok=True`.

### Done
- Folder-form capability `agency/capabilities/research/`:
  - `_main.py` — ResearchCapability class; scaffold marker; ontology
    with 4 nodes (Research/Citation/ResearchClaim/Verification),
    3 enums (Research.status, Citation.source_kind,
    Verification.status), 4 edges (CITES/SUPPORTS/CONTRADICTS/
    VERIFIES), 1 schema (research-report), 1 skill (deep-research).
  - `_lead.py` — depth-driven specialist planning (brief→1,
    standard→2, deep→4); URL-in-question heuristic adds web.
  - `_specialist.py` — 4 specialist runners:
      codebase         → grep + file walk; confidence 1.0
      prior-reflections → reflect.recall_semantic; confidence = score
      doc-corpus       → walk docs/; substring=1.0, semantic=score
      web              → injected WebSearchClient; v1 returns
                          "no driver" message (NOT exception) when
                          web_search is None
  - `_verify.py` — 2 decidable checks:
      evidence-supports-claim → substring (≥50% token overlap) OR
                                 semantic cosine ≥0.5
      contradiction-cluster   → polarity-flipped claim_supported +
                                 high topic similarity (≥0.3) → warn
  - `_findings.py` — substring_supports + semantic_score helpers.
  - `_web.py` — WebSearchClient Protocol (boundary, no default driver).
- Three verbs (lead/specialist/verify) registered + lint clean
  block-mode.
- Engine extension: `web_search` injector slot
  (`agency/engine.py:__init__` adds `web_search=None` kwarg).
- Skill walker (4 phases — plan/fan-out/verify/publish[hard]) on
  `ResearchCapability.ontology.skills["deep-research"]`. Scope +
  render phases land in v2 with `document.render(scope='research-
  report')`.
- `skills/deep-research/SKILL.md` + 2 references
  (specialist-roles.md + verification-rules.md).
- 23 tests across `test_research_capability.py` (16) and
  `test_research_verify.py` (7).

### Scope-cut for v1
- **Web specialist** — protocol shipped; default backend NONE. v2
  wraps the host's MCP `WebSearch` tool.
- **Render phase** — walker has 4 phases (no scope/render). v2 adds
  `document.render(scope='research-report')` for the render step.
- **Web reachability check** — verifier ships 2 of 3 spec'd checks;
  reachability defers until the web specialist driver lands.
- **Novel-research prompts (audit task F)** — the 5 prompts ALREADY
  shipped under `research/novel-prompts/` (S1-S5 + F1-F5). Spec 044
  validates the SHAPE — the prompts are valid `research.lead` inputs
  once a Gemini wrapper lands.

### Code-review loop (agency:code-review skill — applied informally)
- Pass 1 — contradiction-cluster logic was INVERTED (flagged low-
  similarity pairs instead of high-similarity-with-polarity-flip).
  Fixed via test_verify_flags_contradiction_cluster.
- Pass 2 — dogfooded the wire: lead → specialist(codebase) → verify
  on a real Spec 048 question; 2 citations recorded; verifier ok.

### Cluster-coherence cross-refs (Spec 047)
- C10 Research (it IS — the canonical lead+specialists+verifier
  composition Spec 047 §C10 specified).
- C04 Quality (verifier reuses similar adversarial discipline).
- C08 Memory (prior-reflections specialist directly composes Spec
  045's recall_semantic).
- C11 Orchestration (research.lead's plan honors Spec 040's
  dispatch_decision; deep depth fires S4:parallel ≥3).

## Followup — Original Implementation Status (2026-06-02)

**Verdict:** Not started — spec drafted; agency has no research surface
today.

### Done
- The dispatch substrate (`delegate` cap), the gate substrate (`gate`
  cap), and the render substrate (Spec 043 when it lands) are all
  available; this spec composes them, doesn't build them.
- Task F (Novel-research prompts) is fully specified in this spec; the
  five prompt files can be written and used standalone before the
  capability ships.

### Still to implement
- Folder + 4 axis modules.
- Three verbs (lead, specialist, verify).
- Web-search boundary driver + injector slot.
- The walker template + SKILL.md + references.
- Five Novel research prompt files (research/novel-prompts/).
- Two test files.

### Refinement needed
- Open Question 1 (web-search backend) needs a one-line policy decision
  before v1 ships (lazy-import host `WebSearch` is the lean call).
- Open Question 5 (verification mutation vs. projection) deserves a
  one-line policy call before the ontology fragment is final.
