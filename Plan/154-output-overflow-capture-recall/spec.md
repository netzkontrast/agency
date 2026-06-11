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
      carries a typed `OverflowHandle{recall_handle: ArtefactId,
      total_tokens: int, returned_tokens: int, truncated: True}`.
- [ ] **`memory.recall_overflow(handle, slice="", grep="")`** returns a
      typed `RecallSlice{body: str, slice_tokens: int, total_tokens: int,
      matches_returned: int, more_available: bool}` — by line range or
      grep pattern. The agent asks for what it needs.
- [ ] **Prefix never overflows** (Spec 146) — only the body is
      captured; the cacheable prefix stays intact.
- [ ] **Token measurement via Spec 082 TokenCounter.**
- [ ] **Measurable invariants** (rule 8):
      (a) `prefix_bytes(response_with_overflow) ==
      prefix_bytes(response_without_overflow)` (prefix byte-stability
      across truncation — composes with Spec 146);
      (b) `sum(recall_overflow(h, slice=full).body)` reconstructs the
      original body byte-for-byte (no lossy capture);
      (c) `recall_slice_tokens <= max_tokens` always (recall itself
      honours the budget — no infinite-recursion overflow);
      (d) every truncation event in the live registry has a matching
      Artefact node (truncate-without-capture is invariant zero).
- [ ] Test: a verb returning > budget records an overflow Artefact;
      `recall_overflow` returns the grep'd slice; prefix byte-stable.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  research.fetch returns a 12,000-token body; budget is 4,000
When:   the engine envelopes the response
Then:   response.body carries first 4,000 tokens AND
        OverflowHandle{recall_handle="art_abc", total_tokens=12000,
        returned_tokens=4000, truncated=True};
        an Artefact(kind="overflow-capture", body=<full 12000 tokens>)
        SERVES the originating intent

Given:  the agent needs the tail with "error:" lines
When:   memory.recall_overflow(handle="art_abc", grep="error:")
Then:   RecallSlice{body=<only matching lines>, matches_returned=N,
        more_available=False} — never re-runs the verb
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Lossy capture | non-utf8 / binary body | invariant (b) — reconstruct check | base64-wrap binary; reject silently-lossy encodings |
| Stale handle | overflow Artefact GC'd between calls | typed `Codes.OVERFLOW_NOT_FOUND` | open-question 1 default = keep (no GC); explicit `forget()` later |
| Recall-of-recall blow-up | agent recalls overflow that itself overflows | invariant (c) — slice budget gate | force `slice=` or `grep=` on recalls > budget |
| Driver mis-routes recall | LLM driver invents handle | typed shape + provenance check | reject handles not SERVED by the active intent |

## Interconnects

- **Output-budget chain** (146): this is the recall half of the budget
  story — 146 freezes the prefix, 154 captures the overflowing body.
- Spec 147 (AnthropicDriver) uses `recall_handle` to fetch tails
  without re-running the verb.
- Spec 023 (adaptive disclosure) is the truncation point this hooks.
- Spec 151 (Codes coverage) supplies `Codes.OVERFLOW_CAPTURED` and
  `Codes.OVERFLOW_NOT_FOUND`.
- Spec 159 (dogfood deprecation) shares the no-markdown-parse posture
  — overflow lives as a graph Artefact, never a sidecar file.
- Spec 160 (CLI `--fields`) is the bash-side counterpart: project
  before truncation rather than recall after.

## Open questions

1. TTL on overflow Artefacts, or keep forever? **Recommend**: keep
   (graph is the store, Goal 7); they SERVE an intent and are part of
   the provenance record — a session-scoped GC is a Slice-2 knob.
2. Auto-recall on cursor exhaustion or always agent-driven?
   **Recommend**: agent-driven only — silent auto-recall hides the
   token cost from the budget the driver is trying to manage.
