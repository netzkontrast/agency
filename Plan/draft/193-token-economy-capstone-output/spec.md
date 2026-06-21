---
spec_id: "193"
slug: token-economy-capstone-output
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "074"
depends_on: ["074", "186", "187", "146"]
vision_goals: [1]
affects:
  - tests/test_token_economy_capstone.py
  - docs/vision/GOALS.md
---

# Spec 193 — token-economy capstone, output-side proof

## Why

Spec 074 is the token-economy cluster capstone — it proved the
input/discovery economy goal met. The enhancement charter adds the
output side (Specs 146/154/160/186/187). The capstone should be
re-run with the output-side invariants included, producing the
end-to-end proof: a wrapping LLM driver sees a cache-stable prefix, a
budgeted body, and a recall handle for overflow — the full token-economy
story Goal 1 promises.

## Done When

- [ ] **End-to-end capstone test** — a simulated LLM-driver session
      over the engine measures a typed `CapstoneReport{cache_read:
      int, cache_creation:int, overflow_count:int, recall_handles:
      list[str], projected_fields:list[str], invariants_passed:
      list[str]}`. The simulator wraps `mcp__agency__{search,
      get_schema, execute}` with `cache_control` on the prefix and
      replays a representative agent loop.
- [ ] **The proof is relationships** (rule 8): asserted invariants
      include `cache_read > 0 on the second call`, `every overflow
      has a recall_handle`, `--fields projection reduces body tokens
      by at least 50%`, `prefix bytes byte-identical across calls
      with unchanged capability set`. No pinned token counts.
- [ ] **Wave-spanning coverage**: the capstone exercises at least
      one verb from each output-economy chain (146 prefix, 154
      overflow, 160 fields) AND at least one Driver call (147) to
      prove the wrapping LLM sees the cache.
- [ ] **GOALS.md Goal-1 row updated** to cite the output-side proof,
      sourced from Spec 191's derived matrix — the citation is a
      derived field, not a hand-pinned sentence.
- [ ] **CI + tagged-live variants**: the simulated capstone runs on
      every PR; the live-API variant runs on `v*` tags only.
- [ ] **Failure-mode coverage** for cache mock divergence, simulator
      drift from real API behavior, and partial-shipment regressions.
- [ ] Test: the capstone session asserts all invariants; a regression
      fixture (re-introduce a `datetime.now()` in a prefix) trips it.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  Specs 146, 154, 160 all shipped with lints at error level
        AND a mocked Anthropic client that records cache_control headers
            and returns usage{cache_creation_input_tokens, cache_read_input_tokens}
When:   capstone_test runs the simulated session: call agency_welcome();
        sleep 0.1s; call agency_welcome() again with same cache_control
Then:   CapstoneReport.cache_read > 0 on the second call AND
        cache_creation > 0 on the first AND
        prefix bytes byte-identical between calls AND
        no overflow recorded AND
        invariants_passed includes "prefix_stable", "cache_hit",
        "no_silent_truncation"

Given:  the capstone runs against a synthetic verb whose result exceeds
        MAX_BODY_BYTES
When:   the verb returns via the engine
Then:   overflow_count == 1, recall_handles is non-empty, the truncated
        body carries the handle, invariants_passed includes
        "overflow_captured"; NO assertion of a pinned byte count

Given:  a regression: someone reintroduces datetime.now() in a prefix builder
When:   the capstone runs on PR CI
Then:   prefix bytes differ between the two welcome calls;
        invariants_passed lacks "prefix_stable"; capstone fails with
        the offending site cited via the Spec 187 lint output
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Mock divergence | mocked client computes cache differently than real Anthropic | tagged-live variant on `v*` re-validates with real API | run live variant pre-release; treat divergence as a release blocker |
| Simulator overfit | capstone always passes because the agent loop is too narrow | coverage check: at least one verb per output chain | rotate the agent loop fixture per release cycle |
| Partial regression | 146 passes, 154 silently regresses | per-invariant assertions, not a single aggregate boolean | one assertion per invariant; failure cites the chain |
| API quota drain | live variant blows the budget | live variant gated on tag + budget env | hard-cap requests per live run; abort on overage |
| Stale Goal-1 citation | GOALS.md row hand-edited after capstone changed | Spec 191 derive-docs regenerates the row from spec frontmatter | derive, never hand-pin |

## Interconnects

- **Output-budget chain** (146/154/160): this is its end-to-end proof.
- Spec 186 (cluster charter) + Spec 187 (lints) are the companions.
- Spec 147 (AnthropicDriver) is the LLM wrapper the capstone simulates.
- Spec 188 (tiered-discovery drill) is exercised in the agent loop.
- Spec 191 (live matrix) consumes the capstone's verdict for the
  Goal-1 row.
- Spec 195 (event replay) records the capstone session for re-running
  the proof against any future engine.

## Open questions

1. Live API in the capstone, or simulated? **Recommend**: simulated
   (deterministic, no API cost) for CI; a tagged live variant
   validates real cache behavior on `v*` tags. Both required —
   one for speed, one for ground truth.
2. Which agent loop is the canonical fixture? **Recommend**: a
   minimal three-step loop (welcome → search → execute) that touches
   every output chain. Keep the loop versioned so a change is
   reviewable.
3. What's the budget for the live variant? **Recommend**: a hard
   cap of $0.10 per release; the test aborts if `usage` projects
   higher. Document the cap in the test header.
