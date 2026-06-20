---
spec_id: "353"
slug: brooks-lint-port
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 4, 6]
depends_on: ["042", "016", "080", "081", "047", "334", "336", "349", "292"]
domain: analyze
wave: program-master
---

# Spec 353 — Brooks-lint port (judgment-based code-quality lens, native + develop-integrated)

> Owner directive: *"Port the Brooks-Lint into Agency — improve and integrate
> linting into the `develop` capability (replace the Shell Script) and use
> everything from the Brooks-Lint system."*
>
> Owner forks decided (brainstorm, 2026-06-20): **replace = brooks-lint itself**
> (the external shell/JS/markdown plugin — port it native, retire the external
> dependency) · **home = extend `analyze` + a `develop` seam** · **engine =
> hybrid** (decidable AST scanners tagged with risk codes + skill-walked judgment
> for the reasoning-heavy risks) · **decomposition = this umbrella + 5 seam
> specs**.

## Why

[brooks-lint](https://github.com/netzkontrast/brooks-lint) is a Claude Code
**plugin** for code-quality diagnosis grounded in twelve classic software-
engineering books. It is implemented as a **shell/JS/markdown** system: a
`hooks/session-start` bash banner, six markdown skills under `skills/`, a
`_shared/` framework (the Iron Law + decay-risk reference), and `scripts/*.mjs`
plumbing (report-parse → SARIF, eval runner, parser-fidelity benchmark). "Replace
the Shell Script" = retire that external plugin and make its whole system a
**native agency capability surface** so an agent reaches for `develop.review`,
not a second plugin.

Agency already owns a code-quality surface — `analyze` (Spec 042) — but it is the
**complementary half**: decidable, mechanical, decided-by-rule. The port adds the
**judgment half** brooks contributes, and the two compose.

### What brooks-lint ships, and where each piece lands

| brooks-lint surface | Agency today | This program |
|---|---|---|
| Iron Law: `Symptom → Source → Consequence → Remedy` | ❌ (`Finding` = rule/severity/file/line/message/evidence) | **Spec 354** — extend the `Finding` value object |
| 12 decay risks: R1–R6 (code) · T1–T6 (test) | ⚠️ partial overlap (long-fn, import-cycle, dup detected — untagged) | **Spec 354** — decay-risk knowledge as data + decidable→risk-code tagging |
| 6 modes: review · audit · debt · test · health · sweep | ❌ | **Spec 355** — six walkable skills + `develop.review` seam |
| `--fix` remedy mode (auto-apply safe, confirm risky) | ❌ | **Spec 355** — remedy phase behind a gate |
| Health Score (base 100; strict/balanced/legacy-friendly presets) | ❌ | **Spec 356** — computed score + presets |
| `.brooks-lint.yaml` config (disable/severity/ignore/focus/strictness/suppress/custom_risks) | ⚠️ unified `config` (Spec 334) exists | **Spec 356** — map onto agency config |
| history `.brooks-lint-history.json` + trend | ❌ (graph + `manage.timeline`) | **Spec 356** — runs as graph nodes; trend is a query |
| triage (accept/dismiss/defer/skip) + suppress w/ expiry | ❌ | **Spec 356** — graph-recorded suppressions |
| SARIF output (`sarif.mjs`) | ❌ | **Spec 357** — `analyze.sarif` emit |
| report-parse (`report-parse.mjs`) | n/a — findings already structured | **Spec 357** — *dropped* (port-forward: no prose to parse) |
| CI GitHub Action + ci-gate | ⚠️ `.github/workflows/test.yml` + `gate` cap | **Spec 357** — review-on-diff CI step + score gate |
| 12-book source-coverage discipline | ❌ | **Spec 358** — source-coverage data + cite-discipline |
| eval suite (57 scenarios) + parser benchmark (frozen 30 reports) | ❌ (Gherkin acceptance, Spec 053/077) | **Spec 358** — translate to Gherkin + SARIF property tests |

The inventory is exhaustive — **every** brooks-lint surface has a destination, so
"use everything from the Brooks-Lint system" is satisfied, not approximated.

### The one insight that makes this a port, not a copy

brooks-lint and `analyze` are **two lenses on the same finding**, and agency
already mechanically detects the decidable half of several decay risks:

| Decay risk | Already decidable in `analyze` | Judgment-only (skill-walked) |
|---|---|---|
| R1 Cognitive Overload | long function / long params / nesting (`_quality.py`) | naming clarity, shallow modules |
| R3 Knowledge Duplication | partial (token dup) | "same *decision* in 2 places" |
| R4 Accidental Complexity | file/LOC thresholds (`_architecture.py`) | speculative generality, middle-men |
| R5 Dependency Disorder | **import cycles, fan-out** (`_architecture.py`) | conceptual integrity, ISP intent |
| R6 Domain Model Distortion | — | anemic model, ubiquitous-language drift |

So the hybrid engine (owner Q3) is not a compromise — it is the **correct
factoring**: the decidable subset is auto-detected by extending `analyze`'s AST
scanners and **tagged with the risk code + book source** (Spec 354); the
reasoning-heavy risks run as **skill-walked judgment** producing Iron Law
findings (Spec 355). Both record as `Finding` graph nodes (Goal 2).

## Design

### 1. Three lenses, one substrate (cluster coherence — Spec 047)

The repo will carry **three** code-review lenses. The boundary must be explicit
or they collide (the same hazard Spec 348 §1 resolved for `frugal` vs `analyze`):

| Lens | Capability | Asks | Output vocabulary |
|---|---|---|---|
| **analyze** (Spec 042) | `analyze.*` | "Is this *decidably* wrong?" (lint/security/perf/arch by rule) | `Finding{rule, severity}` |
| **frugal** (Spec 348) | `frugal.review` | "Is this *over-engineered*?" (YAGNI/stdlib/delete) | `FrugalFinding` |
| **brooks** (this program) | `develop.review` → `analyze.*` modes | "Will this *decay*?" (maintainability, grounded in 12 books) | `Finding{risk_code, source, consequence, remedy}` |

**No overlap by construction:** brooks does not re-detect what `analyze` already
decides — it **consumes** those findings (tagging them with risk codes) and adds
the judgment layer on top. `frugal` stays orthogonal (over-engineering ≠ decay;
a YAGNI abstraction is R4-adjacent but `frugal` owns the delete-it verdict while
brooks owns the "why it will hurt, per Ousterhout" diagnosis). The umbrella
registers the brooks lens in `Plan/047-cluster-integration/spec.md` under the
quality/review cluster at implementation time.

### 2. Home: extend `analyze`, seam through `develop` (owner Q2)

- **The engine extends `analyze/`** — the `Finding` shape (354), the decidable
  risk-code scanners (354), score/config/triage/history (356), SARIF (357). This
  honors the drop-in-capability bar: the port is mostly *adding files under an
  existing folder* (`analyze/data/`, `analyze/_decay.py`, `analyze/_score.py`,
  `analyze/_sarif.py`), not a new top-level capability.
- **The developer-facing entry is `develop.review`** — "integrate linting INTO
  `develop`". `develop` already owns walkable disciplines + `skill_walk`; the six
  modes are walkable skills it drives (355). `develop.review(mode, scope)`
  dispatches the mode skill, which calls `analyze.*`. The verb-routing table
  (CLAUDE.md) gains a "review code for decay → `develop.review`" row.

> **Tension resolved (analyze-vs-develop split):** the *heavy machinery* lives in
> `analyze` (where the `Finding` model and scanners already are — no second copy);
> the *discipline* lives in `develop` (where walkable skills + the dev loop
> already are). This is the same factoring as `develop.test` → `analyze`/pytest:
> develop is the seam, analyze is the engine. Neither capability grows a
> redundant half.

### 3. The hybrid engine (owner Q3) — decidable feeds judgment

Each mode skill (355) walks the same shape, one phase at a time (bounded context):

1. **Scope** — auto-detect (git diff → staged → branch → ask), per brooks'
   `common.md` Auto-Scope rules.
2. **Decidable pass** — call `analyze.quality/security/performance/architecture`;
   every returned `Finding` is tagged with the risk code it evidences (354).
3. **Judgment pass** — the agent reads the decay-risk data (354) for the
   reasoning-heavy risks (R3/R6, T-risks, the non-decidable parts of R1/R4/R5)
   and emits Iron Law `Finding`s, citing a book only when the symptom matches
   (the source-coverage cite-discipline, 358).
4. **Score + report** — Health Score computed from findings × preset (356);
   render the Iron Law report (357).
5. **Remedy/triage** (optional, gated) — `--fix` applies safe remedies, confirms
   risky ones; triage records suppressions (356).

### 4. Provenance upside (Goal 2 — where the substrate wins)

In brooks every run is ephemeral terminal output parsed back from prose by
`report-parse.mjs`. In agency every finding is **born structured** as a `Finding`
graph node SERVING the intent, so:

- "what decayed" / "what did we suppress" / "is the score trending down" are
  **graph queries** (`analyze.graph`, `manage.timeline`), not re-runs or
  re-greps. The history file + the report parser both **disappear** — they were
  artifacts of a markdown-only design.
- Findings are captured **in full** (CLAUDE.md #9 / Spec 336) — never truncated
  to a budget; the wire return is token-bounded with a locator (the Spec 348-S3
  pattern), the graph keeps everything.

### 5. Single-source the knowledge (rule 2 / derivability)

- The 12 decay-risk definitions + the 12-book source matrix are **vendored as
  data** (`analyze/data/decay-risks.json`, `analyze/data/source-coverage.json`),
  cited to brooks-lint as upstream — the precedent is the Dramatica ontology
  vendored in Spec 101. The skills and scanners READ that data; no risk
  definition is duplicated in prose-in-code.
- The six mode skills **derive** their SkillDoc from the module docstring
  (Spec 080 pattern), not hand-authored metadata.
- The risk-code → book-source mapping is one table (354), read by both the
  decidable tagger and the judgment skills.

### Child spec map + build order

```
353 (this umbrella)
 └─ 354  decay-risk Finding shape + knowledge data   ← FOUNDATION (no dep)
     ├─ 355  six modes as skills + develop.review     ← needs 354
     ├─ 356  Health Score + config + triage + history ← needs 354
     ├─ 357  SARIF + CI + quality gate                ← needs 354 (+356 score)
     └─ 358  acceptance + source-coverage + evals      ← needs 354,355
```

354 ships first (everything depends on the extended `Finding` + the data). 355
and 356 are parallelizable on top of 354. 357 needs the score from 356. 358
(tests/docs) lands last, validating the rest.

### What this program does NOT do

- **No second plugin / no second MCP server** — the agency MCP wire + the
  extended `analyze`/`develop` verbs ARE the port (Spec 348 §4 precedent).
- **No new top-level capability** unless 354 review finds the `analyze` extension
  genuinely incoherent — default is extend, not add.
- **No frozen scores / pinned counts** (rule 8) — Health Score is computed; preset
  weights are documented tunable budgets; tests assert invariants.
- **No LLM-judge-only path** — judgment is *skill-walked* (the agent reasons with
  the data), not a hidden model call that emits findings opaquely (owner Q3).
- **No deletion of the brooks-lint repo** — it stays the cited upstream reference
  the data is vendored from (like ponytail for `frugal`, Spec 348).
- **No VS Code / non-Claude-surface work** — out of scope (brooks-lint's own
  CLAUDE.md says the same).

## Acceptance (Gherkin) — program-level

```gherkin
Scenario: the brooks lens auto-discovers through develop
  When I call agency_welcome
  Then "review" appears among develop's verbs
  And develop.review lists the six modes (review/audit/debt/test/health/sweep)

Scenario: decidable feeds judgment on one finding
  Given a 60-line function with mixed abstraction levels
  When I run develop.review(scope="diff")
  Then a Finding is recorded tagged risk_code "R1"
  And it carries a book Source, a Consequence, and a Remedy (the Iron Law)
  And the Finding is a graph node SERVING the current intent

Scenario: the three lenses stay distinct
  Then analyze.quality findings carry no risk_code unless brooks tags them
  And frugal.review findings stay FrugalFinding (over-engineering, not decay)
  And develop.review findings carry the Iron Law fields

Scenario: every brooks-lint surface has a live destination
  Then each row of the §"What brooks-lint ships" table maps to a shipped child slice
  And no surface is "approximated" — report-parse is intentionally dropped (findings born structured)
```

## Open questions

- **OQ1 — config file name.** Keep `.brooks-lint.yaml` for drop-in compat, or
  fold entirely into `.agency/config.yaml` under a `quality:` block? (356 default:
  honor both, agency config canonical.)
- **OQ2 — mode skill home.** Mode skills authored on `develop.ontology.skills`
  vs `analyze.ontology.skills`? (Default: `develop`, since `develop` drives the
  walk; analyze stays the engine.)
- **OQ3 — `develop.review` vs `analyze.review`.** Single seam verb on develop, or
  also expose `analyze.review` for headless/CI? (357 default: both — develop for
  humans, analyze for CI; one implementation.)

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — design record, no code yet. Opened by the owner's "port
brooks-lint into agency, integrate linting into develop, use everything"
directive; codegraph-grounded familiarization of both repos (agency 364 files /
7,829 nodes; brooks-lint 22 files / 292 nodes) established the analyze-vs-brooks
lens factoring. Brainstorm forks decided (replace=brooks-itself · home=extend-
analyze+develop-seam · engine=hybrid · 5+1 specs). Children 354–358 drafted in
the same commit. Next: spec-panel pass on the program, then 354 (foundation) TDD.
