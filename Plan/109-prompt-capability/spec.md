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
  - "Plan/_research/novel-mvp-source/research-prompt-optimizer/ (the 5-tool research-prompt-optimizer pattern: intent_capture + brief_render + dossier.audit + brief_finalize + catalog_list)"
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
- [ ] 5 walkable skills ship (`dossier-author` / `prompt-engineering-pass`
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
│   ├── dossier-skeleton.md
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
        # Research-dossier lineage (1-5):
        "ResearchIntent":      ["seed_query", "topic", "deliverable",
                                "success_criteria"],
        "ResearchBrief":       ["intent", "body_uri"],
        "BriefAudit":          ["dossier", "clarity_score",
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
            "dossier", "report", "outline", "memo"},
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
        "dossier-author":            BRIEF_AUTHOR_SKILL,
        "prompt-engineering-pass": PROMPT_ENGINEERING_PASS_SKILL,
        "optimize-pass":           OPTIMIZE_PASS_SKILL,
        "audit-pass":              AUDIT_PASS_SKILL,
        "iterate-variants":        ITERATE_VARIANTS_SKILL,
    },
    schemas={
        "intent-yaml":     ["topic", "deliverable", "success_criteria"],
        "research-dossier":  ["intent_ref", "body"],
        "prompt-instance": ["template_ref", "rendered_body"],
        "audit-report":    ["brief_ref", "clarity_score", "missing_sections"],
    },
    templates={
        "dossier-skeleton":          None,  # → data/templates/
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
# dossier-author (5 phases — research-dossier lineage):
BRIEF_AUTHOR_SKILL = {
    "name": "dossier-author", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "intent-capture",
         "produces": ["intent_yaml_recorded"]},
        {"index": 2, "name": "module-select",
         "produces": ["catalog_modules_chosen"]},
        {"index": 3, "name": "dossier-render",
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
def test_dossier.audit_returns_clarity_score_and_missing_sections(): ...
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

## Prompt frameworks as walkable skills (iter-13b — user directive)

User directive (2026-06-07): *"the prompt capability should also include
all prompt Frameworks From the Research prompt optimizer skill… Like
react etc… also… they Need to bei walkeble - so that they dont Flood
context Window - but that they can be given to the Agent step by step
when the Agent needs that instructions."*

The capability ships **18 prompt frameworks** from the literature as
**walkable skills** — each phase delivers ONE chunk of instruction so
the agent's context window doesn't get flooded with the full framework
at once. The walker (per Spec 080/081 contract) advances one phase at
a time; the agent fills `produces` keys and calls back to advance.

### The 18 frameworks (catalog)

| # | Framework | Category | Phases | Triggers |
|---|---|---|---|---|
| 1 | `zero-shot` | foundational | 2 | direct instruction |
| 2 | `few-shot` | foundational | 3 | analogy from examples |
| 3 | `chain-of-thought` (CoT) | reasoning | 4 | multi-step reasoning |
| 4 | `zero-shot-cot` | reasoning | 3 | "let's think step by step" |
| 5 | `tree-of-thoughts` (ToT) | search | 5 | branching exploration |
| 6 | `react` | acting | (loop) 3+1 | reasoning + action loops |
| 7 | `rewoo` | planning | 4 | plan-then-execute |
| 8 | `reflexion` | self-critique | 4 (loop) | retry with reflection |
| 9 | `plan-and-solve` | planning | 4 | explicit plan before solve |
| 10 | `least-to-most` | decomposition | 4 | break into easier sub-problems |
| 11 | `self-consistency` | sampling | 4 | sample N reasoning paths + vote |
| 12 | `self-refine` | iteration | 4 (loop) | iterative refinement |
| 13 | `generated-knowledge` | priming | 3 | generate facts first |
| 14 | `step-back` | abstraction | 3 | abstract the question first |
| 15 | `self-ask` | decomposition | 4 (loop) | decompose into sub-questions |
| 16 | `skeleton-of-thought` | structure | 3 | skeleton then expand |
| 17 | `chain-of-verification` | verification | 4 | generate then verify |
| 18 | `persona-prompting` | role-based | 3 | adopt expert role |

### Why walkable? Context-window discipline

Without walkable delivery, including the FULL framework in a prompt
means:
- ReAct's full instruction set ≈ 800-1500 tokens of scaffolding
- 18 frameworks × ~1000 tokens = 18K tokens just for framework docs
- The agent's context window fills with meta-instructions

With walkable delivery:
- Phase 1 (e.g. ReAct "Thought") gets ~150 tokens of instruction
- Agent reasons, fills `produces` keys, calls back
- Engine tracks state in the Lifecycle
- Context-window usage stays bounded; framework guidance is
  just-in-time

### Two new verbs (iter-13b)

```python
@verb(role="act")
def framework_walk(self, name: str, problem: str = "",
                   intent_id: str = "") -> ToolResult:
    """Begin walking a prompt framework. Creates a Lifecycle that
    SERVES the intent + registers the framework's phase schema. Returns
    the FIRST phase's instructions only.

    Example: prompt.framework_walk("react", problem="Find the capital")
    → returns Phase 1 (Thought) instructions ~150 tokens."""

@verb(role="effect")
def framework_advance(self, lifecycle_id: str,
                      produces: dict) -> ToolResult:
    """Advance a framework walk to the next phase. Records the
    produces keys on the Lifecycle; returns the next phase's
    instructions OR signals completion if terminal phase fired.

    Loop-based frameworks (ReAct / Reflexion / Self-Refine): walker
    re-enters loop phase when continue_loop is set; exits when
    commit is set."""
```

### Example: ReAct as a walkable skill

```python
REACT_FRAMEWORK = {
    "name": "react", "kind": "framework",
    "category": "acting", "loop": True,
    "phases": [
        {"index": 1, "name": "thought",
         "instruction": (
             "Reason about what to do. Format: 'Thought: <reasoning>'. "
             "Identify whether you need an Action, more Thought, or commit."),
         "produces": ["thought", "next_action_kind"]},
        {"index": 2, "name": "action",
         "instruction": (
             "Choose one action. Format: 'Action: <name>(<args>)'. "
             "Available: search / lookup / compute / ask."),
         "produces": ["action_name", "action_args", "action_result"]},
        {"index": 3, "name": "observation",
         "instruction": (
             "Record what you learned. Format: 'Observation: <text>'. "
             "Decide: loop back to thought OR commit if you have the answer."),
         "produces": ["observation", "continue_loop", "commit"]},
        {"index": 4, "name": "answer",
         "instruction": "Provide the final answer. Format: 'Answer: <text>'.",
         "produces": ["final_answer"],
         "gate": "hard"},
    ],
}
```

Total context cost: ~600 tokens for a full ReAct walk versus ~2000 for
including the framework upfront.

### Lifecycle integration (Workflows Core)

User directive (2026-06-07): *"It might also have to be integrated with
Workflows Core capability (lifecycle)."*

Every framework walk creates a **Lifecycle** node (Spec 080/081
contract). The Lifecycle:
- SERVES the parent intent (provenance preserved)
- Holds the current phase + accumulated `produces` keys
- Records gate.check ledger entries for each phase
- Pauses on hard gates via `elicit`/`lifecycle_gate`

```
USER → prompt.framework_walk(name="react", problem="...")
    ↓ creates Lifecycle{state="working", phase=1, name="react"}
    ↓ Lifecycle SERVES intent
    ↓ returns phase 1 instructions (only)
AGENT → reads instructions, fills produces, calls framework_advance
    ↓
prompt.framework_advance(lifecycle_id, produces={thought, ...})
    ↓ records produces on Lifecycle + advances to phase 2
    ↓ returns phase 2 instructions (only)
... loop until commit or hard gate ...
```

### Three new ontology nodes

```python
PromptFramework  (slug, category, loop, phase_count)
FrameworkWalk    (slug, framework, lifecycle, phases_completed,
                  final_answer)
FrameworkChoice  (slug, problem, chosen_framework, rationale)
```

Closed enum: `(PromptFramework, category)`: `foundational / reasoning /
search / acting / planning / self-critique / sampling / iteration /
priming / abstraction / decomposition / structure / verification /
role-based`

### Two helper walkable skills

- `framework-select` (3 phases — characterize-problem →
  recommend → confirm HARD GATE)
- `framework-compare` (4 phases — select-pair → walk-a → walk-b →
  compare HARD GATE)

### Catalog data file

`agency/capabilities/prompt/data/reference/frameworks/catalog.yaml`
holds the 18 framework definitions verbatim with phase schemas + per-
phase `instruction` field (the token-budget delivery) + source
citations.

### Integration with existing 109 verbs

Framework walks are COMPLEMENTARY to the engineering pass:
- `prompt.engineer` composes a prompt FOR THE LLM CALL
- `prompt.framework_walk` walks THE AGENT through a reasoning framework

Complete writing-assist session:
1. Agent walks `framework-select` → choose framework
2. Agent walks the chosen framework (e.g. ReAct) → solve problem
3. Agent uses `prompt.engineer` → compose LLM call
4. Agent uses `prompt.score_output` → evaluate
5. Everything recorded in the Lifecycle + provenance graph

## Open questions

1. **Default `llm` driver requirement?** Path A rule-based works for
   all 17 verbs. Path B (LLM-needed for `intent_capture` /
   `brief_audit`) opts in via `[prompt-llm]` extra.
2. **Per-domain catalog modules?** The A/B/C × M01-M12 catalog is the
   research-dossier default; per-domain caps (novel/music/screenplay)
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
