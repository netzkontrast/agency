---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or opening a PR — run the command and confirm the output first.
allowed-tools:
  - Read
  - Bash
---

# Verification Before Completion

## The rule
Evidence before assertions. Never claim "done/fixed/passing" without running the
verification and reading its output.

## The chain (a walkable agency skill: `verify`)
`identify` (command) → `run` (output) → `confirm` (hard gate: evidence_matches).

The hard gate blocks the completion claim until the fresh output matches it.
