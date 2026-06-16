---
spec: 300
title: token-symbols-capability
status: Partial (Slice 1 shipped)
depends_on: [295, 299]
clusters: [thinking]
vision_goals: [1, 4]
---

# Spec 300 — `symbols`: token-efficient symbol compression, first-class

> Sixth extract→spec→reimplement slice. Completes the Token-Efficiency story:
> `mode.token_efficiency` is the posture; `symbols` is the mechanism.

SuperClaude's `MODE_Token_Efficiency` + `BUSINESS_SYMBOLS` define a phrase↔symbol
legend for compressed communication. Reimplemented natively as decidable
transforms.

## Design

- `symbols.legend()` — the phrase↔symbol legend (logic/flow · status · domain).
- `symbols.compress(text)` — substitute known phrases with symbols; report token
  reduction.
- `symbols.expand(text)` — the inverse (symbol → canonical phrase).

Pure `role="transform"` verbs (no provenance write) — compose anywhere.

## Done-When

- [x] Legend extracted; `compress`/`expand` decidable + measured; scenarios green.
- [ ] **Follow-up:** wire `compress` into the engine output path under
  `mode.token_efficiency` when a token budget is tight.

## Followup — Implementation Status (2026-06-16)

**Done.** `agency/capabilities/symbols/` — `legend`/`compress`/`expand`.
