---
spec: 294
title: superclaude-port
status: Partial (Slice 1 shipped — surface import + gap-map)
depends_on: [292, 293]
clusters: [develop, navigate]
vision_goals: [4]
---

# Spec 294 — Port SuperClaude into agency (surface import + gap-map)

> User directive (2026-06-16): *"check the SuperClaude plugin and port everything
> completely over to agency."*

## Approach — the agency-native port

SuperClaude is a markdown-prompt plugin: 33 `/sc:*` commands + 27 agents, each a
prompt file. The agency-native reading of "port everything" (this session's
premise — *every file is also a prompt → a Document*) is a two-part move:

1. **Surface import** — ingest every SuperClaude command/agent `.md` as a
   prompt-audited `Document` (the source is external/read-only, so `ingest` is
   called with `write_anchor=False`). They become discoverable + queryable +
   round-trippable inside agency's graph.
2. **Coverage gap-map** — map each file against agency's live capability / verb /
   skill vocabulary, so the remaining native-port work is *scoped*, not guessed.

Shipped as a **reusable porter** — `develop.port_plugin(source, origin, kind)`
— not a one-off script; it ports ANY external prompt plugin.

## Live gap-map (run 2026-06-16)

**Commands (33 ported):** ~18 literal-name matches. **Agents (27 ported):** ~16
matches. The matcher is **name-token only** (conservative) — several apparent
gaps are already covered under a different agency name:

| SuperClaude | Already in agency as |
|---|---|
| `sc-implement` | `develop.implement` (skill) |
| `sc-test` | `develop.test` |
| `sc-git` | `branch.commit_smart` / `branch.finish_branch` |
| `sc-task` / `sc-spawn` | `subagent.*` / `delegate.fan_out` |
| `sc-troubleshoot` | `debug` discipline skill |
| `sc-load` / `sc-save` | `develop.session_init` / `session_resume` |
| `sc-design` | `brainstorm` / `spec-panel` / `develop` |

Meta/non-functional files (`README`, `sc-sc`, `sc-pm`, `IMPLEMENTATION_SUMMARY`,
`setup-mcp`) are dispatcher/doc shims with no verb to port.

**Genuine net-new candidates** (no clean agency equivalent): `sc-recommend`
(command recommender), `sc-select-tool` (MCP tool selector — partially in
dispatch-decision), `sc-business-panel` (covered: maps to the existing
`business-panel` agent), the specialist personas (`sc-python-expert`,
`sc-refactoring-expert`, `sc-requirements-analyst`, `sc-root-cause-analyst`,
`sc-learning-guide`) — these are agent *personas* that map most naturally to
`subagent.dispatch` parameterizations, not new core verbs.

## Done-When

- [x] `develop.port_plugin` ingests an external plugin's prompts as Documents
  (non-mutating — `write_anchor=False`) + emits a coverage gap-map.
- [x] `document.ingest` gains `write_anchor` so external/read-only files port
  without being mutated.
- [x] Ran live against SuperClaude — 60 files ported, gap-map produced.
- [x] 1 acceptance scenario (synthetic plugin dir); covered/gap classification.
- [ ] **Follow-up:** turn the genuine net-new candidates into native surface —
  most as `subagent.dispatch` persona parameterizations, a few as verbs
  (`recommend`). Each is a small, independently-shippable slice scoped by the
  gap-map above.

## Followup — Implementation Status (2026-06-16)

**Done.** `develop.port_plugin` + `document.ingest(write_anchor=…)`; live port of
SuperClaude (33 commands + 27 agents) with the gap-map captured above. The
import is reproducible on demand — the porter is the durable artefact, not a
committed DB dump.

**Still.** The net-new persona/verb slices (follow-up above). Most SuperClaude
*functionality* is already mirrored by agency's `analyze`/`thinking`/`intent`/
`develop`/`research`/`spec-panel`/`brainstorm` surface; the port's value is the
explicit coverage map + the reusable porter.
