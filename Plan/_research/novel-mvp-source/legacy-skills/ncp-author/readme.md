# ncp-author

## What
>- Schema cheatsheet, canonical vocabulary (463 appreciations + 144 narrative_functions), validation rules, 10-stage authoring workflow, and runnable schema validator for NCP (ncp-schema.json v1.3.0). Actively co-invokes dramatica-theory (storyform decisions, why a Class/Type/Variation is correct) and dramatica-vocabulary (Dynamic-Pair validation, KTAD coherence, Element-Quad checks) at explicit workflow checkpoints — this skill owns JSON-IO and enum-compliance; the two Dramatica skills own meaning. Use when the user mentions NCP, narrative-context-protocol, ncp-schema, .ncp.json, 'convert to NCP', 'validate NCP', 'storyform JSON', or Subtxt export. Trigger auch auf Deutsch — Storyform anlegen, NCP-Datei validieren, NCP-Skelett, Storyform aus Outline. Do NOT use for general Dramatica theory (defer to dramatica-theory or dramatica-vocabulary) or prose drafting. Path A per TODO T-1.

## Why here
Snapshot of the user-skill `/mnt/skills/user/ncp-author/` from a Claude.ai
session (taken 2026-05-04). Version-controlled here so that other agents
(Claude Code, Jules, gemini-cli) can read, audit, and propose changes via PR.
The session-side copy under `/mnt/skills/user/` remains the live runtime
"upstream" until a sync-back protocol is defined.

## Top-level navigation
- [SKILL.md](./SKILL.md)
- [SPEC.md](./SPEC.md)
- [TODO.md](./TODO.md)
- [assets/](./assets/)
- [package-lock.json](./package-lock.json)
- [package.json](./package.json)
- [references/](./references/)
- [scripts/](./scripts/)
- [upstream/](./upstream/)

## Assumptions Log
- Skill-internal subfolders (e.g. `references/`, `scripts/`, `agents/`) are
  NOT given their own `readme.md`. Rationale: skills are governed by `SKILL.md`
  and Anthropic's skill-creator conventions; adding per-subfolder readmes would
  trigger "Structural Bloat" per `FRUSTRATED.md` (FL2 special-trigger). This
  drift is logged once here and once globally in the PR Frustration Log.
- The `name` and `description` shown above are extracted verbatim from
  `SKILL.md` YAML frontmatter; if the skill is updated in `/mnt/skills/user/`,
  this readme drifts until the next snapshot run.
