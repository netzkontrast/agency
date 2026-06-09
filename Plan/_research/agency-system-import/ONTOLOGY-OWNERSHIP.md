# Ontology Ownership — Specs 109, 110, 112, 114

> Iter-15 panel fix (consensus issue A1). Single source-of-truth for
> every node type declared across the new substrate-adjacent
> capabilities. **Each node has exactly ONE owning capability**; other
> capabilities reference it via the owner's OntologyExtension.

## Ownership table

| Node | Owned by | Defined in | Read by | Why |
|---|---|---|---|---|
| **ResearchIntent** | `dossier` (112) | `dossier_ontology` | `prompt` (109 references for `intent_capture` source), `research` (consumes) | Dossier is the lifecycle owner; intent capture is the dossier's Phase-0 |
| **ResearchBrief** | `dossier` (112) | `dossier_ontology` | `prompt` (rendering), `research` (consumes for query) | Brief IS the dossier's output artefact |
| **BriefAudit** | `dossier` (112) | `dossier_ontology` | `prompt` (109's `audit` verb generalizes the read pattern) | Brief audit operates on Brief; same cap |
| **ResearchSource** | `dossier` (112) | `dossier_ontology` | `research` (specialist citations link here) | Corpus is the dossier's domain |
| **ResearchChunk** | `dossier` (112) | `dossier_ontology` | — | Sub-node of Source; same owner |
| **ResearchEntity** | `dossier` (112) | `dossier_ontology` | `prompt` (consumes for snippet bundling), `thinking` (consumes for evidence in `bayesian_update`) | Entity is the dossier's extracted unit |
| **EntityTag** | `dossier` (112) | `dossier_ontology` | — | Belongs to entity; same owner |
| **EntityRelation** | `dossier` (112) | `dossier_ontology` | `thinking` (consumes for `analogy_map`) | Cross-entity relations live with the corpus |
| **Context** | `dossier` (112) | `dossier_ontology` | `prompt` (consumes for snippet bundling) | Context mapping is the dossier's Phase-3 |
| **PromptSnippet** | `dossier` (112) | `dossier_ontology` | `prompt` (consumes via `engineer`) | Snippet is the dossier's output; prompt consumes |
| **CatalogModule** | `dossier` (112) | `dossier_ontology` | `prompt` (109's `catalog_list` references same source) | Catalog seeds both briefs AND prompts; dossier owns the data |
| **PromptTemplate** | `prompt` (109) | `prompt_ontology` | — | Prompt-engineering authored templates |
| **PromptInstance** | `prompt` (109) | `prompt_ontology` | `thinking` (consumes as input for `red_team` of a prompt) | Engineering pass output |
| **PromptOutput** | `prompt` (109) | `prompt_ontology` | — | LLM response + score; same owner |
| **PromptVariant** | `prompt` (109) | `prompt_ontology` | — | A/B variant of an instance; same owner |
| **AntiPattern** | `prompt` (109) | `prompt_ontology` | — | Anti-pattern library for prompt-engineering |
| **OptimizationPass** | `prompt` (109) | `prompt_ontology` | — | Engineering-pass metric record |
| **Builder** | `prompt` (109) | `prompt_ontology` | — | 10-builder family registration |
| **PromptFramework** | `prompt` (109) | `prompt_ontology` | — | 18-framework catalog |
| **FrameworkWalk** | `prompt` (109) | `prompt_ontology` | — | Walker state per framework instance |
| **FrameworkChoice** | `prompt` (109) | `prompt_ontology` | — | Recommendation history |
| **DossierWorkflow** | `dossier` (112) | `dossier_ontology` | `prompt` (composes with via lifecycle handoff) | The dossier-side Lifecycle wrapper |
| **DecomposeFinding** | `thinking` (110) | `thinking_ontology` | `develop` (consumes for spec authoring) | Atomic thinking-method output |
| **Assumption** | `thinking` (110) | `thinking_ontology` | `develop` (consumes), `dogfood` (consumes) | Atomic |
| **PremortemFinding** | `thinking` (110) | `thinking_ontology` | `develop`, `dogfood` | Atomic |
| **FirstPrincipleFinding** | `thinking` (110) | `thinking_ontology` | `develop` | Atomic |
| **InversionFinding** | `thinking` (110) | `thinking_ontology` | `develop` | Atomic |
| **Steelman** | `thinking` (110) | `thinking_ontology` | `develop`, `dossier` | Atomic |
| **ConsequenceChain** | `thinking` (110) | `thinking_ontology` | `develop`, `delegate` | Atomic |
| **Tradeoff** | `thinking` (110) | `thinking_ontology` | `develop`, `delegate`, `analyze` | Atomic |
| **RedTeamFinding** | `thinking` (110) | `thinking_ontology` | `dossier` (`audit` consumes), `develop` | Atomic |
| **SocraticChain** | `thinking` (110) | `thinking_ontology` | `develop`, `develop.brainstorm` | Atomic |
| **PreCommitment** | `thinking` (110) | `thinking_ontology` | `gate` (consumed by gate.check predicates) | Atomic |
| **IfThenElseTree** | `thinking` (110) | `thinking_ontology` | `delegate`, `develop` | Atomic |
| **BayesianBelief** | `thinking` (110) | `thinking_ontology` | `dossier` (evidence link), `develop` | Atomic |
| **Evidence** | `thinking` (110) | `thinking_ontology` | — | Sub-node of BayesianBelief |
| **AnalogyMap** | `thinking` (110) | `thinking_ontology` | `develop`, `dossier` | Atomic |
| **ThoughtChain** | `thinking` (110) | `thinking_ontology` | `develop` (skill walker reads), `dogfood` | Composite |
| **CriticalAnalysisArtefact** | `thinking` (110) | `thinking_ontology` | `develop`, `dogfood`, `reflect` | Composite |
| **DecisionRecord** | `dogfood` (114 — moved here) | `dogfood_ontology` | `gate`, `thinking` | Decision-record discipline already in dogfood (Spec 017) |
| **DesignReviewArtefact** | `thinking` (110) | `thinking_ontology` | `develop`, `dogfood`, `reflect` | Composite |
| **SessionLifecycle** | `develop` (114) | `develop_ontology` | All caps (provenance container) | Sessions are develop's territory |
| **ModeShift** | `develop` (114) | `develop_ontology` | `dogfood` (lessons signal) | Sub-node of SessionLifecycle |
| **BoundaryUse** | `dogfood` (114) | `dogfood_ontology` | `develop` (consumes for skill suggestions) | Boundary-use tracking is observation territory |
| **SessionReflection** | `reflect` (114) | `reflect_ontology` | `develop`, `dogfood` | Session synthesis IS reflection territory |

## Edge ownership

Edges have the SAME ownership rule — declared on ONE side, traversable
from both:

| Edge | Owned by | Connects |
|---|---|---|
| `RENDERS_FROM` | `dossier` | `ResearchBrief` → `ResearchIntent` |
| `AUDITS_BRIEF` | `dossier` | `BriefAudit` → `ResearchBrief` |
| `EXTRACTED_FROM` | `dossier` | `ResearchEntity` → `ResearchChunk` |
| `TAGGED_AS` | `dossier` | `ResearchEntity` → `EntityTag` |
| `RELATES_TO_ENTITY` | `dossier` | `EntityRelation` source → target |
| `CONTEXTUALIZES` | `dossier` | `Context` → `ResearchEntity` |
| `BUNDLES` | `dossier` | `PromptSnippet` → `ResearchEntity` |
| `DERIVED_FROM_MODULE` | `dossier` | `ResearchBrief` → `CatalogModule` |
| `COMPOSED_BY` | `prompt` | `PromptInstance` → `Builder` |
| `BUNDLES_TEMPLATE` | `prompt` | `PromptInstance` → `PromptTemplate` |
| `VARIANT_OF` | `prompt` | `PromptVariant` → `PromptInstance` |
| `PRODUCED_BY` | `prompt` | `PromptOutput` → `PromptInstance` |
| `FLAGS_ANTI` | `prompt` | `PromptOutput` → `AntiPattern` |
| `APPLIES_PASS` | `prompt` | `PromptInstance` → `OptimizationPass` |
| `DEPENDS_ON_FINDING` | `thinking` | Composite → atomic finding |
| `REFUTES` | `thinking` | Later artefact → prior Assumption |
| `REINFORCES` | `thinking` | Later artefact → prior |
| `CHANGED_BY` | `thinking` | `PreCommitment` lineage |
| `DERIVED_FROM` | `thinking` | `BayesianBelief` evidence ref |

## How to read this table

- A node-row tells implementers: **`<capability>` owns the schema; other
  caps read but never declare**.
- If a future spec needs to add a field to a node, it goes through the
  owning capability's OntologyExtension — not via a parallel declaration.
- Edges follow the same rule — declared on the source-cap side.

## Validation

Every cap's `OntologyExtension` MUST declare ONLY the nodes listed in
its row above. A drift-check script (`scripts/check-ontology-ownership`)
parses each cap's ontology.py and asserts:

- No node label appears in more than one cap's `nodes={}` dict.
- No edge type appears in more than one cap's `edges=set()`.
- Cross-cap reads use `ctx.recall_typed(id, label)` (Spec 056 pattern),
  which validates the label belongs to the right cap.

CI runs this check on every PR that touches a new-cap's ontology.
