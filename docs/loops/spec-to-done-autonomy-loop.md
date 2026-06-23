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
| 3 | 341 lifecycle-observe-suite | **PARKED — genuinely partial** | Slice 2 (`lifecycle-board.md` convergence Document) is real remaining implementation, not a stale Followup; 342 + 343 already in `/done`. A new implement-TDD effort, deferred to a fresh-context session. | — (no merge) |

## Terminal state (this run)

Pass 3 **merged nothing** — the next genuine lifecycle candidate (341) needs a real
new slice, so it was parked rather than force-shipped in a deep-context session.
Per the stop rule ("a full pass merges nothing"), the run reaches its checkpoint
terminal here. **Net: 3 specs driven to `/done` (394, 340, 339) across 2 merged PRs
(#301, #302); 1 regression caught + fixed (the ephemeral-DB digest lossiness); the
cheap recipe proven.** ~245 specs remain — inherently multi-session.

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
