---
spec_id: "075"
slug: shell-template-registry
status: draft
last_updated: 2026-06-06
owner: "@agency"
depends_on: ["073"]
affects:
  - agency/capabilities/shell.py        # define + graph-stored templates + query discovery
  - tests/test_shell.py
estimated_jules_sessions: 0
domain: capability
wave: 5
---

# Spec 075 — Definable, discoverable shell-template registry

## Why

Spec 073 shipped `shell` with a **hardcoded** `_TEMPLATES` dict — fine as a seed,
but the user directive (2026-06-06) wants more: *"define and create new shell
tools above the shell capability — that define not only a specific use-case but
also how to filter the output … put them into an MCP-discoverable surface."* And
CLAUDE.md rule #8 (no hardcoded values) says the registry should be **definable +
graph-stored**, not a frozen dict. A named template bundles a **command + an
output filter + a doc** — the agent calls `run(template="git-log")` instead of
re-composing the command and the token-trimming filter every time.

## Research first (the seed set)

Survey the agent's MOST COMMON bash commands across recent sessions (git status /
log / diff, grep/rg, find, ls, ruff, pytest slices, check-drift) and the filter
that makes each token-cheap (e.g. `git log --oneline -10` → `full`; `git status`
→ `short`; a long grep → `head:30`). Record the survey as a graph reflection; the
seed templates ship from it.

## Done When

- [ ] **`shell.define(name, command, filter, doc="", tags="")`** (act) — records a
  `Artefact{kind:"command-template", name, command, filter, doc, tags}` (graph-
  stored — no new node label, per canon; reuse Artefact). Re-defining a name
  supersedes. Validates the command's first token against the allowlist.
- [ ] **`shell.templates(query="")`** (transform) — the **discoverable surface**:
  returns built-in seeds ∪ graph-defined templates, ranked/filtered by `query`
  (matches name/doc/tags). This is MCP-discoverable (call the verb) WITHOUT
  bloating the tool catalog with one tool per template (which would defeat the
  token-economy goal).
- [ ] **`shell.run(template=)`** resolves graph templates first, then seeds.
- [ ] **A seeded set of common bash recipes** (from the research) shipped as
  documented defaults (rule-8 config), each with a token-saving filter.
- [ ] Tests: define→run round-trip; query discovery; graph template overrides a
  seed; allowlist still enforced on defined commands.
- [ ] `pytest` green; `check-drift` clean.

## Migration

Additive: the seed templates remain; `define` adds graph templates; `templates()`
gains the `query` param (default = all, as today). No break.

## Open Questions

1. **Discoverability depth.** v1: discoverable via `shell.templates(query)`. A v2
   could surface templates through the global `search` (tagging) IF it can be done
   without adding catalog entries — needs the CodeMode catalog story (cf. Spec 069).
2. **Per-user vs per-project templates.** Graph-stored = per-project (`.agency/`);
   a future per-user template store is out of scope.

## Evidence

- `agency/capabilities/shell.py` (the `_TEMPLATES` seed + `run`/`filter` this extends).
- CLAUDE.md rule #8 (no hardcoded values → definable registry).
- User directive (2026-06-06): definable/discoverable shell tools + output filters.
