---
spec_id: "020"
slug: central-graph-db
status: complete
last_updated: 2026-06-03
version: 2
owner: "@agency"
depends_on: []
affects:
  - agency/__main__.py            # DB resolution order (--db > env > local > home)
  - agency/cli.py                  # same default resolution
  - agency/install.py              # add .agency/ scaffold to the install
  - bin/agency-install             # bash install path
  - .gitattributes                 # mark .agency/session.db as binary
  - examples/                      # docs example: working in a target repo
estimated_jules_sessions: 0
domain: substrate
wave: 3
---

# Spec 020 — Central graph DB (`.agency/session.db`)

## Why

The graph IS the moat (GOALS.md goal #2; CORE.md Memory). For the moat
to work across sessions, the DB has to **live somewhere persistent the
team agrees on** — not ephemeral `/tmp/*.db` paths (what this session
used) and not just `~/.agency.db` (system-wide, per-user, leaks across
projects).

Two requirements collapse into one design:

1. **Cross-session learning extraction.** `reflect.search("COMPLETED")`
   from Tuesday's session should find observations Monday's session
   recorded. That requires a stable DB location PER PROJECT, surviving
   process restarts + clones + branch switches.
2. **Plugin-installed-in-target-repo case (Mode B).** When the agency
   plugin is installed in someone else's repo (per AGENCY_PROTOCOL Mode B),
   the DB lives in THAT repo so the project's learnings travel with the
   project, not with the developer's home directory.

The canonical location: **`.agency/session.db` at the project root**,
committed to git alongside the project's code. Provenance becomes
shareable; cross-session memory becomes a team asset.

## Done When

- [ ] **DB path resolution order** (in `agency/__main__.py`,
  `agency/cli.py`, every entry point):
  1. `--db <path>` CLI flag (explicit override; for testing, etc).
  2. `AGENCY_DB` env var (per-session override).
  3. `./.agency/session.db` (CWD-local — the default in any project).
  4. `~/.agency.db` (system fallback — only when neither CWD nor env
     resolves; e.g. running `python -m agency` from $HOME directly).
- [ ] **`agency/install.py` creates `.agency/` in the install CWD**
  - `.agency/session.db` — the graph (created empty on first install
    if missing).
  - `.agency/README.md` — explains the dir + the commit-it convention
    + how to inspect (`sqlite3 .agency/session.db`) + reset
    (`rm .agency/session.db && python -m agency.install`).
  - `.agency/.gitkeep` — keeps the dir tracked even when DB is empty.
- [ ] **`.gitattributes` marks the DB as binary**
  ```
  .agency/session.db binary
  .agency/session.db diff=sqlite
  ```
  The `diff=sqlite` driver is OPTIONAL (requires `git config
  diff.sqlite.textconv "sqlite3 \$1 .dump"` per-developer); marked as
  binary prevents git from trying to merge raw bytes.
- [ ] **Merge-conflict survivable.** When two branches both modify the
  DB and merge, the conflict is binary. Recovery: a `dogfood.export
  <path.json>` verb that dumps the graph to a portable JSON file (Spec
  017's `dogfood.render` pattern), so a conflicted DB can be regenerated
  by replaying both branches' JSON exports. Out of scope to AUTOMATE
  conflict resolution; the export + manual replay path is the v1 fallback.
- [ ] **`bin/agency-install` (existing bash wrapper) calls
  `python -m agency.install --scaffold-db`** — the new flag triggers
  the `.agency/` directory creation. Existing call paths (`pip install
  -e .` workflow) get the scaffold automatically too.
- [ ] **Tests** — `tests/test_db_path_resolution.py`:
  - `--db` flag overrides env + local + home.
  - `AGENCY_DB` overrides local + home.
  - In a CWD with `.agency/session.db`, that path is selected.
  - In a CWD without `.agency/`, home fallback fires.
  - `install.py --scaffold-db` creates `.agency/{session.db,README.md,.gitkeep}`.
  - `install.py --scaffold-db` adds `.gitattributes` entry if absent;
    idempotent if present.

## Files

- **Modify:**
  - `agency/__main__.py` — DB resolution order at line 20.
  - `agency/cli.py` — same resolution, applied wherever `--db` defaults today.
  - `agency/install.py` — add `--scaffold-db` flag + the four-file
    `.agency/` scaffold.
  - `bin/agency-install` — call `python -m agency.install --scaffold-db`.
  - `README.md` — document the `.agency/` convention + commit guidance.
  - `AGENCY_PROTOCOL.md` — add a note: "the graph lives at
    `.agency/session.db`; treat it as part of the repo's provenance."
- **Create:**
  - `.gitattributes` (if missing) with the DB binary marker.
  - `tests/test_db_path_resolution.py` (~10 asserts).
  - `agency/capabilities/dogfood.py` — add `export(path)` verb (the
    JSON dump fallback for merge conflicts). Small (~30 LOC).

## Open Questions

1. **Commit the DB OR keep it gitignored + commit JSON exports only?**
   The user's directive is COMMIT THE DB. Direct commit is simplest;
   merge conflicts are the cost. JSON-only commits trade conflict
   handling for "the DB isn't the source of truth in git, the exports
   are." Recommend: **commit the binary DB** for v1 + add the export
   fallback for conflict recovery. Revisit if conflicts become frequent.

2. **What about `.agency/session.db` in the AGENCY REPO ITSELF?**
   Mode A (dogfood). Should THIS repo also commit its DB? Yes — the
   agency's own observations + skill walks + Reflection nodes are the
   richest dataset we have. Make the `.agency/` scaffold + git commit
   the FIRST landed change of Spec 020's implementation.

3. **Per-branch vs per-repo DB?** A long-running feature branch
   accumulates observations distinct from main; on merge they collide.
   Recommend: per-repo (single `.agency/session.db`); rely on
   bi-temporal append-only semantics — old records survive merge
   conflicts as long as both branches' inserts can replay against
   the unified DB.

4. **Sensitive data?** What if a Reflection or Intent text contains
   secrets (API keys, tokens, internal customer names)? Committed DB
   would expose them.
   **Recommend: a `dogfood.scrub` filter that runs before commit**
   (pre-commit hook), redacts based on regex (env-configurable) +
   the standard secret patterns. Documented as orchestrator
   responsibility for v1; tooled-up in v2.

5. **DB size growth.** Append-only means monotonically growing.
   Recommend: an `archive` verb that snapshots + truncates the DB at
   major releases (e.g. v0.2, v0.3); old DBs archived under
   `.agency/archive/session-<tag>.db`. Out of scope for v1.

6. **Discovery: `.agency/` vs `.cache/` vs `.local/` vs root-level**
   `.agency/session.db`? `.agency/` mirrors XDG-style + clearly
   project-scoped. Root-level `.session.db` would be cleaner for tab-
   completion but signals "throwaway" via the dot-prefix without a
   context dir. Recommend `.agency/`.

## Evidence

- This session's `/tmp/*.db` proliferation (each spec dispatch + each
  reflect.note demo used a different DB; observations didn't accumulate
  across `python` invocations).
- `agency/__main__.py:20` — the current `AGENCY_DB` env var + home
  fallback; the foundation Spec 020 extends.
- `docs/vision/GOALS.md` goal #2 (provenance as a free byproduct;
  the graph IS the moat) + goal #6 (doctrine evolves through
  dogfooding — needs persistence).
- `AGENCY_PROTOCOL.md` §8 (bi-temporal record; assumes DB persists).
- `agency/memory.py:_intent_chain` — the cross-amendment walker that
  proves cross-session continuity is already designed-for in the graph.

## Followup — Implementation Status (2026-06-03)

**Verdict:** Shipped — DB path resolution, .agency/ scaffold, .gitattributes
binary marker, MCP/CLI convergence, AND `dogfood.export` JSON dump all
live. 10 spec tests for export green; live wire dogfood emitted a
55KB / 112-node / 114-edge JSON from the agency repo's own DB.

### Done (this finish-pass)
- `dogfood.export(path)` transform verb — Spec 020 line 69-73 fallback
  for merge-conflict recovery.
  - Default path: `.agency/export-<unix-ns>.json` (ns-precision avoids
    collision when called back-to-back; sc:sc-analyze F6 review fix).
  - Full bi-temporal history capture: MATCH (n) RETURN n returns
    superseded nodes alongside current ones — correct for replay
    (sc:sc-analyze F1 review fix; updated docstring to match).
  - JSON shape: `{version=1, generated_at, nodes:[{id,label,properties}],
    edges:[{from,to,type,properties}]}`. indent=2 + sort_keys=True for
    diffability. Triple-fallback edge-type extraction handles graphqlite
    variant keys (type/rel_type/relationship).
- Returns `{path, nodes, edges, bytes}` — caller sees the file location
  + the metrics needed for sanity-check or commit decision.
- v1 ships EXPORT only; matching `dogfood.import` (replay JSON into
  fresh DB preserving original ids + vfrom/vto windows) is v2 follow-up
  per docstring note.

### Tests (tests/test_dogfood_export.py — 10 tests)
- export verb registered as dogfood capability verb
- payload shape: {path, nodes, edges, bytes}
- file is well-formed JSON with {version, nodes, edges} keys
- Reflection nodes captured with plan_slug property (round-trip)
- Intent nodes captured with Spec 048 owner + parent_intent_id
- edges captured with type (OBSERVED_DURING + SERVES)
- default path defaults to .agency/export-<ns>.json (abspath)
- transform purity (no graph writes)
- sc:sc-analyze F6 regression: ns-precision path avoids collision
  between back-to-back calls
- empty-graph export still produces valid JSON with bootstrap intent

### sc:sc-analyze review applied (3 actionable findings)
- F1 (warn) — docstring claimed "current snapshot only" but query had
  no vto filter. Switched to FULL history with documented rationale
  for merge-recovery.
- F3 (warn) — recovery story coherence: documented v2 import-verb
  follow-up in the docstring.
- F6 (warn) — collision risk on time.time(): switched to time.time_ns
  + regression test.

### Cluster-coherence (Spec 047)
- C08 (Memory) — closes the partial substrate work; bi-temporal
  graph now durably exportable.
- C09 (Git) — JSON exports are diff-friendly + commit-friendly when
  the binary DB conflict path needs human resolution.

## Followup — v2 dogfood.import (2026-06-03)

**Verdict:** Shipped.

### Done
- `dogfood.import(path)` verb added (role=effect; the import bites
  the filesystem then mutates the graph).
- Direct `g.upsert_node` / `g.upsert_edge` calls — bypass `record()`
  to preserve the original `vfrom` / `vto` window verbatim.
- Logical-clock advance after import (memory._tick = max(imported
  vfrom/vto)) so subsequent writes don't reuse stale ticks and
  overlap an imported node's window.
- `@verb(name=...)` decorator extension to register `import_`-the-
  Python-method as `import`-the-verb (Python-keyword collision; one
  decorator-level change in `agency/capability.py`).
- Substrate-tool brief-slicing parity in `Engine.build_mcp` —
  walks `mcp.providers[*]._components`, slices any tool's
  description that isn't already a brief.
- Closes merge-conflict recovery loop: branch A exports → branch B
  imports → continues; OR branches both export, merge JSONs replay
  into fresh DB.

### Tests (tests/test_dogfood_import.py — 10 tests)
- verb registration
- payload shape (imported_nodes / imported_edges / version)
- rejects unsupported version
- raises FileNotFoundError on missing path
- preserves node ids
- preserves Reflection properties
- preserves vfrom/vto window
- recreates edges (SERVES / OBSERVED_DURING)
- round-trip: export → fresh DB → import → re-export → original ids
  are subset of re-exported ids
- clock advances past max(vfrom, vto)

### Cluster-coherence (Spec 047)
- C08 (Memory) — closes the symmetric write side of the export.
- C13 (Plugin/MCP Authoring) — substrate brief-slicing parity
  closes the search-budget asymmetry between `@mcp.tool`-decorated
  substrate verbs and capability verbs.

## Followup — Original Implementation Status (2026-05-31)

> Consolidation pass on branch `claude/plan-spec-review-74gHM`. Frontmatter `status:` may be stale; this section reflects verified code state.

**Verdict:** Partially implemented

### Done
- **DB path resolution order** fully implemented in `agency/_db_path.py` (`resolve_db_path()`): explicit → `AGENCY_DB` env → `./.agency/session.db` (if dir exists) → `~/.agency.db`. Wired into `agency/__main__.py:22` and `agency/cli.py:67`.
- **`agency/install.py` scaffold** complete: `scaffold_agency_dir()` (line 302) creates `.agency/`, `.gitkeep`, `README.md`; `update_gitattributes()` (line 322) appends the binary marker; `scaffold_db()` (line 341) ties both together. `--scaffold-db` flag wired at line 478.
- **`bin/agency-install`** calls `python -m agency.install --scaffold-db "$ROOT"` (line 49).
- **`.gitattributes`** present at repo root with the required binary marker (`agency/session.db binary` + `diff=sqlite`), written by install and committed.
- **`.agency/session.db` committed** to the repo (tracked via `git ls-files`; commits `aa345ab` + `ae0b9ba`).
- **Tests shipped**: `tests/test_db_path_resolution.py` (10 assertions covering all four resolution levels + scaffold idempotency) and `tests/test_install_db_path.py` (MCP/CLI DB convergence assertion).
- **MCP/CLI convergence fix**: `_mcp_config()` emits `AGENCY_DB: ${CLAUDE_PROJECT_DIR}/.agency/session.db` so both surfaces write one graph (reflection:9cd97a38).

### Still to implement
- **`dogfood.export(path)` verb** — the JSON-dump fallback for merge-conflict recovery (spec's "Files → Create" item). Not present in `agency/capabilities/dogfood.py`.
- **`.agency/.gitkeep`** — not present in the live `.agency/` dir (only `README.md` and `session.db` appear under `git ls-files .agency/`). The scaffold creates it on fresh installs but the repo's own `.agency/` was set up before the scaffold wrote `.gitkeep`.
- **Merge-conflict documented recovery path** — the `dogfood.export` + replay doc is blocked on the export verb above.

### Refinement needed (given later specs)
- Spec 021 extends the `.agency/` convention with `monitor.log`; it should add `.agency/monitor.log*` to `.gitignore` via the scaffold (minor addition to `scaffold_agency_dir`).
- Spec 017 (`dogfood.note`/`dogfood.render`) relies on 020's persistent DB being present — the substrate dependency is met.

### Evidence
- code: `agency/_db_path.py` (full resolution logic); `agency/install.py:302,322,341,478`; `agency/__main__.py:22`; `agency/cli.py:67`; `.gitattributes`
- tests: `tests/test_db_path_resolution.py`, `tests/test_install_db_path.py`
- commits/notes: `aa345ab` ("track .agency/*.db — Spec 020 doctrine"), `ae0b9ba` ("refresh dogfood .agency/session.db")
