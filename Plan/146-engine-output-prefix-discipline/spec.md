---
spec_id: "146"
slug: engine-output-prefix-discipline
status: partial
last_updated: 2026-06-11
owner: "@agency"
enhances: "023"
depends_on: ["023", "067", "082", "147", "149"]
vision_goals: [1, 6]
affects:
  - agency/_envelope.py
  - agency/_lints/_response_prefix.py
  - tests/test_response_prefix_discipline.py
---

# Spec 146 — Engine output-prefix discipline (cache-friendly substrate)

## Why

Spec 023 ships token-budget slicing; Spec 067 ships *name* token-budget
lint. Neither budgets the BYTES returned by `mcp__agency__{search,
get_schema, execute}` to the LLM driver that wraps the engine. The
Claude API's prompt-caching is a **prefix match** — any byte change
anywhere in the prefix invalidates everything after it (`claude-api`
skill, `shared/prompt-caching.md`). Today substrate-tool responses
interpolate `datetime.now()` ISO timestamps + intent-id UUIDs into the
HEAD of every response — silently invalidating every wrapper's cache.

## Done When

- [ ] **`agency/_envelope.py` defines `ResponseEnvelope{prefix, body}`** —
      `prefix` = `{schema_version, capability_set_hash, ontology_hash}`
      (frozen per build); `body` = `{intent_id, timestamps, payload,
      next_cursor}` (per-call). Serializer renders `prefix` then `body`
      in deterministic key order (sorted JSON). The Claude API caller
      places `cache_control: {type: "ephemeral"}` on the prefix.
- [ ] **`_check_response_prefix` lint rule** (Spec 067 family, AST):
      flags `datetime.now()`/`time.time()`/`uuid4()`/unsorted-dict and
      any read of `os.environ` resolving at request-time inside any
      function reachable from a substrate-tool's prefix builder. WARN
      one cycle (Spec 056/058 pattern), then promote to **error** once
      the live registry reports zero violations.
- [ ] **`agency_doctor` reports `prefix_stability`** = `{stable: bool,
      drift_bytes: int, drift_tokens: int, prefix_size_tokens: int}` —
      drift is the byte-delta of `prefix` across two `agency_welcome`
      calls separated by 60s. Invariant: `drift_bytes == 0` whenever the
      capability set has not changed. Token count via Spec 082 locally,
      Spec 201 API count when `[anthropic]` extra installed.
- [ ] **Cache-hit invariant test** — beyond byte-stability, exercise the
      Claude API path with a mocked client: assert
      `usage.cache_read_input_tokens > 0` on the second call against the
      live `agency_welcome` prefix (≥ 1024 tokens — claude-api skill
      minimum). On Opus 4.6/4.8 and Haiku 4.5 the minimum is 4096; the
      test parameterizes by model.
- [ ] **Failure mode: prefix overflow** — when capability set grows
      such that the prefix exceeds `MAX_PREFIX_TOKENS` (a configured
      budget, default 8000 tokens), the envelope must REJECT the
      response with `Codes.PREFIX_BUDGET_EXCEEDED` (Spec 151) — never
      silently truncate the prefix, which would partial-cache.
- [ ] **TODO row + drift clean.**

## Worked example (Given/When/Then)

```text
Given:  capability set unchanged between calls
When:   call agency_welcome() twice 60s apart with an LLM driver wrapping
        the engine, cache_control on prefix
Then:   response 2's usage.cache_read_input_tokens > 0 AND
        envelope.prefix bytes are byte-identical to response 1's

Given:  a verb's prefix-builder calls datetime.now()
When:   _check_response_prefix lint runs (post-WARN cycle)
Then:   lint fails with PREFIX_NONDETERMINISTIC pointing at the call site

Given:  capability count grows past MAX_PREFIX_TOKENS
When:   any substrate tool returns
Then:   response carries Codes.PREFIX_BUDGET_EXCEEDED — never silent
        truncation that would partial-cache
```

## Interconnects

- Drives the **output-budget chain** the charter declares.
- Spec 147 (AnthropicDriver) honors the prefix split: every wrapped
  call ships `cache_control: {type:"ephemeral"}` on the prefix.
- Spec 149 (derived docs) consumes `prefix_stability` as a derived
  field; treats `drift_bytes > 0 without capability-set change` as a
  drift bug.
- Spec 154 (output-overflow) caps body, never prefix.
- Spec 201 (TokenCounter API backend) provides authoritative counts
  when the `[anthropic]` extra is installed.
- Spec 257 (managed-agents cache proof) re-verifies prefix-stability
  across Managed-Agents session boundaries.
- Spec 151 (Codes coverage) supplies `PREFIX_BUDGET_EXCEEDED` +
  `PREFIX_NONDETERMINISTIC`.

## Open questions

1. **Token count source.** Use `messages.count_tokens(model=...)` for
   measured budgets, or stick to local cl100k via Spec 082?
   **Recommend**: both — local for lint speed (sub-ms), API call when
   `[anthropic]` extra installed and verifying `prefix_stability`
   (per `claude-api` skill: "do not use tiktoken; it undercounts
   Claude tokens by ~15–20%").
2. **MAX_PREFIX_TOKENS default.** Hard-cap or soft-warn? **Recommend**:
   soft-warn at 6000, hard-fail at 8000 — leaves headroom above the
   tiered-discovery payload (Spec 068 measured) without eating the
   wrapping driver's context budget.
3. **Capability-set-hash granularity.** Hash by verb names only, or
   by verb names + signatures? **Recommend**: names + signatures — a
   signature change is a wire-shape change (Spec 019) and should
   invalidate the cache.

## Followup — Implementation Status (2026-06-11)

### Done — Slice 1 (envelope split + agency_welcome wiring)

- **`agency/_envelope.py` ships the typed `ResponseEnvelope`** —
  `prefix: dict` + `body: dict` with `__post_init__` rejecting non-dict
  halves (Spec 002 boundary typing). `to_dict()` raises
  `ValueError("...overlap...")` when prefix/body share a key.
  `prefix_hash()` returns SHA-256 hex of canonical-JSON prefix.
- **`canonical_json(env)`** — prefix keys (sorted) BEFORE body keys
  (sorted), compact JSON separators (no insignificant whitespace).
  Two envelopes with the same content yield byte-identical output
  regardless of dict-insertion order — the prefix-match invariant.
- **`capability_set_hash(names, signatures=None)`** — order-invariant
  on `names` (set semantics); when `signatures` is given, names +
  signatures hash per Open-Q 3 (a signature change rolls the hash).
- **`ontology_hash(nodes)`** — order-invariant on top-level + lists.
- **`agency_welcome` rewired through the envelope** — `prefix` carries
  `{schema_version, capability_set_hash, ontology_hash, wire_contract,
  code_mode_example, bootstrap_example, install_example, capabilities,
  capability_tier, discipline_skills}`; `body` carries `{state,
  intents_count, last_intent, db_path, next}`. The merged return adds
  `_prefix_keys` declaring the split for wrapping drivers.
- **15 tests green** (`tests/test_response_prefix_discipline.py`) —
  shape + canonical-JSON + hash determinism + body-isolation +
  capability_set_hash properties + ontology_hash determinism + two
  integration tests on the live `agency_welcome`.

### Done — Slice 2.1 (pure AST lint library, 2026-06-11)

- **`scripts/check_response_prefix.py`** — pure AST audit (Spec 067
  family) flagging `datetime.now()` (both `datetime.datetime.now()`
  and bare `datetime.now()` forms), `time.time()`, `uuid.uuid4()` (and
  bare `uuid4()` after `from uuid import uuid4`), `os.environ[...]`
  subscripts, `os.environ.get(...)`, and `os.getenv(...)`.
- **Typed shapes**: `ViolationKind` enum (DATETIME_NOW / TIME_TIME /
  UUID4 / OS_ENVIRON); `PrefixViolation(loc, kind, snippet)`;
  `PrefixReport(violations, total_files)`. Sorted by `(path, line)`
  for deterministic output.
- **`classify_call(ast_node)`** + `audit_source(src, path)` +
  `audit_tree(root)` — all pure; handle malformed Python safely
  (parse error → empty violation list).
- **Live audit**: `agency/_envelope.py` reports **0 violations**
  (Slice 1 hand-authored clean). `agency/engine.py` reports 3
  `OS_ENVIRON` sites — all in body-side state-aware welcome logic
  per the Slice 1 envelope split, not in prefix builders.
- **CLI**: `python -m scripts.check_response_prefix [--root <path>]`
  prints violation count + per-site `path:line  kind` (head:30).
  Slice 2.1 is informational (returns 0); Slice 2.2 promotes to
  CI-blocking gate per Spec 056/058 WARN→error doctrine.
- **16 tests** in `tests/test_response_prefix_lint.py` cover each
  violation kind, both call-form variants (qualified + from-import),
  clean source negative, file-loc capture, syntax-error tolerance,
  tree audit + determinism + `__pycache__` skip, and the live-tree
  envelope/engine smoke tests.

### Done — Slice 2.2 (WARN→error gate + baseline, 2026-06-12)

- **`BaselineEntry(path, line, kind)`** frozen dataclass + `load_baseline(path)`
  parses `<path>:<line>:<kind>` lines (blank/`#`-comment lines tolerated;
  malformed lines raise `ValueError` — fail loud).
- **`compare_to_baseline(report, baseline)` → `RegressionReport{new_violations,
  fixed_violations, ok}`** — pure set-difference: live − baseline is
  REGRESSIONS (gate-fail); baseline − live is FIXED (author trims).
- **CLI flags** `--baseline PATH --strict`:
  - `--strict` without baseline: any violation → exit 1.
  - `--strict --baseline`: only `new_violations` → exit 1; `fixed_violations`
    are surfaced so the baseline can be trimmed in the same PR.
- **`Plan/_planning/prefix-lint-baseline.txt`** — enumerates the 45 live
  `agency/` sites (set: 20 OS_ENVIRON + 12 unsorted_dict + 10 time_time +
  2 datetime_now + 1 uuid4). Generated from `audit_tree('agency')`; the
  gate flags any REGRESSION beyond this set.
- **CI step `Response-prefix lint`** in `.github/workflows/test.yml` runs
  the gate on every push + PR (`--root agency --baseline … --strict`).
- **10 new tests** in `tests/test_response_prefix_lint.py` cover:
  baseline parse + comment/blank handling + malformed-line ValueError +
  no-regression OK + new-site regression + fixed-site surfaced + CLI
  strict-without-baseline / strict-with-baseline-OK / strict-with-baseline-fail
  + a **live invariant** asserting the committed baseline equals the live
  `agency/` audit (drift gate on the baseline itself — a fix must trim;
  a regression must justify or fix).

### Done — Slice 2.2 gate re-promotion (2026-06-20)

The Slice 2.2 baseline was created 2026-06-12 but the Spec 286 module
refactor (2026-06-14) moved call sites between files, staling the
baseline and causing a false regression. The gate was demoted to
advisory at that point (`continue-on-error: true` in CI).

This followup:
- Refreshed `Plan/_planning/prefix-lint-baseline.txt` from the live tree
  (60 violations: 26 OS_ENVIRON + 20 unsorted_dict + 11 time_time +
  2 datetime_now + 1 uuid4 across 60 sites in 35 files).
- Removed `continue-on-error: true` from the CI step — the gate is
  **gating** again, not advisory.
- Zero regressions on a fresh `--strict --baseline` run (exit 0).

### Still — Slice 2.3+

- **Slice 2.3**: reachability analysis — restrict the scan to functions
  REACHABLE from substrate-tool prefix builders (Spec 067 family
  call-graph walk). Today's audit is conservative (every file
  contributes); Slice 2.3 narrows to the actual prefix-building
  call chains.
- **Slice 2.4**: `unsorted-dict` detector — flag dict literals in
  prefix builders that aren't sorted-keys serialized.
- **Slice 3**: `agency_doctor.prefix_stability` reporting
  `{stable, drift_bytes, drift_tokens, prefix_size_tokens}` across two
  60s-separated `agency_welcome` calls. Token count via Spec 082
  locally, Spec 201 API count with `[anthropic]` extra. Mocked Claude
  API cache-hit invariant test asserting
  `usage.cache_read_input_tokens > 0` on call 2.
- **Slice 4**: `MAX_PREFIX_TOKENS` hard-fail returning
  `Codes.PREFIX_BUDGET_EXCEEDED` (Spec 151 dep); never silent
  truncation.
- **Substrate parity**: Apply the same envelope split to the other
  substrate tools (`agency_doctor`, `agency_install`, `intent_bootstrap`)
  + the three wire-contract tools (`search`, `get_schema`, `execute`).
- **Spec 147 integration**: the AnthropicDriver `complete()` path adds
  `cache_control: {type:"ephemeral"}` on the rendered prefix when
  wrapping a substrate-tool response.
