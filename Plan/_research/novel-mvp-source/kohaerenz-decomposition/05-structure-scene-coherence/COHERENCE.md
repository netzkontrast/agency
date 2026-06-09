# Coherence Checks Classification

This document classifies each coherence check identified in the `novel-architect` slice as either **DECIDABLE** (a pure `transform`/linter with a deterministic pass/fail) or **JUDGEMENT** (requiring an LLM/human call).

## Hard Rules Validation (H1 - H12)

Source: `tasks/073-novel-architect-hard-rules-validation/task.md` and `skills/novel-architect-structure/methods/validation/hard-rules.md`

All 12 Hard Rules are **DECIDABLE**. They represent structural invariants whose violations break the storyform model. The implementation uses deterministic checks over `architecture.yaml` and the `tools/dramatica-nav/nav.py` ontology.

*   **H1 (Exactly 4 throughlines named):** DECIDABLE
*   **H2 (Each Class used exactly once):** DECIDABLE
*   **H3 (OS-SS and MC-IC are complementary dynamic pairs):** DECIDABLE
*   **H4 (Story Goal at Type level):** DECIDABLE
*   **H5 (Crucial Element at Element level):** DECIDABLE
*   **H6 (Crucial Element in OS throughline):** DECIDABLE
*   **H7 (MC Resolve ↔ Crucial Element agreement):** DECIDABLE
*   **H8 (IC sits on dynamic-pair partner of MC's Element):** DECIDABLE
*   **H9 (No character carries both Elements of a pair):** DECIDABLE
*   **H10 (Outcome × Judgment yields one of four endings):** DECIDABLE
*   **H11 (Story Driver consistent across all act transitions):** DECIDABLE
*   **H12 (All four Signposts of a throughline are the four Types of that throughline's Class):** DECIDABLE

*Note: The actual rules text varies slightly between the task and the methods markdown, but both explicitly state that H1-H12 are mechanically checkable.*

## Scene-Level Bridge Audit (Q1 - Q5)

Source: `tasks/075-novel-architect-scene-level-bridge/task.md` and `skills/novel-architect-scene/methods/scene-level-bridge.md`

The Scene-Level Bridge validates if a moment is properly encoded in storyform terms.

*   **Q1 (Which throughline is dominant?):** **DECIDABLE** (Checks for the presence of a filled slot `dominant_throughline`)
*   **Q2 (Which throughlines are also present / Signpost timing?):** **DECIDABLE** (Checks for the presence of a valid `signpost_ref` and timing slot)
*   **Q3 (Operating level / Conflict flavor):** **DECIDABLE** (Checks for the presence of the `storypoint_element_id` slot)
*   **Q4 (Plot story point / Character arc beat):** **DECIDABLE** (Checks for the presence of the `character_arc_beat` slot)
*   **Q5 (Motivation elements / Thematic alignment):** **DECIDABLE** for presence checking (Checks if `theme_anchor_ref` is populated). However, evaluating if the *prose actually serves the theme* or evaluating the semantic alignment between the chosen element and the scene's content is **JUDGEMENT**. The linter task (`085-novel-architect-phase-flow-linters`) enforces completeness mechanically (e.g., `SC.Q5_EMPTY`).

## Anti-Patterns (AP-1 to AP-14)

Source: `tasks/074-novel-architect-anti-patterns/task.md`

Anti-Patterns function as diagnostic Pre-Checks during different phases. While some can be partially caught mechanically, evaluating them fully generally requires context.

*   **AP-1 (MC ≠ Protagonist intentional?):** **JUDGEMENT**. Requires assessing if the separation is narratively justified.
*   **AP-3 (Goal at wrong level):** **DECIDABLE**. Equivalent to H4, can check if it's a Type.
*   **AP-4 (Crucial Element too abstract to write):** **JUDGEMENT**. Assessing if an element is "too abstract" requires LLM/human evaluation of the draft.
*   **AP-5 (Class double-assignment):** **DECIDABLE**. Equivalent to H2.
*   **AP-6 (MC Resolve ↔ Crucial Element disagreement in draft):** **JUDGEMENT**. While the structural assignment is decidable (H7), detecting if the actual *draft* diverges from this requires semantic analysis.
*   **AP-8 (Mental Sex misapplied as character trait):** **JUDGEMENT**. Requires reading the characterization to see if Linear/Holistic is treated as personality rather than problem-solving logic.
*   **AP-9 (Inconsistent Driver changing scene-to-scene):** **JUDGEMENT** (in draft). Mechanically (H9/H11) it's decidable at the structural level, but assessing the execution in the prose needs judgement.

## Phase Flow and Canon Status

*   **Worksheet Order (`tools/check-worksheet-order.py`):** **DECIDABLE**. Enforces sub-phase heading order in Phase 2 markdown (`tasks/085-novel-architect-phase-flow-linters/task.md`).
*   **Canon Status Hierarchy (`tools/check-canon-status.py`):** **DECIDABLE**. Mechanically checks if decanonized entities are referenced or if disputed entities block active phases (`tasks/086-novel-architect-canon-status-linter/task.md`).
