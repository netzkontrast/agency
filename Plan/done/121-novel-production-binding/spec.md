---
spec_id: "121"
slug: novel-production-binding
status: shipped
state: done
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["101", "102", "115", "117"]
affects:
  - agency/capabilities/novel/drivers_production.py
  - agency/capabilities/novel/config.py
  - tests/test_novel_production.py
domain: novel / production / state
parent_spec: "101"
mvp-source:
  - "Plan/_research/novel-mvp-source/prior-specs/010-on-disk-layout.md (works/{author}/works/{genre}/{slug}/)"
  - "agency/capabilities/music/drivers_production.py (FileStateDriver reference impl)"
  - "agency/capabilities/music/config.py (MusicConfig 4-level resolution)"
---

# Spec 121 — Novel Production Binding (disk layout + StateDriver)

## Why

The novel cap is graph-only: every Slice 1-3 verb records nodes but
writes NO files. Music proved the production-binding pattern twice
(Spec 115 `FileStateDriver` + Spec 117 lazy auto-wiring); the novel cap
mirrors it so an actual novelist gets a real `works/` tree — chapters
as markdown with frontmatter, NCP JSON on disk, templates rendered with
substituted values (Spec 117's F3/F4/F5 render-fidelity lessons applied
from day one, not retrofitted).

## Done When

- [ ] **`NovelStateDriver` Protocol** declared with the Spec-102 method
      delta (create_novel_root, create_chapter, create_scene,
      list_chapters, rename_novel, novel_progress, get/update_session,
      read_ncp, write_ncp, list_ideas) + deterministic
      `FakeNovelStateDriver`.
- [ ] **`FileNovelStateDriver`** — real disk writes per prior-spec 010
      layout: `works/{author}/works/{genre}/{slug}/` with `work.md`,
      `premise.md`, `chapters/NN-slug.md`, `scenes/`, `ncp.json`,
      `dramatica.md`. Templates rendered WITH field substitution
      (title/author/genre/number land in frontmatter — Spec 117 F3
      lesson) and `status:` in frontmatter as the single source of
      truth (F4/F5 lessons — no sidecar files).
- [ ] **`NovelConfig`** — `.agency/novel-config.yaml` per-project +
      global fallback + env override (mirror MusicConfig's mtime-cached
      4-level resolution).
- [ ] **Lazy auto-wiring** at the MCP entrypoint mirroring Spec 117:
      `_require_drv` builds production drivers once on first miss,
      gated on the engine production flag; bare unit-test engines keep
      typed DEPENDENCY_MISSING.
- [ ] **Iteration-6 import verbs** (Slice 2 of this spec, may defer):
      `import_from_markdown`, `export_for_editor`,
      `reconcile_disk_with_graph`.
- [ ] Existing graph-only verbs gain optional disk side-effects when the
      driver is wired (graph stays canonical; files are the rendered
      view per CLAUDE.md rule 2).
- [ ] TODO.md row updated; Spec 102/106 "Still" carve-outs referencing
      StateDriver are pointed here.

## Design notes

- Two-store doctrine holds: graphqlite owns provenance; disk owns the
  rendered view; Spec 116 (SQLModel) may later own structured domain
  data — design the Protocol so a SQLModel-backed driver can drop in.
- Frontmatter parse/set via stdlib (mirror music `_fill_track_body`).

## Open questions

1. Genre directory level: prior-spec 010 has `works/{author}/works/{genre}/{slug}` —
   keep verbatim or flatten to `works/{author}/{slug}`? (Recommend:
   verbatim — byte-compatibility with the-agency-system's validators.)
2. Should `create_scene` write separate files or sections within the
   chapter file? (Prior-spec 010 says separate `scenes/` files.)

## Followup — Implementation Status (2026-06-10)

**Done (Slice 1):**
- `NovelConfig` shipped in `agency/capabilities/novel/config.py` — mirrors
  MusicConfig: 4-level resolution (`.agency/novel-config.yaml` → `~/.agency-novel/` →
  `$AGENCY_NOVEL_HOME` → `defaults()`), mtime-cached `load()`, idempotent
  `bootstrap()` that writes the default config + creates `content_root`.
  Minimal handrolled YAML parser falls back when PyYAML is missing.
- `FileNovelStateDriver` shipped in `drivers_production.py` — disk writes per
  prior-spec-010 layout `works/{author}/works/{genre}/{slug}/`. Render-fidelity
  applied from day one: F3 (template field substitution: `{{author_slug}}`,
  `{{work_slug}}`, `{{genre_slug}}`, `{{work_title}}`, `{{premise_logline}}`,
  `{{created}}`); F4 (frontmatter `status` round-trip via
  `_set_frontmatter_field`); F5 (template default `status: draft` matches
  what `create_novel` records). `create_work`, `update_work_field`,
  `create_chapter`, `list_chapters`, `update_chapter_field`, `read_ncp`,
  `write_ncp` shipped.
- Lazy auto-wiring mirrors Spec 117: `_production_enabled()` gates on
  `engine._novel_production`; `_autowire_novel_drivers()` builds
  `production_drivers(NovelConfig.bootstrap())` ONCE on first miss;
  `_require_drv` registers the bundle. Bare unit-test engines keep typed
  `DEPENDENCY_MISSING` contract — bounded blast radius.
- `create_novel(title, author, genre="novel")` extended with optional
  disk side-effect (`work_path` in return); `create_chapter` writes
  `chapters/NN-slug.md` when driver is wired. Genre property added to
  Novel node so chapter writes inherit the disk routing.
- MCP entrypoint (`agency/__main__.py`) flips `engine._novel_production = True`
  alongside the existing music flag — production runtime auto-wires both.

**Still (Slice 2 carve-out per spec):** iteration-6 import/export verbs
(`import_from_markdown`, `export_for_editor`, `reconcile_disk_with_graph`).
Deferred — Slice 1 closes the "write the bitwize-compatible tree from the
graph" half; Slice 2 closes the "load an existing tree back into the graph"
half. Author of the prior-spec-010 tree on disk → `reconcile_disk_with_graph`
in a future PR.

**Test:** 14 new tests (`tests/test_novel_production.py`) — config
defaults/load/bootstrap/mtime-cache, disk layout, template substitution,
frontmatter round-trip, chapter creation + listing, NCP round-trip, bare-engine
no-disk, production-engine writes-disk, bundle factory. 235 across
novel/naming/install green. Check-drift clean.

**Open Q resolutions:** Q1 — layout kept verbatim per prior-spec-010 (genre
sub-level preserved for byte-compatibility with the-agency-system validators).
Q2 — separate `scenes/` files (per prior-spec-010); scene verbs in Slice 2.
