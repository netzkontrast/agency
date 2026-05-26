---
name: test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code — write the failing test first, watch it fail, then write minimal code.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# Test-Driven Development

## The Iron Law
**No implementation without a failing test first.** In the agency `tdd` skill the
phase ordering enforces it — `green` is unreachable until `red` produced a
failing test.

## The chain (a walkable agency skill: `tdd`)
`red` (failing_test) → `green` (implementation) → `refactor` (refactored) → `verify` (hard gate: tests_pass).

```bash
python -m agency.cli --db dev.db execute --code 'return await call_tool("capability_develop_checklist", {"discipline": "tdd", "intent_id": INTENT})'
```

Wrote code before the test? Delete it and start over.
