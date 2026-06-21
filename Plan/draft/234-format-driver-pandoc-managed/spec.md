---
spec_id: "234"
slug: format-driver-pandoc-managed
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "124"
depends_on: ["124", "223", "147", "002"]
vision_goals: [8, 7]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_format_driver_pandoc.py
---

# Spec 234 — format-driver Slice 2 (Pandoc + Managed-Agent)

## Why

Spec 124 ships FakeFormatDriver; Slice 2 names "PandocFormatDriver
(weasyprint per Open Q1) + `[novel-format]` extra + back-cover template
port". Spec 223 already drafted the Managed-Agent path. This ships both:
local Pandoc when present, Managed-Agent fallback for zero-install.

## Done When

- [ ] **`PandocFormatDriver`** behind the Spec 002 boundary returning
      `ExportArtefact = {path: Path, format: Literal["epub","pdf","docx"],
      bytes: int, sha256: str, backend: Literal["pandoc","managed"]}` —
      pandoc + weasyprint for EPUB/PDF/DOCX; `[novel-format]` extra.
      Invariant: `bytes == path.stat().st_size` AND `sha256` matches the
      file contents after write.
- [ ] **Managed-Agent fallback** (Spec 223) when the local extra absent —
      invariant: `ExportArtefact.format` and `ExportArtefact.sha256`
      structure are IDENTICAL across backends for the same novel input;
      ONLY `backend` and the precise bytes may differ (rendering engines
      differ). The artefact SHAPE is byte-identical, not the bytes.
- [ ] **Back-cover template ported**; Artefacts identical across backends.
- [ ] **Backend selection is DERIVED** — invariant: `which("pandoc")` +
      `import weasyprint` both succeed → backend="pandoc"; either fails
      → backend="managed"; never read from a config flag. Reported via
      `agency_doctor` (Spec 231).
- [ ] **Failure modes** — Pandoc subprocess timeout → `Codes.EXPORT_TIMEOUT`
      with elapsed-ms; Managed-Agent unreachable (Spec 147 Driver down)
      → `Codes.DRIVER_UNAVAILABLE`, surfaced as a doctor hint;
      template-render error (Jinja undefined) → `Codes.TEMPLATE_INVALID`
      naming the missing variable, never a partial file.
- [ ] Test: each backend exports a fixture novel; artefacts match shape.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a fixture novel with the [novel-format] extra installed
When:   format.export(novel_id, format="epub") runs
Then:   ExportArtefact.backend == "pandoc" AND
        ExportArtefact.bytes == path.stat().st_size AND
        ExportArtefact.format == "epub" AND
        sha256 matches file contents

Given:  same fixture, [novel-format] NOT installed, Managed-Agent reachable
When:   format.export(novel_id, format="epub") runs
Then:   ExportArtefact.backend == "managed" AND
        ExportArtefact.format == "epub" AND
        the artefact shape matches the pandoc-path artefact (same keys,
        same types) AND a doctor hint names the pip-install command
```

## Interconnects

- Spec 223 (MA export) is the fallback · **LLM-driver chain** (147).
- Spec 002 boundary; **Goal 7** files-render-from-graph.
- Spec 231 (novel-doctor) — backend selection surfaces as drivers_wired.
- Spec 235 (typed paths) — Artefact provenance graph: Novel→PRODUCES→
  ExportArtefact traversed for "what was exported when" queries.
- Spec 236 (research ingest) — output artefacts share the sha256 +
  bytes hygiene with research corpus entries.

## Open questions

1. **Pandoc version pin.** Pin minor version or accept any pandoc ≥ 3.0?
   **Recommend:** accept ≥ 3.0, record actual version in
   `ExportArtefact.metadata` so drift is visible later.
2. **Managed-Agent cost ceiling.** **Recommend:** hard-cap per export
   at 60s wall-clock; over → `Codes.EXPORT_TIMEOUT` and fall back to
   pandoc if available, else fail.
3. **Format set.** EPUB/PDF/DOCX only, or markdown too? **Recommend:**
   add markdown as a fourth backend-agnostic path — it's the lossless
   round-trip.
