---
spec_id: "351"
slug: liveness-doctor
status: draft
state: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [9]
depends_on: ["039", "054", "303", "336"]
domain: core
wave: core-discipline
---

# Spec 351 — Liveness doctor (*presence ≠ activation*)

> `agency_doctor` today asks **"is X present/installed?"**. This spec adds the
> orthogonal, higher-value question: **"is X actually doing its job in THIS
> environment right now?"** — runtime liveness, asserted by OUTCOME, surfaced at
> session start, with the static-structure checks pushed to `check-drift` where
> CI enforces them. Born from the 2026-06-20 session's dominant failure mode:
> infrastructure that EXISTS in the tree but is DORMANT in the live harness.
> Provenance: `intent:470c1958`; reflections `c4898f0e` (the meta-pattern),
> `3c51981f` (capture root cause), `b3ab3853` (tracked-binary churn),
> `262eb275` (defect-class sweep), `de6eabb3`/`c6b315dc`/`9c9a6d2a` (family B).

## Why (evidence + doctrine)

One session produced four instances of the SAME failure: a mechanism built and
present in the repo, but inactive in the live environment.

| Mechanism | Present? | Active? | How it was found |
|---|---|---|---|
| Spec 336 tool-call capture | ✓ (hooks.json + dispatch + engine handler) | **dormant** — never wired into the live `.claude/settings.json` | `boundary_use_audit=0`, no `toolcalls.db`, by hand |
| codegraph index | ✓ | **corrupt** (SQLite B-tree damage) | a query erroring |
| codegraph.db git-ignore | intended | **violated** (tracked, churning 13MB) | a stop-hook complaint |
| `spec_id` uniqueness | gated nowhere | **collided** (338, then 348) | a reviewer comment, twice |

Each was discovered late, by accident, after costing real work. The unifying
lesson (`reflection:c4898f0e`): **presence ≠ activation** — verifying that code
or config EXISTS proves nothing about whether the mechanism FIRES. The substrate
already owns the question of its own health (`agency_doctor`, Spec 039 — "doctor
green or names the gap", GOALS.md Goal 9). It diagnoses *silent-failure modes*;
dormancy is the silent-failure mode it does not yet name.

**Doctrine fit.** This is the RUNTIME sibling of Spec 054 drift detection. Drift
asks "is the open SET in sync?" (static, CI). Liveness asks "is the mechanism
FIRING?" (runtime, in-session). Spec 153's dormant-schemas gate is the narrow
precedent ("a declared schema nothing emits is dead code"); Spec 351 generalises
*dormant surface* from schemas to **activation**.

## Design

### Two homes, by decidability (the panel's load-bearing cut)

A check belongs in the **runtime doctor** ONLY if a static gate cannot see it.
Everything statically decidable from the tree belongs in **`check-drift`**, where
CI enforces it on every PR instead of waiting for someone to run the doctor.

```
RUNTIME (agency_doctor.liveness)   — needs a live session/process to decide
STATIC  (scripts/check-drift)      — decidable from the tree alone → CI-enforced
```

### A — `agency_doctor` gains a `liveness` block (runtime-only, OUTCOME-asserted)

Each check returns `{name, status, evidence, fix}` with
`status ∈ {firing, dormant, unknown}`. **A check asserts an OUTCOME, never a
config** — otherwise the liveness check commits the very sin it diagnoses
(a wired hook in `settings.json` is still just *presence*; only a row in
`toolcalls.db` proves the hook *fired*).

- **`provenance_capture`** — did the Spec 336 tool-call store receive ≥ 1 row
  in the current session? `firing` (rows this session) / `dormant` (store exists
  but empty, or no store) / `unknown` (cannot resolve). The fix string cites the
  PR #231 wiring + `verify.presence-is-not-activation`. This is the check that
  would have caught this session's bug on call one.
- **`capture_store_writable`** — does `ToolcallStore` resolve to a real path, not
  the silent `:memory:` fallback (which loses every row)? Catches a mis-resolved
  `AGENCY_TOOLCALLS_DB` / unwritable `.agency/`.

That is the whole runtime surface — **two checks**, both seeing something static
analysis cannot. Index integrity is explicitly OUT (codegraph health is
codegraph's concern; `PRAGMA integrity_check` is O(db size) and would tax every
doctor call — Nygard's cost guard).

### B — static-structure checks move INTO `check-drift` (CI-enforced)

- **`spec_id_unique`** — `grep '^spec_id:' Plan/*/spec.md | sort | uniq -d`
  must be empty. (Catches the 338/348 collision class automatically — the
  reviewer found it twice by hand; CI finds it once, forever.)
- **`tracked_db_binaries`** — `git ls-files '*.db'` must be empty (no SQLite
  binary re-enters tracking past the `*.db` ignore).

These exit non-zero in `check-drift`, the existing gate (`reflection:262eb275`:
fix the class, not the instance — a CI gate IS the class fix).

### C — auto-surface (the leverage upgrade)

A doctor nobody runs is itself dormant (Meadows: a check you must remember has
the blind spot it diagnoses). The `SessionStart` hook — which already fires —
runs the `liveness` block and prints any `dormant` line to the session banner.
Dormancy announces itself; no one has to think to ask.

### D — the learnings as queryable doctrine rules (Spec 303)

Family B (behavioural) lessons land as DATA in the doctrine registry — cheap,
queryable, cited by liveness `fix` strings, enforced by review not code:

- `verify.presence-is-not-activation` — the meta-rule; a liveness/health check
  must assert an outcome, never the presence of its own enabling config.
- `verify.exact-ci-command` — replicate the EXACT CI invocation locally
  (flags, `--root`, `--baseline`, `--strict`) before claiming green
  (`reflection:de6eabb3`). (Why a rule, not a check: "did CI run THIS sha?"
  needs the network; the doctor stays offline — frugal floor.)
- `verify.measure-before-hang` — measure a baseline runtime before declaring a
  hang; low xdist-master CPU is normal (`reflection:c6b315dc`).
- `test.no-ambient-secret` — a test asserting a no-key path must control
  `os.environ`, never rely on the ambient shell (`reflection:9c9a6d2a`).
- `fix.sweep-the-class` — a reported structural defect is a sample; sweep the
  whole class (`reflection:262eb275`).
- `artifact.untrack-rebuildables` — local rebuild artefacts stay untracked AND
  pattern-ignored (`reflection:b3ab3853`).

## Done-When (acceptance — Gherkin-shaped, behaviour not implementation)

- [ ] `agency_doctor`'s report carries a `liveness` block: a list of
      `{name, status, evidence, fix}` with `status ∈ {firing, dormant, unknown}`.
- [ ] `provenance_capture` returns `dormant` when the toolcall store has no rows
      this session, and `firing` when it has ≥ 1 — asserted on the store OUTCOME,
      not on `settings.json` content.
- [ ] `capture_store_writable` returns `dormant`/`unknown` when the store
      resolves to `:memory:` or an unwritable path, `firing` otherwise.
- [ ] A `liveness` check that raises is caught and reported as `unknown` —
      the doctor never crashes on a check (self-guard).
- [ ] `agency_doctor.ok` DEGRADES (warns) on dormancy but does NOT hard-fail —
      dormancy can be intentional (e.g. no capture by choice).
- [ ] `scripts/check-drift` gains `spec_id_unique` + `tracked_db_binaries`;
      both exit non-zero on violation. The current `spec_id: "348"` collision is
      resolved so the new check passes (Slice 1 closes it).
- [ ] The `SessionStart` path renders any `dormant` liveness line into the
      session banner (auto-surface).
- [ ] The six family-B rules are registered + queryable via the `doctrine`
      capability; each liveness `fix` cites a rule id.
- [ ] Acceptance scenarios under `tests/acceptance/`; `check-drift` +
      `check-doc-drift` clean; `TODO.md` row added.

## Invariants (relationships, not magic numbers — rule 8)

- A liveness check's verdict is a function of an OBSERVED OUTCOME (a row count, a
  resolved path), never of the presence of config/code. (The anti-trap invariant.)
- `live_static_checks ⊆ check-drift`, `live_runtime_checks ⊆ agency_doctor` — a
  check that is statically decidable is NOT in the doctor (no duplication).
- `dormant ⇒ degraded`, never `dormant ⇒ crash` and never `dormant ⇒ hard-fail`.
- Every `fix` string names a doctrine rule id (traceable remediation).

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| A liveness check raises | caught → `status="unknown"` + the error in `evidence`; doctor continues |
| No git repo (drift checks) | `spec_id_unique`/`tracked_db_binaries` skip with a `n/a` note, never fail |
| Toolcall store is `:memory:` (in-memory engine / tests) | `capture_store_writable` = `dormant` with the reason; not an error |
| Large DB integrity | not attempted — index health is out of scope (cost guard) |
| Dormancy is intentional | `ok` warns (degraded), never blocks; the banner line is advisory |
| The doctor itself isn't run | the `SessionStart` auto-surface covers the highest-value check |

## Interconnects

- **Spec 336** (tool-call capture) — the mechanism `provenance_capture` verifies;
  its PR #231 wiring is what `firing` confirms.
- **Spec 054** (drift) — the static sibling; `spec_id_unique`/`tracked_db_binaries`
  land in its `check-drift` gate.
- **Spec 153** (dormant-schemas gate) — the narrow precedent liveness generalises.
- **Spec 303** (doctrine) — home of the family-B rules.
- **Spec 039 / 334** (`agency_doctor`) — the host surface extended; the CLI
  `agency-doctor` inherits the `liveness` block for free.

## Slices (TDD)

1. **`check-drift` static checks + close the live 348 collision.** Add
   `spec_id_unique` + `tracked_db_binaries`; resolve the current `spec_id: "348"`
   duplicate so the gate is green. (Highest leverage, smallest surface — the
   class fix.)
2. **`agency_doctor.liveness` block** — `provenance_capture` +
   `capture_store_writable`, outcome-asserted, self-guarded, `ok` degrades.
3. **Auto-surface** on `SessionStart`; **doctrine rules** registered + cited.

## Open questions (resolved at brainstorm + panel)

1. Dormancy → warn or hard-fail? **Resolved: warn (degrade), never hard-fail.**
2. "Did CI run THIS sha?" → live check or rule? **Resolved: a doctrine rule
   (`verify.exact-ci-command`) — the doctor stays network-free.**
3. Liveness via config-presence or outcome? **Resolved (panel): OUTCOME only —
   else the check commits the presence≠activation sin it diagnoses.**
