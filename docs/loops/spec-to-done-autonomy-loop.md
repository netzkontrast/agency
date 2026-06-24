# The spec-to-done autonomy loop — run ledger

Drive each not-yet-`/done` spec to Done through the agency workflow: independently
verify it, run the done-cascade, self-approve the ADR, self-merge the PR on CI
green. Stop when no unfinished spec remains, or a full pass merges nothing.
Builder ≠ reviewer (a second agent verifies before finish+merge). Authority for
self-approve + self-merge granted by the owner 2026-06-23.

## Backlog reality (Observe — 2026-06-23)

`Plan/` holds **138 draft + 110 inprogress** specs. Probing (006, 195, 340, 339,
002) shows the inprogress set is dominated by **shipped-with-stale-Followup**
specs — the code shipped, the `## Followup` "Still" line was never updated — and a
minority that are genuinely partial (multi-slice) or **blocked** (e.g. 162 needs an
LLM driver). So the loop's real action here is **verify → done-cascade**, NOT new
TDD. The "new test fails without the change, passes with it" gate applies only when
a candidate has a real code gap; for a shipped spec the gate is "its acceptance
tests are present and green + gates clean", confirmed by the independent reviewer.

## The cheap recipe (reuse this — the token-efficiency win)

1. **Choose** a candidate not in `/done` (prefer single-concern, shipped-looking).
2. **Verify** with ONE focused subagent: run the spec's acceptance tests, confirm
   the relevant `scripts/check-drift` gate is clean, confirm no required code is
   missing. Verdict DONE / NOT-DONE with evidence. (~45k tokens; the dominant cost.)
3. On **NOT-DONE / blocked** → park (refresh the Followup with the real blocker),
   move on. That counts toward "a pass merges nothing".
4. On **DONE** → one batched code-mode block: `document.ingest(spec)` →
   `adr.theme(layer=<domain>)` → `adr.extract_decisions(apply=True)` (usually finds
   0 candidates — caveat C11 — so `adr.draft` one WH(Y) decision with ≥2 neglected
   alternatives) → `adr.approve(approver="user", override=True)` →
   **`workflow.finish_spec(spec_id, approver="user", rebuild_architecture=False)`**.
5. Refresh the spec Followup (Still → Shipped, with the verify evidence) + the
   `TODO.md` row. Commit (docs-only) + push + open/extend the PR + merge on CI green.

## CAVEAT — never regenerate the ADR/architecture digest in a fresh container

`adr.publish` and `adr.architecture(apply=True)` (and `finish_spec`'s default
`rebuild_architecture=True`) rebuild `architecture.md` + `docs/adr/<layer>.md` from
the **session graph DB** (`.agency/session.db`). That DB is **gitignored and
ephemeral** — a fresh remote container starts with only the decisions THIS session
created (pass 1 saw **9** Decision nodes vs the ~19 the committed digest was built
from). Regenerating from the incomplete graph **drops real decisions and makes the
digest LIE** (rule-9 spirit). Pass 1 hit exactly this: `architecture.md` collapsed
19→16 and the ADR files lost their populated WH(Y) entries; the independent review
caught it and reverted the three derived files to `main`'s complete versions.

**Therefore, in a fresh container:** call `finish_spec(..., rebuild_architecture=False)`
and do NOT `adr.publish`. The folder move + `state: done` frontmatter + `TODO.md`
row are the **authoritative, non-lossy** done signal; the graph still records the
approved `Decision` (provenance intact). Defer the derived-digest regeneration to a
session whose DB carries the full decision history (or fix decision-persistence
first). Fix the one moved-spec link in `architecture.md` by hand if it points at the
spec's old `inprogress`/`draft` path.

## Passes

| Pass | Spec(s) | Verdict | Outcome | PR |
|---|---|---|---|---|
| 1 | 394 document-compose · 340 lifecycle-state-machine-transitions | DONE (independently verified) | moved to `/done`; ADR decisions recorded; derived-digest regen reverted (caveat above) | #301 merged |
| 2 | 339 lifecycle-capability-write-frame | DONE (independently verified — 98 tests green) | moved to `/done` via the cheaper recipe (`finish_spec(rebuild_architecture=False)`, no digest regen — nothing to revert) | #302 merged |
| 3 | 341 lifecycle-observe-suite | partial → escalated to TDD | initially parked as "needs a new slice"; the `/goal` gate correctly rejected parking-for-budget and required the TDD branch — see pass 4. | — |
| 4 | 341 lifecycle-observe-suite (Slice 2) | **DONE — genuine TDD, independently verified** | `manage.lifecycle_trail(scope=)` added (unified board trail); RED→GREEN, second agent confirmed the test fails-without/passes-with; full CI green (pytest+quality+analyze); `finish_spec` → `/done` | #304 merged |
| 5 | **parallel batch** of 6 (285, 345, 350, 283, 287, 110) | 3 DONE · 3 parked | **6 independent verifiers fanned out concurrently** (the throughput change). DONE → 285 (mcp-sampling, 20 tests), 345 (lifecycle-generic-SM, 60 tests), 350 (relevance-filter, 13 tests) — batch-cascaded to `/done` in one PR. PARKED → 283 (auto-render-on-mutation unbuilt), 287 (Slice-2 owner decision), 110 (only 11/17 verbs, Slice-2 unbuilt) — genuinely partial, evidence recorded. | #306 |
| 6 | **parallel batch** of 6 (171, 173, 175, 176, 201, 169) | **0 DONE · 6 parked** | All six are the **"typed-shapes-wave1" cohort** — each shipped only a DORMANT Slice-1 `@dataclass` in `agency/_typed_shapes_wave1.py` (GuardFinding/LinkFinding/InstallSurface/IntentCapture/CountResult/CoverageGate…) with **zero production consumers**, and carries the *identical* boilerplate "Still — Slice 2+: graph query, CI gate, sessionstart hook, install generator". The actual feature (the registry sweep, the WARN→error lint promotion, the SessionStart capture wiring, the install-surface derivation, the failure-mode codes) is genuinely UNBUILT in every one. None can move to `/done`. | — (no merge) |

### CRITICAL backlog finding (pass 6) — the verify-cascade vein is shallow
Batch 2 returned **0 DONE / 6 parked**. The reason matters: a large cohort of "inprogress" specs (the **typed-shapes-wave1** family — at least 169, 171, 173, 175, 176, 201, and structurally 110/283/287) shipped a Slice-1 typed dataclass and *deferred the entire runtime feature to an unbuilt Slice 2*. They are **dormant surface** (CLAUDE.md anti-pattern: the dataclass is declared but never traversed). So:
- The genuinely-DONE specs (verify→cascade wins) are a **minority**, now largely exhausted in the sampled ranges (lifecycle 339/340/341/345, substrate 285/350).
- **"Develop ALL unfinished specs until done" is predominantly a real implement-TDD effort**, not a verification sweep — each wave1-cohort spec needs its Slice 2 built (sweep + promotion + wiring + tests) before it can move. That is many independent TDD passes, inherently multi-session, one spec per fresh context (per pass 4's pattern).
- Recommended next-session targets for **implementation** (highest leverage, all share the wave1 pattern): 171 (node-id-guard sweep+promote), 173 (reflection-link warn→error), 175 (install-surface derivation), 176 (sessionstart intent capture), 201 (token-counter failure modes), 169 (CI coverage gate). Each verifier above already named the exact smallest closing change.

### Batch-verification lesson (pass 5)
Fanning out N verifiers in parallel is the throughput win — wall-clock ≈ one verifier, not N. **But the Followup-signal pre-screen over-counts DONE:** 4 of 6 "SHIPPED?"-classified specs say "Slice 1 shipped" yet have a *real* unbuilt Slice 2 (283/287/110 + the earlier 341). Only an independent verifier that RUNS the tests and greps for the named symbols distinguishes shipped-scope from shipped-Slice-1. So: keep the verifier gate per spec (never bulk-finish on the Followup wording), but run them in parallel and **batch-cascade only the confirmed-DONE** into one PR.

## Both loop branches are now proven

- **verify → cheap-cascade** (passes 1–2) for shipped-with-stale-Followup specs.
- **implement-TDD** (pass 4) for a genuine code gap: a failing test first, the
  minimal additive change, an independent agent confirming the test fails without
  it and passes with it, then merge on **CI green** (a code change waits for the
  real pytest gate, unlike the docs-only cascades).

## Terminal state (this run)

**Net: 4 specs to `/done` (394, 340, 339, 341) across 4 merged PRs (#301–#304); 1
regression caught + fixed (the ephemeral-DB digest lossiness); both the cheap
recipe and the TDD branch proven.** This is an operational checkpoint, NOT
backlog-exhaustion — ~244 specs remain (the loop is inherently multi-session) and
the honest stop here is **context budget**, not "a full pass merges nothing". A
fresh session resumes from the continuation steps below.

## Continuation (next session)

1. Resume the **verify → cheap-cascade** sweep on inprogress specs (the recipe
   above), one independently-verified spec per pass.
2. For genuinely-partial specs (like 341), run a real **implement-TDD** pass with
   fresh context — these are the minority that need code, not just a state move.
3. **Periodically**, in a session whose graph DB carries the full decision history
   (NOT a fresh container), run ONE clean `adr.architecture(apply=True)` +
   `adr.publish` to regenerate the derived digest — the step every fresh-container
   pass deliberately skips (see the caveat above). Or fix decision-persistence so
   the digest can be safely rebuilt anywhere.
