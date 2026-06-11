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

- [ ] **Welcome shows the full driver matrix** — typed shape
      `DriverReadiness = {driver: str, configured: bool, verified:
      bool, remediation: str | None, hint_url: str | None}` for each of
      jules / anthropic / fable / managed_agent / inline. A `not
      configured` row carries a one-line remediation (Spec 170 hint
      pattern); a `configured but not verified` row carries the verify
      command.
- [ ] **`/agency-doctor` slash** (Spec 148 family) renders it on
      demand; same renderer as welcome's first-touch view.
- [ ] **Onboarding (Spec 262) chains it** when the user accepts
      capture — the onboarding flow surfaces only the gaps, not the
      already-green rows.
- [ ] **The Spec 030 statefulness preserved** — once a green row is
      seen, it doesn't repeat on subsequent sessions unless `verified`
      flips back to False (key rotation, env unset).
- [ ] **Driver matrix is OPEN-SET** — derived from the registered
      driver list (Spec 271 `RemoteDriver` registry + Spec 147
      AnthropicDriver registration), not a hand-pinned 5-row block. A
      new driver appears in the matrix when it registers.
- [ ] **Invariants** (CLAUDE.md rule 8):
      - `set(welcome.matrix.rows) == set(registered_drivers) ∪
        {inline}` — symmetric difference is a drift violation.
      - For every `DriverReadiness` row where `configured=True AND
        verified=True`, `remediation is None` — green rows carry no
        noise.
      - For every row with `configured=False`, `remediation is not
        None AND remediation.startswith(actionable_verb)` — every gap
        has a fix.
      - Stateful suppression: a row that flipped green in session N
        does NOT appear in welcome of session N+1 unless its state
        regresses (verified by snapshot diff).
- [ ] **Failure modes table** — see below.
- [ ] Test: welcome reports the full matrix + remediations; stateful
      repeat suppressed; a newly-registered driver auto-appears; a
      revoked key flips the row red with the remediation.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  fresh session, JULES_API_KEY set + verified, ANTHROPIC_API_KEY
        unset, Fable retention not configured, managed_agent ready
When:   agency_welcome runs
Then:   matrix renders 5 rows: jules=green (suppressed if seen prior
        session), anthropic=red ("export ANTHROPIC_API_KEY=sk-..."),
        fable=red ("run agency_fable_config retention=..."), MA=green,
        inline=green; onboarding chain only surfaces the 2 red rows

Given:  next session, same env, no state change
When:   agency_welcome runs
Then:   stateful filter suppresses green rows; only the 2 red rows
        render; if the user resolves anthropic mid-session,
        agency_doctor re-runs and surfaces the now-green row once
        (acknowledgment), then suppresses it next session

Given:  Spec 271 registers a new driver "remote_agent_x" in the
        RemoteDriver registry
When:   agency_welcome renders next
Then:   the matrix auto-grows a 6th row for remote_agent_x with its
        readiness predicate (registered by the driver's own
        capability); no hand-edit to doctor code
```

## Failure modes

| # | Failure | Detection | Response |
|---|---|---|---|
| F1 | Driver-readiness probe network call hangs | Per-probe timeout (default 2s) | Render row as `configured=True, verified=unknown` with hint "probe timeout — retry"; never block welcome |
| F2 | Hand-pinned driver list drifts from registry | Set-equality invariant check at render | Render fails closed (visible error in welcome) + emits `driver_matrix_drift` MonitorEvent |
| F3 | Stateful suppression masks a regression | State snapshot diff per session start | A green→red flip ALWAYS renders (suppression only applies to stable greens) |
| F4 | Remediation string is non-actionable ("contact support") | Lint at register time | Reject driver registration without an actionable remediation template |
| F5 | Onboarding chain spams the user with greens | Filter check | Onboarding surfaces only `configured=False` rows; greens stay in `/agency-doctor` on demand |
| F6 | `/agency-doctor` slash invoked before any Intent bootstrapped | Pre-flight check | Render matrix anyway (doctor is global, not intent-scoped); do NOT require Intent |

## Interconnects

- Spec 030 (parent) — agency_doctor + stateful welcome.
- Spec 170 (doctor deepening) is the report engine.
- Spec 262 (onboarding cap) chains the welcome → onboarding handoff.
- Spec 263 (Fable extras) registers Fable retention as a driver row.
- Spec 147 (AnthropicDriver) registers as a driver row.
- Spec 271 (Jules/MA bridge) defines the `RemoteDriver` registry the
  matrix derives from — open-set drift gate.
- Spec 148 (slash family) provides `/agency-doctor`.
- Spec 274 (structured monitor) records `driver_matrix_drift` +
  readiness-probe failures.
- Spec 277 (dispatch LLM refine) reads driver readiness to skip
  unavailable drivers in the heuristic.
- **UX-onboarding chain** + **agent-uniform** (Goal 3) extension —
  every driver shares the readiness shape.

## Open questions

1. **Probe cadence.** Probe drivers every welcome, or cache?
   **Recommend**: cache for `ttl=5min` per driver — frequent welcomes
   in the same session don't re-probe; stale state caught by
   regression-detection on next session start.
2. **Driver-specific verification depth.** Should the doctor make a
   *real* API call per driver (cost) or just key-format check (cheap)?
   **Recommend**: cheap on welcome (key-format + reachability HEAD);
   `/agency-doctor --deep` does a real probe per driver. Default
   path stays fast.
3. **Onboarding-vs-doctor split.** Should `/agency-doctor` ever
   trigger onboarding? **Recommend**: only when ALL drivers red — a
   fresh-install signal; otherwise doctor surfaces gaps without
   hijacking the session.
