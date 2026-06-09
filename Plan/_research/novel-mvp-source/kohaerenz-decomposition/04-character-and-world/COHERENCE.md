# Coherence Check (Slice 4)

This document evaluates how the existing character and world-building capabilities (`skills/novel-architect-character/` and `skills/novel-architect-world/`) align with the Agency plugin model described in `PLUGIN-CONCEPTS.md`.

## Character/World: Graph Nodes vs. Rendered Files

The defining principle is: **The graph is the store; files are a rendered view.**

### Character State
Currently, `novel-architect-character` writes to NCP (`narratives[].subtext.players[]`) and to a workspace file `character-architecture.yaml`.
*   **Where it fits:** The structured psychological profiles (Big Five scores, Enneagram types, Jungian archetypes) map perfectly to **graph nodes**. The traits, motivations, and linkages to specific Dramatica roles (e.g., this character is the Protagonist in the OS throughline) are highly relational and queryable.
*   **Where it fights:** Storing this data permanently in a monolithic `character-architecture.yaml` alongside the NCP JSON fights the single-source-of-truth model. The YAML should be considered a *rendered view* or an export, not the primary state. The true state should live in the bi-temporal graph, merging into the `OntologyExtension` for the novel domain.

### World State
Currently, `novel-architect-world` manages `world-bible.md` and a directory of research briefs/findings.
*   **Where it fits:** The research *process* fits the lifecycle model perfectly. Creating a brief (`intent`), passing a gate (`BLOCKED_ON` awaiting human approval to run research), and receiving findings are discrete states well-suited to the bi-temporal graph. The domain definitions (e.g., Genre: Hard-SF -> Domain: Physics) are solid ontology edges.
*   **Where it fights:** A monolithic `world-bible.md` is heavily human-authored and unstructured, making it an "explicit, documented exception" (a canon document). However, the metadata *about* the world—such as identified domains, the status of research for each domain, and key factual axioms extracted from findings—should be **graph nodes**. The system currently treats the markdown file as the sole repository of world truth, which makes programmatic validation (e.g., "does this scene contradict a known physical law in our world bible?") difficult.

## Plugin Model Fit vs. Friction

### Clean Fits
1.  **Pure Functions (Transforms)**: The Dramatica-Slot-Resolution (mapping an archetype to an NCP slot) and the domain-mapping heuristics (Genre -> Domains) are pure, deterministic `transform` verbs. They take inputs (Genre or Archetype) and return decidable outputs without side effects.
2.  **Lifecycle Gates**: The research delegation workflow in `skills/novel-architect-world/methods/deep-research-briefs.md` explicitly calls for a pause ("askuser: 'Brief fertig. An research-prompt-optimizer übergeben?'"). This is an exact 1:1 match for a `gate:"hard"` with `BLOCKED_ON` + `input-required`.
3.  **Ontology Extensions**: The specific psychological models (OCEAN, Enneagram) are perfect candidates for an `OntologyExtension`. They add widen-only enums (e.g., adding `enneagram_type` properties to a character node) without modifying the core engine.

### Friction Points & Required Changes
1.  **State Management**: `novel-architect-character` lists `state_management: "ncp"` in its `SKILL.md`. Under the plugin model, state management is the *graph*. The NCP is a schema and perhaps a rendering target, but the active, queryable state of the character's psychology must reside in the memory graph. We must refactor to make the graph the source of truth, rendering NCP or `character-architecture.yaml` only when needed (as an `effect`).
2.  **Delegation Boundaries**: The current system relies on "Sub-Skills" that are called by a "parent orchestrator" (`novel-architect`). The plugin model flattens this slightly: intents are resolved to capabilities via `search`. The hierarchical delegation should be re-envisioned as a sequence of steps in a capability's `Lifecycle`, binding inputs/outputs at each step, rather than tight coupling between hardcoded skill scripts.
3.  **File I/O as Primary Operation**: The existing skills frequently talk about writing to specific files (`research/briefs/<domain>.md`). In the plugin model, creating the brief is an `act` that updates the graph state. Writing it to a markdown file on disk is merely a side-effect (`effect`) to allow human inspection or to pass to an external agent not integrated into the graph.
