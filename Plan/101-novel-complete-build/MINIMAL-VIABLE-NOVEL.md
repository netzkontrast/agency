# Minimal Viable Novel — the simplest end-to-end workflow

> Iteration 12. Per the **premortem** critical-thinking pass, the
> design risks scaring off simple-novel writers with verb count. This
> doc shows the **5-verb path from idea to manuscript** so the
> simple-novel use case is documented as the default, not the
> exception.

## The five verbs

A writer with a single-volume, single-POV, monolingual,
no-storyform-required novel uses exactly these 5 verbs across 3
clusters:

| # | Verb | Cluster | Phase |
|---|---|---|---|
| 1 | `conceptualize` | 102 | Capture premise + theme + tracklist |
| 2 | `create_novel` | 102 | Initialise novel root from templates |
| 3 | `create_chapter` | 102 | Add chapters one by one |
| 4 | `chapter_report` | 104 | Per-chapter readability + voice diagnostics |
| 5 | `render_manuscript` | 107 | Render the final manuscript |

That's it. The walkable skill `novel-concept` (10 phases) + the 5
verbs above are the **minimum viable novel**. No storyform required.
No multi-POV gates. No subplots. No worldbuilding sub-graph. No
audiobook prep. No prompt engineering.

## The walkable skill: `novel-concept` (already specified in 102)

10 phases (premise → genre → audience → POV → setting → characters-
core → dramatica-seed → outline-shape → series-hypothesis →
confirmation HARD GATE). For a simple novel, the user can SKIP phases
7 (dramatica-seed) and 9 (series-hypothesis) — they emit warnings but
don't block.

## Example session (annotated)

```python
# Step 1 — capture the idea
agency:
  capability_novel_capture_idea(
    text="A small-town librarian discovers her grandmother's diary "
         "reveals a long-hidden family secret tied to local history.")
  → {idea_id: "idea:abc123"}

# Step 2 — promote idea to novel concept
agency:
  capability_novel_promote_idea(idea_id="idea:abc123")
  → walkable skill: novel-concept starts at phase 1

# Step 3 — walk the 10 phases (or just 8 if skipping dramatica + series)
agency:
  capability_develop_skill_walk(intent_id=..., name="novel-concept")
  # Iteratively fill each phase's `produces` keys; phase 10 is hard
  # gate (elicit asks "is this concept ready to draft?")

# Step 4 — initialise novel
agency:
  capability_novel_create_novel(
    author="Jane Author",
    title="The Library at Whitefall",
    genre="literary mystery",
    premise="<from phase 1>")
  → {novel_slug: "the-library-at-whitefall"}

# Step 5 — for each chapter, create + draft + diagnose
for ch in range(1, 25):
    agency:
      capability_novel_create_chapter(
        novel="the-library-at-whitefall",
        slug=f"ch{ch:02d}",
        number=ch)
    # Writer drafts the chapter body in the rendered chapter.md
    # OR uses chapter_draft_assisted if [novel-llm] extra is bound
    agency:
      capability_novel_chapter_report(
        chapter=f"ch{ch:02d}",
        lyrics="<chapter body>")
    → {readability, voice_signature_drift, filter_word_count, …}

# Step 6 — when complete, render the manuscript
agency:
  capability_novel_render_manuscript(
    novel="the-library-at-whitefall",
    format="manuscript")  # Times New Roman, double-spaced, etc.
  → artefact: manuscript-format
```

## What this skips

The simple novel does **not use**:
- 103 storyform cluster (Dramatica engine) — entirely optional
- Multi-volume hierarchy (Volume / Part / Book) — single Novel root suffices
- World subschema (Culture / Religion / Language / MagicSystem) —
  contemporary literary novels don't need it
- 99% of iteration-2+ additions (multi-POV gates, multilingual canon,
  multi-author, audiobook prep, prompt engineering, research-entity
  ontology)
- The 4 publication gates (pre-draft / beta-ready / query-ready /
  publish-ready) — the writer ships when they're ready, no required
  gates

## When to scale up

| Add this | When |
|---|---|
| 103 storyform | The novel has clear dramatic structure and the writer wants Dramatica validation |
| Iter-2 Volume hierarchy | The novel is part of a series OR has explicit Parts |
| Iter-2 World subschema | Fantasy / SF where world rules need consistency |
| Iter-2 multi-POV gates | 2+ POV characters |
| Iter-5 AI-use disclosure | LLM-assisted drafting (any chapter via Path B) |
| Iter-7 character psychology | Literary fiction with deep character work |
| Iter-10 research-entity | Research-heavy fiction (hard SF, historical, biographical) |
| Iter-11 prompt engineering | Heavy LLM-assisted drafting + iteration on prompts |
| Iter-12 distribution | Self-publishing across multiple channels |

The progression is **organic** — writers turn on features as their
project needs them. No upfront commitment to the full complexity
surface.

## The discoverability story

A writer who installs the novel capability can run:

```bash
agency novel help        # lists every verb organized by cluster
agency novel skills      # lists every walkable skill
agency intent suggests   # given the current intent, recommend a skill
```

The CLI surface (per Spec 079) provides this for free. Writers
discover features by need, not by reading a 2000-line spec.
