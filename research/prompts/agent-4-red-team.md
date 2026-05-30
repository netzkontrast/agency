# Agent 4 — Red-team / critical critique of PR1

**Output dir:** `research/red-team/`
**Critical-thinking method:** devil's advocate + pre-mortem + Chesterton's fence.

Read `research/JULES_RESEARCH_PROTOCOL.md` and `research/SOURCES.md` first and obey
them. Satisfy Gate 1 (full recursive ingestion + `_ingest.md` ledger) before any
finding.

## Scope to ingest (read every file)

- **Work repo (PR1):** all of `agency/**`, all of `tests/**`, `docs/vision/**`.
  Pay attention to: the code-mode `execute` sandbox (`engine.py`), the single
  graph (`memory.py`, provenance + the logical clock), the ontology enforcement
  (`ontology.py`), the injected boundaries (`_vcs.py`, `jules.py`,
  `_jules_api.py`), and `delegate`/`subagent`/`gate`.
- **Sources (read-only):** `the-agency-system` → `Plan/JULES_PROTOCOL.md`,
  `Plan/harness/design.md`, any security/scaling notes. Use what you can clone.

## Method

Adversarially dissect PR1. For each candidate weakness, FIRST apply Chesterton's
fence ("why might this be intentional / what does the current design buy?"), THEN
decide if it is a real risk. Run a pre-mortem on the model itself (single graph,
code-mode, isomorphic surfaces) at 100× scale and under a hostile caller.

## Investigate at minimum

- Is the code-mode `execute` block a security boundary? What can a malicious or
  buggy `code` argument reach? (sandbox escape, resource exhaustion, graph writes)
- Single-graph scaling: the full-scan `_max_persisted_tick`, provenance traversal
  cost, lock contention.
- Provenance gaps and trust: the open review findings still unaddressed —
  `jules.verify` trusting the caller's `branch_on_remote`, `_jules_api` pagination
  cap (>1000 sources), `_vcs` merge-into-base / dirty-in-worktree.
- Ontology completeness, enum coverage, and the isomorphism edge cases (CLI ≡ MCP
  on errors, scalars, large payloads).

## Deliverables (concrete artifacts, every claim cited `path:line` + repro)

- `research/red-team/_ingest.md` — the ingestion ledger.
- `research/red-team/FINDINGS.md` — risks ranked by severity × likelihood; each
  with the Chesterton's-fence note, a concrete repro or scenario, and a cited
  `path:line`.
- `research/red-team/hardening-spec.md` — the proposed fix per risk (shape + test
  idea), ordered by ROI.

Publish one ready PR into `claude/extract-agency-plugin-o4JRc` per the protocol.
