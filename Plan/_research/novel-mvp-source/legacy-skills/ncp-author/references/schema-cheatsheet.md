# NCP Schema Cheatsheet

Quick-reference structural map of NCP v1.3.0 (`schema/ncp-schema.json`, draft-07). Load this whenever authoring or editing an NCP document. For canonical enum lists (Appreciations, Narrative Functions, Dynamics, Vectors), see `canonical-vocabulary.md`. For semantic rules beyond JSON-Schema, see `validation-rules.md`.

## Top-level shape

```json
{
  "schema_version": "1.3.0",
  "story": { ... }
}
```

`schema_version` and `story` are both **required** at the document root.

## Story object

Required: `id`, `title`.
Optional: `genre`, `logline`, `created_at` (ISO-8601), `ideation`, `narratives`.

```json
"story": {
  "id": "story_<uuid-or-stable>",
  "title": "...",
  "genre": "...",
  "logline": "...",
  "created_at": "2026-01-01T00:00:00Z",
  "ideation": { ... },
  "narratives": [ ... ]
}
```

`id` follows the `stable_id` shape — string, no whitespace constraints beyond JSON. The `story_*`/`narrative_*` prefixes shown in examples are convention, not required by the schema.

## Ideation (optional, beginner-friendly)

```json
"ideation": {
  "character": [<ideation_node>],
  "theme":     [<ideation_node>],
  "plot":      [<ideation_node>],
  "genre":     [<ideation_node>]
}
```

`ideation_node` requires `id` + `summary`. Optional: `title`, `notes`, `tags[]`. Use this layer **before** committing to a Storyform. Once a `narratives[].subtext` exists, ideation nodes become historical/seed material — they are not deleted but they no longer drive anything downstream.

## Narratives

```json
"narratives": [
  {
    "id": "narrative_<id>",
    "title": "...",
    "status": "candidate" | "draft" | "complete",
    "subtext": { ... },
    "storytelling": { ... }
  }
]
```

Multiple narratives are allowed but rare (see SPECIFICATION §96–98 for the *Empire* / *Barbie* dual-Storyform examples). Default to one. `status` is optional but recommended for the autonomous-handoff workflow.

## Subtext — the structural layer

Five arrays, all optional individually but each governed by strict required-field rules when present:

```json
"subtext": {
  "perspectives": [],
  "players":      [],
  "dynamics":     [],
  "storypoints":  [],
  "storybeats":   []
}
```

### `perspectives[]`

Required: `id`, `author_structural_pov`, `summary`, `storytelling`.
`author_structural_pov` enum: `"i" | "you" | "we" | "they"` — **lowercase**, single-letter or short pronoun. This is *authorial* POV (where the author stands relative to the conflict), not the audience-facing narrative POV.

Perspectives are pure POV records. Do not put character identity, role, or conflict metadata here — those belong on Players, Storypoints, and Storybeats.

### `players[]`

Required (heavy): `id`, `name`, `role`, `visual`, `audio`, `summary`, `bio`, `storytelling`, `motivations[]`, `perspectives[]`.

`role` is a free-form string in the schema, but conventional values are the four throughline names plus archetype labels (Protagonist, Antagonist, Guardian, Contagonist, Sidekick, Skeptic, Reason, Emotion). When an archetype is used, set `role` to the archetype name and link to the appropriate perspective via `perspectives[].perspective_id`.

`motivations[]` items: each requires `narrative_function`, `illustration`, `storytelling`. The `narrative_function` value must come from the canonical enum (see `canonical-vocabulary.md`) or use `custom_narrative_function` + `custom_narrative_function_namespace`.

`perspectives[]` on a Player is a list of `{ "perspective_id": "..." }` linking to perspectives in `subtext.perspectives[]`.

### `dynamics[]`

Required: `id`, `dynamic`, `vector`, `summary`, `storytelling`.

`dynamic` enum (9 values, snake_case):
- `main_character_resolve`
- `influence_character_resolve`
- `main_character_growth`
- `main_character_approach`
- `problem_solving_style`
- `story_limit`
- `story_driver`
- `story_outcome`
- `story_judgment`

`vector` enum (16 values, snake_case): `change | steadfast | stop | start | do_er | be_er | linear | holistic | optionlock | timelock | action | decision | success | failure | good | bad`.

**Dynamic-vector pairing is not enforced at schema level** but is structurally meaningful (see `validation-rules.md`):
- `main_character_resolve` → `change | steadfast`
- `*_growth` → `stop | start`
- `main_character_approach` → `do_er | be_er`
- `problem_solving_style` → `linear | holistic`
- `story_limit` → `optionlock | timelock`
- `story_driver` → `action | decision`
- `story_outcome` → `success | failure`
- `story_judgment` → `good | bad`

### `storypoints[]`

Required: `id`, `appreciation`, `illustration`, `summary`, `storytelling`, `perspectives[]`.

`appreciation` must come from the **canonical_appreciation** enum (463 values) OR use `custom_appreciation` + `custom_appreciation_namespace`. See `canonical-vocabulary.md`.

`narrative_function` is **optional** on a Storypoint but RECOMMENDED — it ties the Storypoint to its canonical Dramatica Element. When present, must be from the `canonical_narrative_function` enum (144 values).

`throughline` is optional and enum-restricted: `"Objective Story" | "Main Character" | "Influence Character" | "Relationship Story"`. The throughline is usually inferable from the appreciation prefix (e.g., "Main Character Issue" → Main Character), but storing it explicitly aids consumers that don't parse the appreciation string.

### `storybeats[]`

Required: `id`, `scope`, `sequence`, `summary`, `storytelling`, `perspectives[]`.

`scope` enum: `"signpost" | "progression" | "event"`.
`sequence` integer, minimum 1.
`throughline` (optional but strongly recommended) — same enum as Storypoint.
`appreciation` (optional, derived) — when present, restate the structural slot like `"Main Character Signpost 4"` or `"Objective Story Event 12"`.
`narrative_function` (optional) — canonical enum.

**Important:** `signpost` is *not* a separate field on Storybeats. The structural slot is `throughline + scope + sequence`. The repo's HISTORY.md explicitly removes the legacy `signpost` field — derive it from structure instead.

## Storytelling — the audience-facing layer

```json
"storytelling": {
  "overviews": [],
  "moments": []
}
```

### `overviews[]`

Required: `id`, `label`, `summary`, `storytelling`.
`label` enum (3 values): `"Logline" | "Genre" | "Blended Throughlines"`.

The `Blended Throughlines` overview is where MC/IC/OS/RS converge into a single audience-facing summary — a useful single-source description for marketing, dust-jackets, pitches.

### `moments[]`

Required (heavy): `summary`, `synopsis`, `setting`, `timing`, `imperatives`, `storybeats[]`.
Optional but conventional: `id`, `act` (integer), `order` (integer), `maximum_steps` (integer), `audience_experiential_pov`, `fabric[]`.

`audience_experiential_pov` enum: `first_person_central | first_person_peripheral | second_person | third_person_limited | third_person_objective | third_person_omniscient`.

`storybeats[]` on a Moment is a list of `{ "sequence": <int>, "storybeat_id": "<beat-id>" }`. The `sequence` here is the order **within the Moment**, distinct from the Storybeat's own `sequence` field (which is its order within the throughline). A single Storybeat MAY appear in multiple Moments if needed.

`fabric[]` items take the shape `{ "type": "space" | "time", "limit": <int> }` and encode Story Limit (Optionlock / Timelock) as a presentation constraint.

## Mapping NCP entities to where novel-craft artifacts go

This is the practical translation table — what a novelist's instinctive vocabulary maps to in NCP:

| Novel-craft term         | NCP location                                       |
| ------------------------ | -------------------------------------------------- |
| Premise / logline         | `story.logline` AND `storytelling.overviews[label="Logline"]` |
| Character bio             | `subtext.players[].bio`                             |
| Character archetype       | `subtext.players[].role` (Protagonist/Antagonist/etc.) |
| Inner conflict / arc      | `subtext.dynamics[main_character_resolve]` + MC Storypoints |
| Theme statement           | `subtext.dynamics[story_outcome]` + `story_judgment` + Blended Throughlines overview |
| Plot beat (act level)     | `subtext.storybeats[scope="signpost"]`              |
| Plot beat (mid level)     | `subtext.storybeats[scope="progression"]`           |
| Plot beat (scene level)   | `subtext.storybeats[scope="event"]`                 |
| Chapter / scene heading   | `storytelling.moments[]`                            |
| Worldbuilding / setting   | `storytelling.moments[].setting` per moment + custom overviews via `custom_label` |
| Prose passage             | `storytelling.moments[].synopsis` (compressed) — actual prose lives outside NCP |

Note the last row: **NCP does not store prose**. It holds *intent for* prose. Generated chapters/scenes belong in separate Markdown or document files, with cross-references to `moment.id` for traceability.

## Common pitfalls

1. **Confusing `appreciation` with `narrative_function`.** Appreciation = structural slot ("Main Character Issue"). Narrative Function = the canonical Dramatica Element ("Rationalization") that fills that slot. A Storypoint's appreciation says *where in the structure*; its narrative_function says *what specifically*.

2. **Dropping required fields under "minimal viable" pressure.** Players require ten fields including `visual`, `audio`, `bio` — placeholders are acceptable during drafting but must not stay empty. The schema will pass, but downstream consumers depend on them.

3. **Treating `throughline` as enum-free.** Only four values are valid for the typed `throughline` field on Storybeat/Storypoint. Any other value belongs in custom fields.

4. **Putting prose in `storytelling`.** The `storytelling` field on every entity is a *short descriptive summary of the storytelling intent*, not the actual prose. One paragraph at most.

5. **Custom values without namespace.** When using `custom_appreciation`, `custom_dynamic`, `custom_narrative_function`, etc., always pair with the matching `*_namespace` object. The namespace identifies the external framework being mapped (e.g., `"hero_journey"`, `"save_the_cat"`).

6. **Forgetting `perspectives[]` on Storypoints and Storybeats.** Both require a non-empty `perspectives[]` array. A Storypoint or Storybeat without a Perspective link is structurally adrift.

7. **`schema_version` mismatch.** Always emit `"schema_version": "1.3.0"` for current spec. Older documents may use earlier versions; the validator is strict.
