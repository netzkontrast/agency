<!-- agency-generated: v1 -->
---
name: prompt
description: Use when authoring research dossiers, engineering structured prompts that honor a token budget, auditing prompts for clarity / anti-patterns.
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# prompt capability

Two-lineage capability:

## When to use

- A research intent needs a dossier authored before generation begins
- A prompt is being constructed and needs token-budget gating
- An LLM output flagged for anti-patterns needs an optimization pass

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
| `fragment` | transform | Look up a single Dramatica prompt fragment (transform). | [details](references/fragment.md) |
| `fragments_for` | transform | Compose multiple fragments for a storyform scope (transform). | [details](references/fragments_for.md) |
| `framework` | transform | Look up a single prompt-engineering framework by slug (transform). | [details](references/framework.md) |
| `frameworks_for` | transform | Budget-aware candidate list for a known intent category (transform). | [details](references/frameworks_for.md) |
| `intent_capture` | act | Record a structured ResearchIntent SERVING the intent (act). | [details](references/intent_capture.md) |
| `register_fragment` | effect | Write a fragment to the project overlay (effect; runtime-extensible). | [details](references/register_fragment.md) |
| `register_framework` | effect | Write a custom framework to the project overlay (effect; extensible). | [details](references/register_framework.md) |
| `token_budget_gate` | effect | Computed token-budget gate — passes iff approx_tokens ≤ max_tokens (effect). | [details](references/token_budget_gate.md) |

## Example

```bash
await call_tool('capability_prompt_assemble_scene_brief', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-rolling prompts outside the engineering pipeline → call `prompt.engineer`
- Skipping the audit gate → call `prompt.audit` (general-case) or `prompt.brief_audit` (dossier-case)

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`dossier-author`** (workflow): intent-capture → module-select → dossier-render → audit → finalize
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'dossier-author', 'inputs': {}, 'intent_id': '…'})`
- **`prompt-engineering-pass`** (workflow): select-builder → inject-context → specify-constraints → render-prompt → iterate-variants → score-output
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'prompt-engineering-pass', 'inputs': {}, 'intent_id': '…'})`
