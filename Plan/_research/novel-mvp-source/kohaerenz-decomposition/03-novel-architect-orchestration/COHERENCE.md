# Coherence Check: Orchestration vs. Agency Model

This document analyzes how the `novel-architect` orchestration maps to the Agency plugin model primitives defined in `PLUGIN-CONCEPTS.md`.

## Lifecycle & Gate Mapping: Clean Fits

The 8-phase orchestration model maps elegantly to the Agency **Lifecycle** concept. Specifically, the "AskUserQuestion" loops and hard exit gates map perfectly to the Agency `gate` primitive.

*   **PASSED / BLOCKED_ON Mapping:**
    *   In `skills/novel-architect/phases/phase2-narrative-architecture.md`, the 3-gate loop explicitly pauses execution. Gate 1 (storyform shape + throughlines) requires a user approval. In Agency terms, this is a `gate:"hard"` that transitions the Lifecycle to `BLOCKED_ON` with an `input-required` flag.
    *   Once the user provides input (approve or edit), the gate resolves to `PASSED`, and the Lifecycle advances to the next step.
    *   This exact pattern repeats in Phase 5 (`skills/novel-architect/phases/phase5-scene-matrix.md`) with its 3-Gate loop (Act -> Chapter -> Scene).

These multi-step worksheet loops with explicitly defined pausing points are the ideal use case for the Agency plugin's gated workflows.

## Progressive Disclosure: Fits & Fights

The Agency model dictates that skills should be walked with **progressive disclosure**, revealing steps as you go and binding inputs/outputs into the memory graph.

### Where it fits cleanly

The internal structure of phases like Phase 2 and Phase 5 are prime examples of progressive disclosure.
*   **Phase 2:** The 8-step worksheet doesn't ask the user for all story points at once. It asks for the shape (Gate 1), then the dynamics (Gate 2), and finally the elements (Gate 3). Each step binds its output as provenance for the next, precisely as the skill model intends.

### Where it fights

The primary conflict between the legacy `novel-architect` and the Agency plugin model lies in **state persistence and file routing**.

*   **The Conflict:** `novel-architect` heavily relies on writing YAML/Markdown files directly to a file system workspace (`/home/claude/novel-projects/<slug>/` as seen in `skills/novel-architect/phases/phase0-bootstrap.md` and `skills/novel-architect/SKILL.md`).
*   **The Agency Model:** As stated in `PLUGIN-CONCEPTS.md`, "The graph is the store; files are a rendered view."
*   **Resolution:** The orchestration must stop treating files like `intent.yaml`, `architecture.yaml`, and `scene-matrix.md` as the primary source of truth. Instead, these phases must use `act` verbs to mutate the bi-temporal **Memory** graph directly. The YAML and Markdown files should only be generated as an `effect` (a rendered view) for human consumption or when a specific human-authored canon document is needed.

The current system's reliance on specific file paths outside of the plugin's graph is a "fight" that needs to be refactored into graph nodes and edges via an `OntologyExtension`.