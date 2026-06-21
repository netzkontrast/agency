---
spec_id: "385"
slug: quality-migration
status: draft
state: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [4, 2]
depends_on: ["379", "360", "381", "292"]
domain: analyze
wave: brooks-port
parent_spec: "379"
---

# Spec 385 — Migration: brooks-lint plugin → native agency quality surface

> Part of the Spec 379 brooks-lint port. This slice is the **transition path** for
> an existing brooks-lint user: convert the two sidecar files
> (`.brooks-lint.yaml`, `.brooks-lint-history.json`) into agency's config + graph,
> and define the deinstall + vendored-data versioning timeline. Opened by the
> spec-panel critique (Newman: "the migration/versioning path is the completeness
> gap"; 2026-06-20).

## Why

Spec 379 "replaces brooks-lint itself" — but a project that *already runs*
brooks-lint has state on disk: a `.brooks-lint.yaml` config and a
`.brooks-lint-history.json` trend. The port specs (381) say these "disappear" —
correct as an end-state, but a user mid-stream needs them **carried over**, not
dropped. Without a migration the port is a rewrite the user must redo by hand;
with it, `develop.review` on day one honours their tuning + shows their trend.

This is the same discipline agency applied when a sidecar became a graph node
elsewhere (Spec 195/289 portability) — a one-time importer, not a permanent shim.

## Design

### 1. Config migration — `.brooks-lint.yaml` → `.agency/config.yaml quality:`

`develop.migrate_quality_config()` (`role="effect"`) — a one-time importer:

- Reads `.brooks-lint.yaml` (the brooks `common.md` schema: `disable`, `severity`,
  `ignore`, `focus`, `strictness`, `suppress`, `custom_risks`).
- Maps each key onto the unified `quality:` block (381 §2), preserving semantics
  (`strictness`→`quality.strictness`, `suppress`→`Suppression` nodes via
  `intent.triage`, `custom_risks`→`quality.custom_risks`).
- Writes the `quality:` block to `.agency/config.yaml`, leaving `.brooks-lint.yaml`
  in place (non-destructive — keep-both, Spec 292), and reports a diff.
- **Compat window:** 381 already reads `.brooks-lint.yaml` for one release
  (381 OQ1), agency config winning on conflict. This verb makes the migration
  *explicit + durable*; the auto-read is the *safety net* during the window. After
  the window, the auto-read is removed (a 381 follow-up) and the file is inert.

### 2. History migration — `.brooks-lint-history.json` → `QualityRun` nodes

`develop.migrate_quality_history()` (`role="effect"`):

- Reads the JSON array (`{date, mode, score, findings:{critical,warning,
  suggestion}, scope}` per brooks `common.md` History Tracking).
- Mints one `QualityRun{mode, scope, score, critical, warning, suggestion,
  recorded_at, status: complete}` per record (381 §3), back-dating `recorded_at`
  from the record's `date` so the **bi-temporal trend is preserved** — the
  imported runs slot into the timeline at their original dates, and the next
  `develop.review` shows a continuous trend across the migration boundary.
- Idempotent: a content hash per record prevents double-import on re-run
  (keep-both — re-running never duplicates).

### 3. Plugin deinstall timeline

The external brooks-lint Claude Code plugin and the native surface must not
double-fire (two `/brooks-review` handlers). The ordered hand-off:

1. **Native lands** (360–384 shipped) — `develop.review` live, both surfaces
   coexist (the native uses `quality-*` names; brooks uses `/brooks-*` — Spec 380
   keeps the `/brooks-*` aliases for muscle memory, so no collision).
2. **Migrate** — run §1 + §2 once per project.
3. **Deinstall** — `/plugin uninstall brooks-lint` once the native surface is
   verified (the `quality-override`/trend/SARIF parity checks pass).
4. The brooks-lint **repo stays** as the cited upstream the data is vendored from
   (Spec 379 — like ponytail for `frugal`); deinstalling the *plugin* ≠ deleting
   the *reference*.

### 4. Vendored-data versioning (cross-ref — owned by 360/383)

The `_source: brooks-lint@<rev>` provenance keys on `decay-risks.json` (360) and
`source-coverage.json` (383), checked by `check-drift`, are the *forward*
versioning path (upstream changes → flagged stale). This slice only consumes them:
`migrate_*` records which upstream rev it migrated *from*, so a later re-vendor can
diff. No new versioning machinery here — just the provenance read.

### What this slice does NOT do

- No new config schema (381 owns `quality:`) — it *writes* it from the legacy file.
- No new `QualityRun`/`Suppression` shape (381) — it *imports into* them.
- No destructive deletion of the legacy files (keep-both; the user removes them).
- No permanent dual-read shim — the 381 auto-read is a bounded compat window; this
  verb is the durable migration that lets the window close.
- No re-vendoring of the decay-risk data (360/383 own the data + its `_source`).

## Acceptance (Gherkin)

```gherkin
Scenario: legacy config migrates to the quality block, non-destructively
  Given a .brooks-lint.yaml with strictness legacy-friendly and disable [T5]
  When I run develop.migrate_quality_config
  Then .agency/config.yaml quality.strictness is legacy-friendly
  And quality.disable includes T5
  And .brooks-lint.yaml still exists (keep-both)

Scenario: history migrates into back-dated QualityRun nodes preserving the trend
  Given a .brooks-lint-history.json with three review records over three dates
  When I run develop.migrate_quality_history
  Then three QualityRun nodes exist with recorded_at back-dated to the record dates
  And the next develop.review trend line is continuous across the migration

Scenario: history migration is idempotent
  When I run develop.migrate_quality_history twice
  Then no QualityRun record is duplicated (content-hash dedup)

Scenario: suppress entries become Suppression nodes via intent.triage
  Given a .brooks-lint.yaml suppress entry for R3 in src/util.py
  When I run develop.migrate_quality_config
  Then a Suppression node (intent ontology) records R3 + the pattern
  And the next review downgrades that finding (381 §4)

Scenario: the native + legacy surfaces do not collide pre-deinstall
  Given the brooks-lint plugin is still installed
  Then /brooks-review (alias) and develop.review both resolve without double-firing
```

## Open questions

- **OQ1** — one combined `develop.migrate_quality(...)` verb or the two split
  (`_config` + `_history`)? (Default: split — different inputs, different idempotency
  models; a thin `migrate_quality` can compose both.)
- **OQ2** — should migration be auto-offered on first `develop.review` when a
  `.brooks-lint.*` file is detected, or stay explicit? (Default: detect + *suggest*
  in the report ("legacy brooks-lint state found — run develop.migrate_quality"),
  never auto-run an effect.)

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — the migration/transition slice of the Spec 379 program,
opened by the spec-panel critique (Newman — the completeness gap the critical-
thinking pass and the panel both flagged). No code yet. Reuses 381 (`quality:`
config + `QualityRun`/`Suppression`), `intent.triage` (381 §4), keep-both (292).
Two one-time importer verbs (`migrate_quality_config` + `migrate_quality_history`,
both `role="effect"`, idempotent, non-destructive) + the deinstall timeline +
the vendored-data `_source` read. Lands alongside 383/384 (late — needs 381's
config + nodes live). Next (after 381): the two importers + the first-review
detect-and-suggest, RED→GREEN against the §Acceptance scenarios.
