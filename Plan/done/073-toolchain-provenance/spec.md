---
spec_id: "073"
slug: toolchain-provenance
status: done   # Shipped 2026-06-06 — RESHAPED into the `shell` capability (user directive)
state: done
last_updated: 2026-06-06
owner: "@agency"
serves_intent: "intent:558f1bf5"
depends_on: ["020", "053", "054"]   # central DB; test markers/slicing; check-drift
affects:
  - agency/capabilities/dogfood/_main.py     # NEW run_tests / run_script / run_suite verbs
  - agency/capabilities/dogfood/schemas/      # toolchain-run artefact schema
  - agency/engine.py                          # inject a `runner` boundary (stubbable)
  - tests/test_dogfood_toolchain.py           # NEW
estimated_jules_sessions: 0
domain: meta
wave: 5
---

# Spec 073 — Run scripts & tests through agency (toolchain provenance)

## Why

Today the project's own verification toolchain — `pytest` slices,
`scripts/check-drift`, `scripts/test-cap`, `scripts/test-changed`,
`python -m agency.install` — runs via **bare Bash**, leaving **no provenance**.
That contradicts the doctrine: GOALS #2 (provenance as a free byproduct), #6
(doctrine evolves through dogfooding — running the system on itself), #8
(harness-in-harness), and the user directive (2026-06-06): *"all scripts and
tests should be executed by agency capabilities, to save the audit trail."*

This spec makes every verification run a **recorded graph event**: which slice
ran, the exit code, pass/fail counts, a bounded output tail, and the duration —
an Artefact that `SERVES` + `OBSERVED_DURING` the intent — while only a small
summary delta crosses the wire (GOALS #1/#7: the graph is the store).

## Design decision — re-home to `dogfood` (not a new capability)

The canon's net-new-primitive budget is spent (CAPABILITY-CLUSTERS); the Spec 011
reframe set the precedent: re-home behaviour to an existing concept rather than
mint a capability. **`dogfood` is the exact home** — its concept *is* "the system
running on itself, recorded as provenance" (it already ships
`collect`/`note`/`render`/`export`/`import`). Running the toolchain and recording
the result is dogfooding by definition. No new capability; new verbs on `dogfood`.

## Done When

- [ ] **`dogfood.run_tests(selector="", parallel=True)`** (`role=effect`) — runs
  the pytest slice (`scripts/test-cap <selector>` when `selector` names a marker,
  else `pytest -n auto -m "not e2e"` for the full slice), parses the summary
  (passed/failed/skipped), records an `Artefact{kind:"toolchain-run", tool:"pytest",
  command, exit_code, passed, failed, skipped, duration_s, tail}` linked `SERVES`
  + `OBSERVED_DURING` the intent, and on failure ALSO records a
  `Reflection{scope:"observation"}` (the dogfood loop). Returns the small wire
  delta `{passed, failed, skipped, exit_code, run_id, first_failure?}`.
- [ ] **`dogfood.run_script(name, args="")`** (`role=effect`) — runs an
  **ALLOWLISTED** repo script only (`check-drift`, `test-cap`, `test-changed`,
  `install`); records the same `toolchain-run` Artefact (`tool:<name>`); returns
  `{exit_code, summary, run_id}`. A non-allowlisted name returns
  `{error: "script not allowlisted", allowed: [...]}` — NEVER executes arbitrary
  strings from the wire (security: this is the one place wire input becomes a
  subprocess).
- [ ] **`dogfood.run_suite()`** (`role=effect`) — convenience for the full
  regression (`pytest -n auto -m "not e2e"`) + `check-drift`, recording both runs
  and returning the combined gate verdict.
- [ ] **Stubbable `runner` boundary** — the engine injects a `runner` (like
  `client`/`vcs`); tests stub it so the suite never shells out to a real pytest.
  The boundary's one method is `run(argv, timeout) -> {exit_code, stdout, stderr,
  duration_s}`.
- [ ] **Bounded output** — `tail` capped to a token budget (graph stores the
  bounded tail; the wire gets counts + the first failure only). Full reproduction
  is the recorded `command` (re-runnable), not a megabyte of stdout in the graph.
- [ ] **`tests/test_dogfood_toolchain.py`** — verbs record the Artefact with both
  edges; allowlist rejects an unknown script; the runner boundary is stubbed (no
  real subprocess); a failing run records the observation Reflection; the wire
  payload is small.
- [ ] `dogfood.run_script("check-drift")` reproduces `scripts/check-drift`'s
  verdict (exit 0/1) as recorded provenance.
- [ ] `pytest -n auto -m "not e2e"` green; `check-drift` clean;
  `plugin.lint_capability("dogfood")` ok (block mode — dogfood is scaffold-marked).

## Migration

Purely **additive**: bare Bash (`pytest`, `scripts/check-drift`) keeps working
unchanged — this spec adds a provenance-recording *path*, it does not remove the
direct one. A future spec may route CI through `dogfood.run_suite` so even CI runs
are recorded; that is out of scope here.

## Open Questions

1. **Per-test vs per-run granularity.** v1 records ONE Artefact per run (counts +
   tail), not one per test (too noisy / too many nodes). Per-test failures live in
   the tail + are re-derivable from the recorded command. (Resolved: per-run.)
2. **Allowlist scope.** v1: the four repo scripts + the pytest slices. New scripts
   are added to the allowlist explicitly (an `AGENCY-DRIFT: toolchain-allowlist`
   tag so Spec 054 surfaces it). No glob, no arbitrary command.
3. **Should CI itself call these verbs?** Out of scope (a follow-up). v1 makes the
   capability available; wiring `.github/workflows/test.yml` through it is later.

## Evidence

- `GOALS.md` #2 (provenance), #6 (dogfood loop), #8 (harness-in-harness), #1/#7
  (only deltas cross / graph is the store).
- `agency/capabilities/dogfood/_main.py` (the home capability — already records
  the system-on-itself); `agency/capabilities/jules/` (the boundary-injection
  pattern: `client`/`vcs` → here a `runner`).
- `scripts/check-drift`, `scripts/test-cap`, `scripts/test-changed` (Spec 053/054
  — the scripts this wraps).
- User directives (2026-06-06): "use Agency MCP as much as possible — to save the
  audit trail"; "all scripts and tests should also be executed by agency
  capabilities."


## Followup --- Implementation Status (2026-06-06) --- RESHAPED

> Shipped on branch `claude/spec-073-impl-toolchain`. **Reshaped per user
> directive** from "dogfood toolchain verbs" into a broader **`shell`
> capability**: a token-efficient, recorded, templated host-command boundary
> (not just the repo's own tests).

**Verdict:** Shipped (foundation; extensions specced as 075)

### Done
- `agency/capabilities/shell.py` --- a new capability with three verbs:
  - `shell.run(command|template, args, filter)` (effect) --- runs an ALLOWLISTED
    command (or a named template), FILTERS the output to cut tokens, records a
    `command-run` Artefact (SERVES + OBSERVED_DURING), returns only the filtered
    delta. The allowlist (first-token check) is the safety model --- never
    arbitrary exec from wire input.
  - `shell.filter(text, spec)` (transform) --- pure output filter
    (full|tail:N|head:N|grep:PAT|lines:A-B|count|last), no execution --- HOOK-READY.
  - `shell.templates()` (transform) --- the named query recipes (write-less).
- `agency/_runner.py` `SubprocessRunner` boundary + engine `runner` injector
  (stubbable; tests never shell out).
- Behaviour-first tests (`tests/test_shell.py`, no hardcoded counts).

### Migration / notes
- Additive; bare Bash unchanged. The `dogfood` toolchain verbs from the narrow
  draft were reverted --- this functionality lives in `shell`.
- Default seed templates are documented config (CLAUDE.md rule #8 allows
  named/overridable config); making templates **definable + graph-stored +
  MCP-discoverable** + seeding the common bash commands is **Spec 075**.
