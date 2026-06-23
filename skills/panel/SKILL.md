---
name: panel
description: "Use when a strategy / plan / business decision needs stress-testing through"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

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
| `experts` | act | The 9-expert roster — name · framework · lens · signature question. | [details](references/experts.md) |

## Example

```bash
await call_tool('capability_panel_convene', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- One-framework analysis of a multi-stakeholder decision → convene the panel
- Calling a strategy sound with no challenge → run convene in debate mode

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`strategic-analysis`** (discipline): frame → convene → challenge → synthesize
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'strategic-analysis', 'inputs': {}, 'intent_id': '…'})`
  1. **frame** — Frame the subject and the panel mode.
     State what's under strategic analysis and the mode (sequential, debate, or Socratic). A sharp subject focuses the panel.
  2. **convene** — Convene the expert lenses over the subject.
     Run each expert lens (Christensen, Porter, Drucker, …) over the subject; capture each one's distinct read. Don't collapse them into one voice.
  3. **challenge** — Surface the tensions between the experts.
     Where do the lenses DISAGREE? The tensions are the signal — the places the strategy is genuinely contested, not the consensus.
  4. **synthesize** — Synthesise a decision from the tensions.
     Resolve the tensions into a strategic recommendation with its rationale. Confirm this gate only when the synthesis takes a position, not a summary of views.

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_panel_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_panel_convene", {"intent_id": iid})
await call_tool("capability_panel_experts", {"intent_id": iid})
```
