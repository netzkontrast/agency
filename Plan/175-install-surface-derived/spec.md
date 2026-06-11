---
spec_id: "175"
slug: install-surface-derived
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "061"
depends_on: ["061", "149", "148", "170"]
vision_goals: [5, 4]
affects:
  - agency/install.py
  - tests/test_install_surface_derived.py
---

# Spec 175 — install-surface fully derived

## Why

Spec 061 (install-surface-refresh) made `marketplace.json`'s
description read the live registry (cap count + first-7 surface). The
enhancement layer extends this: the ENTIRE install surface
(`marketplace.json`, the README capability table, the slash-command
family from Spec 148, the `userConfig` extras list) should DERIVE from
the live registry + the installed extras, so adding a capability or an
extra updates the install surface with zero hand-edits (the drop-in
bar, CLAUDE.md).

## Done When (measurable invariants — rule 8)

- [ ] **Typed surface map: `InstallSurface{marketplace_desc: str,
      readme_capability_rows: list[Row], slash_commands:
      list[CommandFile], userconfig_extras: list[str], generated_at:
      timestamp}`** — the rendered install surface as one object;
      every field derives from a named source.
- [ ] **Invariant: `set(readme_capability_rows.name) ==
      set(registry.capabilities)`** — derived; a new capability
      auto-adds its row, a removed one auto-drops.
- [ ] **Invariant: `set(userconfig_extras) ==
      set(pyproject.optional_dependencies.keys())`** — derived from
      pyproject.toml; a new extra auto-appears.
- [ ] **Invariant: `set(slash_commands.name) ⊇ {/agency,
      /agency-doctor} ∪ {/agency-<skill> | skill ∈ walkable_skills}`**
      — every walkable skill (Spec 081) gets a `/agency-<skill>` file
      (Spec 148 family).
- [ ] **Invariant: install-time and commit-time regen produce
      byte-identical surface** for the same registry hash + pyproject
      hash + skill set — relationship; the two paths must agree.
- [ ] **Invariant: `check-doc-drift` fails when the rendered README
      table diverges from the live registry** — Spec 149 doc-source
      marker; no hand-edits silently accepted.
- [ ] **Failure mode (regen path):** `agency install` mid-write
      crash leaves the prior surface intact — write to a tempfile +
      atomic rename; never a half-rendered README. Failure emits
      `Codes.INSTALL_REGEN_PARTIAL` Reflection.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  capability set = {analyze, develop, research, ...};
        pyproject extras = {analyze, anthropic, dev};
        walkable skills = {develop.brainstorm, dispatch.decision, ...}
When:   `agency install` runs
Then:   marketplace.json description names "N capabilities" derived
        from len(registry); README has a row per capability; the
        commands/ folder has /agency, /agency-doctor, and one
        /agency-<skill>.md per walkable skill; userConfig extras
        contains anthropic + analyze + dev

Given:  a developer adds `agency/capabilities/music/_main.py` +
        commits without running `agency install`
When:   CI runs `check-doc-drift`
Then:   FAILS — README missing the `music` row; drift gate points at
        the offending source; PR cannot merge until install regens

Given:  `agency install` crashes mid-write (e.g. disk full)
When:   the user reruns
Then:   the prior README is still intact (tempfile + atomic rename);
        INSTALL_REGEN_PARTIAL Reflection points at the failed render
```

## Failure modes

| Failure | Install response |
|---|---|
| Regen crashes mid-write | atomic rename guarantees prior surface intact + `INSTALL_REGEN_PARTIAL` |
| README hand-edit divergence | `check-doc-drift` fails CI; Spec 149 gate |
| New capability without a SkillDoc | Spec 163 derive lint catches; row still generates |
| Install-time vs commit-time disagree | byte-equality invariant fails; one path is bugged — both must agree |
| pyproject extra renamed | userConfig auto-updates; the slash command for an obsolete extra removed (open-set evolution) |

## Interconnects

- **Drift-derivation chain** (149) — `check-doc-drift` gates every
  surface field.
- **UX-onboarding chain** (148/176) — slash commands derive here;
  SessionStart consumes the resulting `/agency-onboard` file.
- Spec 170 (doctor) reports the derived surface freshness
  (`generated_at` vs current registry hash).
- Spec 163 (progressive-disclosure closure) supplies the SkillDoc
  rows the README table renders.
- Spec 177 (plugin-reference audit) gates the generated slash command
  files' frontmatter shape.
- Spec 165 (micro-extensions closure) — `branch.commit_smart` +
  `develop.estimate` rows appear here once their fragment verdicts
  resolve.
- Spec 151 (Codes coverage) supplies `INSTALL_REGEN_PARTIAL`.

## Open questions

1. Derive at install-time or commit-time? **Recommend**: both —
   commit-time gate (drift) keeps the repo honest; install-time regen
   keeps a fresh clone correct; the byte-equality invariant proves
   they agree.
2. Render template — vendored or inline? **Recommend**: vendored
   Templates (Spec 060/174) so the README structure itself is
   versioned + Schema-validated.
3. What about consumers reading the README on GitHub between
   regens? **Recommend**: a CI step regenerates + commits the README
   on every merge to main; the merge-time render is the canonical
   public view.
