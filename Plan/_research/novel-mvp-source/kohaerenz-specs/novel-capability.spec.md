# Specification — The `novel` Capability for the Agency Plugin

> Formal, normative specification for the novel-writing capability that powers the
> **Kohärenz Protokoll** repository. Derived from the five-slice decomposition
> (`Legacy/` corpus → `kohaerenz-protokoll-novel-writing-incubator/` slices 01–05
> → `SYNTHESIS.md`). Working language is English; the novel's canon prose is
> German and MUST NOT be translated by any tool or agent.

---

## Spec-N: The `novel` Capability

### §0. Status & Provenance

- **Status:** `Draft`
- **Last Review Date:** 2026-05-31
- **Primary Sources:** the five Jules slice analyses (PRs #137, #138, #140, #141,
  #142 against `netzkontrast/agency-backups`); their reconciliation in
  `SYNTHESIS.md`; the Agency plugin contract (`PLUGIN-CONCEPTS.md`); the vendored
  Dramatica ontology and NCP schema in the `Legacy/` corpus. Specific citations in §9.

### §1. Normative Conventions

> The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, NOT RECOMMENDED, MAY, and OPTIONAL in every produced Spec are to be interpreted as described in BCP 14 when, and only when, they appear in all capitals, as shown here.

### §2. System-Level Prompt Conventions

- **N.2.1** — The `novel` capability MUST register with the engine through the
  `extra_capabilities` extension point and MUST NOT modify the engine core,
  ontology core, or memory core.
- **N.2.2** — The capability MUST contribute its domain vocabulary as a single
  `OntologyExtension` using widen-only enums and a closed edge set.
- **N.2.3** — Every verb the capability exposes MUST declare exactly one role tag
  from the set `{transform, act, effect}`.
- **N.2.4** — The bi-temporal graph MUST be the canonical store for all
  structured, queryable narrative state; on-disk files MUST be treated as rendered
  views, except the human-authored canon-prose exception defined in N.5.5.
- **N.2.5** — A `transform` verb MUST NOT write to the graph or the filesystem; an
  `effect` verb MUST be the only verb kind that writes to the filesystem.
- **N.2.6** — The capability MUST NOT translate German canon prose into any other
  language.

### §3. Aspect 1 — Explore (Lookup & Context)

#### §3.1 Normative Statements

- **N.3.1** — Dramatica ontology lookups (dynamic pair, quad, hierarchy) MUST be
  exposed as a `transform` verb (`dramatica_lookup`).
- **N.3.2** — The capability MUST seed its Dramatica vocabulary from the vendored
  ontology file and MUST ship a checksum sidecar (`.sha`) alongside it.
- **N.3.3** — A consumer querying narrative state SHOULD read it from the graph
  via a `transform` verb rather than parsing a rendered file on disk.
- **N.3.4** — The capability MUST NOT load the full ontology file into a
  non-narrative context; lookups MUST go through the lookup verb.

#### §3.2 Acceptance Criteria (Gherkin)

```gherkin
# anchor: N.3.1
Feature: Dramatica lookup is a pure transform
  Scenario: An agent queries the dynamic pair of an element
    Given the novel capability is registered with a seeded Dramatica ontology
    When the agent calls the dramatica_lookup verb for the element "Logic"
    Then the verb returns the element's dynamic-pair partner
    And no node or edge is written to the graph
    And no file is written to disk
```

```gherkin
# anchor: N.3.2
Feature: Vendored ontology carries a checksum sidecar
  Scenario: The capability initialises its ontology seed
    Given the vendored ontology file ships with the capability
    When the capability loads the ontology at registration
    Then a .sha sidecar for the ontology file is present
    And the loaded entry count matches the count measured from the file
```

#### §3.3 Rationale

Slice 01 measured the bundled ontology at **303 entries** (4 class, 16 type, 62
variation, 63 element, 65 dynamic-pair) and recommended a `.sha` sidecar as a
drift guard so `execute` chains can trust the theory graph version. The lookup is
a textbook `transform`: deterministic, side-effect-free. N.3.4 mirrors the
existing narrative-ontology load discipline in the source corpus (the `dramatica-nav`
tool is the sanctioned access path; direct bulk loads are a known anti-pattern).

### §4. Aspect 2 — Plan / Develop Spec (Storyform & NCP State)

#### §4.1 Normative Statements

- **N.4.1** — Each discrete storyform choice MUST be committed as an `act` verb
  that writes one node or edge to the graph with provenance
  (`storyform_commit_choice`).
- **N.4.2** — Structural validity of the committed storyform MUST be checkable by
  a decidable `transform` verb implementing Hard Rules H1–H12
  (`validate_storyform`).
- **N.4.3** — NCP document validity MUST be checkable by a `transform` verb
  (`ncp_validate`) that validates against the draft-07 schema and the vendored
  canonical vocabulary, and that MUST NOT perform Dramatica meaning/coherence
  judgement.
- **N.4.4** — Each NCP decision MUST be recorded as an `act` node; the on-disk
  `ncp.json` MUST be produced only by an `effect` render verb.
- **N.4.5** — The capability SHOULD expose storyform choices through a
  progressive-disclosure Lifecycle rather than requiring the entire storyform to
  be populated in one call.

#### §4.2 Acceptance Criteria (Gherkin)

```gherkin
# anchor: N.4.3
Feature: NCP validation is structural only
  Scenario: An agent validates an NCP document
    Given an ncp.json document declaring schema_version "1.3.0"
    When the agent calls ncp_validate on the document
    Then the verb validates the document against the draft-07 schema
    And the verb validates enum fields against the vendored canonical vocabulary
    And the verb returns a pass-or-fail report with structural violations
    And the verb does not assert any Dramatica theory judgement
```

```gherkin
# anchor: N.4.2
Feature: Storyform Hard Rules are decidable
  Scenario: A committed storyform violates a Hard Rule
    Given a storyform subgraph where two characters carry both elements of one pair
    When the agent calls validate_storyform
    Then the verb reports a FAIL finding for Hard Rule H9
    And the verb does not mutate the storyform subgraph
```

#### §4.3 Rationale

Slices 01 and 02 agreed the storyform is a graph subgraph and NCP is a projection
of graph decisions. Slice 02 measured the schema as draft-07, top-level
`{schema_version, story}`, version `1.3.0`, with **463 canonical appreciations**
and **144 narrative functions** as vendored enums. The MUST-NOT in N.4.3 keeps
schema-validation (`transform`, decidable) cleanly separated from theory judgement
(deferred skill, §6). N.4.5 reflects slice 01's friction finding: Dramatica's
top-down web must be revealed step-by-step to fit the plugin's progressive-disclosure
Lifecycle.

### §5. Aspect 3 — Implement / Execute (Orchestration & Scaffold)

#### §5.1 Normative Statements

- **N.5.1** — The novel-writing workflow MUST be expressed as one gated Lifecycle
  skill (`orchestrate-novel`) whose states correspond to the authoring phases.
- **N.5.2** — Each phase boundary that requires human approval MUST be a
  `gate:"hard"` that records `BLOCKED_ON` with an `input-required` state until the
  decision is supplied.
- **N.5.3** — Workspace initialisation MUST be an `effect` verb
  (`scaffold_novel_workspace`) that renders the on-disk layout from graph state.
- **N.5.4** — The author, genre, and slug MUST be committed to the graph as `act`
  verbs before `scaffold_novel_workspace` renders them; the scaffolded directories
  MUST NOT be treated as the canonical source of those values.
- **N.5.5** — Human-authored canon prose (chapter and scene drafts, and the
  narrative body of the world bible) MUST be treated as disk-canonical and MUST NOT
  be overwritten by any `effect` render verb.
- **N.5.6** — The work slug MUST be kebab-case, ASCII, and at most 64 characters.

#### §5.2 Acceptance Criteria (Gherkin)

```gherkin
# anchor: N.5.3
Feature: Scaffold renders the workspace from graph state
  Scenario: An author initialises the Kohärenz Protokoll workspace
    Given the author "netzkontrast", genre "hard-sf", and slug "kohaerenz-protokoll" are committed as graph nodes
    When the agent calls scaffold_novel_workspace
    Then the directory novels/netzkontrast/works/hard-sf/kohaerenz-protokoll/ is rendered
    And its seven root files and seven subfolders are created
    And the canonical author, genre, and slug remain the graph nodes
```

```gherkin
# anchor: N.5.5
Feature: Canon prose is protected from re-render
  Scenario: A render runs after a human has written a chapter
    Given a human-authored German chapter exists under chapters/
    When any effect render verb runs over the workspace
    Then the chapter file content is left unchanged
```

#### §5.3 Rationale

Slice 03 specified `orchestrate-novel` as the spine, mapping the legacy 8 phases
to Lifecycle states with hard gates at Intent / Architecture / Character /
Research / Scene boundaries, and proposed `scaffold_novel_workspace` to replace
the hard-coded `/home/claude/novel-projects/<slug>/` setup. N.5.4 enforces the
graph-canonical rule even at scaffold time: the directory is a render, not a
record. N.5.5 is the single documented disk-canonical exception that all
prose-touching slices (02, 03, 04) independently named — the analogue of the
plugin's own canon-docs carve-out.

### §6. Aspect 4 — Review (Coherence Classification)

#### §6.1 Normative Statements

- **N.6.1** — The capability MUST expose a `coherence_check` `transform` verb that
  implements only the decidable subset of checks and emits a PASS/FAIL report
  without mutating the graph.
- **N.6.2** — The decidable subset MUST include Hard Rules H1–H12, worksheet-order
  constraints, canon-status referential integrity, and Q1–Q5 presence/completeness.
- **N.6.3** — Checks requiring semantic or draft-level judgement (e.g. whether
  prose serves a theme, AP-1/AP-4/AP-6/AP-8/AP-9) MUST NOT be implemented as a
  `transform` and MUST be deferred to a judgement skill that records its outcome
  back to the graph.
- **N.6.4** — The user MUST NOT treat a passing `coherence_check` as evidence of
  narrative quality; it certifies structural decidable validity only.

#### §6.2 Acceptance Criteria (Gherkin)

```gherkin
# anchor: N.6.2
Feature: Coherence check covers the decidable subset
  Scenario: A scene moment is missing a required storyform slot
    Given a Moment node whose theme_anchor_ref slot is empty
    When the agent calls coherence_check over the scene matrix
    Then the verb reports a FAIL finding for the Q5 presence check
    And the verb does not attempt to judge whether the prose serves the theme
```

```gherkin
# anchor: N.6.3
Feature: Judgement checks are not faked as linters
  Scenario: An agent requests an anti-pattern audit that needs draft analysis
    Given a request to evaluate anti-pattern AP-6 (draft diverges from MC Resolve)
    When the workflow routes the request
    Then the request is handled by a judgement skill, not coherence_check
    And the skill's outcome is recorded to the graph as provenance
```

#### §6.3 Rationale

Slice 05 classified every check in the source corpus with per-rule citations:
H1–H12, worksheet-order, and canon-status are mechanically decidable; Q1–Q5 are
decidable for *presence* but their semantic alignment is judgement; several
anti-patterns (AP-1, AP-4, AP-6, AP-8, AP-9) require reading the draft. N.6.3
encodes the brief's "decidable-subset honesty" requirement — a linter that
pretends to judge meaning is the failure mode being prohibited. N.6.4 protects the
user's epistemics: structural pass ≠ good novel.

### §7. Aspect 5 — Validate / Verify (Pre-Drafting Gate & Render)

#### §7.1 Normative Statements

- **N.7.1** — Entry into the drafting phase for a target scene or chapter MUST be
  guarded by a `pre_drafting` gate that evaluates `coherence_check` on the target's
  Q1–Q5 slots.
- **N.7.2** — The `pre_drafting` gate MUST record `PASSED` only when all required
  storyform slots for the target are present and coherent; otherwise it MUST record
  `BLOCKED_ON` with `input-required`.
- **N.7.3** — Rendered status views and outlines MUST be produced by invoking the
  underlying `transform` live (or its cached graph result) and MUST NOT depend on a
  stale on-disk artefact written by an earlier linter run.
- **N.7.4** — A hand-edit to a rendered file (e.g. `ncp.json`) SHOULD be
  reconciled back into the graph as `act` operations so the file remains a
  projection rather than a divergent source of truth.

#### §7.2 Acceptance Criteria (Gherkin)

```gherkin
# anchor: N.7.2
Feature: Pre-drafting gate blocks on incomplete storyform
  Scenario: An agent attempts to draft a scene with a missing slot
    Given a target Moment whose dominant_throughline slot is unset
    When the agent requests entry into the drafting phase for that Moment
    Then the pre_drafting gate records BLOCKED_ON
    And the gate sets an input-required state to elicit the missing slot
```

```gherkin
# anchor: N.7.3
Feature: Status views render from live graph state
  Scenario: A status view is requested after a storyform change
    Given a storyform choice was just committed via an act verb
    When the agent requests the architecture status view
    Then the render effect invokes coherence_check live against the graph
    And the rendered view reflects the latest committed choice
    And the render does not read a stale .architecture-validation.json file
```

#### §7.3 Rationale

Slice 05 identified the `pre_drafting` gate (Phase 6) as the verification
checkpoint and surfaced the graph-vs-disk tension in the render path: the legacy
`render_architecture.py` (Task 087) consumes a flat JSON written to disk and
checks mtimes for staleness. N.7.3 resolves it in the plugin model — the render
queries the graph (or a cached transform result), eliminating the stale-artefact
class of bug. N.7.4 is slice 02's `ncp-io` reconciliation, kept SHOULD because the
bidirectional parser is v2 scope (§8).

### §8. Known Limitations & Open Questions

- This spec governs the capability's contract and verb roles; it does not specify
  the internal algorithm of any verb beyond its role tag and decidability class.
- The judgement coherence-skills (N.6.3) are named but not specified here; their
  prompts and acceptance criteria are deferred to a future Spec-N revision or a
  companion skill spec.
- The bidirectional `ncp-io` reconciliation (N.7.4) is v2 scope; until it ships,
  hand-edits to `ncp.json` can diverge from the graph and MUST be re-rendered
  rather than trusted.
- Verb names are indicative; the exact wire names (`capability_novel_<verb>`) are
  fixed at implementation time and may be refined, provided role tags are preserved.
- The measured counts (303 ontology entries; 463 appreciations; 144 narrative
  functions) are asserted from the bundled data at the cited SHA; an implementation
  MUST re-measure at test time rather than hard-code these numbers.
- This spec does not constrain the German canon prose itself — only the tooling
  around it.

### §9. Source Index

1. Slice 01 — Dramatica engine decomposition (`01-dramatica-engine/{CONCEPTS,COHERENCE,PROPOSAL}.md`), PR #137.
2. Slice 02 — NCP protocol decomposition (`02-ncp-protocol/…`), PR #138.
3. Slice 03 — Novel-architect orchestration (`03-novel-architect-orchestration/…`), PR #140.
4. Slice 04 — Character & World (`04-character-and-world/…`), PR #141.
5. Slice 05 — Structure, Scene & Coherence (`05-structure-scene-coherence/…`), PR #142.
6. `SYNTHESIS.md` — reconciliation of slices 01–05 into the unified `novel` capability.
7. `PLUGIN-CONCEPTS.md` — the Agency plugin contract (four concepts, wire contract, role tags, OntologyExtension, gates/skills).
8. `Legacy/maintenance/schemas/narrative-ontology/ontology.json` — vendored Dramatica ontology (303 entries).
9. `Legacy/skills/ncp-author/upstream/schema/ncp-schema.json` — NCP draft-07 schema v1.3.0 (463 appreciations, 144 narrative_functions).
10. `Legacy/` tasks 073/074/075/084/085/086/087 — Hard Rules, anti-patterns, scene-level bridge, linters, render wiring (decidability citations for §6).
