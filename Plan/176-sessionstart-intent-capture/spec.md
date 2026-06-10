---
spec_id: "176"
slug: sessionstart-intent-capture
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "062"
depends_on: ["062", "148", "076", "147"]
vision_goals: [2, 5, 3]
affects:
  - hooks/session-start.sh
  - agency/capabilities/develop/_main.py
  - tests/test_sessionstart_intent_capture.py
---

# Spec 176 — SessionStart Intent capture

## Why

Spec 062 ships a SessionStart hook that auto-installs the engine. The
UX chain (Spec 148) wants first-touch to CAPTURE INTENT — every session
should serve an Intent (CLAUDE.md session-start protocol: `agency_welcome`
→ `intent_bootstrap` → walk a discipline skill). Today that's manual.
The hook should offer it, and when accepted, the capture turns become
graph Artefacts (Goal 2 provenance) via the Spec 076 unified hook layer.

## Done When

- [ ] **SessionStart hook (Spec 062) gains an Intent-capture offer** —
      non-blocking; when no open Intent exists in the repo's
      `.agency/session.db`, it prints the `/agency-onboard` invite.
- [ ] **Accepted capture writes the Intent + N onboarding Artefacts**
      (Spec 148 interview) with PRODUCES edges (Spec 076 dispatch).
- [ ] **`AGENCY_INTENT` env (Spec 018) auto-set** to the captured
      intent so every subsequent verb SERVES it implicitly.
- [ ] **Idempotent** (Spec 062) — re-running a session with an open
      Intent does not re-prompt.
- [ ] Test: a fresh repo session offers capture; capture sets
      `AGENCY_INTENT` + records the Intent.
- [ ] TODO row + drift clean.

## Interconnects

- **UX-onboarding chain** (148) · provenance (Goal 2).
- Spec 076 (unified hooks) is the dispatch substrate.
- Spec 147 (Driver) powers the conversational capture when present.

## Open questions

1. Block the session on capture? **Recommend**: never block — offer +
   one-keystroke accept; a session can proceed Intent-less (degrades to
   a default `ad-hoc` Intent that later captures supersede).
