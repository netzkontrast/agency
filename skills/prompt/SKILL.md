---
name: prompt
description: "Author research dossiers, engineer token-budgeted prompts, route a draft to the right one of 27 research-backed frameworks, and score prompts — and agency's own functional docs — for clarity and anti-patterns. Use when authoring a research dossier, engineering a token-budgeted prompt,"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# prompt capability

Author research dossiers, engineer token-budgeted prompts, route a draft to the right one of 27 research-backed frameworks, and score prompts — and agency's own functional docs — for clarity and anti-patterns. The prompt-as-substrate spine where templates, the framework library, and evaluation meet.

## When to use

- A research intent needs a dossier authored before generation begins
- A draft prompt needs the right framework picked, then filled to a token budget
- A prompt or a capability's own doc needs clarity / anti-pattern scoring

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `assemble_scene_brief` | act | Compose a Novelcrafter-style scene brief from graph state (act). | [details](references/assemble_scene_brief.md) |
| `audit` | effect | General-case reader-test simulation for any prompt (effect). | [details](references/audit.md) |
| `audit_gate` | effect | Computed audit gate — passes iff clarity_score ≥ min_score (effect). | [details](references/audit_gate.md) |
| `brief_audit` | effect | Rule-based clarity audit of a ResearchBrief (effect). | [details](references/brief_audit.md) |
| `brief_finalize` | effect | Finalize a ResearchBrief — flips its status (effect). | [details](references/brief_finalize.md) |
| `brief_render` | act | Render a ResearchBrief body from the dossier-skeleton template (act). | [details](references/brief_render.md) |
| `catalog_list` | transform | List bundled CatalogModule entries optionally filtered by category (transform). | [details](references/catalog_list.md) |
| `engineer` | act | Render a PromptInstance inside a token budget (act). | [details](references/engineer.md) |
| `evaluate` | effect | Goal-aware multi-dimension evaluation of a prompt body (effect). | [details](references/evaluate.md) |
| `fragment` | transform | Look up a single Dramatica prompt fragment (transform). | [details](references/fragment.md) |
| `fragments_for` | transform | Compose multiple fragments for a storyform scope (transform). | [details](references/fragments_for.md) |
| `framework` | transform | Look up a single prompt-engineering framework by slug (transform). | [details](references/framework.md) |
| `frameworks_for` | transform | Budget-aware candidate list for a known intent category (transform). | [details](references/frameworks_for.md) |
| `intent_capture` | act | Record a structured ResearchIntent SERVING the intent (act). | [details](references/intent_capture.md) |
| `register_fragment` | effect | Write a fragment to the project overlay (effect; runtime-extensible). | [details](references/register_fragment.md) |
| `register_framework` | effect | Write a custom framework to the project overlay (effect; extensible). | [details](references/register_framework.md) |
| `render` | act | Fill a framework's template with ``fields`` → a PromptInstance (act). | [details](references/render.md) |
| `route_framework` | effect | Route a free-text ``draft`` to the ONE right framework (effect). | [details](references/route_framework.md) |
| `token_budget_gate` | effect | Computed token-budget gate — passes iff approx_tokens ≤ max_tokens (effect). | [details](references/token_budget_gate.md) |

## Example

```bash
await call_tool('capability_prompt_assemble_scene_brief', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-rolling a prompt instead of routing → call `prompt.route_framework` then `prompt.render`
- Reading all 27 frameworks to pick one → `prompt.route_framework` returns the one
- Skipping the score gate → `prompt.evaluate` (or `prompt.audit` for the legacy contract)
- Adding a Role to a function's doc → that is `role_padding`; functions need actionable insight, not a persona

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`dossier-author`** (workflow): intent-capture → module-select → dossier-render → audit → finalize
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'dossier-author', 'inputs': {}, 'intent_id': '…'})`
- **`prompt-engineering-pass`** (workflow): select-builder → inject-context → specify-constraints → render-prompt → iterate-variants → score-output
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'prompt-engineering-pass', 'inputs': {}, 'intent_id': '…'})`
