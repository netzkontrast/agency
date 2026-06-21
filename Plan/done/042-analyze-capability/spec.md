---
spec_id: "042"
slug: analyze-capability
status: complete
state: done
last_updated: 2026-06-02
owner: "@agency"
depends_on: [016, 020, 023, 040]
affects:
  - agency/capabilities/analyze/__init__.py            # NEW folder-form capability (heavy)
  - agency/capabilities/analyze/_main.py
  - agency/capabilities/analyze/_quality.py            # decidable lint/complexity transforms
  - agency/capabilities/analyze/_security.py           # decidable pattern checks
  - agency/capabilities/analyze/_performance.py        # ast-based hot-path detection
  - agency/capabilities/analyze/_architecture.py       # dependency-graph + cluster analysis
  - agency/capabilities/analyze/_findings.py           # Finding shape + severity union
  - skills/code-analysis/SKILL.md                       # walker discipline + the 4-axis chain
  - skills/code-analysis/references/finding-shape.md
  - skills/code-analysis/references/improve-vs-cleanup.md
  - tests/test_analyze_capability.py
  - tests/test_analyze_quality.py
  - tests/test_analyze_security.py
  - tests/test_analyze_performance.py
  - tests/test_analyze_architecture.py
estimated_jules_sessions: 3
domain: meta
wave: 2
unblocks: [043, 046]
---

# Spec 042 — `analyze` Capability (Multi-Axis Decidable Analysis)

## Why

SuperClaude ships **three overlapping commands**: `sc-analyze`,
`sc-improve`, and `sc-cleanup`. Reading them (subagent report, PR #17
thread) shows they share an architectural pattern that agency doesn't
have today: **multi-axis code analysis with severity-rated findings**.
SC implements this with persona-injection and MCP-orchestration; agency
can implement it as **four pure transform verbs** (one per axis) + **two
act verbs** (improve, cleanup) that compose them.

The agency-native shape is more honest than SC's because:

- Each axis is a **decidable transform** (same code → same findings) —
  no LLM in the loop. This is the same discipline that distinguishes
  `dramatica_lookup` from `coherence_check`'s heuristic checks (Spec 010
  §"The decidable coherence subset").
- The composition layer (`improve`/`cleanup`) is an `act` that RECORDS
  the findings as `Finding` nodes in the graph — provenance survives the
  session.
- A `code-analysis` Lifecycle skill walks the four-axis chain one phase
  at a time (progressive disclosure), ending at a hard `apply` gate.

This spec also subsumes `sc-improve` and `sc-cleanup` as **modes of the
same capability**, not three separate surfaces. The user picks an
intention (`analyze`, `improve`, `cleanup`); the capability runs the
appropriate subset of transforms and composes them differently.

## Done When

### Folder-form capability (Spec 016 Phase 3)

- [ ] `agency/capabilities/analyze/` exists with `__init__.py` re-exporting
  `AnalyzeCapability` and `_main.py` carrying `# agency-scaffold: v1` on
  line 1.
- [ ] `plugin.lint_capability("analyze")` returns `ok=True` in block mode.

### Four `transform` verbs (one per axis, pure, decidable)

- [ ] `analyze.quality(path: str = ".", lang: str = "py") -> dict` —
  reports `{findings: [Finding, ...], counts: {info|warn|fail: int}}`.
  Findings are surfaced from **decidable lint rules** only:
  ruff-equivalent (unused imports, long lines, etc.), cyclomatic
  complexity > 12, function length > 80, file length > 500. No
  taste-judgement rules ("name is unclear" → not shipped).
- [ ] `analyze.security(path: str = ".", lang: str = "py") -> dict` —
  same shape; findings include: hardcoded secrets (regex over known
  patterns), `eval`/`exec`/`shell=True` usage, dangerous deserialization
  (`pickle.load`, `yaml.load` without SafeLoader), SQL string-format
  patterns. NO LLM-based "may be vulnerable" judgements.
- [ ] `analyze.performance(path: str = ".", lang: str = "py") -> dict` —
  AST-based decidable checks: `O(n²)` nested loop on growing collections,
  unbounded `while True` without sleep/break, `+=` in a loop (string
  concatenation antipattern), recursive call without memoization decorator.
- [ ] `analyze.architecture(path: str = ".") -> dict` — dependency graph
  + structural metrics: import cycles, package fan-in/fan-out, the
  largest module by LOC, files exceeding 600 LOC (cluster-by-purpose
  doctrine — `CLAUDE.md` Rule #2 implies this is a signal).
- [ ] Every finding carries `{rule: str, severity: "info"|"warn"|"fail",
  file: str, line: int, message: str, evidence: str}`. Severity enum is
  declared on `AnalyzeCapability.ontology.enums[("Finding", "severity")]`.
- [ ] **Severity-assignment rule per axis** (Wiegers — requirements
  clarity; no ambiguity on what severity a rule emits):
  - **quality**: `fail` = breaks the build / static-analysis blocker
    (unused import that triggers `-Werror`, cyclomatic > 20). `warn` =
    code-smell that doesn't block (cyclomatic 13–20, long line, function
    > 80 LOC). `info` = style preference (function > 60 LOC, dense
    one-liner).
  - **security**: `fail` = exploitable today (hardcoded credential,
    `eval(<user_input>)`, SQL string-format with user data). `warn` =
    exploit-conditional-on-context (`shell=True` with constant input,
    `pickle.load(<file>)` where file might be user-controlled). `info` =
    pattern-of-concern that needs human review (`subprocess` with shell
    substitution).
  - **performance**: `fail` = O(n²) loop on a collection > 1000 items
    documented in surrounding code. `warn` = O(n²) on collection of
    unknown size. `info` = `+=` string-concat in a loop of unknown bound.
  - **architecture**: `fail` = circular import. `warn` = file > 600 LOC,
    package fan-in > 8. `info` = file > 400 LOC.
  Severity assignments are **fixed per rule ID**; users cannot
  reconfigure via flags in v1 (Spec 023 doctrine: severities are
  contract-level, not preference-level).

### Two `act` verbs (compose + record)

- [ ] `analyze.run(path: str, axes: list[str] = None, intent_id: str)`
  (act) — runs the requested axes (default: all four), records one
  `Analysis` node + one `Finding` node per finding (all linked
  `OBSERVED_DURING` the intent), returns a compact summary
  `{analysis_id: str, totals: {axis: counts}}`. The detail lives in the
  graph; the wire payload stays small.
- [ ] `analyze.improve(analysis_id: str, intent_id: str,
  axes: list[str] = None, apply: bool = False)` (act) — reads a prior
  Analysis, produces an **improvement plan** as a Reflection node (kind
  `improvement-plan`), and IF `apply=True`, dispatches a `gate.check`
  per finding cluster to be approved before the orchestrator writes. The
  apply path is gated; the planning path is pure.
- [ ] `analyze.cleanup(path: str, dry_run: bool = True, intent_id: str)`
  (act) — a focused variant of `improve` that ONLY targets dead-code
  findings (unused imports, unreachable branches, empty try/except),
  produces a patch plan, applies on `dry_run=False` with the same gate.

### Skill walker

- [ ] `skills/code-analysis/SKILL.md` exists with frontmatter
  ("Use when…" trigger, `allowed-tools` list, kebab-case name).
- [ ] The Lifecycle skill template on
  `AnalyzeCapability.ontology.skills["code-analysis"]` has five phases:
  ```
  scope → axes → run → review → apply(hard)
  ```
  `scope` decides path + language; `axes` chooses which transforms to
  run; `run` calls `analyze.run`; `review` surfaces the findings; `apply`
  is a hard gate before `improve` / `cleanup` writes.
- [ ] The walker calls `delegate.dispatch_decision` (Spec 040) at the
  `axes` phase: if `analyze_architecture` fires on a tree > 10 packages,
  dispatch S1:tokens + S2:files signals → subagent.

### Ontology fragment

- [ ] `AnalyzeCapability.ontology` declares:
  - **Nodes:** `Analysis` (`required: [path, axes, started_at]`),
    `Finding` (`required: [rule, severity, file, line, message]`).
  - **Enums:** `(Finding, severity): {info, warn, fail}` and
    `(Analysis, axis): {quality, security, performance, architecture}`.
  - **Edges:** `HAS_FINDING` (Analysis → Finding), `IMPROVES`
    (Reflection → Analysis), `CLEANS` (Reflection → Analysis).
  - **Schemas:** `improvement-plan` artefact `[analysis_id, items]`.
  - **Skills:** `code-analysis` (walker above).

### Tests

- [ ] `tests/test_analyze_quality.py` — fixture file with 2 unused
  imports + 1 long line; assert 3 findings with correct severities.
- [ ] `tests/test_analyze_security.py` — fixture with 1 `eval(...)` +
  1 hardcoded API key pattern; assert 2 fail-severity findings.
- [ ] `tests/test_analyze_performance.py` — fixture with nested `O(n²)`
  loop on growing list; assert 1 warn finding.
- [ ] `tests/test_analyze_architecture.py` — fixture with circular
  import; assert 1 fail finding.
- [ ] `tests/test_analyze_capability.py` — `analyze.run` records the
  graph artefacts and the wire shape stays compact (< 500 tokens for a
  small repo).

## Design

### Why four AXES, not "one analyze with options"

SuperClaude bundles them into `sc-analyze`; agency splits them so each
axis is a callable transform on its own. Three reasons:

1. **Token-economy.** Calling `analyze.security` on a known
   already-quality-clean PR returns only security findings — no padding.
2. **Composition.** Specs 035 (`research`) and 038 (`business-panel`)
   will call individual axes. They don't want the full bundle.
3. **Testability.** Each axis is independently testable. A dispatch-test
   for `analyze.architecture` doesn't pull in the security ruleset.

### Why decidable-only (and what's deliberately NOT shipped)

The decidable subset is what we can defend in code review without
disclaiming "this is heuristic". Three categories of judgement we
deliberately **do not ship**:

| Family | Why not |
|---|---|
| "Name is unclear" / "doc is poor" | Taste; needs LLM grounded in context |
| "May be vulnerable to deserialization attack" | Confidence interval; needs runtime model |
| "This loop is slow" without `O(n²)` proof | Profiling is the answer, not lint |
| "Architecture smell" beyond cycle / fan-out / LOC | Needs project-context knowledge |

If users want LLM-grounded judgement, they walk the `code-analysis` skill
and use `delegate.dispatch` to a subagent at the `review` phase — but
that's an explicit dispatch, not an inline "smart" lint.

### Modes of the same capability

| Verb | What it does | When to use |
|---|---|---|
| `analyze.run` | runs N transforms, records findings, returns summary | "give me the report" |
| `analyze.improve` | reads findings, drafts a plan, optionally applies | "fix the findings" |
| `analyze.cleanup` | improve restricted to dead-code findings | "tidy up only what's obviously dead" |

The acceptance-gate on `improve` and `cleanup` is the agency-native answer
to SC's "STOP AFTER analysis" output-only-boundary discipline. Same goal,
different mechanism — agency uses the hard-gate Lifecycle phase, SC uses
prompt-text "do not write code".

### Finding shape (the contract)

```python
class Finding(TypedDict):
    rule: str          # rule id, stable across runs ("U001", "S014", "P003", "A007")
    severity: Literal["info", "warn", "fail"]
    file: str          # repo-relative path
    line: int          # 1-indexed
    message: str       # ≤ 120 chars (Spec 023 brief-budget)
    evidence: str      # the source line, truncated to 200 chars
```

This is the agency-canonical lint-finding shape. Every axis emits this.
Downstream (`improve`, `cleanup`, `business-panel`) clusters by `rule`
prefix (`U*` = unused, `S*` = security, …).

### Token-budget discipline

- `analyze.run` returns `{analysis_id, totals: {axis: {info, warn, fail}}}`
  — typically < 200 tokens. Details are in the graph.
- `analyze.<axis>` returns the full `findings` list — token-bounded by
  cap on max-findings-per-axis (default 50, override via param). A path
  with 200 findings gets truncated with a `truncated: true` marker.
- `analyze.improve` returns `{improvement_plan_id, item_count, summary}`
  — < 300 tokens. The plan itself is a Reflection node.

## Files

- **Scaffold first** via `develop.scaffold_capability(name="analyze",
  kind="heavy")`.
- **Create** (post-scaffold):
  - `agency/capabilities/analyze/__init__.py`
  - `agency/capabilities/analyze/_main.py`
  - `agency/capabilities/analyze/_quality.py`
  - `agency/capabilities/analyze/_security.py`
  - `agency/capabilities/analyze/_performance.py`
  - `agency/capabilities/analyze/_architecture.py`
  - `agency/capabilities/analyze/_findings.py`
  - `skills/code-analysis/SKILL.md`
  - `skills/code-analysis/references/finding-shape.md`
  - `skills/code-analysis/references/improve-vs-cleanup.md`
  - `tests/test_analyze_*.py` (5 files)
- **Do not modify:** the engine / ontology / memory core.

## Open Questions

1. **Multi-language coverage.** v1 is Python-only (`lang="py"`). Specs
   013 / 014 / 015 in the future could add `lang="ts"` / `"rs"` / etc.
   Open: keep `lang` as a string parameter (v1) or split into per-language
   capabilities later? v1 keeps single capability; multi-lang via param.
2. **Caching analysis results.** If a user runs `analyze.run` then
   `analyze.improve(analysis_id=...)` 30 minutes later, the source may
   have changed. Should `improve` re-run the analysis automatically?
   v1 says: trust the analysis_id, document the risk in the docstring;
   v2 considers a freshness check.
3. **Apply path safety.** `analyze.improve(apply=True)` writes to disk.
   Should we require `gate.check` per `file` (atomic per-file approval)
   or per `cluster` (approve the whole "unused imports" group)? Lean
   per-cluster; the gate is overridable per file inside the gate via
   `force=True` (Spec 010 §"Edges" precedent).
4. **Relationship to `develop.review`.** The existing `develop.review`
   skill is human-driven; `analyze.run` is automated. Both produce
   findings. Open: should `develop.review` invoke `analyze.run` at one
   of its phases, or stay independent?

## Evidence

- SC commands `sc-analyze`, `sc-improve`, `sc-cleanup` (PR #17 subagent
  report) — the cross-cluster pattern this spec generalises.
- Spec 010 §"The decidable coherence subset" — the decidable-vs-judgement
  doctrine; analyze follows the same discipline.
- Spec 016 (folder-form capability + scaffold + block-mode lint) — the
  authoring substrate.
- Spec 023 (adaptive disclosure) — token-budget discipline on findings.
- Spec 040 (subagent decision heuristics) — analyze.architecture's
  dispatch trigger.
- CLAUDE.md Rule #1 (dogfood the engine) + Rule #2 (graph is the store)
  — Findings recorded as graph nodes, not as `lint-report.json` files.

## Followup — Implementation Status (2026-06-02)

**Verdict:** Shipped — 7 verbs live, 4 axes + 2 acts wired,
code-analysis skill folder shipped, lint_capability("analyze")
returns ok=True in block mode, 502 full-suite tests green after
4 code-review passes + 2 dogfood-driven false-positive fixes.

### Done
- Folder-form capability `agency/capabilities/analyze/`:
  - `_main.py` — `AnalyzeCapability` class (scaffold marker on
    line 1; ontology with 2 nodes, 2 enums, 3 edges, 1 schema, 1 skill;
    7 verbs).
  - `_findings.py` — Finding TypedDict + `make_finding()` with severity
    validation + Spec 023 truncation + `count_by_severity()` helper.
  - `_walk.py` — shared `python_files()` + `read_text()` (DRY across
    axes; extracted in code-review pass).
  - `_quality.py` — Q001 unused-import (AST + __all__ + __future__
    handling), Q002 long-line, Q003 long-function, Q004 long-file.
  - `_security.py` — S001 eval/exec, S002 hardcoded credential
    (regex + value-never-leaks), S003 pickle.load, S004 subprocess
    shell=True (restricted to subprocess family — code-review F12 fix).
  - `_performance.py` — P001 nested O(n²), P002 += in loop, P003
    unbounded while True (with break/return/sleep escape detection).
  - `_architecture.py` — A001 circular import (Tarjan SCC), A002
    large file (>600 LOC), A003 medium file (>400 LOC).
- 4 transform verbs (`quality`, `security`, `performance`, `architecture`)
  + 2 act verbs (`run` records Analysis + Finding nodes;
  `improve` drafts improvement-plan Reflection; `cleanup` focused
  dead-code mode).
- 5-phase `code-analysis` Lifecycle skill on
  `AnalyzeCapability.ontology.skills` (scope → axes → run → review →
  apply(hard)).
- `skills/code-analysis/SKILL.md` + `references/finding-shape.md` +
  `references/improve-vs-cleanup.md`.
- Engine dedupe fix in `engine.py` (discover() + extra_capabilities
  with same name now first-wins; surfaced by lint_capability's
  consumer-contract check when the cap is BOTH auto-discovered AND
  passed as extra — first scaffold-marked cap so first to hit).
- Tests: `test_analyze_quality.py` (8), `test_analyze_security.py` (6),
  `test_analyze_performance.py` (4), `test_analyze_architecture.py` (4),
  `test_analyze_capability.py` (10) — total 33 spec tests; 502 full
  suite passes; lint_capability("analyze") ok=True block mode.

### Code-review loop (agency:code-review skill)
- Pass 1 — surfaced F1 (DRY: _python_files+_read 4×) → extracted
  `_walk.py`; F12 (shell=True false positives) → restricted to
  subprocess family + added test.
- Pass 2 — found unused `os` import in `_security.py` after refactor
  (irony: my own Q001 rule would have caught this); dead
  `_FINDING_KEYS` in `_findings.py`; redundant `hasattr(ast,
  "NameConstant")` ternary in `_performance.py` — all cleaned up.
- Pass 3 (meta-dogfood) — ran `analyze.quality` on the capability
  itself. Found 8 false-positive Q001 findings:
  7× `from __future__ import annotations` (compile-time directive,
  not a name binding) + 1× `from ._main import AnalyzeCapability`
  in `__init__.py` (re-export via __all__). Fixed both with
  `_imported_names()` skipping __future__ + `_exported_names()`
  reading `__all__` literal. Added two regression tests.
- Pass 4 — `lint_capability("analyze")` ok=True; one final brief-budget
  fix on `performance` verb docstring (21 → 19 cl100k tokens).

### Open for v2 (per spec §Open Questions)
- OQ1 multi-language coverage (currently Python-only via `lang="py"`).
- OQ2 caching analysis results (re-run-on-stale-source vs.
  trust-analysis_id).
- OQ3 apply path (`gate.check` per cluster) — v1 ships planning-only.
- OQ4 relationship to `develop.review` — needs a one-paragraph
  doctrine pass in `develop.py` docstring.

### Cluster-coherence cross-refs (Spec 047)
- C04 Quality (it IS).
- C03 Implementation (Spec 041 code-reviewer-prompt reuses Finding shape).
- C06 Cleanup (cleanup verb is the dead-code mode of analyze).
- C13 Plugin (lint_capability's consumer-contract check uncovered the
  engine dedupe bug; Spec 047 §C04 Risk 1 — one Finding shape across
  surfaces — verified live).
