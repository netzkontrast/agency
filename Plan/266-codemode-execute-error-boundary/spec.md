---
spec_id: "266"
slug: codemode-execute-error-boundary
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "019"
depends_on: ["019", "059", "151", "154", "256", "260"]
vision_goals: [5]
affects:
  - agency/engine.py
  - tests/test_codemode_error_boundary.py
---

# Spec 266 — code-mode execute: error boundary

## Why

Spec 019 ships the wire-shape contract; `execute` chains tool calls in
a sandbox and returns one envelope. Today an exception in a chained
call surfaces as a raw Python traceback inside the result — useful
for a human debugger, useless to an orchestrator that wanted a
typed `ToolResult`. Per Spec 059 typed errors + Spec 151 Codes
coverage, every chained call should boundary into the same typed
envelope so the orchestrator gets `{result, errors: [{trace_id, code,
message}], partial_capture_ref}` consistently. Bonus: an error
mid-chain captures partial state via Spec 154 so the next session can
inspect what was DONE before the failure without re-running the
expensive prefix.

## Done When

- [ ] **`execute` wraps each chained `call_tool` in a try/typed-error
      boundary** — exceptions become `ChainCallFailure{trace_id, code,
      message, position}` failures; never leak a raw traceback.
- [ ] **Typed `ExecuteResult` return shape**:
      ```python
      class ExecuteResult(TypedDict):
          result: Any                       # the return value
          errors: list[ChainCallFailure]    # any per-call failures
          partial_capture_ref: str | None   # Spec 154 capture handle
          calls_attempted: int
          calls_succeeded: int
      ```
- [ ] **Partial results from mid-chain failures capture via Spec 154**
      — the engine writes the pre-failure state to a capture node and
      returns the ref so debugging stays cheap.
- [ ] **Wire-shape invariant (Spec 019) preserved** — no Python
      object, no traceback, no raw exception leaks across the wire.
- [ ] **Measurable invariants** (relationships, not pinned counts):
      - `calls_attempted >= calls_succeeded` (trivial sanity)
      - `len(errors) == calls_attempted - calls_succeeded` (every
        failure is enumerated; none silently dropped)
      - `partial_capture_ref is not None ⇔ len(errors) > 0`
        (capture happens iff something failed)
      - every `ChainCallFailure.code` is a member of the Spec 151 Codes
        enum (no `Codes.UNKNOWN` leaks)
      - every `trace_id` is unique within an `ExecuteResult` (so logs
        correlate per-call, not per-execute)
- [ ] Test: an exception mid-chain returns typed error envelope +
      partial capture handle; orchestrator can `analyze.capture` the
      ref; chained calls after the first failure either short-circuit
      OR continue (caller controls via `on_error: "stop" | "continue"`).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  user passes execute(code="""
            a = await call_tool("intent_bootstrap", {...})
            b = await call_tool("nonexistent_tool", {})  # will fail
            c = await call_tool("analyze.graph", {...})
            return {a, b, c}
        """, on_error="continue")
When:   engine runs the chain
Then:   ExecuteResult{
            result: {a: <ok>, b: None, c: <ok>},
            errors: [ChainCallFailure{trace_id:"t2",
                code:Codes.TOOL_NOT_FOUND, position:1,
                message:"nonexistent_tool"}],
            partial_capture_ref: "capture://abc123",
            calls_attempted: 3, calls_succeeded: 2}
        AND analyze.capture("capture://abc123") returns the pre-failure
        binding {a: <ok>} so debugging skips re-running step 1

Given:  same code but on_error="stop"
When:   engine runs the chain
Then:   ExecuteResult{result: None,
            errors: [ChainCallFailure at position 1],
            calls_attempted: 2, calls_succeeded: 1,
            partial_capture_ref: "capture://..."}
        AND step 2 (c) was NEVER attempted (calls_attempted == 2)

Given:  a chained call invokes the LLM via Spec 147 driver and the
        model refuses
When:   the driver returns DriverError.REFUSAL
Then:   ChainCallFailure{code: Codes.REFUSAL, message includes refusal
        category, refusal_billed_tokens preserved}
        AND Spec 256 fallback was already tried by the driver before
        the boundary saw the error (boundary is the LAST resort)
```

## Failure modes (Nygard)

| Failure | Boundary response |
|---|---|
| Raw Python exception in chained call | Caught + wrapped as `ChainCallFailure`; traceback preserved in capture, not in result envelope |
| Tool not found in registry | `Codes.TOOL_NOT_FOUND` typed failure; no Python AttributeError leaks |
| Validation error on tool args | `Codes.BAD_REQUEST` with the validation detail in `message` |
| LLM driver refusal mid-chain (via Spec 256) | `Codes.REFUSAL` propagates; partial billed tokens preserved |
| Sandbox timeout | `Codes.TIMEOUT`; partial capture saves bindings up to the timeout |
| Capture write fails (graph unavailable) | `Codes.CAPTURE_UNAVAILABLE` listed in errors; result still returned (capture is best-effort, not blocking) |
| Code-mode `return` value not JSON-serializable | `Codes.SERIALIZATION_ERROR`; capture preserves the un-serializable value for inspection |
| Re-entrant `execute` call exceeds depth limit | `Codes.RECURSION_LIMIT`; never deadlocks the engine |

## Interconnects

- Spec 019 (parent wire-shape contract) — this closes the failure
  surface of the contract.
- Spec 059 (typed errors) — defines the `ChainCallFailure` type
  family.
- Spec 151 (Codes coverage audit) — `Codes.TOOL_NOT_FOUND`,
  `Codes.CAPTURE_UNAVAILABLE`, `Codes.RECURSION_LIMIT`,
  `Codes.SERIALIZATION_ERROR` land here.
- Spec 154 (output-overflow capture-recall) — supplies the partial
  capture infrastructure this spec relies on.
- Spec 256 (refusal fallback) — refusal handling is driver-level;
  boundary sees the post-fallback outcome only.
- Spec 260 (slash NL routing) — slash routing dispatches through
  `execute`; this boundary makes slash failures observable.
- Closes the code-mode contract for failure paths.

## Open questions

1. **Default `on_error` — stop or continue?** **Recommend**: `stop` —
   safer default; downstream calls after a failure may have undefined
   inputs. Power users opt into `continue` explicitly.
2. **Should the capture include LLM token usage from chained calls?**
   **Recommend**: yes — aggregate usage by call position so debugging
   cost regressions is one query, not many.
3. **How long do partial captures persist?** **Recommend**: align with
   Spec 154 capture TTL (default 24h); long enough for the next
   session, short enough to bound storage.
