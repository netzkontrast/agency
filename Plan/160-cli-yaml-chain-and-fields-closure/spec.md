---
spec_id: "160"
slug: cli-yaml-chain-and-fields-closure
status: draft
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

- [ ] **`agency <cap> <verb> --fields a,b,c`** projects only those keys
      from the result dict (the bash `--transform` analog; mirrors the
      `ant` CLI's `--transform`, `claude-api` skill). Returns the
      projected subset preserving the Spec 146 prefix split — the
      `body` filters, the `prefix` is untouched.
- [ ] **`agency --chain plan.yaml`** runs a YAML list of
      `{cap, verb, args, save_as}` steps, threading `save_as` outputs
      into later steps' args — one engine session, deltas only (the
      code-mode `execute` parity for bash agents). Typed step:
      `ChainStep{cap: str, verb: str, args: dict, save_as: str | None,
      fields: list[str] | None}`.
- [ ] **Output honors the Spec 146 prefix split** — `--fields` never
      strips the cache-stable prefix.
- [ ] **Measurable invariants** (rule 8):
      (a) `tokens(--fields a,b) < tokens(no --fields)` for any verb
      whose result has > 2 keys (projection actually reduces bytes);
      (b) `prefix_bytes(--fields output) == prefix_bytes(no --fields
      output)` — projection NEVER touches the cacheable prefix;
      (c) `--chain N-step` issues ONE engine session (not N) — measured
      by Invocation count: `len(invocations_from_chain) == N` AND
      `engine_sessions_opened == 1`;
      (d) `save_as` outputs are typed and validated at chain-parse
      (Spec 152) — unknown refs fail before any step runs.
- [ ] Test: `--fields` projects; `--chain` threads a 3-step plan and
      returns only the final delta; prefix byte-stable across both.
- [ ] TODO row + drift clean.

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
