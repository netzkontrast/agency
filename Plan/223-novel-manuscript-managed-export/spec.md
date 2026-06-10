---
spec_id: "223"
slug: novel-manuscript-managed-export
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "107"
depends_on: ["107", "124", "147", "209"]
vision_goals: [8, 7]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_manuscript_managed.py
---

# Spec 223 — novel manuscript Managed-Agent export

## Why

Spec 107 (novel-manuscript) ships the FormatDriver; Spec 124 added the
FakeFormatDriver + 3 export verbs, deferring the production
PandocFormatDriver (weasyprint) to Slice 2. Like the music audio driver
(Spec 209), heavy export (pandoc/weasyprint → EPUB/PDF) can run on a
Managed-Agent sandbox for users without local binaries (Goal 8) — the
zero-install publication path. The FormatDriver boundary already exists.

## Done When

- [ ] **A Managed-Agent FormatDriver** behind the Spec 107 boundary —
      dispatches pandoc/weasyprint export to a session (Spec 147),
      output files return via the session-outputs Files API.
- [ ] **The FakeFormatDriver stays the CI default** (zero binaries,
      Spec 124).
- [ ] **The export Artefact (Goal 7: files render from the graph)**
      records identically across backends.
- [ ] Test: the Managed-Agent driver exports an EPUB (mocked session);
      Fake fallback unchanged.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) — Managed-Agents bridge.
- Spec 209 (music audio MA driver) is the parallel pattern.
- Spec 124 (format-driver) is the parent.

## Open questions

1. Managed-Agent or document a local-pandoc install? **Recommend**:
   both — local when present (faster), Managed-Agent as the
   zero-install fallback.
