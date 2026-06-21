---
spec_id: "135"
slug: sensitivity-reader-workflow
status: draft
state: done
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["101", "104", "108", "122"]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_sensitivity_pass.py
domain: novel / editorial / sensitivity
parent_spec: "101"
mvp-source:
  - "Spec 122 `check_sensitivity` ships an advisory lexicon — informational only, no workflow"
  - "Industry practice: a structured sensitivity pass before publication, with documented categories + severities + suggestions"
---

# Spec 135 — Sensitivity reader workflow

## Why

Spec 122's `check_sensitivity` advisory lexicon catches keyword presence
but not the work an actual sensitivity reader does: flagging
*portrayals*, scoring severity, suggesting revisions, tracking
resolution status. Trade publishers expect a documented sensitivity
pass before final manuscript; agency today has no surface for one.

Without this, authors who want to do the work right end up tracking it
in a separate doc — losing the provenance moat. With it, every
sensitivity finding IS a graph node, traceable to the scene, with a
documented resolution status.

## Done When

- [ ] **`SensitivityFinding` node**:
      ```
      {scene_id, category, severity, finding, suggestion, status,
       reader_id?, reader_notes?}
      ```
      - `category`: one of `SENSITIVITY_CATEGORIES` (mental-health /
        identity / trauma / culture / religion / disability /
        socioeconomic — open-set per the documented categories table)
      - `severity`: one of `SENSITIVITY_SEVERITY` enum (info / advisory
        / concern / serious)
      - `finding`: short description of what the reader caught
      - `suggestion`: proposed revision (freeform)
      - `status`: one of `SENSITIVITY_STATUS` enum (open / acknowledged /
        revised / dismissed-with-reason)
      - `reader_id`: optional id of the human reader who flagged it
        (string slug; not a graph ref in v1)
      - `reader_notes`: full context from the reader
- [ ] **`FLAGGED_IN` edge**: SensitivityFinding → Scene.
- [ ] **3 enums** declared on novel ontology: `SENSITIVITY_CATEGORIES`
      (open set — 7 documented), `SENSITIVITY_SEVERITY` (4 levels),
      `SENSITIVITY_STATUS` (4 states).
- [ ] **7 verbs on `novel` cap**:
      - `record_sensitivity_finding(scene_id, category, severity,
        finding, suggestion, reader_id="", reader_notes="")` — mints
        SensitivityFinding + FLAGGED_IN.
      - `list_sensitivity_findings(novel_id, status="", severity="",
        category="")` — multi-filter audit.
      - `update_finding_status(finding_id, status, resolution_notes="")`
        — flips status with audit trail (resolution_notes preserved on
        the node, never overwritten).
      - `acknowledge_finding(finding_id, notes)` — convenience wrapper:
        sets status to `acknowledged`.
      - `dismiss_finding(finding_id, reason)` — sets status to
        `dismissed-with-reason`; requires non-empty reason.
      - `mark_revised(finding_id, scene_id_revised)` — sets status to
        `revised`; `scene_id_revised` confirms which scene the author
        revised (can match original scene_id or point to a new scene
        if the original was split / merged).
      - `sensitivity_pass_gate(novel_id, min_severity_blocking="concern")`
        composite gate — passes IFF every SensitivityFinding with
        severity ≥ `min_severity_blocking` has `status ∈ {revised,
        dismissed-with-reason}`. Acknowledged ≠ resolved.
- [ ] **`sensitivity-reader-pass` walkable skill** (4-phase):
      1. **scan** → binds to existing `novel.check_sensitivity` over
         every chapter's body; auto-records `info`-severity findings
         from lexicon hits.
      2. **review** → human/agent-driven; for each scan-finding,
         author/reader uses `update_finding_status` or
         `record_sensitivity_finding` to add new manual findings.
      3. **revise** → for `serious` and `concern` severities, author
         must mark as revised OR dismiss-with-reason.
      4. **sign-off** (HARD GATE) → binds to `sensitivity_pass_gate`.
- [ ] **`record_sensitivity_finding` records an Invocation that SERVES
      the intent** — the moat: every finding is provenance-traceable to
      who flagged it, when, and to which scene.
- [ ] TODO row + drift clean.

## Design notes

- **The lexicon scan stays advisory** (per Spec 122's exact-severity
  discipline). Scan-findings auto-flag at `info` severity; the human
  reader elevates to `advisory` / `concern` / `serious` based on
  *portrayal*, not just keyword presence.
- **Dismissal requires a reason** — no silent "ignored". The
  doctrine: every dismissal IS a documented author decision, surfaceable
  to publisher / agent if asked.
- **`reader_id` is a string slug v1** — not a graph node. A future
  spec can elevate readers to a `SensitivityReader` node with
  credentials / specialty / engagement record. For now the author logs
  whatever they want ("freelance-1", "hired-firm-A").

## Open questions

1. **Should `acknowledged` count as resolved for gate purposes?**
   *Recommend*: no — only `revised` or `dismissed-with-reason` pass the
   gate. `acknowledged` is "I see this finding" not "I addressed it."
2. **Multi-reader workflows** — same finding flagged by two readers?
   *Recommend*: two separate SensitivityFinding nodes pointing at the
   same Scene; the `reader_id` distinguishes them. Author resolves
   each independently. Slice 2 may add `MERGED_INTO` edge.
3. **Public sensitivity lexicon vs project-specific** — should
   `SENSITIVITY_CATEGORIES` be hardcoded or overlay-able? *Recommend*:
   ship 7 documented categories; a project can add categories via a
   `_sensitivity_categories_overlay` config field (same pattern as
   Spec 129 fragments overlay).

## Followup

(Populated when the PR ships.)
