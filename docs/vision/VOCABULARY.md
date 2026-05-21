---
slug: vision-vocabulary
type: vision
status: ready
summary: Canonical terms. One definition each; used consistently across canon, specs, and code.
---

# Vocabulary

| Term | Meaning |
|---|---|
| **Domain** | One of the three exported bases: `agentic`, `workflow`, `context`. |
| **Row** | A capability nested in its one owning domain (e.g. `jules` in `agentic`). |
| **Export** | A skill or tool a row publishes, named without prefix; the harness derives the full name from `(domain, row, export)`. |
| **Four-verb contract** | `list_tools`, `call_tool`, `list_skills`, `dispatch_skill` — the engine's entire public surface. |
| **CodeMode** | Rendering a domain's call surface as a code sandbox where its functions are callable. |
| **Tool result envelope** | The frozen four-key return: `ok`, `data`, `warnings`, `next_suggested_tools` (spec 02). |
| **Phase** | A graph node representing a step in a process; bodies referenced by `body_ref`. |
| **Gate** | A guard on a phase; hard-blocking or advisory (spec 03). |
| **Continuation** | A graph node holding a yielded workflow's state (no state files on disk). |
| **Artefact** | A graph node recording a product; its bytes live in user storage via a driver. |
| **Artefact driver** | A backend mapping `Artefact` nodes to external storage (`fs`, `repo`, `s3`, `http`, `drive`). |
| **Graph / GraphQLite** | The SQLite + Cypher substrate at `context/_store/ontology.db`; the only persistent state. |
| **skill_kind** | A skill's classification (e.g. `domain`, `tool`, `orchestrator`, `discipline`, `workflow`, `analysis`). |
| **Frontmatter canon** | Required front-matter on canon docs and skills: `slug`, `type`, `status`, `summary` (summary ≤ 240 chars for specs, ≤ 120 for skills). |
