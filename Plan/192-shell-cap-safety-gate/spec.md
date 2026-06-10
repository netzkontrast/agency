---
spec_id: "192"
slug: shell-cap-safety-gate
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "073"
depends_on: ["073", "075", "147", "151"]
vision_goals: [3, 5]
affects:
  - agency/capabilities/shell.py
  - tests/test_shell_safety_gate.py
---

# Spec 192 — shell capability safety gate

## Why

Spec 073 ships the `shell` capability (run/filter/templates) and Spec
075 adds a definable command registry. `shell.run` executes arbitrary
bash — the `claude-api` agent-design guidance is explicit that
hard-to-reverse actions should be gateable (a dedicated tool gives the
harness an action-specific hook). The shell cap should classify a
command's reversibility and gate destructive ones behind an `elicit`
(CORE.md: gates are elicit steps), so a bash-only agent (Goal 8) can't
silently `rm -rf`.

## Done When

- [ ] **`shell.run` classifies reversibility** — a decidable rule set
      (destructive verbs: rm/mv/dd/git-push-force/curl-POST…) flags a
      command as `irreversible`; optional Spec 147 judgement for
      ambiguous cases.
- [ ] **Irreversible commands gate** via `ctx.elicit` (CORE.md) — the
      Lifecycle pauses at `input-required`; the outcome records a Gate.
- [ ] **`shell.run(confirm=True)`** bypass for durably-authorized
      contexts (the harness-in-harness ladder).
- [ ] **Typed refusal** (Spec 151 Codes) when gated-and-denied.
- [ ] Test: `rm -rf` gates; `ls` runs free; confirm bypasses.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) for ambiguous classification.
- Spec 075 (shell.define) registry inherits the gate.
- Spec 151 (Codes) for the refusal shape.

## Open questions

1. Block-list or allow-list? **Recommend**: block-list of irreversible
   verbs (most commands are safe); the allow-list is the user's policy.
