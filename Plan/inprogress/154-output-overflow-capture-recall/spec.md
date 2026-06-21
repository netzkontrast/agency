---
spec_id: "154"
slug: output-overflow-capture-recall
status: partial
state: inprogress
last_updated: 2026-06-11
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

## Followup — Implementation Status (2026-06-11)

### Done — Slice 1 (pure capture + recall library)

- **`agency/_overflow.py`** — pure capture/recall functions with an
  injected token-counter so tests pin a deterministic proxy
  (`4 chars ≈ 1 token`) without depending on the Spec 082 backend:
  - `capture_overflow(body, *, max_tokens, counter)` → `OverflowResult`
    with `head` (monotone-prefix slice ≤ budget), `full_body`
    (preserved verbatim for follow-up recall), `total_tokens`,
    `returned_tokens`, `truncated`.
  - `recall_overflow_slice(body, *, slice="full", grep="",
    max_tokens, counter)` → `RecallSlice{body, slice_tokens,
    total_tokens, matches_returned, more_available}`. Selection
    priority: `grep` (line filter) → `slice` (line-range
    `"<start>:<stop>"` or `"full"`).
- **Typed shapes**: `OverflowResult`, `OverflowHandle{recall_handle,
  total_tokens, returned_tokens, truncated}`, `RecallSlice` —
  frozen dataclasses; immutable.
- **Recall honours its own budget** (invariant c): grep matches or
  line slices are themselves truncated to `max_tokens` with
  `more_available=True` set when truncation fires — no
  infinite-recursion overflow.
- **Round-trip property** (invariant b): `capture_overflow(body).full_body
  == body` byte-for-byte; the captured body is not re-encoded or
  lossy.
- **14 tests green** (`tests/test_output_overflow.py`) — short-body
  passthrough; long-body truncation; monotone-prefix invariant;
  round-trip preservation; full-slice recall; line-range recall +
  clamp; grep recall + no-match; recall budget honoured;
  frozen-dataclass mutability check; `OverflowHandle` shape; empty-body
  safety; malformed-slice defensive fallback.

### Done — Slice 2 (envelope body-half wiring, 2026-06-12)

- **`capture_body_overflow(env, max_body_tokens, counter)`** in
  `agency/_envelope.py` — pure function over `ResponseEnvelope`. Body
  serializes to canonical JSON, passed through `_overflow.capture_overflow`;
  when truncated, the returned envelope's body becomes
  `{_overflow_preview: head_blob, _overflow_handle: {recall_handle,
  total_tokens, returned_tokens, truncated}}`. The PREFIX is unchanged —
  the canonical-JSON bytes for a prefix-only sub-envelope are byte-identical
  before and after capture (Spec 146 invariant).
- **`BodyOverflowResult{envelope, handle}`** typed return; `handle` is
  `None` when body fit the budget, an `OverflowHandle` instance when
  capture fired.
- **Counter contract** matches Slice 1's `_as_counter_fn` adapter —
  accepts callable OR Spec 082 `TokenCounter`.
- **7 new tests** in `tests/test_response_prefix_discipline.py`:
  unchanged-under-budget; truncated-over-budget; prefix-byte-stability;
  handle carries token counts; zero-budget edge; negative budget rejected;
  handle.total matches canonical-JSON serialization size.

### Done — Slice 3 (graph verb `dogfood.recall_overflow_slice`, 2026-06-12)

- **`dogfood.recall_overflow_slice(body, slice, grep, offset,
  byte_offset, max_tokens)`** — the read-side graph verb. Delegates
  to the pure `_overflow.recall_overflow_slice` library with the
  engine's `token_counter` (Spec 082 backend; char-proxy fallback in
  hermetic tests). Returns the typed `RecallSlice` shape: `{body,
  slice_tokens, total_tokens, matches_returned, more_available,
  next_match_offset, next_byte_offset}`.
- **5 new tests** in `tests/test_hook_event_replay.py` (21 total green):
  pass-through under budget; grep filters matching lines; max_tokens
  truncates + sets `more_available`; line-range slice; grep paging via
  `offset=next_match_offset`.

### Still — Slice 3a+

- **Slice 3a** — `Artefact(kind="overflow-capture")` write/read so
  agents recall by Artefact id instead of resupplying the body each
  call (SERVES + PRODUCES edges per Spec 002). Today the body comes in
  as a verb arg; Slice 3a pulls it from the graph by handle.
- **Slice 4** — `agency_doctor.overflow_capture_health` reports a
  count of overflow Artefacts vs untracked-truncation events
  (invariant d: every truncate has a matching Artefact).
- **Slice 5** — Spec 082 `TokenCounter` injected at the boundary
  (replaces the proxy when `[anthropic]` extra installed); the
  capture/recall math becomes Anthropic-accurate.
- **Slice 6** — `Codes.OVERFLOW_CAPTURED` (Spec 151 invariant b);
  every truncated response carries the typed code so wrapping LLM
  drivers (Spec 147) can branch on it.
