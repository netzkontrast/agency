# AGENCY_PROTOCOL.md — remote async agent doctrine

Applies to any **remote async agent** the agency drives — Jules today;
others tomorrow (Codex, Devin, OpenHands, …). Formerly `JULES_PROTOCOL.md`;
generalised because the failure modes and recovery flow are universal:
the agent runs in its own VM, you only see its outputs via a REST API,
and the gap between "agent says it's done" and "work is on origin" is
where reliability lives or dies.

Read [`AGENTS.md`](AGENTS.md) first for the repo-wide conventions.

---

## §1 — `COMPLETED ≠ done`

A session reading `state=COMPLETED` with `has_outputs=True` does **not**
imply the work is published. The canonical silent-fail variants:

1. **COMPLETED + no branch on origin.** Publish step never ran — the
   agent finished the work in its VM but never called `submit(...)`.
   Most common variant.
2. **COMPLETED + branch on origin + no PR open.** Work pushed but no
   pull request opened. `automationMode` was misconfigured or the agent
   skipped the PR step.
3. **COMPLETED + branch on origin + agent reports fabricated SHAs in
   chat.** Agent confabulates progress. Trust `git ls-remote`, never the
   in-chat SHAs.

**The verification rule:** never declare done without checking the remote
yourself. `git ls-remote origin <branch>` is the source of truth.

## §2 — Name the publish tool

Every dispatch prompt MUST explicitly name the agent's publish tool by
its canonical symbol. Prose like "open a PR when you're done" leaves
the work in the VM. For Jules the canonical pair is:

```
pre_commit_instructions()
submit(branch_name="...", commit_message="...", title="...", description="...")
```

The agency's `jules.lint_prompt(text, must_name=[...])` predicate
enforces this — Phase 3 of the `jules-protocol-preamble` skill walks it
before any dispatch. (See `Plan/013-…/DESIGN.md`.)

**Related Jules tools the canon expects you to name in the prompt**
(catalogued in full in `agency/capabilities/_jules_reference.md` §3):

- `replace_with_git_merge_diff` — preferred multi-line edit primitive
  (Git merge-conflict markers; avoids JSON-escape failures).
- `request_code_review()` — triggers the Jules Critic before `submit`,
  catches edge cases inside the session rather than at PR-review time.

Naming these in the dispatch prompt reduces hallucinated edits and
raises per-session quality, but only `pre_commit_instructions` and
`submit` are load-bearing for the silent-fail guard.

## §3 — Scope discipline

- The dispatch carries an `affects:` list. **It is a hard allow-list.**
  If the agent needs to touch a path outside it, the doctrine is:
  emit a `BLOCKED:` PR explaining what extra paths are needed and stop.
  Don't silently expand.
- **No source copying.** Don't paste research-doc contents into PR
  bodies or commits — cite the source path, let reviewers fetch it.
- TDD when the task has a clear acceptance: RED test first, then GREEN
  implementation, then REFACTOR. Each transition is a separate commit
  when feasible.

## §4 — Blocking ask vs status update

- Questions go through the **blocking** ask tool. For Jules:
  `request_user_input(message)` — NEVER `message_user(...)`, which is
  status-only and the agent keeps going (probably down a wrong path).
- One open question at a time. Stack of questions = the agent waits for
  the user; multiple stacked questions is confusing and slow.
- If the question is "the next step is ambiguous", prefer to emit a
  `BLOCKED:` PR with the options enumerated.

## §5 — Recovery flow on silent-fail

When `verify` reports no branch on origin despite COMPLETED state:

1. **Probe** the agent: "your branch isn't on origin — push and reply
   with the PR URL, or reply `EMPTY` if you have nothing to publish."
   Send via `message` (status channel — the question is NOT for the
   user, it's for the agent to act on).
2. **Wait** for the probe response. Cadence: ~5 min × 3 attempts
   (config: `agency.recovery_probe_budget`).
3. **Outcome routing:**
   - Reply contains `EMPTY` → record outcome=empty on the
     `JulesSession` node, close out.
   - Reply contains a PR URL → re-verify via GitHub MCP
     (`list_branches`); record `pr_url` on the session.
   - No reply within budget → **patch-extract recovery**: pull the
     ChangeSet activity from the activity stream, parse its `gitPatch`
     via `agency.capabilities._jules_patch.build_recovery_plan(...)`,
     execute the resulting `[{tool, args}]` ops via GitHub MCP.
4. **Record** the outcome on the `JulesSession` node so the bi-temporal
   graph carries the recovery provenance.

## §6 — Network errors are orthogonal to session errors

- TLS / clock-skew flakiness on the agent's REST API path is a
  `network_error` `WatchEvent` — retry with exponential back-off; never
  classify as session failure or terminal-stuck.
- GitHub MCP runs on a different network path; use it as the **fallback
  verification channel** when the agent's API itself is unreachable.
- The watcher state machine treats `network_error` as transient + safe
  to retry; `session_error` as a real terminal state requiring
  recovery routing per §5.

## §7 — Automation modes and plan-approval gates

(Specific to Jules; analogous flags exist for other agents.)

| `require_plan_approval` | `automation_mode` | Use when |
|---|---|---|
| `True` (default) | `""` (manual PR confirm) | Doctrine default — plan is reviewed, then PR is confirmed. |
| `True` | `"AUTO_CREATE_PR"` | Agency drives Jules end-to-end; plan gated, PR auto-opens. **Opt-in for spec-driven dispatch.** |
| `False` | `""` | Legacy / pre-spec-012 shape. |
| `False` | `"AUTO_CREATE_PR"` | **Zero-touch — only safe with a tight `affects:` allow-list.** |

`auto_create_pr=True` is a back-compat alias for
`automation_mode="AUTO_CREATE_PR"`; it emits a `DeprecationWarning` and
will be removed in a future spec. See `agency/capabilities/jules.py` for
the dispatch signature.

## §8 — The bi-temporal record

Every dispatch records a `JulesSession` node (or analogous for other
agents) in the bi-temporal graph. The session node carries:
- `id`, `state`, `branch_on_remote`, `pr_url`, `recovery_method`
  (`null` | `"empty"` | `"reply"` | `"patch-extract"`), `automation_mode`,
  `require_plan_approval`.
- Edges: `SERVES → Intent`, `OBSERVED_OF → WatchEvent[]`, `RECOVERED_BY
  → Patch?`, `ALIAS_OF → JulesAlias?`.

Provenance is one traversal. No parallel `sessions.json`. `memory.graph_
provenance(intent_id)` returns the full causal chain.

---

## Quick reference — the canonical incantations

**Dispatch (Mode A, dogfood):**
```python
e.invoke("jules", "dispatch",
         source="netzkontrast/agency",
         starting_branch="feat/...",
         prompt="<task>",
         protocol_preset="agency-default",
         automation_mode="AUTO_CREATE_PR",
         require_plan_approval=True)  # plan-gated default
```

**Verify (the silent-fail guard):**
```python
e.invoke("jules", "verify", session=sid)
# returns {branch_on_remote: bool, pr_url: str|"", ...}
# branch_on_remote=False ⇒ silent-fail; route to recovery (§5).
```

**Probe (recovery step 1):**
```python
e.invoke("jules", "message", session=sid,
         text="your branch isn't on origin — push and reply with the "
              "PR URL, or reply EMPTY if you have nothing to publish.")
```

**Patch-extract (recovery step 3):**
```python
plan = e.invoke("jules", "patch", session=sid,
                branch="recover-<sid>", base="main",
                owner="netzkontrast", repo="agency")
# Execute plan["ops"] via GitHub MCP one by one.
```

---

*Doctrine evolves through dogfooding. Add lessons to the relevant
`Plan/NNN-…/DOGFOOD-NOTES.md` (not here) — this file holds only
stabilised invariants.*
