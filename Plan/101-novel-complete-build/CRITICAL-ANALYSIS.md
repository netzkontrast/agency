# Critical-Thinking Analysis — Novel Spec Set (101–108)

> Iteration 12 (2026-06-07). User directive: *"use critical thinking
> Methods (Look at the-agency-system repo „Research prompt optimizer"
> (Copy over as Source for prompting)) - and use those Methods to
> Improve the novel specs from different viewpoints"*.
>
> Applies the **eight intent capability methods** (per agency Spec 091:
> decompose, assumptions, premortem, first_principles, inversion,
> steelman, second_order, tradeoffs) to the 11-iteration novel spec
> set. Each method surfaces a specific improvement landed in this
> commit.
>
> Research-prompt-optimizer source imported under
> `Plan/_research/novel-mvp-source/research-prompt-optimizer/`
> (catalog + 5-phase workflow definition).

## Method 1 — DECOMPOSE (MECE sub-problems)

**Question**: Are the 7 clusters MECE? What's missing?

**Findings**:
- ✅ Covered: lifecycle, storyform, prose, research, catalogue,
  manuscript, gates + iter-extensions (complexity, writer-workflow,
  prompt-engineering, research-entity)
- ❌ **MISSING — distribution-channel optimization** (KDP vs Apple
  Books vs IngramSpark per-channel metadata)
- ❌ **MISSING — post-publication feedback loop** (reviews/ratings
  ingestion as feedback into the design's quality reports)
- ❌ **MISSING — IP-extension framework** (audio drama / TTRPG /
  video game / film adaptation as sibling artefacts to the novel)

**Improvement landed (iter-12)**: ADR-13 adds a `Distribution`
sub-cluster to 107 manuscript covering per-channel metadata + a
`PostPubFeedback` node to 106 catalogue covering ingested
reviews/ratings. IP-extension framework deferred to a future spec
(too out-of-scope for this wave).

## Method 2 — ASSUMPTIONS (load-bearing vs incidental)

**Question**: What load-bearing assumptions does the design rest on?
If any fails, what breaks?

**Load-bearing**:
1. **Dramatica as canonical story-design framework** (103)
   — Risk: writers who use Story Grid / Save-the-Cat / pure intuition
     find storyform cluster dead weight
   — Mitigation: 103 must be **optional** for simple novels (already
     true via `Novel.storyform_required: bool`); add explicit
     "story-method-agnostic" path

2. **Graph-canonical, file-derived** (ADR carried from kohaerenz)
   — Risk: writers expecting Scrivener-style file-first UX find graph
     model alien
   — Mitigation: import/export verbs (iter-6) provide bidirectional
     bridge; reconcile_disk_with_graph (iter-6) helps

3. **LLM availability for Path B** (092 G3 driver)
   — Risk: offline writers / OPENROUTER_API_KEY absent → Path B
     unavailable
   — Mitigation: Path A (rule-based) is always default; iter-5
     LLM-failure handling already specified

4. **Markdown as primary prose format**
   — Risk: writers using rich-text / Word as primary find conversion
     friction
   — Mitigation: docx/Scrivener imports cover initial onboarding

**Incidental** (could change without breaking):
- pytest as the test framework
- SQLite as the graph store
- Specific data formats (YAML vs JSON for config)

**Improvement landed (iter-12)**: 101 gains an "Assumption manifest"
section explicitly listing load-bearing vs incidental, so the
implementation team knows where flexibility lives.

## Method 3 — PREMORTEM (assume-failed; what went wrong?)

**Question**: 6 months after 101 → Shipped, the design is judged a
failure. What happened?

**Top failure modes**:

1. **Writers found it too complex** (most likely)
   — Cause: 30+ verbs in 104 prose alone after iterations 7+8+11
   — Mitigation: ROADMAP.md already sequences Wave-1 = simple-novel
     baseline; add "minimal viable novel" workflow doc

2. **Dramatica adoption was too low**
   — Cause: 103 was the biggest spec; if it sits unused, the
     decidability advantage is lost
   — Mitigation: make 103 truly optional + ship a "story-method-
     agnostic" walkable skill that uses ONLY beat sheet without
     storyform constraints

3. **Prompt-engineering layer (iter-11) produced bad outputs**
   — Cause: A/B variants + scoring requires lots of human eval;
     without it, no learning loop closes
   — Mitigation: pre-seed AntiPattern library with known failure
     modes from literature (filter words, on-the-nose dialogue);
     ship as `data/reference/prose/anti-patterns/<lens>.yaml`

4. **Migration from existing drafts (Scrivener/Word) broke**
   — Cause: iter-6 import discipline is round-trip-lossless ON BODY
     but not on metadata; complex Scrivener projects have nested
     binder hierarchies my spec didn't handle
   — Mitigation: pre-import "dry-run + manual review" gate; surface
     unmigrated metadata as findings

5. **The 6-level hierarchy (Series→Volume→Part→Book→Chapter→Scene)
   confused simple-novel writers**
   — Cause: iter-2 made it opt-in but the documentation didn't
     emphasize this; new users saw "6 levels!" and bounced
   — Mitigation: 102's first-PR-scope section ALREADY makes Chapter
     → Scene the default; iter-12 reinforces this with explicit
     "minimal viable novel" example

**Improvement landed (iter-12)**: New doc `MINIMAL-VIABLE-NOVEL.md`
shows the smallest end-to-end workflow (4 verbs, 1 skill, no
storyform required).

## Method 4 — FIRST PRINCIPLES (strip to fundamentals)

**Question**: What's the irreducible core?

**The irreducible novel-capability**:
- A novel = a structured narrative artifact
- Structure = decidable (where possible) + emergent (prose)
- Production = research → outline → draft → revise → ship
- Quality = gated, audited, traceable

That's 4 fundamentals. Everything in iterations 1-11 is **convention**,
**discipline**, **policy**, **decoration** — useful, but not the core.

**What you really need at MINIMUM**:
1. State a Novel
2. Capture a Premise + Outline (1-3 walkable phases)
3. Draft Chapters
4. Revise (1+ pass)
5. Render manuscript

That's 5 verbs across 102 + 104 + 107.

**Improvement landed (iter-12)**: 101 gains a "First-Principles
Minimum" section explicitly identifying these 5 verbs. The minimum
viable novel ships with: `conceptualize`, `create_novel`,
`create_chapter`, `chapter_report`, `render_manuscript`. Everything
else is opt-in.

## Method 5 — INVERSION (what guarantees failure?)

**Question**: What MUST we NEVER do?

**Hard-NEVERs** (violations = design failure):
1. Edit `agency/engine.py` or `agency/capability.py` core (drop-in bar)
2. Translate canon prose (ADR-1)
3. Silently flip `generated_by="llm"` → `human` (ADR-7)
4. Make any iter-2+ feature mandatory for simple novels (opt-in
   discipline)
5. Add a 7th driver protocol (6 = `StateDriver`/`TextDriver`/
   `AudioDriver`/`DBDriver`/`CloudDriver`/`FormatDriver` is the cap;
   `llm` driver is shared substrate)
6. Allow gates without human escape valves (every hard gate has
   `elicit`)
7. Couple cluster-to-cluster via direct imports (use `ctx.call`)

**Improvement landed (iter-12)**: 101 gains an explicit "Invariants
That Cannot Be Broken" section enumerating the 7 hard-NEVERs.
`scripts/check-drop-in-bar` (already specified) enforces #1; CI
linter rules can enforce some of the others.

## Method 6 — STEELMAN (strongest counter-case)

**Question**: What's the strongest argument the design is WRONG?

**Steelman**: *"This design tries to be a graph-native novel-writing
IDE with built-in research, Dramatica analysis, multilingual canon
preservation, multi-author collaboration, LLM-assisted drafting with
prompt engineering, audiobook prep, marketing tie-ins, series
management, and IP-extension. That's not a focused product — it's a
kitchen sink. A novelist who just wants to FINISH HER NOVEL has no use
for 95% of this. The drop-in bar means it costs the substrate nothing
to add — but it costs the USER everything to navigate. The 30+ verbs
in 104 alone exceed what any one writer can hold in working memory."*

**Best response**:
- The design IS opt-in: simple writers use 5 verbs (per First Principles)
- The clusters compose: a writer can enable JUST 102+104 and have a
  working novel experience
- The verb count is a FEATURE for power users (multi-volume epic
  authors, hard-SF writers, multi-author teams); simple users don't see
  most of them
- Discoverability via `agency:help` + walkable skills means writers
  don't need to memorize the verb list
- The drop-in bar makes the substrate cost zero; the per-cluster extras
  (`[novel-format]`, `[novel-db]`, etc.) keep install lean

**Improvement landed (iter-12)**: 101 explicitly addresses the
steelman in a new "Why this isn't a kitchen sink" section. Documents
the discoverability story (`agency:help` → walkable skills → verb
introspection) so writers find what they need without memorizing.

## Method 7 — SECOND-ORDER (and-then-what?)

**Question**: After 101 ships, what happens downstream?

**Consequence chain**:

1. **Writers using it generate huge volumes of provenance data**
   → 2. Research opportunity: study creative process via the provenance
        graph
   → 3. Publishers ask for tooling to integrate with the catalogue +
        manuscript clusters for streamlined acquisition
   → 4. Specific tooling emerges (e.g. an agent that ingests a
        publisher's submission requirements + auto-formats the
        manuscript)
   → 5. Some writers reject the substrate over privacy concerns; we
        need clear data-ownership messaging

2. **Dramatica community contributes ontology improvements**
   → 6. ontology.json grows beyond 304 entries; we need versioning
        discipline (already in iter-9 schema migration)
   → 7. Forks emerge for non-Dramatica frameworks (Save-the-Cat,
        Story Grid) — pattern is reusable

3. **Prompt-engineering pipeline (iter-11) becomes a model**
   → 8. The 10-builder family pattern gets copied by other
        domain-capabilities (music, screenplay, journalism)
   → 9. A `agency.prompt-engineering` substrate capability emerges
        from the common pattern

4. **AI-use disclosure (ADR-7) becomes table-stakes**
   → 10. Traditional publishers reject undisclosed AI-assistance
        more aggressively
   → 11. The disclosure metadata becomes a publishing-industry
        standard

**Improvement landed (iter-12)**: 101 gains a "Downstream Predictions"
section that documents the consequence chain. Helps the implementation
team prioritize Wave 4 PRs against likely future demand.

## Method 8 — TRADEOFFS (options × criteria)

**Question**: What other design shapes were considered? Why this one?

**Matrix** (options × criteria):

| Option | Drop-in bar | Writer accessibility | Decidability | Coverage breadth | Implementation cost | Wave-1 ship time |
|---|---|---|---|---|---|---|
| **Current** (7 clusters, opt-in iter-2+, all iterations) | ✓ | medium | high | wide | high | ~3 weeks |
| Slim (102+104+108 only, no iter-2+) | ✓ | **high** | medium | narrow | low | **~1 week** |
| Fat (all features mandatory) | ✓ | low | high | wide | very high | ~6 weeks |
| Plugin-per-cluster (separate agency-novel-X plugins) | medium | medium | high | wide | very high | ~6 weeks |
| Embed in music plugin (music+novel together) | ✓ | medium | high | wide | medium | ~2 weeks |
| Use external Scrivener API (no agency cluster) | n/a | high | low | narrow | low | ~3 days |

**Selected**: Current (7 clusters, opt-in iter-2+).
**Reason**: Best balance of coverage + decidability + drop-in compliance.
Wave-1 ships the slim path (1 week); iter-2+ extends.

**Tradeoff acknowledged**: Wave-1-to-Wave-3 takes ~3 weeks instead of
1; the additional 2 weeks buy the complex-novel coverage that
distinguishes this from a simple Scrivener clone.

**Improvement landed (iter-12)**: 101 gains a "Design Alternatives
Considered" section documenting why Current was selected over the
5 alternatives.

## Research-prompt-optimizer pattern integration (iter-12)

The imported `agentic-tool-catalog.md` references a 5-tool research-
prompt-optimizer family:

1. `research_intent_capture(seed_query, out_path)` — Phase-1: turn a
   seed query into intent YAML (LLM-assisted)
2. `research_brief_render(intent_yaml, out_dir, modules=None)` —
   Phase-2: deterministic render (decidable)
3. `research_brief_audit(brief_path)` — Phase-3: reader-test
   simulation (LLM-assisted)
4. `research_brief_finalize(brief_path, out_zip)` — Phase-4: package
   artefact set (decidable)
5. `research_catalog_list(category=None)` — Phase-5: catalog of
   A/B/C × M01-M12 modules (decidable)

**Applied to 105 iter-12**: the existing iter-10 research pipeline
(ingest → extract → map → render) gains a **Phase 0: intent capture**
that runs BEFORE source ingestion:

```python
@verb(role="act")
def research_intent_capture(self, novel: str,
                            seed_query: str) -> ToolResult:
    """Per the research-prompt-optimizer pattern. Turn a free-form
    seed query ('the novel needs background on quantum decoherence and
    Kantian epistemology') into a structured intent YAML:
    {topic, sub_topics, depth, deliverable, success_criteria,
     deadline, audience}.

    The intent YAML drives the ingestion + extraction stages — it
    tells extract_entities WHICH entity kinds matter, tells
    chapter_research_brief what shape the output should take, and
    feeds the AB module-catalog (next verb)."""

@verb(role="transform")
def research_catalog_list(self, category: str = "") -> ToolResult:
    """List the A/B/C × M01-M12 research-module catalog (36 modules
    per the imported catalog). category options: A (foundational) /
    B (extension) / C (synthesis). Used by chapter_research_brief to
    select which modules apply."""

@verb(role="effect")
def research_brief_audit(self, brief_artefact_slug: str) -> ToolResult:
    """Reader-test simulation: can a fresh reader locate task,
    constraints, deliverable, success criteria from the brief?
    Uses the `llm` driver if bound; falls back to rule-based check.
    Records a BriefAudit node with findings."""
```

These bring the rigor of research-prompt-optimizer's research-brief
discipline to the novel research pipeline.

## Summary — what changed in iter-12

| Method | Change in spec set |
|---|---|
| Decompose | ADR-13: Distribution + PostPubFeedback; IP-extension deferred |
| Assumptions | 101 gains Assumption Manifest section |
| Premortem | New MINIMAL-VIABLE-NOVEL.md doc (4 verbs + 1 skill) |
| First Principles | 101 gains "First-Principles Minimum" section (5 core verbs) |
| Inversion | 101 gains "Invariants That Cannot Be Broken" (7 hard-NEVERs) |
| Steelman | 101 gains "Why this isn't a kitchen sink" + discoverability story |
| Second-order | 101 gains "Downstream Predictions" consequence chain |
| Tradeoffs | 101 gains "Design Alternatives Considered" (6-option matrix) |
| Research-prompt-optimizer | 105 gains 3 verbs (Phase 0 intent + catalog + audit) per the imported 5-phase pattern |
