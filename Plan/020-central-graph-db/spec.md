---
spec_id: "020"
slug: central-graph-db
status: draft
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
