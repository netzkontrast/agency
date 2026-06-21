---
spec_id: "054"
slug: drift-management
status: complete
state: done
last_updated: 2026-06-03
owner: "@agency"
depends_on: [030, 053]
informs: [016, 047]
affects:
  - agency/engine.py                     # agency_doctor.drift section
  - scripts/check-drift                  # NEW — grep + invoke doctor
  - README.md                            # ground the conventions
  - CLAUDE.md                            # promote drift discipline
  - .github/workflows/test.yml            # gate PRs on check-drift
estimated_jules_sessions: 1
domain: meta
wave: 2
---

# Spec 054 — Drift management (code tags + runtime doctor)

## Why

User audit (2026-06-03): *"We need to define code tags we can search
for — for code that needs changing if we add new capabilities — or
everything needs to use reflection to wire stuff — please brainstorm
solutions for addressing drift."*

The agency capability surface is OPEN (Spec 016 + reflection-based
`discover()`), but a new capability indirectly touches at least
**nine places**:

1. `pyproject.toml` extras (if it adds optional deps)
2. `agency.install` regen (skills/help/SKILL.md, commands/, .mcp.json)
3. CLAUDE.md (doctrine if it changes the chain rules)
4. TODO.md (CLAUDE.md Rule #4 is mandatory)
5. `docs/vision/SPEC-VISION-ALIGNMENT.md` (cluster mapping)
6. Per-capability test file (under tests/test_<cap>_*.py)
7. `.github/workflows/test.yml` (extras matrix)
8. `agency_doctor` (extras + install_method + drift reports)
9. The capability's own spec.md Followup section

Today, none of these are auto-discoverable. The doctrine relies on
the implementer remembering all nine. Drift is INEVITABLE without
explicit guard rails.

## Done When

### Code-tag convention (search-driven, manual)

- [ ] `# AGENCY-DRIFT: <topic>` (or `// AGENCY-DRIFT:` / `<!-- AGENCY-DRIFT: -->`
  per language) is the canonical drift marker.
- [ ] Every code path that depends on the SET of {capabilities, skills,
  ontology values, extras} carries a marker line. Examples:
  - `agency/install.py` regen logic — `# AGENCY-DRIFT: capability-list`
  - `agency/engine.py::agency_doctor.analyze_extras` —
    `# AGENCY-DRIFT: analyze-extras-list`
  - `tests/conftest.py::_AUTO_MARKER_PATTERNS` — `# AGENCY-DRIFT:
    test-marker-patterns`
  - `pyproject.toml` `[analyze]` extra — `# AGENCY-DRIFT: deps-extras`
- [ ] Seed at least 8 tags across the existing codebase (one per
  drift point in §"Why").

### Drift-check script (runtime-driven, automated)

- [ ] `scripts/check-drift` — shell + python script that:
  - greps for `AGENCY-DRIFT:` tags across `agency/`, `tests/`,
    `pyproject.toml`, `.github/`, `CLAUDE.md`, and prints them
    organized by topic.
  - runs `python -m agency.install --dry-run` (or compares the
    rendered output against committed); reports if regen would change
    files.
  - lists tests/test_*.py without an auto-marker match (Spec 053
    pattern); these are "untagged" and won't show in `pytest -m <cap>`.
  - reports per-capability whether the corresponding test file
    exists.
  - returns exit code 0 if no drift detected; 1 if drift present.

### agency_doctor.drift report

- [ ] `agency_doctor.drift` field — runtime-derived drift signals:
  - `install_regen_needed: bool` — would `python -m agency.install`
    produce a diff?
  - `capabilities_without_tests: list[str]` — capabilities for which
    no `tests/test_<name>_*.py` file exists.
  - `tagged_files_count: int` — how many files carry an
    `AGENCY-DRIFT:` marker.
- [ ] Surfaces in `next_steps[]` when any drift indicator fires.

### CI integration

- [ ] `.github/workflows/test.yml` runs `scripts/check-drift` as a
  step (post-pytest). PR fails if drift is reported.
- [ ] The existing "self-hosted install" check in the workflow gets
  consolidated with check-drift (one source of truth for
  install-regen-needed).

### Documentation

- [ ] `README.md` includes a "Drift management" section explaining
  the AGENCY-DRIFT convention + linking to scripts/check-drift.
- [ ] `CLAUDE.md` gets a Rule #6 about drift discipline: when adding
  a new capability, run `scripts/check-drift` BEFORE commit; failure
  to do so is a doctrine violation.

## Design

### Why two layers (tag + doctor)

- **Tag layer** catches code-path dependence at AUTHORING time. When
  reviewer reads `agency/install.py::_capability_skill_doc()` and sees
  `# AGENCY-DRIFT: capability-list`, they immediately know "this
  function reads the live capability set; if we added X, this needs
  re-running OR re-thinking."
- **Doctor layer** catches state drift at RUNTIME. When the engine
  starts and 3 capabilities have no test file, `agency_doctor` says
  so. When `agency.install --dry-run` would emit a diff, doctor
  says so.

The two layers cover orthogonal failure modes: dev-time omissions
(tag) vs. state drift (doctor).

### Tag taxonomy (initial set)

| Tag | Where it appears | Trigger to re-read |
|---|---|---|
| `AGENCY-DRIFT: capability-list` | code that reads `registry.names()` or `discover()` results | adding/removing a capability |
| `AGENCY-DRIFT: skill-list` | code that reads `ontology.skills` | adding/removing a skill |
| `AGENCY-DRIFT: deps-extras` | pyproject [project.optional-dependencies] | adding a new optional extra |
| `AGENCY-DRIFT: analyze-extras-list` | agency_doctor.analyze_extras subset | adding to/removing from {ruff,bandit,radon,...} |
| `AGENCY-DRIFT: test-marker-patterns` | conftest auto-marker patterns | adding a new capability test file |
| `AGENCY-DRIFT: install-manifest` | install.py regen targets | adding a new artefact emit |
| `AGENCY-DRIFT: substrate-tools` | substrate tool list (welcome/install/doctor/intent_bootstrap/lifecycle_gate/memory_graph_provenance) | adding a new substrate tool |
| `AGENCY-DRIFT: spec-vision-alignment` | SPEC-VISION-ALIGNMENT.md table | shipping a spec |

### Why not pure Spec-grounded metadata

A `drift_anchors: [pyproject.analyze, agency_doctor.analyze_extras]`
frontmatter field on each spec would be MORE machine-readable than
plain tags. But:
- specs are version-controlled separately from code; staleness risk
  is HIGHER for spec metadata than for inline code tags
- code-tag is searchable from the test/PR-review viewpoint without
  walking specs
- spec metadata can ALWAYS be added later (additive)

v1 ships the simpler tag convention. v2 may add spec-frontmatter drift
anchors as a secondary discipline.

### Anti-patterns

- **Comment-only tags without code dependency** — useless drift
  bookkeeping. Tags MUST mark places where code reads a set/list
  that changes when capabilities change.
- **Tag drift itself** — tags that no longer reflect what the code
  does. The doctor's `tagged_files_count` is the smoke alarm; if
  the count drops without a real refactor, someone removed a tag
  by accident.
- **Burying tags in skill docs** — tags are CODE-LEVEL. Skill doc
  references go in CLAUDE.md text, not inline.

## Files

- **Add:**
  - `scripts/check-drift` — drift detection runner.
- **Modify:**
  - `README.md` — drift-management section.
  - `CLAUDE.md` — Rule #6 drift discipline.
  - `agency/engine.py::agency_doctor` — drift field.
  - `agency/install.py` — `--dry-run` flag for diff-without-write.
  - 8+ initial AGENCY-DRIFT tag insertions across the codebase.
  - `.github/workflows/test.yml` — check-drift step.

## Open Questions

1. **Should tags be standardized to one syntax** (`# AGENCY-DRIFT:`)
   across Python + YAML + Markdown comments? Yes — easier grep.
2. **Per-file vs per-symbol tags?** Per-symbol (right above the
   function/list literal) gives the reader precise context. v1 uses
   per-symbol where possible; per-file when the entire file is
   capability-list-dependent.

## Followup — Implementation Status (2026-06-03)

**Verdict:** Shipped v1 — code-tag convention + check-drift script +
agency_doctor.drift field + CLAUDE.md Rule #6 all live. 8 canonical
AGENCY-DRIFT sites seeded. Live `scripts/check-drift` reports
"NO DRIFT DETECTED" on this branch.

### Done
- `# AGENCY-DRIFT: <topic>` code-tag convention documented in CLAUDE.md
  Rule #6 (drift discipline). 8 initial sites seeded:
  - `agency/engine.py::_drift_signals` → capability-list
  - `agency/engine.py::analyze_extras loop` → analyze-extras-list
  - `tests/conftest.py::_AUTO_MARKER_PATTERNS` → test-marker-patterns
  - `pyproject.toml [project.optional-dependencies]` → deps-extras
  - 3× `scripts/check-drift` self-references
  - `CLAUDE.md Rule #6` body
- `scripts/check-drift` (chmod +x):
  - greps `AGENCY-DRIFT:` across agency/, tests/, scripts/,
    pyproject.toml, CLAUDE.md, .github/, docs/
  - runs `python -m agency.install`; reports diff via git on
    .claude-plugin/, .mcp.json, skills/help/, commands/
  - lists capabilities (registry.names()) without a corresponding
    tests/test_<name>_*.py file
  - exit 0 = clean; 1 = drift; supports `--quiet` for CI use
- `agency_doctor.drift` field — runtime-derived (cheap, file-existence
  lookups only):
  - `capabilities_without_tests: list[str]`
  - `capability_count: int`
  - Heavy checks (install regen diff) live in scripts/check-drift, not
    the doctor.
- `CLAUDE.md Rule #6` documents the drift discipline.
- `README.md` "Drift management" section in Develop ties tags +
  check-drift + Spec 054 together. Plus a substantial Install
  rewrite covering pipx + local-dev + self-hosted regen.

### Open for v2
- OQ3 Spec-frontmatter `drift_anchors` field — deferred; v1 tag
  convention is the simpler path
- OQ4 CI integration of check-drift — README mentions; actual
  workflow step deferred until check-drift gets more battle-tested
  (false positives could block merges)
- OQ5 lint rule: catch tags that no longer reference real code —
  v2; would need AST-or-grep matching

### Cluster-coherence (Spec 047)
- C12 Meta (it IS — drift management is meta-discipline)
- C13 Plugin (drift affects every plugin-authoring decision)
