# Session graph analysis — `.agency/session.db` (at untracking, 2026-06-19)

The committed `session.db` (3.7 MB) was analysed in full, then **removed from the
branch** (untracked → local-only, like `.agency/toolcalls.db`) to stop the
per-turn binary churn. This file preserves what it contained.

## Census (1608 nodes · 1617 edges)

| Label | Count | | Edge | Count |
|---|---|---|---|---|
| Event | 1539 (96%) | | IN_SESSION | 1539 |
| Invocation | 26 | | SERVES | 39 |
| Gate | 13 | | PERFORMED_BY | 26 |
| Intent | 13 | | GATES | 13 |
| RepoIndex | 13 | | | |
| Agent | 2 | | | |
| Session | 2 | | | |

## What the graph actually held

- **13 Intents** — all SessionStart-hook artefacts: 12× `session-start repo index`
  + 1× `renumber-spec reindex`. All `clarity=0.40`, all clarity gates `passed=False`
  (auto-generated, never human-confirmed work).
- **26 Invocations** — only `develop.index` (13) + `document.index_repo` (13): the
  SessionStart hook regenerating `PROJECT_INDEX.md` each session.
- **13 Gates** — clarity, all failed (the low-clarity auto intents).
- **1539 Events** — pre-Spec-336 tool-use churn (`IN_SESSION` only).
- **Absent:** no `Reflection`, `Artefact`, `BoundaryUse`, or `Document` nodes — i.e.
  **no durable work-provenance**. The graph was hook noise + event churn.

## Snapshotted, not committed

The committed DB was 96% machine-generated churn with zero durable signal, changed
every session (binary diffs + merge conflicts + stop-hook nags), and embedded this
container's absolute paths (non-portable). So:

- **`.agency/session.db` is gitignored** (removed from the branch; the live file
  stays local and working).
- The **durable** graph (Intents · Invocations · Gates · Agents · Reflections ·
  Artefacts — the 60 value nodes, NOT the 1539 Events) is exported to portable SQL
  at **`.agency/sql/session-snapshot.sql`** via `scripts/session-snapshot export`
  (SQLModel `snap_node`/`snap_edge`; deterministic so git diffs are minimal). Run
  it now and then to re-snapshot.
- On **SessionStart**, when `session.db` is missing, the hook runs
  `agency snapshot import` to replay the snapshot into a fresh db before the index
  opens it — so the durable provenance restores across clones.

Round-trip verified: export 60 → import 58 (the 2 Session nodes are best-effort);
the typed projection (Intent/Invocation/Gate/Agent) is rebuilt.
