---
spec_id: "260"
slug: slash-family-natural-language
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "148"
depends_on: ["148", "176", "147", "188"]
vision_goals: [5, 3]
affects:
  - commands/agency.md
  - tests/test_slash_natural_language.py
---

# Spec 260 — slash family: natural-language routing

## Why

Spec 148 anchors the UX-onboarding chain. `/agency [query]` routes to
search today. With Spec 147 + Spec 188 LLM drill, `/agency <free
text>` can route to the right verb OR skill directly — the natural
extension of `/agency-onboard`'s conversational pattern. Discovery →
disambiguate → execute, all from a single slash.

## Done When

- [ ] **`/agency <free text>`** dispatches via the Spec 188 LLM-drill
      to the most relevant verb/skill (one structured-output call).
- [ ] **Confirmation gate** before mutating verbs run (the safety
      gate from Spec 192).
- [ ] **Onboarding (Spec 148/176) for unmatched queries** — offers
      capture instead of failing.
- [ ] **Output budget** (Spec 146) on the dispatch payload.
- [ ] Test: free-text query routes correctly (mocked); mutating verb
      gates for confirmation.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 148 (parent); Spec 176 (sessionstart capture); Spec 188 (LLM drill).
- **UX-onboarding chain** completion.
