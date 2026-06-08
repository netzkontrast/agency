# Orchestration Concepts: Mapping to the Agency Plugin Model

This document maps the existing `novel-architect` orchestration state machine to the Agency plugin model primitives (Intent, Capability, Lifecycle, Memory) outlined in `PLUGIN-CONCEPTS.md`.

## Lifecycle Mapping: The 8 Phases

The novel-architect's 8 phases track the state of work in progress, cleanly mapping to the **Lifecycle** concept. Here is how each phase maps and the state it reads/writes:

1.  **Phase 0 — Bootstrap (`skills/novel-architect/phases/phase0-bootstrap.md`)**
    *   **Action:** Sets up the workspace layout.
    *   **State:** Writes initial workspace structure. Reads `project-config.yaml` to detect existing projects.
    *   **Agency Concept:** Initialization, mapped to an `effect` verb that structures the canvas.
2.  **Phase 1 — Intent Capture (`skills/novel-architect/phases/phase1-intent-capture.md`)**
    *   **Action:** Captures author constraints (genre, audience, language, etc.) until 100% clarity.
    *   **State:** Writes `intent.yaml` which defines the exact context.
    *   **Agency Concept:** Populates the **Intent** graph nodes. This sets the parameters for capability search.
3.  **Phase 2 — Narrative Architecture (`skills/novel-architect/phases/phase2-narrative-architecture.md`)**
    *   **Action:** Executes the 8-step storyform worksheet (Throughlines, Dynamics, Elements).
    *   **State:** Reads `intent.yaml`. Writes `architecture.yaml` and NCP skeletons to `canon/<slug>.ncp.json`.
    *   **Agency Concept:** A skill execution that writes dense semantic state to the Memory graph (`act` verb).
4.  **Phase 3 — Character Architecture (`skills/novel-architect/phases/phase3-character-architecture.md`)**
    *   **Action:** Defines characters, roles, models, and relationships.
    *   **State:** Reads `architecture.yaml` and `intent.yaml`. Writes `character-architecture.yaml` and updates NCP `players[]`.
    *   **Agency Concept:** Ontology extension (Characters, Psycho-Models) populated via `act` verbs.
5.  **Phase 4 — World & Research (`skills/novel-architect/phases/phase4-world-research.md`)**
    *   **Action:** Identifies research domains and generates world-building briefs.
    *   **State:** Reads `intent.yaml`. Writes `world-bible.md` and `research/briefs/<domain>.md`.
    *   **Agency Concept:** External research `effect` leading to `act` ingestion of context into the graph.
6.  **Phase 5 — Scene & Chapter Matrix (`skills/novel-architect/phases/phase5-scene-matrix.md`)**
    *   **Action:** Builds the act-to-scene hierarchy.
    *   **State:** Reads `architecture.yaml`, `character-architecture.yaml`, `world-bible.md`. Writes `scene-matrix.md` and NCP `storybeats[]`/`moments[]`.
    *   **Agency Concept:** Refinement of the narrative Intent to specific structural graph nodes.
7.  **Phase 6 — Drafting (`skills/novel-architect/phases/phase6-drafting.md`)**
    *   **Action:** Generates prose based on the structural constraints.
    *   **State:** Reads NCP context, `scene-matrix.md`, `character-architecture.yaml`, `world-bible.md`, `canon-meta.md`. Writes prose files (`drafts/ch-XX.docx`).
    *   **Agency Concept:** Generative `act` guided by strict graph constraints, producing rendered output views (`effect`).
8.  **Phase 7 — Iteration (`skills/novel-architect/phases/phase7-iteration.md`)**
    *   **Action:** Open Questions resolution, audits, and spec generation.
    *   **State:** Reads current overall state. Writes `roman-spec.md` or audit reports.
    *   **Agency Concept:** `transform` operations for checking coherence (linters) and rendering RFC-2119 specs.

## Hard Gates & Human Decisions

In the `novel-architect`, human input is explicitly required at key structural points. These map perfectly to the Agency plugin `gate:"hard"` checkpoint, transitioning the Lifecycle to a `BLOCKED_ON` + `input-required` state until human or external agent review resolves the gate.

*   **Phase 1 Gates (`phase1-intent-capture.md`):** Re-loops until all required intent slots (genre, length, core_conflict) are explicitly approved. This is an implicit gate to exit Phase 1.
*   **Phase 2 Gates (`phase2-narrative-architecture.md`):** Contains a defined 3-Gate approval loop:
    *   **Gate 1:** Approves Storyform Shape + Throughline names (Steps 0-1).
    *   **Gate 2:** Approves Classes + 8 Dynamics + Story Points (Steps 2-5).
    *   **Gate 3:** Final architecture approval before writing NCP Skeleton (Steps 6-8 + Validation).
*   **Phase 4 Gates (`phase4-world-research.md`):** Gate prior to research brief delegation (Phase 4.2), approving the research scope.
*   **Phase 5 Gates (`phase5-scene-matrix.md`):** Contains a 3-Gate loop progressing down the hierarchy: Act level -> Chapter level -> Scene level.

At each of these points, the system asks the user ("AskUserQuestion" or specific prompt loops) and pauses execution, aligning flawlessly with the `BLOCKED_ON` agency mechanic.