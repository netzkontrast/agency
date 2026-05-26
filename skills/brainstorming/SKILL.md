---
name: brainstorming
description: Use when starting any creative or design work — a new feature, capability, or behavior change — before writing code, to explore intent and requirements first.
allowed-tools:
  - Read
  - Write
  - Edit
---

# Brainstorming

## When to use
Before building anything new. Turn a vague idea into a concrete, agreed design.

## The chain (a walkable agency skill: `brainstorm`)
`explore` (questions, assumptions) → `present` (design, tradeoffs) → `confirm` (hard gate).

Drive it via the engine's skill walker, or get the steps with the `develop` capability:

```bash
python -m agency.cli --db dev.db execute --code 'return await call_tool("capability_develop_checklist", {"discipline": "brainstorm", "intent_id": INTENT})'
```

Source: superpowers `brainstorming` · SuperClaude `/sc:brainstorm`. Stop at the hard gate until the human confirms the design — do not jump to implementation.
