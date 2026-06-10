---
spec_id: "151"
slug: toolresult-code-coverage-audit
status: draft
last_updated: 2026-06-10
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
- [ ] **`agency_doctor` reports `codes_coverage`** — fraction of
      failure sites using a typed Code; derived (Spec 149), not pinned.
- [ ] **Codes namespace gains the missing members** the audit surfaces.
- [ ] Test: a fixture verb with a literal-string failure trips the lint;
      the live registry reports ≥ the documented coverage floor.
- [ ] TODO row + drift clean.

## Interconnects

- **Output-budget chain** (146): typed codes keep error payloads short
  + cache-stable.
- **Drift-derivation chain** (149): `codes_coverage` is a derived field.
- Spec 019 (wire-shape) is the sibling discipline for the ok-path.

## Open questions

1. Promote to hard error immediately or WARN-first? **Recommend**:
   WARN-first one cycle (Spec 056/058 pattern), then flip after the
   coverage floor is met.
