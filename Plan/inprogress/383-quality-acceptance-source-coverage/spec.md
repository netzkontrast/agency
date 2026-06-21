---
spec_id: "383"
slug: quality-acceptance-source-coverage
status: partial
state: inprogress
last_updated: 2026-06-21
owner: "@agency"
vision_goals: [6, 2]
depends_on: ["379", "360", "380", "053", "077"]
domain: analyze
wave: brooks-port
parent_spec: "379"
---

# Spec 383 — Acceptance coverage + source-coverage + eval/benchmark translation

> Part of the Spec 379 brooks-lint port. This slice ports brooks-lint's
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
`decay-risks.json` source mappings (Spec 360) reference these books by the same
canonical titles — one book registry, two consumers.

The **cite-discipline** is a phase the judgment pass (380) reads on demand
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

**Concrete fixtures, not prose Givens (Adzic fix).** "Given a composition root
wiring concrete dependencies" is a description, not a test — it cannot guard
anything. Each scenario binds a **real fixture file** under
`tests/acceptance/fixtures/quality/<risk>/{positive,negative}.py` (the actual
code) and asserts against the **structured `Finding`** (risk_code + the Iron Law
fields), not a prose match. The fixtures ARE the specification-by-example corpus —
the negative (false-positive) fixtures especially must be real compilable code, or
the "What Not to Flag" guard is untested.

**Per-mode coverage, not only per-risk (Crispin fix).** The meta-test also asserts
each of the six modes (review/audit/debt/test/health/sweep) has ≥1 scenario — risk
coverage and mode coverage are independent matrices, both enforced.

**Deterministic vs wet-LLM split (Crispin fix — the load-bearing test-strategy
decision).** The decidable-tagging scenarios are deterministic (no LLM) and run in
the **default CI gate every PR**. The judgment-pass scenarios exercise a
non-deterministic LLM (Spec 352 wet path) and are **tag-gated** (`-m wet`, run on a
tag / nightly), mirroring the existing `-m e2e` split (Spec 053) — so the PR gate
never flakes on model variance, while the judgment is still exercised. The
false-positive *decidable* guards (e.g. R5 composition-root via import analysis)
stay deterministic; only the *reasoning* guards are wet.

### 3. Parser benchmark → SARIF-validity property test

brooks' `benchmark-corpus.json` (frozen 30 reports) + `benchmark.mjs` test the
**parser/SARIF plumbing** — severity-count fidelity, risk-code precision/recall,
SARIF validity. Agency has no parser (findings born structured, Spec 382), so this
becomes a **property test over a frozen finding-fixture set**:

- A small frozen fixture of `Finding`s (one per risk, incl. decidable-only and a
  `Cx`) — the agency analogue of the corpus, but structured findings, not prose
  reports. Stored as a test fixture, regenerated only deliberately (brooks'
  frozen-artifact discipline — do NOT hand-edit to make a failing renderer pass).
- Properties asserted (computed, not pinned): SARIF is valid 2.1.0; the rule set
  equals the live risk-code registry (Spec 382 §1 — drift-proof); every finding
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

- No new findings/score/SARIF (360/381/382 own those) — it *tests* and *grounds*
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

Scenario: scenarios bind real fixtures, not prose Givens
  Then each happy/false-positive scenario references a fixture file under
       tests/acceptance/fixtures/quality/<risk>/{positive,negative}.py
  And it asserts the structured Finding (risk_code + Iron Law fields), not a prose match

Scenario: deterministic decidable scenarios run every PR; wet judgment is tag-gated
  Then decidable-tagging scenarios carry no wet marker and run in the default gate
  And judgment-pass scenarios are marked -m wet (run on a tag/nightly, not the PR gate)

Scenario: every mode has coverage, independent of risk coverage
  Then each of review/audit/debt/test/health/sweep has >=1 acceptance scenario
  And the mode matrix and the risk matrix are both enforced by the meta-test
```

## Open questions

- **OQ1** — port all 57 eval scenarios 1:1, or the minimal paired-coverage set
  (≥1 happy + ≥1 false-positive per risk = ~24) and grow as findings surface
  gaps? (Default: minimal paired set first — rule 7 values the contract, not the
  count; grow on real misses.)
- **OQ2** — keep the frozen finding fixture in `tests/` or as vendored data under
  `analyze/data/`? (Default: `tests/` — it is a test artifact, not runtime data.)

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — the grounding/verification slice of the Spec 379 program.
No code yet. Translates brooks' evals + benchmark into agency's Gherkin-acceptance
canon (rule 7, Spec 077) + SARIF property tests; vendors the 12-book
source-coverage as derived data (rule 8). Reuses Spec 053/054 (test slices +
drift). Depends on 360 (risk registry) + 380 (modes to exercise). Lands last,
validating 360–382.

**Amended 2026-06-20 (spec-panel critique):** scenarios bind **real fixture files**
(`tests/acceptance/fixtures/quality/<risk>/{positive,negative}.py`) asserting the
structured `Finding`, not prose Givens (Adzic); the deterministic decidable
scenarios run in the default PR gate while wet-LLM judgment scenarios are
**tag-gated `-m wet`** (Crispin — no PR-gate flakiness); the meta-test enforces a
**per-mode** coverage matrix alongside the per-risk one (Crispin). Next (after
360/380): `source-coverage.json` (+ `_source` marker) + the paired fixture-backed
acceptance features (deterministic + `-m wet`) + the SARIF property test + the
per-risk/per-mode check-drift rule.

### Slice 1 — SHIPPED 2026-06-21 (source-coverage + grounding + SARIF property)

`status: draft → partial`. TDD RED→GREEN:
- **`agency/capabilities/analyze/data/source-coverage.json`** — the 12-book matrix
  (Brooks…Google), keys in the SAME `"Author — Title"` form as
  `decay-risks.json` `sources[].book` (one book registry, two consumers). Each
  entry carries `encoded` (principles the book contributes) + `do_not_ignore`
  (false-positive guardrails). Stamped `_source: brooks-lint@ec44ec8`.
- **`agency/capabilities/analyze/_coverage.py`** — `load_source_coverage()`,
  the single reader (mirrors `_decay.load_risks()`); excludes `_`-prefixed
  metadata; book COUNT derived from the file (rule 8).
- **`tests/acceptance/{features/quality_coverage.feature,test_quality_coverage.py}`**
  — 3 scenarios, behaviour-only (rule 7): (a) book registry DERIVED (≥12 canonical
  books as a SUBSET assertion, each shaped, count from the file); (b) **grounding
  invariant** — every book a decay risk cites exists in source-coverage (no
  name-dropping); (c) **SARIF property** over a frozen 5-finding fixture (R1/R5/T1/
  custom-Cx/decidable-only) — valid 2.1.0, rule set == live registry, one result
  per finding. The grounding test IS the live consumer (contract-guarded, not dead
  code). `python -m pytest tests/acceptance/test_quality_coverage.py` → 3 passed.

### Slice 2 — SHIPPED 2026-06-21 (paired decidable corpus + coverage matrix)

Verification/grounding slice over existing `develop.review` behaviour (§"does NOT
do" — no new findings/score/SARIF). TDD, but GREEN-on-write by nature (it grounds
behaviour that already ships):
- **`tests/acceptance/{features/quality_corpus.feature,test_quality_corpus.py}`** —
  the **paired decidable corpus**. For every DECIDABLE risk (R1→Q003 long-function,
  R4→Q004 long-file, R5→A001/A004 cycle/fan-out — the set DERIVED from each risk's
  `decidable` array, rule 8) a positive fixture trips it (asserts the structured
  `Finding` carries the risk code + a complete Iron Law: Source · Consequence ·
  Remedy) and a negative **"What Not to Flag"** fixture is spared (the load-bearing
  half — a short function / small file / acyclic-low-fan-out package). Fixtures are
  real compilable code GENERATED from the live thresholds (`_FUNC_LOC_LIMIT` /
  `_FILE_LOC_LIMIT`) — rule 8, no frozen snapshot — exercised through the real
  `develop.review` path (Adzic — not prose Givens), mirroring `test_decay_risk`.
- **Coverage matrix (derived invariants):** (a) every decidable risk in the live
  registry is covered by the corpus manifest (a new decidable rule ⇒ the meta-test
  fails until a builder + Examples row is added — the drift guard); (b) all six
  quality modes (review/audit/debt/test/health/sweep) run a decidable scan. 5
  scenarios, `python -m pytest tests/acceptance/test_quality_corpus.py` → 5 passed.

**Design choice — generated fixtures over committed `fixtures/quality/<risk>/*.py`
for the decidable risks.** The spec sketched committed fixture files; the decidable
risks are all THRESHOLD/STRUCTURAL, so a committed `>500`-line file would FREEZE the
threshold (rule 8) and a retune would silently flip negative→positive. Generating
from the live limit is rule-8-clean AND meets the Adzic concern (real compilable
code, structured-`Finding` assertion). Committed hand-authored fixtures remain the
right form for the **wet judgment** risks (Slice 3), where the pattern SHAPE is the
point and there is no numeric threshold to derive.

### Slice 3 — SHIPPED 2026-06-21 (check-drift coverage gate + AGENCY-DRIFT tags)

The §4 drift-coverage half — promotes the Slice 1 + 2 invariants from test-only to
a fast standalone CI gate:
- **`scripts/check-drift` — "decay-risk coverage gate"**: (1) **grounding** — every
  book a decay risk cites (`decay-risks.json` `sources[].book`) MUST exist in
  `source-coverage.json` (no shallow name-dropping); (2) **decidable corpus** —
  every risk with a `decidable` rule-id mapping MUST have a paired Examples row in
  `quality_corpus.feature`. Both sets are DERIVED from the registry (rule 8); the
  corpus side reads the feature file (decoupled from the test module). Verified to
  CATCH both drift modes (remove a cited book → flagged; drop a decidable row →
  flagged), so it is live surface, not a dormant gate. Clean run reports
  "12 cited books grounded; 3 decidable risks paired".
- **`# AGENCY-DRIFT` tags** at the two registry readers: `decay-risk-set` on
  `_decay.load_risks()` (the canonical risk-set reader) and `source-coverage` on
  `_coverage.load_source_coverage()`, each naming the gate that guards them.

**BLOCKED — the `-m wet` judgment corpus (deferred, not a Spec 383 gap).** §2's wet
half (happy + false-positive scenarios for the nine JUDGMENT-only risks
R2/R3/R6/T1–T6) needs a path that takes a code file and emits an R2/R3/T1 *judgment*
finding. **That capability does not exist yet:** `develop.review` runs the DECIDABLE
scanners + `_decay.tag` only, and `_wet_verify` (Spec 164) is phase-DISCIPLINE
verification, not decay-judgment over code. Authoring `-m wet` scenarios now would
test a non-existent path (vaporware). The wet corpus lands when the LLM
code-judgment pass ships (a Spec 352/380 follow-on); until then Spec 383 stays
`partial` on a genuine dependency, with everything decidable DONE (grounding · SARIF
property · decidable corpus · coverage matrix · check-drift gate · drift tags).
