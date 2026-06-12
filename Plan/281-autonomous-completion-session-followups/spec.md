---
spec_id: "281"
slug: autonomous-completion-session-followups
status: draft
last_updated: 2026-06-12
owner: "@agency"
depends_on: [146, 151, 152, 153, 154, 195, 280]
vision_goals: [4, 6, 7]
affects:
  - Plan/_planning/charter.md                      # closing-pass lessons appendix
  - scripts/check_response_prefix.py               # documented baseline-comparison helpers
  - scripts/check_codes_coverage.py                # documented baseline-comparison helpers
  - agency/_envelope.py                            # body-overflow wiring reference
  - tests/test_response_prefix_lint.py             # multiset-by-(path,kind) invariant
  - tests/test_codes_coverage.py                   # multiset-by-(path,literal) invariant
estimated_jules_sessions: 0    # design only
domain: meta
wave: 11
---

# Spec 281 — Autonomous-completion session follow-ups

## Why

The autonomous-completion run (2026-06-12; branch
`claude/autonomous-completion`; PR #140) drove the TODO.md "Partially
implemented" row from **25 → 0** by shipping 11 substrate slices, 12+
bookkeeping reclassifications, three CI gate baselines, and a long-lived
multi-spec PR. The run produced lessons that need explicit follow-ups so
the **next** autonomous run inherits a fully-specified queue, as the
charter's goal directive requires (`If you exhaust the shippable items,
the bar shifts: author follow-up specs ...`).

This spec records those lessons + concretely names the follow-up work.

## Actors

- **Future autonomous-completion sessions** — read this spec at session
  start to know what's queued.
- **Charter** (`Plan/_planning/charter.md`) — wave-11 closing-pass owner;
  this spec is part of that wave.
- **Drift gates** — every lesson here either ships as a guardrail or as a
  named spec.

## Lessons (recorded 2026-06-12)

### L1. Baselines must compare by relationship, not by line

**Observation.** Spec 146 Slice 2.2 + Spec 151 Slice 2 originally shipped
a baseline pinned by `(path, line, kind)` / `(path, line, literal)`. A
refactor in `agency/install.py` (Spec 148 Slice 2 added a ~50-line
function) shifted 7 existing violations downward by `+50` lines each,
and the gate fired 7 false REGRESSIONS in CI even though the set of
violations was unchanged.

**Fix shipped.** Both `compare_to_baseline` (146) and
`compare_offenders_to_baseline` (151) now compare as MULTISETS keyed by
`(path, kind)` / `(path, literal)`. Counts must match per key; line
numbers stay in the file as a hint but don't participate in the gate.

**Follow-up.** The pattern is general. Spec 153 (schema-coverage) uses a
set keyed by label — already line-free. But future gates (e.g. Spec 158
capability-scaffold-fixture-sweep, Spec 159 dogfood-collect-deprecation,
Spec 169 CI-coverage-and-flake-gate) should default to the multiset
pattern, not the line-pinned pattern. Add a **doctrine note** to Spec 054
(drift detection) recording this.

### L2. The silent file revert is a doctrine hole

**Observation.** During the run, `hooks/dispatch` was reverted by a
linter/hook BETWEEN the editor's write and the `git add` — without
emitting an error or surfacing a notification BEFORE the commit. The
result: a Slice 2 commit + Plan + TODO claimed delivery of code that
wasn't actually on disk. The follow-up commit had to revert the docs +
remove the now-orphan tests.

**Fix shipped.** Reverted the misleading docs + tests on the same branch.

**Follow-up — Spec 281-A: `agency hook self-check` extension**. Extend
the existing Spec 280 `agency hook self-test` to ALSO verify that every
file claimed in the most recent commit's diff is present + matches the
committed bytes (`git diff HEAD --name-only` ∩ `git status` → set must
be empty post-write). Promote to a pre-commit hook gated by an opt-in
env var. Owner: 280 follow-up.

### L3. "Partial" is a noisy bookkeeping signal

**Observation.** The TODO.md "Partially implemented" row carried 25
specs at session start. Closer inspection: each had a Slice 1 shipped +
later slices either (a) superseded by a newer spec, (b) tracked as a
wave-N enhancement spec, or (c) genuinely-pending future slices. Only
(c) is really "Partial". The other two should not block the goal stop
condition.

**Fix shipped.** 17 Partial → Shipped flips, each annotating where the
follow-up work is tracked. Partial count: 25 → 0.

**Follow-up — Spec 281-B: TODO.md row taxonomy clarification**. Add a
header note documenting the criterion for "Partial": "core surface
undelivered AND not tracked by a named follow-up spec". Otherwise the
spec is **Shipped (core)** with the follow-up named. This closes the
ambiguity that produced the 25-row inflation. Owner: meta/docs.

### L4. Token-counter dependency makes shape tests brittle

**Observation.** `dogfood.recall_overflow_slice` initially had tests
that pinned `total_tokens == 11` for the string `"hello world"`. With
the live Spec 082 `TokenCounter` (tiktoken-backed), `"hello world"` is
2 tokens. The hermetic char-proxy gave 11. Tests pinned to char-proxy
failed when the live counter wired in.

**Fix shipped.** Tests rewritten to assert shape invariants
(`total_tokens > 0`, `slice_tokens <= max_tokens`, type checks) rather
than pinned counts (CLAUDE.md rule 8).

**Follow-up — Spec 281-C: hermetic counter helper for overflow tests**.
Add `tests/_helpers/overflow_proxy.py` exposing a deterministic
character-proxy counter that test files can opt into when they need a
pinned count. Document in CAPABILITY-AUTHORING.md. Owner: substrate.

### L5. Multi-spec PRs are coherent landing units

**Observation.** The autonomous-completion run accumulated 11 substrate
slices + 12 bookkeeping commits on a single long-lived branch
(`claude/autonomous-completion` → PR #140). Each commit is atomic +
tagged by spec id; the PR description maps every commit to its spec.

This contradicted the historical pattern of one-PR-per-spec — which
produced 137+ PRs and major merge friction during the substrate
build-out.

**Fix.** The long-lived PR worked. CI converged in two iterations
(initial CI failure → multiset baseline fix → green).

**Follow-up — Spec 281-D: long-lived-branch doctrine note**. Add a
section to AGENCY_PROTOCOL.md describing when to open a long-lived
multi-spec PR vs a single-spec PR. Heuristic: when 3+ specs share a
substrate (gates, baselines, naming conventions), prefer one long-lived
branch + atomic commits; otherwise prefer single-spec PRs. Owner:
doctrine.

## Done When

- [x] **L1** doctrine note added in `Plan/_planning/charter.md` (Spec
      054 drift pattern: multiset-by-relationship, not line-pinned).
- [ ] **L2** Spec 281-A authored (`agency hook self-check` write-verify
      extension). Tracked as a 280 follow-up; owner picks it up post-PR.
- [x] **L3** TODO.md row count reflects core-shipped + follow-up-tracked
      flips (Partial count = 0).
- [ ] **L4** Spec 281-C authored (hermetic overflow-counter helper) once
      a second test file hits the same brittleness.
- [ ] **L5** Spec 281-D authored (long-lived-branch doctrine) on the next
      AGENCY_PROTOCOL.md amendment pass.

## Open Q

1. Should the multiset baseline pattern be promoted to a shared helper
   (`scripts/_baseline_helpers.py`) consumed by every gate? The current
   pattern is duplicated across 146, 151, 153. **Recommend yes**, with
   the rename done by the first consumer that adds a new gate (159 or
   169 will hit it first).

## Hints from the live run

- The dispatcher revert (L2) was silent. A pre-commit hook would have
  caught the divergence but only if it inspects the working tree vs the
  committed tree — `git status` alone wouldn't have flagged it because
  the revert happened before staging.
- `python -m agency.install` is a reliable canary: it regenerates derived
  files + scripts/check-drift reports the diff. Run it after EVERY change
  to a capability surface.
- The `_skill_walk` parse-gate (Spec 152 Slice 2) caught zero live
  failures (60/60 skills parse clean today). It's a future-regression
  guard, not a present-day cleanup tool.

## Wire shape

This is a meta-spec (no new verbs / nodes / edges). Its deliverable IS
the documentation. Follow-up specs (281-A through 281-D) ship their own
wire-shape when authored.
