# F1 — Novel Writing: 2026 SOTA Landscape Survey

> **Audience:** Gemini Deep Research (or equivalent).
> **Deliverable expected:** ≤ 6000 tokens, cited markdown.
> **Self-contained:** all context Gemini needs is in this prompt.

---

## Question

What is the **2026 state-of-the-art** for novel writing methodologies,
theory, and frameworks? Surface the **alive, in-use, and influential**
approaches — distinguishing them from historical artefacts that no longer
have practitioner uptake.

The survey should cover **five families** of methodology:

### 1. Story-structure frameworks

Canonical sequence-of-events frameworks practitioners use to plan a
novel's macro-shape:

- **Save the Cat! Writes a Novel** (Jessica Brody, 2018; based on Blake
  Snyder's 2005 screenwriting work) — the 15-beat structure with the
  "beat sheet" template.
- **Story Grid** (Shawn Coyne, 2015+) — the 5-leaf clover model; global
  story + internal story + genre + obligatory scenes + quintet arcs.
- **The Snowflake Method** (Randy Ingermanson) — ten-step expansion
  from a one-sentence summary to a full draft.
- **Anatomy of Story / 22 Steps** (John Truby, 2007 + updates) — moral
  argument + 22 narrative steps.
- **Story** (Robert McKee, 1997 + updates) — three-act structure with
  inciting incident, climax, resolution; the controlling idea.
- **Hero's Journey** (Joseph Campbell 1949 → Christopher Vogler 1992
  updates) — the 12-stage monomyth.
- **The Five-Act Structure** (Aristotelian / Freytag's pyramid) —
  exposition, rising action, climax, falling action, denouement.
- **Eight-Sequence Structure** (originally Frank Daniel; adapted for
  novels) — eight ~30-page sequences.
- **Three-Act Structure** (Syd Field 1979) — setup, confrontation,
  resolution with two plot points.

### 2. Story-content / theme frameworks

How practitioners structure WHAT happens vs. just WHEN:

- **The Story Engine** (Lisa Cron, 2020) — story as protagonist's
  evolving belief about the world.
- **Wired for Story** (Cron, 2012) — neuroscience-grounded story
  craft; story as evolutionary cognitive tool.
- **Into the Woods** (John Yorke, 2013) — fractal five-act structure
  applied at scene, sequence, and act level.
- **The Anatomy of Genres** (John Truby, 2022) — genre-as-philosophy;
  how content shapes form.
- **The Emotional Craft of Fiction** (Donald Maass, 2016) — emotional
  vs. plot mechanics.

### 3. Theory-grounded frameworks

Frameworks grounded in a theoretical model of story:

- **Dramatica** (Melanie Anne Phillips & Chris Huntley, 1993; updates
  through 2020s) — story as a problem-solving model of mind; 4
  throughlines, 8 archetypes, 64 elements. See F2 for deep dive.
- **The Plot Whisperer** (Martha Alderson, 2011) — three-energy plot
  planning.
- **Linguistic / cognitive narratology** academic frameworks (Bal,
  Genette, Herman, Ryan).
- **Affect theory** applications to narrative (Sianne Ngai 2020+).

### 4. Discovery-vs-outline poles

The plotter ↔ pantser spectrum:

- **Pure outlining** (Snowflake, full pre-draft scene list).
- **Hybrid "plotter-pantser"** (rough beats + discovery between).
- **Pure discovery** (Stephen King "On Writing", George R.R. Martin's
  "gardener" model).
- **Modern hybrids**: scene-card / index-card methods (Trey Parker,
  Stewart Stafford), the zero-draft method, the Stephen Pressfield
  "Foolscap" method.

### 5. Tooling / production methodologies

Software-mediated frameworks that ARE methodologies, not just editors:

- **Scrivener** (Literature & Latte) — corkboard + binder model.
- **Plottr** — visual timeline + template-driven beat planning.
- **Campfire** — modular novel-development workbench.
- **World Anvil** — world-building-first methodology.
- **Save the Cat! Software** — beat-sheet workbench.
- **Articy:Draft** — game-narrative methodology adopted for novels.
- **AI-assisted tools** (NovelAI, Sudowrite, Plot Bunni, Squibler, etc.)
  — covered separately in F3.

## Specialists (where Gemini should look)

| Source kind | Specific targets |
|---|---|
| **Books by methodology authors** | Direct citations — Brody, Coyne, Ingermanson, Truby, McKee, Cron, Maass, Vogler, Yorke, Field, Alderson, Snyder. Cite specific editions + publication years. |
| **Production tool docs** | Official documentation pages for Scrivener, Plottr, Campfire, World Anvil, Articy:Draft 3+, Save the Cat! Software (latest version). |
| **Methodology-author courses** | Online courses, MasterClass, podcasts, Substacks where the methodology authors teach (e.g. Truby's writing classes 2023+, Coyne's Story Grid podcast). |
| **Academic narratology** | Mieke Bal "Narratology" (4th ed); David Herman "Story Logic"; Marie-Laure Ryan; Routledge Encyclopedia of Narrative Theory (2024 entries). |
| **Writing-community discourse** | r/writing, r/writers, Reddit and Discord pulse on what's actively practiced 2024–2026; SFWA blog 2024+; Authors Guild publications. |
| **Industry data** | Publishers Marketplace 2024+ deal categories; agent submission-guide patterns; what acquiring editors say is "selling" (which methodology shapes are visible in 2024–2026 acquisitions). |

## Method (verification rules)

- **Each methodology** must be evaluated against:
  1. **Origin** — author, year, key publication.
  2. **Liveness** — 2024+ evidence of active use (a 2024 podcast
     episode, a 2024 workshop offering, a 2024 published book using it,
     a 2024 tool update).
  3. **Adoption tier** — heavy (taught widely, multiple books, software
     support) / moderate (small dedicated community) / historical
     (cited but not actively taught).
  4. **Distinctive claim** — what does it offer that another framework
     doesn't?
- **No methodology accepted without a primary-source citation** — the
  author's own book/site, not a third-party summary.
- **Liveness verification:** if no 2024+ evidence exists, label as
  "historical / no longer actively taught" rather than presenting as
  current SOTA.
- **Taste-claim flagging:** rules like "novels need three acts" or
  "save-the-cat is formulaic" are TASTE; flag them as such, don't
  present as findings.

## Output format

```
# Novel Writing — 2026 SOTA Landscape

## 1. Story-structure frameworks
A table:
| Framework | Author | Year | Adoption tier | Distinctive claim | 2024+ liveness evidence |

Then for the heavy-adoption ones (top 5–8): one paragraph each on
mechanics, when it's used, who teaches it.

## 2. Story-content / theme frameworks
Same table-then-paragraphs treatment.

## 3. Theory-grounded frameworks
Same — Dramatica gets a one-paragraph summary here (deep dive in F2).

## 4. Discovery-vs-outline spectrum
A spectrum diagram (textual) placing the methodologies along the
plotter ↔ pantser axis, with notes on hybrid practices.

## 5. Tool-mediated methodologies
A table:
| Tool | Methodology embedded | Active user community estimate | Notable workflow |

## 6. The 2026 synthesis
≤ 800 words on:
- What are the top 5 frameworks any contemporary novel-writer is
  likely to encounter / be taught?
- What's the relationship between the structure frameworks (do they
  compete, or do practitioners stack them)?
- What's distinctive about 2024–2026 vs. the 2010s? (e.g. theme/
  content frameworks rising; AI-tool adoption; genre conventions
  shifting).
- What's overrated noise (popular but not actually shaping practice)?
- What's underrated signal (small community but high practitioner
  quality)?

## 7. Cited bibliography
≥ 18 entries with publication years; ≥ 70% from 2022+.
```

## Acceptance

- [ ] Every framework named is cited to its primary source (book / site /
      paper).
- [ ] Each heavy-adoption framework has 2024+ liveness evidence.
- [ ] At least 18 bibliography entries, ≥ 70% from 2022 or later.
- [ ] §6 distinguishes "actively taught" from "popular discussion-noise".
- [ ] §6 explicitly names what's distinctive about 2024–2026 (post-LLM-
      mass-adoption era for fiction writers).
- [ ] Taste-claims are flagged as taste, not findings.
- [ ] Methodologies older than 2022 with no 2024+ evidence are labelled
      "historical".

## Anti-patterns (Gemini should avoid)

- Treating every blog post recommending a framework as evidence of
  liveness. Look for production use (books in print, tool updates,
  workshop offerings, course revisions) in 2024+.
- Conflating SCREENWRITING frameworks with novel frameworks. Save-the-
  Cat originated in screenwriting; the novel-specific adaptation
  (Brody 2018) is the citation for novel SOTA, not Snyder 2005.
- Listing the Hero's Journey as if it's a contemporary methodology
  without noting it's now mostly meta-commentary (cited more often
  than actively used as a planning tool by working novelists).
- Conflating "the book sold many copies" with "the methodology is
  actively taught/used". Some books (e.g. McKee's "Story") sell
  perennially while the methodology itself has fragmented practice.
- Including ALL methodologies ever published. Filter for liveness.
- Recommending one methodology as universally best. The survey is
  descriptive, not prescriptive.
- Treating Dramatica superficially. F2 covers Dramatica in depth; F1's
  Dramatica entry is one paragraph cross-referencing F2.
