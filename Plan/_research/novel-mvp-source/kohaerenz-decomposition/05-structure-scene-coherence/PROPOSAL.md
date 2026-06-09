# Proposal: Integration of Novel Structure and Scene Coherence into Agency Plugin

This proposal outlines how the structural validation and scene-matrix mechanics of `novel-architect` should be expressed within the Agency Plugin engine.

## 1. The `coherence_check` Verb (Transform)

We propose adding a new `coherence_check` capability mapping to a **`transform`** verb. This verb will act as a pure, deterministic linter against the narrative state in the graph.

**Decidable Subset Included:**
*   All 12 Hard Rules (H1-H12) from Phase 2 (Narrative Architecture).
*   Worksheet Step ordering constraints (e.g., `WS.STEP_ORDER`).
*   Canon Status referential integrity (e.g., `CS.DECANONIZED_REFERENCED`, `CS.DISPUTED_BLOCKS_ACTIVE`).
*   Presence and non-emptiness checks for the Scene-Level Bridge (Q1-Q4 completeness and Q5 non-emptiness).

The output is a standardized validation report (e.g., JSON artifact format per Task 084) containing `PASS` or `FAIL` findings without mutating the narrative graph.

## 2. The `pre_drafting` Gate

A new checkpoint, the **`pre_drafting` gate**, must be registered in the plugin Lifecycle for Phase 6 (Drafting).

*   **Trigger:** Execution of this gate is requested when attempting to begin writing a draft for a scene/chapter.
*   **Condition:** It evaluates the `coherence_check` output specifically for the Q1-Q5 Scene-Level Bridge audit on the target moments.
*   **Result:** It records `PASSED` if all required schema fields (dominant throughline, signpost ref, etc.) are present and coherent. If any are `MISSING` or `PARTIAL`, the gate records `BLOCKED_ON` with an `input-required` state, pausing the workflow to elicit a human or agent decision (e.g., filling in the missing Q5 theme anchor).

## 3. Scene-Matrix Artefacts as Graph Nodes

The items manipulated during Phase 5 (Scene Matrix) must exist as queryable state in the bi-temporal graph rather than just flat files.

**Ontology Extension:**
*   **Nodes:** `Chapter`, `Storybeat`, `Moment`
*   **Edges:** A `Moment` must have edges linking to storyform structural nodes: `dominant_throughline`, `signpost_ref`, `storypoint_element_id`, `character_arc_beat`, and `theme_anchor_ref`.

Generating or updating these nodes and edges uses an `act` verb.

## 4. Render Architecture and Graph-vs-Disk Tension

The visual output that users interact with (like `architecture-status-view.md` or a Chapter Draft) is a downstream rendering of the graph state, generated using an `effect` verb.

**The Graph-vs-Disk Tension:**
Task 087 (`render_architecture.py`) highlights a key tension: the renderer currently consumes a flat JSON artifact (`.architecture-validation.json`) written to disk by the linter, checking file mtimes to detect staleness.

In the pure Agency Plugin model, **the graph is the store, and files are rendered views**. To resolve this tension in the plugin architecture:
*   The output of the `coherence_check` (`transform`) should not be written to a static `.json` file on disk for the renderer to read.
*   Instead, the render `effect` should dynamically invoke the `transform` verb (or query its cached result in the Memory graph) to generate the status-view markdown. This eliminates the stale-artifact problem and perfectly aligns with the engine's core philosophy that queryable state lives only in the graph.