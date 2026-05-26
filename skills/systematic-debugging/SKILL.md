---
name: systematic-debugging
description: Use when encountering a bug, test failure, or unexpected behavior, before proposing fixes — gather evidence at boundaries and trace to the root cause.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# Systematic Debugging

## When to use
At the first sign of a bug or failure — before guessing at fixes.

## The chain (a walkable agency skill: `debug`)
`gather` (evidence) → `hypothesize` (hypothesis) → `trace` (root_cause) → `fix` (hard gate: fix_verified).

Gather evidence at component boundaries, form one hypothesis, trace the data flow backward to the root cause, then fix and verify. No cascading guesses.
