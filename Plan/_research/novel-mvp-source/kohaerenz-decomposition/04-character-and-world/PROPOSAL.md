# Proposal: Character & World Implementation (Slice 4)

This proposal details how the Character and World subsystems should be implemented within the Agency plugin, adhering strictly to the `PLUGIN-CONCEPTS.md` contract.

## 1. State Management: Graph Nodes vs. Rendered Files

The overarching principle is that the bi-temporal graph is the source of truth for queryable, structured data.

### Character State (`cast/characters/`)
*   **Graph Nodes:**
    *   `CharacterNode`: Represents a narrative entity.
    *   `PsychologicalProfileNode`: Linked to a CharacterNode. Includes properties defined by the selected frameworks (e.g., `ocean_openness: 75`, `enneagram_type: 4`, `tsdp_host: ANP`).
    *   `DramaticaRoleEdge`: Connects a CharacterNode to a specific structural function (e.g., Protagonist).
*   **Rendered View:** A unified `character-architecture.yaml` (or individual `cast/characters/<name>.yaml` files) is generated dynamically as an `effect`. It is a view, not the authoritative state.
*   **NCP Relationship:** The NCP `players[]`, `motivations[]`, and `perspectives[]` arrays are *rendered* from the graph state. Direct hand-edits to these NCP slots are forbidden, as the graph maintains the provenance of these psychological traits.

### World State (`world/`, `research/`)
*   **Graph Nodes/Edges:**
    *   `DomainNode`: (e.g., "Physics", "Mythology").
    *   `ResearchLifecycleState`: Tracks a domain's research progress (Identified -> Brief Drafted -> Pending External -> Findings Integrated).
    *   `WorldAxiomNode`: Specific, queryable facts extracted from research (e.g., "FTL travel is impossible").
*   **Rendered View:**
    *   `research/briefs/<domain>.md`: Generated as an `effect` to interface with `research-prompt-optimizer`.
    *   `world-bible.md`: This is the major exception—a human-authored canon document. However, its creation and updating are guided by the integration of findings (`act`). It serves as the canonical prose reference, but structured metadata remains in the graph.

## 2. Capability Verbs

The functionalities from `skills/novel-architect-character/` and `skills/novel-architect-world/` are decomposed into distinct verbs tagged with roles:

### Character Verbs
*   `transform_select_psych_framework`: Evaluates project intent (e.g., Genre, Tone) and returns a recommended array of psychological models (e.g., `["big-five", "enneagramm"]`). Deterministic.
*   `act_generate_psych_profile`: Creates or updates a `PsychologicalProfileNode` in the graph for a specific character using a selected framework. Mutates state and records provenance.
*   `transform_validate_dramatica_mapping`: Ensures that the generated psychological traits do not conflict with the character's assigned Dramatica role (e.g., ensuring a Contagonist has appropriate antagonistic traits). Pure function.
*   `effect_render_ncp_players`: Exports the current character graph state into the NCP JSON format.

### World Verbs
*   `transform_map_genre_to_domains`: Takes a genre (e.g., "Hard-SF") and returns a recommended list of research domains (`["Physics", "AI"]`). Pure heuristic function based on `methods/domain-mapping.md`.
*   `act_draft_research_brief`: Generates the content of a research brief based on the domain and depth heuristics, storing the draft state in the graph.
*   `effect_export_research_brief`: Writes the drafted brief to disk (`research/briefs/<domain>.md`) for the external agent to pick up.
*   `act_integrate_research_findings`: Takes incoming findings, extracts structural `WorldAxiomNode`s, updates the graph state, and prepares a diff for `world-bible.md`.

## 3. Lifecycle & Gates

The most prominent lifecycle application here is the deep research workflow from `methods/deep-research-briefs.md`:

1.  **Intent:** `intent:conduct-world-research`
2.  **Step 1:** System calls `transform_map_genre_to_domains`.
3.  **Step 2:** System calls `act_draft_research_brief` for each domain.
4.  **Step 3 (Gate):** A `gate:"hard"` is reached. Status becomes `BLOCKED_ON` awaiting human confirmation to execute research ("Hand off to research-prompt-optimizer?").
5.  **Step 4:** Upon approval, system calls `effect_export_research_brief`.
6.  **Wait State:** System awaits return of findings.
7.  **Step 5:** System calls `act_integrate_research_findings`.

This progressive disclosure ensures the user remains in control of the expensive/external research phase, while the graph perfectly records the provenance of how a specific scientific axiom ended up in the world bible.
