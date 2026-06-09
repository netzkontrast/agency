# Dramatica Plugin Concepts Mapping

This document maps the irreducible Dramatica primitives onto the Agency plugin's core model as defined in `PLUGIN-CONCEPTS.md`.

## Primitive 1: The Storyform
A storyform is the structural blueprint of the narrative.
- **Concept Mapping:** **Memory** (The Bi-temporal Graph)
- **Role:** It represents the queryable narrative state stored as nodes and edges in the graph.
- **Operations:**
  - Modifying a storyform property (e.g., setting the Main Character Resolve) is an **`act`**. It mutates the graph state and records the provenance of the change.

## Primitive 2: The Throughline
A throughline isolates one specific perspective within the Storyform.
- **Concept Mapping:** **Memory** (Graph Sub-structures)
- **Role:** Throughlines are structural sub-graphs or specific node relationships linked to the main storyform node, shaped by an `OntologyExtension`.
- **Operations:**
  - Assigning a throughline to a Class is an **`act`** (state mutation).
  - Validating throughline rules is a **`transform`** (deterministic pass/fail linter check).

## Primitive 3: The Dynamic Pair
A dynamic pair connects two opposing narrative terms (e.g., Logic vs. Feeling).
- **Concept Mapping:** **Memory** (OntologyExtension Data)
- **Evidence & Metrics:** By explicitly measuring the actual data in `maintenance/schemas/narrative-ontology/ontology.json`, we find a discrepancy from canonical theory: the file contains exactly **303** total entries, breaking down into **4** `class`, **16** `type`, **62** `variation` (missing 2 from canonical 64), **63** `element` (missing 1 from canonical 64), and exactly **65** `dynamic-pair` table entries (missing 10 from the 75 mentioned in the vocabulary skill). These measured numbers represent the actual current vendored state.
- **Operations:**
  - Looking up a term's opposite is a **`transform`** because it is a deterministic, decidable read from the ontology.

## Primitive 4: The Lookup Operation
Navigating the Dramatica structure (e.g., querying quads, definitions, structural positions).
- **Concept Mapping:** **Capability / Verb**
- **Wire Contract:**
  - **`search`**: Finds the Dramatica capability when the Intent involves structuring a story.
  - **`get_schema`**: Fetches the required parameters for the verb (e.g., `term_id`).
  - **`execute`**: Runs the verb in code-mode.
- **Operations:**
  - A lookup verb (e.g., `dramatica_lookup`) is a pure **`transform`**. It has no side effects and relies on static ontology data.
