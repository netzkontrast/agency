---
spec_id: "234"
slug: format-driver-pandoc-managed
status: draft
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

- [ ] **`PandocFormatDriver`** behind the Spec 002 boundary —
      pandoc + weasyprint for EPUB/PDF/DOCX; `[novel-format]` extra.
- [ ] **Managed-Agent fallback** (Spec 223) when the local extra absent.
- [ ] **Back-cover template ported**; Artefacts identical across backends.
- [ ] Test: each backend exports a fixture novel; artefacts match shape.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 223 (MA export) is the fallback · **LLM-driver chain** (147).
- Spec 002 boundary; **Goal 7** files-render-from-graph.
