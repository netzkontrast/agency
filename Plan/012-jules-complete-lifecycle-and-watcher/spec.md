---
spec_id: "012"
slug: jules-complete-lifecycle-and-watcher
status: draft
owner: "@agency"
depends_on: ["001", "002", "006"]
affects:
  - agency/capabilities/jules.py
  - agency/capabilities/_jules_api.py
  - agency/capabilities/_jules_watch.py
  - agency/capabilities/_jules_patch.py
  - agency/__main__.py
  - agency/ontology.py
  - tests/test_agency.py
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
estimated_jules_sessions: 4
domain: capability
wave: 2
---

# Spec 012 — Complete Jules Lifecycle + Long-Polling Watcher

## Why

The current `agency.jules` capability covers **~50 %** of the Jules v1alpha
surface (lifecycle reads/drives: `dispatch · status · list · activities · plan
· approve_plan · message · stop · verify`) and nothing orbital
(`research/NOTES-jules-capability.md`, R2 gap audit). Lesson-15 in
`the-agency-system/Plan/_lessons-learned/15-manual-ops-the-mcp-should-automate.md`
codifies fifteen recurring manual ops the MCP *should* automate: watcher
arming, independent branch-on-remote in `verify`, silent-fail recovery,
plan-vs-`affects:` review, quota guard, protocol preamble, spec-driven
dispatch, patch audit, and seven more. The user's stated goal: a **stable,
automatic state-flow for handling Jules sessions** — polled every 10 s, with
the MCP delivering a *tailored, token-efficient, clear-and-complete
instruction* to the agent on every change.

**The binding constraint, established by R3:** MCP has **no server→client
"wake-the-agent" primitive**; `subscribe_pr_activity` is a Claude Code
built-in we cannot replicate. The realistic pattern is **agent-driven
long-polling**: a `watch` tool that blocks server-side (≤30 s) on an internal
event queue that a FastMCP background task fills as it polls Jules every
10 s. On change, the tool returns a structured `{action, instruction, evidence}`
payload — the verb-driven, token-efficient "tailored instructions" the user
asked for. The agent loops on `watch`; the server owns the polling cadence;
the conversation reads only deltas.

This spec closes the 50 % gap, encodes the lesson-15 automations, and
delivers the long-polling watcher as a Lifecycle-driven wake mechanism — all
inside the existing `jules` capability (no new top-level concept; the poll
loop is engine middleware, per `CORE.md:16-18`).

## Done When

- [ ] **Verb-surface parity (close R2's top-5).** New verbs land on `JulesCapability`:
  - `resolve_source(owner, repo) → {source}` *(transform)* — wraps `GET /v1alpha/sources` (currently inlined in `_jules_api._resolve_github_source`).
  - `patch(session) → {summary, files, lines, bytes}` *(transform)* — extracts the latest activity-artifact unidiff via API, returns summary stats only (no body in conversation by default).
  - `patch_body(session, max_bytes=4096) → {unidiff_truncated}` *(transform)* — explicit, capped retrieval; only for the recovery flow.
  - `apply_patch(session, branch, base_branch) → {commit_sha, pr_url}` *(effect)* — parses the unidiff and writes via `mcp__github__create_branch` + `push_files` + per-file `delete_file` + `create_pull_request` (signed web-flow commits; **never** `git apply + git push`, per JULES_PROTOCOL §8).
  - `status_all(states=[]) → {by_state, totals, next_page_token}` *(transform)* — paginated grouping.
  - `approve_awaiting(filter={}, limit=0) → {approved: [sid]}` *(effect)* — bulk-approve every `AWAITING_PLAN_APPROVAL` matching filter.
  - `quota(now_iso="") → {active_today, daily_limit, truncated}` *(transform)* — `createTime`-windowed counting via `list`.
  - `alias(name, session=None) → {session}` *(act)* — read or upsert a stable alias for a sid (stored as a `JulesAlias` node, not `sessions.json`).
  - `recover(session) → {state, branch_on_remote, applied_pr_url?}` *(effect)* — the silent-fail recovery flow as one verb: read state, list-branches on origin to set the truth-bool, if `COMPLETED && !branch_on_remote && patch.files > 0`: send one probe via `message`, wait one poll cycle, if still no branch → `apply_patch` locally; if `COMPLETED && patch.files == 0`: return `dispatch_fresh` recommendation.
- [ ] **`dispatch` parameter completeness.** Forward `title`, `require_plan_approval=True` (recommended default; flip from the current `False` hardcode at `jules.py:45`), `auto_create_pr`, and `alias` to `_jules_api.jules_create`. Validate `source` accepts `owner/repo`, `https://github.com/owner/repo`, and `sources/<id>`.
- [ ] **`verify` independence.** Drop the caller-supplied `branch_on_remote` bool: call `list-branches` on origin (via the existing `vcs` boundary from spec-002, augmented with `remote_exists` per spec-006 F3) and derive the truth-value. Returns `{done, state, branch_on_remote, pr_url?}`. Fail-closed: `done=False` whenever remote cannot be independently verified.
- [ ] **`status` returns the full session shape** — `{id, state, title, source, branch, url, has_outputs, require_plan_approval}` (matches `_jules_api.jules_get`'s return; today's verb discards 5 fields at `jules.py:94`).
- [ ] **Long-polling `watch(session?, timeout=30) → WatchEvent`** lands; see `## Design — the watch protocol`.
- [ ] **FastMCP background poll loop** runs at **10 s cadence** with jitter ±2 s and exponential backoff to 60 s on quota-pressure responses (`429`). One coroutine in the engine's lifespan; one in-process queue per watched session; clean cancellation on shutdown.
- [ ] **The instruction-payload contract** in `## Design — WatchEvent shape` is enforced by a `JSON Schema` validate test; every emission has `action` ∈ the closed enum + an `instruction` ≤ 280 chars + `evidence` whose shape matches the action.
- [ ] **Session registry as graph nodes**, not `sessions.json` — every `dispatch` records a `JulesSession` node (id = sid) with `alias`, `intent_id`, `branch`, `source`, `pr_url`; transitions record `JulesWatchEvent` nodes edged `OBSERVED_OF → JulesSession`. Cross-concern provenance stays one traversal (the canon's moat — `CORE.md:38-45`).
- [ ] **Ontology extension** declares `JulesSession`, `JulesAlias`, `JulesWatchEvent`, `JulesPatch` node kinds + the `OBSERVED_OF`/`RECOVERED_BY`/`ALIAS_OF` edges + the `WatchAction` enum.
- [ ] **Tests** (TDD; extend `tests/test_agency.py`): a deterministic `StubJulesClient` exercising every new verb; a fake-clock watcher test that simulates `IN_PROGRESS → COMPLETED + no branch` and asserts the watch emits the `recover_silent_fail` action with the right `instruction`; a patch-extract test with a sample unidiff; quota-guard test; and the `verify` independence test (verify never trusts the caller bool).

## Design

### Vision alignment

- **No new concept, no new role-tag.** `jules` stays the one effect/transform capability; the watcher is **engine middleware** (background asyncio task in the engine's lifespan), per `CORE.md:16-18` ("Cross-cutting guards … are engine middleware, **not** concepts").
- **The wake mechanism is agent-driven long-polling**, not server-initiated push (R3, MCP-spec-binding). The canon's "code-mode is the contract" is preserved: the agent calls `await call_tool("capability_jules_watch", …)` in `execute`; the call blocks in-sandbox; only the structured delta crosses into context.
- **Returns Spec-001's `ToolResult` envelope** (`data: WatchEvent`). The `evidence` field is the minimal data the agent needs to act, never the raw patch body — that lives in the `JulesPatch` node and is fetched on demand via `patch_body`.

### The watch protocol

The agent loops:

```python
# inside execute()
while True:
    ev = (await call_tool("capability_jules_watch",
                          {"session": sid, "timeout": 30, "intent_id": INTENT}))["data"]
    if ev["action"] == "noop": continue
    if ev["action"] == "review_and_approve_plan":
        plan = (await call_tool("capability_jules_plan", {"session": sid, "intent_id": INTENT}))["data"]
        # show plan; if confidence ≥ 0.9 or human approves:
        await call_tool("capability_jules_approve_plan", {"session": sid, "intent_id": INTENT})
        continue
    if ev["action"] == "answer_agent_question":
        # ev["evidence"]["agent_message"] carries the question
        await call_tool("capability_jules_message",
                        {"session": sid, "prompt": "<answer>", "intent_id": INTENT}); continue
    if ev["action"] == "recover_silent_fail":
        await call_tool("capability_jules_recover", {"session": sid, "intent_id": INTENT}); continue
    if ev["action"] in ("verify_pr", "dispatch_fresh", "terminal"):
        break
```

Server side: a single FastMCP lifespan task `_poll_loop()` iterates the
**watched-sessions registry** every 10 s (jitter ±2 s, exp-backoff to 60 s on
`429`), pulls `jules_get` + a small `jules_activities(only_kinds=...)` per sid,
runs `_classify(prev, curr)` → `WatchEvent | None`, and puts the event on the
per-session `asyncio.Queue`. The `watch` tool awaits the queue with the
caller's `timeout`; on timeout it returns `action=noop` (no data churn).

### `WatchEvent` shape (the tailored instruction payload)

```json
{
  "action":      "review_and_approve_plan",      // ∈ WatchAction enum, closed
  "session":     "14726194687931644486",
  "state":       "AWAITING_PLAN_APPROVAL",
  "instruction": "Plan ready (8 steps). Call jules.plan to read it, then jules.approve_plan within ~5 min — this state has a timeout window.",
  "evidence":    {"plan_steps": 8, "url": "https://jules.google.com/session/…"}
}
```

Closed `WatchAction` enum + per-action instruction template (≤280 chars,
verb-driven, evidence-only data) — the **single source of truth** for the
agent's per-state behavior:

| Transition (prev → curr) | `action` | `instruction` template | `evidence` |
|---|---|---|---|
| ∅ → `QUEUED` | `noop` | — (suppressed: baseline-seed) | — |
| `QUEUED` → `PLANNING` | `noop` | "Planning started." | — |
| `PLANNING` → `AWAITING_PLAN_APPROVAL` | `review_and_approve_plan` | "Plan ready ({n} steps). Read it via jules.plan, then jules.approve_plan within ~5 min — this state has a timeout window." | `{plan_steps, url}` |
| `*` → `IN_PROGRESS` | `noop` | "Working." | — |
| `IN_PROGRESS` → `AWAITING_USER_FEEDBACK` | `answer_agent_question` | "Agent asked: '{q[:200]}'. Reply via jules.message with a concrete answer; never leave it idle — sessions waiting on their own question time out and FAIL." | `{agent_message, url}` |
| `IN_PROGRESS` → `COMPLETED` (branch on origin) | `verify_pr` | "Session done; branch {ref} on origin. Verify the PR contents match the spec's `affects:`." | `{branch, pr_url}` |
| `IN_PROGRESS` → `COMPLETED` (no branch + patch>0) | `recover_silent_fail` | "COMPLETED without a branch on origin ({files} files in patch). Call jules.recover — it will probe once, then apply the patch via the GitHub MCP." | `{files, lines, bytes}` |
| `IN_PROGRESS` → `COMPLETED` (no branch + patch=0) | `dispatch_fresh` | "COMPLETED with empty patch — genuine no-op. Re-dispatch with the same prompt (the only legitimate fresh-dispatch trigger)." | `{original_prompt_hash}` |
| `*` → `FAILED` | `dispatch_fresh` | "FAILED: {error[:200]}. Dispatch a fresh session; `message` cannot revive FAILED." | `{error, url}` |
| `*` → `PAUSED` | `inspect_and_resume` | "PAUSED. Inspect last activities via jules.activities, then jules.message to resume." | `{url}` |
| `*` → `CANCELLED` | `terminal` | "CANCELLED (cause: {actor})." | `{cause}` |
| same state + new `agentMessaged` | `answer_agent_question` | (as above — re-emit on new question per `watch_jules.py:444-451`) | `{agent_message, url}` |

The instruction strings live in `agency/capabilities/_jules_watch.py` as a
module-level constant `INSTRUCTIONS: dict[WatchAction, str]` — easy to lint,
re-translate, A/B-test. Token budget per WatchEvent: ≤ 200 tokens.

### State classification

`_classify(prev: SessionView, curr: SessionView, agent_msg: str | None) → WatchEvent | None`:

1. Same `state` and no new `agentMessaged` → `None` (no churn).
2. `curr.state in TERMINAL`: distinguish the three `COMPLETED` variants and `FAILED`/`CANCELLED` per the table; `branch_on_remote` derived independently via the `vcs` boundary (cached per sid+ref).
3. `curr.state == AWAITING_*`: emit the action; carry the `plan_steps` count or `agent_message` text in `evidence`.
4. Baseline seed on first observation suppresses storm of stale terminal events (`watch_jules.py:430-435`).

### Quota / 429 backoff

The poll loop tracks rolling-window `429` rate; on first `429` it doubles its
sleep up to 60 s and emits a single `jules.quota` health log. Resets on a
clean cycle.

### Ontology extension (capability-owned, isolated)

Nodes: `JulesSession`, `JulesAlias`, `JulesWatchEvent`, `JulesPatch`.
Edges: `OBSERVED_OF` (event → session), `RECOVERED_BY` (session → invocation), `ALIAS_OF` (alias → session).
Closed enums: `JulesState`, `WatchAction`.
All declared in `JulesCapability.ontology` (`OntologyExtension`) and merged strictly per `CORE.md:131-133`. No leak into the core ontology.

### `recover` flow (the silent-fail one-shot)

```
state, branch_on_remote = _verify_truth(sid)        # GitHub MCP list-branches; independent
if state != COMPLETED:                              return {"done": False, "state": state}
if branch_on_remote:                                return {"done": True,  "branch": ref, "pr_url": …}
patch = _patch_summary(sid)                         # 1 API call
if patch["files"] == 0:                             return {"action": "dispatch_fresh"}
message(sid, "your state is COMPLETED but no branch on origin — push and reply with PR URL")
await asyncio.sleep(10)                             # one poll cycle
if (state, branch_on_remote) := _verify_truth(sid); branch_on_remote:
    return {"done": True, "branch": ref, "pr_url": …}
return _apply_patch_via_github_mcp(sid, branch=f"agency-recover-{sid}", base=current_branch)
```

## Files

- **Create**:
  - `agency/capabilities/_jules_watch.py` — the poll loop + `_classify` + `INSTRUCTIONS` table + per-session asyncio queues + watched-session registry helper.
  - `agency/capabilities/_jules_patch.py` — unidiff parsing + the GitHub-MCP-mediated apply (`mcp__github__create_branch` / `push_files` / `delete_file` / `create_pull_request`); stats-only by default.
  - `tests/test_jules_watch.py` — fake-clock watcher tests + state-classification matrix; verifies the closed `WatchAction` enum and every instruction template renders.
- **Modify**:
  - `agency/capabilities/jules.py` — add the new verbs (`resolve_source`, `patch`, `patch_body`, `apply_patch`, `status_all`, `approve_awaiting`, `quota`, `alias`, `recover`, `watch`); extend `dispatch` params; make `verify` independent; extend `status` shape; extend `JulesBackend` Protocol + `JulesClient`; expand the `OntologyExtension`.
  - `agency/capabilities/_jules_api.py` — add the missing endpoint wrappers (`jules_patch_extract`, `jules_status_all`, `jules_approve_awaiting`, `jules_quota`, `jules_resolve_source`) and full-shape `jules_get_full`.
  - `agency/__main__.py` — wire the FastMCP lifespan to start `_jules_watch.start(engine)` and cancel on shutdown.
  - `agency/ontology.py` — register the new node kinds / edges / enums (or rely on `OntologyExtension` strict merge — the canonical path).
  - `tests/test_agency.py` — extend `StubJulesClient` for the new backend methods; add `test_jules_verb_surface_complete` (the parity test) and update the help-skill regeneration as the verb list grows.

## Open Questions / Needs Research

1. **10 s cadence vs Jules quota.** The proven `watch_jules.py` uses 30 s base. 10 s on N watched sessions = N × 6 / minute. The free-tier quota isn't documented; should the default be **10 s with auto-backoff to 30/60 s under `429`**, or 30 s with a `--fast` opt-in? Recommend: default 10 s + auto-backoff; expose `agency.jules.watch_cadence` as a tunable.
2. **`apply_patch` and the GitHub MCP dependency.** The recovery path requires `mcp__github__*` tools (signed web-flow commits — see `the-agency-system/CLAUDE.md` "Recovery flow"); these are GitHub-MCP tools, not the agency capability's. Should `_jules_patch._apply` be **a method the agent calls** (so the GitHub MCP is in the agent's tool surface), or should `jules.recover` call them via `ctx.call("github", "create_branch", …)` (which assumes the agency engine has the GitHub MCP as a driver)? Recommend (b) once the cross-MCP driver story lands (touches Spec 002).
3. **Where the watched-session registry lives between MCP server restarts.** Two options: (a) persist `JulesSession` nodes in the bi-temporal graph (the canon: one graph) and re-seed the watcher on lifespan startup from all not-`is_terminal` sessions; (b) ephemeral, agent re-arms after restart. Recommend (a) — graph-native, survives restarts, one source of truth.
4. **Auto-approve-plan policy.** Lesson-15 §6 wants a quota guard; lesson-15 §1 wants automatic re-arming; the plan-approval-timeout window argues for `approve_awaiting(confidence_threshold)`. Spec the threshold model (default: never auto-approve; opt-in `policy=auto-if-affects-only` that checks the plan's touched files against the spec's `affects:` and approves if subset).
5. **`watch` re-emission on agent-message text change** — the canonical poller re-emits when the same `AWAITING_USER_FEEDBACK` carries a *new* `agentMessaged`. The classifier needs a per-session "last agent message id" memo; cheap, but spec the memo explicitly to avoid drift.
6. **What `status_all` returns when the account has > 1 page of sessions.** The reference paginates fully and may stretch to many calls; bound it (`max_pages=20`) and surface `truncated: true`. Confirm the bound.
7. **`patch_body` token risk.** Default cap **4096 bytes** is conservative; some recovery flows want the whole patch. Recommend keeping the default low and forcing an explicit `max_bytes=` for larger reads, so a careless call can't blow the agent's context.

## Evidence

- `research/NOTES-jules-capability.md` — the original gap note.
- `research/capability-specs/specs/jules-orchestration.md` — the parity record (post-vision-alignment).
- Reference impl: `the-agency-system/jules-plugin/mcp-server/src/jules_mcp/tools/{lifecycle,patches,bulk,aliases}.py` and `lib/{sessions_state,watch_jules}.py` @ `0a6a9e7…`.
- Doctrine: `the-agency-system/Plan/JULES_PROTOCOL.md`, `JULES-REVIEW-LOOP.md`; `_lessons-learned/02,08,10,11,12,15`.
- MCP wake constraint: `https://modelcontextprotocol.io/specification` (notifications carry no model-visible payload); `https://gofastmcp.com` (lifespan + background-task pattern); R3 audit.
- Canon: `CORE.md:9-18, 33-35, 38-45, 131-133`; `CAPABILITY-CLUSTERS.md:26-43` (no new primitive; middleware = engine).
