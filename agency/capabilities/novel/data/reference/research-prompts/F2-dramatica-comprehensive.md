# F2 — Dramatica Theory: Comprehensive Primer + 2026 Computational State

> **Audience:** Gemini Deep Research (or equivalent).
> **Deliverable expected:** ≤ 7000 tokens, cited markdown.
> **Self-contained:** all context Gemini needs is in this prompt.

---

## Question

**Dramatica** is a story-structure theory and software developed by
Melanie Anne Phillips and Chris Huntley, first released in 1993 (the
"Dramatica Theory" book) with continuous refinement through
Dramatica.com and the Dramatica Pro software (latest major version
released by Write Brothers).

Produce a **comprehensive primer** on Dramatica that:

1. Explains the **full theoretical model** (story-mind, throughlines,
   archetypes, elements, signposts, journeys, plot dynamics — all of
   it, in working detail).
2. Surveys the **2026 state of the theory and ecosystem** (who's
   teaching it, what tools implement it, what schemas exist, what
   open-source / research projects use it).
3. Identifies the **computational-implementation surface** (which parts
   of Dramatica can be deterministically validated vs. which require
   human judgement).

The audience is someone designing a structured authoring system or
narrative-validation tool who needs to understand Dramatica
end-to-end **without using Dramatica Pro itself**. They need to be
able to explain it to a junior developer AND defend implementation
choices against a senior Dramatica practitioner.

## What Gemini needs to cover

### Part A — The theory (working primer)

For each concept, give a working definition + how it relates to the
others. The known scope:

- **Story mind** — Dramatica's foundational metaphor: a complete story
  is a model of a single problem-solving mind.
- **Four throughlines** — Overall Story (OS), Main Character (MC),
  Impact Character (IC), Relationship Story (RS / MC-IC).
- **Throughline-to-class assignment** — each throughline is one of
  four Dramatica Classes: Universe, Physics, Mind, Psychology.
- **Concerns within classes** — each class has four concerns; story
  selects one concern per throughline.
- **Issues within concerns** — drilling down further.
- **Problems and solutions** — paired elements at the leaf level.
- **The 64 elements** — the leaves of the throughline tree; the
  building blocks of plot.
- **Quads** — 4-element groupings with rotation/neighbour relationships
  (Knowledge-Thought-Ability-Desire is one example).
- **8 archetypes** — Protagonist, Antagonist, Guardian, Contagonist,
  Reason, Emotion, Sidekick, Skeptic. Each maps to a Motivation-quad
  position.
- **Plot dynamics** — Resolve (Change / Steadfast), Growth (Start /
  Stop), Approach (Do-er / Be-er), Mental Sex (Linear / Holistic) — 4
  dynamics that gate story-form interpretation.
- **Story form** — the complete tuple of selections (throughlines +
  concerns + issues + problems + dynamics + … ) that defines a
  particular story's structure.
- **Signposts and journeys** — 4 signposts per throughline (the macro
  beats); journeys between them.
- **Storypoints and storybeats** — the granular structural anchors.
- **Storyforming vs. storyencoding vs. storytelling** — Dramatica's
  three-layer model of how an abstract story-form becomes a told story.
- **The Story Engine** — Dramatica's interactive constraint solver
  that propagates user selections through the model.

### Part B — The 2026 ecosystem state

- **Canonical sources** — Dramatica.com (the theory site), the
  Dramatica Theory book (1993, revisions), the Dramatica Pro software
  (Write Brothers, latest version), the Dramatica Story Expert (newer
  software product).
- **Authors who teach Dramatica** in 2024+ — courses, podcasts,
  YouTube channels, Substack newsletters. Is Melanie Anne Phillips
  still active? Chris Huntley? Successor teachers?
- **Notable practitioners** — published novelists who openly use
  Dramatica.
- **Critical reception** — what do other framework authors say about
  Dramatica? (Truby, McKee, Brody have all engaged in some form.)
  What do academic narratologists say?
- **Open-source implementations** — GitHub search for "dramatica",
  "story engine", "narrative coherence protocol". The Narrative
  Coherence Protocol (NCP) is a JSON-Schema attempt at machine-
  readable Dramatica artefacts; surface what versions / forks exist.
- **Schemas and machine-readable formats** — beyond NCP, any other
  attempts to formalise Dramatica (XML, YAML, custom DSLs).
- **Ports to other tools** — has Dramatica's vocabulary made it into
  Scrivener templates, Plottr templates, Campfire modules, Articy
  exports?

### Part C — The computational-implementation surface

For someone building a Dramatica-aware tool, what is **decidable** from
the theory vs. what requires **author judgement**?

- **Decidable** — relationships fully determined by the published
  Dramatica model (e.g. archetype-element pairing, throughline-class
  membership rules, dynamic-pair reciprocity, quad-element membership,
  signpost-ordering constraints per throughline).
- **Judgement-required** — relationships where the theory provides
  vocabulary but not deterministic rules (e.g. is THIS element
  appearance "earned" by the story? Does THIS character voice
  consistently express THAT archetype?).
- **Story-engine constraint propagation** — Dramatica Pro's engine
  resolves user choices into a unique story-form via constraint
  solving. Document the constraint network as well as Gemini can
  reconstruct it (from Dramatica.com pages, the published theory book,
  any open-source decompilations).
- **Coherence checks** — what consistency checks does a Dramatica-
  conformant validator run? (e.g. each throughline must have a
  distinct class; the Resolve dynamic must be consistent with the
  MC arc shape; etc.)

## Specialists (where Gemini should look)

| Source kind | Specific targets |
|---|---|
| **Canonical Dramatica** | Dramatica.com (every page on theory, archetypes, elements, classes, throughlines, signposts, plot dynamics); the "Dramatica: A New Theory of Story" book (1993, 4th ed 2004); Phillips & Huntley's later books |
| **Dramatica Pro / Story Expert** | Write Brothers product documentation; user manuals; the help text shipped with the software (often the most precise definitions) |
| **Author courses & podcasts** | Melanie Anne Phillips's YouTube channel, Storymind.com; Chris Huntley's appearances; any successor teachers active 2024+ |
| **Critical engagement** | Reviews, comparisons (Truby, McKee, Brody, Cron commentary); academic narratology papers citing Dramatica; Reddit r/writing / r/dramatica threads 2023+ |
| **Open-source code** | GitHub: "dramatica", "narrative coherence protocol", "NCP schema", "story engine". Surface forks, schema versions, what each implements. |
| **Practitioner novels** | Published novels whose authors cite Dramatica use (interviews, blog posts, acknowledgements). Surface ≥ 3 named examples. |
| **Web archive** | For the older Dramatica.com pages (the theory has been on the site since the 1990s; older articulations matter) |

## Method (verification rules)

- **Every concept definition** must cite a Dramatica primary source
  (Dramatica.com URL, the theory book chapter, or the Pro software
  documentation page).
- **No claim about decidability** without showing the rule explicitly
  (e.g. "throughline-class membership is decidable because Dramatica.com
  /<URL> states the bijection").
- **2026 ecosystem claims** require 2023+ evidence — a dead repo or
  archived course does NOT count as current SOTA.
- **Distinguish Dramatica theory from Dramatica Pro** — the theory is
  public; the software's exact constraint-propagation algorithm is
  proprietary. Document what's known publicly and what's proprietary.
- **Distinguish Phillips's Dramatica from later splinter / successor
  approaches** (the Phillips-Huntley split, if any; any "modern
  Dramatica" rebrands).

## Output format

```
# Dramatica Theory: Comprehensive 2026 Primer

## Part A — The theory
Working primer covering all the concepts in the "What Gemini needs to
cover §A" list, each with:
- 1–2 paragraph definition
- canonical source citation
- relationship to adjacent concepts
- one concrete example (a famous novel / film and how the concept
  applies)

## Part B — Ecosystem state 2026
1. Canonical sources (alive vs. archived)
2. Active teachers (named, with 2023+ evidence)
3. Practitioner novelists (≥ 3 named, with citation showing they use it)
4. Critical engagement (other framework authors; academic narratology)
5. Open-source implementations (each repo: stars, last commit, what
   it implements, what schema version)
6. Machine-readable formats (NCP and any others)
7. Cross-tool adoption (Scrivener templates, etc.)

## Part C — Computational surface
1. Decidable rules (numbered list; ≥ 10; each with source + algorithm
   sketch)
2. Judgement-required (numbered list; ≥ 5; each with why the theory
   stops short of decidability)
3. Story-engine constraint network (textual graph of which selections
   constrain which others — as much as is publicly documented)
4. Standard coherence checks (≥ 8 named checks; for each: decidable
   y/n; canonical source)

## Part D — The implementation gap
A short critical section: where does the theory shipped publicly
underdetermine the implementation? What does the Pro software encode
that the public theory leaves ambiguous? What would a public
re-implementation need to invent vs. lift?

## Part E — Cited bibliography
≥ 25 entries; ≥ 12 Dramatica.com page URLs; the canonical book; the
Pro documentation; ≥ 3 open-source code references.
```

## Acceptance

- [ ] Every concept in §A has a working definition + a primary citation.
- [ ] §A has a concrete novel/film example per concept.
- [ ] §B identifies ≥ 3 active 2024+ teachers / sources.
- [ ] §B identifies ≥ 3 named practitioner novelists.
- [ ] §C lists ≥ 10 decidable rules with algorithm sketches.
- [ ] §D honestly names the public-theory ↔ Pro-software gap.
- [ ] Bibliography ≥ 25 entries; ≥ 12 Dramatica.com URLs; the canonical
      book + Pro documentation cited.
- [ ] All claims about decidability are verifiable from the cited
      sources, not invented.

## Anti-patterns (Gemini should avoid)

- Paraphrasing Dramatica.com in the abstract without quoting the
  specific theory it documents. The theory has very specific
  terminology; substitution loses precision.
- Treating proprietary Dramatica Pro engine internals as if they were
  public. Document the gap.
- Confusing Dramatica with adjacent theories (Hero's Journey, three-
  act, Story Grid). Dramatica is distinct and incompatible with
  several common assumptions (e.g. Dramatica explicitly denies that
  every story has a single climax in the three-act sense).
- Cherry-picking famous novels as Dramatica examples without showing
  the analysis. If you cite "Casablanca is a Dramatica example",
  show which throughlines, which Resolve, etc. — or don't cite it.
- Treating dead open-source projects (last commit 2018) as current
  state. Note staleness.
- Recommending Dramatica as universally best. The survey is
  comprehensive primer + state assessment, not advocacy.
- Skipping Part D. The gap between public theory and proprietary
  engine is the most-important practical question; don't omit it.
