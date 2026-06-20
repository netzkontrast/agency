---
spec_id: "338"
slug: openrouter-first-wet-generation
status: draft
last_updated: 2026-06-20
owner: "@agency"
enhances: "331"
depends_on: ["331", "147", "092"]
vision_goals: [1, 4]
affects:
  - agency/_llm.py
  - agency/_drivers/_anthropic.py
  - pyproject.toml
  - .agency/config.yaml
  - tests/acceptance/features/wet_generation.feature
  - tests/acceptance/test_wet_generation.py
---

# Spec 338 — OpenRouter-first wet generation + use-case model selection

## Why

Owner directive (2026-06-20): *"Use OpenRouter free models — when the API key
is in env — instead of Anthropic."* And, refining it through a spec-panel +
brainstorm: *"a model list with priority and use-case, plus flags the LLM
driver can be started with (like `novel` — different requests need different
models); a config for the ordered list; fetch model info directly from
OpenRouter; install the OpenRouter SDK as a default dependency."*

Spec 331 made the LLM **decider** (`agency/_llm.py::LLMClient`) OpenRouter-free
only: `decide(prompt, options)` enforces a `:free` model id, is gated on
`OPENROUTER_API_KEY`, and never touches Anthropic. But two gaps remain:

1. **Generation.** Wet free-form text is the `AnthropicDriver`'s `complete`
   (Spec 147) — the Anthropic SDK, billed against `ANTHROPIC_API_KEY`. The
   ~dozen `-wet` specs (204 reasoning, 220 prose, 226 thinking, 230 storyform,
   240 scene-writer, 249 reveal, 311 clarify, 317 acceptance, …) would each
   default to the **paid** SDK the moment they wire their runtime.
2. **Model selection is flat.** `_MODEL_PREFERENCE` is a single global ranking;
   it can't say "reasoning wants DeepSeek-R1, prose wants Llama-70B, code wants
   Qwen-Coder." A clustered consumer like `novel` needs different models for
   different request types.

This spec adds (a) a **use-case-tagged, priority-ordered model registry** with
flags, populated/validated from **live OpenRouter model info via the official
SDK**; (b) a free-text **`generate`** method + the single **provider-selection
rule** so plain-text generation prefers OpenRouter free models; and (c) a
**barbell recovery** — never a silent paid fallback, but a loud per-call
`require="anthropic"` opt-in (the spec-panel's Taleb finding).

**Out of scope:** token **counting** — OpenRouter has no `count_tokens`
endpoint, and Spec 201's Anthropic count backend is already dormant without
`ANTHROPIC_API_KEY`. Counting stays Anthropic-when-keyed / tiktoken otherwise.

## Spec-panel findings folded in (panel:78a56705)

- **Christensen/Drucker/Taleb — quality gate:** gating Anthropic only by
  *feature* under-serves quality-sensitive plain text. → per-call
  `require="anthropic"` opt-in (owner-chosen).
- **Taleb — fragility:** hard-fail on a free outage is fragile; silent paid
  fallback violates the directive. → barbell: typed error, caller re-calls with
  `require="anthropic"` (loud, explicit, never a silent bill).
- **Porter/Meadows — single leverage point:** `select_text_generator` is the
  SOLE plain-text path; no verb constructs an `AnthropicDriver` directly.
- **Meadows — feedback loop:** per-(use_case, model) quality/failure learning is
  the highest future leverage → named as a deferred slice, not built now.

## Done When

### Slice 1 — registry + selection + generation seam

- [ ] **`ModelProfile` registry** (`agency/_llm.py`) — a priority-ordered list
      of free models, each `{id (\`:free\`), use_cases: tuple[str,...],
      priority: int, flags: dict}`. Built-in default works with ZERO config;
      a `models:` block in `.agency/config.yaml` OVERRIDES it (rule 8 —
      documented config, not a frozen snapshot of live state).
- [ ] **Use-case selection** — `select_model(use_case, *, live_ids=None) ->
      str` walks the registry filtered to `use_case`, sorted by `priority`,
      and returns the first id that is BOTH in the registry AND (when
      `live_ids` is supplied) live-available; falls back across:
      explicit `model=` → registry pick → `_DEFAULT_MODEL`. A `general`
      use-case is the catch-all every model carries.
- [ ] **OpenRouter SDK as a core dependency** — `openrouter` added to
      `[project.dependencies]` (replacing the raw-`httpx` GET in
      `list_free_models`). A thin `_openrouter_models()` boundary returns the
      live free-model catalogue with `flags` (`context_length`, pricing-zero,
      `supports_json` where exposed); the registry's `flags` are POPULATED
      from it, never hand-frozen (rule 8). The fetch is lazy + failure-isolated
      (no network at import; a fetch failure degrades to the built-in registry).
- [ ] **Driver flags** — `LLMClient(model=None, use_case="general",
      require=None, auto=False)`: started with a default use-case + optional
      pinned model + `auto` (live-discovery) + `require` ("anthropic" forces
      the Anthropic path). `:free` enforced on every resolved OpenRouter model
      (cost-safety, same as `decide`).
- [ ] **`LLMClient.generate(prompt, *, use_case=None, system=None,
      max_tokens=1024, model=None) -> GenerationResult`** — plain-text free
      completion over the SDK; `GenerationResult = {text, model, backend:
      "openrouter", finish_reason}`. `use_case` selects the model via the
      registry; per-call `use_case` overrides the driver default.
- [ ] **`select_text_generator(drivers, *, env=os.environ, require=None) ->
      (name, driver)`** — the SOLE plain-text path:
      `require=="anthropic"` OR (no `OPENROUTER_API_KEY` AND `ANTHROPIC_API_KEY`
      set) → the `anthropic` driver; `OPENROUTER_API_KEY` set → the `llm`
      driver; neither key → typed `Codes.DEPENDENCY_MISSING`.
- [ ] **Anthropic keeps its explicit escape** — structured outputs / adaptive
      thinking / managed-agents dispatch request the `anthropic` driver
      DIRECTLY (a free model can't honor them); only plain text is routed
      free-first.
- [ ] **No silent paid fallback** — a free `RATE_LIMITED`/`TIMEOUT`/`AUTH`
      error surfaces a typed error; recovery is the caller re-invoking with
      `require="anthropic"` (barbell). An `AGENCY_GENERATE=anthropic` env is the
      documented all-session opt-in.
- [ ] **Measurable invariants** (relationships, not pinned values):
      - `OPENROUTER_API_KEY` set + `require=None` ⇒ `select_text_generator(...)
        [0] == "llm"` even when `ANTHROPIC_API_KEY` is also set (directive wins).
      - `require="anthropic"` ⇒ `[0] == "anthropic"` regardless of keys present
        (and raises `DEPENDENCY_MISSING` when no Anthropic key).
      - neither key ⇒ `DEPENDENCY_MISSING` (typed; verb degrades, never crashes).
      - every model `select_model`/`generate` resolves ends in `:free`.
      - `select_model(uc)` for a registered use-case returns a model whose
        `use_cases` contains `uc` (or the documented `_DEFAULT_MODEL` fallback);
        registry partition: every model carries ≥1 use-case.
      - config override REPLACES the built-in registry deterministically
        (same input → same selection).
- [ ] TODO row + drift clean + install regen if the surface changed.

### Slice 2+ (named, not built)

- [ ] **`-wet` consumers** (204/220/226/230/240/249/311/317) call
      `select_text_generator` + `generate(use_case=…)`; each Followup notes the
      free-first default and its use-case.
- [ ] **Streaming** `generate_stream()` (OpenRouter SSE).
- [ ] **Feedback loop** — record per-(use_case, model) success/failure as graph
      provenance; `select_model` prefers models that worked (Meadows leverage).

## Worked example (Given/When/Then)

```text
Given:  OPENROUTER_API_KEY set; ANTHROPIC_API_KEY also set; registry maps
        reasoning→[deepseek-r1:free(p10), …], prose→[llama-70b:free(p30), …]
When:   a reasoning verb calls select_text_generator(ctx.drivers) then
        generate("weigh X vs Y", use_case="reasoning")
Then:   the generator is ("llm", LLMClient)  — NOT anthropic
        AND the resolved model is deepseek-r1:free (live-available, top priority)
        AND GenerationResult.backend == "openrouter", model ends ":free"

Given:  a prose verb wants Anthropic-grade output
When:   it calls select_text_generator(ctx.drivers, require="anthropic")
Then:   returns ("anthropic", AnthropicDriver) — the explicit quality opt-in

Given:  OPENROUTER_API_KEY set; the free model 429s
When:   generate(...) runs
Then:   raises a typed error (no silent paid fallback)
        AND the caller MAY re-invoke select_text_generator(require="anthropic")

Given:  novel needs scene prose vs. a structured beat-sheet
When:   it calls generate(use_case="prose") and, for the beat-sheet,
        get_driver("anthropic").complete(output_schema=…)
Then:   prose routes to a free prose-tagged model; the structured call uses the
        Anthropic driver directly (free models can't honor output_config.format)

Given:  .agency/config.yaml has a models: block
When:   the LLMClient resolves
Then:   the config registry REPLACES the built-in default (override, rule 8)
```

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| `OPENROUTER_API_KEY` unset, `ANTHROPIC_API_KEY` set | fall back to `anthropic` (documented) |
| Both keys unset | `Codes.DEPENDENCY_MISSING`; verb degrades to its Spec-147 typed shape |
| OpenRouter model fetch fails | degrade to the built-in registry (no network at import; fetch is best-effort) |
| Free model 429 / timeout / pulled mid-session | typed error; barbell recovery via `require="anthropic"`; `auto` re-resolves the next live free model |
| `use_case` unknown to the registry | resolve via `general`, else `_DEFAULT_MODEL` (never crash) |
| Misconfigured non-free `model=` override | `ValueError` at construction / call (same `:free` enforcement as `decide`) |
| Verb needs structured output / thinking | NOT routed free; requires the `anthropic` driver |
| Config `models:` block malformed | fail closed to the built-in registry + a typed warning (Spec 058) |

## Interconnects

- **Spec 331** (openrouter-free-provider) — extends the SAME `LLMClient`:
  `generate` + the registry sit beside `decide`; reuses `:free` enforcement,
  `resolve_model`, and the model fetch (now via the SDK).
- **Spec 147** (anthropic-driver-boundary) — `AnthropicDriver` stays the home
  for Anthropic-specific features; this spec adds the selection rule.
- **Specs 204/220/226/230/240/249/311/317** — `-wet` consumers; free-first via
  `select_text_generator` + use-case selection.
- **Spec 094/101** (music/novel clusters) — the clustered consumers that need
  per-request-type models (`novel`'s scene vs. brief).
- **Spec 263** (claude-fable-driver-extras) — the legit Anthropic-specific path.
- **Spec 201** (token-counter) — orthogonal; counting stays Anthropic-when-keyed.
- **Spec 334** (unified-config) — `.agency/config.yaml` is the override home.

## Open questions

1. **Both keys set — which wins for plain text?** **Resolved**: OpenRouter free
   (the directive). Anthropic for plain text only via per-call
   `require="anthropic"` or the `AGENCY_GENERATE=anthropic` env override.
2. **Use-case taxonomy — fixed or open?** **Recommend**: OPEN set of strings
   (a model declares whatever use-cases it serves; `general` is the catch-all).
   No frozen enum to maintain; consumers coin use-cases as needed.
3. **SDK vs httpx.** **Resolved** (owner directive): the official `openrouter`
   SDK as a core dep — type-safe, Pydantic-validated, tracks the live model
   catalogue. The raw-`httpx` GET in `list_free_models` is replaced by the SDK
   behind a thin `_openrouter_models()` boundary (one swap site).
4. **Where do `flags` come from?** **Resolved**: populated from live OpenRouter
   model info (`context_length`, zero-pricing, capabilities) — derived, never
   hand-frozen (rule 8). The built-in registry carries only `id` + `use_cases` +
   `priority`; `flags` hydrate at fetch time.
