# Agent 5 — Code-mode & Context-mode SOTA

**Output dir:** `research/code-context-mode/`
**Critical-thinking method:** benchmarking + first-principles token-economics.

Read `research/JULES_RESEARCH_PROTOCOL.md` and `research/SOURCES.md` first and obey
them. Satisfy Gate 1 (full recursive ingestion + `_ingest.md` ledger) before any
finding.

## Scope to ingest (read every file)

- **Work repo (PR1):** the engine surface (`engine.py` — `search`/`get_schema`/
  `execute`, the auto-wiring), `cli.py`, `skill.py` (progressive disclosure /
  `current()`), `capabilities/plugin.py` (`help`), `capabilities/develop.py`
  (`reference`), and the tests proving code-mode chaining + isomorphism.
- **Sources (read-only):** `the-agency-system` → `Plan/000-overview.md` (the
  **anchor-triad** `*_search`/`*_describe`/`*_invoke` pattern, the < 4 KB boot
  target, Context Mode Path B + the ontology graph), `Plan/008-codemode-registry/`,
  `Plan/harness/`. FastMCP Code Mode docs via WebFetch. Use what you can clone.

## Method

This is the SOTA thesis of the whole system: **token efficiency via code-mode
(many calls → one delta) and context-mode (progressive disclosure)**. Measure
PR1's current behaviour from first principles (what crosses the context boundary
on a typical task?), benchmark it against the anchor-triad / Path-B prior art, and
propose concrete upgrades.

## Investigate / propose

- **`search` ranking & shape** — how good is discovery? Propose ranking + a
  result shape that points at the next action, not a tool dump.
- **`get_schema` disclosure** — minimal-but-sufficient schema slices; examples.
- **`next_suggested_tools`** — the engine guiding the next call (pairs with
  Agent 1's `ToolResult` envelope).
- **Reference / T3 loading** — extend `develop.reference`; a `context_*` triad
  over docs (Path B) loaded on demand.
- **Boot budget** — measure the boot tool surface; propose anchor-triads +
  `hidden/defer_schema` to shrink it (cite the Plan's < 4 KB / < 500-token target).

## Deliverables (concrete artifacts, every claim cited)

- `research/code-context-mode/_ingest.md` — the ingestion ledger.
- `research/code-context-mode/FINDINGS.md` — current token-economics of PR1's
  surface, measured/estimated, cited `path:line`; gaps vs the prior art.
- `research/code-context-mode/PROPOSAL.md` — concrete upgrades (anchor-triads,
  `next_suggested_tools`, richer `search`/`get_schema`, a `context_*` triad),
  each with a shape, a worked example, and the token saving it buys.

Publish one ready PR into `claude/extract-agency-plugin-o4JRc` per the protocol.
