# Validation Rules

The JSON schema (`upstream/schema/ncp-schema.json`, validated by `scripts/validate.js` once that script is added) catches **structural** violations: missing required fields, unknown enum values, wrong types. It does **not** catch semantic violations. This file lists the semantic rules that an NCP-conformant document MUST satisfy beyond schema-level validation.

Run schema validation first (it's fast and free), then walk this checklist before declaring a document complete.

> **Status:** This is a working draft. Some rules below are conjecture from reading the SPECIFICATION.md — they need confirmation against actual canonical examples (`upstream/examples/anora.json`, `upstream/examples/the-shawshank-redemption.json`) before being treated as enforced.

---

## 1. Reference integrity

These are checks for cross-references inside the document.

### 1.1 Perspective links resolve

Every `perspective_id` referenced from any of the following must exist in `subtext.perspectives[]`:

- `subtext.players[].perspectives[].perspective_id`
- `subtext.storypoints[].perspectives[].perspective_id`
- `subtext.storybeats[].perspectives[].perspective_id`

A dangling `perspective_id` is structurally broken — Players, Storypoints, and Storybeats define *which authorial lens* shapes their meaning; without a resolvable link, the lens is null.

### 1.2 Storybeat references in moments resolve

Every `storytelling.moments[].storybeats[].storybeat_id` must match an `id` in `subtext.storybeats[]`. Moments that reference non-existent beats orphan the storytelling layer from the structural layer.

### 1.3 Throughline consistency between appreciation and field

When a Storypoint or Storybeat has both an `appreciation` (e.g., `"Main Character Issue"`) and an explicit `throughline` field (e.g., `"Main Character"`), the two MUST agree. Mismatch ("Main Character Issue" + `throughline: "Objective Story"`) indicates either an authoring error or a structural misclassification.

For the four-throughline-prefixed appreciations, the `throughline` field is derivable. Tooling SHOULD warn if a derived throughline conflicts with the explicit one.

---

## 2. Dynamic-vector pairing

The schema does not enforce which `vector` values are valid for a given `dynamic`. The semantic constraint is:

| `dynamic`                     | Valid `vector` values  |
| ----------------------------- | ---------------------- |
| `main_character_resolve`      | `change`, `steadfast`  |
| `influence_character_resolve` | `change`, `steadfast`  |
| `main_character_growth`       | `stop`, `start`        |
| `main_character_approach`     | `do_er`, `be_er`       |
| `problem_solving_style`       | `linear`, `holistic`   |
| `story_limit`                 | `optionlock`, `timelock` |
| `story_driver`                | `action`, `decision`   |
| `story_outcome`               | `success`, `failure`   |
| `story_judgment`              | `good`, `bad`          |

Any other pairing is a semantic violation. Tooling SHOULD flag this.

---

## 3. Storybeat sequence rules

### 3.1 Scope determines maximum sequence

Per the canonical Dramatica structure (also visible in the appreciation enum):

- `scope: "signpost"` → `sequence` MUST be in `[1, 4]`
- `scope: "progression"` → `sequence` MUST be in `[1, 16]`
- `scope: "event"` → `sequence` MUST be in `[1, 64]`

The schema only enforces `minimum: 1`. The upper bounds are semantic.

### 3.2 Sequence uniqueness within (throughline, scope)

Within a single throughline + scope, every `sequence` value MUST be unique. Two Storybeats with `throughline: "Main Character"`, `scope: "signpost"`, `sequence: 2` are a conflict.

Across throughlines, the same `sequence` is normal and expected (Main Character Signpost 2 and Objective Story Signpost 2 coexist).

### 3.3 Storybeat-appreciation consistency

When a Storybeat has both structural fields (`throughline`, `scope`, `sequence`) AND an `appreciation` (e.g., `"Main Character Signpost 4"`), they MUST agree. The appreciation is the human-readable form of the structural triple.

---

## 4. Storypoint canonical fit

### 4.1 Throughline-prefixed appreciation matches throughline field

Same rule as 1.3 but for Storypoints. If the appreciation starts with one of the four throughlines, the explicit `throughline` field MUST agree.

### 4.2 Story-level appreciations have no `throughline`

Story-level appreciations (`Story Goal`, `Story Outcome`, `Story Limit`, etc.) are not throughline-specific. The `throughline` field SHOULD be omitted or null on these Storypoints.

### 4.3 Holistic-mode aliases

Character-framing aliases (`Character Intentions`, `Character Repercussions`, etc.) are valid only when `subtext.dynamics[dynamic="problem_solving_style"].vector` is `holistic`. Using these aliases in a `linear` storyform is structurally incoherent — the framing presupposes holistic problem-solving.

---

## 5. Required-field non-emptiness

The JSON schema treats `""` (empty string) as a valid string. Semantically, several required fields are non-empty:

- `story.title` MUST NOT be empty
- `subtext.perspectives[].summary` and `.storytelling` MUST NOT be empty
- `subtext.players[].name`, `.bio`, `.summary`, `.visual`, `.audio` MUST NOT be empty (placeholders like "TBD" are acceptable during drafting but not in final documents)
- `subtext.storybeats[].summary` and `.storytelling` MUST NOT be empty
- `storytelling.moments[].synopsis`, `.setting`, `.timing`, `.imperatives` MUST NOT be empty

A "schema-passing" document with empty required strings is not actually usable.

---

## 6. Status-coherence rules

### 6.1 Status reflects actual completion

- `status: "candidate"` — exploratory; subtext may be sparse, ideation may dominate
- `status: "draft"` — a Storyform has been picked; `subtext` is being populated
- `status: "complete"` — the Storyform is locked; `storytelling` should be complete or near-complete

A narrative marked `complete` with an empty `storytelling.moments[]` is incoherent.

### 6.2 Per-phase semantic gates (proposed)

Per SPEC.md §7.6, status transitions correspond to phase completion. A proposed gate set:

| From → To              | Required for transition                                                |
| ---------------------- | ---------------------------------------------------------------------- |
| `candidate` → `draft`  | At least 4 perspectives (one per throughline) and at least 1 Storypoint per throughline |
| `draft` → `complete`   | All 9 dynamics present, signpost-scope storybeats for all 4 throughlines (16 beats minimum), full `players[]` array |

These are derived from the SPEC, not from the upstream NCP schema. They are project-policy rather than spec-policy. Tooling SHOULD warn but MAY not block on these.

---

## 7. What this file does NOT cover

- **Quad (KTAD) integrity.** The Knowledge / Thought / Ability / Desire matrix Dramatica uses to constrain Element selection is *not* encoded in NCP. KTAD validation belongs in `dramatica-vocabulary` or `dramatica-theory`. See `references/related-skills.md`.
- **Dynamic Pair coherence.** The 75 Dynamic Pairs that constrain consistent Storyform selection live in `dramatica-vocabulary`. The NCP schema cannot detect, e.g., a Storyform where the chosen Problem Element doesn't pair with the chosen Solution Element.
- **Justification-ordering correctness.** Per SPECIFICATION.md §450 ("Dynamics × Storypoints = Storybeats"), the *order* of Storybeats encodes meaning. Whether a given ordering is structurally justified is a deep theory question and belongs in `dramatica-theory`.
- **Prose quality.** NCP is a structural format. Prose-level checks (voice, pacing, line-edit) are the responsibility of revision skills, not of NCP validation.

---

## 8. Checklist — quick scan before declaring "complete"

```text
[ ] Schema validation passes (ajv or upstream validate-file.js)
[ ] All perspective_id references resolve (rule 1.1)
[ ] All storybeat_id references in moments resolve (rule 1.2)
[ ] Throughline ↔ appreciation agreement on Storypoints/Storybeats (rules 1.3, 4.1)
[ ] Dynamic-vector pairs are valid (rule 2)
[ ] Storybeat sequence values within scope-appropriate bounds (rule 3.1)
[ ] No (throughline, scope, sequence) collisions (rule 3.2)
[ ] Story-level appreciations have no throughline field (rule 4.2)
[ ] Holistic aliases only used when problem_solving_style = holistic (rule 4.3)
[ ] No required-field empty strings (rule 5)
[ ] status reflects actual completion state (rule 6.1)
[ ] Hand off to dramatica-vocabulary/dramatica-theory for Quad/Pair/Justification audits
```
