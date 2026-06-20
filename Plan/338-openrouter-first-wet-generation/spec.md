---
spec_id: "338"
slug: openrouter-first-wet-generation
status: shipped
last_updated: 2026-06-20
owner: "@agency"
enhances: "331"
depends_on: ["331", "147", "092"]
vision_goals: [1, 4]
affects:
  - agency/_llm.py
  - agency/_drivers/_anthropic.py
  - tests/acceptance/features/wet_generation.feature
  - tests/acceptance/test_wet_generation.py
---

# Spec 338 — OpenRouter-first wet generation

## Why

Owner directive (2026-06-20): *"Use OpenRouter free models — when the API key
is in env — instead of Anthropic."*

Spec 331 already made the LLM **decider** (`agency/_llm.py::LLMClient`)
OpenRouter-free-only: the `decide(prompt, options)` classifier never touches
Anthropic, enforces a `:free` model id, and is gated on `OPENROUTER_API_KEY`.

But the wet **generation** boundary is the `AnthropicDriver` (Spec 147,
`agency/_drivers/_anthropic.py::complete`), which calls the Anthropic SDK
(`messages.create`) and bills against `ANTHROPIC_API_KEY`. The ~dozen `-wet`
Slice-2 specs that produce free-form text — **204** reasoning, **220** prose,
**226** thinking, **230** storyform, **240** scene-writer, **249** reveal,
**311** clarify, **317** acceptance, … — will each reach for generation. With
no free-first seam they would default to the **paid** Anthropic SDK the moment
they wire their runtime, silently violating the directive.

This spec adds a free-text **`generate`** method to the OpenRouter
`LLMClient` and a single **provider-selection rule** so plain-text generation
prefers OpenRouter free models whenever `OPENROUTER_API_KEY` is set, and only
falls back to Anthropic when (a) no OpenRouter key is present, or (b) the call
needs an **Anthropic-specific** feature (structured outputs, adaptive thinking,
managed-agents dispatch) that a free OpenRouter model can't honor.

Token **counting** is explicitly out of scope: OpenRouter has no
`count_tokens` endpoint, and Spec 201's Anthropic count backend is already
dormant without `ANTHROPIC_API_KEY` (OpenRouter-only setups count via
tiktoken/proxy). This spec covers generation only.

## Done When

- [ ] **`LLMClient.generate(prompt, *, system=None, max_tokens=1024,
      model=None) -> GenerationResult`** — a free-model chat completion over
      the existing `_chat` httpx plumbing, WITHOUT the strict-JSON decision
      schema (plain text out). `GenerationResult = {text: str, model: str,
      backend: Literal["openrouter"], finish_reason: str}`. Enforces the
      `:free` suffix on `model` exactly as `decide()` does (cost-safety — a
      misconfigured override never silently bills).
- [ ] **`select_text_generator(drivers, *, env=os.environ) -> (name, driver)`**
      — the ONE provider-selection rule for plain-text generation:
      `OPENROUTER_API_KEY` set → the `llm` (OpenRouter) driver; else
      `ANTHROPIC_API_KEY` set → the `anthropic` driver; else raise the typed
      `Codes.DEPENDENCY_MISSING` (never a silent paid path, never a crash).
- [ ] **Anthropic-specific features keep their explicit escape.** A verb that
      needs structured outputs / adaptive thinking / managed-agents dispatch
      requests the `anthropic` driver DIRECTLY (documented) — those do not
      route through `select_text_generator`, because a free OpenRouter model
      can't honor them. Plain free-form text is the only thing routed free-first.
- [ ] **Measurable invariants** (relationships, not pinned values):
      - `OPENROUTER_API_KEY` set ⇒ `select_text_generator(...)[0] == "llm"`
        (the OpenRouter backend), regardless of whether `ANTHROPIC_API_KEY` is
        also set — the directive wins for plain text.
      - `generate()` only ever returns a model id ending in `:free`
        (same cost-safety enforcement as `decide()`).
      - neither key set ⇒ `select_text_generator` raises
        `Codes.DEPENDENCY_MISSING` (typed; the verb degrades, never crashes).
      - a structured-output / thinking request is NOT routed to OpenRouter free
        (feature-gated: it requires the `anthropic` driver or degrades with a
        typed code) — proven by the selection rule covering only the plain-text
        path.
- [ ] **Failure-mode coverage** — OpenRouter `RATE_LIMITED` / `TIMEOUT` /
      `AUTH_FAILED` surface a typed error (NO automatic Anthropic fallback for a
      free-first call — falling back to a paid provider on a transient free
      error would violate the directive; an explicit `AGENCY_GENERATE=anthropic`
      override is the documented opt-in).
- [ ] **The `-wet` specs consume the seam.** 204 / 220 / 226 / 230 / 240 / 249
      / 311 / 317 (and siblings) call `select_text_generator` for their
      plain-text generation; their Followups note the free-first default. (This
      spec ships the seam + tests; each `-wet` spec wires its own consumer.)
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  OPENROUTER_API_KEY set, ANTHROPIC_API_KEY also set
When:   a wet verb calls select_text_generator(ctx.drivers) for plain text
Then:   it returns ("llm", <OpenRouter LLMClient>) — NOT the anthropic driver
        AND generate("draft a one-line summary of X") returns
            GenerationResult{text:"…", model:"…:free", backend:"openrouter"}

Given:  only ANTHROPIC_API_KEY set (no OpenRouter key)
When:   select_text_generator(ctx.drivers) runs
Then:   it returns ("anthropic", <AnthropicDriver>) — the documented fallback

Given:  neither key set
When:   select_text_generator(ctx.drivers) runs
Then:   raises Codes.DEPENDENCY_MISSING with a hint naming both env vars
        AND the verb degrades to its deterministic Spec-147 typed shape

Given:  a verb needs structured JSON output (output_config.format)
When:   it routes generation
Then:   it requests the `anthropic` driver directly (free OpenRouter models
        can't honor structured outputs) — select_text_generator is for plain
        text only
```

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| `OPENROUTER_API_KEY` unset, `ANTHROPIC_API_KEY` set | fall back to the `anthropic` driver (documented) |
| Both keys unset | `Codes.DEPENDENCY_MISSING`; verb degrades to its deterministic shape |
| OpenRouter `RATE_LIMITED` / `429` | typed error; NO silent paid Anthropic fallback (directive) — retry per `_chat` or surface |
| OpenRouter `TIMEOUT` | typed `timeout` error; same no-paid-fallback rule |
| Free model unavailable mid-session | `AGENCY_LLM_MODEL=auto` re-resolves the best live free model (Spec 331) |
| Verb needs structured output / thinking | NOT routed free; requires the `anthropic` driver or degrades with a typed code |
| Misconfigured non-free `model=` override | `ValueError` at `generate()` — the same `:free` enforcement as `decide()` |

## Interconnects

- **Spec 331** (openrouter-free-provider) — this extends the SAME `LLMClient`
  with `generate` alongside `decide`; reuses `_chat`, `resolve_model`, and the
  `:free` enforcement.
- **Spec 147** (anthropic-driver-boundary) — `AnthropicDriver` remains the home
  for Anthropic-specific features (structured outputs, adaptive thinking,
  managed-agents); this spec adds the selection rule, not a replacement.
- **Specs 204 / 220 / 226 / 230 / 240 / 249 / 311 / 317** (the `-wet`
  generation specs) — consumers; default free-first via `select_text_generator`.
- **Spec 263** (claude-fable-driver-extras) — the Anthropic-specific feature
  path that legitimately stays on the `anthropic` driver.
- **Spec 201** (token-counter) — counting is orthogonal: OpenRouter has no
  count endpoint, so it stays Anthropic-when-keyed / tiktoken-otherwise.
- **Spec 092 G3** — the `llm` Driver registration this builds on.

## Open questions

1. **Both keys set — which wins for plain text?** **Recommend**: OpenRouter
   free (the directive). Anthropic is used for plain text only via an explicit
   `AGENCY_GENERATE=anthropic` override (documented config, not a silent
   default).
2. **Quality floor — free models vary.** **Recommend**: rely on Spec 331's
   `AGENCY_LLM_MODEL=auto` preference ranking; a verb may pass a per-call
   `:free` model. Quality-sensitive verbs document an Anthropic opt-in.
3. **Streaming.** OpenRouter supports SSE. **Recommend**: a `generate_stream()`
   follow-up slice; Slice 1 is non-streaming text (the `_chat` shape already
   used by `decide`).
4. **Retry-then-fallback?** Should a persistent OpenRouter outage fall back to
   Anthropic? **Recommend**: NO by default (a paid fallback on a free-first
   call violates the directive); make it an explicit opt-in env flag so the
   cost is never a surprise.

## Followup — Implementation Status (2026-06-20, steward run)

### Done — Slice 1 (complete, 2026-06-20)

- **`GenerationResult` frozen dataclass** — `agency/_llm.py` (after constants):
  `{text: str, model: str, backend: Literal["openrouter"], finish_reason: str}`.
- **`_GENERATION_SYSTEM`** constant — minimal system prompt for plain-text calls.
- **`LLMClient._chat_text(key, prompt, model, *, system, max_tokens)`** —
  plain-text companion to `_chat()` (no `response_format` / JSON schema);
  returns `(text, finish_reason)`; `# pragma: no cover - network` (same
  convention as `_chat()`).
- **`LLMClient.generate(prompt, *, system, max_tokens, model)`** —
  enforces `:free` suffix; raises `RuntimeError` when `OPENROUTER_API_KEY`
  absent; returns `GenerationResult`.
- **`select_text_generator(drivers, *, env=os.environ)`** — module-level
  selection rule: `OPENROUTER_API_KEY` → `("llm", drivers.get("llm"))`;
  `ANTHROPIC_API_KEY` → `("anthropic", drivers.get("anthropic"))`; neither
  → `RuntimeError(code: dependency_missing)`.
- **6 Gherkin scenarios** in `tests/acceptance/features/wet_generation.feature`
  + `tests/acceptance/test_wet_generation.py` (all hermetic — no network):
  1. OpenRouter wins when both keys set.
  2. Anthropic fallback when only `ANTHROPIC_API_KEY` set.
  3. `DEPENDENCY_MISSING` when neither key set.
  4. `generate()` enforces `:free` suffix.
  5. `generate()` raises when key absent.
  6. `generate()` returns `GenerationResult` via mocked `httpx.post`.
- Full suite **1248 green**; drift clean; 5 docs re-stamped (check-doc-drift).
- TODO.md Spec 338 row updated (Drafted → Shipped; count 89 → 90).

### Still — consumer wiring

Each `-wet` spec (204/220/226/230/240/249/311/317) needs to wire
`select_text_generator(ctx.drivers)` as its generation seam in Slice 2.
This spec ships the seam; each consumer spec wires its own call.
