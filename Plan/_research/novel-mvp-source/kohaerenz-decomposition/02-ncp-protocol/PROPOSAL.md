# Narrative Context Protocol — Plugin Proposal

## 1. The `ncp_validate` Transform Verb

To bridge the Narrative Context Protocol into the Agency plugin environment safely, we propose introducing an `ncp_validate` verb under the novel capability extension.

- **Role Tag:** `transform`
- **Purpose:** A pure, deterministic function with no side effects. It takes a JSON payload and evaluates it against the strict rules of the NCP schema.
- **Mechanism:** It performs JSON Schema validation against the Draft 07 specification to ensure the document conforms to the `1.3.0` structural requirements. Critically, it validates all enum fields against the canonical vendored vocabulary (the 463 appreciations and 144 narrative functions). It returns a pass/fail boolean and a list of structural violations if any exist. It explicitly does *not* perform Dramatica theory meaning/coherence validation (which remains the domain of separate theory skills).

## 2. Where Schema and Vendored Vocabulary Live

The validation logic relies on a static source of truth for the schema and enums:
- The authoritative JSON Schema file is located at: `skills/ncp-author/upstream/schema/ncp-schema.json`.
- This file acts as the single embedded source for the vendored vocabulary, containing the complete `$defs.canonical_appreciation.enum` and `$defs.canonical_narrative_function.enum` lists. The `ncp_validate` transform verb must load and apply this specific file to ensure 100% compliance with the documented constraints.

## 3. The Per-Work `ncp.json` Skeleton

When a new story lifecycle is instantiated, the system creates a base skeleton reflecting the top-level schema shape:

```json
{
  "schema_version": "1.3.0",
  "story": {
    "id": "<generated-uuid>",
    "title": "Untitled",
    "genre": "",
    "logline": "",
    "created_at": "<timestamp>",
    "ideation": {},
    "narratives": [
      {
        "id": "primary-narrative",
        "status": "candidate",
        "title": "Main Draft",
        "subtext": {},
        "storytelling": {}
      }
    ]
  }
}
```

## 4. Graph Node vs. Rendered File

To align the NCP model with the plugin's "graph is the store" philosophy while acknowledging current spec realities:

- **Graph Nodes (Queryable State):** Every discrete decision—such as assigning a Dramatica Domain to a Perspective or finalizing a sequence of Storybeats—must be recorded as an `act` verb. These actions produce nodes in the bi-temporal memory graph. For example, `(Intent: "Define MC Resolve" -> Act: Set to "Change")` becomes a permanent, queryable node.
- **Rendered File (View):** The `ncp.json` file on disk represents a *projection* (or view) of the current state of the graph. When the graph reaches a valid checkpoint (e.g., passing a `gate` for Phase 2 completion), an `effect` verb renders the canonical `story.json` to disk for potential human review or export. If human authors directly edit the JSON file, an `ncp-io` reconciliation skill must translate those changes back into graph `act` nodes to maintain provenance.
