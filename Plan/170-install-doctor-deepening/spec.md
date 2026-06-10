---
spec_id: "170"
slug: install-doctor-deepening
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "055"
depends_on: ["055", "065", "147", "148"]
vision_goals: [5, 3]
affects:
  - agency/_doctor.py
  - tests/test_doctor_deepening.py
---

# Spec 170 — agency_doctor deepening

## Why

Spec 055 (pipx-only-install) + Spec 065 (pipx-direct-doctrine) settled
the install path and gave `agency_doctor` install_method reporting. But
as the enhancement waves add capabilities (AnthropicDriver, server-side
tools, Managed Agents), `doctor` needs to report their readiness so a
user/agent knows what's wired BEFORE invoking. A deep doctor is the
first-touch diagnostic the UX chain (Spec 148) leans on.

## Done When

- [ ] **`agency_doctor` reports the enhancement-era surface** (all
      derived, Spec 149): `anthropic_driver`, `managed_agents_capable`,
      `prefix_stability`, `codes_coverage`, `schema_coverage`,
      `analyze_extras`, `drift`.
- [ ] **Actionable hints** — each not-ready field carries a one-line
      fix pointer (the pipx-HINT pattern from Spec 065).
- [ ] **`/agency-doctor` slash command** (Spec 148 family) renders it.
- [ ] Test: doctor reports each field; a missing extra yields its hint.
- [ ] TODO row + drift clean.

## Interconnects

- **UX-onboarding chain** (148): doctor is the first-touch diagnostic.
- **LLM-driver chain** (147): reports driver readiness.
- **Drift-derivation chain** (149): every field derived.

## Open questions

1. One doctor or per-extra doctors? **Recommend**: one, sectioned —
   matches the single `agency_doctor` surface users already know.
