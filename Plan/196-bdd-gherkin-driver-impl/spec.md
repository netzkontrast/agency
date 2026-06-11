---
spec_id: "196"
slug: bdd-gherkin-driver-impl
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "077"
depends_on: ["077", "147", "169", "152", "146", "150", "199"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/develop/_bdd.py  (NEW)
  - tests/test_bdd_gherkin.py
---

# Spec 196 — BDD/Gherkin test-authoring driver

## Why

Spec 077 (bdd-gherkin-tests) is a research-first backlog draft. The
research question — "how does the engine author behaviour tests from a
spec's Done-When list?" — is now answerable: each Done-When bullet is a
behaviour, and the Spec 147 Driver can render it as a Gherkin scenario +
a pytest skeleton (`output_config.format`). This closes the loop between
a spec's acceptance criteria and its test suite, which the CI
coverage gate (Spec 169) then enforces.

## Done When

- [ ] **`develop.author_bdd(spec_id) -> BDDArtefact`** where
      `BDDArtefact = {spec_id, scenarios: list[Scenario], pytest_path,
      driver_used: bool}` and `Scenario = {given, when, then, source_bullet}` —
      reads a spec's Done-When list and emits one scenario per bullet via
      the Spec 147 Driver with `output_config.format`; degrades to a
      structured stub (one scenario per bullet, blank G/W/T) without
      `[anthropic]`.
- [ ] **Generated tests link to the spec** — every emitted pytest carries
      a `PRODUCES` edge FROM the spec's Intent node TO the test file
      Artefact; `analyze.graph_query` (Spec 203) can recover the chain.
- [ ] **Invariant — scenario-to-bullet parity** (relationship, not pinned
      count): `len(scenarios) == count_done_when_bullets(spec_id)` for
      every spec authored. Drift (a bullet without a scenario, or a
      scenario without a bullet) fails the check.
- [ ] **Invariant — CI coverage uplift** (relationship): per-capability
      scenario count must be `>=` Spec 169's floor AFTER `author_bdd`
      runs on every Partial-status spec touching that capability.
- [ ] **Invariant — generated tests execute** (relationship): every
      emitted skeleton is import-clean (`pytest --collect-only` exits 0)
      even when `xfail`-marked; a non-collectable skeleton fails.
- [ ] Test: a fixture spec with N Done-When bullets yields N scenarios
      (mocked Driver); each scenario carries its `source_bullet` index.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  Spec 196 has 5 Done-When bullets and ANTHROPIC_API_KEY is set
When:   develop.author_bdd("196") runs
Then:   returns BDDArtefact{scenarios: [5 items], driver_used: true}
        AND tests/test_spec_196_bdd.py is import-clean
        AND graph has 5 PRODUCES edges from Intent(spec=196) to Artefact

Given:  [anthropic] extra not installed
When:   develop.author_bdd("196") runs
Then:   returns BDDArtefact{driver_used: false} with blank G/W/T stubs
        AND scenario count still equals Done-When bullet count

Given:  a spec author edits a Done-When bullet
When:   author_bdd reruns
Then:   the matching Scenario regenerates; sibling scenarios stay
        byte-stable (cache-friendly per Spec 146 prefix discipline)
```

## Failure modes (Nygard)

| Failure | author_bdd response |
|---|---|
| Driver `REFUSAL` (Spec 147) | emit scaffold scenario; record reason on artefact; do not retry |
| Driver `RATE_LIMITED` | retry per Spec 147 budget; never exceed per-intent cap |
| `TIMEOUT` mid-generation | partial artefact written under tempfile; never overwrite a green skeleton |
| Spec has zero Done-When bullets | typed `BAD_REQUEST{detail:"empty_done_when"}` — never generate empty test files |
| `output_config.format` schema-violation | re-issue once with stricter schema; on second failure, emit stub + WARN |
| Driver returns scenario count != bullet count | hard fail invariant; never write to disk |

## Interconnects

- **LLM-driver chain** (147) · Spec 169 (coverage gate) consumes output.
- Spec 152 (typed Skill) — the authoring step is a walkable phase.
- Spec 146 (output-prefix) — emitted artefact JSON honours the prefix
  split so re-runs are cache-hit on unchanged bullets.
- Spec 150 (dogfood classifier) — author_bdd emits a Reflection on every
  run; classifier may propose amendments when bullet drift is detected.
- Spec 199 (Skills round-trip) — `develop.author_bdd` is itself a
  published skill; its description gates loading.
- Spec 200 (adaptive walk) — author_bdd is one phase of the `develop-usage`
  adaptive walk when the task hint mentions "test" or "BDD".
- Spec 203 (graph query) — the bullet→scenario→test PRODUCES chain is
  queryable via the moat query.
- Spec 205 (substrate hardening) — generated tests being import-clean
  is a standing check (eligible for G(n+1) in the hardening suite).

## Open questions

1. Author at spec-draft time or implement time? **Recommend**:
   implement time (the Done-When is stable by then); draft-time is noisy.
2. Re-author on every Done-When edit, or only on explicit request?
   **Recommend**: explicit request — auto-regen would churn the test
   suite; surface a "drift detected" WARN via Spec 149 instead.
3. Where do filled scenarios live when the Driver answer disagrees with
   a hand-edited pytest? **Recommend**: never overwrite hand-edits —
   `author_bdd` writes to `tests/_generated/`; integration is a manual
   merge so the bullet→test trace stays auditable.
