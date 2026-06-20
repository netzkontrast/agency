---
spec_id: "358"
slug: quality-acceptance-source-coverage
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [6, 2]
depends_on: ["353", "354", "355", "053", "077"]
domain: analyze
wave: brooks-port
parent_spec: "353"
---

# Spec 358 — Acceptance coverage + source-coverage + eval/benchmark translation

> Part of the Spec 353 brooks-lint port. This slice ports brooks-lint's
> **grounding + verification** layer: the 12-book source-coverage discipline (so
> findings cite a book only when the symptom matches), and the eval suite + frozen
> parser benchmark — translated into agency's **Gherkin acceptance** contract
> (rule 7) and **SARIF property tests**.

## Why

brooks-lint's credibility rests on two things this slice carries over:

1. **Source-coverage discipline** (`_shared/source-coverage.md`) — a per-book
   matrix ("encoded today" / "do not ignore") that exists *"to prevent shallow
   book-name-citation reviews"*. It is read before writing findings so a book is
   cited only when the observed symptom actually matches that book's principle.
   Without it the Iron Law's "Source" field degrades into name-dropping.
2. **Verification** — brooks has an eval suite (57 scenarios: R1–R6, T1–T6, plus
   false-positive / tradeoff cases that must NOT be flagged) and a frozen
   parser-fidelity benchmark (30 real reports). Agency's testing canon is
   different: **Gherkin acceptance scenarios are the contract** (CLAUDE.md rule 7,
   Spec 077; no unit tests on internals), and findings are structured (no parser).
   So the evals translate to acceptance scenarios, and the benchmark translates to
   a SARIF-validity property test.

## Design

### 1. Source-coverage as data + the cite-discipline

`agency/capabilities/analyze/data/source-coverage.json` — the twelve books
vendored from brooks `_shared/source-coverage.md`, cited upstream:

```
The Mythical Man-Month · Code Complete · Refactoring · Clean Architecture ·
The Pragmatic Programmer · Domain-Driven Design · A Philosophy of Software Design ·
Software Engineering at Google · xUnit Test Patterns · The Art of Unit Testing ·
Working Effectively with Legacy Code · How Google Tests Software
```

Each entry: `{book, encoded: [...], do_not_ignore: [...]}`. The **book count is
derived** from this file, never hardcoded (brooks does exactly this — its
validator derives `sourceCount` from the frontmatter; rule 8). The
`decay-risks.json` source mappings (Spec 354) reference these books by the same
canonical titles — one book registry, two consumers.

The **cite-discipline** is a phase the judgment pass (355) reads on demand
(`develop.reference("source-coverage")`): cite a book only when the symptom
matches its principle; a threshold crossing is a hint, not a verdict; look for
justified tradeoffs before flagging; state the tension when two books pull apart.
This is enforced softly (it is judgment) but **testable** via the false-positive
scenarios (§2).

### 2. Eval suite → Gherkin acceptance (rule 7)

brooks' 57 `evals/evals.json` scenarios become `tests/acceptance/` Gherkin
features (`pytest-bdd`, Spec 053/077). The **invariant** (computed, not pinned —
rule 8): every risk code in the live registry has **≥1 happy-path** scenario (the
symptom IS flagged with the right risk + an Iron Law finding) **and ≥1
false-positive** scenario (the "What Not to Flag" guard — the symptom-shaped-but-
legitimate case is NOT flagged). Examples, one per family:

```gherkin
Scenario: R5 flags a real dependency cycle (happy path)
  Given a domain module importing a concrete database driver
  When develop.review(mode="audit") runs
  Then an R5 Finding cites Clean Architecture (Dependency Inversion)
  And it carries a Consequence and a Remedy

Scenario: R5 does NOT flag a composition root (false positive)
  Given a composition root wiring concrete dependencies
  When develop.review(mode="audit") runs
  Then no R5 finding is raised for the composition root
  # brooks decay-risks.md R5 "What Not to Flag": composition root is not DIP debt

Scenario: R4 does NOT flag a switch over a closed protocol enum (tradeoff)
  Given a switch over an external wire-format enum
  Then no R4 "missing polymorphism" finding is raised
```

The false-positive scenarios are the load-bearing half — they are how the port
proves it ported the *judgment* (the "What Not to Flag" guards from
`decay-risks.md`), not just the symptom list. Coverage is asserted by a meta-test:
`live_risk_codes ⊆ risks_with_happy_scenarios ∩ risks_with_false_positive_scenarios`.

### 3. Parser benchmark → SARIF-validity property test

brooks' `benchmark-corpus.json` (frozen 30 reports) + `benchmark.mjs` test the
**parser/SARIF plumbing** — severity-count fidelity, risk-code precision/recall,
SARIF validity. Agency has no parser (findings born structured, Spec 357), so this
becomes a **property test over a frozen finding-fixture set**:

- A small frozen fixture of `Finding`s (one per risk, incl. decidable-only and a
  `Cx`) — the agency analogue of the corpus, but structured findings, not prose
  reports. Stored as a test fixture, regenerated only deliberately (brooks'
  frozen-artifact discipline — do NOT hand-edit to make a failing renderer pass).
- Properties asserted (computed, not pinned): SARIF is valid 2.1.0; the rule set
  equals the live risk-code registry (Spec 357 §1 — drift-proof); every finding
  produces exactly one SARIF result; `tier→level` mapping is total; severity
  counts in the report equal the finding counts (the fidelity brooks measured,
  now an equality not a percentage because there is no lossy parse step).

> **Tension resolved — frozen fixture vs rule 8 (no frozen snapshots).** The
> *fixture inputs* are frozen (a deliberate, regenerate-only corpus — the brooks
> discipline, and CLAUDE.md #8's documented exception for a cited external
> constant). The *assertions* are computed invariants over them (rule set ==
> registry, counts equal), never a pinned "expected 30 results" magic number. The
> corpus is data; the test guards behaviour.

### 4. Drift coverage (Spec 054)

The port adds a capability surface (risk codes, presets, modes), so it must not
drift across the ~9 dependent sites:

- `# AGENCY-DRIFT: decay-risk-set` tags where the risk-code set is read
  (`_decay.py`, `_sarif.py`, the score, the skills).
- `scripts/check-drift` gains a check: every risk in `decay-risks.json` has a
  source in `source-coverage.json` AND ≥1 acceptance scenario each side (§2) —
  the brooks "every new risk code gets paired coverage" rule, enforced in CI.
- A `<!-- doc-source: -->` marker on any hand-written quality doc (Spec 054
  doc-drift); the capability reference page stays generated (`gen-capability-docs`).

### What this slice does NOT do

- No new findings/score/SARIF (354/356/357 own those) — it *tests* and *grounds*
  them.
- No unit tests on internals (rule 7) — Gherkin acceptance only.
- No prose-report corpus (port-forward: structured fixtures, no parser).
- No live-AI eval runner port (`run-evals-live.mjs`) — the judgment is exercised
  by the acceptance scenarios + the agency wet-LLM path (Spec 352), not a separate
  eval harness.

## Acceptance (Gherkin)

```gherkin
Scenario: the book registry is derived, not hardcoded
  Then source-coverage.json lists the twelve books
  And the reported book count is derived from the file (adding a book needs no code edit)

Scenario: every risk has paired happy + false-positive coverage
  Then for each risk code in the live registry there is >=1 happy-path scenario
  And >=1 false-positive ("What Not to Flag") scenario
  And check-drift fails if a risk lacks either

Scenario: a false-positive case raises no finding
  Given a CRUD transaction-script workflow (legitimately not a rich domain model)
  When develop.review(mode="review") runs
  Then no R6 domain-distortion finding is raised

Scenario: SARIF validity is a computed property over the frozen fixture
  Given the frozen finding fixture (one per risk + a Cx + a decidable-only)
  When analyze.sarif renders it
  Then the SARIF is valid 2.1.0
  And the rule set equals the live risk-code registry
  And report severity counts equal the finding counts (no lossy parse)

Scenario: citing a book requires a matching symptom
  Given an R1 finding
  Then its Source names a book whose source-coverage entry covers that symptom
  And a finding cannot cite a book absent from source-coverage.json
```

## Open questions

- **OQ1** — port all 57 eval scenarios 1:1, or the minimal paired-coverage set
  (≥1 happy + ≥1 false-positive per risk = ~24) and grow as findings surface
  gaps? (Default: minimal paired set first — rule 7 values the contract, not the
  count; grow on real misses.)
- **OQ2** — keep the frozen finding fixture in `tests/` or as vendored data under
  `analyze/data/`? (Default: `tests/` — it is a test artifact, not runtime data.)

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — the grounding/verification slice of the Spec 353 program.
No code yet. Translates brooks' evals + benchmark into agency's Gherkin-acceptance
canon (rule 7, Spec 077) + SARIF property tests; vendors the 12-book
source-coverage as derived data (rule 8). Reuses Spec 053/054 (test slices +
drift). Depends on 354 (risk registry) + 355 (modes to exercise). Lands last,
validating 354–357. Next (after 354/355): `source-coverage.json` + the paired
acceptance features + the SARIF property test + the check-drift rule.
