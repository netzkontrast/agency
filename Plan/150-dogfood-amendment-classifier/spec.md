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

- [ ] **`dogfood.parse_amendment(scope="", since="", limit=20)`**
      reads recent `Reflection` nodes via Spec 045 semantic recall,
      classifies each as `observation` / `proposal` / `refinement`,
      and emits a structured payload per proposal:
      ```python
      ProposalPayload = {
        "spec_id":      str,           # must exist; lint enforces
        "section":      str,           # "Done When" | "Open questions" | "Followup" | "row"
        "op":           Literal["add-row", "flip-status", "add-open-q",
                                "add-done-when", "supersede"],
        "before":       str,           # verbatim source text
        "after":        str,           # verbatim proposed text
        "rationale":    str,           # ≥ 40 chars; ≥ 1 source citation
        "source_reflections": list[str],  # ≥ 1 reflection node id
        "confidence":   float,         # 0..1; classifier-reported
      }
      ```
- [ ] **Classification runs through Spec 147 AnthropicDriver** with
      `output_config.format` (the strict ProposalPayload JSON schema)
      so the payload is guaranteed-parseable; degrades to a decidable
      keyword classifier when no `[anthropic]` extra (never silently
      no-ops; the keyword path emits the same shape with
      `confidence=0.3` flag).
- [ ] **`dogfood.apply_amendment(payload, dry_run=True)`** renders the
      proposed spec-edit as a unified diff (dry-run default — NEVER
      silently mutates a spec, even with `dry_run=False` unless
      explicit `confirm_token` matches the proposal's id-hash). Records
      an `Artefact(kind="amendment-proposal")` with SERVES + the
      `source_reflections` as PRODUCES-from edges.
- [ ] **Rubric** (Managed-Agents Outcome path) — a vendored
      `amendment.rubric.md` grading: cites ≥1 reflection, names a real
      spec_id (lookup at gradeable-time), op is one of the documented
      enum values, rationale ≥ 40 chars, before/after are non-trivial
      diff (not whitespace-only).
- [ ] **`dogfood.collect` (the markdown-parse anti-pattern) fully
      retired** behind this — Spec 017 deprecated it; Spec 159 removes
      the last caller. CI fails if a `collect` import resolves.
- [ ] **Quality metric** (Spec 258 closes the loop) — proposal
      accept-rate over time, derived (Spec 149); a regression triggers
      a warning Reflection (the meta-loop).
- [ ] **Failure modes**:
      - `Codes.AMENDMENT_BAD_SPEC` when proposed spec_id doesn't exist;
      - `Codes.AMENDMENT_NO_SOURCE` when source_reflections is empty;
      - `Codes.AMENDMENT_VAGUE` when rationale fails the 40-char floor;
      - `Codes.DRIVER_REFUSAL` propagated from Spec 147 when the
        classifier refuses (rare; not retried).
- [ ] **Acceptance invariant**: every accepted amendment must
      trace-back through the graph to ≥ 1 named Reflection (provenance
      moat unbroken). A reviewer running `analyze.graph_query`
      (Spec 203) can reconstruct "this amendment came from these
      observations" in one call.
- [ ] Test: seed 3 Reflections, assert one `proposal` payload with a
      valid op and ≥40-char rationale; dry-run produces a diff, not a
      write; live-write requires `confirm_token`; reject-on-bad-spec
      asserts the typed code.
- [ ] **TODO row + drift clean.**

## Worked example (Given/When/Then)

```text
Given:  5 Reflections about a verb returning oversized payloads
When:   dogfood.parse_amendment(scope="output-budget") runs
Then:   returns ≥1 ProposalPayload with
        op="add-done-when", spec_id="146", rationale citing the 5
        reflections, confidence ≥ 0.7

Given:  ProposalPayload with confidence 0.85 and dry_run=True
When:   apply_amendment runs
Then:   returns {diff: "...", artefact_id: "art-..."}
        AND no spec file modified
        AND analyze.graph_query("Artefact{kind:amendment-proposal}
            PRODUCES-from Reflection") returns the 5 source citations

Given:  proposal cites a non-existent spec_id "999"
When:   apply_amendment runs
Then:   returns Codes.AMENDMENT_BAD_SPEC; no Artefact written
```

## Interconnects

- Anchors the **dogfood-loop chain** the charter declares — closes the
  GOALS.md Goal-6 loop end to end.
- Spec 147 (AnthropicDriver) is the classifier engine.
- Spec 149 (derived docs) renders accepted amendments as TODO-row
  deltas, so an applied amendment self-updates the index.
- Spec 045 (semantic recall) selects the candidate Reflections.
- Spec 017 (graph-native ledgers) is the write-side this consumes.
- Spec 159 (collect retirement) removes the last anti-pattern caller.
- Spec 173 (reflection-link error promotion) keeps source citations
  unbroken.
- Spec 181 (embedder upgrade) sharpens candidate selection.
- Spec 183 (intent-chain opportunity) feeds verb-promotion proposals.
- Spec 199 (Skills round-trip) validates skill-promote proposals.
- Spec 258 (quality loop) measures classifier accept-rate.
- Spec 264 (self-improvement meta-cap) composes this into one verb.

## Open questions

1. **Auto-apply low-risk amendments** (e.g. flip-status when the test
   suite proves it) or always human-gate? **Recommend**: always
   human-gate v1 (dry-run diff); a `--auto` flag for the narrow
   flip-status-on-green case is a Slice-2 once trust is established.
2. **Managed-Agents Outcome vs single structured-output call?**
   **Recommend**: single structured-output call v1 (cheaper, no
   session lifecycle); promote to an Outcome with iterate-to-rubric
   when measured proposal accept-rate < 0.5.
3. **De-duplication** — what if the classifier proposes the same edit
   twice across runs? **Recommend**: hash by `(spec_id, section,
   after-text)` and skip; the existing proposal is returned with a
   `duplicate_of` field.
4. **Acceptance review surface.** Where does a human accept? **Recommend**:
   a `/agency-amendments` slash command (Spec 148 family) renders
   pending proposals; accepting opens a PR draft. Closes the loop end
   to end.
