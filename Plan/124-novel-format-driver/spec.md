---
spec_id: "124"
slug: novel-format-driver
status: draft
last_updated: 2026-06-09
owner: "@agency"
depends_on: ["107", "121"]
affects:
  - agency/capabilities/novel/drivers_production.py
  - agency/capabilities/novel/_main.py
  - tests/test_novel_format.py
domain: novel / manuscript / export
parent_spec: "101"
mvp-source:
  - "Plan/107-novel-manuscript-cluster/spec.md (FormatDriver design)"
  - "agency/capabilities/music/drivers.py (FakeAudioDriver zero-binaries-in-CI pattern)"
---

# Spec 124 — Novel FormatDriver (epub / PDF / docx export)

## Why

Spec 107 shipped the 3 driver-free renderers (blurb / query-letter /
synopsis) but the actual publication formats need shell-outs (pandoc,
wkhtmltopdf, calibre). Music's audio cluster proved the pattern: a
Driver Protocol with a deterministic fake (zero binaries in CI) and a
production binding that shells out. The novel's last mile is identical
in shape.

## Done When

- [ ] **`FormatDriver` Protocol**: `to_epub(manuscript_md, meta) -> path`,
      `to_pdf(...)`, `to_docx(...)`, `available_formats() -> list`.
- [ ] **`FakeFormatDriver`** — deterministic: returns predictable paths,
      records call log, NO binaries (mirror FakeAudioDriver).
- [ ] **`PandocFormatDriver`** — production: pandoc for epub/docx,
      pandoc+wkhtmltopdf (or weasyprint) for PDF; degrades to typed
      DEPENDENCY_MISSING when binaries absent; wired via Spec 121's
      lazy auto-wiring + `[novel-format]` extra (AGENCY-DRIFT:
      deps-extras checklist applies).
- [ ] **3 export verbs**: `export_epub(novel_id)`, `export_pdf(novel_id)`,
      `export_docx(novel_id)` — each renders the manuscript (reuse
      `render_manuscript`), hands to driver, records `published-manuscript`
      Artefact with PRODUCES edge.
- [ ] **`publication_gate(novel_id)` composite** — `publish_ready_gate`
      AND ≥1 export format available AND front-matter complete (title /
      author / content-warnings declared). Terminal gate.
- [ ] **`publish-prep` walkable skill** (4-phase, hard gate at upload).
- [ ] **4 publication templates port** from bitwize source
      (query-letter / synopsis / blurb / back-cover) — verbatim where
      they exist, else derive from the shipped renderers.
- [ ] TODO.md row updated; Spec 107 "Still" carve-outs pointed here.

## Open questions

1. PDF engine: wkhtmltopdf (heavier, HTML-fidelity) vs weasyprint
   (pip-installable)? (Recommend: weasyprint — stays in the Python
   dependency graph, no system binary.)
2. EPUB metadata: minimum viable (title/author/lang) or full ONIX
   subset? (Recommend: minimum viable; ONIX is catalogue territory.)

## Followup

(Populated when the PR ships.)
