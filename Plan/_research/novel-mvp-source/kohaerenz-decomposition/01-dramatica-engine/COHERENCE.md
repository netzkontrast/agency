# Dramatica Plugin Coherence Check

This document examines how the Dramatica source material fits into the strict Agency plugin model.

## Clean Fits

### The Storyform as a Graph Subgraph
- The storyform perfectly aligns with the **Memory** concept. A storyform is fundamentally a graph subgraph of interconnected nodes representing the narrative state. Instead of being a rigid monolithic text file, the storyform lives as queryable edge-relations in the bi-temporal graph.

### Lookup Tools as Transforms
- Dramatica lookup tools (e.g., querying elements by quad or dynamic pair) are pure, deterministic reads with zero side effects. This strictly maps to the plugin's **`transform`** verb role tag, making them ideal for lookups, decidable linters, and validations.

### The Ontology as `OntologyExtension`
- The `maintenance/schemas/narrative-ontology/ontology.json` (measuring exactly 303 total entries: 4 `class`, 16 `type`, 62 `variation`, 63 `element`, 65 `dynamic-pair`, etc.) maps directly to the plugin model's **OntologyExtension** contract. The extension adds the required static nodes (the structural vocabulary) and the strict, closed edge set (dynamic pair relationships, hierarchical nesting) to the graph schema.

## Friction Points & Modifications

### Friction: Is the Ontology Vendored Data?
- **Current State:** The theory is maintained offline in large JSON schemas and markdown files (`skills/dramatica-theory/`, `maintenance/schemas/narrative-ontology/ontology.json`).
- **Plugin Tension:** Does this data ship as vendored static assets within the plugin, or does it exist as actual pre-populated graph nodes injected upon extension initialization?
- **Required Change:** To adhere fully to the plugin's single-graph mandate, the static `ontology.json` should act as vendored seed data. However, for deterministic provenance and state integrity, this data might need a **checksum sidecar** to ensure the specific version of the theory graph hasn't drifted when `execute` commands trace their logic.

### Friction: Rigid Hierarchy vs. Progressive Disclosure
- **Current State:** Dramatica implies a top-down, rigidly pre-computed web of choices.
- **Plugin Tension:** The plugin model dictates **Lifecycles** that follow **progressive disclosure** (unfolding step-by-step) with explicit `PASSED` or `BLOCKED_ON` gates.
- **Required Change:** The Dramatica engine must not demand the entire storyform to be populated at once. It must expose a multi-step `Lifecycle` skill where individual structural choices (e.g., selecting the Domain Class) are revealed and committed sequentially as isolated **`act`** verbs, gating further dependent queries.
