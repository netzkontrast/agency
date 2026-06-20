---
spec_id: "050"
slug: analyze-deps-integration
status: complete
last_updated: 2026-06-03
owner: "@agency"
depends_on: [042, 045]
informs: [044, 041]
affects:
  - pyproject.toml                                       # [analyze] extras
  - agency/capabilities/analyze/_main.py                 # invoke ruff/bandit/radon when available
  - agency/capabilities/analyze/_ruff.py                  # NEW — ruff wrapper
  - agency/capabilities/analyze/_bandit.py                # NEW — bandit wrapper
  - agency/capabilities/analyze/_radon.py                 # NEW — radon wrapper
  - tests/test_analyze_deps_integration.py                # NEW
estimated_jules_sessions: 1
domain: meta
wave: 2
---

# Spec 050 — Analyze deps integration (ruff + bandit + radon)

## Why

Spec 042 v1 ships hand-rolled lint/security/performance rules
(Q001-Q004, S001-S004, P001-P003). Total: ~10 rules across three
axes. The industrial Python ecosystem has industrialised this:

- **ruff** ships 700+ lint rules (replaces flake8 + pylint + isort +
  pyupgrade + autopep8 in one fast Rust binary). EXACT same severity-
  per-rule-id discipline Spec 042 uses.
- **bandit** ships the canonical Python security ruleset (CWE-mapped,
  configurable, mature). Spec 042's S001-S004 are a small subset.
- **radon** ships cyclomatic complexity (Q005 candidate), maintain-
  ability index, raw metrics (LOC variants beyond Q004's simple count).

Each integrates cleanly via subprocess + JSON parsing. The agency
Finding shape (Spec 042 §"Finding contract") is rich enough to carry
every external rule's data — rule, severity, file, line, message,
evidence. Same severity-per-rule-id discipline (Wiegers).

Doctrine win: instead of trying to catch up to ruff's 700-rule
coverage by hand, agency **composes** ruff and gets the coverage for
free, ALONGSIDE the agency-native Q001-Q004 hand-rolled rules (which
stay for the zero-dep path).

## Done When

### Optional-deps extra

- [ ] `pyproject.toml` `[project.optional-dependencies]` adds an
  `analyze` extra:
  ```toml
  analyze = ["ruff>=0.6", "bandit>=1.7", "radon>=6"]
  ```
- [ ] Activate via `pip install -e .[analyze]`; the wrappers detect
  the tools' presence and degrade silently when missing (same
  pattern as Spec 045 BGE embedder).

### ruff wrapper (`_ruff.py`)

- [ ] `agency/capabilities/analyze/_ruff.py` exposes `scan(path) ->
  list[Finding]`.
- [ ] Subprocess: `ruff check --output-format=json <path>`; captures
  stdout, parses JSON, maps each diagnostic to a Finding.
- [ ] Rule-id translation: ruff's `code` (e.g. `E501`, `F401`)
  becomes the Finding `rule`. Severity mapped from ruff's
  `fix`/`level` per a fixed table.
- [ ] Returns empty list when ruff isn't installed (degrade silently).
  `analyze.quality` keeps emitting Q001-Q004 in the fallback path.
- [ ] Subprocess timeout 30s; failure → empty list + stderr-logged
  warning.

### bandit wrapper (`_bandit.py`)

- [ ] `_bandit.py::scan(path) -> list[Finding]`.
- [ ] Subprocess: `bandit -r <path> -f json`; parse, map to Finding.
- [ ] Rule-id translation: bandit's `test_id` (e.g. `B101`,
  `B602`) becomes the Finding `rule`. Severity from bandit's
  `issue_severity`.
- [ ] Silent fallback when bandit missing.

### radon wrapper (`_radon.py`)

- [ ] `_radon.py::cyclomatic(path) -> list[Finding]` — emits Q005
  findings for complexity > 12. Subprocess: `radon cc <path> -j`.
- [ ] `_radon.py::maintainability(path) -> list[Finding]` — emits
  Q006 findings for MI < 65 (low). Subprocess: `radon mi <path> -j`.
- [ ] Silent fallback when radon missing.

### Integration into `_quality.py` + `_security.py`

- [ ] `_quality.py::scan(path)` appends `_ruff.scan(path)` results
  AND `_radon.cyclomatic/maintainability(path)` results to the
  existing Q001-Q004 list. Order: internal first, external second
  (so the Spec 042 fixtures still find their findings at the front).
- [ ] `_security.py::scan(path)` appends `_bandit.scan(path)` to
  S001-S004.
- [ ] No mode flag in v1; the integration is automatic when deps
  are available.

### agency_doctor reporting

- [ ] `agency_doctor` payload reports `analyze_extras` field:
  `{ruff: "0.6.x"|"missing", bandit: "1.7.x"|"missing",
  radon: "6.x"|"missing"}` so users see which extras are active.

### Tests

- [ ] `tests/test_analyze_deps_integration.py`:
  - When ruff IS installed: scan a fixture file with a long-line +
    unused-import; assert ruff's E501 + F401 findings appear in the
    output AND the internal Q002 + Q001 also fire (no double-coverage
    suppression).
  - When ruff IS missing (mock the subprocess Popen): scan succeeds
    with only internal findings.
  - bandit/radon — same mock-on-missing test shape.

## Design

### Why "compose, don't replace"

Replacing Q001-Q004 with ruff would strand zero-dep users (the
agency core stays light). Compose keeps both paths:

- Zero-dep: Spec 042 internal rules fire.
- `[analyze]` extra: internal AND external rules fire.

Users see more findings with the extra installed; they see the same
core findings without it. No silent feature loss either way.

### Subprocess + JSON, not Python-level imports

ruff is a Rust binary; bandit is a Python lib with a heavy import.
Subprocess gives us:
- isolation from the tool's CLI startup cost (we always run on a
  fresh process)
- robust failure modes (timeout, non-zero exit, JSON-parse error
  all degrade to empty list)
- no Python-version compatibility surface

The downside is invocation overhead (~50ms per tool). Acceptable
given `analyze.run` is already not a hot path.

### Rule-id namespace

ruff codes (E*, F*, W*, …) and bandit codes (B*) DON'T collide with
agency's Q* / S* / P* / A* / IP* (Spec 048). The Finding output
carries the source's native code as `rule`, with a small mapping
table in each wrapper module documenting the conversion.

### Severity mapping tables

Each wrapper has a fixed table from external-severity → agency-severity:

```
# ruff: ruff doesn't have a 3-tier severity per rule
ruff_severity = {
    "E501": "warn",   # long-line
    "F401": "warn",   # unused-import
    "F811": "warn",   # redefined
    # ... default: warn
}

# bandit:
bandit_severity = {
    "HIGH": "fail",
    "MEDIUM": "warn",
    "LOW": "info",
}

# radon cyclomatic:
radon_severity = {  # by complexity score
    "A": None,        # 0-5 — not reported
    "B": None,        # 6-10 — not reported
    "C": "warn",      # 11-20
    "D": "warn",      # 21-30
    "E": "fail",      # 31-40
    "F": "fail",      # 41+
}
```

Tables are constants in the wrapper modules; spec amendment to change.

## Files

- **Add:**
  - `agency/capabilities/analyze/_ruff.py`
  - `agency/capabilities/analyze/_bandit.py`
  - `agency/capabilities/analyze/_radon.py`
  - `tests/test_analyze_deps_integration.py`
- **Modify:**
  - `pyproject.toml` — `[analyze]` extra.
  - `agency/capabilities/analyze/_quality.py` — call ruff + radon
    additions.
  - `agency/capabilities/analyze/_security.py` — call bandit.
  - `agency/engine.py::agency_doctor` — `analyze_extras` field.

## Open Questions

1. **Should the rule-id namespace be agency-prefixed?** E.g. ruff's
   `E501` → `RUF-E501` to distinguish from a future agency-native
   `E501`. Lean: no — adopt the external code AS-IS; collisions
   surface in audit if they happen.
2. **bandit's confidence field.** bandit reports `issue_confidence`
   AND `issue_severity`. agency Finding has only one severity. v1
   ignores confidence; v2 may add as a separate field.
3. **radon's MI threshold.** Default MI < 65 = "low". Some teams want
   < 20 as the only fail-level. Configurable in v2.

## Followup — Implementation Status (2026-06-03)

**Verdict:** Shipped — `[analyze]` extra wires ruff + bandit + radon
into the analyze axes; 9 deps-integration tests green; live dogfood
on this repo activates ruff (E/F/W rules) + bandit + radon CC + MI.

### Done
- `pyproject.toml` `[analyze]` extra: `ruff>=0.6 bandit>=1.7 radon>=6`.
- `_ruff.py` — subprocess wrapper; explicit `--select E,F,W
  --line-length 100 --isolated` so findings stay deterministic
  regardless of user ruff config. Severity table covers E501,
  F401, F811, F841, naming, pyupgrade. Silent fallback when ruff
  missing.
- `_bandit.py` — subprocess wrapper; HIGH/MEDIUM/LOW maps to
  fail/warn/info. Silent fallback when bandit missing.
- `_radon.py` — TWO entry points: `cyclomatic` (Q005 by rank A/B/C/D/
  E/F; A/B not reported) + `maintainability` (Q006 by MI threshold
  65). Silent fallback.
- `_quality.py::scan` extended: appends ruff + radon cyclomatic +
  radon maintainability after internal Q001-Q004. Composition
  pattern.
- `_security.py::scan` extended: appends bandit after internal
  S001-S004.
- `agency_doctor.analyze_extras` reports `{ruff, bandit, radon} →
  version|missing` so users see which extras are live.

### Tests (9 in tests/test_analyze_deps_integration.py)
- Silent-when-missing for each tool (mock shutil.which).
- Real-tool-fires-expected-codes for each tool when installed
  (E501/F401, bandit B-series, radon Q005 on a 15-branch function).
- Composition test: _quality.scan returns BOTH internal Q* AND
  ruff E*/F* when ruff is installed.
- Composition test: _quality.scan falls back to internal-only
  when shutil.which is patched to return None.

### Open for v2
- OQ1 namespace prefix for external codes (`E501` → `RUF-E501`) —
  v1 adopts native AS-IS.
- OQ2 bandit confidence field — v1 ignores; v2 may add to Finding.
- OQ3 radon MI threshold — v1 hard-codes 65; configurable in v2.

### Cluster-coherence (Spec 047)
- C04 Quality (it extends — analyze axes get 700+ ruff rules + full
  bandit CWE coverage + radon cyclomatic/MI for free).
- The composition pattern (silent-fallback + extend) matches Spec
  045 BGE embedder + Spec 044 web_search — agency-canonical optional-
  dep handling.
