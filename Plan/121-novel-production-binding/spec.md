---
spec_id: "121"
slug: novel-production-binding
status: draft
last_updated: 2026-06-09
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

## Followup

(Populated when the PR ships.)
