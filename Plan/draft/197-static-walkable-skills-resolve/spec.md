---
spec_id: "197"
slug: static-walkable-skills-resolve
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "078"
depends_on: ["078", "081", "152", "190", "200", "149", "157"]
vision_goals: [4, 1]
affects:
  - Plan/draft/078-static-walkable-skills/spec.md
  - tests/test_static_walkable_resolve.py
---

# Spec 197 — static-walkable-skills, resolve the clarification

## Why

Spec 078 (static-walkable-skills) is a research-first draft that "needs
clarification". The clarification is now answerable from the shipped
081 (walkable usage-skills derive) + 152 (typed Skill) + 190 (skill
reconciliation): the open question was whether a skill's phase graph
can be STATIC (authored once) vs DERIVED (from the docstring). The
answer is the 081 model — derived by default, authored override —
so 078 resolves to "fold into 081's derive model, document the override
path, cancel the standalone static-skill concept."

## Done When

- [ ] **Spec 078 gets an explicit verdict** — folded into the 081
      derive model with a documented authored-override path (not a new
      static-skill mechanism). The verdict row in TODO.md flips to
      `Closed/Superseded → 081` with a one-line pointer.
- [ ] **`Skill.override_path` field** on the Spec 152 typed Skill
      records the optional authored phase graph path; `None` =>
      derived (Spec 081 default).
- [ ] **Invariant — precedence relationship**: when both exist,
      `effective_skill == override` AND
      `derived_skill_payload_tokens >= override_payload_tokens / 2`
      (the override is not pathologically larger than what derivation
      would yield — guards against override-as-escape-hatch).
- [ ] **Invariant — derive-by-default**: across the live capability
      registry, `count(skills_with_override) < count(skills_total) * 0.2`
      — override is the rare exception, not the norm; a regression
      (overrides outpacing derives) trips the architecture gate (Spec
      157).
- [ ] **Invariant — derive output unchanged**: for every capability
      without an override, the derived SkillDoc bytes are byte-stable
      across `agency_welcome` calls (Spec 146 prefix discipline holds).
- [ ] Test: authored override wins over derived; default derive
      unchanged; precedence invariant asserted over a fixture cap.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  capability X has a docstring that derives a 4-phase walk
        AND no override file exists
When:   develop.skill_walk("intent-id", "x-usage") runs
Then:   effective walk == derived walk
        AND derived payload bytes are byte-stable across calls

Given:  capability X gains skills/x-usage/override.yaml with 3 phases
When:   develop.skill_walk runs again
Then:   effective walk == override (3 phases)
        AND derived skill is still computed but not delivered
        AND Spec 149 drift check flags any docstring change that would
            have produced a derived walk diverging from the override

Given:  override count > 20% of capability count
When:   architecture gate (Spec 157) runs
Then:   CI fails — overrides have become the norm, not the exception
```

## Interconnects

- Spec 081 (walkable usage-skills) is the resolution surface.
- Spec 152 (typed Skill) + Spec 190 (reconciliation) are the model.
- Spec 200 (adaptive phase budgeting) — overrides participate in the
  same per-phase token budget as derived walks; adaptive selection
  honors the override path when present.
- Spec 149 (derived-doc drift) — docstring-vs-override divergence is
  the drift signal.
- Spec 157 (architecture gate) — enforces the override-rarity
  invariant.
- Spec 199 (skill round-trip) — overrides published as Agent Skills
  validate through the same round-trip; trigger-quality applies to
  both derived and authored.
- Spec 203 (graph query) — the override/derived precedence chain is
  queryable as Lifecycle provenance.
- Spec 205 (substrate hardening) — the override-rarity invariant is a
  standing check, not a one-time pass.

## Open questions

1. Any genuine static-only need? **Recommend**: no — the derive+override
   model covers it; cancel the standalone concept.
2. Where do override files live? **Recommend**:
   `agency/capabilities/<cap>/skill_override.yaml` colocated with the
   capability — keeps the cap a single drop-in folder (CLAUDE.md
   drop-in bar).
3. How does the engine signal "override exists but stale"?
   **Recommend**: Spec 149 drift check + a `WARN` lifecycle event when
   the docstring's derivable structure has diverged from the override
   shape; never silently auto-merge.
