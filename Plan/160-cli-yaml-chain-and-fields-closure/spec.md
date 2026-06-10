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
      `ant` CLI's `--transform`, `claude-api` skill).
- [ ] **`agency --chain plan.yaml`** runs a YAML list of
      `{cap, verb, args, save_as}` steps, threading `save_as` outputs
      into later steps' args — one engine session, deltas only (the
      code-mode `execute` parity for bash agents).
- [ ] **Output honors the Spec 146 prefix split** — `--fields` never
      strips the cache-stable prefix.
- [ ] Test: `--fields` projects; `--chain` threads a 3-step plan and
      returns only the final delta.
- [ ] TODO row + drift clean.

## Interconnects

- **Output-budget chain** (146): `--fields` is the CLI's budget knob.
- Spec 079 (CLI verb mirror) is the surface this extends.
- Spec 018 is the parent bundle.

## Open questions

1. YAML `--chain` or JSON? **Recommend**: YAML (matches the `ant` CLI
   relaxed-YAML input + the existing `shell.templates` format).
