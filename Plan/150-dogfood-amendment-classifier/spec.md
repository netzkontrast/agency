---
spec_id: "150"
slug: dogfood-amendment-classifier
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "014"
depends_on: ["014", "017", "045", "147", "149"]
vision_goals: [6, 7, 2]
affects:
  - agency/capabilities/dogfood/_main.py
  - tests/test_dogfood_amendment_classifier.py
---

# Spec 150 — Dogfood amendment classifier (close Goal 6)

## Why

Goal 6 ("doctrine evolves through dogfooding") is the alignment
matrix's standing 🔴 critical gap: Reflections accumulate (Spec 045
gives semantic recall) but NO automated path turns "observed pattern"
into "spec amendment proposal". Spec 014 was drafted for exactly this
and is Not Started. The `claude-api` skill gives the missing engine —
a Managed-Agents Outcome with a gradeable rubric, or a single
structured-output call — that classifies recent Reflections and emits
a JSON-ops payload a human applies to a spec.

## Done When

- [ ] **`dogfood.parse_amendment(scope="", since="")`** reads recent
      `Reflection` nodes (via Spec 045 recall), classifies each as
      `observation` / `proposal` / `refinement`, and emits a structured
      `{spec_id, section, op, before, after, rationale, source_reflections}`
      payload per proposal.
- [ ] **Classification runs through Spec 147 AnthropicDriver** with
      `output_config.format` (a strict JSON schema) so the payload is
      guaranteed-parseable; degrades to a decidable keyword classifier
      when no `[anthropic]` extra (never silently no-ops).
- [ ] **`dogfood.apply_amendment(payload, dry_run=True)`** renders the
      proposed spec-edit as a diff (dry-run default — never silently
      mutates a spec); records an `Artefact(kind="amendment-proposal")`
      with SERVES + the `source_reflections` as PRODUCES-from edges.
- [ ] **Rubric** (Managed-Agents Outcome path) — a vendored
      `amendment.rubric.md` grading: cites ≥1 reflection, names a real
      spec_id, op is one of {add-row, flip-status, add-open-q,
      supersede}, rationale non-empty.
- [ ] **`dogfood.collect` (the markdown-parse anti-pattern) fully
      retired** behind this — Spec 017 deprecated it; this removes the
      last caller.
- [ ] Test: seed 3 Reflections, assert one `proposal` payload with a
      valid op; assert dry-run produces a diff, not a write.
- [ ] TODO row + drift clean.

## Interconnects

- Anchors the **dogfood-loop chain** the charter declares — closes the
  GOALS.md Goal-6 loop end to end.
- Spec 147 (AnthropicDriver) is the classifier engine.
- Spec 149 (derived docs) renders accepted amendments as TODO-row
  deltas, so an applied amendment self-updates the index.
- Spec 045 (semantic recall) selects the candidate Reflections.
- Spec 017 (graph-native ledgers) is the write-side this consumes.

## Open questions

1. Auto-apply low-risk amendments (e.g. flip-status when the test
   suite proves it) or always human-gate? **Recommend**: always
   human-gate v1 (dry-run diff); a `--auto` flag for the narrow
   flip-status-on-green case is a Slice-2 once trust is established.
2. Managed-Agents Outcome vs single structured-output call?
   **Recommend**: single structured-output call v1 (cheaper, no
   session lifecycle); promote to an Outcome with iterate-to-rubric
   when proposal quality demands it.
