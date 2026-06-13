# Vision-realignment program — master plan (durable record)

> **Why this file exists.** Sessions restart and context is summarized; this is
> the durable, in-repo record of the multi-phase program + the two-agent role
> split, so any session can resume without re-deriving it. Owner directives,
> 2026-06-13.

## The two agents (role split)

| Agent | Branch(es) | Owns |
|---|---|---|
| **Refactor agent** | `claude/agency-error-enum-fixes-13tpnf` (PR #141) | The **Spec 286 OOP refactor** (spine + ports + leaf decomposition + capability-per-folder) **first**, then the Spec 287 planning skill. Exchange channel: `refactor.md`. |
| **Vision owner + Review partner** (this line) | `claude/agency-plugin-vision-review-1fjfv8` (PR #142, Phase A) · `claude/agency-spec-restructure-phaseb-1fjfv8` (PR #143, Phase B) | The **Vision realignment** (docs/specs/tests) + **reviewing every commit** the refactor agent pushes (log: `Review.md`). |

**Current focus (owner directive):** the refactor agent **internalizes the new
Vision docs, then refactors FIRST**; the Vision owner **focuses on reviews** of
that work. Phase B/C *execution* is paused until the refactor settles.

## The Core Vision (the north star)

`docs/vision/CORE.md` §"Four complete pillars": each of **Intent · Capability ·
Lifecycle · Memory** becomes a **complete suite of code + tools** — write *and*
read. The write/act sides are mature; the **read/manage** side is the gap, and
the **Management capability** (Spec 288 — a read-API over all graph nodes) is its
keystone. Goals (`docs/vision/GOALS.md`) are **enduring aspirations, not a status
board**.

## The three phases (each its own PR)

### Phase A — Vision  ·  PR #142  ·  **DONE (in review)**
Realign the vision docs to truth. Shipped:
- `GOALS.md` reframed as aspirations (honest gaps in italics: G5 alias cancelled/069, G6 dogfood loop manual/014 unbuilt, G7 canon-docs exception).
- `docs/architecture/` merged into `docs/vision/reference/` (one layer).
- Four-pillars Core Vision + Management capability added to `CORE.md` + `CAPABILITY-CLUSTERS.md`.
- `Spec 288` (Management capability) drafted.
- `OVERVIEW.md` reframed (dropped frozen counts — rule 8).
- Deleted dead `SPEC-VISION-ALIGNMENT.md` (superseded by the validator).
- **Scoped out (tracked follow-up):** content-accuracy re-stamp of the 7 stale `reference/` docs (pre-existing source drift — a maintenance pass, not vision-truth).

### Phase B — Specs  ·  PR #143  ·  **DESIGNED, execution PAUSED**
Replace the 230-spec / 269-folder corpus with **~29 living specs** (one per
capability + substrate concept), organized **by pillar**, generated-from-code +
one authored `## Why`; `git mv` all historical specs → `Plan/_archive/`
(preserved). Full design: `Plan/_planning/phase-b-spec-restructure.md`.
Execution steps (gated): scaffold+exemplar → archive move → generate → dispatch
4 sonnet subagents (per pillar) → index + guardrails. **Resume after the
refactor settles + owner confirms the target structure.**

### Phase C — Tests  ·  **NOT STARTED**
Cluster the 193 flat `tests/test_*.py` files onto the code architecture (the
four pillars + per-capability), aligning with `tests/conftest.py`
`_AUTO_MARKER_PATTERNS`. Own PR. Plan TBD after Phase B.

## Spec ledger (this program)
- **282** error-severity taxonomy · **283** render substrate · **284** projected-enum · **285** MCP sampling — shipped on #141 (the prior error-enum work).
- **286** OOP refactor (umbrella) — in progress, refactor agent.
- **287** `develop` plan-execute skill — shipped Slice 1 on #141 (CI red on schema-coverage of new `Plan`/`PlanStep` labels — refactor agent's fix).
- **288** sqlmodel-entity-store — built Slice 1 on #141 (refactor agent, user-directed; typed entities derived from the ontology, `table=False`).
- **289** Management capability — drafted (Phase A, renumbered from 288 after the collision with 288-sqlmodel), build deferred (feature work).

**Claimed spec numbers (collision guard):** 282–286 error-enum + refactor · 287 plan-execute skill · 288 sqlmodel-entity-store · 289 management-capability. Claim the next free number here BEFORE creating a Plan/NNN folder on either branch.

## Out of scope / later (coordinated)
- **`/plans` migration** — open specs → graph-backed Plans via Spec 287's planning architecture, rendered under `/plans`, old `Plan/` deleted after. A *later* convergence of Phase B + Spec 287. Flagged to the refactor agent on PR #141. Currently a non-goal.
- **Building the Management capability** (Spec 288) — feature work, after the restructure.

## Resume checklist (for a fresh session)
1. Read this file + `Review.md` (on #141) + `refactor.md` (on #141).
2. Re-arm the commit-watch: `scripts/review-watch.sh` (or the inline Monitor loop) on `claude/agency-error-enum-fixes-13tpnf`.
3. Focus: review the refactor agent's commits; keep CI green; Phase B/C paused until the refactor settles.
