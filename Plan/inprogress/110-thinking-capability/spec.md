---
spec_id: "110"
slug: thinking-capability
status: draft
state: inprogress
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["001", "002", "020", "047", "054", "060", "076", "079", "080", "081", "091", "092"]
affects:
  - agency/capabilities/thinking/
  - agency/capabilities/intent/    # may relocate critical-thinking methods (see Open Q)
  - tests/test_thinking_*.py
source-material:
  - "Spec 091 (intent capability): 8 critical-thinking methods (decompose / assumptions / premortem / first_principles / inversion / steelman / second_order / tradeoffs)"
  - "Plan/inprogress/101-novel-complete-build/CRITICAL-ANALYSIS.md (iter-12 application of the 8 methods to the novel spec set — proves the methods compose across domains)"
domain: capability / reasoning
wave: 8
research_first: false
---

# Spec 110 — `thinking` Capability

## Why

User directive (2026-06-07): *"Create specs for prompt optimizer- and
critical thinking Port - and a Right Integration into Core, templates
and Schemas as well as ontology - prompt capability and a thinking
capability."*

Spec 091 (`intent` capability) ships eight critical-thinking methods —
but as side-methods of the intent-bootstrap workflow. The methods are
GENERAL-purpose: novel iter-12 proved they apply to design review of
ANY spec set, not just intent analysis.

Spec 110 PROMOTES these to a first-class `thinking` capability under
`agency/capabilities/thinking/` AND extends with 6 additional methods.
The `intent` capability's critical-thinking methods become thin
wrappers that delegate to `thinking.*` (see Migration Plan in 111).

## What the capability ships

**14 critical-thinking methods** (8 from intent + 6 net-new):

| # | Method | From | What it produces |
|---|---|---|---|
| 1 | `decompose` | intent (091) | MECE sub-problems |
| 2 | `assumptions` | intent (091) | load-bearing vs incidental tagging |
| 3 | `premortem` | intent (091) | assume-failed → causes + mitigations |
| 4 | `first_principles` | intent (091) | strip-to-fundamentals reasoning |
| 5 | `inversion` | intent (091) | what-guarantees-failure analysis |
| 6 | `steelman` | intent (091) | strongest counter-case |
| 7 | `second_order` | intent (091) | consequence chain (N steps) |
| 8 | `tradeoffs` | intent (091) | options × criteria matrix |
| 9 | **`red_team`** | NEW (iter-12) | adversarial review pass |
| 10 | **`socratic`** | NEW (iter-12) | five-why-deeper questioning |
| 11 | **`pre_commitment`** | NEW (iter-12) | odyssey-binding decision lock |
| 12 | **`if_then_else`** | NEW (iter-12) | explicit decision-tree branching |
| 13 | **`bayesian_update`** | NEW (iter-12) | prior + evidence → posterior |
| 14 | **`analogy_map`** | NEW (iter-12) | cross-domain analogical reasoning |

Plus 3 composite verbs:
- `apply_full_review(subject, depth)` — runs the 8 core methods in
  sequence; produces a full critical-analysis artefact (the pattern
  novel iter-12 used)
- `apply_decision_discipline(subject, decision, depth)` — runs
  tradeoffs + premortem + red_team + pre_commitment for binding
  decisions
- `apply_design_review(spec_path, depth)` — runs all 14 methods on a
  spec/design doc (the pattern that produced novel iter-12)

## Done When

- [ ] `agency/capabilities/thinking/` registers `ThinkingCapability`
      with drop-in bar.
- [ ] 14 method verbs + 3 composite verbs = 17 user-facing verbs.
- [ ] 3 walkable skills (`critical-thinking` / `red-team-pass` /
      `decision-discipline`).
- [ ] Templates ship under `agency/capabilities/thinking/templates/`
      (decompose / tradeoff-matrix / premortem / bayesian-update /
      analogy-map / red-team-checklist / pre-commitment-bind).
- [ ] Ontology + schemas + edges declared (see Design).
- [ ] Migration: `intent` capability's 8 methods become thin
      wrappers (see Spec 111). Backward-compat preserved for callers
      of `intent.decompose` etc.
- [ ] `tests/test_thinking_capability.py` Green (~20 tests).
- [ ] `TODO.md` updated with 110 row.

## Verb manifest

### 14 method verbs (uniform signature)

```python
@verb(role="transform")  # ALL methods are read-only transforms
def decompose(self, subject: str = "",
              intent_id: str = "") -> ToolResult:
    """MECE sub-problems. Defaults subject to the serving intent
    (per Spec 091's pattern). Returns {sub_problems: list[dict],
    coverage_score: 0.0-1.0, residual: list[str]}.

    Output schema: 'thinking-decompose'.
    Template: 'decompose-template'.
    """

@verb(role="transform")
def assumptions(self, subject: str = "",
                intent_id: str = "") -> ToolResult: ...
    # Returns {assumptions: [{claim, load_bearing: bool,
    #                        status: held|refuted, evidence_refs}]}

@verb(role="transform")
def premortem(self, subject: str = "",
              intent_id: str = "") -> ToolResult: ...
    # Returns {assume_failed_cause: str,
    #          causes: list[dict], mitigations: list[dict]}

@verb(role="transform")
def first_principles(self, subject: str = "",
                     intent_id: str = "") -> ToolResult: ...
    # Returns {fundamentals: list[str], derived: list[str],
    #          irreducible_core: str}

@verb(role="transform")
def inversion(self, subject: str = "",
              intent_id: str = "") -> ToolResult: ...
    # Returns {what_guarantees_failure: list[dict]}

@verb(role="transform")
def steelman(self, subject: str = "", position: str = "",
             intent_id: str = "") -> ToolResult: ...
    # Returns {strongest_counter_argument: str, response: str}

@verb(role="transform")
def second_order(self, subject: str = "", n_steps: int = 3,
                 intent_id: str = "") -> ToolResult: ...
    # Returns {consequence_chain: [{step, claim, downstream}]}

@verb(role="transform")
def tradeoffs(self, subject: str = "",
              options: list = None, criteria: list = None,
              intent_id: str = "") -> ToolResult: ...
    # Returns {matrix: dict[option, dict[criterion, score]],
    #          recommendation: str}

# NEW in 110 (6 net-new methods):

@verb(role="transform")
def red_team(self, subject: str = "", n_attacks: int = 5,
             intent_id: str = "") -> ToolResult:
    """Adversarial review. Adopts an attacker's stance and identifies
    weaknesses. Returns {attacks: [{name, weakness, exploit_path,
    severity}], top_recommendation: str}.

    Distinct from steelman: steelman finds the strongest argument
    AGAINST your position; red_team finds the strongest path to your
    SYSTEM's failure."""

@verb(role="transform")
def socratic(self, subject: str = "", n_questions: int = 5,
             intent_id: str = "") -> ToolResult:
    """Five-why-deeper questioning. Recursively asks "why" / "what
    if" / "how do you know" to surface implicit assumptions. Returns
    {questions: [{level, q, implied_assumption}],
     exposed_assumptions: list[str]}."""

@verb(role="effect")  # records a PreCommitment node
def pre_commitment(self, subject: str = "", decision: str = "",
                   binding_conditions: list = None,
                   intent_id: str = "") -> ToolResult:
    """Odyssey-binding pre-commitment. Records a decision + the
    conditions under which the user has pre-committed (e.g. "if
    metric X falls below Y, we ship the slim variant"). The
    PreCommitment node SERVES the intent + is queried by 108's gates
    later. Tests assert that a pre-committed decision cannot be
    silently flipped — modification records a CHANGED_BY edge."""

@verb(role="transform")
def if_then_else(self, subject: str = "", scenarios: list = None,
                 intent_id: str = "") -> ToolResult:
    """Decision-tree branching. Given scenarios (each with conditions
    + outcomes), renders a clean tree. Returns {tree: nested-dict,
    leaf_nodes: list[dict]}."""

@verb(role="effect")  # records BayesianBelief + Evidence nodes
def bayesian_update(self, claim: str = "",
                    prior: float = 0.5, evidence: list = None,
                    intent_id: str = "") -> ToolResult:
    """Explicit Bayesian reasoning. Given a prior P(claim) and a list
    of evidence items (each with likelihood ratio), computes the
    posterior. Returns {prior, posterior, evidence_summary,
    confidence_level}.

    The BayesianBelief node SERVES the intent; queryable later via
    memory.provenance — the reasoning trail is preserved."""

@verb(role="transform")
def analogy_map(self, subject: str = "",
                target_domain: str = "",
                intent_id: str = "") -> ToolResult:
    """Cross-domain analogical reasoning. Maps the subject onto a
    target domain (e.g. 'novel-writing capability AS-IF a music-
    production capability'). Returns {mapping: dict[subject_concept,
    target_concept], insights: list[str], limits_of_analogy: list[str]}."""
```

### 3 composite verbs

```python
@verb(role="effect")
def apply_full_review(self, subject: str = "", depth: str = "standard",
                       intent_id: str = "") -> ToolResult:
    """Runs the 8 CORE methods in sequence (decompose → assumptions
    → premortem → first_principles → inversion → steelman →
    second_order → tradeoffs). Produces a single
    CriticalAnalysisArtefact node with all 8 sub-findings.
    Depth: brief | standard | deep — controls per-method elaboration."""

@verb(role="effect")
def apply_decision_discipline(self, subject: str = "",
                              decision: str = "",
                              depth: str = "standard",
                              intent_id: str = "") -> ToolResult:
    """Runs tradeoffs + premortem + red_team + pre_commitment for a
    BINDING decision. Produces a DecisionRecord node that 108's
    gates query later."""

@verb(role="effect")
def apply_design_review(self, spec_path: str,
                        depth: str = "standard",
                        intent_id: str = "") -> ToolResult:
    """Runs ALL 14 methods on a spec/design document. Produces a
    DesignReviewArtefact node — the pattern that produced novel
    iter-12's CRITICAL-ANALYSIS.md."""
```

**Total: 14 method + 3 composite = 17 user-facing verbs.**

## Design

### Ontology

```python
thinking_ontology = OntologyExtension(
    nodes={
        # Per-method artefact nodes:
        "DecomposeFinding":      ["intent_ref", "sub_problems",
                                  "coverage_score"],
        "Assumption":            ["claim", "load_bearing",
                                  "status"],
        "PremortemFinding":      ["intent_ref", "assume_failed_cause",
                                  "causes", "mitigations"],
        "FirstPrincipleFinding": ["intent_ref", "fundamentals",
                                  "irreducible_core"],
        "InversionFinding":      ["intent_ref",
                                  "what_guarantees_failure"],
        "Steelman":              ["intent_ref", "position",
                                  "strongest_counter", "response"],
        "ConsequenceChain":      ["intent_ref", "n_steps", "chain"],
        "Tradeoff":              ["intent_ref", "options", "criteria",
                                  "matrix", "recommendation"],
        "RedTeamFinding":        ["intent_ref", "attacks", "severity"],
        "SocraticChain":         ["intent_ref", "questions",
                                  "exposed_assumptions"],
        "PreCommitment":         ["intent_ref", "decision",
                                  "binding_conditions"],
        "IfThenElseTree":        ["intent_ref", "tree"],
        "BayesianBelief":        ["claim", "prior", "posterior"],
        "Evidence":              ["belief_ref", "description",
                                  "likelihood_ratio"],
        "AnalogyMap":            ["intent_ref", "source_subject",
                                  "target_domain", "mapping"],

        # Composite artefacts:
        "CriticalAnalysisArtefact": ["intent_ref", "depth",
                                     "findings_refs"],
        "DecisionRecord":           ["intent_ref", "decision",
                                     "discipline_refs"],
        "DesignReviewArtefact":     ["spec_path", "depth",
                                     "findings_refs"],
    },
    enums={
        ("Assumption", "load_bearing"): {True, False},
        ("Assumption", "status"): {"held", "refuted", "amended"},
        ("RedTeamFinding", "severity"): {"low", "medium", "high",
                                         "critical"},
        ("PreCommitment", "binding_strength"): {"soft", "firm", "hard"},
    },
    edges={
        "DEPENDS_ON_FINDING",  # composite → atomic finding
        "REFUTES",             # later artefact refutes a prior assumption
        "REINFORCES",          # later artefact reinforces
        "CHANGED_BY",          # PreCommitment lineage
        "DERIVED_FROM",        # BayesianBelief evidence ref
    },
    skills={
        "critical-thinking":   CRITICAL_THINKING_SKILL,      # from 091
        "red-team-pass":       RED_TEAM_PASS_SKILL,          # new
        "decision-discipline": DECISION_DISCIPLINE_SKILL,    # new
    },
    schemas={
        "decompose-finding":         ["sub_problems"],
        "assumption-record":         ["claim", "load_bearing"],
        "premortem-finding":         ["assume_failed_cause", "causes"],
        "tradeoff-matrix":           ["options", "criteria", "matrix"],
        "red-team-finding":          ["attacks", "severity"],
        "bayesian-belief":           ["claim", "prior", "posterior"],
        "analogy-map":               ["source_subject", "target_domain"],
        "critical-analysis-artefact":["depth", "findings_refs"],
        "decision-record":           ["decision", "binding_strength"],
        "design-review-artefact":    ["spec_path", "findings_refs"],
    },
    templates={
        "decompose-template":          None,
        "tradeoff-matrix":             None,
        "premortem-template":          None,
        "bayesian-update-template":    None,
        "analogy-map-template":        None,
        "red-team-checklist":          None,
        "pre-commitment-bind":         None,
        "design-review-template":      None,
        "decision-record-template":    None,
    },
)
```

### 3 walkable skills

```python
# critical-thinking — already authored per 091, ported VERBATIM here.

# red-team-pass (4 phases):
RED_TEAM_PASS_SKILL = {
    "name": "red-team-pass", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "adopt-adversary",
         "produces": ["adversary_stance_declared"]},
        {"index": 2, "name": "challenge",
         "produces": ["attacks_enumerated"]},
        {"index": 3, "name": "defense",
         "produces": ["defenses_articulated"]},
        {"index": 4, "name": "synthesis",
         "produces": ["recommendations"], "gate": "hard"},
    ],
}

# decision-discipline (6 phases):
DECISION_DISCIPLINE_SKILL = {
    "name": "decision-discipline", "kind": "workflow",
    "phases": [
        {"index": 1, "name": "state",
         "produces": ["decision_stated"]},
        {"index": 2, "name": "tradeoffs",
         "produces": ["tradeoffs_done"]},
        {"index": 3, "name": "premortem",
         "produces": ["premortem_done"]},
        {"index": 4, "name": "red-team",
         "produces": ["red_team_done"]},
        {"index": 5, "name": "pre-commit",
         "produces": ["pre_commitment_bound"]},
        {"index": 6, "name": "review",
         "produces": ["decision_accepted"], "gate": "hard"},
    ],
}
```

## Integration with the broader engine

### Cross-capability surface

The `thinking` capability is invoked by:
- `intent` (091) — its 8 methods become thin wrappers delegating to
  `thinking.*` (see Spec 111 migration)
- `develop` (064/060) — its design-review pass calls
  `thinking.apply_design_review`
- `analyze` (042) — its quality axis prioritization calls
  `thinking.tradeoffs`
- `delegate` (040) — its dispatch decision calls
  `thinking.tradeoffs` + `thinking.premortem`
- Domain caps (novel/music/screenplay) — call
  `thinking.apply_decision_discipline` for major design choices

### Discoverable via `agency_welcome`

`thinking` registers like any other capability. `agency_welcome`
lists it. `intent.suggests` (091) recommends `thinking.*` methods
for high-uncertainty intents.

## Lifecycle integration (Workflows Core)

User directive (2026-06-07): *"It might also have to be integrated with
Workflows Core capability (lifecycle)."*

Every thinking-method invocation that produces an artefact creates a
**ThoughtChain** Lifecycle node (Spec 080/081 contract). The Lifecycle:

- SERVES the parent intent (provenance preserved)
- Holds accumulated method-findings as the chain progresses
- Records gate.check ledger entries when a composite verb
  (`apply_full_review` / `apply_decision_discipline` /
  `apply_design_review`) walks its 8/14 methods in sequence
- Pauses on hard gates via `elicit`/`lifecycle_gate` — composite
  reviews can require human acknowledgement of critical findings
  (RedTeam severity=critical) before progressing

Each method verb optionally accepts `lifecycle_id` to RESUME a
ThoughtChain in progress (vs starting a new one):

```python
# First call — starts a chain:
result1 = thinking.decompose(subject="design X")
# returns {finding_id, lifecycle_id}

# Subsequent methods attach to the same chain:
result2 = thinking.assumptions(subject="design X",
                                lifecycle_id=result1["lifecycle_id"])
# attaches AssumptionFinding to the same ThoughtChain
```

The `critical-thinking` walkable skill (ported from Spec 091) creates
ThoughtChain Lifecycles by default. Each phase records its method-
finding as part of the chain.

### ThoughtChain node (new — added to ontology)

```python
ThoughtChain  (slug, intent_ref, depth, finding_refs: list,
               status, started_at, completed_at)
               # status: working / paused / complete / abandoned
```

ThoughtChain SERVES the parent intent + accumulates DEPENDS_ON_FINDING
edges to atomic findings as the chain progresses. A composite verb
(`apply_full_review`) populates one ThoughtChain with 8 finding refs;
`apply_design_review` populates with 14.

## Test plan

```python
# tests/test_thinking_capability.py — ~20 tests
def test_capability_registers_with_drop_in_bar(): ...
def test_decompose_defaults_subject_to_intent_deliverable(): ...
def test_assumptions_distinguishes_load_bearing_from_incidental(): ...
def test_premortem_returns_causes_and_mitigations(): ...
def test_first_principles_extracts_irreducible_core(): ...
def test_inversion_lists_failure_guarantees(): ...
def test_steelman_returns_strongest_counter_plus_response(): ...
def test_second_order_chain_has_n_steps(): ...
def test_tradeoffs_matrix_has_recommendation(): ...
def test_red_team_returns_severity_classified_attacks(): ...
def test_socratic_exposes_implicit_assumptions(): ...
def test_pre_commitment_records_node_with_binding_strength(): ...
def test_pre_commitment_modification_records_changed_by_edge(): ...
def test_if_then_else_renders_decision_tree(): ...
def test_bayesian_update_computes_posterior(): ...
def test_bayesian_update_records_evidence_provenance(): ...
def test_analogy_map_returns_mapping_and_limits(): ...
def test_apply_full_review_runs_8_methods_in_sequence(): ...
def test_apply_decision_discipline_records_decision_record(): ...
def test_apply_design_review_produces_design_review_artefact(): ...
def test_decision_discipline_skill_walks_through_6_phases(): ...
```

## Open questions

1. **Naming collision with `intent.<method>`?** No — `intent.decompose`
   stays (becomes thin wrapper); `thinking.decompose` is the
   canonical home. Spec 111 documents the migration; callers see no
   API break.
2. **PreCommitment binding strength enforcement?** Soft = warning;
   firm = warning + log; hard = blocking gate (108-pattern). For v1,
   all three record the node; gate enforcement is a v2 follow-up.
3. **Bayesian-update prior elicitation?** v1 accepts numeric prior;
   v2 may add `elicit_prior` verb that walks the user through
   prior calibration.
4. **Analogy-map source domain?** v1 accepts target_domain only
   (source = subject). v2 may support explicit source_domain.

## Followup

## Followup — Implementation Status (2026-06-09)

**Verdict:** Partial (Slice 1 shipped — 8 founding methods + 2 net-new + 1 composite + 1 skill).

### Done (Slice 1 — bundled with PR #77 / Spec 109)
- **11 verbs**: 8 founding (`decompose`, `assumptions`, `premortem`, `first_principles`, `inversion`, `steelman`, `second_order`, `tradeoffs`) + 2 net-new (`red_team`, `socratic`) + 1 composite (`apply_full_review`)
- **1 walkable skill**: `critical-thinking-pass` (5-phase: decompose → surface-assumptions → premortem → steelman-and-inversion → synthesize, hard elicit at synthesize)
- **Ontology**: 2 nodes (ThinkingMethod, ThinkingFinding) + ThinkingFinding.severity enum + ANALYZES edge + 2 schemas (thinking-analysis, thinking-finding)
- **Method shape**: all transforms returning `{method, subject, steps, output_schema}` — scaffolds the agent fills out. Subject defaults to the serving intent\047s deliverable (Spec 091 pattern preserved)
- **`red_team` distinct from `steelman`**: steelman finds the strongest argument AGAINST a position; red_team finds the strongest path to system failure. Documented + tested
- **14 tests** covering surface invariants + each method\047s scaffold shape + composite artefact production + walkable skill walk + enum bites
- **Block-mode lint clean**: 0 violations
- **Skill name**: `critical-thinking-pass` (renamed from spec\047s `critical-thinking` to avoid collision with the existing `intent` capability\047s skill of the same name; Spec 111 migration will reconcile)

### Still to implement (Slice 2)
- **4 remaining methods**: `pre_commitment`, `bayesian_update`, `if_then_else`, `analogy_map`
- **2 more composites**: `apply_decision_discipline` (tradeoffs + premortem + red_team + pre_commitment), `apply_design_review` (all 14 methods on a spec/design doc)
- **2 more walkable skills**: `red-team-pass`, `decision-discipline`
- **7 templates**: decompose, tradeoff-matrix, premortem, bayesian-update, analogy-map, red-team-checklist, pre-commitment-bind
- **Intent capability migration (Spec 111)**: the 8 founding methods on `intent.py` become thin wrappers that delegate to `thinking.*`. Backward-compat preserved for callers of `intent.decompose` etc.

### Evidence
- code: `agency/capabilities/thinking/{__init__,_main}.py`
- tests: `tests/test_thinking_capability.py` (14 tests Green); full suite Green: 1204 passed
- lint: `plugin.lint_capability(\047thinking\047)` → ok=True block-mode, 0 violations
- branch: `claude/spec-109-prompt-capability` (bundled)

(Populated when the PR ships.)
