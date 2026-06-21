# Architecture Decision Records — thematic, living (Spec 353/354)

agency uses **thematic, living ADRs**, not one-immutable-file-per-decision.
There is one ADR Document per architecture **layer**; each individual decision
is a WH(Y) `Decision` node `PART_OF` its theme, and the file below renders the
theme's currently-live decisions (`adr.render`). "Extended inline" = appending a
new `Decision`; a revised decision `SUPERSEDES` its predecessor (history retained,
keep-both — Spec 292). The theme is the ported **Master ADR** (aggregate status
over its children).

These records exist primarily to extract the **code + architecture hints**
(`adr.hints`) re-loaded into context at the start of implementation.

| Layer | File | Scope |
|---|---|---|
| Datalayer | [`adr-datalayer.md`](adr-datalayer.md) | how agency stores, versions and reconciles all state |
| Substrate | [`adr-substrate.md`](adr-substrate.md) | the FastMCP engine and the wire contract every capability rides |
| Capabilities | [`adr-capabilities.md`](adr-capabilities.md) | how capabilities are authored, discovered and bounded |
| Lifecycle | [`adr-lifecycle.md`](adr-lifecycle.md) | how stateful entities transition, with provenance |
| Workflow | [`adr-workflow.md`](adr-workflow.md) | the ADR-centred repo-development lifecycle (Spec 353 reconciliations) |

## Working with ADRs (the `adr` capability)

- `adr.theme(layer, title, scope)` — get-or-create a layer's theme Document.
- `adr.draft(theme_id, decision, context, facing, neglected, benefits, tradeoffs)` —
  record a WH(Y) `Decision` (status `proposed`) `PART_OF` the theme.
- `adr.validate(decision_id)` — the decidable WH(Y) rules (WHY-001/003/005, MIN-005).
- `adr.approve(decision_id, approver)` — the owner-gated approval (no agent self-approve).
- `adr.render(theme_id)` — project the theme's live decisions to its body.
- `adr.theme_status(theme_id)` / `adr.impact(decision_id)` — aggregate status / blast radius.

A new theme is an **owner decision** (one theme == one architecture layer) — this
is what keeps "only a handful of ADRs" true. The decisions below are recorded as
`proposed`; promotion to `approved`/`implemented` is the owner's 355-gated step.
