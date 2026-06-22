---
spec_id: "187"
slug: lint-token-rules-output-side
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "067"
depends_on: ["067", "146", "154", "186"]
vision_goals: [1]
affects:
  - agency/_lints/
  - tests/test_output_token_lints.py
---

# Spec 187 — output-side token-economy lint rules

## Why

Spec 067 ships the executable token-economy goal-test — but only over
NAMES (`name_token_budget`, `bare_name_*`, `prefix-dominance`). The
output side (the bytes returned to an LLM driver) has no lint. This
spec adds the output-side rules so the same lint pipeline that guards
name economy guards response economy.

## Done When

- [ ] **`response_prefix_stable` lint** (the Spec 146 discipline, in
      the 067 pipeline) — fails when a substrate-tool prefix
      interpolates non-deterministic content (`datetime.now`, `time.time`,
      `uuid4`, unsorted dicts, request-time `os.environ` reads). Returns
      a typed `LintFinding{rule:str, file:str, line:int, kind:Literal[
      "nondeterministic_call","unsorted_dict","env_read"]}` per hit.
- [ ] **`overflow_capture_present` lint** — a verb whose result can
      exceed the budget must route through Spec 154 capture (not
      silent truncation). Detection: AST search for return paths that
      slice/truncate a payload without emitting a `recall_handle`.
- [ ] **`fields_projectable` lint** — a CLI-exposed verb's result is a
      flat-enough dict that `--fields` (Spec 160) can project it.
      Invariant: `max_nesting_depth(return_shape) <= FIELDS_MAX_DEPTH`
      (default 3, documented tunable).
- [ ] **All three are relationship/invariant rules** (rule 8), not
      pinned byte caps. The only literal numbers permitted are named,
      overridable budgets (`MAX_PREFIX_TOKENS`, `FIELDS_MAX_DEPTH`,
      `OVERFLOW_BODY_BYTES`) with a documented rationale.
- [ ] **Each lint follows the WARN-then-promote cycle** (056/058/171/173):
      WARN until the live registry reports zero violations, then promote
      to error. Promotion is automatic when `agency_doctor.lints[rule].
      violations == 0` for one full cycle.
- [ ] **Failure-mode coverage**: each lint has a fixture demonstrating
      its trigger, its detection signal, and the mitigation path.
- [ ] Test: each lint trips its fixture; the live registry passes.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a substrate verb whose prefix builder calls `datetime.now().isoformat()`
When:   `_check_response_prefix` runs in the 067 pipeline
Then:   a LintFinding{rule:"response_prefix_stable", file:..., line:...,
        kind:"nondeterministic_call"} is emitted; CI fails after the WARN
        cycle has elapsed

Given:  a verb returns a dict whose body can exceed MAX_BODY_BYTES but
        the return path slices to N items without emitting recall_handle
When:   `overflow_capture_present` runs
Then:   lint fails pointing at the truncation site; mitigation: route
        through Spec 154 `engine.capture_overflow(payload, intent_id)`

Given:  the live registry after all three lints promoted from WARN to error
When:   pytest -q runs
Then:   zero violations, `cache_read_input_tokens > 0` on a re-discovery
        call, no truncation lacking a recall handle anywhere
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Prefix interpolation | verb prefix calls `datetime.now()` / `uuid4()` | `response_prefix_stable` (AST) | move the call into `body`, not `prefix` |
| Silent truncation | verb slices payload without `recall_handle` | `overflow_capture_present` (AST) | route through Spec 154 capture |
| Unprojectable shape | verb returns deeply nested dict (depth > 3) | `fields_projectable` (return-shape inspection) | flatten or add explicit `--fields` translation |
| Premature promotion | lint flipped to error while live violations remain | promotion gate reads `doctor.lints[rule].violations` | block promotion until violations == 0 for one cycle |
| Magic-number creep | someone writes a literal byte cap inline | rule-8 magic-number lint | define a named, overridable budget instead |

## Interconnects

- **Output-budget chain** (146/154/160): these are its lints.
- Spec 067 is the pipeline; Spec 186 the cluster charter.
- Spec 193 (capstone) consumes all three lint signals in its end-to-end proof.
- Spec 184 (codemode alias) must pass `response_prefix_stable` after
  registering the alias.
- Spec 147 (AnthropicDriver) is the consumer whose cache behavior the
  lints protect.
- Spec 149 (derived docs) re-renders the lint inventory.

## Open questions

1. WARN or error first? **Recommend**: WARN one cycle then promote
   (the 056/058/171/173 pattern), per-rule. Automate the promotion
   gate so it doesn't drift.
2. Should `fields_projectable` accept depth-4 with an explicit
   `--fields` translator? **Recommend**: yes — the lint flags the
   shape; an authored projector clears it.
3. What about non-CLI verbs that still return deep shapes?
   **Recommend**: the `fields_projectable` lint is scoped to verbs
   reachable from `agency.cli`; substrate-internal verbs are exempt.
