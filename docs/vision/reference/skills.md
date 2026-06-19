# Skills — schemas, the walker, derivation, emission

<!-- doc-source: agency/skill.py agency/skill_emit.py agency/disclosure.py agency/capabilities/skills/_main.py agency/capabilities/develop/_main.py -->
<!-- doc-hash: ec8a9849e9966069 -->

A **skill** is a phase-graph (a Lifecycle template) a capability ships on its
`ontology.skills`. Skills are how workflow guard-rails become *walkable* discipline
instead of prose. This page ties together the skill machinery spread across several
modules.

## The schema

```python
{"name": "tdd", "kind": "discipline",
 "applies_when": {"kind": "pattern", "pattern": "…", "confidence": 0.8},   # optional Matcher
 "phases": [
   {"index": 1, "name": "red", "produces": ["failing_test"], "verbs": ["…"]},
   …,
   {"index": N, "name": "confirm", "produces": ["done"], "gate": "hard"},  # terminal human gate
 ]}
```

## Two sources: authored vs derived (Spec 080/081)

- **Authored** — a capability declares real disciplines on `ontology.skills`
  (`develop`'s 11, `jules`'s 6, `intent`'s `critical-thinking`, `music`'s gated skills).
- **Derived** — a capability that authored *none* gets a `<cap>-usage` walk derived from
  its verbs (clustered by role, ≤6 phases, hard confirm gate) by `derive_usage_skill`
  in `as_capability()`. Authored skills override the derived default.

This guarantees **every capability ships at least one walkable skill**.

## Walking a skill (`agency/skill.py`)

`develop.skill_walk(name, inputs, resume_from)` walks a skill one phase at a time to its
first hard gate (`SkillRun`), recording each phase as provenance — progressive
disclosure, not a single dump.

## The projection (Spec 026)

- **`intent.suggests(called_capability, called_verb, called_state, floor)`** — projects
  the serving intent + last-state to the best applicable skill, evaluating each skill's
  `applies_when` **Matcher** (`pattern` regex, `verb_code` decider — cycle-checked — or
  `llm_select`, which asks the `llm` Driver, Spec 092 G3).
- **`skills.find` / `render` / `lint` / `rank`** — the first-class `skills` capability to
  enumerate, read, validate, and rank skills.
- **`skills.index`** — promotes `ontology.skills` into the graph as `Skill` + `Phase`
  nodes (queryable via `analyze.graph`).

## Emission (`skill_emit.py`, `disclosure.py`)

`emit_skill` renders a per-capability **Agent Skill** to `skills/<cap>/SKILL.md` (the
L1/L2/L3 tiers: description → overview/verb table/walk section → `references/<verb>.md`),
**derived** from the docstring + verb registry. `disclosure.py` governs the tiered
discovery budget (Spec 068). `plugin.publish_skill` packages an emitted skill for the
Anthropic Skills API (Spec 083).

## Related

- The walker discipline lives in the `develop` capability ([../../guide/capabilities.md]).
- The token budget the emission respects: [token-economy.md](token-economy.md).
