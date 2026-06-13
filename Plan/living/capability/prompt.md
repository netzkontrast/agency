---
capability: prompt
pillar: capability
vision_goals: []        # TODO(why-author): which GOALS.md goals this serves
status: living
last_generated: 2026-06-13
sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this
---

# prompt — Two-lineage capability: (capability pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
_TODO: authored intent._

## Verbs (generated · 13)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `prompt.assemble_scene_brief` | act | **scene_id** · max_tokens · section_budget | Compose a Novelcrafter-style scene brief from graph state (act). |
| `prompt.audit` | effect | **prompt_body** · min_score | General-case reader-test simulation for any prompt (effect). |
| `prompt.audit_gate` | effect | **lifecycle_id** · **prompt_body** · min_score | Computed audit gate — passes iff clarity_score ≥ min_score (effect). |
| `prompt.brief_audit` | effect | **brief_id** · min_score | Rule-based clarity audit of a ResearchBrief (effect). |
| `prompt.brief_finalize` | effect | **brief_id** | Finalize a ResearchBrief — flips its status (effect). |
| `prompt.brief_render` | act | **research_intent_id** · module_ids | Render a ResearchBrief body from the dossier-skeleton template (act). |
| `prompt.catalog_list` | transform | category | List bundled CatalogModule entries optionally filtered by category (transform). |
| `prompt.engineer` | act | **builder_kind** · **context** · constraints · max_tokens | Render a PromptInstance inside a token budget (act). |
| `prompt.fragment` | transform | **slug** | Look up a single Dramatica prompt fragment (transform). |
| `prompt.fragments_for` | transform | **scope** · max_tokens | Compose multiple fragments for a storyform scope (transform). |
| `prompt.intent_capture` | act | **seed_query** · **topic** · deliverable · success_criteria | Record a structured ResearchIntent SERVING the intent (act). |
| `prompt.register_fragment` | effect | **slug** · **text** · overlay_path | Write a fragment to the project overlay (effect; runtime-extensible). |
| `prompt.token_budget_gate` | effect | **lifecycle_id** · **prompt_body** · max_tokens | Computed token-budget gate — passes iff approx_tokens ≤ max_tokens (effect). |

## Ontology (generated)

**Nodes:** `ResearchIntent`(seed_query, topic, deliverable) · `ResearchBrief`(intent, body) · `BriefAudit`(brief, clarity_score) · `CatalogModule`(category, identifier, name) · `PromptInstance`(builder_kind, rendered_body) · `PromptVariant`(parent_instance, variant_kind) · `PromptOutput`(instance, response_body) · `AntiPattern`(kind, body) · `OptimizationPass`(slug, kind)
**Edges:** `APPLIES_PASS` · `AUDITS` · `FLAGS_ANTI` · `PRODUCED_BY` · `RENDERS_FROM` · `VARIANT_OF`
**Enums:** `('ResearchIntent', 'deliverable')` ∈ {dossier, memo, outline, report} · `('CatalogModule', 'category')` ∈ {A, B, C} · `('PromptInstance', 'purpose')` ∈ {description-prompt, dialogue-prompt, exposition-prompt, few-shot-bundle, metaphor-prompt, system-prompt, writing-assist} · `('PromptVariant', 'variant_kind')` ∈ {constraint-relax, constraint-tighten, length-target, structure-shift, tone-shift, voice-shift} · `('AntiPattern', 'kind')` ∈ {adjective-heavy, ambiguous-instruction, filter-words, hallucination-prone, leading-question, on-the-nose, telling-not-showing, yes-bias} · `('OptimizationPass', 'kind')` ∈ {brevity, clarity, few-shot-injection, instruction-tightening, negative-example-injection, specificity, structural-reformat} · `('BriefAudit', 'status')` ∈ {failed, passed, pending}

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/prompt -->
