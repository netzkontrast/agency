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

- [ ] **Schema version stamped in the DB** + read on connect; a
      mismatch triggers migration.
- [ ] **Migrations as ordered scripts** under `agency/_migrations/`
      (numbered; each idempotent; each forward-only by default).
- [ ] **A migration is REQUIRED when an ontology Schema (Spec 153) is
      added or changed** — Spec 157 architecture-gate enforces.
- [ ] **Import (Spec 020) auto-migrates** an older dump on import.
- [ ] **Vendoring discipline (Spec 267) covers migration scripts.**
- [ ] Test: an old fixture DB migrates to current; export→import
      round-trip preserves; missing migration trips the gate.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 153 (schema coverage) triggers migration drafts.
- Spec 157 (architecture gate) enforces the requirement.
- Spec 267 (vendoring) covers the migration files.
