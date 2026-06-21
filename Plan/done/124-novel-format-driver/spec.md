---
spec_id: "124"
slug: novel-format-driver
status: shipped
state: done
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["107", "121"]
affects:
  - agency/capabilities/novel/drivers_production.py
  - agency/capabilities/novel/_main.py
  - tests/test_novel_format.py
domain: novel / manuscript / export
parent_spec: "101"
mvp-source:
  - "Plan/done/107-novel-manuscript-cluster/spec.md (FormatDriver design)"
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

## Followup — Implementation Status (2026-06-10)

**Done (Slice 1):**
- `FakeFormatDriver` shipped in `drivers_production.py` — `available_formats()`
  returns `["epub", "pdf", "docx"]`; `to_epub` / `to_pdf` / `to_docx` return
  deterministic paths (sha256 hash of the manuscript body for content-keyed
  paths under `/tmp/agency-novel-format/`) and record a `calls` log. Zero
  binaries; mirrors `FakeAudioDriver`'s pattern.
- `production_drivers(cfg)` bundle extended with `novel_format` — currently
  ships the fake; `_select_format_driver` is the swap point where Slice 2's
  `PandocFormatDriver` lands.
- `_NOVEL_DRIVER_NAMES` extended to `("novel_state", "novel_format")`;
  `_maybe_format_driver()` helper added alongside `_maybe_state_driver` via
  a new `_maybe_driver(name)` base.
- **3 export verbs** ship (`export_epub` / `export_pdf` / `export_docx`),
  all effects: render manuscript → hand to driver → record
  `Artefact(kind="published-manuscript", format, path, novel_id)` with
  SERVES intent + PRODUCES (intent → artefact) edges. Typed
  `DEPENDENCY_MISSING` when driver not wired.
- **`publication_gate(novel_id)`** terminal composite: combines
  `publish_ready_gate` + ≥ 1 `published-manuscript` Artefact present +
  `content_warnings` field declared on the Novel node (empty string OK —
  just must be SET so reviewers see a deliberate state).
- **`publish-prep` 4-phase walkable skill** registered: render → export →
  publication-gate → sign-off (hard). Phases bind to the real verbs per
  Spec 080 doctrine.

**Still (Slice 2 — deferred):**
- `PandocFormatDriver` production binding (pandoc for epub/docx; weasyprint
  for PDF). Per Open Q1, the recommendation stands: **weasyprint** —
  pip-installable, no system binary, stays in the Python graph.
- `[novel-format]` extras-deps entry in `pyproject.toml` once the prod
  driver ships.
- 4 publication-template port from bitwize source (query-letter / synopsis /
  blurb / back-cover) — Spec 107's existing renderers cover 3 of those
  already; the 4th (back-cover) is the carve-out.

**Open Q resolutions:** Q1 — weasyprint recommended for Slice 2 (pip-only).
Q2 — minimum-viable EPUB metadata (title/author/lang) confirmed; ONIX is
catalogue territory.

**Test:** 12 new tests (`tests/test_novel_format_driver.py`) — fake driver
format list + call recording + deterministic + content-keyed paths,
production_drivers bundle wiring, bare engine typed DEPENDENCY_MISSING,
production export writes Artefact, multi-format independence, publication
gate block-without-exports, gate pass-with-exports-and-declarations, skill
registration + verb registration. 247 across novel/naming/install green;
drift clean; lint clean.
