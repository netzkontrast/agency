---
spec_id: "276"
slug: doctor-welcome-managed-aware
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "030"
depends_on: ["030", "170", "262", "263"]
vision_goals: [5, 3]
affects:
  - agency/_doctor.py
  - tests/test_doctor_managed_aware.py
---

# Spec 276 — agency_doctor + welcome: managed-agents-aware

## Why

Spec 030 ships `agency_doctor` + stateful welcome + JULES_API_KEY
clarity. As the AnthropicDriver (Spec 147) + managed-agents-onboarding
cap (Spec 262) + Fable 5 extras (Spec 263) land, welcome should
discover them. A user opening a session sees in ONE place: install
method (Spec 065), Jules key (Spec 030), Anthropic key (147), Fable
retention status (263), readiness to dispatch to MA — with one-line
fixes per gap.

## Done When

- [ ] **Welcome shows the full driver matrix** — jules-key /
      anthropic-key / fable-retention / MA-ready, each with a one-line
      remediation if not ready (Spec 170 hint pattern).
- [ ] **`/agency-doctor` slash** (Spec 148 family) renders it.
- [ ] **Onboarding (Spec 262) chains it** when the user accepts capture.
- [ ] **The Spec 030 statefulness preserved** — once seen, doesn't repeat.
- [ ] Test: welcome reports the full matrix + remediations; stateful
      repeat suppressed.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 170 (doctor deepening) is the report engine.
- Spec 262 (onboarding cap) + Spec 263 (Fable extras) chain in.
- **UX-onboarding chain** + **agent-uniform** (Goal 3) extension.
