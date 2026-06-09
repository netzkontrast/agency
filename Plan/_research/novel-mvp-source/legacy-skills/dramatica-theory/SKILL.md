---
name: dramatica-theory
description: "Apply Dramatica narrative theory (Phillips & Huntley, *Dramatica*, 4th ed., 2001) to story analysis, storyforming, drafting, and draft diagnosis. Dramatica models a complete story as one mind solving one problem, viewed through four throughlines (Overall Story, Main Character, Impact Character, Subjective/Relationship), with a structural model of 4 Classes / 16 Types / 64 Variations / 64 Elements selected to form a \"storyform\". Ships the full source book as nine thematic reference chunks plus an in-skill conceptual overview and storyforming quick-reference. Trigger phrases include — dramatica, story mind, storyform, throughline, grand argument story, archetype, protagonist antagonist guardian contagonist sidekick skeptic reason emotion, MC resolve, mental sex, story outcome judgment driver limit, signposts and journeys, crucial element, plot dynamics, phillips huntley, dramatica anwenden, throughlines bestimmen. Also for drafts that feel flat, characters feel unmotivated, or act structure is unclear."
skill_bundles_tools:
  - tools/dramatica-nav
---

# Dramatica Theory

Working interface to Dramatica — the narrative theory developed by Melanie Anne Phillips and Chris Huntley (*Dramatica: A New Theory of Story*, 4th ed., 2001, Screenplay Systems Inc.). The full source book lives in `references/` as nine thematic chunks; six additional working-tool files (worksheet, validation, decision heuristics, anti-patterns, scene-level bridge, worked storyforms) sit alongside. This SKILL.md gives the conceptual map, a glossary, a storyforming quick-reference, workflows by phase, and a concept→file index — so most working questions are answerable without loading the 900K-character source.

## Honest framing

Dramatica makes strong claims about story structure and the underlying "Story Mind" metaphor is contested. It is not the only valid story theory, and applied dogmatically to a draft that wants to be something else, it will damage the draft. Its real strength is forcing structural decisions to be made explicitly — which exposes contradictions in drafts that *are* trying to be tightly structured stories.

Use it as a diagnostic and as a storyforming aid, not as a recipe. When the framework and the draft disagree, the draft usually wins; the disagreement is information about what the draft is actually doing.

Dramatica distinguishes its model — the **Grand Argument Story** — from other valid forms it calls **Tales**, **vignettes**, **slices of life**. Tales are not lesser; they are different. Don't try to model a Tale as a Grand Argument Story.

## Conceptual overview

### The Story Mind premise

A complete Grand Argument Story models one mind working through one problem. The audience temporarily inhabits that mind. Every character is a perspective on or a piece of that single mental process. Every plot beat is the mind in motion. Every theme is the mind weighing values. A story with several disconnected problems, or none, is a Tale — perfectly legitimate, just not what Dramatica describes.

### The four throughlines

Four perspectives on the single story problem. A Grand Argument Story has all four:

| Throughline | POV | What it is |
|---|---|---|
| Overall Story (OS) | "they" | The objective conflict — what's happening to everyone |
| Main Character (MC) | "I" | One character's personal struggle, seen from inside |
| Impact Character (IC) | "you" | The character whose existence challenges the MC's worldview |
| Subjective Story (SS) | "we" | The MC↔IC relationship, treated as its own story |

The MC is **not** necessarily the Protagonist. The MC is whoever's personal problem we live inside; the Protagonist is the OS-throughline character pursuing the Story Goal. They often coincide (Luke is both); they often don't (Scout is MC, Atticus is Protagonist in *Mockingbird*).

### The four classes

Each throughline is assigned to exactly one Class, and each Class is used by exactly one throughline. The four form two dynamic pairs: **Universe ↔ Mind** (state pair) and **Physics ↔ Psychology** (process pair).

| Class | Also called | What it is |
|---|---|---|
| Universe | Situation | An external state |
| Physics | Activity | An external process |
| Mind | Fixed Attitude | An internal state — a way of thinking that won't shift |
| Psychology | Manipulation | An internal process — thinking shifting under pressure |

Constraint: OS and SS always sit in one dynamic pair; MC and IC in the other. Once you assign OS, three of the four are constrained.

### The structural model: 4 / 16 / 64 / 64

Each of the 4 Classes contains 4 Types (16 total). Each Type contains 4 Variations (64 total). Each Variation rests on Elements drawn from the 64 Motivation Elements. The storyform pins down one item at each level for each throughline:

- **Class** — the throughline's domain
- **Type** — the throughline's **Concern** (what it's *about*)
- **Variation** — the throughline's **Issue** (the thematic question)
- **Element** — the throughline's **Problem** (the actual irritant)

Full canonical lists: `references/09-reference.md`.

### The eight archetypes

Pure archetypes carry one motivation pair each — an Action characteristic and a Decision characteristic.

**Driver Quad** (force the story forward): Protagonist (Pursue / Consideration), Antagonist (Prevent / Reconsider), Guardian (Help / Conscience), Contagonist (Hinder / Temptation).

**Passenger Quad** (color and complicate): Reason (Control / Logic), Emotion (Uncontrolled / Feeling), Sidekick (Support / Faith), Skeptic (Oppose / Disbelief).

Real characters often split or blend these across players. Rule: no single character carries both elements of a dynamic pair.

### The four stages of storytelling

1. **Storyforming** — choosing the storyform.
2. **Storyencoding** — dressing the abstract storyform in concrete subject matter.
3. **Storyweaving** — arranging the encoded material into the narrative the audience experiences.
4. **Story Reception** — modeling who the audience is and what impact the author intends.

## Quick glossary

The 30 most-used Dramatica terms. For full definitions and cross-references, load `references/09-reference.md`.

**Structural model:** *Class* (top of the structural hierarchy, 4 of them); *Type* (subdivision of Class, 16 total — also called Concern); *Variation* (subdivision of Type, 64 total — also called Issue); *Element* (subdivision of Variation, 64 Motivation Elements — also called Problem); *Storyform* (the complete set of structural choices for one story).

**Throughlines:** *Overall Story / OS* ("they"-perspective); *Main Character / MC* ("I"-perspective, the one we live inside — not the same as Protagonist); *Impact Character / IC* ("you"-perspective, challenges MC's worldview); *Subjective Story / SS* ("we"-perspective, the MC↔IC relationship as its own story).

**Characters:** *Archetype* (a character carrying pure motivation pairs); *Protagonist* (pursues the OS Goal); *Driver / Passenger* (Drivers force the story forward, Passengers don't); *Crucial Element* (the single Element where MC and OS hinge — MC sits on it); *Dynamic Pair* (two Elements in opposition: Pursue↔Avoid, Logic↔Feeling, etc.).

**Character Dynamics (4 binary choices for the MC):** *Resolve* (Change / Steadfast); *Growth* (Start / Stop); *Approach* (Do-er / Be-er); *Mental Sex* (Linear / Holistic; original term "Male/Female problem-solving" is dated).

**Plot Dynamics (4 binary choices for the story):** *Story Driver* (Action / Decision); *Story Limit* (Timelock / Optionlock); *Story Outcome* (Success / Failure); *Story Judgment* (Good / Bad).

**Story Points (per throughline or per OS):** *Story Goal* (the OS's Type-level objective); *Requirements* (what must be done to reach Goal); *Consequences* (what happens if Goal fails); *Forewarnings* (early signs of Consequences arriving); *Dividends, Costs, Prerequisites, Preconditions* (driver/passenger plot points); *Concern* (Type level), *Issue* (Variation level), *Problem* (Element level); *Solution, Focus, Direction* (per-throughline thematic positioning).

**Plot progression:** *Acts* (the four major divisions); *Sequences, Scenes, Events* (progressively finer units); *Signposts* (the four Type-level moments per throughline, one per Act); *Journeys* (the three transitions between Signposts).

**Stages:** *Storyforming* (Stage 1 — pick the structure); *Storyencoding* (Stage 2 — dress it in subject matter); *Storyweaving* (Stage 3 — arrange the narrative); *Story Reception* (Stage 4 — model the audience).

## Storyforming quick reference

The operational core. Going through these decisions yields a complete storyform. Order matters less than completeness — but skipping steps tends to produce incoherence later. For the fillable template, use `references/00-storyform-worksheet.md`.

### Step 0 — Author's Intent / Premise

Before structure: what does this story *say*? Dramatica is built to construct an argument; you can only build the argument if you know what's being argued.

- **Premise** in one sentence — what is the thematic claim?
- **Argument shape** — I want to argue that X leads to Y (and the opposite leads to ~Y).
- **Take** — am I writing *for* or *against* the premise? (Tragedy stories often argue *against* their MC's chosen approach.)
- **Audience** — who's this for? What change of mind/feeling am I aiming at?

If Step 0 is empty, the storyform you build will be technically valid but argumentatively hollow. Encoding will feel mechanical. Don't skip this step — even a rough one-sentence premise is better than none.

### Step 1 — Identify the four throughlines

For the story you're working on, name what each throughline IS:

- **OS** — what's the objective conflict everyone is involved in?
- **MC** — whose personal struggle do we live inside?
- **IC** — who keeps challenging the MC's worldview by their existence?
- **SS** — what's the MC↔IC relationship-as-its-own-story about?

If you can't name all four, that's diagnosis #1. The most commonly missing one is the SS.

### Step 2 — Assign each throughline to a Class

Pick one Class for OS; the other three are constrained by the dynamic-pair rule (OS-SS form one pair, MC-IC the other). If the assignment feels wrong, the throughline identification in Step 1 is probably wrong; iterate.

### Step 3 — Character Dynamics (4 binary choices for the MC)

| Dynamic | Options | What it sets |
|---|---|---|
| MC Resolve | Change / Steadfast | Does MC give up or hold their core driving Element by the end? |
| MC Growth | Start / Stop | Growing INTO something they lack or OUT of something they have? |
| MC Approach | Do-er / Be-er | Acts on the world or adapts themselves? |
| MC Mental Sex | Linear / Holistic | Cause-effect chains or relating multiple things at once? |

### Step 4 — Plot Dynamics (4 binary choices for the story)

| Dynamic | Options | What it sets |
|---|---|---|
| Story Driver | Action / Decision | Do actions force decisions or do decisions force actions, at act transitions? |
| Story Limit | Timelock / Optionlock | Story ends because time or options run out? |
| Story Outcome | Success / Failure | OS Goal achieved? |
| Story Judgment | Good / Bad | MC ends in satisfied internal state? |

Outcome × Judgment yields four endings: Triumph (S/G), Personal Triumph (F/G), Personal Tragedy (S/B), Tragedy (F/B).

### Step 5 — Pick the story points

Static plot story points: Story Goal (Type level), Requirements, Consequences, Forewarnings.

Driver/Passenger plot story points: Dividends, Costs, Prerequisites, Preconditions.

Thematic story points (per throughline): Concern (Type), Issue (Variation), Problem (Element), Solution, Focus, Direction.

### Step 6 — Identify the Crucial Element

The single Element (one of the 64 OS Character Elements) where MC and OS hinge. MC sits on it; IC sits on its dynamic-pair partner. If MC Resolve is Change, the Crucial Element is the *problem* the MC gives up. If Steadfast, it's the *solution* the MC holds.

If Step 3 (MC Resolve) and the Crucial Element disagree, the storyform is broken — fix one or the other.

### Step 7 — Encode, weave, deliver

Stages 2–4. Once the storyform is locked, you can re-encode freely without breaking the structure — that's what makes Dramatica useful for revision: the storyform is the load-bearing scaffolding; encoding and weaving are the surfaces.

### Validate before locking

Before declaring the storyform complete, run the validation checks in `references/00-storyform-validation.md`. Hard rules first (structural — invalid if violated), soft checks second (completeness — predict trouble even when valid).

## Workflows by phase

Different stages of writing use the skill differently. Use these as recipes; mix as needed.

### Greenfield outlining (new story, nothing drafted)

1. Step 0 — name the premise.
2. Steps 1–6 of the worksheet, in order. Keep each step's choices tentative until the next step confirms or contradicts.
3. Run hard-rule validation (`references/00-storyform-validation.md`).
4. Compare your storyform's pattern to the worked examples in `references/13-worked-storyforms.md` — if your pattern matches a known one, that's confidence; if it doesn't match anything, that's worth examining.
5. Build Signposts and Journeys for at least the OS and one of MC/IC/SS (`references/07-storyencoding.md`).
6. Start drafting. Let encoding inform the storyform; don't lock fully yet.

### Mid-draft, stuck

The draft is partway and you don't know what scene comes next, or the next scene-options all feel wrong.

1. Reconstruct the storyform from what's drafted so far. (You probably had it implicitly; making it explicit helps.)
2. Use `references/12-scene-level-bridge.md` — the "When the storyform is silent on a scene" section.
3. Check which throughline is most behind on scenes. Check which Signpost is overdue. Check which static plot story point hasn't been touched yet this Act.
4. If none of those generate a scene idea, the limiting factor isn't the storyform — switch to encoding/voice questions, not structural ones.

### Revision pass on a complete draft

Draft is complete and now you're auditing structure.

1. Run all four checks in the "Diagnosing a draft" section below.
2. For each finding, classify: structural (storyform-level — needs rewrites at scene level) or surface (encoding/prose — fixable in line edits).
3. If multiple hard-rule violations surface, see `references/11-anti-patterns.md` — odds are you're hitting one of the 14 named patterns.
4. Use `references/12-scene-level-bridge.md` to audit individual scenes that feel off, scene by scene.

### Series / multi-book planning

Dramatica is a single-story model. For series, two patterns:

- **Series-as-one-storyform** — the multi-book arc is itself one Grand Argument Story, with each book as a major Act or sub-Act. Build one storyform for the series.
- **Each book is its own storyform** — books share characters but each has its own complete storyform. Series-level coherence comes from continuity, not from a unifying storyform.

The book's section on Episodic Series and Multi-Story Ensembles (`references/08-storyweaving-reception.md`) covers both patterns.

### Character depth (one character, going deeper)

When a character feels flat or under-motivated:

1. Identify their throughline role: are they OS-only, MC, IC, or SS-axis?
2. For pure archetypes — what's their motivation pair? Are both halves visible in scenes?
3. For complex characters — which Motivation Elements (from the 64) do they actually carry across the draft? Are any pairs broken (carrying both halves of a dynamic pair)? See `references/02-characters.md`.
4. For an MC specifically — is the Crucial Element actually engaging in their scenes, or is it abstract?

### Diagnosing an existing draft (someone else's, or your own with distance)

When a draft feels off and you need to find why:

1. Try to identify all four throughlines from the draft itself. If you can't name one, that's diagnosis #1.
2. Try to assign each throughline to a Class. If two want the same Class, diagnosis #2 — structural collapse.
3. Test the eight dynamics. Look for self-contradiction across acts.
4. Check the Crucial Element — does the MC's arc actually pivot on giving up / holding to that Element?

These four checks surface most structural problems Dramatica is designed to surface. Issues that don't show up here are usually encoding or prose, not structure.

## Concept → file index

| You need | Load |
|---|---|
| **Fillable storyform template** to copy into your project | `references/00-storyform-worksheet.md` |
| **Validation checklist** — hard rules + soft checks for a built storyform | `references/00-storyform-validation.md` |
| Story Mind metaphor, Grand Argument vs Tale, Four Throughlines with Star Wars + *Mockingbird* worked | `references/01-foundations.md` |
| Archetypes, character dimensions, complex characters, motivation elements, Driver/Passenger split, Subjective Characters intro | `references/02-characters.md` |
| Why characters cling to broken solutions; Justification theory; problem-solving structure | `references/03-deep-theory.md` |
| Theme, Concerns/Issues/Problems hierarchy, throughline-to-Class assignments worked, storyform synthesis | `references/04-theme.md` |
| Plot story points, Acts, Sequences, Scenes, Events, Genre as Modes of Expression | `references/05-plot-genre.md` |
| Storyforming Stage 1 in full — Character Dynamics, Plot Dynamics, picking story points, the Crucial Element | `references/06-storyforming.md` |
| Storyencoding Stage 2 — encoding archetypes, complex characters, Mental Sex, theme, plot; **Signposts and Journeys** for all four throughlines | `references/07-storyencoding.md` |
| Storyweaving Stage 3 (spatial / temporal techniques, format-specific tips); Story Reception Stage 4 (audience, propaganda); worked Jurassic Park analysis | `references/08-storyweaving-reception.md` |
| Vocabulary glossary (alphabetical with cross-references); canonical lists of 16 Types, 64 Variations, 64 Elements | `references/09-reference.md` |
| **Decision heuristics** — how to actually choose for the hard decisions (Class for each throughline, Change vs Steadfast, Action vs Decision Driver, Linear vs Holistic, Goal Type-level, Optionlock vs Timelock, Outcome × Judgment) | `references/10-decision-heuristics.md` |
| **Anti-patterns** — 14 common mistakes when applying Dramatica, with fixes | `references/11-anti-patterns.md` |
| **Scene-level bridge** — translating storyform decisions into scene work; auditing existing scenes | `references/12-scene-level-bridge.md` |
| **Worked storyform cards** — Star Wars and *Mockingbird* as anchor examples (verified vs inferred values flagged) | `references/13-worked-storyforms.md` |

For any definitional question ("what's the difference between Issue and Problem?"), `09-reference.md` is the right file. For any decision difficulty ("how do I pick Class for OS?"), `10-decision-heuristics.md`. For any "why is this draft off?" question, `11-anti-patterns.md` first, then the diagnostic workflow above.

## Navigator

Conceptual questions ("explain the Story Mind premise", "why does MC Resolve matter?") still want the chapter prose. But for *structural* questions about specific terms — dynamic-pair partners, Quad membership, KTAD position, NCP-enum mapping — `tools/dramatica-nav/nav.py` answers without loading a 90 KB chapter:

```bash
python3 tools/dramatica-nav/nav.py by-id el.trust                  # term record + term_file pointer
python3 tools/dramatica-nav/nav.py by-id el.trust --full           # plus inlined prose section via extract.py
python3 tools/dramatica-nav/nav.py by-quad quad.logic-feeling-el   # the four Quad members
python3 tools/dramatica-nav/nav.py by-ncp 'Relationship Story'     # ontology entries with this NCP appreciation
```

When the navigator's `term_file` pointer indicates the answer needs prose, `tools/dramatica-nav/extract.py el.trust` returns just the heading-bound section, not the whole chapter — typically < 5 KB vs the 90–300 KB chapter source.

Cross-cutting load triggers (NO.1–NO.6) for the Narrative Ontology live in [`AGENTS.md § Narrative Ontology`](../../AGENTS.md). Non-narrative work MUST NOT load the ontology (NO.5 — token economy).

## Integration with other narrative skills

Dramatica is a structural model. It does not replace:

- **Project canon / state-tracking** — the storyform belongs in the project's authoritative state document (e.g. `CANON_STATE.md` or equivalent). It should be the single source of truth for structural decisions, with revisions tracked. Open structural questions belong in the project's open-questions list.
- **Prose-craft** — voice, line-level prose, dialogue rhythm, sentence music. Dramatica says nothing useful here.
- **Subject-matter research** — Dramatica's encoding stage assumes you know what your subject material is. World-building, period research, and domain expertise are separate workstreams.
- **Other story-structure frameworks** — if you're parallel-using Save the Cat, Hero's Journey, Story Grid, Truby, or McKee, run them in separate passes with separate vocabularies. Don't translate Dramatica terms onto them silently; the mappings are not clean.

When working bilingually (e.g. drafting in German, reasoning in English): Dramatica vocabulary is a closed technical system; translating its terms into another language tends to corrupt them. Keep Dramatica terms in English even when the conversation is in another language.

## What this skill is not for

- **Tales, vignettes, slices of life.** Dramatica describes complete Grand Argument Stories. Many great stories are not Grand Argument Stories. Don't force the model on them.
- **Roleplay or improvisational narrative.** Dramatica describes complete authored stories — it has nothing useful to say about emergent or co-created narrative.
- **Reproducing the source book.** This is a working interface for personal narrative-craft use. The reference chunks are working material, not a redistributable edition.

## Source

Phillips, Melanie Anne & Huntley, Chris. *Dramatica: A New Theory of Story.* 4th ed. Burbank: Screenplay Systems Incorporated, 2001. © 1993–2001 Screenplay Systems Inc. All rights reserved by the original publisher. The reference chunks in this skill are verbatim extracts from the PDF edition for personal narrative-craft use.
