---
spec_id: "273"
slug: central-graph-db-migrations
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "020"
depends_on: ["020", "153", "157", "267"]
vision_goals: [2, 7]
affects:
  - agency/_db.py
  - scripts/migrate-graph
  - tests/test_graph_migrations.py
---

# Spec 273 — central graph DB: migrations + schema versioning

## Why

Spec 020 ships `.agency/session.db` + import/export round-trip. As the
ontology grows (every wave adds nodes + edges + enums), the DB schema
implicitly versions — but there's no MIGRATION path. A user with an
old session.db who pulls a new agency build risks silent breakage. The
graph IS the store (Goal 7); migrations are the path that keeps it
durable across schema evolution.

## Done When

- [ ] **Schema version stamped in the DB** as a `_schema_meta` row
      `{version: int, applied_at: iso8601, sha: str}`; read on connect;
      a mismatch where `db.version < code.version` triggers migration,
      `db.version > code.version` raises `SchemaAhead` (refuse to open).
- [ ] **Migrations as ordered scripts** under `agency/_migrations/`
      (numbered `NNNN_slug.py`; each idempotent; each forward-only by
      default; each carries `up(conn)` + optional `verify(conn) -> bool`).
- [ ] **A migration is REQUIRED when an ontology Schema (Spec 153) is
      added or changed** — Spec 157 architecture-gate fails the build
      when `set(live_schemas.sha) != set(latest_migration.schemas.sha)`.
- [ ] **Import (Spec 020) auto-migrates** an older dump on import; the
      migration log appends a `MigrationApplied` MonitorEvent (Spec 274).
- [ ] **Vendoring discipline (Spec 267) covers migration scripts** —
      migrations are content-addressed and immutable post-merge.
- [ ] **Invariants** (CLAUDE.md rule 8):
      - `db.schema_version == max(applied_migration.number)` always —
        no skipped migrations.
      - For every ontology Schema change between release N and N+1,
        `exists(migration where touches(schema))` — the gate.
      - Migration sequence is monotone: `migration[i].number <
        migration[i+1].number` and no gaps (`migration[i+1].number ==
        migration[i].number + 1`).
      - Round-trip equivalence: `import(export(db)).nodes ==
        db.nodes` (set equality, not ordering) post-migration.
- [ ] **Failure modes table** — see below.
- [ ] Test: an old fixture DB migrates to current; export→import
      round-trip preserves all nodes + edges; missing migration trips
      Spec 157 gate with file:line of the offending Schema; a
      `db.version > code.version` opens raises `SchemaAhead`.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  .agency/session.db at schema_version=7 and code at
        schema_version=9 (two new migrations: 0008_add_monitor_event,
        0009_add_driver_field)
When:   Engine() opens the DB
Then:   0008 then 0009 run in order; each wraps in a transaction;
        verify() confirms post-state; _schema_meta updates to {version:9,
        sha: hash(migrations[0:9])}; MigrationApplied MonitorEvent
        emits per step

Given:  a contributor adds a new node type to agency/ontology/ but
        forgets the migration
When:   CI runs scripts/check-drift + Spec 157 architecture gate
Then:   gate fails with file:line of the new Schema + the required
        migration filename (0010_<slug>.py); the build is red

Given:  .agency/session.db carries schema_version=12 but the installed
        code is schema_version=9 (user downgraded)
When:   Engine() opens
Then:   SchemaAhead raised — refuse to open + remediation hint:
        "upgrade agency OR use a separate session.db"; never run a
        rollback (forward-only doctrine)
```

## Failure modes

| # | Failure | Detection | Response |
|---|---|---|---|
| F1 | Migration script raises mid-run | Transaction wrap | Rollback transaction; leave `_schema_meta` at prior version; surface error with migration filename |
| F2 | Two migrations share a number (merge collision) | Loader sort + uniqueness check | Refuse to start; name both files in error |
| F3 | New ontology Schema with no migration | Spec 157 gate diff | CI red; gate names the Schema + suggested migration filename |
| F4 | Import of a dump newer than installed code | Header version > code version | Raise `DumpAhead`; refuse import; suggest agency upgrade |
| F5 | Migration `verify()` returns False post-run | Post-step check | Treat as F1; rollback; do NOT advance `_schema_meta` |
| F6 | Idempotency violated (re-run produces a different state) | Spec 153 fixture re-run | Build-time test; flag the migration as non-idempotent |

## Interconnects

- Spec 020 (parent) — central graph DB + import/export round-trip.
- Spec 153 (schema coverage) triggers migration drafts.
- Spec 157 (architecture gate) enforces the requirement.
- Spec 267 (vendoring) covers the migration files.
- Spec 274 (structured monitor) records MigrationApplied events for
  postmortem queryability.
- Spec 271 (Jules/MA bridge) — `_schema_meta` reads MUST tolerate the
  new `driver` field on MonitorEvent without a migration churn.
- **Graph-as-store** (Goal 7) durability + **provenance** (Goal 2)
  extended to schema evolution.

## Open questions

1. **Forward-only vs reversible.** Should migrations carry `down()`?
   **Recommend**: forward-only by default; reversible is opt-in for
   migrations that drop columns. Doctrine: the graph grows; rollbacks
   invite data loss. A user who needs the old shape uses the export
   from before the upgrade.
2. **Migration runner — sync or async?** **Recommend**: sync on
   connect — opening a DB at version N-2 blocks until migrated, with a
   progress line per step. Async invites a race where the orchestrator
   queries pre-migration state.
3. **Where do migration tests live?** **Recommend**: `tests/migrations/`
   with one fixture DB per version checkpoint; CI runs the full chain
   on every PR. Fixture DBs are content-addressed via Spec 267.
