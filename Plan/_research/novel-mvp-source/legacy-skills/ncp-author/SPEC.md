# Narrative Context Protocol — Specification for AI-Agent-Driven Novel Co-Authoring

> **Status in this skill:** This is the *target specification* — Michael's normative SPEC produced via `research-prompt-optimizer` v2.1.0 and the `spec-skill` workflow. The current `ncp-author` skill is **work-in-progress** and does NOT yet implement the full hexagonal architecture described below. See `TODO.md` for the implementation plan and `SKILL.md` for the current scope. Reference both `references/related-skills.md` and `upstream/SPECIFICATION.md` (the open-source NCP spec) when reasoning about gaps between this SPEC and current behavior.

## Document Metadata
- **Version:** 1.0
- **Date:** 2026-05-02
- **Repo SHA Pinned:** `0b9ab1223d3822a49eddc139bcdf2669aa067734`
- **Source Skill:** research-prompt-optimizer v2.1.0
- **Conformance Level:** High (RFC 2119 / BCP 14)
- **Audience:** Senior Software Architect / AI Systems Developer / Autonomous AI Agent (Claude Code / Gemini Jules)

---

## §1 Conformance Language

### §1.1 RFC 2119 / BCP 14 normative keywords
The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.

### §1.2 Gherkin syntax binding
Every behavioural example, agent-interaction scenario, or hand-off specification in this document MUST use standard Gherkin syntax (Feature, Scenario, Given, When, Then, And, But) and MUST be self-contained and executable.

### §1.3 Style Guide for normative statements
1. Normative statements MUST use exactly one RFC 2119 keyword.
2. Acceptance criteria MUST be written as Gherkin scenarios.
3. Rationales and descriptions MUST NOT contain normative keywords in uppercase.
4. Inline citations MUST use the form `path/to/file.ext:Lstart-Lend@<sha>`.

---

## §2 Glossary

- **Story**
  - *NCP Context:* The root JSON object representing the entire narrative, including `ideation`, `subtext`, and `storytelling`.
  - *Dramatica Context:* The overarching narrative argument formed by the Story Mind.
- **Scene**
  - *Novel Craft Context:* A unit of prose action happening in one time and place.
  - *NCP Context:* Mapped as `storytelling.moments[]` containing one or more `storybeats`.
- **Beat / Storybeat**
  - *NCP Context:* A structural step in the `subtext` layer with a scope (`signpost`, `progression`, `event`).
  - *Dramatica Context:* A specific progression within a throughline.
- **Throughline**
  - *Dramatica Context:* One of four perspectives (Objective Story, Main Character, Influence Character, Relationship Story).
  - *NCP Context:* A string field within `perspectives` or `storybeats` used for grouping.
- **Skill**
  - *Agentic Context:* A `SKILL.md` file granting specialized capability to an AI agent.
- **Workflow / Phase**
  - *SDD Context:* One of the eight sequential steps of novel co-authoring defined in this specification.
- **Context / Protocol**
  - *NCP Context:* The serialized JSON schema (`ncp-schema.json`) holding authorial intent.

---

## §3 Scope and Non-Goals

### §3.1 In scope
The workflow MUST cover the following eight phases of novel co-authoring:
1. Premise & Concept
2. Dramatica Storyform
3. Outline & Plot Structure
4. Character Work & Relationships
5. Worldbuilding & Wiki Build-up
6. Scene Drafting (Prose)
7. Revision & Consistency Checks
8. Editing & Final Polish

### §3.2 Non-goals
This specification MUST NOT define rules for style, voice, or tone generation. It MUST NOT include auto-publishing pipelines. It MUST NOT include proprietary Dramatica software output (UI/exports).

---

## §4 Architectural Decision: NCP ↔ Dramatica Relationship

### §4.1 Option A — Parallel Layers
NCP maintains pure intent; Dramatica acts as an external structural engine. Requires bidirectional syncing via cross-cutting skills.

### §4.2 Option B — Dramatica-In-NCP
Dramatica concepts are modelled as first-class NCP entities natively using the `storypoints`, `perspectives`, and `storybeats` arrays.

### §4.3 Option C — NCP-In-Dramatica
Dramatica leads the data model, and NCP acts merely as a file format export layer.

### §4.4 Trade-off matrix
| Axis | Option A | Option B | Option C |
| --- | --- | --- | --- |
| Extension Cost | High | Low | Medium |
| Agent Ergonomics | Medium | High | Low |
| Fidelity to Canon | High | High | High |
| Evolvability | High | Medium | Low |

### §4.5 Recommendation
The system MUST implement **Option B — Dramatica-In-NCP**. The NCP schema inherently utilizes Dramatica terminology (e.g., `appreciation`, `throughline`, `dynamics`). Implementing Dramatica directly within the NCP data model reduces agent context-switching and leverages the existing `ncp-schema.json`.

### §4.6 Pre-commitment
I would reverse this recommendation if I found that NCP lacks fields for dynamically resolving Quads or parallel constraints that require an external inference engine.

---

## §5 NCP Data Model

### §5.1 Entity inventory
- **Story**: Root container (`schema/ncp-schema.json:L8-L16@0b9ab1223d3822a49eddc139bcdf2669aa067734`).
- **Ideation**: Pre-narrative elements (`schema/ncp-schema.json:L18-L23@0b9ab1223d3822a49eddc139bcdf2669aa067734`).
- **Narratives**: Array of candidate structures (`schema/ncp-schema.json:L30-L100@0b9ab1223d3822a49eddc139bcdf2669aa067734`).
- **Subtext**: Contains `perspectives`, `players`, `dynamics`, `storypoints`, `storybeats`.
- **Storytelling**: Contains `overviews` and `moments`.

### §5.2 Relationships and cardinalities
A `Story` HAS ONE `ideation` and HAS MANY `narratives`. A `narrative` HAS ONE `subtext` and HAS ONE `storytelling`. `Moments` map to `storybeats` via `storybeat_id`.

### §5.3 State machines
The state is managed by `narratives[].status`, which MUST be `candidate`, `draft`, or `complete`.

### §5.4 Entry points
File format contract: JSON document conforming to `ncp-schema.json`.

### §5.5 Integration surfaces for Dramatica
`subtext.storypoints` and `subtext.dynamics` host the Storyform. `subtext.perspectives` host the Four Throughlines.

### §5.6 Gaps requiring Dramatica-side extension
NCP does not explicitly model generic novel "Chapters". This MUST be compensated for by using `storytelling.overviews` with custom labels.

---

## §6 Dramatica Canon

### §6.1 Story Mind and the four Throughlines
The Story Mind represents a single human mind solving a problem. The four Throughlines are Objective Story, Main Character, Influence Character, and Relationship Story [^1].

### §6.2 Domain / Concern / Issue / Problem
The structural hierarchy nesting from broad Domain (Universe, Physics, Psychology, Mind) down to the specific Element (Problem/Solution) [^2].

### §6.3 Quads
The recursive matrix of Knowledge, Thought, Ability, and Desire (KTAD) defining relationships at every level [^3].

### §6.4 Dynamics
Key drivers of the narrative including Story Driver, Story Limit, Story Outcome, and Story Judgment.

### §6.5 Authoring phases
Concept -> Storyform -> Storyweaving -> Storytelling.

---

## §7 Workflow Architecture

### §7.1 Candidate patterns
1. **Pipeline**: Strict sequential agent runs.
2. **DAG**: Directed Acyclic Graph orchestration based on artifact dependency.
3. **Autonomous hand-off via NCP-state**: Agents poll `status` and trigger sub-skills autonomously.

### §7.2 Trade-off matrix
| Axis | Pipeline | DAG | Autonomous Hand-off |
| --- | --- | --- | --- |
| Agent Autonomy | Low | Medium | High |
| Error Recovery | Low | High | Medium |
| State Complexity | Low | Medium | High |

### §7.3 Recommendation
The system MUST implement **Autonomous hand-off via NCP-state** combined with cross-cutting validation skills.

### §7.4 Pre-commitment
I would reverse this recommendation if I found that Claude Code cannot natively trigger on file-watcher events without a DAG orchestrator.

### §7.5 Workflow diagram
```text
[Premise] -> [Storyform] -> [Outline] -> [Character] -> [Worldbuild] -> [Draft] -> [Revise] -> [Edit]
   v            v             v              v               v             v           v          v
   +----------------------- Updates NCP JSON `status` and arrays ---------------------------------+
```

### §7.6 NCP state-machine read/write conventions per phase
Agents MUST read the entire JSON file, update their specific scope (e.g., Phase 2 updates `subtext.storypoints`), and increment `status` to `complete` when all validations pass.

### §7.7 Hand-off Gherkin scenarios per phase boundary

```gherkin
Feature: Phase 2 to Phase 3 Handoff
  Scenario: Agent detects completed storyform and begins outlining
    Given the NCP document "story.json" has "status" set to "complete" for Phase 2
    And "subtext.storybeats" contains exactly 16 progressions
    When the router skill "outline-router" is invoked
    Then the agent MUST generate "storytelling.moments"
    And the agent MUST set Phase 3 status to "draft"
```

---

## §8 Skill Catalog

### §8.1 Catalog conventions
Skills MUST use the Hexagonal pattern. Main `SKILL.md` acts as a router, calling sub-skills via prompt/CLI injection.

### §8.2 Phase 1 — Premise & Concept
#### §8.2.1 Phase router skill
`skills/premise-router/SKILL.md`
#### §8.2.2 Sub-skills
- `premise-ideation`: Triggers on `/ideate`. Updates `ideation` layer.
- `premise-logline`: Triggers on `/logline`. Updates `story.logline`.

### §8.3 Phase 2 — Dramatica Storyform
#### §8.3.1 Phase router skill
`skills/storyform-router/SKILL.md`
#### §8.3.2 Sub-skills
- `storyform-dynamics`: Triggers on `/dynamics`. Establishes Story Driver/Outcome.
- `storyform-throughlines`: Triggers on `/throughlines`.

### §8.4 Phase 3 — Outline & Plot Structure
#### §8.4.1 Phase router skill
`skills/outline-router/SKILL.md`
#### §8.4.2 Sub-skills
- `outline-beats`: Triggers on `/plot`. Populates `storybeats`.

### §8.5 Phase 4 — Character Work & Relationships
#### §8.5.1 Phase router skill
`skills/character-router/SKILL.md`
#### §8.5.2 Sub-skills
- `character-players`: Triggers on `/cast`. Updates `subtext.players`.

### §8.6 Phase 5 — Worldbuilding & Wiki Build-up
#### §8.6.1 Phase router skill
`skills/worldbuild-router/SKILL.md`
#### §8.6.2 Sub-skills
- `worldbuild-settings`: Triggers on `/world`. Updates `storytelling.overviews`.

### §8.7 Phase 6 — Scene Drafting (Prose)
#### §8.7.1 Phase router skill
`skills/draft-router/SKILL.md`
#### §8.7.2 Sub-skills
- `draft-scene`: Triggers on `/draft`. Generates prose based on `moments`.
- `draft-dialogue`: Triggers on `/dialogue`.

### §8.8 Phase 7 — Revision & Consistency Checks
#### §8.8.1 Phase router skill
`skills/revision-router/SKILL.md`
#### §8.8.2 Sub-skills
- `revise-consistency`: Triggers on `/check`. Checks prose against `subtext`.

### §8.9 Phase 8 — Editing & Final Polish
#### §8.9.1 Phase router skill
`skills/edit-router/SKILL.md`
#### §8.9.2 Sub-skills
- `edit-copy`: Triggers on `/copyedit`.
- `edit-format`: Triggers on `/format`.

### §8.10 Cross-cutting skills
- `ncp-io`: Triggers on `/save` or `/load`. Handles valid JSON updates.
- `dramatica-validator`: Triggers on `/validate`. Ensures KTAD logic integrity.

---

## §9 Agent Targets

### §9.1 Claude Code (primary)
Claude Code loads skills automatically from the `.claude/skills/` or `skills/` directory containing `SKILL.md` files. It reads NCP state natively by parsing JSON.

### §9.2 Gemini Jules
Gemini Jules does not natively support a `skills/` directory loader [^4].
**Compensation Pattern:** For Jules, the project MUST include an `AGENT_NOTES.md` file in the root directory that acts as the router, concatenating required sub-skill instructions into the system prompt context at runtime.

### §9.3 Portability requirements

```gherkin
Feature: Agent Capability Portability
  Scenario: Jules ingests skills without a native loader
    Given the agent is "Gemini Jules"
    When the agent initializes the workspace
    Then the agent MUST read "AGENT_NOTES.md"
    And the agent MUST apply the compensation pattern rules within
```

---

## §10 Acceptance Criteria for SPEC.md Itself

### §10.1 Coverage scenarios

```gherkin
Feature: Phase Coverage
  Scenario: All 8 phases are addressable
    Given the skill catalog in §8
    When an agent audits the specification
    Then the agent MUST find exact routers for Phases 1 through 8
```

### §10.2 NCP-entity coverage scenarios

```gherkin
Feature: NCP Entity Mapping
  Scenario: All core entities map to skills
    Given the NCP schema defines "ideation", "subtext", and "storytelling"
    When the agent processes Phase 1
    Then "ideation" MUST be utilized
    And "subtext" MUST be utilized in Phase 2
    And "storytelling" MUST be utilized in Phase 6
```

### §10.3 Hexagonal-pattern scenarios

```gherkin
Feature: Skill Delegation
  Scenario: Routers do not perform heavy lifting
    Given a phase router skill is triggered
    When it requires complex logic
    Then it MUST delegate to at least 1 sub-skill
```

### §10.4 Conformance-language scenarios

```gherkin
Feature: Normative Formatting
  Scenario: RFC 2119 enforcement
    Given a normative statement in this document
    When it dictates behaviour
    Then it MUST contain exactly one uppercase RFC 2119 keyword
```

---

## §11 Validation Walkthrough

### §11.1 Worked example
**Project:** *The Silica Paradox* (Sci-Fi, 80k words, A detective investigating a rogue AI realizes they are the AI).
**Justification:** Generic, non-living-person project exercising deep internal psychology (Mind/Manipulation Domains) and robust worldbuilding.

### §11.2 Walkthrough phase-by-phase
1. **Phase 1:** `premise-router` triggered. Agent creates `ideation.plot` nodes.
2. **Phase 2:** `storyform-router` triggered. Agent defines MC Domain as `Psychology`, OS Domain as `Physics`. Saves to `subtext.perspectives`.
3. **Phase 3:** `outline-router` triggered. Generates 16 `progression` `storybeats`.
4. **Phase 4:** `character-router` triggered. Defines the Detective in `subtext.players`.
5. **Phase 5:** `worldbuild-router` triggered. Expands the cyberpunk city in `storytelling.overviews`.
6. **Phase 6:** `draft-router` triggered. Converts `storybeats` into `storytelling.moments` prose.
7. **Phase 7:** `revision-router` triggered. Audits moments against `storyform` intent.
8. **Phase 8:** `edit-router` triggered. Corrects pacing and grammar.

---

## §12 Open Questions and Deferred Decisions
- [NOT-FOUND] How are multi-agent concurrent edits merged in a single JSON file? Assume git-level merging for now.
- [NOT-FOUND] How does the system handle parallel quads beyond the basic four without a proprietary inference engine? (Pending community extension).

---

## §13 Versioning and Change-Control
This SPEC.md is version 1.0. Any changes to the normative requirements MUST increment the minor version and update the Document Metadata.

---

## §14 References
- [^1] Dramatica Theory Canonical Book (dramatica.com/theory).
- [^2] Narrative First, "The Science Behind Dramatica" (narrativefirst.com).
- [^3] Discuss Dramatica KTAD Quads Thread (discuss.dramatica.com).
- [^4] [single-source] Anthropic Agentic Skill Documentation & Tech Blogs regarding ecosystem differences.

---

## Implementation Notes (added during skill build, 2026-05-03)

After cloning the upstream repo and reading the schema (`upstream/schema/ncp-schema.json`) the following observations from the actual code/spec collide with the SPEC above and need resolution before scaling out the full hexagonal catalog:

1. **§4.6 pre-commitment is partially triggered.** The NCP schema does NOT encode Quad (KTAD) tuple structure — only `appreciation` (slot) and `narrative_function` (Element) enums. Quad inference therefore lives **outside** the JSON. This means §4.5's "Option B — Dramatica-In-NCP" is true at the *vocabulary* level but partial at the *inference* level. The `dramatica-validator` cross-cutting skill in §8.10 cannot ground all KTAD checks in NCP alone — it must consult `dramatica-vocabulary` or `dramatica-theory`. See `references/related-skills.md`.

2. **§9.2 naming collision.** The upstream repo already has an `AGENTS.md` at the root (used by Codex/Cursor). The SPEC's `AGENT_NOTES.md` proposal avoids the collision but should be called out in §9 explicitly. The upstream `AGENTS.md` is preserved in this skill as `upstream/UPSTREAM_AGENTS.md` to avoid confusion.

3. **§7.5 Phase 5 (Worldbuilding) — "no Chapter type" gap.** §5.6 notes NCP does not model Chapters; the proposed compensation via custom-labeled `overviews` works for top-of-book overviews but not for chapter-level scaffolding. Chapter scaffolding likely belongs in `storytelling.moments[].act` + `order` + an external chapter-level container. This is a real gap, not a doc gap. See `TODO.md` item T-5.

4. **§8 catalog over-decomposition.** Many proposed sub-skills (`premise-logline`, `draft-dialogue`, `edit-copy`, `edit-format`) are LLM-native and may not justify their own SKILL.md. Decision deferred — see `TODO.md` item T-1 (granularity).
