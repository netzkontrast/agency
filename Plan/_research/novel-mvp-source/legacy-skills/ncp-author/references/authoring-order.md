# Authoring Order

A practical, linear authoring sequence for filling an NCP document from scratch. This dissolves SPEC.md §7's 8-phase workflow into a single ordered checklist that one Claude session can drive — useful before the full hexagonal multi-skill catalog (SPEC §8) exists.

When the SPEC's hexagonal architecture is built, each block below maps to one or more router skills. Until then, this is the practical playbook.

---

## Stage 0 — Project setup

1. Create or open the target NCP file (e.g., `my-novel.ncp.json`).
2. Set `schema_version: "1.3.0"` and instantiate `story` with `id`, `title`, and `created_at`.
3. Add `genre` and `logline` if known; both are optional but anchor the rest of the work.
4. Decide: single narrative (default) or multiple? Most projects need one; only commit to multiple narratives when the project genuinely has parallel Storyforms (rare, see SPECIFICATION.md §96–98).
5. Initialize `narratives[0]` with `id`, `title`, `status: "candidate"`, and empty `subtext` + `storytelling` containers.

**Maps to SPEC phases:** 1 (Premise & Concept) — partial.

---

## Stage 1 — Ideation (optional, beginner-friendly)

If the project is still pre-Storyform, populate `story.ideation` with seed nodes across `character`, `theme`, `plot`, `genre`. Each node needs only `id` + `summary`; add `tags[]` if useful for later grouping.

**Skip this stage** when starting from an existing pitch document, treatment, or detailed outline — go straight to Stage 2.

**Maps to SPEC phases:** 1 (Premise & Concept) — full.

---

## Stage 2 — Perspectives

Define the four authorial perspectives. For most stories, exactly four perspectives correspond to the four throughlines (Main Character, Influence Character, Objective Story, Relationship Story).

For each perspective:
- `id`: stable UUID-ish string
- `author_structural_pov`: one of `i | you | we | they` (lowercase, single token)
- `summary`: a 1-sentence label naming whose lens this is (often a character name plus role)
- `storytelling`: 2-3 sentences describing how that lens shapes the conflict

**Important:** Perspectives are authorial POV records, NOT character bios. Character identity goes on Players (Stage 4).

**Maps to SPEC phases:** 2 (Storyform) — perspective layer.
**Defer to:** `dramatica-theory` if uncertain how the four throughlines map to the project's central conflict.

---

## Stage 3 — Dynamics

Lock the 9 storyform dynamics. Each dynamic is a binary choice; together they form the Storyform's structural skeleton.

Required for each: `id`, `dynamic`, `vector`, `summary`, `storytelling`.

Recommended order (each constrains the next):

1. `story_driver` → `action` | `decision`
2. `story_outcome` → `success` | `failure`
3. `story_judgment` → `good` | `bad`
4. `story_limit` → `optionlock` | `timelock`
5. `problem_solving_style` → `linear` | `holistic`
6. `main_character_resolve` → `change` | `steadfast`
7. `influence_character_resolve` → `change` | `steadfast`
8. `main_character_growth` → `stop` | `start`
9. `main_character_approach` → `do_er` | `be_er`

**Defer to:** `dramatica-theory` for the *why* of each choice. `dramatica-vocabulary` for Dynamic Pair consistency. `ncp-author` only enforces that the chosen vector pairs with the right dynamic per `references/validation-rules.md` §2.

**Maps to SPEC phases:** 2 (Storyform) — dynamics layer.

---

## Stage 4 — Players

Cast the named characters into Players. Each Player is a heavyweight object — ten required fields. During drafting, placeholders are acceptable for `visual`, `audio`, `bio`, but they MUST be filled before `status: "complete"`.

For each Player:
- `name`, `role` (archetype like "Protagonist", or throughline name like "Main Character")
- `visual`, `audio`: sensory characterization — what we see and hear
- `summary`, `bio`: short pitch + longer biography
- `storytelling`: how this character is *presented* to the audience (distinct from bio)
- `motivations[]`: at least one entry, each with `narrative_function` (canonical enum), `illustration`, `storytelling`
- `perspectives[]`: link to relevant perspective IDs from Stage 2

**Maps to SPEC phases:** 4 (Character Work).
**Defer to:** `dramatica-theory` for archetype theory. `dramatica-vocabulary` for narrative_function selection on motivations.

---

## Stage 5 — Storypoints

Place the structural anchors. Storypoints are spatial — they describe *what kind of conflict lives where* in the Storyform.

For each Storypoint:
- `appreciation`: must come from canonical_appreciation (463 values, see `references/canonical-vocabulary.md`)
- `narrative_function`: optional but strongly recommended; from canonical_narrative_function (144 values)
- `illustration`: a concrete image of the Storypoint in action ("justifying bad behavior")
- `summary`: 1-sentence description
- `storytelling`: 2-3 sentences of how this Storypoint surfaces in storytelling
- `perspectives[]`: at least one perspective_id

Minimum coverage to mark `status: "draft"` complete:
- All four throughline Domains: `Main Character Domain`, `Influence Character Domain`, `Objective Story Domain`, `Relationship Story Domain`
- All four throughline Concerns: `Main Character Concern`, etc.
- Story-level: `Story Goal`, `Story Consequence`, `Story Cost`, `Story Dividends`
- MC Issue, MC Problem, MC Solution, MC Symptom, MC Response (the Pivotal Element cluster)

**Maps to SPEC phases:** 2 (Storyform) — storypoint layer.

---

## Stage 6 — Storybeats (Outline)

Sequence the temporal beats. Three scopes, in order of granularity:

1. `signpost` — 4 per throughline (16 total minimum). The act-level beats.
2. `progression` — up to 16 per throughline (64 total possible). The mid-level beats.
3. `event` — up to 64 per throughline (256 total possible, rarely all filled). Scene-level beats.

For each Storybeat:
- `scope`, `sequence` — see `references/validation-rules.md` §3 for sequence bounds
- `throughline` — one of the four (recommended explicit even though derivable from appreciation)
- `appreciation` (optional but useful for human-readability)
- `narrative_function` — the Element this beat activates
- `summary`, `storytelling`, `perspectives[]`

**Most projects only need signposts + progressions.** Event-scope is for highly detailed pre-production (e.g., interactive narrative).

**Maps to SPEC phases:** 3 (Outline) — storybeat layer.

---

## Stage 7 — Overviews

Author the audience-facing umbrella descriptions in `storytelling.overviews`. Three valid labels:

- `Logline` — single-sentence pitch
- `Genre` — 1-2 sentence genre framing
- `Blended Throughlines` — single description that fuses MC, IC, OS, RS into one audience-facing argument summary

These are the texts that appear on dust jackets, query letters, and pitch decks.

**Maps to SPEC phases:** 5 (Worldbuilding overlap), partly 1.

---

## Stage 8 — Moments

Convert Storybeats into Moments — the actual scene/chapter scaffolding the prose will be drafted from.

For each Moment:
- `summary`: 1-sentence pitch of the moment
- `synopsis`: longer description of what happens
- `setting`, `timing`: where and when
- `imperatives`: what this moment MUST achieve (often a 3-bullet list)
- `audience_experiential_pov`: which narrative POV the audience experiences
- `act`, `order`: optional positional fields
- `fabric[]`: optional Story Limit encoding (`{type: "space"|"time", limit: <int>}`)
- `storybeats[]`: ordered list of `{sequence, storybeat_id}` references

**Important:** A single Storybeat MAY appear in multiple Moments. Conversely, a Moment MAY contain multiple Storybeats from different throughlines firing simultaneously.

**Maps to SPEC phases:** 6 (Scene Drafting) — pre-prose scaffolding only. Actual prose lives outside NCP.

---

## Stage 9 — Validate

Before declaring `status: "complete"`:

1. Run schema validation (`scripts/validate.js` once available, or `node upstream/tests/validate-file.js path.json`).
2. Walk the checklist in `references/validation-rules.md` §8.
3. Hand off to `dramatica-vocabulary` for Quad/Pair audit if KTAD coherence matters.
4. Hand off to `dramatica-theory` if any Storyform choice still feels uncertain.

**Maps to SPEC phases:** 7 (Revision & Consistency Checks).

---

## Stage 10 — Prose drafting (out of NCP scope)

The actual scene prose belongs in separate files (`.md`, `.docx`, etc.) with cross-references back to `moment.id` for traceability. NCP holds intent; it does not hold prose.

**Maps to SPEC phases:** 6 (Scene Drafting) — prose layer, 8 (Editing).
**Defer to:** project-specific orchestrator skill (e.g., `novel-architect` if it exists for the project).

---

## Quick reference: required minimum for each `status`

| Status      | Minimum bar                                                                    |
| ----------- | ------------------------------------------------------------------------------ |
| `candidate` | `story.id`, `story.title`, at least one narrative entry                         |
| `draft`     | All 4 perspectives, all 9 dynamics, at least 1 Storypoint per throughline       |
| `complete`  | Full `players[]`, Storypoints covering all required slots, at least 16 signpost storybeats, all required overviews, every storybeat referenced by at least one moment |
