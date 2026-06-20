---
spec_id: "355"
slug: quality-modes-develop-seam
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 3, 6]
depends_on: ["353", "354", "081", "080", "018", "046"]
domain: develop
wave: brooks-port
parent_spec: "353"
---

# Spec 355 — Six quality modes as walkable skills + the `develop.review` seam

> Part of the Spec 353 brooks-lint port. This slice is the **"integrate linting
> into `develop`"** half of the directive: the six brooks modes become walkable
> agency skills (Lifecycle templates), and `develop.review` is the
> developer-facing seam that drives them — so an agent reaches for a verb, not the
> external shell-script plugin.

## Why

brooks-lint ships six modes as six markdown skills (`skills/brooks-{review,audit,
debt,test,health,sweep}/`), each a `SKILL.md` + a numbered `{mode}-guide.md`,
loaded via the Skill tool and reading `_shared/` on demand. In agency, **a
walkable skill IS a Lifecycle template** (CORE.md:47-62) — the engine's
`develop.skill_walk` delivers ONE phase at a time so context stays bounded
(Spec 018/081). That is a strictly better home for a multi-step diagnostic
discipline than a flat markdown file the agent reads all at once.

The modes also need an **entry point inside `develop`** — the directive is
explicit ("integrate linting INTO the `develop` capability"). `develop` already
owns the dev loop (`brainstorm`/`write_spec`/`implement`/`test`/`skill_walk`) but
has **no review verb** today (codegraph: develop's only "lint" is
`plugin.lint_capability`, which lints capability *shape*, not code decay). So
`develop.review` is a genuine addition, and it is where the brooks lens plugs into
the existing TDD/implement disciplines.

## Design

### 1. The six modes as walkable skills

Each mode is a walkable discipline on `develop.ontology.skills` (owner OQ2
default), authored to walk the **hybrid shape** from Spec 353 §3. The SkillDoc
derives from the discipline docstring (Spec 080 — no hand-authored metadata).

| Skill (agency) | brooks origin | Scope default | Distinctive phase |
|---|---|---|---|
| `quality-review` | brooks-review (PR review) | working-tree diff | quick test-check (T-risks on co-located tests) |
| `quality-audit` | brooks-audit (architecture) | whole repo | **Module Dependency Graph** (mermaid, R5) |
| `quality-debt` | brooks-debt (tech debt) | whole repo | prioritized refactoring **roadmap** |
| `quality-test` | brooks-test (test quality) | all test files | T1–T6 against co-located production |
| `quality-health` | brooks-health (dashboard) | whole repo | **all dimensions** in one score |
| `quality-sweep` | brooks-sweep (full + fix) | whole repo | **remedy phase** (auto-apply safe, confirm risky) |

Naming uses the `quality-*` prefix (the agency lens name from Spec 353 §1), not
`brooks-*` — the discipline is agency-native; brooks is the cited upstream. (The
short-form `/brooks-review` etc. can be aliased for muscle-memory compat, like
Spec 348 kept `audit` as a `review(scope="repo")` alias.)

### 2. The walk shape (one phase at a time)

Every mode skill walks the Spec 353 §3 phases, with mode-specific bodies:

1. **scope** — auto-detect per brooks `common.md`: PR review →
   `git diff --cached` → `git diff` → `git diff main...HEAD` → ask; audit/debt →
   whole repo or `--since=<ref>` incremental; test → test files; always emit a
   `Scope:` line. (Reuses `develop._detect_mode`'s git seam, codegraph:
   develop/_main.py:1304.)
2. **decidable** — call `analyze.quality/security/performance/architecture`; tag
   findings with risk codes (Spec 354 `_decay.py`).
3. **judgment** — read `decay-risks.json` (354) for the reasoning-heavy risks;
   emit Iron Law `Finding`s; **HARD GATE**: a finding without Consequence +
   Remedy is rejected (the Iron Law, enforced — `gate.check`).
4. **score+report** — Health Score (356) + render the Iron Law report (357).
5. **remedy/triage** (sweep + `--fix` only) — §3 below; the triage step calls
   `intent.triage` (Spec 356 §4 — triage is an intent judgment), interactive only.

The engine records a `SkillRun` (Spec 018/346) over the walk, so "which review,
when, what did it find" is provenance, and the walk is resumable.

Each phase's **guidance prose** (the brooks `{mode}-guide.md` steps) is rendered
from a `develop/templates/quality-{mode}.md` template (Spec 359), not inlined in
the skill docstring — so the engine still delivers one phase at a time, but the
diagnostic voice lives in a lint-enforced template (`<!-- AGENT: -->`, Spec 060).
The judgment-pass how-to (`decay-risks`, `source-coverage`) is fetched on demand
via `develop.reference(...)` (Spec 359).

### 3. The `develop.review` seam (the entry verb)

`agency/capabilities/develop/_main.py` gains:

```python
@verb(role="transform")
def review(self, mode: str = "review", scope: str = "", fix: bool = False) -> dict:
    """Walk a code-quality mode (review/audit/debt/test/health/sweep) over a
    scope, producing Iron Law findings as graph artefacts.

    Inputs: mode (str — one of the six), scope (str — '' = auto-detect;
            'diff'/'repo'/path), fix (bool — apply the remedy phase).
    Returns: {findings: [...], score, report_ref, skill_run_id} (token-bounded;
             full findings live in the graph — Spec 348-S3 pattern).
    chain_next: develop.review(mode='sweep', fix=True) to remediate; or
                analyze.sarif(...) for CI upload (Spec 357).
    """
```

`review` resolves the mode → the walkable skill and drives `skill_walk` (it is the
thin dispatcher; the heavy lifting is the skill + `analyze.*`). It is the
"linting integrated into develop". A headless twin `analyze.review(...)` (owner
OQ3) shares the implementation for CI (357) — develop for humans, analyze for
machines, one engine.

**Cross-link into the existing dev loop** (the "wire it into develop" intent):

- The `tdd` / `implement` disciplines (Spec 041/018) gain an optional **review
  phase** before their commit gate — `develop.review(scope="diff")` on the
  working tree, so decay is caught at implement time, not after.
- The verb-routing table (CLAUDE.md "How to use the agency MCP") gains:
  `| Review code for decay/maintainability | develop.review(mode, scope) | (the brooks-lint plugin) |`.
- `develop.reference("brooks")` / `("decay-risks")` surfaces the heavy how-to on
  demand (the T3 disclosure pattern, like `develop.reference("codegraph")`).

### 4. Remedy mode (`--fix`) — the sweep behaviour, gated

brooks-sweep auto-applies safe fixes and confirms risky ones. Ported as the
**remedy phase** (phase 5), behind a `gate`:

- Each `Finding`'s `remedy` (Spec 354) is classified safe vs risky (safe =
  mechanical + local, e.g. extract-constant, rename-in-file; risky = structural,
  e.g. move-class, invert-dependency).
- Safe remedies auto-apply (recorded as an `Artefact` PRODUCES edge); risky ones
  pause the lifecycle `input-required` via `gate.check(passed=False)` and surface
  a confirm prompt (Hint #8 — resume with `confirmed=True`).
- The `remedy-guide.md` discipline (brooks `_shared/remedy-guide.md`) is read on
  demand before writing fixes (vendored as `develop.reference("remedy")`).

> **Tension resolved — `--fix` mutates, so it cannot be a `transform`.** The
> remedy phase is `role="effect"` (it writes files); the diagnosis phases stay
> `transform` (read-only). `develop.review(fix=True)` routes through the effect
> path so the provenance moat tags it correctly (the analyze findings stay a
> pure transform; only the remedy step mutates).

### What this slice does NOT do

- No score math (356) — phase 4 *calls* it.
- No SARIF / CI (357).
- No new decidable detectors — judgment reads 354's data; decidable is 354's
  bridge.
- No auto-fix of risky changes without confirmation (the gate is mandatory).
- No removal of `analyze`'s standalone axes — they remain callable directly;
  `develop.review` *composes* them.

## Acceptance (Gherkin)

```gherkin
Scenario: develop.review walks the PR-review mode on the diff
  Given staged changes with a 60-line mixed-abstraction function
  When I call develop.review(mode="review")
  Then the Scope line reports "staged changes"
  And an R1 Iron Law Finding is recorded as a graph node
  And a SkillRun provenance node records the walk

Scenario: the Iron Law is enforced at the judgment gate
  Given a judgment finding drafted without a Remedy
  When the judgment phase gate runs
  Then the finding is rejected (no fix before complete diagnosis)

Scenario: audit mode emits a module dependency graph
  When I call develop.review(mode="audit")
  Then the report contains a mermaid Module Dependency Graph
  And R5 dependency-disorder findings cite Clean Architecture

Scenario: sweep --fix applies safe remedies and gates risky ones
  Given findings with one safe (extract-constant) and one risky (invert-dependency) remedy
  When I call develop.review(mode="sweep", fix=True)
  Then the safe remedy is applied and recorded as a PRODUCES artefact
  And the risky remedy pauses the lifecycle input-required for confirmation

Scenario: the six modes are discoverable and walkable
  When I search the live skill registry
  Then quality-review/audit/debt/test/health/sweep are all walkable disciplines
  And each derives its SkillDoc from its docstring (no hand-authored metadata)

Scenario: review integrates into the implement loop
  Given the implement discipline's review phase is enabled
  When implement reaches its pre-commit gate
  Then develop.review(scope="diff") has run and its findings are attached to the intent
```

## Open questions

- **OQ1** — short-form aliases (`/brooks-review`): ship for compat, or
  agency-native names only? (Default: alias for muscle memory, native canonical.)
- **OQ2** — should `quality-health` (all-dimensions) *compose* the other five
  skills, or run its own combined walk? (Default: compose — single source, the
  brooks-health "one pass over four dimensions" maps to five sub-walks.)

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — the develop-integration slice of the Spec 353 program.
No code yet. Grounded in codegraph: `develop` verb surface (no review verb today),
`_detect_mode` git seam (develop/_main.py:1304), `skill_walk` (1097), the
`SkillRun` provenance path (Spec 018/346). Depends on 354 (the tagged `Finding` +
decay data). Next (after 354 GREEN): the six walkable disciplines + `develop.review`
dispatcher + the implement/tdd cross-link, RED→GREEN per phase.
