# Novel Writing — Gemini Deep-Research Prompt Suite

A set of five self-contained Gemini Deep-Research prompts surveying the **2026 state-of-the-art** in novel writing, Dramatica theory, agentic AI-assisted authoring, and the canonical methodologies for structuring novel concepts and outlines.

> **Self-contained by design.** Each prompt inlines all the knowledge
> Gemini needs to do the research. No external references that aren't
> public web URLs Gemini can fetch. No assumptions about the requester's
> codebase, internal projects, or specifications.

## The five prompts

| File | Topic | Output |
|---|---|---|
| [`F1-novel-writing-sota.md`](F1-novel-writing-sota.md) | The 2026 SOTA for novel writing frameworks, methodologies, theory | Comprehensive landscape survey + 12+ source bibliography |
| [`F2-dramatica-comprehensive.md`](F2-dramatica-comprehensive.md) | Dramatica theory comprehensive: 4 throughlines, 8 archetypes, 64 elements, NCP, computational implementation | Theory primer + 2026 ecosystem state |
| [`F3-agentic-novel-writing-sota.md`](F3-agentic-novel-writing-sota.md) | 2026 SOTA for AI-assisted / multi-agent / agentic novel writing | Tools, papers, workflows survey |
| [`F4-novel-concept-structuring.md`](F4-novel-concept-structuring.md) | How to structure a novel CONCEPT (logline → premise → character → world → theme) | Methodology comparison + recommended pipeline |
| [`F5-novel-outline-structuring.md`](F5-novel-outline-structuring.md) | How to structure a novel OUTLINE (beat-by-beat, scene-by-scene, the canonical patterns) | Methodology comparison + recommended outline shape |

## How to use them

1. **Pick the prompt** that matches the survey you need.
2. **Copy-paste** the full prompt body into Gemini Deep Research (or any
   comparable research tool). The prompt is self-contained — it carries
   its own scope, source-quality rules, and output format requirements.
3. **Review** the returned report against the per-prompt `## Acceptance`
   checklist.
4. **Save** the verified report locally for downstream synthesis into
   your own design / planning / implementation work.

## Why these five questions

Novel writing is a centuries-old craft with a thick layer of contemporary
practice (Save-the-Cat, Story Grid, Snowflake, Dramatica), a fast-moving
agentic AI overlay (multi-agent narrative generation, AI co-writing tools,
narrative-coherence enforcement), and a lot of opinionated noise. The five
prompts triangulate the field:

- **F1** establishes the landscape (what frameworks are alive in 2026 and
  how do they relate).
- **F2** deep-dives Dramatica — the most-formally-structured of the
  frameworks, and the one with the deepest computational implementations,
  because it shaped the field's vocabulary even outside its users.
- **F3** is the AI/agentic axis — 2024–2026 has been a major shift; SOTA
  needs to be re-surveyed (LLM-based co-writing, multi-agent coordination
  for long-form, RAG over story-bibles, etc.).
- **F4** is the concept-shaping axis — how do practitioners go from
  "what's this story about?" to a workable foundation.
- **F5** is the outlining axis — how do practitioners go from concept to
  a structured scene-level plan ready for drafting.

Together: the input space for any computational tool, agentic workflow, or
authoring methodology that touches novel writing as of 2026.

## Source-quality discipline (applies to every prompt)

Every prompt enforces three universal rules:

1. **Recency.** 2026 SOTA means primary references must be 2022+ where
   possible; pre-2022 references must be supplemented with a 2024+
   confirmation that the methodology / framework / tool is still in
   active use.
2. **Primary sources.** A peer-reviewed paper, a canonical
   methodology-author book, or a production tool's official
   documentation outranks a blog post or a YouTube video. Gemini is
   expected to surface and cite primary sources.
3. **Distinguish framework vs. tool vs. taste.** Many novel-writing
   recommendations are taste-claims dressed as principles. The
   acceptance checklists ask Gemini to FLAG taste-claims as taste-
   claims, not present them as SOTA.

## What's deliberately out of scope across all 5

- **Genre-specific guidance** at the marketing/category level (cozy
  mystery word counts, romance subgenre tropes by year, etc.) — that's
  market intelligence, not writing methodology.
- **Marketing / publishing / business of novels** — distinct field.
- **Short-form fiction** (short stories, novellas) — different craft
  with different conventions; novel-specific focus.
- **Non-fiction memoir / narrative non-fiction** — overlaps but is its
  own field.
- **Screenwriting** — referenced where it informs novel methodology
  (Save-the-Cat originated as a screenwriting framework) but not the
  primary target.

## What to do with the verified responses

These responses are general-purpose domain research. Once verified, they
can inform any downstream synthesis — authoring tool design, agentic
workflow architecture, AI co-writing prompts, educational material, or
your own writing practice. The prompts deliberately do NOT mandate a
specific consumer; they produce knowledge.
