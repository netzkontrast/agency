# NOTE — improve the `jules` capability: add the missing session verbs

**Status:** backlog / improvement note · **Recorded:** 2026-05-27 · **Found by:**
live use during the multi-agent PR1 research dispatch.

## What's missing

`agency/capabilities/jules.py` exposes only `dispatch` / `status` / `verify`, and
its `JulesBackend` Protocol only declares `create` / `get`. The vendored client
`agency/capabilities/_jules_api.py` implements only `jules_create` + `jules_get`.

There is **no verb to send a message to (resume) a running or `COMPLETED`
session** — yet that is the single most-used control in practice (answer a
question, request a plan revision, nudge a silent-failed session to push). When
the orchestrator needed to send follow-up instructions to the five dispatched
sessions, the `jules` capability could not do it; we had to call the Jules REST
endpoint directly. That is the gap this note records.

## Reference implementation (already proven in `the-agency-system`)

The sibling repo implements the rest of the same Jules REST surface — copy the
endpoints, not the packaging:

- `servers/agency-mcp/src/agency_mcp/handlers/jules/lifecycle.py`
- `jules-plugin/mcp-server/src/jules_mcp/tools/lifecycle.py`

| Function there | Endpoint | Purpose |
|---|---|---|
| `jules_message(sid, prompt)` | `POST /v1alpha/sessions/{id}:sendMessage` `{"prompt": …}` | resume / send feedback |
| `jules_approve_plan(sid)` | `POST /v1alpha/sessions/{id}:approvePlan` `{}` | clear the plan-approval gate |
| `jules_activities(sid)` | `GET /v1alpha/sessions/{id}/activities` | read the activity log |
| `jules_list()` | `GET /v1alpha/sessions` | enumerate sessions |
| `jules_stop(sid)` | — | documents that the API exposes **no** stop/cancel/delete; do not fake one |

Key semantics to carry over (already in this repo's CLAUDE.md): **`COMPLETED ≠
done`** — `COMPLETED` means *idle / waiting for input*, and a session is resumed
by `sendMessage` (it transitions back to `IN_PROGRESS`). Always verify the branch
on origin before trusting `COMPLETED` (the silent-fail guard).

## Proposed change

1. **`_jules_api.py`** — add `jules_message`, `jules_approve_plan`,
   `jules_activities`, `jules_list` (reuse the existing `_request` / `_short_id`
   / `_paginate` helpers).
2. **`JulesBackend` Protocol** — grow to `create · get · message · approve_plan ·
   activities · list`; `JulesClient` delegates each to the `_jules_api` call.
3. **`JulesCapability` verbs** —
   - `message(session, prompt)` → role `effect` (resume / feedback)
   - `approve_plan(session)` → role `effect`
   - `activities(session)` → role `transform` (feeds `verify` / a summary view)
   - `list()` → role `transform`
4. Keep the deterministic-test pattern: tests inject a stand-in backend (see the
   existing `jules` cases in `tests/test_agency.py`).

## Done When

- [ ] `JulesBackend` declares the four new methods and `JulesClient` implements them.
- [ ] `_jules_api` gains the four functions with the endpoints in the table above.
- [ ] `jules` capability exposes `message` / `approve_plan` (effect) and
      `activities` / `list` (transform), auto-wired like the rest.
- [ ] `message` round-trip is covered by a test with an injected backend.
- [ ] `verify` can consume `activities` + branch-on-remote to decide `done`.
- [ ] No stop/cancel verb is invented — the API has none.
