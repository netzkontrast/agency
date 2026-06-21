---
spec_id: "262"
slug: managed-agents-onboarding-cap
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "029"
depends_on: ["029", "148", "176", "147", "256", "257"]
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
EXACTLY the right interview shape for capturing an Intent: open with
the user's purpose, refine into a configurable agent shape, surface
the environment/tools the work will need, dispatch a session.
Wrapping this pattern as a first-class capability means a user or
external agent runs it once and walks away with a structured Intent +
Resources + (when consent given) a persisted Managed-Agent ready for
session dispatch — and every interview turn is captured as a graph
Artefact PRODUCES edge (Spec 176). The user feels creative; the AI
captures everything; Goal 8 (harness-in-harness) is realised at the
onboarding edge.

## Done When

- [ ] **`intent.managed_onboard(seed: str)`** runs the 4-beat
      interview; each beat = one Artefact with PRODUCES edges:
      ```python
      class OnboardOutcome(TypedDict):
          intent_id: str                    # the captured Intent
          beats: list[dict]                 # 4 beat Artefacts
          agent_config: dict | None         # when consent given
          agent_id: str | None              # when persisted via Lock
          environment: dict                 # resources/tools surfaced
          session_handle: SessionHandle | None  # when dispatched
      ```
- [ ] **Produces a structured Intent** + (when consent given) a
      Managed-Agents Agent config the user can start sessions against
      via Spec 137 Lock (persist `agent_id` + `version`; create-once
      doctrine from claude-api skill `managed-agents-core.md`).
- [ ] **Reuses Spec 147 Driver** for the interview itself — each beat
      is a structured-output call that takes the user's free text and
      returns the next beat's prompt + state delta.
- [ ] **`/agency-onboard` (Spec 148) routes here**; Spec 260 routes
      ambiguous slash queries here.
- [ ] **Measurable invariants** (relationships, not pinned counts):
      - `len(beats) == 4` per the documented pattern (describe,
        configure, environment, session) — invariant
      - every beat Artefact has at least one PRODUCES edge to the
        Intent node (provenance moat)
      - `agent_id is None ⇔ consent_to_persist == False` (consent
        gates persistence)
      - `session_handle is None ⇔ agent_id is None` (you cannot
        dispatch without a persisted Agent)
      - interview total token spend `<= max_onboard_tokens` (default
        20000) — cost cap, not a snapshot
- [ ] Test: 4-beat interview captures 4 Artefacts + 1 Intent (mocked);
      consent-withheld path produces Intent but no Agent; consent-given
      path produces persisted Agent + session_handle.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  user types "/agency-onboard" with seed "I want to make a
        concept album about the Enron scandal"
When:   intent.managed_onboard(seed=...) runs
Then:   beat 1 (describe): produces Artefact{kind:"describe",
        body:"album about financial scandal, narrative arc, 10
        tracks"} PRODUCES Intent
        beat 2 (configure): asks about genre/tone; produces
        Artefact{kind:"configure", body:"investigative folk"}
        beat 3 (environment): surfaces music capability verbs +
        researcher skill bundle; produces Artefact{kind:"environment"}
        beat 4 (session): asks consent to persist; on yes, calls
        Spec 137 Lock to create_once Agent A, dispatches session via
        driver.dispatch_session
        AND OnboardOutcome{intent_id, beats:[4], agent_id:"A",
        session_handle:{...}, environment:{verbs:[...], skills:[...]}}

Given:  same flow but user declines persistence at beat 4
When:   the consent gate runs
Then:   OnboardOutcome{intent_id, beats:[4], agent_config:{...},
        agent_id:None, session_handle:None} — Intent captured,
        nothing persisted in the Managed-Agents surface

Given:  driver refuses mid-interview (stop_reason: "refusal")
When:   beat 2's structured-output call returns refusal
Then:   Spec 256 fallback retries on Opus 4.8; on success, beat 2
        proceeds; on exhaustion, the onboard surfaces a
        Codes.ONBOARD_REFUSED reflection and falls back to the
        non-LLM intent_bootstrap (Spec 029) so the user still
        captures SOMETHING
```

## Failure modes (Nygard)

| Failure | Onboard response |
|---|---|
| Driver refusal mid-interview | Spec 256 fallback chain; on exhaustion, degrade to plain `intent_bootstrap` so the session captures intent even without LLM |
| Consent withheld at beat 4 | Intent captured, no Agent persisted, no session dispatched; OnboardOutcome reflects all three Nones |
| Agent already exists (Spec 137 Lock collision) | Reuse — create-once doctrine; record `agent_reused: True` so observability sees the duplicate |
| ZDR org without Fable 5 retention | Driver pre-flights (Spec 170); onboard skips Fable-only beats and dispatches on Opus 4.8 |
| Managed-Agents API unavailable | Onboard completes through beat 3 (Intent + config captured); beat 4 returns `session_handle: None` with `Codes.MANAGED_AGENTS_UNAVAILABLE` so the user knows why |
| User abandons mid-interview | Partial Artefacts persist with `complete: False`; future session can resume by reading the most recent incomplete onboard via `analyze.graph` |
| Onboard budget exhausted | Cap at `max_onboard_tokens`; degrade to a minimal Intent capture; reflection records "onboard truncated by budget" |

## Interconnects

- Spec 029 (parent intent_bootstrap) — this wraps it in the 4-beat
  managed-agents pattern.
- Spec 148 (slash family) — `/agency-onboard` routes here.
- Spec 176 (sessionstart capture) — the Artefact PRODUCES discipline
  this builds on.
- Spec 147 (AnthropicDriver) — the interview model.
- Spec 256 (refusal fallback) — required for the interview to survive.
- Spec 257 (managed cache proof) — onboarding ALWAYS hands off into
  a Managed-Agent session; cache must survive the handoff.
- Spec 260 (slash NL routing) — ambiguous routes land here.
- **UX-onboarding chain** + **harness-in-harness** (Goal 8).

## Open questions

1. **Should the seed text persist as an Artefact, or only the parsed
   describe-beat?** **Recommend**: both — seed as the raw input,
   describe-beat as the LLM-refined version; provenance preserves the
   user's actual words.
2. **What happens when the user resumes an incomplete onboard from a
   prior session?** **Recommend**: the resume path reads the most
   recent `complete:False` onboard via `analyze.graph` and re-enters
   at the next beat; no re-interrogation of completed beats.
3. **How does the user discover what verbs/skills exist for the
   environment beat?** **Recommend**: the environment beat reads the
   live registry (Spec 188 LLM drill against the seed) and surfaces
   the top-5 relevant verbs + skills, not the full catalogue.
