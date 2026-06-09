# F3 — Agentic Novel Writing: 2026 SOTA Survey

> **Audience:** Gemini Deep Research (or equivalent).
> **Deliverable expected:** ≤ 6500 tokens, cited markdown.
> **Self-contained:** all context Gemini needs is in this prompt.

---

## Question

What is the **2026 state-of-the-art** for **agentic AI-assisted novel
writing** — the use of LLMs, multi-agent systems, retrieval-augmented
generation, and structured workflows to help write long-form fiction
(novels, novellas, and novel-length serials)?

Specifically: not just "an LLM that writes for you," but **systems and
methodologies** that:

- Maintain coherence across novel-length spans (60K–150K+ words).
- Coordinate multiple AI roles (planner, drafter, editor, continuity-
  checker, character-voice keeper).
- Integrate with author workflows (co-writing, draft review, outline
  expansion, scene generation from beats).
- Use structured representations (story bibles, character ladders,
  plot graphs, narrative state machines) as grounding.
- Address the hard problems of long-form fiction (continuity, voice
  consistency, foreshadowing, narrative tension, character arc
  fidelity).

The audience is someone designing the next generation of agentic
novel-writing tools or workflows. They need to know what's been tried,
what works, what doesn't, and what's actively shipping in 2026.

## What Gemini needs to cover

### A. Commercial AI co-writing tools (2024–2026)

The shipping landscape:

- **Sudowrite** — what does it do? What's its agent architecture? How
  does it handle long-form continuity?
- **NovelAI** — text generation + lorebook system; how does the
  lorebook work as long-form grounding?
- **NovelCrafter** — methodology-driven novel-writing workbench.
- **Squibler** — outlining + AI drafting.
- **Plot Bunni** — beat-sheet-driven AI drafting.
- **Sassbook AI Writer**, **Shortly AI**, **Jasper AI fiction module**
  — surface the live ones, drop the discontinued.
- **Claude Projects / ChatGPT custom GPTs for fiction** — the use of
  general-purpose LLM platforms with author-curated context.
- **Cursor / Continue for fiction** — code-editor-style tools adapted
  for prose.

For each: what's the agent architecture (single LLM call vs. multi-step
vs. multi-agent)? How does it ground long-form context? What's the
2024+ user-base evidence?

### B. Multi-agent novel-writing research

Academic and industry research on multi-agent systems for long-form
narrative:

- **Multi-agent story generation** papers (LLM agents specialised by
  role: world-builder, plot-architect, character, prose-stylist,
  continuity-checker).
- **Long-form generation** papers (Re3 (Yang et al.), DOC (Yang et al.
  2023), the Re3 + DOC family, NovelGen, AutoGen for fiction, CAMEL
  for fiction).
- **Story bibles as RAG context** — papers and projects using
  retrieval-augmented generation over an author-curated story bible.
- **Narrative-coherence enforcement** — papers using LLMs as judges
  to flag continuity errors mid-draft (consistency models, character
  tracking, world-state tracking).
- **Hierarchical generation** — outline → chapter → scene → paragraph
  drilldown architectures.
- **Agentic workflow systems** (LangGraph, CrewAI, AutoGen) applied
  to fiction generation.

### C. Author-facing methodologies (2024+)

How working novelists actually integrate AI:

- **Prompt-engineering for fiction** — the published patterns; system
  prompts that elicit specific voices/styles; "few-shot with style
  exemplars"; multi-turn dialogue patterns.
- **The "AI as drafter, human as editor" workflow** — best practices
  + critiques.
- **The "AI as outliner, human as drafter" workflow** — best practices
  + critiques.
- **The "AI as continuity-checker" workflow** — using AI on completed
  drafts as a beta-reader.
- **Author-disclosed AI use** — published-novel case studies where the
  author has been transparent about AI involvement (positive or
  negative).
- **Author resistance** — the ethical / craft objections; Authors
  Guild positions; publishers' policies (Tor 2023+, Macmillan, Hachette,
  etc. on AI submissions).

### D. The hard problems

For each, what's the 2026 SOTA approach (or honest admission no good
approach exists):

- **Continuity across 100K words** — can the system catch "in Chapter
  3 the protagonist's eyes were brown; in Chapter 17 they're hazel"?
- **Character voice consistency** — does the dialogue in Chapter 22
  sound like the same character as in Chapter 2?
- **Foreshadowing and payoff** — can the system plant + harvest
  structural elements across long spans?
- **Narrative tension maintenance** — does the system avoid the LLM
  default of "everything resolves quickly and pleasantly"?
- **Subplot weaving** — can the system manage 2–4 parallel plot lines
  with their own tension curves?
- **Character arc fidelity** — does the protagonist's transformation
  actually happen across the planned beats?
- **Style as a learned constraint** — can the system maintain "this
  author's voice" across a novel-length span?

### E. The structured-grounding axis

Approaches that ground LLM generation in structured artefacts:

- **Story bibles as JSON / YAML / Markdown** — author-curated;
  retrieved at generation time.
- **Character cards / character ladders** — what fields, how used.
- **Plot graphs / scene graphs** — explicit dependency tracking.
- **Narrative state machines** — explicit world-state, character-
  state, knowledge-state per scene.
- **Dramatica-style structured story-forms** — see F2; what tools
  use Dramatica or NCP as grounding?
- **Save-the-Cat beat sheets as grounding** — beat-by-beat structure
  driving generation.
- **Custom DSLs** — INK, Yarn, ChoiceScript adapted for novel
  generation.

## Specialists (where Gemini should look)

| Source kind | Specific targets |
|---|---|
| **Commercial tool docs** | Sudowrite blog 2024+, NovelAI changelog 2024+, Squibler and Plot Bunni release notes, NovelCrafter docs |
| **Academic papers** | ACL, EMNLP, NeurIPS, ICML 2023+ on long-form generation, multi-agent fiction, narrative coherence; arXiv pre-prints (cs.CL category) 2024+ |
| **Author-community discourse** | r/WritingWithAI, r/novelai, r/sudowrite 2024+; Authors Guild publications; SFWA blog 2024+; the Substack ecosystem (J. Daniel Sawyer, etc.) |
| **Tool comparison reviews** | Reedsy blog, Kindlepreneur, Author Imprints 2024+ AI-tool comparisons |
| **Open-source frameworks** | GitHub: AutoGen, CrewAI, LangGraph — search for fiction-specific applications; "novel agent", "story agent", "fiction multi-agent" |
| **Published author case studies** | Authors who've published novels using AI workflows (note: some are controversial; surface both successful and cautionary cases) |
| **Publisher / industry policy** | Tor, Penguin Random House, Hachette, HarperCollins, Macmillan public statements on AI submissions 2023+; Amazon KDP policies 2024+ |
| **Workshops / conferences** | Worldcon, NaNoWriMo (controversial 2024 AI stance), Future of Storytelling conference 2024+, AI for Authors conferences |

## Method (verification rules)

- **Each commercial tool** must have 2024+ evidence (release note,
  blog post, user thread, comparison review). Discontinued or stale
  tools get a "discontinued / stale" tag.
- **Each academic paper** must be cited with arXiv/conference URL +
  the specific claim it supports (not just "this paper exists").
- **Author case studies** must cite the published novel + the author's
  own statement about AI use. Hearsay or speculation gets flagged.
- **For each hard problem in §D**: if no good approach exists in 2026,
  SAY SO. Don't manufacture optimism.
- **Distinguish hype from substance** — many AI fiction tools claim
  capabilities they don't deliver. Cross-check vendor claims against
  user reports.
- **Surface ethical and labour concerns** — Authors Guild, individual-
  author concerns, training-data lawsuits where they affect tool
  availability or methodology.

## Output format

```
# Agentic Novel Writing — 2026 SOTA

## A. Commercial AI co-writing tools
A table:
| Tool | Architecture | Long-form grounding mechanism | 2024+ user-base estimate | Distinctive | Maturity |

Then for the top 5 by maturity: one paragraph each on what they
actually do (cite user reports + vendor docs).

## B. Multi-agent research landscape
A table of papers / frameworks (≥ 10):
| Title | Authors | Year | Architecture | Key finding | Open-source code? |

Then ≤ 1000 words of synthesis on what works, what doesn't, and
where the research frontier is.

## C. Author-facing methodologies
Document the named workflows (drafter / outliner / continuity-checker)
and the named anti-patterns. Include ≥ 3 published-author case studies
(both positive and cautionary).

## D. The hard problems — 2026 honest assessment
For each of the 7 hard problems: 1 paragraph on the 2026 SOTA
approach. If none exists, say so explicitly. Cite the strongest
attempt in each category.

## E. Structured grounding approaches
A table comparing story-bible / character-card / plot-graph / state-
machine / Dramatica-style / beat-sheet / DSL approaches:
| Approach | Tools using it | Strengths | Weaknesses | 2024+ examples |

## F. The 2026 synthesis
≤ 800 words on:
- Which architectures are converging vs. fragmenting?
- What's the right division of labour between AI and author?
- What does the next 12–24 months likely bring?
- What's the ethical / legal landscape (training data, author
  attribution, publisher policies)?
- What would a green-field 2026 agentic novel-writing system look
  like, given everything above?

## G. Cited bibliography
≥ 25 entries; ≥ 60% from 2023+; mix of papers, vendor docs, author
case studies, community discourse.
```

## Acceptance

- [ ] Every commercial tool has 2024+ liveness evidence or a
      "discontinued" tag.
- [ ] §B cites ≥ 10 papers/frameworks with arXiv/conference URLs.
- [ ] §C includes ≥ 3 named author case studies (with novel titles +
      author statements).
- [ ] §D honestly admits where SOTA falls short on each hard problem.
- [ ] §E table covers all 7 grounding approaches.
- [ ] §F's "green-field 2026 system" sketch is grounded in §A–§E, not
      blue-sky speculation.
- [ ] Bibliography ≥ 25 entries; ≥ 60% from 2023+.
- [ ] Ethical / labour concerns are surfaced, not glossed.

## Anti-patterns (Gemini should avoid)

- Treating every AI fiction tool's marketing claim at face value.
  Cross-check against user reports.
- Confusing "this paper exists" with "this is the SOTA". Many papers
  are first attempts that didn't scale. Synthesise.
- Hyping multi-agent systems beyond their demonstrated capabilities.
  Most multi-agent fiction systems STILL struggle past ~20K words
  coherently.
- Ignoring the ethical / labour controversy. The Authors Guild has
  been vocal; surface both their position and the counter-positions.
- Recommending a tool because it's most-marketed. Cite usage evidence.
- Treating ChatGPT-with-good-prompting as "agentic". An agentic
  system has multiple coordinated steps / agents; a single LLM call
  isn't.
- Skipping §D's honest assessment. The hard problems are still hard;
  glossing over them mis-serves the reader.
- Forgetting that long-form is genuinely different from short-form.
  Many "AI writes a novel" claims are actually "AI writes 5K-word
  chapters strung together with no continuity model".
