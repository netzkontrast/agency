# Proposal: Gated Agency Skill for Novel Orchestration

This proposal outlines how the existing `novel-architect` orchestration will be refactored into a native Agency plugin skill, governed by an explicit `OntologyExtension` and lifecycle gates.

## The Gated Agency Skill Structure

The current 8-phase system will become a single, overarching Agency `skill` named `orchestrate-novel`.

*   **Lifecycle Management:** This skill will track a `Lifecycle` entity within the graph, progressing from state `BOOTSTRAP` to `ITERATION`.
*   **Gate Primitives:** Rather than loose prompt loops, we will implement rigid `gate:"hard"` checkpoints for:
    *   `Intent Approval` (Exiting Phase 1)
    *   `Architecture Approval` (The 3 gates defined in Phase 2)
    *   `Character Roster Approval` (Exiting Phase 3)
    *   `Research Scope Approval` (Mid Phase 4)
    *   `Scene Matrix Approval` (The 3 gates defined in Phase 5)
*   At these gates, the skill will record a `BLOCKED_ON` status, returning control to the agent/human to provide the `input-required` (e.g., selecting a psycho-model or approving a throughline).

## Command Surface Mapping

The legacy command surface defined in `skills/novel-architect/commands/` will map to capability searches via the `Intent` primitive:

*   `/novel-start` -> Maps to setting an Intent to "Initialize a new narrative workspace." Triggers the new `scaffold` verb (see below) and enters the `BOOTSTRAP` lifecycle state.
*   `/novel-design` (Phase 2), `/novel-characters` (Phase 3), `/novel-research` (Phase 4), `/novel-scenes` (Phase 5), `/novel-draft` (Phase 6), `/novel-reflect` (Phase 7):
    *   These will no longer be standalone commands that read random markdown files.
    *   They will become specific Intent targets that attempt to resume the `orchestrate-novel` skill at the corresponding Lifecycle state, provided the requisite graph provenance (e.g., approved architecture before starting characters) exists.

## The `scaffold` Verb (Workspace Initialization)

To break away from the hardcoded `/home/claude/novel-projects/<slug>/` setup (seen in `skills/novel-architect/phases/phase0-bootstrap.md`), we propose a dedicated `scaffold` verb.

*   **Verb Definition:** `scaffold_novel_workspace`
*   **Role Tag:** `effect` (Touches the outside world/filesystem export).
*   **Purpose:** To generate the rendered view of the initial project state based on user intent.
*   **Action:** When executed, this verb creates the standard directory layout:
    `novels/{author}/works/{genre}/{slug}/`
*   **Context:** Unlike the old setup which stored the canonical state in these folders, this layout is strictly a *rendered view*. The canonical truth of the author, genre, and slug lives as nodes in the Memory graph, inserted via an `act` verb prior to calling `scaffold`.