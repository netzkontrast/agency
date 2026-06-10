---
spec_id: "198"
slug: cli-mirror-chain-parity
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "079"
depends_on: ["079", "160", "146", "157"]
vision_goals: [5, 8, 1]
affects:
  - agency/cli.py
  - tests/test_cli_mirror_parity.py
---

# Spec 198 — CLI mirror ↔ code-mode parity proof

## Why

Spec 079 mirrors every capability verb as `agency <cap> <verb>` for
non-MCP agents (Goal 8), "code-mode stays canonical beneath it". Spec
160 adds `--chain`/`--fields`. The isomorphism CORE.md promises (the
same contract three ways — MCP/Skills/bash) needs a STANDING parity
proof: every verb reachable via code-mode is reachable via the CLI with
the same result shape, so a bash-only agent (Jules) is genuinely
first-class. The bash↔MCP isomorphism test exists for the wire verbs;
this extends it to the full mirror.

## Done When

- [ ] **Parity property test** — for every verb, a CLI call and a
      code-mode `execute` call return the same result shape (the
      isomorphism, asserted over the live registry).
- [ ] **`--chain` parity** — a YAML chain (Spec 160) equals the
      equivalent code-mode `execute` block.
- [ ] **Output honors the prefix split** (Spec 146) on both surfaces.
- [ ] **The architecture gate (Spec 157) asserts mirror completeness** —
      a new verb auto-appears on the CLI or fails CI.
- [ ] Test: the parity property over the registry; a missing mirror trips.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 160 (CLI chain/fields) is the surface; Spec 157 gate enforces.
- **output-budget chain** (146).

## Open questions

1. Property-test every verb (slow)? **Recommend**: sample + always-test
   the mutating verbs; full sweep nightly.
