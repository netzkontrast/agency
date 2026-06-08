# dramatica-theory

## What
Apply Dramatica narrative theory (Phillips & Huntley, *Dramatica*, 4th ed., 2001) to story analysis, storyforming, drafting, and draft diagnosis. Dramatica models a complete story as one mind solving one problem, viewed through four throughlines (Overall Story, Main Character, Impact Character, Subjective/Relationship), with a structural model of 4 Classes / 16 Types / 64 Variations / 64 Elements selected to form a "storyform". Ships the full source book as nine thematic reference chunks plus an in-skill conceptual overview and storyforming quick-reference. Trigger phrases include — dramatica, story mind, storyform, throughline, grand argument story, archetype, protagonist antagonist guardian contagonist sidekick skeptic reason emotion, MC resolve, mental sex, story outcome judgment driver limit, signposts and journeys, crucial element, plot dynamics, phillips huntley, dramatica anwenden, throughlines bestimmen. Also for drafts that feel flat, characters feel unmotivated, or act structure is unclear.

## Why here
Snapshot of the user-skill `/mnt/skills/user/dramatica-theory/` from a Claude.ai
session (taken 2026-05-04). Version-controlled here so that other agents
(Claude Code, Jules, gemini-cli) can read, audit, and propose changes via PR.
The session-side copy under `/mnt/skills/user/` remains the live runtime
"upstream" until a sync-back protocol is defined.

## Top-level navigation
- [SKILL.md](./SKILL.md)
- [references/](./references/)
- [scripts/](./scripts/)

## Assumptions Log
- Skill-internal subfolders (e.g. `references/`, `scripts/`, `agents/`) are
  NOT given their own `readme.md`. Rationale: skills are governed by `SKILL.md`
  and Anthropic's skill-creator conventions; adding per-subfolder readmes would
  trigger "Structural Bloat" per `FRUSTRATED.md` (FL2 special-trigger). This
  drift is logged once here and once globally in the PR Frustration Log.
- The `name` and `description` shown above are extracted verbatim from
  `SKILL.md` YAML frontmatter; if the skill is updated in `/mnt/skills/user/`,
  this readme drifts until the next snapshot run.
