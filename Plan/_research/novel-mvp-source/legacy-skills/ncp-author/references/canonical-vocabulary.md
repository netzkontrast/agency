# Canonical Vocabulary

This file is the source of truth for the **canonical_appreciation** (463 values) and **canonical_narrative_function** (144 values) enums in `schema/ncp-schema.json`, plus the smaller `dynamic`, `vector`, `throughline`, `overview_label`, `audience_experiential_pov`, and `narrative.status` enums.

**Use this file when:** filling in any `appreciation`, `narrative_function`, `dynamic`, `vector`, `throughline`, `label`, or `audience_experiential_pov` field. Schema validation will reject unknown values — there are no "close enough" matches. If you need a value that isn't in the canonical list, use the parallel `custom_*` field plus its `*_namespace` companion.

For Dramatica-theory reasoning *about* these terms (which Element pairs with which, what a Quad activation looks like, how Signposts sequence within a throughline), defer to the **`dramatica-vocabulary`** skill. This file is a compliance reference, not a theory reference.

---

## 1. Appreciations (463 values total)

Appreciations fall into a regular structure: each of the four throughlines has ~108 values formed by `<Throughline> <Slot>`. Plus 24 Story-level appreciations, 8 Character-framing aliases, and 18 outliers.

### 1.1 The four throughlines

The four canonical throughlines are exactly:

```
Main Character | Influence Character | Objective Story | Relationship Story
```

These also are the four valid values of the optional `throughline` field on Storypoints and Storybeats.

### 1.2 Per-throughline slot suffixes (~108 each)

For every throughline `T ∈ {Main Character, Influence Character, Objective Story, Relationship Story}`, the canonical appreciation form is `T <Suffix>`.

**Conceptual slots (24 suffixes — appear for all four throughlines):**

```
Adjustment        Issue
Approach          Pivotal Element
Baseline          Problem
Benchmark         Problem-solving Style
Concern           Resistance
Condition         Resolution
Critical Flaw     Resolve
Domain            Response
Evolution         Solution
Flow              Symptom
Growth            Throughline
Introduction      Unique Ability
```

> Note: Objective Story has 99 appreciations (not 100) because it lacks one MC-specific conceptual slot. The OS variants follow the same pattern with two omissions where conceptually inapplicable.

**Sequenced slots (84 suffixes — appear for all four throughlines):**

- `Signpost 1` through `Signpost 4` (4 values)
- `Progression 1` through `Progression 16` (16 values)
- `Event 1` through `Event 64` (64 values)

**Examples of full appreciation strings:**

```
Main Character Issue
Main Character Signpost 4
Influence Character Event 12
Objective Story Progression 7
Relationship Story Domain
```

**Construction rule:** when filling a Storypoint or Storybeat appreciation, pick the throughline, then pick the slot. The full string MUST exactly match `<Throughline> <Slot>` with one space.

### 1.3 Story-level appreciations (24 standalone)

These do not take a throughline prefix:

```
Story Consequence       Story Internalizations
Story Constraints       Story Intention
Story Costs             Story Judgment
Story Dilemma           Story Limit
Story Dividends         Story Outcome
Story Driver            Story Overwhelm
Story Ending            Story Preconditions
Story Ennui             Story Prerequisites
Story Excitement        Story Pressure
Story Forewarnings      Story Reach
Story Goal              Story Requirements
Story Habituations      Story Socializations
```

Note that several of these are **legacy alternate names** for canonical Dramatica terms. The mapping (from `docs/terminology/10.dramatica-translation.md` in the upstream repo):

| Story-level appreciation | Canonical Dramatica term |
| ------------------------ | ------------------------ |
| Story Intention          | Story Goal               |
| Story Overwhelm          | Story Consequence        |
| Story Excitement         | Story Dividends          |
| Story Pressure           | Story Costs              |
| Story Ennui              | Story Forewarnings       |
| Story Habituations       | Story Requirements       |
| Story Internalizations   | Story Prerequisites      |
| Story Socializations     | Story Preconditions      |

Both alias and canonical forms are valid. Pick one and stay consistent within a document.

### 1.4 Character-framing aliases (8 holistic-mode values)

For holistic-framing storyforms, NCP provides Character-centric appreciations as canonical-valid alternatives:

```
Character Intentions    → Story Goal           (alias)
Character Repercussions → Story Consequence    (alias)
Character Adaptations   → Story Requirements   (alias)
Character Affectations  → Story Prerequisites  (alias)
Character Engagements   → Story Preconditions  (alias)
Character Perks         → Story Dividends      (alias)
Character Pressures     → Story Costs          (alias)
Character Forebodings   → Story Forewarnings   (alias)
```

Use these when the storyform's `problem_solving_style` dynamic is `holistic` and the author prefers character-framed thematic vocabulary.

### 1.5 Other appreciations (18 outliers)

```
Argument Approach              Initial Story Driver
Argument Objective             Midpoint Story Driver
Argument Resolution            Nature
Character Evolution            Objective Premise Method
Character Orientation          Reach
Concluding Story Driver        Second Story Driver
Emotional Outcome              Subjective Premise Balance Element
Essence                        Subjective Premise Element
Fourth Story Driver            Tendency
```

These are specialized appreciations for argumentation structure, premise crafting, and Driver sequencing. Use sparingly and only when the structural slot genuinely matches.

---

## 2. Narrative Functions (144 canonical values)

Narrative Functions are the canonical Dramatica Elements — the *content* that fills an appreciation slot. Use these on:

- `subtext.players[].motivations[].narrative_function` (required)
- `subtext.storypoints[].narrative_function` (optional but recommended)
- `subtext.storybeats[].narrative_function` (optional)

The full alphabetical list:

```
Ability              Cause                   Faith
Acceptance           Certainty               Falsehood
Accurate             Change                  Fantasy
Actuality            Chaos                   Fate
Analysis             Choice                  Feeling
Appraisal            Circumstances           Future
Approach             Closure                 Help
Attempt              Commitment              Hinder
Attitude             Conceiving              Hope
Attract              Conceptualizing         Hunch
Avoid                Conditioning            Inaction
Aware                Confidence              Induction
Becoming             Conscience              Inequity
Being                Conscious               Inertia
                     Consider                Instinct
                     Control                 Interdiction
                     Deduction               Interpretation
                     Deficiency              Investigation
                     Delay                   Knowledge
                     Denial                  Learning
                     Desire                  Logic
                     Destiny                 Memory
                     Determination           Mind
                     Disbelief               Need
                     Doing                   Non-acceptance
                     Doubt                   Non-accurate
                     Dream                   Obligation
                     Effect                  Obtaining
                     Ending                  Openness
                     Enlightenment           Oppose
                     Equity                  Order
                     Evaluation              Past
                     Evidence                Perception
                     Expectation             Permission
                     Expediency              Physics
                     Experience              Possibility
                     Fact                    Potentiality

Preconception        Reduction               Subconscious
Preconditions        Repel                   Support
Preconscious         Responsibility          Suspicion
Prediction           Result                  Temptation
Prerequisites        Security                Test
Present              Self Interest           Theory
Proaction            Self-aware              Thought
Probability          Selflessness            Threat
Process              Sense of Self           Trust
Production           Senses                  Truth
Progress             Situation               Uncontrolled
Projection           Skill                   Understanding
Protection           Speculation             Unending
Proven               State of Being          Universe
Psychology           Strategy                Unproven
Pursuit                                      Value
Rationalization                              Wisdom
Re-evaluation                                Work
Reaction                                     Worry
Reappraisal                                  Worth
Reconsider
```

**Important compliance notes:**

- **Hyphenation matters.** `Non-acceptance`, `Non-accurate`, `Re-evaluation`, `Self-aware`, `Problem-solving Style` are hyphenated exactly as shown.
- **Capitalization matters.** Always Title Case. `self interest` and `Self interest` will fail validation; only `Self Interest` (with capital I) is canonical.
- **Multi-word values keep spaces.** `State of Being`, `Sense of Self`.

If a Dramatica concept seems missing, check `dramatica-vocabulary` skill for nuance — sometimes the concept maps to a differently-named canonical value (e.g., the Dramatica Element "Effect" is in this list as `Effect`; the Element "Worry" appears as `Worry`).

---

## 3. Dynamics (9 values, snake_case)

Used in `subtext.dynamics[].dynamic`:

```
main_character_resolve
influence_character_resolve
main_character_growth
main_character_approach
problem_solving_style
story_limit
story_driver
story_outcome
story_judgment
```

**These are snake_case** — distinct from the Title Case used in appreciations and narrative functions.

## 4. Vectors (16 values, snake_case)

Used in `subtext.dynamics[].vector`:

```
change | steadfast       (pairs with *_resolve)
stop | start             (pairs with *_growth)
do_er | be_er            (pairs with main_character_approach)
linear | holistic        (pairs with problem_solving_style)
optionlock | timelock    (pairs with story_limit)
action | decision        (pairs with story_driver)
success | failure        (pairs with story_outcome)
good | bad               (pairs with story_judgment)
```

The pairings above are **not enforced by the JSON schema** but are structurally meaningful — `validation-rules.md` covers the semantic check.

Note: `do_er` and `be_er` keep the underscore — this is the snake_case form of "do-er" / "be-er".

## 5. Throughline values (4 values, Title Case)

Used in the optional `throughline` field on `subtext.storypoints[]` and `subtext.storybeats[]`:

```
Objective Story | Main Character | Influence Character | Relationship Story
```

Schema requires exact-match Title Case. Abbreviations (MC, IC, OS, RS) are not valid in this field — use them in your prose, not in the JSON.

## 6. Overview labels (3 values, Title Case)

Used in `storytelling.overviews[].label`:

```
Logline | Genre | Blended Throughlines
```

## 7. Audience-experiential POV (6 values, snake_case)

Used in `storytelling.moments[].audience_experiential_pov`:

```
first_person_central
first_person_peripheral
second_person
third_person_limited
third_person_objective
third_person_omniscient
```

## 8. Narrative status (3 values, lowercase)

Used in `narratives[].status`:

```
candidate | draft | complete
```

Use `candidate` while exploring storyform options, `draft` when one structural form has been selected and is being filled in, and `complete` when the storyform is locked and storytelling is being authored against it.

## 9. Author structural POV (4 values, lowercase)

Used in `subtext.perspectives[].author_structural_pov`:

```
i | you | we | they
```

Single lowercase string. This is the *author's* structural stance toward the conflict, not the narrator's POV in prose.
