# Agent 1 — OO & architecture critique + redesign

**Output dir:** `research/oo-architecture/`
**Critical-thinking method:** first-principles decomposition + pre-mortem inversion.

Read `research/JULES_RESEARCH_PROTOCOL.md` and `research/SOURCES.md` first and obey
them. This is a context-heavy task — satisfy Gate 1 (full recursive ingestion with
an `_ingest.md` ledger) before writing any finding.

## Scope to ingest (read every file)

- **Work repo (PR1):** all of `agency/**` (especially `capability.py`, `engine.py`,
  `skill.py`, `ontology.py`, `memory.py`, `intent.py`, `lifecycle.py`,
  `install.py`, `cli.py`, `capabilities/**`), all of `tests/**`, and
  `docs/vision/**` (CORE, ARCHITECTURE, specs).
- **Sources (read-only):** `the-agency-system` → `Plan/REFACTOR_DESIGN.md`,
  `Plan/000-overview.md`, `Plan/harness/`, `Plan/008-codemode-registry/`,
  `Plan/023-harness-in-harness/`, `Plan/decisions/`. Use what you can clone.

## Method

Decompose the engine from first principles: what is the irreducible object model,
and where does PR1's implementation add accidental complexity or miss an
abstraction? Then run a pre-mortem: "in six months PR1 was abandoned/rewritten —
what design flaw caused it?" Let the answers drive the proposals.

## Deliverables (concrete artifacts, every claim cited `path:line`)

- `research/oo-architecture/_ingest.md` — the ingestion ledger.
- `research/oo-architecture/FINDINGS.md` — the critique: current object model
  (`Capability`/`CapabilityBase`/`CapabilityContext`/`Registry`/`SkillRun`/
  `OntologyExtension`/boundaries), its seams and smells, contradictions between
  code/tests/docs.
- `research/oo-architecture/PROPOSAL.md` — concrete redesigns with Python sketches
  and a before/after for at least one real verb:
  1. a uniform **`ToolResult` envelope** (`ok / data / warnings / next_suggested_tools`)
     and how every verb + the engine wiring adopts it;
  2. a **`Boundary`/`Driver` Protocol family** generalising `JulesBackend` +
     `VCSBackend`, plus a **driver registry** for `delegate`;
  3. **first-class `Phase`/`Skill` objects** replacing the dict-shaped walker;
  4. **typed error handling** (the failed-invocation record → a typed error in the
     envelope).
  Each proposal: shape + one worked example + a cited precedent (OSS or in-repo) +
  the trade-off and migration cost.

Publish one ready PR into `claude/extract-agency-plugin-o4JRc` per the protocol.
