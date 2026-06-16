---
spec: 294
title: business-panel-capability
status: Partial (Slice 1 shipped)
depends_on: [026, 091, 110]
clusters: [thinking, analyze]
vision_goals: [4]
---

# Spec 294 — `panel`: multi-expert business analysis, first-class

> User directive (2026-06-16): stop "porting" SuperClaude — extract each part,
> write a spec, and **reimplement it as a first-class agency citizen**.

First reimplementation: SuperClaude's **Business Panel** (`MODE_Business_Panel`,
`sc-business-panel-experts`). Extracted, understood, and rebuilt as a native
agency capability — not an ingested prompt file.

## Extracted understanding (from the SuperClaude source)

- **9 expert personas**, each a named strategic framework: Christensen
  (Disruption / Jobs-to-be-Done), Porter (Five Forces / Value Chain), Drucker
  (Management by Objectives), Godin (Permission Marketing / Purple Cow / Tribes),
  Kim & Mauborgne (Blue Ocean / ERRC), Collins (Good-to-Great / Flywheel),
  Taleb (Antifragility / Black Swan), Meadows (Systems Thinking / leverage
  points), Doumont (structured communication).
- **3 interaction modes**: `discussion` (collaborative, complementary lenses —
  default), `debate` (adversarial stress-test), `socratic` (question-driven).
- **Decidable mode selection** by content triggers (debate: controversial /
  risk / decision / trade-off / challenge; socratic: learn / understand / how /
  why; else discussion).

## Design — native, decidable, scaffold-producing

`panel` follows agency's `thinking`/`intent` pattern: a **decidable** capability
that produces a structured multi-expert **critique scaffold** (the orchestrator
/ an LLM fills the analysis; the framework + questions are the first-class
artefact). No LLM backend required.

- `panel.experts()` — the 9-expert roster (name · framework · lens · signature
  question · trigger terms).
- `panel.convene(subject, mode="auto", focus="balanced")` — selects the
  relevant experts (by subject↔trigger overlap; `focus="full"` = all 9), selects
  the mode (decidable triggers when `auto`), and emits a per-mode scaffold:
  discussion lenses, debate tensions, or socratic questions. Records a `Panel`
  node (subject, mode) SERVING the intent — the analysis is provenance.

## Done-When

- [x] 9-expert roster with frameworks + signature questions.
- [x] `convene` selects experts + mode (auto via decidable triggers) and emits a
  mode-appropriate scaffold; records a `Panel` node.
- [x] `Panel` ontology node + `(Panel, mode)` enum; auto-registers (drop-in).
- [x] Acceptance scenarios (roster, auto mode selection per trigger, scaffold
  shape per mode).
- [ ] **Follow-up:** wire `convene`'s scaffold through the AnthropicDriver for
  live expert voices when a backend is present (decidable scaffold stays the
  fallback). Then reimplement the next SuperClaude part (own spec).

## Followup — Implementation Status (2026-06-16)

**Done.** `agency/capabilities/panel/` — `experts` + `convene`; 9-expert registry;
decidable mode selection; `Panel` node. First first-class SuperClaude
reimplementation (replaces the removed "port" scaffolding).

**Still.** LLM-backed expert voices (follow-up); subsequent SuperClaude parts
each get their own extract→spec→reimplement slice.
