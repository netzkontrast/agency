# Narrative Context Protocol — Plugin Concepts

## NCP as a Data Model

The Narrative Context Protocol (NCP) is structured as a declarative data model that can be mapped onto the Agency plugin architecture.

As measured in the official schema file (`skills/ncp-author/upstream/schema/ncp-schema.json`), the schema constrains the data in the following ways:
- **JSON-Schema Version:** `http://json-schema.org/draft-07/schema#`
- **Schema Version:** `1.3.0`
- **Top-Level Shape:** A single root object containing `schema_version` and a `story` object. The `story` object aggregates metadata (`id`, `title`, `genre`, `logline`, `created_at`), an `ideation` object, and an array of `narratives` (which in turn contain `subtext` and `storytelling` layers).

## Canonical Vocabulary and Validation Rules

The schema enforces rigorous enumeration checks for its narrative elements. Based on the JSON Schema `$defs`, the canonical vocabulary consists exactly of:
- **463** appreciations (`$defs.canonical_appreciation.enum` in `skills/ncp-author/upstream/schema/ncp-schema.json`).
- **144** narrative functions (`$defs.canonical_narrative_function.enum` in `skills/ncp-author/upstream/schema/ncp-schema.json`).

These strict constraints allow NCP to be validated through a pure, decidable function (a `transform` verb in the plugin model) that guarantees structural integrity, enum compliance, and basic state validity without requiring external service calls or LLM judgment.

## Relationship to the Dramatica Storyform

NCP serves as the structural container for Dramatica logic, separating the "storage" of narrative intent from the "meaning" of the theory.

- **JSON-IO vs. Meaning:** As noted in `skills/ncp-author/SKILL.md`, the `ncp-author` skill owns JSON-IO and enum-compliance. It relies on the separate `dramatica-theory` and `dramatica-vocabulary` skills to validate the semantic coherence of those choices (e.g., Dynamic-Pair validation, Element-Quad checks, and KTAD coherence).
- **Integration Surfaces:** According to `research/ncp-novel-co-authoring-spec/output/SPEC.md` (§5.5), Dramatica directly maps into specific branches of the NCP document: `subtext.storypoints` and `subtext.dynamics` host the Storyform, while `subtext.perspectives` host the Four Throughlines.

By mapping NCP to the plugin architecture, the act of "drafting a storyform" becomes a series of `act` verbs that record provenance to the bi-temporal graph, gated by `transform` validators that ensure the JSON structurally complies with the 1.3.0 schema and its 607 total vendored vocabulary terms.
