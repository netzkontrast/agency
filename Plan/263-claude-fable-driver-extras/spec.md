---
spec_id: "263"
slug: claude-fable-driver-extras
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "147"
depends_on: ["147", "256", "201", "170"]
vision_goals: [3]
affects:
  - agency/_drivers/_anthropic.py
  - tests/test_fable_driver.py
---

# Spec 263 — Claude Fable 5 driver extras

## Why

Per `claude-api` skill, Claude Fable 5 (`claude-fable-5`) is Anthropic's
most capable widely-released model. Key requirements: protected
thinking is ALWAYS ON (omit `thinking` entirely; `{type:"disabled"}` →
400), no `temperature`/`top_p`/`top_k`, 30-day data retention required,
~30% more tokens than Opus tokenizer, `task_budget` available (beta
`task-budgets-2026-03-13`), assistant prefill rejected. The driver
needs explicit Fable 5 support so a verb opting into the most capable
model gets the right surface.

## Done When

- [ ] **Model selector includes `claude-fable-5`** + `claude-mythos-5`
      (Project Glasswing).
- [ ] **Fable-specific request shape** — omit `thinking`, no sampling
      params, retention check before send.
- [ ] **Task Budgets** (beta `task-budgets-2026-03-13`) — for agentic
      loops on Fable.
- [ ] **`agency_doctor`** (Spec 170) reports Fable-readiness +
      retention status.
- [ ] **Refusal fallback to Opus 4.8** by default (Spec 256 path).
- [ ] Test: Fable request shape correct (mocked); ZDR org refused
      cleanly.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 147 (parent) · Spec 256 (refusal/fallbacks) · Spec 201 (tokens).
- Spec 170 (doctor) reports state.
