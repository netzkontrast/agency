---
name: jules-dispatch
description: Use when fanning a coding task out to one or more remote Jules agent sessions and driving them to a verified PR — dispatching, sending follow-ups or reviews, approving plans, and recovering COMPLETED-but-unpushed silent-fails.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
---

# Jules Dispatch

## Overview

Orchestrate remote async **Jules** coding sessions through the agency `jules`
capability. The capability wraps the real Jules v1alpha REST API and records
every call as provenance, so a fan-out of N sessions is one auditable intent.
Full verb surface (`agency/capabilities/jules.py`):

- `dispatch(source, starting_branch, prompt)` — create a session *(effect)*
- `status(session)` · `list()` · `activities(session)` · `plan(session)` — read *(transform)*
- `approve_plan(session)` · `message(session, prompt)` — drive *(effect)*
- `verify(state, branch_on_remote)` — the `COMPLETED ≠ done` guard *(transform)*
- `stop(session)` — documents that the API has **no** cancel

Needs `JULES_API_KEY` in the env and the GitHub repo connected to the Jules app.

## When to use

- A task is long-running or parallelizable and you want it off the local terminal.
- You're fanning one spec across several sessions (one work-unit each).
- You're sending a follow-up / review to a running session, or approving its plan.
- A session reads `COMPLETED` but its branch never landed — you need recovery.

## The lifecycle (and its hard rules)

1. **Confirm intent first.** Dispatch is a one-way door — there is no cancel
   (`stop` is informational only). Lock the spec, the branch, and the per-session
   scope with the user *before* dispatching. Never dispatch while a decision is in
   flux.
2. **Dispatch the fan-out.** One `dispatch` per session; give each session a
   distinct, self-contained work-unit prompt. Keep scopes disjoint — a broad
   "do everything" message to every session causes scope-creep and duplicated work.
3. **Follow up with `message`.** It is **input only, not a control plane**:
   resumption is racy, so poll `status` after. Never use it to revive a `FAILED`
   session (dispatch fresh) or to cancel one.
4. **Approve plans promptly.** `AWAITING_PLAN_APPROVAL` is the one state that
   times out and discards the session — `plan` to read it, `approve_plan` to clear it.
5. **Verify — `COMPLETED ≠ done`.** A session flips to `COMPLETED` even when it
   paused before pushing. Always check the branch on origin; only `verify(...,
   branch_on_remote=True)` is truly done.
6. **Recover silent-fails, don't re-dispatch.** `COMPLETED` + no branch on origin
   = recoverable. Probe once via `message` ("your branch isn't on origin — push and
   reply with the SHA"); if still nothing after a couple probes, extract the
   session patch and apply it locally. Re-dispatching the same work wastes a slot.

## Driving it (code-mode; works in MCP, as a Skill, or bash-only)

```bash
python -m agency.cli --db jules.db intent \
  --purpose "fan a refactor across N sessions" \
  --deliverable "one verified PR per session" --acceptance "branch on origin"

# dispatch one session (repeat per work-unit)
python -m agency.cli --db jules.db execute --code '
d = await call_tool("capability_jules_dispatch", {
  "source": "owner/repo", "starting_branch": "main",
  "prompt": "<self-contained work-unit prompt>",
  "intent_id": INTENT, "agent_id": "agent:jules"})
return d
'

# follow-up / review to a running session
python -m agency.cli --db jules.db execute --code '
return await call_tool("capability_jules_message",
  {"session": "<sid>", "prompt": "<feedback>", "intent_id": INTENT})
'

# done-check: read state, confirm the branch is on origin, then verify
python -m agency.cli --db jules.db execute --code '
s = await call_tool("capability_jules_status", {"session": "<sid>", "intent_id": INTENT})
return await call_tool("capability_jules_verify",
  {"state": s["state"], "branch_on_remote": True, "intent_id": INTENT})
'
```

For a large fan-out, prefer the `delegate` capability (`fan_out` over a quota +
`join`) with `jules` as the driver, so the orchestration itself is gated and recorded.

## Common mistakes

- Treating `COMPLETED` as success — always `verify` the branch on origin.
- Using `message` to "stop" or "revive" a session — it cannot; it only injects input.
- Broadcasting one broad scope to every session — keep work-units disjoint.
- Re-dispatching a silent-failed session instead of recovering its existing patch.
- Letting `AWAITING_PLAN_APPROVAL` sit — it can time out and discard the session.
