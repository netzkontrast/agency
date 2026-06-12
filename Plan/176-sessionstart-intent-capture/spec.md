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

## Done When (measurable invariants — rule 8)

- [ ] **Typed capture record: `IntentCapture{intent_id,
      captured_at, source: Literal["sessionstart", "manual",
      "auto_ad_hoc"], artefact_ids: list[str], turns: int}`** —
      one per session; SERVES the captured Intent.
- [ ] **Invariant: SessionStart is non-blocking** — capture offer
      times out within `SESSIONSTART_OFFER_TIMEOUT_MS` (default 200ms)
      regardless of user response; never gates the session.
- [ ] **Invariant: idempotent across re-entry** — an open Intent in
      `.agency/session.db` ⇒ hook NO-OPs (no re-prompt). Asserted by
      running the hook twice in the same session.
- [ ] **Invariant: accepted-capture turns each PRODUCE an Artefact**
      — `len(artefact_ids) == turns` (Spec 076 dispatch); a turn that
      writes nothing is impossible (a write per turn is the contract).
- [ ] **Invariant: declined-capture falls back to `auto_ad_hoc`** —
      a default Intent with `scope="ad_hoc"` is created so subsequent
      verbs have something to SERVE; later manual captures supersede
      (Spec 014 amendment pattern).
- [ ] **Invariant: `AGENCY_INTENT` env reflects the captured (or
      ad_hoc) intent_id** for the lifetime of the session — Spec 018
      consumer; verified by running an arbitrary verb post-capture
      and checking the SERVES edge target.
- [ ] **Failure modes (capture path):** Driver (Spec 147) absent →
      fall back to a templated 3-question prompt (no LLM); Driver
      `RATE_LIMITED` mid-capture → save partial turns + emit
      `Codes.CAPTURE_DEGRADED`; user Ctrl-C mid-capture → the
      already-written turns persist + `auto_ad_hoc` intent supersedes
      (no orphan Artefacts).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  fresh repo clone; `.agency/session.db` has no open Intent;
        SessionStart hook fires; `[anthropic]` present
When:   the user accepts the `/agency-onboard` invite within the
        offer timeout (else auto_ad_hoc proceeds)
Then:   Spec 147 Driver runs the conversational capture (3-5 turns);
        each turn writes an Artefact (PRODUCES edge); the captured
        Intent lands in the graph; AGENCY_INTENT env set to its id;
        re-running the hook in the same session NO-OPs

Given:  same fresh clone; user dismisses the invite (presses Esc)
When:   any subsequent verb (e.g. analyze.run) executes
Then:   the verb's Invocation SERVES the auto_ad_hoc Intent (never
        orphan); the user can later run intent_bootstrap to supersede

Given:  user accepted capture, mid-flow the Driver returns
        RATE_LIMITED on turn 4 of 5
When:   capture pauses
Then:   turns 1-3 persist with their PRODUCES Artefacts; CAPTURE_DEGRADED
        Reflection links to the Intent; AGENCY_INTENT still resolves;
        the user can resume on next session
```

## Failure modes (Nygard)

| Failure | Hook response |
|---|---|
| Driver missing | templated 3-Q fallback (no LLM); same Artefact write contract |
| Driver `RATE_LIMITED` mid-capture | partial turns persist; `CAPTURE_DEGRADED`; resumable |
| Driver `REFUSAL` | the offending turn dropped; capture continues with the next prompt |
| User Ctrl-C mid-flow | partial turns persist; auto_ad_hoc supersedes; no orphan |
| `.agency/session.db` write locked | hook NO-OPs + Reflection (never block session); user can retry |
| Hook itself crashes | session proceeds (non-blocking guarantee); Spec 062 already covers |

## Interconnects

- **UX-onboarding chain** (148) — the invite renders the
  `/agency-onboard` slash command (Spec 175-derived).
- **LLM-driver chain** (147) — Driver powers the conversational
  capture when present; degrades cleanly absent the extra.
- **Output-budget chain** (146) — Driver calls honor the envelope;
  turns budget through it.
- **Dogfood-loop chain** (150/173) — every Reflection emitted during
  capture is link-complete (post-promotion) so the classifier can
  read it.
- Spec 062 (SessionStart hook) is the parent substrate.
- Spec 076 (unified hooks) is the dispatch substrate.
- Spec 018 (`AGENCY_INTENT` env) is the propagation consumer.
- Spec 014 (amendment) — manual captures supersede `auto_ad_hoc`
  via the amendment pattern.
- Spec 170 (doctor) reports `sessionstart_capture.ready`.
- Spec 151 (Codes coverage) supplies `CAPTURE_DEGRADED`.

## Open questions

1. Block the session on capture? **Recommend**: never block — offer +
   one-keystroke accept within `SESSIONSTART_OFFER_TIMEOUT_MS`; a
   session always proceeds (`auto_ad_hoc` Intent as fallback);
   later captures supersede.
2. How many capture turns? **Recommend**: 3-5 max (purpose, deliverable,
   acceptance per CLAUDE.md `intent_bootstrap` protocol); a longer
   interview belongs in `develop.brainstorm`.
3. Persist the capture transcript outside the graph? **Recommend**:
   no — transcript = the chain of Artefacts (PRODUCES) + the Intent;
   rendering markdown on demand from the graph (rule 2).

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion` as part of
the typed-shape wave-1 batch (intent:ba14917e tdd walk).

### Done — Slice 1

Typed frozen dataclass + `__post_init__` invariants — see
`agency/_link_finding.py` (Spec 173) and `agency/_typed_shapes_wave1.py`
(Specs 171/175/176). 19 tests in `tests/test_link_finding.py` +
`tests/test_typed_shapes_wave1.py`. The data shape is the Slice 1
contract; Slice 2 wires it into the live verb / gate / hook layer.

### Still — Slice 2+

See the spec's main "Done When" + "Still" sections. The Slice 2
wiring path (graph query, CI gate, sessionstart hook, install
generator) is the next step.

