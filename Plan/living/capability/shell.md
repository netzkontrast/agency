---
capability: shell
pillar: capability
vision_goals: [1, 2]
status: living
last_generated: 2026-06-19
sources: [73, 75]
---

# shell — Shell is a token-efficient host-command boundary: allowlisted execution, output filtering, and definable templates that bundle a command with its token-saving filter (capability pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
Shell is a token-efficient host-command boundary that allowlists execution, filters output to keep context lean, and defines reusable templates so commands stay recorded in provenance and expensive outputs don't bloat the session.

## Verbs (generated · 4)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `shell.define` | act | **name** · **command** · **filter** · doc · tags | Define a named shell template (command + output filter + doc) in the graph. |
| `shell.filter` | transform | **text** · spec | Filter text to a token-bounded slice — pure, no execution (hook-ready). |
| `shell.run` | effect | **runner** · command · template · args · filter | Run an ALLOWLISTED command (or a named template), FILTER its output, record it. |
| `shell.templates` | transform | query | Discover named query templates — built-in seeds ∪ graph-defined (Spec 075). |

## Ontology (generated)

_(no ontology extension)_

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/shell -->
