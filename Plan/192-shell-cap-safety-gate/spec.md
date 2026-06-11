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

- [ ] **`shell.run` classifies reversibility** — returns a typed
      `ReversibilityVerdict{level:Literal["safe","cautious",
      "irreversible"], rule:str, evidence:str, driver_consulted:bool}`
      from a decidable rule set (destructive verbs: rm/mv/dd/
      git-push-force/curl-POST/truncate/`>` redirects to existing
      files, etc.). Spec 147 Driver consulted only when the decidable
      rules return `cautious` AND `[anthropic]` extra is installed.
- [ ] **Irreversible commands gate** via `ctx.elicit` (CORE.md) — the
      Lifecycle pauses at `input-required`; the outcome records a
      `Gate{intent_id, command, verdict, decision:Literal["allow",
      "deny","modify"], decided_by:str}` node.
- [ ] **`shell.run(confirm=True)`** bypass for durably-authorized
      contexts (the harness-in-harness ladder). The bypass is recorded
      on the Gate node with `decided_by:"durable_authorization"` so
      audits see it.
- [ ] **Typed refusal** (Spec 151 Codes) — `Codes.SHELL_GATED_DENIED`
      when the elicit returns deny; `Codes.SHELL_AMBIGUOUS` when the
      Driver is needed but unavailable.
- [ ] **Defense-in-depth invariants** (rule 8 relationships):
      `every shell.run with verdict.level=="irreversible" has a Gate
      node OR a confirm=True bypass record`; `Gate nodes never lack
      a decided_by field`; `gate decision recorded BEFORE the
      command executes` (timestamp ordering).
- [ ] **Failure-mode coverage** for classifier misses, shell-injection,
      and Driver-unavailable cases.
- [ ] Test: `rm -rf` gates; `ls` runs free; confirm bypasses; a
      shell-quoted irreversible (`bash -c 'rm -rf /'`) still classifies
      irreversible; the Driver-unavailable case returns
      `Codes.SHELL_AMBIGUOUS` without executing.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  an agent calls shell.run("rm -rf ./build")
        AND no confirm flag
When:   the safety gate evaluates
Then:   ReversibilityVerdict{level:"irreversible", rule:"rm_recursive_force",
        evidence:"rm -rf token", driver_consulted:False};
        ctx.elicit pauses the lifecycle at "input-required";
        if user replies "deny", Gate{decision:"deny",
        decided_by:"<user_id>"} is recorded AND shell.run returns
        Codes.SHELL_GATED_DENIED without executing rm

Given:  shell.run("ls -la") in any context
When:   the safety gate evaluates
Then:   ReversibilityVerdict{level:"safe", rule:"read_only_listing"};
        no gate; the command executes; no Gate node created

Given:  shell.run("curl -X POST https://api.example/orders -d ...")
        AND [anthropic] not installed
When:   the decidable rules return level:"cautious"
Then:   shell.run returns Codes.SHELL_AMBIGUOUS without executing;
        the agent must either install the Driver, mark confirm=True,
        or rephrase

Given:  a durably-authorized batch job calls shell.run("mv old new",
        confirm=True)
When:   the gate evaluates
Then:   Gate{decision:"allow", decided_by:"durable_authorization"}
        is recorded BEFORE execution; the command runs; the audit
        trail shows the bypass
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Classifier miss | `cat ./file > /etc/passwd` (redirect, not `rm`) | rule covers `>` redirects to existing paths | extend the rule set; add fixture |
| Shell injection via templates | `shell.define("foo", "{x}")` and x="; rm -rf /" | Spec 075 template-param sanitization + re-classify the expanded command | classifier runs on the FINAL command string, not the template |
| Driver unavailable for ambiguous | `[anthropic]` not installed, level == cautious | `Codes.SHELL_AMBIGUOUS` returned; nothing executes | refuse-by-default; never silently auto-allow |
| Gate bypass abuse | confirm=True used promiscuously | every bypass recorded with `decided_by`; audit query | rate-limit confirm=True per intent; surface in `boundary_use_audit` |
| Race on durable authorization | auth revoked mid-batch | gate re-checks auth state per call | per-call check, not session-cached |
| Classifier false positive | `mv old.tmp new.tmp` in scratch dir | confirm=True available; verdict.rule cited | tune rule with evidence; never weaken the default |

## Interconnects

- **LLM-driver chain** (147) for ambiguous classification.
- Spec 075 (shell.define) registry inherits the gate.
- Spec 151 (Codes) for the refusal shape.
- Spec 194 (shell.define LLM suggest) gates suggested templates
  through the same classifier.
- Spec 195 (event replay) records Gate nodes for replay/audit.
- Spec 192's `boundary_use_audit` consumer reads confirm=True usage
  patterns to surface abuse.
- Spec 187 (output lints) ensures the verdict shape is field-projectable.

## Open questions

1. Block-list or allow-list? **Recommend**: block-list of irreversible
   verbs (most commands are safe); the allow-list is the user's policy.
   Allow-listing every safe command would explode and trail real usage.
2. How is "durable authorization" granted? **Recommend**: an explicit
   `intent.authorize_shell(scope, ttl)` that writes an
   Authorization node the gate reads; never via env vars or config
   files (audit trail must show WHO and WHEN).
3. Should the Driver classifier ever be consulted for level=="safe"?
   **Recommend**: no — the decidable rules' safe verdict short-circuits;
   only "cautious" escalates. Otherwise every `ls` pays an API call.
