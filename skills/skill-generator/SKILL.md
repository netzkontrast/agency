---
name: skill-generator
description: "Use when a deploy-ready skill should be produced — grounded in a capability's"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# skill-generator capability

Skill_generator builds a skill from a capability's REAL surface: `ground` reads its live verbs + signatures + docstrings + ontology; `author` samples the host LLM with a per-type skill-creator prompt over that grounding to draft a schema-valid skill; `generate` renders a CSO-clean SKILL.md from a description.

## When to use

- A new skill needed without hand-assembling its files
- A skill idea that should become a deployable artefact
- Authoring a skill that must reference a capability's real verbs (not guesses)

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `author` | act | Draft a skill for a capability by sampling the host LLM with a per-type skill-creator prompt grounded in the cap's real surface (Spec 374 Slices 2–3). | [details](references/author.md) |
| `generate` | act | Author a SKILL.md and lint it against the CSO rules, flagging if not deploy-ready. | [details](references/generate.md) |
| `ground` | transform | Build the authoring grounding for a capability — its live verbs, signatures, docstrings, and ontology — the structured input a skill-creator prompt fills, and the no-host fallback an author reads. | [details](references/ground.md) |

## Example

```bash
await call_tool('capability_skill_generator_author', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-writing a SKILL.md from scratch → ground it via capability_skill_generator_ground
- Authoring a skill that references verbs not in the registry → capability_skill_generator_author grounds in the live surface
- Sampling the host at install time (breaks reproducibility, A7) → author at authoring time and commit the reviewed result

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`skill_generator-usage`** (usage): use-transform → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'skill_generator-usage', 'inputs': {}, 'intent_id': '…'})`

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_skill_generator_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_skill_generator_author", {"intent_id": iid})
await call_tool("capability_skill_generator_generate", {"intent_id": iid})
await call_tool("capability_skill_generator_ground", {"intent_id": iid})
```
