---
name: skill-creation
description: Use when creating a new skill or editing an existing one, before deploying it — to apply the RED-GREEN-REFACTOR discipline and validate the SKILL.md against the CSO rules.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# Skill Creation

## Overview

Create skills the way you write tested code. This is a complete port of the
superpowers `writing-skills` discipline into the agency engine: **NO SKILL
WITHOUT A FAILING TEST FIRST**. The `skill-creation` skill enforces the Iron Law
*structurally* — its phase ordering means you cannot reach GREEN (authoring)
until RED (the failing baseline) has produced its outputs.

## When to use

- You're writing a new skill (a reusable technique/pattern/reference).
- You're editing an existing skill (same discipline applies).
- You want to validate a SKILL.md's frontmatter before shipping.

## The cycle (enforced by phase ordering)

`red-baseline → green-author → lint → refactor → deploy (hard gate)`

- **RED** — run a pressure scenario WITHOUT the skill; record the exact
  rationalizations the agent used (the baseline).
- **GREEN** — author the minimal SKILL.md that addresses those rationalizations
  (the engine's `author_skill` verb renders strict frontmatter + body).
- **lint** — `lint_skill` is the CSO rules as compute: kebab-case ≤64 name,
  description ≤1024 starting with "Use when…", third person.
- **REFACTOR** — close new loopholes; build the rationalization table + red flags.
- **deploy** — a hard gate: STOP and verify before moving on.

## Drive it (code-mode; MCP / Skill / bash-only all identical)

```bash
python -m agency.cli --db skill.db search "lint skill"
python -m agency.cli --db skill.db execute --code '
return await call_tool("capability_plugin_lint_skill", {"name": "my-skill", "description": "Use when ...", "intent_id": INTENT})
'
```

## Common mistakes

- Writing the skill before the baseline — the ordering forbids it; delete and restart.
- A `description` that summarizes the workflow — it becomes a shortcut Claude takes instead of reading the skill. Describe ONLY when to use.
- First-person voice in the description — the linter flags it.
