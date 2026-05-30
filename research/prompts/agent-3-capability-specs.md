# Agent 3 — Capability spec coverage (Plan + all plugins)

**Output dir:** `research/capability-specs/`
**Critical-thinking method:** gap analysis + structured mapping (source → Agency target).

Read `research/JULES_RESEARCH_PROTOCOL.md` and `research/SOURCES.md` first and obey
them. Satisfy Gate 1 (full recursive ingestion + `_ingest.md` ledger) before any
finding — this work-unit is the most ingestion-heavy; read **every** spec and
**every** skill/agent file in the sources you can clone.

## Scope to ingest (read every file)

- **Work repo (PR1):** `agency/capabilities/**`, `docs/vision/specs/superpowers-port.md`,
  `docs/vision/CAPABILITY-CLUSTERS.md`, `docs/EXTENSION-PLAN.md`.
- **Sources (read-only):**
  - `the-agency-system` → all of `Plan/001`–`023`, `Plan/harness/`, `Plan/decisions/`.
  - `superpowers-marketplace` → every plugin/skill (all superpowers plugins).
  - `SuperClaude_Framework` + `SuperClaude_Plugin` → every agent/command/skill.
  - `bitwize-music` → every handler/skill.
  Use whichever you can cleanly clone; note any `[BLOCKED: source …]`.

## Method

For every capability implied by a source, map it to an **Agency target**: a
capability + verbs, a `develop` skill (gated phase-graph), an `OntologyExtension`,
or an example extension (`examples/`). Identify what PR1 already covers, what is
specced-not-built, and what is entirely missing.

## Deliverables (concrete artifacts, every claim cited path/SHA)

- `research/capability-specs/_ingest.md` — the ingestion ledger.
- `research/capability-specs/FINDINGS.md` — coverage summary: covered / specced /
  missing, by source.
- `research/capability-specs/capability-catalogue.md` — the full mapping table:
  `source item → Agency target (capability.verb / skill / extension) → status`.
- `research/capability-specs/specs/` — per-cluster spec stubs in PR1's own spec
  style (one file each) for the high-value missing clusters, e.g. `music`,
  `novel`, `agentic`, `jules-orchestration`, `context-mode`,
  `superclaude-analysts`, `superpowers-remainder`. Each stub: purpose, verbs/role
  tags, ontology fragment, gated skill (if any), and the source it ports from.

Publish one ready PR into `claude/extract-agency-plugin-o4JRc` per the protocol.
