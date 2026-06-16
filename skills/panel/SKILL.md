<!-- agency-generated: v1 -->
---
name: panel
description: Use when a strategy / plan / business decision needs stress-testing through
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# panel capability

A native reimplementation of SuperClaude's Business Panel: nine strategic thinkers, three interaction modes (discussion · debate · socratic), decidable content-based mode selection. Like `thinking`/`intent`, it is DECIDABLE — it produces a structured multi-expert critique SCAFFOLD (framework lenses + signature questions); the orchestrator (or an LLM driver) fills the voices.

## When to use

- A strategic plan or business model to evaluate
- A high-stakes or controversial decision to challenge
- A learning goal that needs Socratic, framework-driven questioning

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `convene` | effect | Convene the panel on a ``subject`` — emit a mode-appropriate multi-expert critique scaffold + record it (Spec 294). | [details](references/convene.md) |
| `experts` | act | The 9-expert roster — name · framework · lens · signature question. | [details](#experts) |

## Example

```bash
await call_tool('capability_panel_convene', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- One-framework analysis of a multi-stakeholder decision → convene the panel
- Calling a strategy sound with no challenge → run convene in debate mode

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`panel-usage`** (usage): use-effect → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'panel-usage', 'inputs': {}, 'intent_id': '…'})`

## experts

The 9-expert roster — name · framework · lens · signature question.

Parameters: `()`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/experts.md.)_
