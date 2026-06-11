---
spec_id: "151"
slug: toolresult-code-coverage-audit
status: partial
last_updated: 2026-06-11
owner: "@agency"
enhances: "059"
depends_on: ["001", "059", "019", "149"]
vision_goals: [1, 5]
affects:
  - agency/_toolresult.py
  - agency/_lints/_codes_coverage.py
  - tests/test_codes_coverage.py
---

# Spec 151 — ToolResult Codes coverage audit

## Why

Spec 059 ships the `Codes` namespace + `.success`/`.failure` ctors +
`trace_id` stamping. But there is no audit that every error path in
every capability actually USES a typed `Code` rather than a freeform
string — the same drift the naming audit (Spec 049) ran for names,
unran for error codes. A verb that returns `{"error": "not found"}`
instead of `Codes.NOT_FOUND` is invisible to a wrapping LLM driver's
error branch.

## Done When

- [ ] **`_check_codes_coverage` lint** (AST) flags any verb that
      constructs a failure ToolResult with a literal string code not in
      the `Codes` namespace. WARN-then-promote-to-error (Spec 058
      precedent).
- [ ] **`agency_doctor` reports `codes_coverage`** — typed shape
      `{covered_sites: int, total_failure_sites: int, fraction: float,
      offenders: list[FileLoc]}`; derived (Spec 149), not pinned.
- [ ] **Codes namespace gains the missing members** the audit surfaces.
- [ ] **Measurable invariants** (rule 8 — relationships, not counts):
      (a) `live.codes_coverage.fraction >= floor` where `floor` is the
      LAST shipped value (monotone non-decreasing across commits);
      (b) `documented_Codes_members ⊇ codes_referenced_in_offenders` —
      a NEW typed code can land only if it appears in `Codes`;
      (c) every Code member has ≥ 1 call site OR is tagged
      `# AGENCY-RESERVED` (no orphan Codes).
- [ ] Test: a fixture verb with a literal-string failure trips the lint;
      the live registry reports `fraction >= floor` (read from the
      previous run's reflection — not a pinned number).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a capability verb returns ToolResult.failure(code="not found")
When:   _check_codes_coverage runs (post-WARN cycle)
Then:   lint fails with CODES_LITERAL_STRING pointing at the call site
        AND offenders[] carries (file, line, literal)

Given:  a verb migrates "not found" → Codes.NOT_FOUND
When:   agency_doctor re-derives codes_coverage
Then:   fraction increases AND the offender drops out of the list
        AND the monotone floor advances by one
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Dead Code member | Code defined, no call site | invariant (c) — orphan check | tag `# AGENCY-RESERVED` or remove |
| Floor regression | a refactor reintroduces a literal | invariant (a) — monotone gate | block CI; require explicit `floor_reset` |
| Cross-capability code drift | two caps invent overlapping codes | substrate set audit (Spec 054 tag) | promote to shared `Codes` namespace |
| LLM driver swallows untyped error | a verb returns `{"error": "..."}` instead of typed Code | the wrapping driver (Spec 147) has no enum branch to match | typed Codes round-trip through `output_config.format`; lint blocks literal strings at source |

## Interconnects

- **Output-budget chain** (146): typed codes keep error payloads short
  + cache-stable.
- **Drift-derivation chain** (149): `codes_coverage` is a derived field.
- Spec 019 (wire-shape) is the sibling discipline for the ok-path.
- Spec 154 (output-overflow) shares the `Codes.PREFIX_BUDGET_EXCEEDED`
  / `Codes.OVERFLOW_CAPTURED` namespace this audit must cover.
- Spec 152 (typed Skill/Phase) consumes the same `Codes` namespace for
  phase-validate failures — the audit covers both surfaces uniformly.
- Spec 157 (architecture-drift gate) consumes `codes_coverage` as one
  of its standing invariants.
- Spec 156 (wet pressure), Spec 158 (scaffold sweep), Spec 159
  (dogfood deprecation), Spec 160 (CLI chain) — every peer that
  emits a typed failure adds a member to the same `Codes` namespace
  this audit polices.
- **LLM-driver chain** (147): the AnthropicDriver matches on the
  typed `Code` enum; literal-string failures are invisible to it.

## Open questions

1. Promote to hard error immediately or WARN-first? **Recommend**:
   WARN-first one cycle (Spec 056/058 pattern), then flip after the
   coverage floor is met.
2. Per-capability sub-floors or a single global floor? **Recommend**:
   single global (matches naming-audit Spec 049 posture); per-cap
   sub-floors emerge only if one capability stalls.

## Followup — Implementation Status (2026-06-11)

### Done — Slice 1 (pure audit module + Codes.INVALID_ARGUMENT promotion)

- **`scripts/check_codes_coverage.py`** — pure AST-walking audit.
  `classify_failure_call(call_node)` per-site classifier returning
  `(CallSiteClass, literal)`; `audit_source(src, path)` walks a single
  module; `audit_tree(root)` composes the `CoverageReport`.
- **Typed shapes** — `FileLoc(path, line)`; `CallSiteClass{ATTR_REF,
  STRING_LITERAL, EXPR, UNKNOWN}`; `CallSiteResult(loc, classification,
  literal)`; `CoverageReport{total_failure_sites, covered_sites,
  offenders, orphan_codes, expr_sites}` with computed `.fraction`
  property (empty-tree convention: `1.0`; EXPR sites subtracted from
  the denominator so opaque computed codes don't skew coverage).
- **Orphan-code detection** (invariant c) — every documented `Codes`
  member with no ATTR_REF call site in the audited tree shows up in
  `orphan_codes` so authors can either backfill a call site or tag the
  constant `# AGENCY-RESERVED`.
- **`Codes.INVALID_ARGUMENT = "invalid_argument"` lands** — promoted
  from heavily-used literal in `novel/_main.py`. Slice 2 migrates the
  call sites from literal-string to `Codes.INVALID_ARGUMENT` attr-ref.
- **CLI** — `python -m scripts.check_codes_coverage [--root agency]`
  prints fraction + offenders (head:20) + orphans. Slice 1 is
  informational (`return 0`); Slice 2 promotes to a CI-blocking gate
  per Spec 058 WARN→error pattern.
- **11 tests green** (`tests/test_codes_coverage.py`) — per-class
  classification + multi-site + tree audit + empty-tree convention +
  orphan detection + Codes namespace subset invariant (rule 8) +
  INVALID_ARGUMENT constant + live-tree shape invariant
  (informational fraction).

### Still — Slice 2+

- **Slice 2** — Spec 058 WARN→error promotion. Once the live tree
  reports `fraction >= 0.9`, promote `check_codes_coverage` to a
  CI-blocking gate. Add `--floor` enforcement (default 0.9, override
  via `Plan/_planning/codes-coverage-floor.txt` Spec 054 drift
  baseline). Monotone-floor invariant (a) — floor advances on each
  commit; regression requires explicit `floor_reset` (audit-trail
  Reflection).
- **Slice 3** — `agency_doctor.codes_coverage` reports the typed
  payload `{covered_sites, total_failure_sites, fraction, offenders}`
  + a `monotone_ok` bool so wrapping drivers can branch on the
  health of the typed-error surface.
- **Slice 4** — backfill the live offenders. Convert every
  `ToolResult.failure("INVALID_ARGUMENT", ...)` to
  `ToolResult.failure(Codes.INVALID_ARGUMENT, ...)` in `novel/_main.py`
  (and any other capability the audit surfaces); push fraction toward
  1.0.
- **Slice 5** — `EXPR` sub-audit. A computed-code call site is opaque
  to lint today; Slice 5 tracks call-site frequency + warns when a
  cap accumulates > N EXPR-form failures (a signal that a `Codes.X`
  promotion is overdue).
