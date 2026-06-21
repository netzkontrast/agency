---
spec_id: "379"
slug: brooks-lint-port
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 4, 6]
depends_on: ["042", "016", "080", "081", "047", "334", "336", "349", "292"]
domain: analyze
wave: program-master
---

# Spec 379 — Brooks-lint port (judgment-based code-quality lens, native + develop-integrated)

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
| Iron Law: `Symptom → Source → Consequence → Remedy` | ❌ (`Finding` = rule/severity/file/line/message/evidence) | **Spec 360** — extend the `Finding` value object |
| 12 decay risks: R1–R6 (code) · T1–T6 (test) | ⚠️ partial overlap (long-fn, import-cycle, dup detected — untagged) | **Spec 360** — decay-risk knowledge as data + decidable→risk-code tagging |
| 6 modes: review · audit · debt · test · health · sweep | ❌ | **Spec 380** — six walkable skills + `develop.review` seam |
| `--fix` remedy mode (auto-apply safe, confirm risky) | ❌ | **Spec 380** — remedy phase behind a gate |
| Health Score (base 100; strict/balanced/legacy-friendly presets) | ❌ | **Spec 381** — computed score + presets |
| `.brooks-lint.yaml` config (disable/severity/ignore/focus/strictness/suppress/custom_risks) | ⚠️ unified `config` (Spec 334) exists | **Spec 381** — map onto agency config |
| history `.brooks-lint-history.json` + trend | ❌ (graph + `manage.timeline`) | **Spec 381** — runs as graph nodes; trend is a query |
| triage (accept/dismiss/defer/skip) + suppress w/ expiry | ❌ | **Spec 381** (scoring read) + **`intent.triage`** verb (owner directive — triage is an intent judgment) |
| 12 markdown prose files (Report Template · 6 mode guides · remedy · source-coverage · decay-risks · custom-risks) | ⚠️ template surface exists (Spec 060) | **Spec 384** — ported as agency templates (`<!-- AGENT: -->`) + `develop.reference` docs |
| SARIF output (`sarif.mjs`) | ❌ | **Spec 382** — `analyze.sarif` emit |
| report-parse (`report-parse.mjs`) | n/a — findings already structured | **Spec 382** — *dropped* (port-forward: no prose to parse) |
| CI GitHub Action + ci-gate | ⚠️ `.github/workflows/test.yml` + `gate` cap | **Spec 382** — review-on-diff CI step + score gate |
| 12-book source-coverage discipline | ❌ | **Spec 383** — source-coverage data + cite-discipline |
| eval suite (57 scenarios) + parser benchmark (frozen 30 reports) | ❌ (Gherkin acceptance, Spec 053/077) | **Spec 383** — translate to Gherkin + SARIF property tests |

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
scanners and **tagged with the risk code + book source** (Spec 360); the
reasoning-heavy risks run as **skill-walked judgment** producing Iron Law
findings (Spec 380). Both record as `Finding` graph nodes (Goal 2).

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

- **The engine extends `analyze/`** — the `Finding` shape (360), the decidable
  risk-code scanners (360), score/config/triage/history (381), SARIF (382). This
  honors the drop-in-capability bar: the port is mostly *adding files under an
  existing folder* (`analyze/data/`, `analyze/_decay.py`, `analyze/_score.py`,
  `analyze/_sarif.py`), not a new top-level capability.
- **The developer-facing entry is `develop.review`** — "integrate linting INTO
  `develop`". `develop` already owns walkable disciplines + `skill_walk`; the six
  modes are walkable skills it drives (380). `develop.review(mode, scope)`
  dispatches the mode skill, which calls `analyze.*`. The verb-routing table
  (CLAUDE.md) gains a "review code for decay → `develop.review`" row. The brooks
  **prose** (Report Template, mode guides, remedy) ports onto `develop`/`analyze`
  **templates** + `develop.reference` docs (Spec 384).
- **One judgment touchpoint in `intent`** — `intent.triage` (381 §4, owner
  directive): triaging a `Finding` (accept/dismiss/defer) is a judgment about that
  finding relative to the goal, so it lands beside `intent.assumptions` /
  `intent.tradeoffs`, not in `analyze`. A small, principled third seam — the
  `Finding` engine stays in `analyze`, the *stance on a finding* is `intent`'s.

> **Tension resolved (analyze-vs-develop split):** the *heavy machinery* lives in
> `analyze` (where the `Finding` model and scanners already are — no second copy);
> the *discipline* lives in `develop` (where walkable skills + the dev loop
> already are). This is the same factoring as `develop.test` → `analyze`/pytest:
> develop is the seam, analyze is the engine. Neither capability grows a
> redundant half.

### 3. The hybrid engine (owner Q3) — decidable feeds judgment

Each mode skill (380) walks the same shape, one phase at a time (bounded context):

1. **Scope** — auto-detect (git diff → staged → branch → ask), per brooks'
   `common.md` Auto-Scope rules.
2. **Decidable pass** — call `analyze.quality/security/performance/architecture`;
   every returned `Finding` is tagged with the risk code it evidences (360).
3. **Judgment pass** — the agent reads the decay-risk data (360) for the
   reasoning-heavy risks (R3/R6, T-risks, the non-decidable parts of R1/R4/R5)
   and emits Iron Law `Finding`s, citing a book only when the symptom matches
   (the source-coverage cite-discipline, 383).
4. **Score + report** — Health Score computed from findings × preset (381);
   render the Iron Law report (382).
5. **Remedy/triage** (optional, gated) — `--fix` applies safe remedies, confirms
   risky ones; triage records suppressions (381).

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
- The risk-code → book-source mapping is one table (360), read by both the
  decidable tagger and the judgment skills.

### Child spec map + build order

```
379 (this umbrella)
 └─ 360  decay-risk Finding shape + knowledge data   ← FOUNDATION (no dep)
     ├─ 380  review/remediate + 6 modes + headless twin ← needs 360
     ├─ 381  Health Score + config + history          ← needs 360
     │        + intent.triage (suppression write)     ← + intent (091)
     ├─ 382  SARIF + CI + quality gate (+ ops hardening) ← needs 360 (+381 score)
     ├─ 383  acceptance + source-coverage + evals      ← needs 360,380
     ├─ 384  brooks PROSE → templates + references      ← needs 360,380,382
     └─ 385  migration (.brooks-lint.* → config+graph)  ← needs 381

POST-v1 followup (NOT in the build order — land on demand, YAGNI):
 ⋯ 386  multi-language decidable scanners              ← needs 360,380
```

360 ships first (everything depends on the extended `Finding` + the data). 380
and 381 are parallelizable on top of 360. 382 needs the score from 381. 383
(tests/docs) + 384 (prose/templates) + 385 (migration) land last: 384 renders
382's report path and binds 380's mode skills; 385 imports into 381's config +
nodes; 383 validates the rest. The triage verb (`intent.triage`) is an `intent`
addition carried under 381 (a `Finding` SERVES an intent, so triaging it is a
judgment the `intent` capability owns — beside `intent.assumptions`/`tradeoffs`).

> **Architecture re-examination (2026-06-20, after the spec-panel critique).** The
> home decomposition was re-checked and **holds** — the changes are refinements,
> not a rebuild. The load-bearing confirmation: Cockburn's "two actors" finding
> RESOLVES onto the existing twin shape rather than forcing a new capability —
> `analyze.review` is the **headless engine twin** (home=capability, CI,
> never-blocks), `develop.review`/`develop.remediate` the **interactive seam**
> (home=lifecycle), both over a shared `analyze/_review.py` core. That one
> clarification dissolves three findings (the twin OQ, the CI use case, half the
> LLM-in-CI concern). The only true correctness fix was Fowler's: split the
> non-implementable `review(fix=bool)` (a static `@verb(role=)` can't flip on an
> arg) into `review` (transform) + `remediate` (effect). Everything else hardened
> the operational axis (382) — the panel's weakest at 5.5/10.

### What this program does NOT do

- **No second plugin / no second MCP server** — the agency MCP wire + the
  extended `analyze`/`develop` verbs ARE the port (Spec 348 §4 precedent).
- **No new top-level capability** unless 360 review finds the `analyze` extension
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
  fold entirely into `.agency/config.yaml` under a `quality:` block? (381 default:
  honor both, agency config canonical.)
- **OQ2 — mode skill home.** Mode skills authored on `develop.ontology.skills`
  vs `analyze.ontology.skills`? (Default: `develop`, since `develop` drives the
  walk; analyze stays the engine.)
- **OQ3 — `develop.review` vs `analyze.review`. RESOLVED (spec-panel, 2026-06-20):**
  BOTH, as a twin over a shared `analyze/_review.py` core — `develop.review`/
  `develop.remediate` are the interactive seam (home=lifecycle, may pause),
  `analyze.review` is the headless engine twin (home=capability, never pauses,
  the CI entry). Not one verb; two front doors, one engine (380 §3a).

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — design record, no code yet. Opened by the owner's "port
brooks-lint into agency, integrate linting into develop, use everything"
directive; codegraph-grounded familiarization of both repos (agency 364 files /
7,829 nodes; brooks-lint 22 files / 292 nodes) established the analyze-vs-brooks
lens factoring. Brainstorm forks decided (replace=brooks-itself · home=extend-
analyze+develop-seam · engine=hybrid · 5+1 specs). Children 360 + 380–383 drafted in
the same commit.

**Amended 2026-06-20 (two owner directives, post critical-thinking pass):**
(1) **Prose → templates** — the twelve brooks markdown files become agency
templates (`<!-- AGENT: -->`, Spec 060) + `develop.reference` docs; promoted to a
dedicated child **Spec 384** (the "use EVERYTHING from brooks" prose layer the
critical-thinking pass flagged as the underspecified gap). (2) **Triage → intent**
— the triage verb moves from `analyze.triage` to **`intent.triage`** (a `Finding`
SERVES an intent; its accept/dismiss/defer stance is an `intent` judgment), with
`Suppression`/`Acknowledgement` nodes on the `intent` ontology; carried as a 381
amendment.

**Optimized 2026-06-20 (spec-panel critique → design update; architecture
re-examined + confirmed).** A 10-expert panel (critique mode) scored the program
6.8/10 and surfaced fixes now FOLDED into the children: **(correctness)** Fowler —
split `review(fix=bool)` into `develop.review` (transform) + `develop.remediate`
(effect), since `@verb(role=)` is static (380); Wiegers — the Iron Law gate is a
**decidable predicate** over `Finding` fields, not agent self-assertion (360/380).
**(architecture)** Cockburn+Hightower — the headless/CI actor is the first-class
`analyze.review` twin over a shared `_review.py` core (380 §3a, resolves OQ3);
Hohpe — the decidable→judgment **merge contract** (one `Finding` per
`(risk_code, span)`, 360/380). **(operational, the 5.5/10 axis)** Hightower —
keyless decidable-only CI degradation + base-branch `.agency` cache so trend
survives ephemeral CI (381/382); Nygard — SARIF size cap with a locator, a
wedged-PR override, partial-walk `status:incomplete` never reports green (381/382).
**(testing)** Crispin — stated language matrix (decidable=py, judgment=any) +
deterministic/`-m wet` scenario split + per-mode coverage (380/383); Adzic —
fixture-backed scenarios, not prose Givens (383). **(completeness)** Newman — the
**migration** path is now dedicated child **Spec 385** (`.brooks-lint.*` →
config+graph) + symmetric vendored-data `_source` versioning (360/383).

The program is now **umbrella + 7 children (360 + 380–385)**, with **Spec 386**
(multi-language decidable scanners) drafted as a **post-v1 followup** — out of the
build order, landed on demand. The one product call the panel surfaced (Python-only
decidable) is **resolved**: v1 stays decidable=py / judgment=any-language (owner
"good call", 2026-06-20), and the multi-language lift is captured as 386 rather
than expanding 360/380 now (YAGNI). Next: 360 (foundation) TDD.
