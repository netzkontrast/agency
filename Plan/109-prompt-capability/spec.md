---
spec_id: "109"
slug: prompt-capability
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["001", "002", "020", "047", "054", "060", "076", "079", "080", "081", "092"]
affects:
  - agency/capabilities/prompt/
  - tests/test_prompt_*.py
source-material:
  - "Plan/_research/novel-mvp-source/research-prompt-optimizer/ (the 5-tool research-prompt-optimizer pattern: intent_capture + brief_render + brief_audit + brief_finalize + catalog_list)"
  - "Plan/_research/novel-mvp-source/prior-specs/021-prompt-builder.md (the 10-builder family pattern: world/character/scene/storyform/throughline/bridge/chapter/revision/theme/relationship; read-only, idempotent, source-traceable, ≤200-token preview, acyclic compose-with DAG)"
  - "Spec 104 iter-11 (novel prose cluster's prompt-engineering layer — generalized into a first-class capability)"
domain: capability / prompt-engineering
wave: 8
research_first: false
---

# Spec 109 — `prompt` Capability

## Why

User directive (2026-06-07): *"Create specs for prompt optimizer- and
critical thinking Port - and a Right Integration into Core, templates
and Schemas as well as ontology - prompt capability and a thinking
capability."*

The novel spec set's iter-11 prompt-engineering layer is a specific
application of a general pattern. The pattern is reusable across every
domain capability (music, novel, screenplay, journalism, …). Spec 109
PROMOTES it to a **first-class agency capability** registered under
`agency/capabilities/prompt/` — discoverable, walkable, composable,
provenance-tracked.

The capability ports three lineages:

1. **The 5-tool research-prompt-optimizer** (from the imported
   `agentic-tool-catalog.md` — `research_intent_capture` /
   `research_brief_render` / `research_brief_audit` /
   `research_brief_finalize` / `research_catalog_list`)
2. **The 10-builder family** (from the imported `021-novel-prompt-
   builder-family.md` — uniform signature, read-only, idempotent,
   source-traceable, ≤200-token preview, acyclic compose-with DAG)
3. **The engineering pass** (from novel iter-11 — token-budget
   composition, A/B variants, scoring, anti-pattern library,
   context injection)

## Done When

- [ ] `agency/capabilities/prompt/` registers `PromptCapability` with
      drop-in bar: zero edits to `agency/engine.py`,
      `agency/capability.py`, `agency/registry.py`, `agency/ontology.py`,
      `agency/toolresult.py`.
- [ ] 15 user-facing verbs ship + 2 internal gate verbs (see manifest).
- [ ] 5 walkable skills ship (`brief-author` / `prompt-engineering-pass`
      / `optimize-pass` / `audit-pass` / `iterate-variants`).
- [ ] Templates ship under `agency/capabilities/prompt/templates/` —
      registered on the consolidated `OntologyExtension.templates`.
- [ ] Ontology + schemas + edges declared (see Design).
- [ ] Cross-capability surface: novel (Spec 104 iter-11) refactored to
      DELEGATE its engineering verbs to `prompt.*` via `ctx.call`.
- [ ] `tests/test_prompt_*.py` Green (~18 tests).
- [ ] `TODO.md` updated with 109 row.

## Verb manifest

| # | Verb | Role | Lineage |
|---|---|---|---|
| 1 | `intent_capture` | act | research-prompt-optimizer Phase 1 (LLM-needed) |
| 2 | `brief_render` | act | research-prompt-optimizer Phase 2 (decidable) |
| 3 | `brief_audit` | effect | research-prompt-optimizer Phase 3 (LLM-needed) |
| 4 | `brief_finalize` | effect | research-prompt-optimizer Phase 5 (decidable) |
| 5 | `catalog_list` | transform | research-prompt-optimizer module catalog (A/B/C × M-IDs) |
| 6 | `build` | transform | 10-builder family generic builder (read-only, idempotent) |
| 7 | `register_builder` | effect | declare a domain-specific builder + its compose-with DAG |
| 8 | `engineer` | act | iter-11 token-budget composition (HEADLINE writing-assist verb) |
| 9 | `optimize` | act | run an OptimizationPass (clarity / brevity / specificity / instruction-tightening / few-shot-injection) |
| 10 | `score_output` | effect | human-eval scoring (promote-to-canonical via accepted=True) |
| 11 | `analyze_iteration` | transform | A/B variant comparison |
| 12 | `register_anti_pattern` | effect | record known failure modes |
| 13 | `list_templates` | transform | discover registered PromptTemplates |
| 14 | `register_template` | effect | add a PromptTemplate |
| 15 | `audit` | effect | reader-test simulation for any prompt (general-case of `brief_audit`) |

**Internal composite gate verbs**:

| # | Verb | Walks |
|---|---|---|
| G1 | `token_budget_gate` | `prompt-engineering-pass` phase 4 (render-prompt) |
| G2 | `audit_gate` | `audit-pass` skill |

**Total: 15 user + 2 gate = 17 registered verbs.**

## Design

### Module layout

```
agency/capabilities/prompt/
├── __init__.py              # PromptCapability + module docstring → SkillDoc
├── ontology.py              # OntologyExtension
├── clusters/
│   ├── __init__.py
│   ├── briefs.py            # research-prompt-optimizer verbs (1-5)
│   ├── builders.py          # 10-builder generic verbs (6-7)
│   ├── engineer.py          # engineering verbs (8-12)
│   └── catalog.py           # template + catalog verbs (13-15)
├── templates/               # template bodies
│   ├── brief-skeleton.md
│   ├── system-prompt-skeleton.md
│   ├── builder-template.md
│   ├── intent-yaml.md
│   ├── audit-checklist.md
│   ├── tradeoff-matrix.md
│   └── anti-pattern-example.md
└── data/
    ├── reference/
    │   ├── research-module-catalog.yaml   # A/B/C × M01-M12 (verbatim from
    │                                       # imported agentic-tool-catalog)
    │   └── anti-pattern-library/          # known failure modes
    │       ├── on-the-nose-dialogue.yaml
    │       ├── filter-word-overload.yaml
    │       ├── adjective-heavy.yaml
    │       └── telling-not-showing.yaml
    └── schemas/
        └── intent-yaml.schema.json
```

### Ontology (consolidated `OntologyExtension`)

```python
prompt_ontology = OntologyExtension(
    nodes={
        # Research-brief lineage (1-5):
        "ResearchIntent":      ["seed_query", "topic", "deliverable",
                                "success_criteria"],
        "ResearchBrief":       ["intent", "body_uri"],
        "BriefAudit":          ["brief", "clarity_score",
                                "missing_sections"],
        "CatalogModule":       ["category", "identifier", "name"],

        # Builder lineage (6-7):
        "Builder":             ["slug", "entity_kind", "composes_with"],

        # Engineering lineage (8-12):
        "PromptTemplate":      ["slug", "builder_kind", "body", "version"],
        "PromptInstance":      ["template", "rendered_body", "entity_refs"],
        "PromptOutput":        ["instance", "response_body", "score"],
        "PromptVariant":       ["parent_instance", "variant_kind"],
        "AntiPattern":         ["kind", "body"],
        "OptimizationPass":    ["slug", "kind", "before_metrics",
                                "after_metrics"],
    },
    enums={
        ("ResearchIntent", "deliverable"): {
            "brief", "report", "outline", "memo"},
        ("CatalogModule", "category"): {"A", "B", "C"},
        ("PromptInstance", "purpose"): {
            "writing-assist", "dialogue-prompt", "description-prompt",
            "exposition-prompt", "metaphor-prompt", "system-prompt",
            "few-shot-bundle"},
        ("PromptVariant", "variant_kind"): {
            "tone-shift", "length-target", "constraint-relax",
            "constraint-tighten", "structure-shift", "voice-shift"},
        ("AntiPattern", "kind"): {
            "on-the-nose", "filter-words", "adjective-heavy",
            "telling-not-showing", "leading-question", "yes-bias",
            "hallucination-prone", "ambiguous-instruction"},
        ("OptimizationPass", "kind"): {
            "clarity", "brevity", "specificity",
            "instruction-tightening", "few-shot-injection",
            "negative-example-injection", "structural-reformat"},
    },
    edges={
        "RENDERS_FROM",      # ResearchBrief → ResearchIntent
        "AUDITS",            # BriefAudit → ResearchBrief
        "COMPOSED_BY",       # PromptInstance → Builder
        "BUNDLES_TEMPLATE",  # PromptInstance → PromptTemplate
        "VARIANT_OF",        # PromptVariant → PromptInstance
        "PRODUCED_BY",       # PromptOutput → PromptInstance
        "FLAGS_ANTI",        # PromptOutput → AntiPattern
        "APPLIES_PASS",      # PromptInstance → OptimizationPass
    },
    skills={
        "brief-author":            BRIEF_AUTHOR_SKILL,
        "prompt-engineering-pass": PROMPT_ENGINEERING_PASS_SKILL,
        "optimize-pass":           OPTIMIZE_PASS_SKILL,
        "audit-pass":              AUDIT_PASS_SKILL,
        "iterate-variants":        ITERATE_VARIANTS_SKILL,
    },
    schemas={
        "intent-yaml":     ["topic", "deliverable", "success_criteria"],
        "research-brief":  ["intent_ref", "body"],
        "prompt-instance": ["template_ref", "rendered_body"],
        "audit-report":    ["brief_ref", "clarity_score", "missing_sections"],
    },
    templates={
        "brief-skeleton":          None,  # → data/templates/
        "system-prompt-skeleton":  None,
        "builder-template":        None,
        "intent-yaml":             None,
        "audit-checklist":         None,
        "tradeoff-matrix":         None,
        "anti-pattern-example":    None,
    },
)
```

### 5 walkable skills

```python
# brief-author (5 phases — research-brief lineage):
BRIEF_AUTHOR_SKILL = {
    "name": "brief-author", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "intent-capture",
         "produces": ["intent_yaml_recorded"]},
        {"index": 2, "name": "module-select",
         "produces": ["catalog_modules_chosen"]},
        {"index": 3, "name": "brief-render",
         "produces": ["brief_body_rendered"]},
        {"index": 4, "name": "audit",
         "produces": ["audit_findings"],
         "gate": "computed", "gate_verb": "prompt.audit_gate"},
        {"index": 5, "name": "finalize",
         "produces": ["brief_finalized"], "gate": "hard"},
    ],
}

# prompt-engineering-pass (6 phases — engineering lineage, verbatim
# from novel iter-11 generalized):
PROMPT_ENGINEERING_PASS_SKILL = {
    "name": "prompt-engineering-pass", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "select-builder",
         "produces": ["builder_kind_selected"]},
        {"index": 2, "name": "inject-context",
         "produces": ["context_refs_chosen"]},
        {"index": 3, "name": "specify-constraints",
         "produces": ["constraints_declared", "anti_patterns_loaded"]},
        {"index": 4, "name": "render-prompt",
         "produces": ["prompt_instance_built"],
         "gate": "computed", "gate_verb": "prompt.token_budget_gate"},
        {"index": 5, "name": "iterate-variants",
         "produces": ["variants_evaluated"]},
        {"index": 6, "name": "score-output",
         "produces": ["output_scored"], "gate": "hard"},
    ],
}

# optimize-pass (3 phases — apply a known OptimizationPass):
OPTIMIZE_PASS_SKILL = {
    "name": "optimize-pass", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "measure-before",
         "produces": ["before_metrics_recorded"]},
        {"index": 2, "name": "apply-pass",
         "produces": ["transformed_prompt_rendered"]},
        {"index": 3, "name": "measure-after",
         "produces": ["after_metrics_recorded"], "gate": "hard"},
    ],
}

# audit-pass (2 phases — reader-test simulation):
AUDIT_PASS_SKILL = {
    "name": "audit-pass", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "scan",
         "produces": ["sections_found", "sections_missing"]},
        {"index": 2, "name": "verdict",
         "produces": ["clarity_score", "recommendations"],
         "gate": "hard"},
    ],
}

# iterate-variants (4 phases — A/B variants):
ITERATE_VARIANTS_SKILL = {
    "name": "iterate-variants", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "fork-variants",
         "produces": ["variants_created"]},
        {"index": 2, "name": "run-each",
         "produces": ["outputs_collected"]},
        {"index": 3, "name": "score-each",
         "produces": ["scores_recorded"]},
        {"index": 4, "name": "select-winner",
         "produces": ["winning_variant_chosen"], "gate": "hard"},
    ],
}
```

### Integration: Core registration

Per CLAUDE.md doctrine: domain capabilities live in `examples/`; this
is NOT a domain capability — it's a substrate-adjacent capability
(like `intent`, `develop`, `document`, `research`). Lands in
`agency/capabilities/prompt/` (first-class) per the same reasoning as
Spec 091 (`intent` capability) and Spec 093 (`music` first-class
exception).

### Integration: Cross-capability delegation

The novel capability's iter-11 prompt-engineering verbs become thin
wrappers around `prompt.*`:

```python
# In agency/capabilities/novel/clusters/prose.py — refactored:
@verb(role="act")
def chapter_draft_assisted(self, novel: str, chapter: int,
                           outline_beats: str = "",
                           inject_prompt_snippet: bool = True
                           ) -> ToolResult:
    """Path A scaffold; Path B with LLM. When inject_prompt_snippet=True
    and PromptSnippet exists, delegate to prompt.engineer for context
    composition."""
    if inject_prompt_snippet:
        instance = self.ctx.call("prompt", "engineer",
                                  builder="chapter",
                                  entity_id=f"{novel}:ch{chapter}",
                                  context_refs=[...],   # research entities
                                  voice_refs=[...],      # character voices
                                  constraints={...},
                                  token_budget=4000)
        prompt_body = instance["rendered_body"]
    # ...rest unchanged
```

Music can adopt the same pattern when it ships its own LLM-assisted
verbs (currently iter-5 stubs).

## Test plan

```python
# tests/test_prompt_capability.py — ~18 tests
def test_capability_registers(): ...
def test_drop_in_bar_zero_engine_edits(): ...
def test_intent_capture_records_research_intent_node(): ...
def test_brief_render_is_deterministic_for_same_inputs(): ...
def test_brief_audit_returns_clarity_score_and_missing_sections(): ...
def test_brief_finalize_packages_artefact_set(): ...
def test_catalog_list_returns_36_modules_from_yaml(): ...
def test_build_is_read_only_and_idempotent(): ...
def test_build_preview_under_200_tokens(): ...
def test_build_source_traceability_every_fragment_in_sources(): ...
def test_engineer_composes_within_token_budget(): ...
def test_engineer_records_prompt_instance(): ...
def test_score_output_with_accepted_creates_canonical_draft(): ...
def test_analyze_iteration_compares_variants(): ...
def test_register_anti_pattern_persists(): ...
def test_optimize_applies_known_pass_and_records_metrics(): ...
def test_audit_general_returns_audit_report(): ...
def test_brief_author_skill_walks_through_audit_gate(): ...
def test_prompt_engineering_pass_skill_walks_through_token_budget_gate(): ...
```

## Open questions

1. **Default `llm` driver requirement?** Path A rule-based works for
   all 17 verbs. Path B (LLM-needed for `intent_capture` /
   `brief_audit`) opts in via `[prompt-llm]` extra.
2. **Per-domain catalog modules?** The A/B/C × M01-M12 catalog is the
   research-brief default; per-domain caps (novel/music/screenplay)
   may declare ADDITIONAL catalog modules under their own
   `data/reference/`.
3. **Shared anti-pattern library?** The base 8 anti-patterns ship with
   109. Domain caps add their own under `data/reference/` (e.g. novel
   adds "filter-word-overload"; music adds "on-the-nose-lyric").
4. **Naming collision with `agency intent`?** No — `intent` is the
   existing capability; this ships as `prompt`. Verbs like
   `intent_capture` are scoped to `prompt.intent_capture` (no
   collision with `intent.suggests` etc.).

## Followup

(Populated when the PR ships.)
