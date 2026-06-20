---
spec_id: "150"
slug: dogfood-amendment-classifier
status: partial
last_updated: 2026-06-11
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

## Followup — Implementation Status (2026-06-11)

### Done — Slice 1 (keyword-classifier path + apply_amendment dry-run)

- **`dogfood.parse_amendment(scope, since, limit)`** — keyword
  classifier reads `Reflection(scope="observation")` nodes, classifies
  each by strong-intent keywords (`should add` / `propose` / `should
  be` / `missing from spec` / `open question`) → ProposalPayload shape
  `{spec_id, section, op, before, after, rationale, source_reflections,
  confidence}`. The keyword path is the documented fallback when
  Spec 147 AnthropicDriver is unavailable (never silent no-op);
  Slice 2 swaps in structured-output classification.
- **`dogfood.apply_amendment(payload, dry_run=True, confirm_token="")`**
  — renders the proposed spec-edit as a unified diff (Python
  `difflib`); records `Artefact(kind="amendment-proposal")` with
  PRODUCES_FROM edges to every cited Reflection (provenance moat
  invariant); SERVES the active intent. Live-write opt-in via
  `confirm_token` matching the payload id-hash (SHA-256 of
  `spec_id|section|op|after`).
- **Typed failure codes on `Codes`** — `AMENDMENT_BAD_SPEC` /
  `AMENDMENT_NO_SOURCE` / `AMENDMENT_VAGUE` (< 40-char rationale floor) /
  `AMENDMENT_UNCONFIRMED` (live-write requested, token mismatch).
- **Ontology extension** — `Artefact: ["kind"]` node + `PRODUCES_FROM`
  edge added to `DogfoodCapability.ontology` so the amendment
  provenance is queryable via `analyze.graph_query` (Spec 203).
- **13 tests green** (`tests/test_dogfood_amendment_classifier.py`) —
  shape + classifier rules + scope/limit filter + dry-run diff +
  provenance Artefact + PRODUCES_FROM edges + typed-code paths
  (bad_spec, no_source, vague, unconfirmed) + Codes sugar.
- **Regression**: `test_dogfood_has_session_tracking_verbs` converted
  from frozen-snapshot `set ==` to a SUBSET invariant (rule 8) so
  documented core verbs must exist; future verbs may extend the set.

### Done — Slice 2 (LLM classifier + Spec 279 delegation, 2026-06-12)

- **LLM classification path** — `dogfood.parse_amendment(scope, since,
  limit, use_llm=True, prefer_delegate=False, host_completion=None)`
  now drives the Spec 147 `AnthropicDriver.complete(...)` with
  `output_config.format=json_schema` (per claude-api skill) when the
  driver is wired AND capable. Schema enforces 3-digit `spec_id`,
  enum-bound `section` + `op`, 40-char `rationale` floor, confidence
  in [0,1]. Hallucinated `reflection_id`s are dropped (defense:
  the LLM can only cite ids from the input set).
- **Spec 279 delegation** — when `prefer_delegate=True` and the
  driver backend is `"none"`, the verb returns
  `{proposals: [], classifier: "llm-delegate", kind: "llm_delegate",
  request: HostLLMRequest.to_dict()}` so Claude Code (the host) runs
  inference and calls the verb again with `host_completion={text,
  parsed}`. The resume path returns `classifier: "host"` — same
  ProposalPayload shape.
- **Silent keyword degrade** — default `prefer_delegate=False`:
  when the driver backend is `"none"` AND no `host_completion` is
  supplied, the verb falls through to the Slice 1 keyword path
  rather than emitting an envelope the caller didn't ask for.
  Backwards-compat invariant: existing 13 Slice 1 tests pass without
  modification.
- **Driver failure recovery** — any exception from
  `driver.complete(...)` (auth / network / refusal) degrades to the
  keyword path; the dogfood loop never crashes.
- **`classifier` field** — every response now reports the path that
  produced it: `"keyword"` / `"llm"` / `"host"` / `"llm-delegate"`.
- **Module-level helpers**: `_PROPOSAL_LIST_SCHEMA` (JSON schema),
  `_CLASSIFIER_SYSTEM` (system prompt), `_reflection_payload_for_llm`
  (1.2K-char text cap per Spec 154 discipline),
  `_build_classifier_messages`, `_parse_llm_proposals`.
- **8 new tests green** (21 total Slice 1 + Slice 2):
  capable-driver path uses LLM; no-backend silently degrades to
  keyword; `prefer_delegate=True` emits the envelope; host_completion
  resume parses proposals; hallucinated reflection_ids dropped;
  `use_llm=False` forces keyword (driver never called); driver
  exception degrades to keyword; malformed `host_completion` raises
  `HostDelegateError(MALFORMED)`.

### Done — Slice 3 (live-write — closes Goal 6's fold-back loop, 2026-06-17)
- **`confirm_token` live-write SHIPPED.** `apply_amendment(payload,
  dry_run=False, confirm_token=<id-hash>)` now performs the actual spec.md
  surgery and returns `written_path` (+ the REAL unified diff of the file
  change, so the recorded Artefact matches what landed on disk). The
  decidable core is the pure, I/O-free `apply_amendment_to_text(text, *,
  section, op, before, after)` helper: `_find_section_bounds` locates the
  `## <section>` heading tolerant of case/punctuation/suffixes
  (`## Done-When (if built)` matches "Done When"); `add-*` appends a bullet
  at the end of the section (checkbox bullet for Done-When, plain elsewhere);
  `edit-*` replaces the first line containing `before` (indentation
  preserved). **Never blind-writes** — a missing section raises
  `amendment_no_section`, a missing edit target raises
  `amendment_before_absent`, so a misclassification cannot corrupt a spec.
  This mechanizes Goal 6's "fold back into the specs" behind the human
  `confirm_token` gate. Tests: 1 live-write acceptance scenario (folds a
  bullet into a temp spec, returns `written_path`) + 3 pure-function
  invariants (append-in-section / missing-section-raises / edit-replaces).

### Still — Slice 4+
- **Slice 4**: rubric.md vendored (Managed-Agents Outcome path);
  promote to an Outcome iterate-to-rubric when measured proposal
  accept-rate < 0.5.
- **Slice 5**: de-dup by payload-hash; existing proposal returned with
  `duplicate_of` field.
- **Slice 6**: `/agency-amendments` slash command (Spec 148 family)
  renders pending proposals + accept opens a PR draft (closes the
  loop end to end).
- **Spec 258 quality loop**: accept-rate metric on the classifier;
  regression triggers a warning Reflection (the meta-loop).
- **Spec 159 collect retirement**: replace the last `dogfood.collect`
  caller with `parse_amendment`; CI fails if a `collect` import
  resolves.
