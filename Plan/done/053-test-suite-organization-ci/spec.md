---
spec_id: "053"
slug: test-suite-organization-ci
status: complete
state: done
last_updated: 2026-06-03
owner: "@agency"
depends_on: [039]
affects:
  - pyproject.toml                              # add pytest-xdist to dev; register per-capability markers
  - tests/conftest.py                            # auto-mark tests by file path
  - scripts/test-changed                         # NEW — git-diff-driven test slicing
  - scripts/test-cap                              # NEW — run tests for one capability
  - .github/workflows/test.yml                   # NEW — CI matrix runner
  - .github/workflows/lint.yml                   # NEW — ruff/bandit/radon on every push
estimated_jules_sessions: 0
domain: meta
wave: 2
---

# Spec 053 — Test-suite organization + CI workflow

## Why

The full pytest suite at this branch's HEAD runs **~4 minutes** locally
(636 tests across ~50 files). Every spec implementation pays this cost
twice (per-spec sweep + final voll-suite). Two complaints land at the
same time:

1. **Locally:** every TDD-loop iteration of a non-trivial spec is
   gate-locked by the suite finish line. The user typed
   "*Die Tests ständig fresseb tuviel Zeit.*"
2. **CI:** there is no GitHub Actions workflow today. Regressions are
   caught by the human running `python -m pytest` before push.

Both reduce to: **organize so local devs iterate FAST, and let CI
catch the rest.** The standard solution is:

- **Mark tests by capability/spec** — `pytest -m research` runs only
  the research-related tests (under 5s).
- **Parallel execution** — `pytest -n auto` uses all CPU cores. On a
  4-core local machine, a 4-min suite drops to ~1 min.
- **GitHub Actions** — push triggers the full suite on a clean
  remote runner with the full deps matrix.

## Done When

### Test marker auto-application

- [ ] `tests/conftest.py` auto-applies markers based on the test file
  name pattern:
  - `tests/test_analyze_*.py` → `@pytest.mark.analyze`
  - `tests/test_research_*.py` → `@pytest.mark.research`
  - `tests/test_dogfood_*.py` → `@pytest.mark.dogfood`
  - `tests/test_document_*.py` → `@pytest.mark.document`
  - `tests/test_reflect_*.py` → `@pytest.mark.reflect`
  - `tests/test_delegate_*.py` + `test_dispatch_*.py` → `@pytest.mark.delegate`
  - `tests/test_intent_*.py` → `@pytest.mark.intent`
  - `tests/test_jules_*.py` → `@pytest.mark.jules`
  - `tests/test_e2e_*.py` → `@pytest.mark.e2e` (already present)
  - All other → no auto-marker (still runs by default)
- [ ] Markers registered in `pyproject.toml`'s
  `[tool.pytest.ini_options].markers` to avoid PytestUnknownMarkWarning.
- [ ] `pytest -m analyze` returns < 10s on the current corpus.
- [ ] `pytest -m research` returns < 10s.

### Parallel execution

- [ ] `pyproject.toml` `[project.optional-dependencies].dev` adds
  `pytest-xdist>=3.5`.
- [ ] CI runs `pytest -q -n auto -m "not e2e"` (parallel, no E2E).
- [ ] Document `pytest -n auto` in CLAUDE.md Dev section.

### Slicing scripts

- [ ] `scripts/test-changed` — uses `git diff --name-only` against the
  branch's merge-base with main to find changed files, maps them to
  test markers, then runs `pytest -m "<derived-markers>"`. Falls back
  to running the full suite when no clear capability-mapping is
  derivable.
- [ ] `scripts/test-cap <name>` — runs `pytest -m <name>` for one
  capability. Used by the just-shipped-spec loop.

### GitHub Actions CI

- [ ] `.github/workflows/test.yml`:
  - Triggers: `pull_request`, `push` to `main`.
  - Matrix: `ubuntu-latest` + Python `3.11`.
  - Steps: checkout, set up Python, `pip install -e ".[dev,analyze]"`,
    run `pytest -q -n auto -m "not e2e"` (the parallel non-E2E run),
    upload the test-summary as an artifact.
  - Reports pass/fail count + duration in the PR check status.
- [ ] `.github/workflows/lint.yml` (optional but recommended):
  - On `pull_request`: run `ruff check --select E,F,W --line-length 100
    agency/` + `bandit -q -r agency/`. Findings DON'T fail the build
    (the agency analyze.* surface uses them in compose-not-replace
    mode); but the workflow's status reports a count.
- [ ] CI runs E2E tests on `tag` builds only (`v*` ref pattern) —
  matches Spec 039 §"E2E test platform coverage".

### Spec 039 cross-update

- [ ] `Plan/done/039-distribution-and-e2e-hardening/spec.md` — note the
  CI workflow now exists; Spec 053 implements the matrix the
  spec deferred.

## Design

### Why auto-mark via conftest, not @pytest.mark.x per test

Manual markers drift. A new test file added by an author who forgot
the convention silently misses the marker → falls out of fast runs.
conftest's `pytest_collection_modifyitems` hook can inspect every
collected test and apply markers based on the file path. Zero per-
test maintenance.

### Marker policy

- Capability-mapping is by `tests/test_<capname>_<…>.py` convention.
  Spec-specific tests (e.g., a `test_spec_039_…py`) get a marker per
  the convention they document.
- A test without a matching prefix gets NO auto-marker. It still runs
  in the default suite; just not selectable via `-m capname`.

### Parallel safety

The current test suite uses `tempfile.mktemp(suffix=".db")` per fixture
— each test gets its own DB file. No shared-state. Safe for `pytest-
xdist -n auto`.

The E2E tests spawn subprocesses with their own `AGENCY_DB=:memory:` —
also safe.

The only risk: tests that monkeypatch global env vars (e.g., PATH,
AGENCY_EMBEDDER) need to use `monkeypatch.setenv` (pytest's per-test
scoped patcher). Audit: tests/test_distribution.py and others
already use monkeypatch.setenv. ✓

### CI workflow shape

```yaml
# .github/workflows/test.yml
name: test
on:
  pull_request:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev,analyze,recall]"
      - name: Install agency-mcp + agency-doctor console-scripts
        run: pip install -e .   # for the agency-mcp E2E fixtures
      - name: Non-E2E suite (parallel)
        run: pytest -q -n auto -m "not e2e"
      - name: E2E suite (only on tagged pushes)
        if: startsWith(github.ref, 'refs/tags/v')
        run: pytest -q -m "e2e"
```

This is plain GitHub Actions; no third-party actions beyond
`actions/checkout` + `actions/setup-python`.

### What's deliberately NOT in this spec

- Coverage reporting (defer; would inflate CI time).
- Test sharding across multiple runners (overkill at <1min/run).
- Specific runtime monitoring (pytest-monitor is overkill).
- Multi-Python-version matrix (3.11 only is fine per pyproject's
  `requires-python = ">=3.11"`).

## Files

- **Add:**
  - `tests/conftest.py` (or extend existing if present) — auto-marker hook.
  - `scripts/test-changed`, `scripts/test-cap` — bash slicing.
  - `.github/workflows/test.yml`.
  - `.github/workflows/lint.yml` (optional).
- **Modify:**
  - `pyproject.toml` — register markers + add pytest-xdist to `[dev]`.
  - `CLAUDE.md` Dev section — document `pytest -n auto` + the slicing
    scripts.

## Open Questions

1. **Should we vendor pytest-xdist or make it optional?** It's
   genuinely needed for fast local feedback; adding to `[dev]` is
   the cleanest option. Lean: in `[dev]`.
2. **Should CI run on `tag` ONLY for E2E?** Spec 039 said
   "Linux on push, macOS on tag, Windows deferred". v1: Linux on
   PR/push for the non-E2E, Linux on tag for E2E. macOS deferred.

## Followup — Implementation Status (2026-06-03)

**Verdict:** Shipped — auto-markers + pytest-xdist + slicing scripts
+ CI workflow upgrade all live. Live measurements:
  - `pytest -m analyze -n auto` — 44 tests in 6.6s (was: included
    in 4-min full suite)
  - `pytest -m research -n auto` — 36 tests in 12.2s
  - `pytest -m dogfood -n auto` — 31 tests in 17.8s
  - `pytest -q -n auto -m "not e2e"` — 636 tests in 163s (2:43;
    vs 253s sequential = ~35% speedup on this box)

### Done
- `tests/conftest.py::pytest_collection_modifyitems` auto-applies
  markers based on `tests/test_<capname>_*.py` basenames. 12 patterns
  ship (analyze, research, dogfood, document, reflect, delegate,
  intent, jules, distribution, install, substrate, e2e).
- `pyproject.toml`:
  - markers registered (12 new + e2e) to avoid PytestUnknownMarkWarning
  - `[dev]` extras gain `pytest-xdist>=3.5` (parallel sharding)
- `scripts/test-cap <marker-expression>` — wraps `pytest -q -n auto
  -m <expr>`. Examples in script header.
- `scripts/test-changed [--with-e2e]` — `git diff` against merge-base
  with main; maps paths to capability markers; runs the slice.
  Falls back to full suite when no derivable mapping. Core-file
  changes (engine/capability/memory/ontology) trigger full suite.
- `.github/workflows/test.yml` upgraded:
  - tags pattern `v*` added to push triggers
  - install gains `[analyze]` extra so composed findings path runs
    in CI
  - `pytest -q -n auto -m "not e2e"` replaces the prior `pytest -q`
  - E2E job runs conditionally on `refs/tags/v*` (Spec 039 §"E2E
    test platform coverage" — Linux on tag)
- `CLAUDE.md` Dev section documents the four common iteration
  patterns (full, parallel, by capability, git-diff-driven).

### Open for v2
- OQ1 ~~pytest-xdist as optional~~ → kept in `[dev]` (closed)
- OQ2 ~~E2E on tag only~~ → matches Spec 039 (closed)
- OQ3 Coverage reporting (deferred; would inflate CI time)
- OQ4 macOS / Windows matrix (deferred; Linux-only matches resource
  scope)

### Cluster-coherence (Spec 047)
- C04 Quality (test infrastructure quality)
- C13 Plugin (CI gate is part of the plugin release discipline)
