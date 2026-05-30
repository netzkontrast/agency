---
spec_id: "024"
slug: authoring-capabilities-discipline
status: draft
owner: "@agency"
depends_on: ["016", "020", "023"]
affects:
  - agency/capabilities/develop.py                       # NEW discipline + 2 verbs
  - agency/capabilities/plugin.py                        # complete lint_capability (paired with Spec 016 P4)
  - skills/authoring-capabilities/SKILL.md               # NEW — model-invoked discipline guide
  - skills/authoring-capabilities/references/            # NEW — synthesized external knowledge
  - docs/vision/CAPABILITY-AUTHORING.md                  # NEW — doctrine page (covers Spec 016 hints + Spec 023 render-slice rules)
  - tests/test_develop_authoring.py                      # NEW — RED-GREEN-REFACTOR coverage
  - tests/test_authoring_pressure_scenarios.py           # NEW — TDD-for-docs subagent pressure tests
estimated_jules_sessions: 0   # Inline implementation; the subagent pressure tests dispatch but are not Jules
domain: meta / self-improvement
wave: 3
---

# Spec 024 — Authoring-capabilities discipline (self-guiding development)

## Why

A new capability author today walks into an **implicit precedent zone**: nothing
in `develop.checklist` covers "I'm adding a new capability"; nothing in
`develop.reference` synthesizes the four external knowledge sources we depend on
(`superpowers:writing-skills`, `superpowers-developing-for-claude-code:{developing-claude-code-plugins,
working-with-claude-code}`, `claude-api`); nothing lints whether the docstrings
will produce useful render slices once Spec 023 is fully shipped.

The author is left to read `Plan/016-…/spec.md`, `Plan/023-…/spec.md`, four
external skills, and the precedent in `reflect.py` / `plugin.py` / `jules.py`
— and then hope they assembled the rules correctly. That's ~3000 tokens of
reading per new capability and the convergence guarantee is "trust me."

**This spec closes that loop with the same discipline the rest of the engine
uses**: a Lifecycle template + supporting verbs + a model-invoked SKILL.md, all
tested via the TDD-for-docs methodology from `writing-skills`. The user's
durable goal — captured as `intent:c374ac3d` — is **"make Development guiding
itself"**; this spec is the first step in that direction. Every authoring
session records `Reflection` nodes that surface back into the discipline's own
refinement (Spec 014 closes the rendering loop later).

## Done When

- [ ] **A new `authoring-capabilities` discipline** lands in
  `agency/capabilities/develop.py`'s `DEV_SKILLS` — 6 phases ending in a hard
  gate:
  1. **research** — author reads the doctrine page + render-slice rules
  2. **scaffold** — invoke `develop.scaffold_capability(name, kind)`
  3. **author** — write verbs with Hint #7 docstrings + correct role tags
  4. **lint** — invoke `develop.lint_capability(name)` — must pass
  5. **token-check** — `parse_slices(verb.doc)["brief"]` non-empty + ≤120 chars
  6. **commit** — hard gate: tests green, lint green, observation recorded
- [ ] **`develop.scaffold_capability(name, kind)`** verb. Kinds:
  - `light` (single-file, 1-3 verbs) — emits `agency/capabilities/<name>.py`
  - `medium` (single-file, 4+ verbs or ships templates) — same but with
    template/schema scaffolding
  - `heavy` (folder per Spec 016) — emits `agency/capabilities/<name>/`
    with `__init__.py` re-export pattern
  Returns `{result: path, artefact: {kind: capability-scaffold, name, path}}`.
- [ ] **`develop.lint_capability(name)`** verb. Composes:
  - **structural lint** (Spec 016 Phase 4): every verb has `Inputs:` /
    `Returns:` / `chain_next:` markers; role tag matches docstring shape
    (`effect` verbs name an external system; `transform` verbs are pure)
  - **render-slice lint** (Spec 023): `parse_slices(verb.doc)["brief"]` is
    non-empty + ≤120 chars (the token-budget gate); the first sentence
    cleanly cleaves (heuristic check via `_first_sentence`)
  - **token-budget lint**: simulated `search` containing only this
    capability's verbs returns ≤ N tokens where N = 20 × verb_count
  Returns `{ok, violations: [{verb, kind, msg, fix}], skipped: N}` (mirrors
  `plugin.lint_skill`).
- [ ] **`skills/authoring-capabilities/SKILL.md`** lands as the
  model-invoked discipline guide — Claude reads it when about to author a
  new capability. Frontmatter:
  ```yaml
  ---
  name: authoring-capabilities
  description: Use when authoring a new agency capability (or extending an
    existing one) — before writing the file, to scaffold per Spec 016
    folder/role/docstring conventions, then lint per Spec 023 render-slice
    rules. Discipline-enforcing: the lint gate must pass before commit.
  allowed-tools:
    - mcp__plugin_agency_agency__search
    - mcp__plugin_agency_agency__get_schema
    - mcp__plugin_agency_agency__execute
    - Read
    - Write
    - Edit
    - Bash
  ---
  ```
  Body: gerund-form per [anthropic-best-practices], description teaches WHEN
  (not WHAT — see `superpowers:writing-skills`'s CSO rules), under 200 lines,
  links to `references/` for deep material.
- [ ] **`skills/authoring-capabilities/references/`** with synthesized
  references (progressive disclosure per anthropic-best-practices):
  - `references/spec-016-hints.md` — the 11 hints, distilled with file:line
  - `references/spec-023-render-slices.md` — docstring → slice cleavage rules
  - `references/role-tags.md` — `act` / `transform` / `effect` decision tree
  - `references/folder-vs-file.md` — when to promote (≥3 sibling files rule)
  - `references/legacy-precedent.md` — `reflect.py` / `plugin.py` / `jules.py`
    cited as light / medium / heavy exemplars
- [ ] **`docs/vision/CAPABILITY-AUTHORING.md`** lands as the canon-adjacent
  doctrine page (Spec 016 Done When item) — humans read this; the skill
  references it. Folds Spec 016 Hints + Spec 023 render-slice into one
  authoritative doc.
- [ ] **TDD-for-docs validation** (the load-bearing test for THIS spec):
  - `tests/test_authoring_pressure_scenarios.py`:
    - **RED scenario**: dispatch a subagent to "Add a `notebook` capability
      with verbs `save(content, path)` and `list(directory)`" WITHOUT
      pointing at the discipline. Capture the resulting `capabilities/notebook.py`.
      Run `develop.lint_capability("notebook")` — assert violations exist
      (this is the baseline failure mode, documented verbatim).
    - **GREEN scenario**: dispatch the same task pointing at
      `skills/authoring-capabilities/SKILL.md`. Capture the resulting file.
      Run `develop.lint_capability` — assert `{ok: true}`.
    - **REFACTOR slot**: every rationalization the RED agent uses
      ("docstring is self-evident", "I'll add markers later", "this verb
      is too simple for the contract") becomes an entry in the discipline's
      rationalization table.
- [ ] **Self-improvement loop wired**: every walk of `authoring-capabilities`
  records a `Reflection` SERVES `intent:c374ac3d` (the durable
  "make Development guiding itself" goal). Spec 014, when shipped, projects
  these into spec amendments.
- [ ] `python -m pytest -q` stays green (currently 262 + the new test files).

## The discipline (phase graph)

```python
"authoring-capabilities": {
    "name": "authoring-capabilities",
    "kind": "discipline",
    "phases": [
        _phase(1, "research", ["doctrine_read", "render_rules_read"]),
        _phase(2, "scaffold", ["path"],
               invoke={"capability": "develop", "verb": "scaffold_capability"},
               inputs=["name", "kind"]),
        _phase(3, "author", ["verbs_written", "docstrings_compliant"]),
        _phase(4, "lint", ["lint_passed"],
               invoke={"capability": "develop", "verb": "lint_capability"},
               inputs=["name"]),
        _phase(5, "token-check", ["brief_under_budget"]),
        _phase(6, "commit", ["tests_green", "reflection_recorded"],
               gate="hard"),
    ],
},
```

Phase 2 and 4 are **bound** to verbs (like `review` is bound to
`delegate.fan_out`) — walking the discipline executes the verb, not merely
documents it. Phase 6's hard gate refuses to close until tests are green
AND a Reflection has been recorded against `intent:c374ac3d`.

## Files

- **Create:**
  - `skills/authoring-capabilities/SKILL.md` (~150 lines)
  - `skills/authoring-capabilities/references/spec-016-hints.md`
  - `skills/authoring-capabilities/references/spec-023-render-slices.md`
  - `skills/authoring-capabilities/references/role-tags.md`
  - `skills/authoring-capabilities/references/folder-vs-file.md`
  - `skills/authoring-capabilities/references/legacy-precedent.md`
  - `docs/vision/CAPABILITY-AUTHORING.md` (~300 lines)
  - `tests/test_develop_authoring.py` (verb-level unit tests)
  - `tests/test_authoring_pressure_scenarios.py` (subagent RED/GREEN)
  - `Plan/024-…/IMPLEMENTATION-PLAN.md` (Workflow output)
- **Modify:**
  - `agency/capabilities/develop.py` — add the discipline + 2 verbs
  - `agency/capabilities/plugin.py` — complete `lint_capability` (Spec 016 P4)

## Open Questions

1. **Skill location**: Claude Code skills live under `skills/<name>/`. The
   agency engine's discipline skills live as `DEV_SKILLS` dict entries in
   `develop.py`. Should `authoring-capabilities` exist BOTH places (skill
   for Claude to read; discipline for the walker to execute), or only as a
   discipline with a generated SKILL.md? **Default**: both, generated from
   the same source via `plugin.author_skill`. Same dogfooded pattern as
   `skills/help/SKILL.md` (which is regenerated by `install.py`).

2. **Subagent dispatch in `tests/test_authoring_pressure_scenarios.py`**:
   pressure tests dispatch real subagents (per writing-skills doctrine).
   That's network-bound and slow. Mark with `@pytest.mark.slow` and skip
   in CI unless `AGENCY_RUN_PRESSURE_TESTS=1`?

3. **Versioning the doctrine**: as the discipline evolves (per the
   self-improvement loop), how do we track which version of the rules a
   given capability was scaffolded against? **Default**: stamp the
   scaffold output with `# scaffolded via authoring-capabilities@<git-sha>`.

4. **Spec 016 Phase 4 timing**: Spec 024 depends on `lint_capability`.
   Either (a) Spec 024 ships `lint_capability` as part of its scope
   (effectively folding Spec 016 P4 into 024), or (b) Spec 024 blocks on
   Spec 016 P4. **Default**: (a) — fold. Spec 016 P4 was always paired
   with the consumer (Spec 023), and Spec 024 IS the consumer.

## Evidence (cites)

- `docs/vision/GOALS.md:32-34` — "Doctrine evolves through dogfooding" —
  the durable goal this spec serves.
- `docs/vision/CORE.md:18-30` — Capability = open set; this spec governs
  growth of that set.
- `Plan/016-…/spec.md` — 11 hints; Phase 4 (`lint_capability`) folded here.
- `Plan/023-…/spec.md` — render-slice contract (paired Done When).
- `agency/capabilities/develop.py:25-99` — current `DEV_SKILLS` (no
  authoring discipline).
- `agency/capabilities/reflect.py` — light single-file precedent.
- `agency/capabilities/plugin.py` — medium with helper functions
  precedent.
- `agency/capabilities/jules.py` + `_jules_*.py` — heavy folder-form
  precedent (will migrate per Spec 016 P6).
- `superpowers:writing-skills/testing-skills-with-subagents.md` — TDD
  methodology applied to the pressure-test design.
- `superpowers:writing-skills/anthropic-best-practices.md` — gerund
  naming, third-person description, "Use when..." convention.
- `superpowers-developing-for-claude-code:working-with-claude-code/references/skills.md`
  — `allowed-tools` frontmatter, model-invoked vs user-invoked,
  progressive disclosure pattern.
- `superpowers-developing-for-claude-code:developing-claude-code-plugins/references/common-patterns.md`
  — "MCP+Skill" pattern: capability provides power, skill provides
  judgment. Agency is exactly this shape; the new skill is the judgment
  layer over the existing MCP capabilities.
- `claude-api/shared/tool-use-concepts.md` — "Be prescriptive about *when*
  to call it" — informs the docstring rule about role-tag clarity.
- `claude-api/shared/prompt-caching.md` — frozen-prefix invariant —
  applies to scaffold templates (deterministic generation = stable cache).
- `reflection:9cd97a38` (MCP/CLI DB divergence) + `reflection:0a59e485`
  (missing MCP intent.capture) + `reflection:007ae70e` (venv footgun) —
  the kind of observation `intent:c374ac3d` will accumulate.

## Goal (this spec's contribution to `intent:c374ac3d`)

`intent:c374ac3d` is the durable "make Development guiding itself" goal.
Spec 024's contribution: **a new capability author can walk one
discipline and arrive at a render-slice-compliant capability** — no
implicit precedent, no four-skill-tab-read, no token waste in `search`.
Every walk leaves a Reflection that surfaces refinement opportunities
back into the discipline itself. The loop closes when Spec 014 lands —
at which point Reflections become spec amendments automatically.
