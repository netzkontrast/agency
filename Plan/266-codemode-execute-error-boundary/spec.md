---
spec_id: "266"
slug: codemode-execute-error-boundary
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "019"
depends_on: ["019", "059", "151", "154"]
vision_goals: [5]
affects:
  - agency/engine.py
  - tests/test_codemode_error_boundary.py
---

# Spec 266 — code-mode execute: error boundary

## Why

Spec 019 ships the wire-shape contract. Code-mode `execute` chains tool
calls in a sandbox; today an exception in one chained call surfaces as
a Python traceback. Per Spec 059 typed errors + Spec 151 Codes
coverage, `execute` should boundary every chained call into a typed
ToolResult — so the orchestrator gets `{result, errors: [{trace_id,
code, message}]}` shape consistently. Bonus: an error mid-chain
captures the partial via Spec 154 so debugging stays cheap.

## Done When

- [ ] **`execute` wraps each chained call in a try/typed-error
      boundary** — exceptions become `Codes.<TYPED>` failures with
      `trace_id`.
- [ ] **Partial results from mid-chain failures capture via Spec 154.**
- [ ] **Wire-shape invariant (Spec 019) preserved** — no leak.
- [ ] Test: an exception mid-chain returns typed error + partial
      capture handle; orchestrator receives well-formed envelope.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 019 (parent) · Spec 059/151 (typed errors) · Spec 154 (capture).
- Closes the code-mode contract for failure paths.
