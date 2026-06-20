---
spec_id: "279"
slug: host-llm-delegation
status: partial
last_updated: 2026-06-11
owner: "@agency"
enhances: "147"
depends_on: ["147", "029", "002", "151", "149"]
vision_goals: [3, 4, 8]
affects:
  - agency/_host_llm.py
  - agency/_drivers/_anthropic.py
  - tests/test_host_llm_delegation.py
---

# Spec 279 — Host-LLM delegation envelope

## Why

Today the AnthropicDriver (Spec 147) returns `DriverError.AUTH_FAILED`
when there's no `ANTHROPIC_API_KEY` and no injected client. Verbs that
wrap the driver either crash, degrade to a scaffold path (lossy — the
intent is lost), or wrap the error and return `ok=False` to the caller.

But the agency plugin is run **INSIDE Claude Code** — the host
orchestrator IS an LLM. When the AnthropicDriver isn't capable, the
verb should hand control BACK to Claude Code, let it perform the
inference using its own model, and then resume the verb with the
result. The provenance moat stays intact (the `Invocation` records the
delegation + the host completion), and the verb's contract is the same
regardless of who actually ran the LLM.

This is the **host-LLM delegation** pattern. It's a cross-cutting
substrate concern: every LLM-using verb adopts the same wrapping helper,
so the pattern composes uniformly.

## Done When

- [ ] **`agency/_host_llm.py`** ships:
      - `HostLLMRequest{kind="llm_delegate", messages, system,
        output_schema, continuation_token, model_hint?, max_tokens?}` —
        frozen dataclass returned by the boundary helper when the driver
        backend is "none". `kind` is the wire signal Claude Code
        recognizes; `continuation_token` is opaque to the host and used
        by the verb to resume.
      - `complete_or_delegate(driver, *, messages, system,
        output_schema=None, host_completion=None, model_hint=None,
        max_tokens=8000) -> Completion | HostLLMRequest` — the boundary
        helper every LLM-using verb wraps. Three branches:
        1. `host_completion` is given → wrap it as `Completion(text,
           parsed, stop_reason="host_provided")` and return.
        2. driver.backend() != "none" → call `driver.complete(...)` as
           in Spec 147 Slice 1.
        3. else → return `HostLLMRequest{...}` so the caller delegates
           to the host.
- [ ] **Wire contract update** (Spec 029 / CORE.md): any verb response
      whose merged dict carries `"kind": "llm_delegate"` IS a host
      delegation signal. Claude Code (the host) MUST run the inference
      with the documented shape (messages + system; optional
      output_schema) and call the verb again passing the result back
      via the documented `host_completion` parameter.
- [ ] **`continuation_token`** is opaque to the host but stable across
      the delegation round-trip: the verb mints it on first call,
      stores any state it needs in the graph keyed by the token, and
      looks it up on resume. Default token shape: SHA-256 of
      `(intent_id, verb_name, json(args)[:200])` — deterministic so
      retries don't multiply.
- [ ] **Provenance invariant** (rule 8): a delegated round-trip records
      EXACTLY ONE `Invocation` node (mints on first call, the `outcome`
      property flips to `"host_resumed"` on the second call). The graph
      stays lossless across delegation.
- [ ] **Backwards compatibility** — when `host_completion=None` AND the
      driver IS capable, behavior is identical to Spec 147 Slice 1
      (`Completion` returned). No existing verb breaks.
- [ ] **Acceptance invariants**:
      (a) `complete_or_delegate(capable_driver, ...)` returns
          `Completion` (driver path);
      (b) `complete_or_delegate(no_backend_driver, ...)` returns
          `HostLLMRequest` (delegate path);
      (c) `complete_or_delegate(driver, host_completion=X)` returns
          `Completion(stop_reason="host_provided", text=X["text"])`
          regardless of driver backend (resume path always wins).
- [ ] **Failure modes** (Spec 151 Codes):
      - `host_completion` is malformed (no `text` field) →
        `Codes.HOST_DELEGATE_MALFORMED` raised at the boundary.
      - the output_schema was specified but `host_completion["parsed"]`
        is missing or doesn't validate →
        `Codes.HOST_DELEGATE_SCHEMA_FAIL` (parsed schema validation is
        Slice 2; Slice 1 trusts the host).
- [ ] **Test:** with capable driver returns Completion; without driver
      returns HostLLMRequest envelope; with host_completion provided
      returns Completion(stop_reason="host_provided"); typed shapes are
      frozen / immutable; `continuation_token` is deterministic per
      (intent, verb, args).
- [ ] **TODO row + drift clean.**

## Worked example (Given/When/Then)

```text
Given:  no ANTHROPIC_API_KEY; verb `novel.generate_scene` calls
        complete_or_delegate(driver, messages=[...], system="...")
When:   driver.backend() == "none"
Then:   complete_or_delegate returns HostLLMRequest{
            kind: "llm_delegate",
            messages: [...],
            system: "...",
            continuation_token: "<sha256[:32]>"
        }
        AND the verb's return envelope carries kind=llm_delegate so
        Claude Code knows to delegate

Given:  Claude Code performed the inference and got `text="<the scene>"`
When:   Claude Code calls novel.generate_scene again with
        host_completion={text: "<the scene>"}
Then:   the verb's complete_or_delegate sees host_completion and
        returns Completion(text="<the scene>", stop_reason="host_provided")
        AND the verb continues its normal flow
        AND the Invocation node's `outcome` flips from "host_delegated"
        to "host_resumed" (single-Invocation invariant)

Given:  ANTHROPIC_API_KEY IS set, no host_completion provided
When:   complete_or_delegate runs
Then:   driver.complete(...) called as in Spec 147 Slice 1; returns
        a typed Completion; no delegation envelope emitted
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Lossy delegation | host runs the inference but never resumes | continuation_token times out (default 1h) | typed `Codes.HOST_DELEGATE_TIMEOUT`; the agent retries (idempotent) |
| Token forgery | host fakes a token from another verb | SHA-256 over `(intent_id, verb, args)` — host can't synthesize without seeing the args | invariant: verb rejects mismatched tokens with BAD_REQUEST |
| Schema mismatch on resume | host returned text not matching output_schema | Slice 2 validates `host_completion["parsed"]` against the schema | typed `Codes.HOST_DELEGATE_SCHEMA_FAIL` |
| Provenance split | two Invocation nodes for one round-trip | invariant (provenance) — Slice 1 mint-once-flip-on-resume | rule 8 test asserts node count |

## Interconnects

- **LLM-driver chain (Spec 147)**: this is the substrate side of the
  same chain. Slice 1 anchors `dispatch_session`; Slice 279 anchors
  the host-fallback pattern. Together they cover BOTH "API-key driver
  ready" + "host orchestrator IS the driver" cases.
- Spec 150 (dogfood classifier) — Slice 2 currently swaps in the
  AnthropicDriver structured-output classifier. With 279, when there's
  no key, the classifier delegates back to Claude Code instead of
  falling back to the keyword path. Same UX, same provenance.
- Spec 220 (novel-prose-driver-wet) — the entire novel cluster's wet
  wave depends on 279 because most installations won't have the
  Anthropic key.
- Spec 232 / 251 / 254 (novel editorial/briefing/voice slices) —
  all use complete_or_delegate.
- Spec 029 / CORE.md — wire contract gets a new envelope kind
  (`llm_delegate`).
- Spec 002 — Boundary/Driver protocol; this helper is a typed
  substrate wrapper around the driver.
- Spec 149 derive-docs — the `kind="llm_delegate"` envelope is one of
  the documented response shapes derived into the alignment matrix.
- Spec 151 (Codes coverage) — supplies `HOST_DELEGATE_MALFORMED` +
  `HOST_DELEGATE_SCHEMA_FAIL` + `HOST_DELEGATE_TIMEOUT`.
- Spec 248 / 252 (novel skill walks managed) — Slice 2.x extends 279
  to handle Managed-Agents session fan-out (when the host hands a
  full sub-session back, not just a single completion).

## Open questions

1. **Should `continuation_token` be a graph node or a SHA-derived
   value?** **Recommend**: SHA-derived for Slice 1 (cheap, idempotent,
   stateless). A graph node lands in Slice 3 when we need richer
   resume state (multi-turn conversations, tool use).
2. **What output_schema enforcement applies to host_completion?**
   **Recommend**: Slice 1 trusts the host; Slice 2 validates
   `host_completion["parsed"]` against the schema; Slice 3 has the host
   negotiate the schema before delegation.
3. **Should the helper auto-detect Claude Code as the host?**
   **Recommend**: no, this is just an envelope contract — any host
   that recognizes `kind="llm_delegate"` participates. Claude Code IS
   the documented first consumer.

## Followup — Implementation Status (Slice 1, 2026-06-12)

### Done — Slice 1 (envelope + boundary helper)

- **`agency/_host_llm.py` ships** — the typed substrate library:
  - `HostLLMRequest` (frozen `@dataclass(frozen=True)`) with the wire
    shape `{kind, messages, system, continuation_token, output_schema?,
    model_hint?, max_tokens=8000}`. `__post_init__` rejects wrong
    `kind`, non-tuple `messages` (frozen-friendly), empty
    `continuation_token`. `to_dict()` emits `kind` FIRST so the host
    dispatcher can route on the leading bytes; optional fields are
    omitted when None (keeps the prefix tight per Spec 146).
  - `make_continuation_token(intent_id, verb_name, args)` — the
    default token shape: SHA-256 (first 32 hex chars) of
    `(intent_id, verb_name, json(args, sort_keys)[:200])`.
    Deterministic across retries; opaque to the host (forgery
    defense — the host can't synthesize without seeing the args).
  - `_derive_fallback_token(messages, system, model_hint)` —
    helper-internal fallback when the verb doesn't supply a token;
    derives from the request shape itself so the envelope still
    carries a stable token.
  - `HostDelegateError` typed failure with `MALFORMED` /
    `SCHEMA_FAIL` / `TIMEOUT` codes (Spec 151 hookup).
  - `complete_or_delegate(driver, *, messages, system, output_schema=None,
    host_completion=None, model_hint=None, max_tokens=8000,
    continuation_token=None) -> Completion | HostLLMRequest` —
    the boundary helper. Three branches, resume path WINS:
    1. `host_completion` given → `Completion(text=…,
       stop_reason="host_provided", parsed=…)`. Driver NOT invoked.
    2. `driver.backend() != "none"` → `driver.complete(...)` direct
       (Spec 147 Slice 1; backwards-compat invariant — behavior
       identical to a bare `driver.complete(...)`).
    3. else → `HostLLMRequest{kind="llm_delegate", ...}` envelope.
  - Raises `HostDelegateError(MALFORMED)` when `host_completion` is
    non-dict or missing `text` — Slice 1 trusts the host on schema;
    Slice 2 will validate `parsed` against `output_schema`.

- **21 tests green** (`tests/test_host_llm_delegation.py`) covering:
  - `HostLLMRequest` frozen + kind/messages/token validation +
    `to_dict()` order + optional-field omission (6 tests).
  - `make_continuation_token` determinism + variance with args / verb
    name / intent_id (4 tests — forgery defense + provenance
    invariant).
  - Branch 2 (driver capable) — uses driver, forwards
    `output_schema` (2 tests).
  - Branch 3 (no backend) — emits envelope with default + provided
    continuation_token, carries `output_schema` / `model_hint` /
    `max_tokens` (3 tests).
  - Branch 1 (resume) — returns `Completion(host_provided)`, wins
    over capable driver, carries `parsed`, raises MALFORMED on
    missing `text` or non-dict (5 tests).
  - `DEFAULT_MAX_TOKENS` constant pin (1 test).

### Still — Slice 2+

- **Slice 2** — `output_schema` validation on
  `host_completion["parsed"]` (when output_schema is supplied at
  request time, on resume the helper validates parsed against the
  schema; raises `HostDelegateError(SCHEMA_FAIL)` →
  `Codes.HOST_DELEGATE_SCHEMA_FAIL` per Spec 151).
- **Slice 2.x — managed-agents hand-off** (Specs 248 / 252) — extends
  the envelope kind family with `kind="session_delegate"` for cases
  where the host hands back a full sub-session (not just a single
  completion).
- **Slice 3** — `continuation_token` as a graph node (multi-turn
  resume + tool use). Today the token is a stateless SHA hash;
  promote to a `Continuation` node when richer resume state is
  needed.
- **Wire contract update** (CORE.md / Spec 029) — document
  `kind="llm_delegate"` as the second envelope kind alongside
  `kind="tool_call"` so external implementers know it's part of the
  protocol.
- **Spec 147 integration** — `AnthropicDriver.complete()` learns the
  same resume signal: when called with `host_completion=…`, returns
  the same `Completion(stop_reason="host_provided")` so callers can
  always use the driver surface uniformly.
- **First consumer cluster** — wire Spec 150 Slice 2 (dogfood
  classifier) and Spec 220 (novel-prose-driver-wet) through
  `complete_or_delegate` so the no-key path delegates instead of
  raising AUTH_FAILED.
- **Provenance invariant test** — once a verb consumes the helper,
  add a graph-level test asserting a single Invocation node per
  delegated round-trip with `outcome` flipping
  `"host_delegated"` → `"host_resumed"` (rule 8 single-Invocation
  invariant).
- **Spec 151 Codes wire-up** — register `HOST_DELEGATE_MALFORMED` /
  `HOST_DELEGATE_SCHEMA_FAIL` / `HOST_DELEGATE_TIMEOUT` in the
  central Codes enum so the audit recognises them.
