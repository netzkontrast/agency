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
   emit Iron Law `Finding`s, **enriching the matching decidable finding in place**
   per the merge contract (§3b). **HARD GATE with a DECIDABLE predicate** (Wiegers
   fix): the gate is not "the agent says it's done" — it is the pure function
   `gate.check(passed = all(f.consequence and f.remedy for f in findings))` over
   the structured `Finding` fields (354 makes them structured precisely so this is
   machine-checkable). A finding with an empty `consequence` or `remedy` fails the
   gate → it cannot be reported. Testable, not aspirational.
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

### 3. Two verbs, not one — `develop.review` (diagnose) + `develop.remediate` (fix)

> **Spec-panel fix (Fowler, 2026-06-20).** `@verb(role=…)` is fixed at decoration
> time (codegraph: `capability.py:424`) — a verb is `transform` OR `effect`, never
> both depending on a `fix` bool. The original single `review(fix=…)` was not
> implementable AND violated SRP (diagnosis + mutation in one verb, two roles).
> Split into two verbs; `quality-sweep` composes them.

`agency/capabilities/develop/_main.py` gains:

```python
@verb(role="transform")
def review(self, mode: str = "review", scope: str = "") -> dict:
    """Walk a code-quality mode (review/audit/debt/test/health) over a scope,
    producing Iron Law findings as graph artefacts. READ-ONLY (diagnosis).

    Inputs: mode (str — one of the diagnostic five), scope (str — '' = auto-detect;
            'diff'/'repo'/path).
    Returns: {review_id, findings:[...], score, report_ref, skill_run_id}
             (token-bounded; full findings live in the graph — Spec 348-S3).
    chain_next: develop.remediate(review_id) to fix; analyze.sarif(review_id) for CI.
    """

@verb(role="effect")
def remediate(self, review_id: str, apply_safe: bool = True) -> dict:
    """Apply the remedy phase for a prior review — the brooks-sweep behaviour.
    MUTATES (writes files) → role=effect, so the provenance moat tags it right.

    Inputs: review_id (from develop.review), apply_safe (auto-apply safe remedies).
    Returns: {applied:[...], gated:[...], skill_run_id}.
    chain_next: confirm a gated risky remedy (resume input-required), or commit.
    """
```

`review` resolves the mode → the walkable skill and drives `skill_walk` (it is the
thin dispatcher; the heavy lifting is the skill + `analyze.*`). `quality-sweep`
runs `review` then `remediate`. Both delegate to a shared **`analyze/_review.py`
core** (§3a) so there is one engine, two front doors.

#### 3a. The headless twin — `analyze.review` (resolves OQ3 + the CI use case)

> **Spec-panel fix (Cockburn + Hightower, 2026-06-20).** The interactive developer
> and the CI system are **two actors with different success guarantees** — the CI
> actor must NEVER block on input. That maps onto agency's twin-capability shape,
> not a bool flag:

| Verb | Home | Actor | Guarantee |
|---|---|---|---|
| `develop.review` / `develop.remediate` | `lifecycle` | human | interactive — walks the skill, may pause for triage/confirm |
| `analyze.review` | `capability` | CI / headless | **never pauses**; auto-declines risky remedies; exits with a status |

Both call `analyze/_review.py` (the shared core: scope → decidable → judgment →
score). "One implementation, two front doors" — `develop.*` adds the walk +
interactive triage/confirm; `analyze.review` is the non-interactive engine entry
CI uses (Spec 357). This dissolves OQ3.

#### 3b. The decidable→judgment merge contract (resolves Hohpe)

> **Spec-panel fix (Hohpe, 2026-06-20).** When the decidable pass tags a
> `long_function` as R1 AND the judgment pass also reasons about R1 on the same
> code, the result must be ONE finding, not two. The join key is
> **`(risk_code, file, line-range-overlap)`**. Rule: the judgment pass **enriches
> an existing decidable finding in place** (filling `consequence`/`remedy`/sharper
> `source`); it **creates** a new `Finding` only where no decidable finding covers
> that `(risk_code, span)`. So the report never double-counts and the score (356)
> sums distinct findings.

#### 3c. Language matrix (resolves Crispin — stated, not silent)

> **Spec-panel fix (Crispin, 2026-06-20).** `analyze`'s decidable scanners are
> Python-only today (codegraph: every axis early-returns for non-`py`). The
> judgment pass is language-agnostic (it reasons over any diff). So v1 is:
> **decidable tagging = Python; judgment = any language.** A TypeScript PR still
> gets brooks judgment findings — only the *mechanical* pre-tagging is py-first.
> This is a documented v1 limitation with an evolution path (add a language's
> decidable scanners → its findings auto-tag), NOT a silent regression. The report
> states the active language coverage in its Scope line.

**Cross-link into the existing dev loop** (the "wire it into develop" intent):

- The `tdd` / `implement` disciplines (Spec 041/018) gain an optional **review
  phase** before their commit gate — `develop.review(scope="diff")` on the
  working tree, so decay is caught at implement time, not after.
- The `tdd`/`implement` review phase calls `develop.review(scope="diff")`
  (read-only) — never `remediate` (no surprise mutation in the dev loop).
- The verb-routing table (CLAUDE.md "How to use the agency MCP") gains:
  `| Review code for decay/maintainability | develop.review(mode, scope) | (the brooks-lint plugin) |`
  and `| Fix reviewed decay | develop.remediate(review_id) | — |`.
- `develop.reference("brooks")` / `("decay-risks")` surfaces the heavy how-to on
  demand (the T3 disclosure pattern, like `develop.reference("codegraph")`).

### 4. Remedy — `develop.remediate`, the sweep behaviour, gated

brooks-sweep auto-applies safe fixes and confirms risky ones. Ported as the
`develop.remediate` verb (§3, `role="effect"`), behind a `gate`:

- Each `Finding`'s `remedy` (Spec 354) is classified safe vs risky (safe =
  mechanical + local, e.g. extract-constant, rename-in-file; risky = structural,
  e.g. move-class, invert-dependency).
- Safe remedies auto-apply (recorded as an `Artefact` PRODUCES edge); risky ones
  pause the lifecycle `input-required` via `gate.check(passed=False)` and surface
  a confirm prompt (Hint #8 — resume with `confirmed=True`).
- **Headless guard (Cockburn):** under the `analyze.review` / CI actor (§3a) there
  is no one to confirm — risky remedies are **auto-declined** (diagnosis-only,
  reported as `gated`), never paused. The interactive `develop.remediate` path
  pauses; the headless path skips. One classifier, two terminal behaviours.
- The `remedy-guide.md` discipline (brooks `_shared/remedy-guide.md`) is read on
  demand before writing fixes (vendored as `develop.reference("remedy")`, Spec 359).

> **Tension resolved — diagnosis and mutation are different verbs, not one verb
> with a bool.** `develop.review` is `role="transform"` (read-only, produces
> findings); `develop.remediate` is `role="effect"` (writes files). The provenance
> moat tags each correctly because the role is static per verb (the Fowler fix,
> §3). `quality-sweep` composes review→remediate; it is not a third role.

### What this slice does NOT do

- No score math (356) — phase 4 *calls* it.
- No SARIF / CI (357) — but the `analyze.review` headless core (§3a) is what 357
  calls; this slice defines it, 357 wires it.
- No new decidable detectors — judgment reads 354's data; decidable is 354's
  bridge.
- No auto-fix of risky changes without confirmation (the gate is mandatory;
  headless auto-declines rather than confirming).
- No `review(fix=…)` bool (the Fowler fix — split into `review`/`remediate`).
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

Scenario: the Iron Law gate is a decidable predicate
  Given a judgment finding drafted with an empty remedy
  When the gate runs gate.check(passed=all(f.consequence and f.remedy ...))
  Then passed is False and the finding cannot be reported
  And the check is a pure function over Finding fields (no agent self-assertion)

Scenario: decidable and judgment passes merge, not double-count
  Given analyze tags a long function as a decidable R1 finding
  When the judgment pass also reasons about R1 on the same line range
  Then there is ONE R1 finding (judgment enriched the decidable one in place)
  And the score counts it once

Scenario: develop.review is read-only; develop.remediate mutates
  Then develop.review is role="transform" and writes no files
  And develop.remediate is role="effect" and applies the remedy phase
  And there is no review(fix=...) bool

Scenario: the headless twin never blocks (the CI actor)
  Given a risky (invert-dependency) remedy under analyze.review
  When the headless review runs
  Then the risky remedy is auto-declined and reported as gated (no pause)
  When the same finding is remediated via develop.remediate interactively
  Then it pauses input-required for confirmation

Scenario: audit mode emits a module dependency graph
  When I call develop.review(mode="audit")
  Then the report contains a mermaid Module Dependency Graph
  And R5 dependency-disorder findings cite Clean Architecture

Scenario: sweep composes review then remediate
  Given findings with one safe (extract-constant) and one risky (invert-dependency) remedy
  When I walk quality-sweep interactively
  Then develop.review runs first, then develop.remediate
  And the safe remedy is applied and recorded as a PRODUCES artefact
  And the risky remedy pauses the lifecycle input-required for confirmation

Scenario: judgment reviews a non-Python diff (language matrix)
  Given a TypeScript diff (no decidable scanner for it in v1)
  When I call develop.review(mode="review")
  Then judgment-pass Iron Law findings are still produced
  And the Scope line states decidable coverage = none for this language

Scenario: the six modes are discoverable and walkable
  When I search the live skill registry
  Then quality-review/audit/debt/test/health/sweep are all walkable disciplines
  And each derives its SkillDoc from its docstring (no hand-authored metadata)

Scenario: review integrates into the implement loop
  Given the implement discipline's review phase is enabled
  When implement reaches its pre-commit gate
  Then develop.review(scope="diff") has run (read-only) and its findings are attached to the intent
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
decay data).

**Amended 2026-06-20 (spec-panel critique, 5 fixes folded):** (Fowler) split the
single `review(fix=…)` into `develop.review` (transform) + `develop.remediate`
(effect) — the role tag is static, so one verb could not be both (§3, §4).
(Cockburn+Hightower) the headless/CI actor is a first-class twin `analyze.review`
(home=capability, never pauses, auto-declines risky remedies) sharing the
`analyze/_review.py` core with the interactive `develop.*` verbs — resolves OQ3
(§3a). (Hohpe) the decidable→judgment **merge contract** (join key
`(risk_code, file, span)`; judgment enriches in place, creates only where none) —
no double-count (§3b). (Wiegers) the Iron Law gate is a **decidable predicate**
`all(f.consequence and f.remedy …)`, not agent self-assertion (§2 phase 3).
(Crispin) the **language matrix** is stated: decidable=py v1, judgment=any-language
(§3c). Next (after 354 GREEN): the six walkable disciplines + `develop.review`/
`remediate` + the shared `_review.py` core + the implement/tdd cross-link,
RED→GREEN per phase.
