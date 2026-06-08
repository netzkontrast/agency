# Dramatica Plugin Integration Proposal

This document outlines how the Dramatica engine should live as part of the broader novel capability, adhering to the principles in `PLUGIN-CONCEPTS.md`.

## Proposed Capability Verbs

The Dramatica capability will expose the following verbs:

1. **`dramatica_lookup` (`transform`)**:
   - A pure lookup against the static ontology data (e.g., fetching a term's dynamic pair or quad relationships).
   - *Example Use*: "What is the dynamic pair of Logic?"
2. **`storyform_commit_choice` (`act`)**:
   - Mutates the narrative state by creating/updating a node or edge in the storyform subgraph and records provenance.
   - *Example Use*: Committing "Main Character Domain = Universe".
3. **`validate_coherence` (`transform`)**:
   - A decidable linter check that runs deterministically. It verifies if the currently committed storyform edges violate Dramatica rules (e.g., Main Character and Influence Character domains must be in a dynamic pair relationship).
4. **`render_outline` (`effect`)**:
   - Touches the outside world by rendering the graph state of the storyform into a human-readable markdown file on disk.

## Data Storage & Ontology

- **Where the ontology lives**: The static Dramatica structure (`maintenance/schemas/narrative-ontology/ontology.json`, 303 entries) acts as vendored initial seed data that loads via the **OntologyExtension**. It provides closed enums for properties (e.g., 65 `dynamic-pair` records, 4 `class` types, 16 `type`, 62 `variation`, 63 `element`).
- **Graph Nodes vs. Rendered Files**:
  - **Graph Nodes**: The storyform choices, characters, and assigned throughlines are individual nodes in the bi-temporal graph. Their relationships (e.g., "Character A belongs to the MC Throughline") are edges.
  - **Rendered Files**: Files on disk are purely derived views of the graph state (e.g., an exported `storyform.md` outline). The only exception would be human-authored prose drafts (canon documents).

## Gates and Judgement

- **Pre-drafting Gate**: A structural `Lifecycle` step where drafting is `BLOCKED_ON` an `input-required` gate until the core storyform choices are legally committed and validate against the `validate_coherence` transform.
- **Judgement Calls**: While `validate_coherence` is a pure decidable transform, determining *how* a specific Dramatica Element translates into a prose scene (Encoding) requires a judgement call (an LLM/human call) and thus represents a separate step in the workflow, recorded back into the graph.
