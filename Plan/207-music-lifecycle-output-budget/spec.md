---
spec_id: "207"
slug: music-lifecycle-output-budget
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "094"
depends_on: ["094", "146", "154", "160"]
vision_goals: [1]
affects:
  - agency/capabilities/music/_main.py
  - tests/test_music_lifecycle_budget.py
---

# Spec 207 — music lifecycle output-budget + cluster-file split

## Why

Spec 094 (music-lifecycle) ships the CRUD pipeline but stays Partial —
"per-cluster verb migration to `clusters/*.py` modules" deferred, and
its list verbs (`list_albums`, `list_tracks`, `album_progress`) can
return large payloads with no budget. The catalogue-listing verbs are
exactly the high-token output the charter's gap #1 targets. This
applies the output-budget discipline and lands the deferred file-split.

## Done When

- [ ] **`list_*` / `*_progress` verbs honor the output budget** (Spec
      146 prefix split + Spec 154 overflow capture + Spec 160 `--fields`).
- [ ] **The deferred `clusters/lifecycle.py` split lands** (094's
      standing migration) — verbs move out of `_main.py`.
- [ ] **094 row flips toward Shipped** once the split + budget land.
- [ ] Test: a 100-album list captures-and-recalls; `--fields` projects;
      the cluster module imports clean.
- [ ] TODO row + drift clean.

## Interconnects

- **output-budget chain** (146/154/160).
- Unblocks the batched cluster-file split (TODO row 129 note).

## Open questions

1. Split all clusters here or just lifecycle? **Recommend**: lifecycle
   first (it carries the migration); siblings split in their own
   enhancement (208-213).
