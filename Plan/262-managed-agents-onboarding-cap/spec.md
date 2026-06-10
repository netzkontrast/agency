---
spec_id: "262"
slug: managed-agents-onboarding-cap
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "029"
depends_on: ["029", "148", "176", "147"]
vision_goals: [5, 8]
affects:
  - agency/capabilities/intent.py
  - commands/agency-onboard.md
  - tests/test_managed_agents_onboard.py
---

# Spec 262 — managed-agents-onboarding capability

## Why

Spec 029 ships `intent_bootstrap`. The `claude-api` managed-agents-
onboarding pattern (describe → configure → environment → session) is
EXACTLY the right interview shape for capturing an Intent. This wraps
the pattern as a first-class capability so a user / external agent can
run it once, get an Intent + Resources + Vault + Session ready, and the
walk's turn-by-turn is captured as graph Artefacts (Spec 176 already
drafted).

## Done When

- [ ] **`intent.managed_onboard(...)`** runs the 4-beat interview;
      each beat = one Artefact with PRODUCES edges.
- [ ] **Produces a structured Intent** + (when consent given) a
      Managed-Agents Agent config the user can start sessions against.
- [ ] **Reuses Spec 147 Driver** for the interview itself.
- [ ] **`/agency-onboard` (Spec 148) routes here.**
- [ ] Test: 4-beat interview captures 4 Artefacts + 1 Intent (mocked).
- [ ] TODO row + drift clean.

## Interconnects

- Spec 148 (slash family) · Spec 176 (sessionstart capture).
- **UX-onboarding chain** + **harness-in-harness** (Goal 8).
