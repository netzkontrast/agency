---
spec_id: "160"
slug: cli-yaml-chain-and-fields-closure
status: done
state: done
last_updated: 2026-06-10
owner: "@agency"
enhances: "018"
depends_on: ["018", "079", "023", "146"]
vision_goals: [1, 5]
affects:
  - agency/cli.py
  - tests/test_cli_chain_fields.py
---

# Spec 160 — CLI `--chain` + `--fields` closure

## Why

Spec 018 (cli-token-efficiency-bundle) is Partial — Wins 1/3/7 shipped,
but its Followup names the remainder: "Win 5 YAML `--chain`, Win 6
`--fields`". For a bash-only agent (Jules, the harness-in-harness
ladder, Goal 8), `--chain` lets one `agency` invocation run a YAML
dataflow of verbs (the bash analog of code-mode's `execute` chaining),
and `--fields` projects only the requested keys out of a verb's result
(the bash analog of the output budget). Both close the token-economy
gap on the CLI surface that code-mode already has on MCP.

## Done When

- [x] **`agency <cap> <verb> --fields a,b,c`** projects only those keys
      from the result dict — `_apply_fields` + the `--fields` option on
      every verb (`cli.py`). The typed kept/dropped record is
      `field_projection() -> GateProjection`.
- [x] **`agency --chain plan.yaml`** runs a YAML list of
      `{cap, verb, args, save_as, fields}` steps, threading `save_as`
      outputs into later steps' args via `${save_as.field}`
      interpolation — `_run_chain` + the typed `ChainStep`. One engine
      session.
- [x] **Output honors the Spec 146 prefix split** — `--fields` projects
      the body dict only; the projection is a key-subset (never invents a
      key). `test_projection_kept_set_matches_apply_fields`.
- [x] **Measurable invariants** (rule 8):
      (a) projection reduces keys — `GateProjection.dropped` is the
      trimmed set; (b) subset invariant `kept ⊆ result.keys()`;
      (c) `--chain` runs one engine session
      (`test_chain_execution_single_session_and_substitution`);
      (d) unknown `save_as` refs fail with `Codes.CHAIN_UNKNOWN_REF`
      before the step's effect (`test_chain_unknown_ref`).
- [x] Test: `--fields` projects; `--chain` threads + returns the final
      delta; typed projection kept/dropped. `tests/test_cli_chain_fields.py`
      (8 tests).
- [x] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  plan.yaml = [
          {cap: research, verb: fetch, args: {url: "..."},
           save_as: doc, fields: [body]},
          {cap: analyze, verb: summarize, args: {text: "${doc.body}"},
           save_as: summary, fields: [summary]},
          {cap: dogfood, verb: note, args: {text: "${summary.summary}"}}
        ]
When:   agency --chain plan.yaml
Then:   one engine session opens; three Invocations recorded;
        stdout carries ONLY the final step's body delta;
        prefix bytes match a single-call agency_welcome prefix
        (cache-stable across the chain)

Given:  agency analyze axis --fields summary,score (result has 8 keys)
When:   the CLI projects
Then:   stdout body contains only {summary, score};
        prefix unchanged; tokens(body) < tokens(unprojected body) by ≥ 40%
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| `save_as` ref typo | step 2 references `${doc.boddy}` | invariant (d) — chain-parse rejects pre-run | typed Codes.CHAIN_UNKNOWN_REF at parse, never at step N |
| `--fields` strips prefix | naive projection over the whole envelope | invariant (b) — prefix byte gate | project on `body` only; prefix is immutable post-envelope |
| Chain explodes context | unbounded `save_as` accumulation | per-step Spec 146 prefix budget; bounded by output overflow (Spec 154) | overflow capture applies per step; recall via handle in next step's args |
| YAML injection via `args` | malicious YAML payload | parse via safe loader; reject anchors/tags outside whitelist | typed Codes.CHAIN_UNSAFE_YAML; document the loader posture |

## Interconnects

- **Output-budget chain** (146): `--fields` is the CLI's budget knob.
- Spec 079 (CLI verb mirror) is the surface this extends.
- Spec 018 is the parent bundle.
- Spec 152 (typed Skill/Phase parse) — `ChainStep` reuses the typed
  parse boundary; one validation discipline across both surfaces.
- Spec 154 (output-overflow) — chain steps respect overflow capture;
  `${step.recall_handle}` is a first-class ref in `args`.
- Spec 151 (Codes coverage) supplies `Codes.CHAIN_UNKNOWN_REF` and
  `Codes.CHAIN_UNSAFE_YAML`.
- Spec 157 (architecture-drift gate) keeps the wire-verb count at 3
  even as `--chain` multiplies invocations — CLI sugar, not new verbs.

## Open questions

1. YAML `--chain` or JSON? **Recommend**: YAML (matches the `ant` CLI
   relaxed-YAML input + the existing `shell.templates` format).
2. `save_as` scope — chain-local only, or persisted as Artefacts?
   **Recommend**: persisted as Artefacts SERVING the chain's intent
   (rule 2 — graph is the store); chain-local cache is the
   render-on-demand view.

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion` as part of
the wave-1 typed-shape batch-2 (intent:2219e694; engine-driven tdd walk).

### Done — Slice 1 (typed shape)

Typed frozen dataclass + `__post_init__` invariants in
`agency/_typed_shapes_wave1_part2.py`; tests in
`tests/test_typed_shapes_wave1_part2.py` (17 tests total across the
8-spec batch). Slice 2 wires each shape into its consuming runtime
(red-team rerunner, CLI projection, derive audit, wrapper modules,
networkx metric, axis registry, migration walker, ref audit).

### Done — Slice 2 (2026-06-26)

The CLI `--chain` + `--fields` surface was already wired in `cli.py`
(`_run_chain` parsing YAML into the typed `ChainStep`, `${save_as.field}`
interpolation, per-step `_apply_fields`, `Codes.CHAIN_UNKNOWN_REF`). Slice 2
consumes the last dormant shape:

- `agency/cli.py::field_projection(result, fields_csv) -> GateProjection` — the
  TYPED kept/dropped projection record `--fields` applies, the single source for
  what `_apply_fields` keeps (operator visibility into what was trimmed).
- `GateProjection` imported + consumed (was dormant).
- 3 new tests in `tests/test_cli_chain_fields.py` (8 total, all green): typed
  kept/dropped, kept-set == `_apply_fields` output (subset invariant), identity
  when no `--fields`.

**Verdict:** Slice 2 SHIPPED — `--chain`/`--fields` closure complete, the typed
`ChainStep` + `GateProjection` both consumed; check-drift clean.

