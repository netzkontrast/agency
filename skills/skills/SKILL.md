---
name: skills
description: "Use when discovering which walkable skills exist, reading one skill's phases at a chosen depth, or validating a skill's phase-graph shape — before walking, emitting, or authoring a skill."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# skills capability

Skills makes the skill surface itself a capability: one home to find, render, and lint the phase-graph skills each capability ships on its ontology, instead of reaching them only through the merged ontology dict or the walker.

## When to use

- An unknown skill surface you need to enumerate before walking
- A skill whose phases you want to read without loading the whole ontology
- A skill schema of uncertain shape, before it is walked or emitted

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `find` | transform | Enumerate the skills across all capabilities — walkable disciplines AND the concept pillars (Spec 375) — with light filters. | [details](references/find.md) |
| `index` | effect | Promote walkable skills into the graph as Skill + Phase nodes (Spec 026). | [details](references/index.md) |
| `lint` | transform | Validate a skill's phase-graph shape — the structural contract a walk relies on. | [details](references/lint.md) |
| `rank` | transform | Rank walkable skills against a free-text query (Spec 161 Slice 1). | [details](references/rank.md) |
| `render` | transform | Render one skill to markdown at a chosen depth (progressive disclosure). | [details](references/render.md) |

## Example

```bash
await call_tool('capability_skills_find', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Guessing a skill's phases from memory → render it via capability_skills_render
- Walking a skill of unknown shape → lint it first via capability_skills_lint

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`skills-triage`** (discipline): enumerate → read → validate → decide
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'skills-triage', 'inputs': {}, 'intent_id': '…'})`
  1. **enumerate** — Enumerate the candidate skills.
     skills.find the walkable skills that might fit the task — filter by kind/capability to keep the shortlist relevant.
  2. **read** — Read each candidate's phase graph.
     skills.render the candidates to see their phase shape — does the flow actually match the work? A name match isn't a fit.
  3. **validate** — Validate the candidate's structural shape.
     skills.lint the front-runner — a soft gate: note shape issues but don't block on them; the decide gate is the hard one.
  4. **decide** — Decide which skill to walk.
     Choose the skill whose phases genuinely fit; or decide none fits and improvise deliberately. Confirm this gate with the chosen skill (or an explicit 'none').
