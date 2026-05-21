---
slug: spec-manifest
type: spec
status: ready
summary: The capability manifest (`<domain>/<capability>/manifest.toml`, present when an aspect is authored) and the immutable name-derivation rules. One shape — universal preamble + export surface + optional domain-specific sections.
---

> Amended by the capability/aspect/lazy-domaining model — see VOCABULARY.md.

# 01 — Manifest & name derivation

When a capability **authors** an aspect in a domain, that aspect is declared by
one `manifest.toml` at `<domain>/<capability>/manifest.toml`. (A lazy aspect
materializes as graph nodes instead and has no manifest.) The harness derives
all public names from `(domain, capability, export)`; exports carry no domain
or capability prefix.

## Preamble (required)

```toml
[capability]
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

Exports MUST NOT contain a domain/capability prefix (`jules-create` is
forbidden; `create` is correct).

## Domain-specific sections (optional)

```toml
# authored workflow aspect
[[gates]]
id           = "research-complete"
path         = "gates/research-complete.yaml"
blocks_phase = "02"

# authored context aspect
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
| skill (slash) | `/<domain>:<capability>:<export>` |
| MCP tool | `mcp__<domain>_<capability>_<export>` |
| handler module | `<domain>.<capability>.handlers.<export>` |
| skill file | `<domain>/<capability>/skills/<export>/SKILL.md` |
| ontology node id | `<capability>/<Type>` |
| schema id | `tag:agency.local,2026:schema:<capability>/<Type>` |

## Validation

Three JSON Schemas (`agentic-aspect`, `workflow-aspect`, `context-aspect`), each
`$id`-tagged with `additionalProperties: false` at root. The regex on `name`
and the exports-prefix ban are enforced at schema time.
