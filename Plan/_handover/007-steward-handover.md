<!-- agency steward handover — read this first next run -->
# Steward Handover 007 — 2026-06-20

## What shipped this run

**Spec 338 — OpenRouter-first wet generation (complete).**

Owner directive: *"use OpenRouter free models instead of Anthropic when the key is in env."*
Spec 331 hardened `LLMClient` to free-only for decisions; Spec 338 extends the same
client with a free-text **`generate()`** method and a single **`select_text_generator()`**
provider-selection rule so all future wet specs have a free-first seam from day one.

### Key changes

**`agency/_llm.py`**
- `GenerationResult` frozen dataclass — `{text, model, backend, finish_reason}`;
  `backend` is typed `Literal["openrouter"]`.
- `_GENERATION_SYSTEM` constant — minimal system prompt for plain-text calls.
- `LLMClient._chat_text(key, prompt, model, *, system, max_tokens)` — plain-text
  companion to `_chat()` (no `response_format` / JSON schema); `# pragma: no cover - network`.
- `LLMClient.generate(prompt, *, system, max_tokens, model)` → `GenerationResult` —
  enforces `:free` suffix; raises `RuntimeError` when `OPENROUTER_API_KEY` absent.
- `select_text_generator(drivers, *, env=os.environ)` — the ONE provider-selection
  rule: `OPENROUTER_API_KEY` set → `("llm", drivers.get("llm"))` (OpenRouter wins
  for plain text regardless of `ANTHROPIC_API_KEY`); else `ANTHROPIC_API_KEY` →
  `("anthropic", drivers.get("anthropic"))`; else `RuntimeError(code: dependency_missing)`.

**`tests/acceptance/features/wet_generation.feature`** +
**`tests/acceptance/test_wet_generation.py`** — 6 hermetic Gherkin scenarios
(no real network calls):
1. OpenRouter wins when both keys set.
2. Anthropic fallback when only `ANTHROPIC_API_KEY` set.
3. `DEPENDENCY_MISSING` when neither key set.
4. `generate()` enforces `:free` suffix.
5. `generate()` raises when key absent.
6. `generate()` returns `GenerationResult` via mocked `httpx.post`.

## Evidence

- RED→GREEN: 6/6 scenarios pass.
- Full suite: **1248 green** (0 regressions).
- `scripts/check-drift` → NO DRIFT.
- `scripts/check-doc-drift --update` → 5 docs re-stamped.
- TODO.md Spec 338 row updated (Drafted → Shipped; Shipped count 89 → 90).
- `Plan/338-openrouter-first-wet-generation/spec.md` Followup added; status → shipped.
- Reflections: `reflection:6ef9dd5d` (candidate selection), `reflection:154c48b7` (lesson).

## Next 3 candidates (ranked)

1. **Spec 149 Slice 2.5 — alignment-matrix Goal column**
   `scripts/vision_matrix.py` (shipped 2026-06-20 as Spec 191 partial) derives the
   vision-alignment matrix but the TODO notes "Remaining (Slice 2): `check-doc-drift`
   CI gate + write the matrix into the `SPEC-VISION-ALIGNMENT.md` fence." Adding the
   CI gate closes the drift loop for the alignment matrix. Low-effort; high visibility.

2. **-wet spec consumer wiring (first one: Spec 311 Slice 2 — `discover.clarify`)**
   Now that Spec 338 ships the `select_text_generator` seam, the first consumer to
   wire it is `discover.clarify` Slice 2 (`ClarifySpec` wet Driver + grounding-sharp
   options). Depends on 147 Slice 2 for the Anthropic wet path, but `select_text_generator`
   routes it free-first when `OPENROUTER_API_KEY` is set — no longer blocked on paid
   Anthropic. Medium effort.

3. **Spec 153 Slice 5 — `AGENCY-SCHEMA-DEFERRED` tag scan**
   (Carried forward from handover 006.) Coverage is at 1.0 now, so urgency is low —
   but adding the tag escape hatch prevents future contributors from being forced to
   author a schema for every new node type immediately. Short addition to
   `scripts/check_schema_coverage.py` + one new test.

## Note: spec number collision (338)

Both `Plan/338-lifecycle-pillar-deep-program/` (draft lifecycle master) and
`Plan/338-openrouter-first-wet-generation/` (now shipped) carry `spec_id: "338"`.
Steward did NOT rename either — doctrine says renaming is rare and only warranted
after a naming collision on merge. Documented in TODO.md. A human reviewer should
assign a new number to the lifecycle master (candidate: 348, the next slot after
the lifecycle wave 338-347) before that program starts implementation.

## Pillar gate (held)

Intent/Capability/Lifecycle/Memory — all pillars read+write load-bearing.
Schema coverage: 89/89 = 1.0 (unchanged). Dormant schemas: 0. Drift: clean.
Doc-drift: clean (5 re-stamped this run). Suite: 1248 green.

## Key lesson

**Test the contract, not the network.** `_chat_text` is `# pragma: no cover - network`
but `generate()` above it is fully tested via `monkeypatch(httpx, "post", ...)`. This
split keeps CI fast and deterministic while proving the public contract (shape, :free
enforcement, key guard) at every run. The monkeypatch works because `_chat_text` does
`import httpx` locally — it reads from `sys.modules`, so patching the module attribute
at test setup time catches it before the local name is bound.
