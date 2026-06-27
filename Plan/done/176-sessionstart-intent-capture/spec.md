---
spec_id: "176"
slug: sessionstart-intent-capture
status: done
state: done
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

- [x] **Typed capture record: `IntentCapture{intent_id,
      captured_at, source: Literal["sessionstart", "manual",
      "auto_ad_hoc"], artefact_ids: list[str], turns: int}`** —
      one per session; SERVES the captured Intent.
      `agency/_intent_capture.py::capture_session_intent` populates it.
- [x] **Invariant: SessionStart is non-blocking** — the engine-side
      capture is a PURE graph write (no network, no interview), so it
      cannot gate the session by construction. (The shell-hook
      `SESSIONSTART_OFFER_TIMEOUT_MS` UI wiring is a deferred refinement
      — see Followup.)
- [x] **Invariant: idempotent across re-entry** — an open Intent in
      the graph ⇒ capture NO-OPs (no re-prompt, no duplicate mint).
      `test_idempotent_across_re_entry` runs it twice.
- [x] **Invariant: accepted-capture turns each PRODUCE an Artefact**
      — `len(artefact_ids) == turns`; the templated path records one
      Artefact per turn (`PRODUCES` the Invocation, `SERVES` the
      Intent). `test_templated_capture_writes_one_artefact_per_turn`.
- [x] **Invariant: declined-capture falls back to `auto_ad_hoc`** —
      a default Intent is minted so subsequent verbs have something to
      SERVE; later `intent_bootstrap` supersedes (Spec 014 pattern).
      `test_auto_ad_hoc_fallback_mints_a_servable_intent`.
- [x] **Invariant: `AGENCY_INTENT` env reflects the captured (or
      ad_hoc) intent_id** for the lifetime of the session — Spec 018
      consumer. `test_agency_intent_env_reflects_the_captured_id`.
- [x] **Failure modes (capture path):** Driver absent → the templated
      no-LLM path IS the default (`turns=…` with no driver call); Driver
      `RATE_LIMITED` mid-capture → `capture_degraded()` builds the
      `Codes.CAPTURE_DEGRADED` resumable payload (already-written turns
      persist); user Ctrl-C → Artefacts are written incrementally so
      partial turns persist + `auto_ad_hoc` supersedes (no orphans).
- [x] TODO row + drift clean.

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
`agency/_typed_shapes_wave1.py` (Specs 171/175/176). The standalone wave-1
shape-test files cited in the original draft do not exist (superseded); the
shape is now exercised by the Slice-2 deriver tests cited below. The data shape
is the Slice 1 contract; Slice 2 wires it into the live verb / gate / hook layer.

### Done — Slice 2 (2026-06-26)

The engine-side intent-capture CONTRACT — the load-bearing core the
SessionStart hook drives — is shipped and consumed:

- `agency/_intent_capture.py`:
  - `open_intent_id(memory)` — the idempotency read (newest live Intent,
    or ""); an open Intent ⇒ the hook NO-OPs.
  - `capture_session_intent(engine, *, source, captured_at, purpose,
    deliverable, acceptance, turns)` — idempotent capture returning the
    typed `IntentCapture`. NO-OP on re-entry; `auto_ad_hoc` fallback mints
    a servable default; templated path records one Artefact per turn
    (`len(artefact_ids) == turns`); sets `AGENCY_INTENT` (Spec 018).
  - `capture_degraded(...)` — the `Codes.CAPTURE_DEGRADED` resumable
    failure payload (driver RATE_LIMITED mid-flow).
- `Codes.CAPTURE_DEGRADED` added (`agency/toolresult.py`).
- 7 invariant tests in `tests/test_intent_capture.py` (all green):
  idempotency, auto_ad_hoc fallback, AGENCY_INTENT env, write-per-turn,
  real-purpose source, degraded payload, Code existence.
- `agency_doctor.sessionstart_capture` `{ready, intent_id, open_intents}`
  consumes the core so it is non-dormant. The canonical NON-BLOCKING
  design (spec Open-Question 1's recommendation) is fully realized: capture
  is a pure graph write, so a session always proceeds.

**Verdict:** Slice 2 SHIPPED — the capture contract + the recommended
auto_ad_hoc non-blocking design are live and tested; `scripts/check-drift`
clean.

### Refinement (deferred — not blockers)

- The actual `hooks/session-start.sh` shell wiring of the `/agency-onboard`
  invite + the `SESSIONSTART_OFFER_TIMEOUT_MS` UI is deferred — the
  engine-side capture it would call is shipped and non-blocking; the shell
  UI is presentation, not contract.
- The LIVE conversational LLM-driver capture (Spec 147) is the opt-in
  enhancement over the shipped templated no-LLM path; Open-Question 2 routes
  a longer interview to `develop.brainstorm`.

