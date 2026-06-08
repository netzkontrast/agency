---
type: theory-chunk
chunk_id: dt-00-storyform-worksheet
summary: Decision template for building a Grand Argument Story storyform step by step, tracking every slot from throughlines to story points.
covers_ontology_ids:
  - concept.storyform
  - throughline.*
  - concept.crucial-element
serves_scenarios:
  - novel.storyform-slot-fill
  - novel.dual-storyform
size_kb: 7
depends_on_chunks:
  - dt-01-foundations
---

# Storyform Worksheet

> Template to be filled out for one Grand Argument Story. Copy this file into your novel project (e.g. `CANON_STATE/storyform.md`) and edit in place. Every field that's left empty is a decision deferred — that's fine, but track which ones. The order below is the recommended decision order; revisit earlier decisions when later ones expose contradictions.

---

## Step 0 — Author's Intent / Premise

Before any structure: what does this story *say*? Dramatica is built to construct an *argument*; you can only build the argument if you know what's being argued.

- **Premise (1 sentence):** _________________________________________
- **Thematic argument:** I want to argue that _______________ leads to _______________ (and the opposite leads to ____________).
- **Take:** Do I write *for* or *against* the premise? (Tragedy/Failure stories often argue *against* the MC's chosen approach.)
- **Audience:** Who's this for? What change of mind/feeling am I aiming at?

---

## Step 1 — Identify the Four Throughlines

Each throughline is a perspective on the single story problem. Name what each one IS in this story.

| Throughline | POV | Question | Your answer |
|---|---|---|---|
| **Overall Story (OS)** | "they" | What's the objective conflict everyone is involved in? | |
| **Main Character (MC)** | "I" | Whose personal struggle do we live inside? | |
| **Impact Character (IC)** | "you" | Who keeps challenging the MC's worldview by their existence? | |
| **Subjective Story (SS)** | "we" | What's the MC↔IC relationship, treated as its own story? | |

If you can't name one — most often the SS — that's diagnosis #1. Don't fudge it; come back when you can.

---

## Step 2 — Assign Each Throughline to a Class

Constraint: OS+SS form one dynamic pair, MC+IC form the other. Pairs are **Universe ↔ Mind** (state pair) and **Physics ↔ Psychology** (process pair). Pick one Class for OS; the other three are constrained.

Classes: **Universe** (external state/situation), **Physics** (external process/activity), **Mind** (internal state/fixed attitude), **Psychology** (internal process/manipulation).

| Throughline | Class | Rationale |
|---|---|---|
| OS | | |
| SS | | (must be OS's Class's pair partner) |
| MC | | (one of the other two) |
| IC | | (must be MC's Class's pair partner) |

If the assignment feels wrong, your throughline identifications in Step 1 are probably wrong. Iterate before continuing.

---

## Step 3 — Character Dynamics (4 binary choices)

| Dynamic | Options | Choice | Rationale |
|---|---|---|---|
| **MC Resolve** | Change / Steadfast | | Does MC give up their core driving Element by the end, or hold it? |
| **MC Growth** | Start / Stop | | Growing INTO something they lack, or OUT of something they have? |
| **MC Approach** | Do-er / Be-er | | Solves problems by acting on the world, or by adapting themselves? |
| **MC Mental Sex** | Linear / Holistic | | Cause-and-effect chains, or relating multiple things at once? (Original term: "Male/Female problem-solving" — dated label, the cognitive distinction is what matters.) |

---

## Step 4 — Plot Dynamics (4 binary choices)

| Dynamic | Options | Choice | Rationale |
|---|---|---|---|
| **Story Driver** | Action / Decision | | Do *actions* force *decisions*, or do *decisions* force *actions*? Pick whichever drives the act-to-act transitions. |
| **Story Limit** | Timelock / Optionlock | | Does the story end because time runs out, or because options run out? |
| **Story Outcome** | Success / Failure | | Does the OS Goal get achieved? |
| **Story Judgment** | Good / Bad | | Does the MC end in a satisfied internal state, or unresolved? |

**Ending type** (= Outcome × Judgment): _______________
- Success/Good = Triumph
- Failure/Good = Personal Triumph
- Success/Bad = Personal Tragedy
- Failure/Bad = Tragedy

---

## Step 5 — Plot Story Points

### Static plot story points (must be set)

| Story Point | Description | Your value |
|---|---|---|
| **Story Goal** | The OS objective (Type level — see decision heuristics) | |
| **Requirements** | What must be done to reach the Goal | |
| **Consequences** | What happens if Goal isn't reached | |
| **Forewarnings** | Early signs that Consequences are arriving | |

### Driver/Passenger plot story points (often set)

| Story Point | Description | Your value |
|---|---|---|
| **Dividends** | Partial rewards along the way | |
| **Costs** | Partial losses along the way | |
| **Prerequisites** | Necessary preconditions for Requirements | |
| **Preconditions** | Author-imposed extra conditions on Requirements | |

### Thematic story points (per throughline)

| Throughline | Concern (Type) | Issue (Variation) | Problem (Element) | Solution | Focus | Direction |
|---|---|---|---|---|---|---|
| OS | | | | | | |
| MC | | | | | | |
| IC | | | | | | |
| SS | | | | | | |

---

## Step 6 — The Crucial Element

The Crucial Element is one of the 64 OS Character Elements. The MC sits on it; the IC sits on its dynamic-pair partner. If MC Resolve is **Change**, the Crucial Element is the *problem* and MC must give it up. If **Steadfast**, the Crucial Element is the *solution* and MC must hold to it.

- **Crucial Element:** _______________
- **IC's opposing Element (dynamic-pair partner):** _______________
- **Consistency check:** Does the MC Resolve from Step 3 match this Element's role here?
  - [ ] Yes — Change MC + Element-as-problem, OR Steadfast MC + Element-as-solution
  - [ ] No — revisit Step 3 or this Element

Worked example from book: *To Kill A Mockingbird* — Crucial Element is **INEQUITY**. Scout (MC) is Change, so Inequity is the problem she gives up (her prejudice against Boo Radley).

---

## Step 7 — Signposts and Journeys (Storyencoding bridge)

Each throughline progresses through 4 Signposts (one per Act, at the throughline's Type level) connected by 3 Journeys (transitions). These come from the Type-Quad of the throughline's Class. Order matters and is constrained by other choices — but the four Signposts must be the four Types of that Class.

| | Signpost 1 | Journey 1→2 | Signpost 2 | Journey 2→3 | Signpost 3 | Journey 3→4 | Signpost 4 |
|---|---|---|---|---|---|---|---|
| **OS** | | | | | | | |
| **MC** | | | | | | | |
| **IC** | | | | | | | |
| **SS** | | | | | | | |

For full treatment of Signpost ordering and four-act vs three-act mapping: `references/07-storyencoding.md`.

---

## Step 8 — Optional: Genre Mode

Dramatica genre = Mode of Expression, not marketing label. Pick one if useful for this storyform; otherwise leave blank. See `references/05-plot-genre.md`.

- **Genre mode:** _______________

---

## Validation pass

Before declaring this storyform locked, run through `references/00-storyform-validation.md`. The hard checks especially: dynamic-pair complementarity, no character carrying both elements of a dynamic pair, Goal at Type level, Crucial Element at Element level, MC Resolve ↔ Crucial Element coherence.

## Living document note

Once locked, the storyform is the load-bearing scaffolding for revision. Encoding (subject matter, prose, dialogue) and weaving (scene order, POV, flashbacks) can change freely without rebuilding the structure. If the *storyform itself* changes mid-draft, you have a structural revision, not a prose revision — call it that explicitly so you don't pretend the rest of the draft still fits.
