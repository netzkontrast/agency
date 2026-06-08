# Structure, Scene & Render Pipeline Mapped to Agency Plugin Concepts

Based on the Agency Plugin model (`PLUGIN-CONCEPTS.md`), we map the core components of the `novel-architect` slice onto the four core engine concepts.

## 1. Intent (The Why)

**Intent** encapsulates what the user wants to accomplish. For structure and scene coherence, this intent is captured via the configuration or selection of plot-structure primitives.
*   **Plot-Structure Primitives:** The desire to build a narrative using the "40-Chapter Matrix" (`skills/novel-architect-structure/methods/40-chapter-matrix.md`) or "Hero's Journey" maps to an Intent configuration. For example, `intent.methods_preference.structure` containing `40-chapter-matrix` directs the engine to produce a 4-Act, 40-chapter structural skeleton.

## 2. Capability (The How)

**Capability** defines what the system can do, exposed as verbs (`act`, `transform`, `effect`).
*   **Scene Matrix Operations:** Generating or updating the Scene Matrix (the structured data representation of scenes and moments) is an `act` verb, as it mutates narrative state and records provenance into the graph.
*   **Validations and Audits:** The mechanical hard rules checks (`skills/novel-architect-structure/methods/validation/hard-rules.md`) and the Q1-Q5 scene-level bridge audit (`skills/novel-architect-scene/methods/scene-level-bridge.md`) act as `transform` verbs. They are pure, deterministic functions that take the state and return a validation output or finding.
*   **Rendering:** The render pipeline, which takes the queried state from the graph and produces Markdown files for the user (e.g., as discussed in `tasks/087-novel-architect-render-architecture-wiring/task.md`), operates via an `effect` verb, touching the filesystem outside the graph.

## 3. Lifecycle (The When)

**Lifecycle** tracks work-in-progress through states, heavily utilizing **gates**.
*   **Phase Flow and Gates:** The transition from Phase 2 (Narrative Architecture) to Phase 3 or Phase 5 to Phase 6 (Drafting) involves formal gates. As seen in `tasks/073-novel-architect-hard-rules-validation/task.md`, Gate 3 of Phase 2 blocks on Hard Rule validations. Similarly, a `pre_drafting` check before Phase 6 enforces the completion of the Q1-Q5 audit per moment. These checkpoints record `PASSED` or `BLOCKED_ON` within the Lifecycle concept.

## 4. Memory (The What Happened)

**Memory** is the bi-temporal graph tracking all state and provenance.
*   **Data Structure vs Rendering:** The Scene Matrix and the structural primitives (like storybeats and moments) exist natively as nodes and edges within this graph (Memory). The actual files on disk (like the Markdown scene matrices or chapter drafts) are merely rendered views of this Memory. The engine queries the Memory to render the view, ensuring the graph remains the authoritative source of truth.
