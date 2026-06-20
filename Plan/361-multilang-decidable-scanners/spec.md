---
spec_id: "361"
slug: multilang-decidable-scanners
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [4, 2]
depends_on: ["353", "354", "355", "042"]
domain: analyze
wave: brooks-port-followup
parent_spec: "353"
---

# Spec 361 — Multi-language decidable scanners (the post-v1 evolution path)

> Followup to the Spec 353 brooks-lint port. v1 ships **decidable tagging =
> Python, judgment = any language** (Spec 355 §3c, owner-confirmed 2026-06-20).
> This spec is the **evolution path**: extend the *decidable* half to more
> languages so a non-Python diff gets mechanical risk-tagging too, not judgment
> alone. Explicitly **out of the initial build order** (354→360) — it lands when a
> non-Python codebase actually needs the decidable lift, not before (YAGNI).

## Why

The hybrid engine (Spec 353 §3) has two halves with different language coupling:

- **Judgment** is already language-agnostic — it reasons over any diff/source as
  text (the LLM reads TypeScript as well as Python). v1 needs nothing here.
- **Decidable tagging** is Python-bound — `analyze`'s scanners
  (`_quality`/`_security`/`_performance`/`_architecture`) are Python-AST based
  (codegraph: every axis early-returns for non-`py`). So a TypeScript PR gets
  brooks *judgment* findings but no *mechanical* R1/R4/R5 pre-tagging.

That asymmetry is acceptable for v1 (the panel's Crispin finding, resolved as a
documented limitation) — but it caps the decidable→judgment bridge (354 §3) to
Python. This spec lifts the cap **per language, on demand**, without touching the
judgment pass, the `Finding` shape, or the risk registry.

## Design

### 1. A language-scanner registry (the open-set pattern)

A `LanguageScanner` protocol — `scan(path, axis) -> list[Finding]` — registered by
language tag, mirroring the existing axis registry (`_AXES`, Spec 057) and the
"add a capability = add a file" open-set discipline:

```python
# agency/capabilities/analyze/scanners/<lang>.py
class TypeScriptScanner:
    lang = "ts"
    axes = {"quality", "architecture"}    # which axes it covers (partial is fine)
    def scan(self, path, axis): -> list[Finding]: ...
```

`analyze.run(path, lang=...)` dispatches to the registered scanner; an
unregistered language falls back to **judgment-only** (the v1 behaviour — no
regression). The registry is the single drift site (`# AGENCY-DRIFT:
language-scanners`), so a new language is one file + one registry entry.

### 2. Adapt existing tools — do NOT hand-roll an AST per language (frugal floor)

The frugal ladder (stdlib → native → dep → 1-line) says: a hand-written
TypeScript/Go/Rust AST walker per decay symptom is the wrong cost. Prefer
**adapting a best-in-class multi-language tool** to the `Finding` shape:

| Source | Covers | Adapter output |
|---|---|---|
| **tree-sitter** (one dep, many grammars) | structural metrics — function length, nesting depth, file LOC, fan-out (R1/R4/R5 decidable subset) | `Finding` per threshold breach |
| **semgrep** (multi-lang pattern engine) | symptom patterns — train-wreck chains, god-object hints, duplicate blocks (R1/R3) | `Finding` per rule hit |
| native linters (eslint/tsc, `go vet`, clippy) | language-idiomatic smells | `Finding` per diagnostic |

The adapter is thin: run the tool (an `effect` boundary — Spec 016 role tag), map
its output → `make_finding(...)` with a **language-prefixed rule-id** (`ts:long_function`,
`go:deep_nesting`). Each tool is an **opt-in extra** (like `analyze`'s existing
`ruff`/`bandit`/`radon`), so the base install stays light and a missing tool →
that language stays judgment-only (graceful, per §1).

### 3. Risk mapping stays single-source (rule 2)

New scanners do not invent a second risk map. Their language-prefixed rule-ids get
`decidable` entries in `decay-risks.json` (354 §2) — e.g. R1's `decidable` array
grows `["long_function", "ts:long_function", "go:long_function", …]`. `_decay.py`
(354 §3) tags them identically; the merge contract (355 §3b) dedups against
judgment the same way. One risk registry, N language scanners feeding it.

### 4. The language matrix becomes live, not static

Spec 355 §3c states the matrix in prose; this spec makes it **computed** — the
report's Scope line and a new `analyze.coverage()` reader derive, per language,
which axes have a registered scanner (`{ts: [quality, architecture], py: [all],
go: []}`). So "decidable coverage = none for this language" (355 acceptance) is a
live query over the registry, not a hardcoded string (rule 8).

### What this slice does NOT do

- **No judgment changes** — judgment is already any-language; this is only the
  decidable half.
- **No `Finding`/risk-registry changes** (354 owns them) — scanners feed the
  existing shape + the existing `decidable` arrays.
- **No hand-rolled per-language AST** (frugal — adapt tree-sitter/semgrep/native
  linters; each an opt-in extra).
- **No new severity vocabulary** — language findings derive `tier` like any other
  (354 §1).
- **Not in the v1 build order** — drafted now (owner directive: "write a followup
  spec"), built when a non-Python codebase needs it.

## Acceptance (Gherkin)

```gherkin
Scenario: a registered language scanner tags decidable findings
  Given the TypeScript scanner is registered (tree-sitter extra installed)
  When analyze.run(path, lang="ts") flags a 60-line function
  Then a Finding with rule "ts:long_function" is produced
  And _decay.py tags it risk_code "R1" from decay-risks.json (same map as py)

Scenario: an unregistered language degrades to judgment-only (no regression)
  Given no scanner is registered for Rust
  When develop.review runs on a Rust diff
  Then no decidable findings are produced for it
  And judgment-pass Iron Law findings are still produced
  And analyze.coverage() reports rust decidable axes = []

Scenario: language scanners feed the one risk registry (single source)
  Then every language-prefixed rule-id appears in some risk's decidable array
  And check-drift fails if a scanner emits a rule-id mapped to no risk

Scenario: decidable coverage is computed, not hardcoded
  When I call analyze.coverage()
  Then it returns per-language axes derived from the live scanner registry
  And the report Scope line uses that query, not a literal string

Scenario: a missing adapter tool is graceful
  Given the semgrep extra is not installed
  When analyze.run(lang="ts") runs
  Then the tree-sitter-covered axes still produce findings
  And the semgrep-covered axes are simply absent (no crash, noted in coverage)
```

## Open questions

- **OQ1 — first language to land?** (Default: TypeScript/JS — the most common
  non-Python PR surface + tree-sitter/eslint maturity; Go second.)
- **OQ2 — tree-sitter vs semgrep as the primary adapter?** (Default: tree-sitter
  for structural metrics R1/R4/R5 — deterministic, no rule-authoring; semgrep as an
  opt-in second adapter for pattern risks R3. Decide per-language at build time.)
- **OQ3 — `analyze.coverage()` as a standalone verb or a field on `analyze.run`'s
  return?** (Default: a thin reader verb — reusable by the report + `agency_welcome`.)

## Followup — Implementation Status (2026-06-20)

**DRAFTED 2026-06-20** — the post-v1 evolution slice of the Spec 353 program,
opened by the owner ("write a followup spec instead" — confirming v1 stays
Python-only decidable, judgment any-language). No code yet, and **deliberately not
in the v1 build order** (354→360) — it lands when a non-Python codebase needs the
decidable lift (YAGNI). Narrowly scoped: a `LanguageScanner` registry +
tool-adapters (tree-sitter/semgrep/native linters as opt-in extras) feeding the
existing `Finding` shape + `decay-risks.json` `decidable` arrays (354) + the merge
contract (355 §3b); makes the 355 §3c language matrix a computed `analyze.coverage()`
query. Depends on 354 (shape/registry) + 355 (matrix concept). Next (when
triggered): the registry + the TypeScript tree-sitter adapter as the first
language, RED→GREEN against the §Acceptance scenarios.
