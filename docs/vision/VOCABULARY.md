---
slug: vision-vocabulary
type: vision
status: ready
summary: Canonical terms. One self-explaining definition each; used consistently across canon, specs, and code. Defines domain, capability, home domain, aspect, lazy-domaining, the naming scheme, and cross-capability dispatch.
---

# Vocabulary

| Term | Meaning |
|---|---|
| **Domain** | One of the three exported bases — and ONLY these three: `agentic` (actions), `workflow` (process), `context` (memory). The word "domain" is reserved for these. |
| **Capability** | A vertical area of work (e.g. `jules`, `music`, `novel`). It is authored in exactly one home domain and expressed across the domains as aspects. |
| **Home domain** | The single domain in which a capability is authored — its primary concern (orchestration → agentic, process → workflow, data/schema → context). Home ≠ exclusive ownership. |
| **Aspect** | A capability's expression in one domain: its agentic aspect (actions), workflow aspect (state machine), context aspect (memory). The aspects are the same capability faithfully restated per domain — isomorphic. The holding domain owns the aspect. |
| **Lazy-domaining** | A capability materializes an aspect in a non-home domain only when it needs one. Default = lazy graph data (workflow `Phase`/`Continuation`; context `Artefact`/memory nodes), no authored folder; a capability with fixed structure may instead author the aspect. No eager triplication. |
| **Export** | A skill or tool an aspect publishes, named without prefix; the harness derives the full name from `(domain, capability, export)`. |
| **Naming scheme** | Every export is `mcp__<domain>_<capability>_<export>` (slash form `/<plugin>:<domain>:<capability>:<export>`). The name alone tells you domain, capability, and export. |
| **Cross-capability dispatch** | One capability invoking another's aspect via the four-verb contract, recorded as a `DISPATCHED_TO` graph edge (e.g. `meta-development` → `jules`). Sketched, not yet first-classed; the edge type already exists. |
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
