---
spec_id: "154"
slug: output-overflow-capture-recall
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "005"
depends_on: ["005", "023", "146", "082", "147"]
vision_goals: [1, 2]
affects:
  - agency/_envelope.py
  - agency/capabilities/memory (overflow store)
  - tests/test_output_overflow.py
---

# Spec 154 — Output-overflow capture + recall

## Why

Spec 005 (output-overflow capture + recall) is Not Started. When a verb
returns more than the token budget (Spec 023), the engine truncates —
and the truncated tail is LOST, even though it might hold the answer.
The Claude API's own answer to large intermediate results is to keep
them out of context and recall on demand (`claude-api` skill,
programmatic tool calling / code execution container). The engine
should do the same: overflow bodies go to the graph as an Artefact, the
response carries a recall handle, and a follow-up verb fetches the slice
the agent actually needs.

## Done When

- [ ] **Overflow capture** — when `_envelope` truncates a body past
      `max_tokens`, the FULL body is recorded as an
      `Artefact(kind="overflow-capture")` with SERVES; the response
      carries `{truncated: True, recall_handle: <artefact_id>,
      total_tokens}`.
- [ ] **`memory.recall_overflow(handle, slice="", grep="")`** fetches
      a budgeted slice of the captured body — by line range or by a
      grep pattern (the agent asks for what it needs).
- [ ] **Prefix never overflows** (Spec 146) — only the body is
      captured; the cacheable prefix stays intact.
- [ ] **Token measurement via Spec 082 TokenCounter.**
- [ ] Test: a verb returning > budget records an overflow Artefact;
      `recall_overflow` returns the grep'd slice; prefix byte-stable.
- [ ] TODO row + drift clean.

## Interconnects

- **Output-budget chain** (146): this is the recall half of the budget
  story — 146 freezes the prefix, 154 captures the overflowing body.
- Spec 147 (AnthropicDriver) uses `recall_handle` to fetch tails
  without re-running the verb.
- Spec 023 (adaptive disclosure) is the truncation point this hooks.

## Open questions

1. TTL on overflow Artefacts, or keep forever? **Recommend**: keep
   (graph is the store, Goal 7); they SERVE an intent and are part of
   the provenance record — a session-scoped GC is a Slice-2 knob.
