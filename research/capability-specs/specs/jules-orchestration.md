---
spec_id: jules-orchestration-001
slug: jules-orchestration
status: done
owner: "@claude"
depends_on: []
affects:
  - "agency/capabilities/jules.py"
  - "agency/capabilities/_jules_api.py"
  - "tests/test_agency.py"
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
estimated_jules_sessions: 0
domain: "orchestration"
wave: 2
---

# Jules Orchestration Cluster

## Status: IMPLEMENTED (parity record)

This spec was originally drafted as "port the missing verbs," but the full
lifecycle is now **shipped** on this branch in `agency/capabilities/jules.py`
+ `agency/capabilities/_jules_api.py` (commit `0668862`). The original draft
was written against a stale read of `jules.py` and contained three factual
errors, corrected below. This document is now the parity record for the
implemented surface.

### Corrections to the original draft

- ❌ "exposes only dispatch, status, and verify" → ✅ the capability now exposes
  **dispatch · status · list · activities · plan · approve_plan · message · stop · verify**.
- ❌ invented a `resume` verb → there is none. **`message`** is the resume path:
  it posts into the session (input only); resumption is racy, so poll `status`
  after — never use it to revive a `FAILED` session or to cancel one.
- ❌ prescribed `ctx.register_verb` → no such mechanism exists. Verbs auto-wire
  from the `@verb` decorator via reflection (`agency/capability.py`,
  `CapabilityBase.as_capability` + `Registry`).

## Why

A remote-agent orchestrator needs the whole session lifecycle, not just
fire-and-forget dispatch: it must read state/activities/plans, approve plans
before they time out, send feedback, and — critically — treat `COMPLETED` as
*not* done until a branch is confirmed on origin. The Jules v1alpha REST API
exposes exactly these calls; `the-agency-system` proved the bindings, and they
are now ported into the Agency capability so no orchestrator-side fallback is
needed.

## Shipped surface

| Verb | Role | REST call | Notes |
|---|---|---|---|
| `dispatch` | effect | `POST /v1alpha/sessions` | create a session |
| `status` | transform | `GET /v1alpha/sessions/{id}` | current state |
| `list` | transform | `GET /v1alpha/sessions` | trimmed listing (one page) |
| `activities` | transform | `GET /v1alpha/sessions/{id}/activities` | summary-trimmed; the costliest read |
| `plan` | transform | (latest `planGenerated` activity) | show before `approve_plan` |
| `approve_plan` | effect | `POST /v1alpha/sessions/{id}:approvePlan` | the one state that times out |
| `message` | effect | `POST /v1alpha/sessions/{id}:sendMessage` | input only; racy resumption |
| `stop` | transform | — | documents that v1alpha has **no** cancel |
| `verify` | transform | — | `COMPLETED != done`: true only with a branch on origin |

## Done When (all met)

- [x] `message` verb wraps `POST …:sendMessage`.
- [x] `approve_plan` verb wraps `POST …:approvePlan`.
- [x] `activities`, `list`, and `plan` reads implemented.
- [x] `stop` returns the explanatory "no cancel" notice instead of faking one.
- [x] `verify` keeps the `COMPLETED != done` guard (branch-on-remote).
- [x] Covered by `tests/test_agency.py::test_jules_complete_lifecycle` (57 passing).

## Source clones

```bash
git clone --depth=1 https://github.com/netzkontrast/the-agency-system.git ~/work/vendor/the-agency-system
# SHA: 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22
```

## Files

- Modify: `agency/capabilities/jules.py` (the `JulesCapability` verbs) — done @ `0668862`.
- Modify: `agency/capabilities/_jules_api.py` (`jules_list`/`jules_activities`/`jules_plan`/`jules_approve_plan`/`jules_message`) — done @ `0668862`.
- Add: `tests/test_agency.py::test_jules_complete_lifecycle` — done @ `0668862`.

## Evidence

- `agency/capabilities/jules.py` @ `0668862` — the role-tagged verb surface above, over a `JulesBackend` Protocol injected by the engine.
- `agency/capabilities/_jules_api.py` @ `0668862` — the vendored httpx REST client implementing the new endpoints.
- `tests/test_agency.py::test_jules_complete_lifecycle` @ `0668862` — exercises the full surface against a stand-in backend.
- Port source: `the-agency-system/jules-plugin/mcp-server/src/jules_mcp/tools/lifecycle.py` and `servers/agency-mcp/src/agency_mcp/handlers/jules/lifecycle.py` @ `0a6a9e71f6c26bc120a8fc1db02f8990b7916f22`.

## Self-Review

1. **Coverage:** the originally-"missing" verbs are all implemented and tested; this spec is now a parity record rather than a porting task.
2. **Residual risk / unknowns:** `verify` still trusts a caller-supplied `branch_on_remote` boolean — independently confirming it via the injected `vcs` boundary is tracked in `research/red-team/hardening-spec.md` (finding F3), not here.
3. **Method reflection:** the original draft's errors came from asserting a code state without reading the live file; the correction was to cite `path:line @ SHA` against the actual branch.
