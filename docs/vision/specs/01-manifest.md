---
slug: spec-manifest
type: spec
status: ready
summary: The row manifest (`<domain>/<row>/manifest.toml`) and the immutable name-derivation rules. One shape — universal preamble + export surface + optional domain-specific sections.
---

# 01 — Manifest & name derivation

Every row is declared by one `manifest.toml` at `<domain>/<row>/manifest.toml`.
The harness derives all public names from `(domain, row, export)`; exports
carry no domain or row prefix.

## Preamble (required)

```toml
[row]
domain = "agentic"   # agentic | workflow | context — MUST match the parent dir
name   = "jules"     # ^[a-z][a-z0-9-]{0,30}$
```

A path/identity mismatch (`agentic/jules/manifest.toml` with `name="music"`) is
a lint error.

## Export surface (optional; any domain)

```toml
[skills]
exports = ["research"]          # → /<domain>:<name>:research

[tools]
exports = ["create", "patch"]   # → mcp__<domain>_<name>_create, ...

[codemode]
prefers = ["create", "patch"]   # tool exports that boot in CodeMode
```

Exports MUST NOT contain a domain/row prefix (`jules-create` is forbidden;
`create` is correct).

## Domain-specific sections (optional)

```toml
# workflow rows
[[gates]]
id           = "research-complete"
path         = "gates/research-complete.yaml"
blocks_phase = "02"

# context rows
[ontology]
node_types = ["ResearchTopic", "Finding"]
[templates]
research_brief = { path = "templates/research-brief.jinja" }
[schemas]
finding = { path = "schemas/finding.schema.json" }
```

Phases are graph nodes, not manifest arrays (see [05](05-workflow-base.md)).

## Derivation rules (immutable, owned by the harness)

| Derived | Rule |
|---|---|
| skill (slash) | `/<domain>:<row>:<export>` |
| MCP tool | `mcp__<domain>_<row>_<export>` |
| handler module | `<domain>.<row>.handlers.<export>` |
| skill file | `<domain>/<row>/skills/<export>/SKILL.md` |
| ontology node id | `<row>/<Type>` |
| schema id | `tag:agency.local,2026:schema:<row>/<Type>` |

## Validation

Three JSON Schemas (`agentic-row`, `workflow-row`, `context-row`), each
`$id`-tagged with `additionalProperties: false` at root. The regex on `name`
and the exports-prefix ban are enforced at schema time.
