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
  - `apply_patch(session, branch, base_branch) → {recovery_plan: {branch, base_branch, ops: [{tool, args}], pr_title, pr_body}}` *(transform)* — parses the unidiff trio of `add`/`modify`/`delete`/`rename` and returns a **recovery plan**: an ordered list of `{tool, args}` calls the agent executes via the GitHub MCP (`mcp__github__create_branch` → `push_files` for adds+modifies → per-file `delete_file` for deletes + rename sources → `create_pull_request`). The verb does NOT perform cross-MCP calls itself — that pretends a capability boundary it doesn't have. Signed web-flow commits via the GitHub MCP only; **never** `git apply + git push` (per JULES_PROTOCOL §8). Iterates multi-output patches with `current_base` propagation (each applied patch advances the base for the next), per JULES-REVIEW-LOOP.md §5:407-450.
  - `status_all(states=[]) → {by_state, totals, next_page_token}` *(transform)* — paginated grouping.
  - `approve_awaiting(filter={}, limit=0) → {approved: [sid]}` *(effect)* — bulk-approve every `AWAITING_PLAN_APPROVAL` matching filter.
  - `quota(now_iso="") → {active_today, daily_limit, truncated}` *(transform)* — `createTime`-windowed counting via `list`.
  - `alias(name, session=None) → {session}` *(act)* — read or upsert a stable alias for a sid (stored as a `JulesAlias` node, not `sessions.json`).
  - `recover(session) → {status: probing|recovered|empty|already_done, …}` *(effect)* — returns **immediately**. The flow is owned by the poll loop, not the verb: on call, if `COMPLETED && !branch_on_remote && patch.files > 0`, send one probe via `message`, register the session under `_recovery_in_flight` (with `attempt_count`, `probe_at_ts`), and return `{status: "probing", attempt: 1}`. The poll loop then performs the probe-wait-recheck at the canonical cadence (~5 min between probes, max 3 attempts per JULES_PROTOCOL §8). If `branch_on_remote` appears in any cycle → emit a `verify_pr` WatchEvent and clear the registry entry. After 3 probes without a branch → emit a `recover_apply_plan` WatchEvent carrying the `apply_patch` recovery plan (the agent runs it). If `patch.files == 0` from the start → return `{status: "empty"}` immediately + a `dispatch_fresh` WatchEvent recommendation. This dodges the long-MCP-request anti-pattern and unifies the whole state machine through the WatchEvent stream — the spec's central thesis.
- [ ] **`dispatch` parameter completeness.** Forward `title`, `require_plan_approval=True` (recommended default; flip from the current `False` hardcode at `jules.py:45`), `auto_create_pr`, and `alias` to `_jules_api.jules_create`. Validate `source` accepts `owner/repo`, `https://github.com/owner/repo`, and `sources/<id>`.
- [ ] **`verify` independence.** Drop the caller-supplied `branch_on_remote` bool: call `list-branches` on origin (via the existing `vcs` boundary from spec-002, augmented with `remote_exists` per spec-006 F3) and derive the truth-value. Returns `{done, state, branch_on_remote, pr_url?}`. Fail-closed: `done=False` whenever remote cannot be independently verified.
- [ ] **`status` returns the full session shape** — `{id, state, title, source, branch, url, has_outputs, require_plan_approval}` (matches `_jules_api.jules_get`'s return; today's verb discards 5 fields at `jules.py:94`).
- [ ] **Long-polling `watch(session?, timeout=30) → WatchEvent`** lands; see `## Design — the watch protocol`.
- [ ] **FastMCP background poll loop** runs at a **state-aware adaptive cadence** — default **10 s for the first 5 min after any state change** (the user-requested high-attention window), then **30 s** while idle in a stable state (matches the proven `watch_jules.py:180` baseline), then **300 s** after 20 min of no transitions; with **jitter ±2 s** and exponential backoff to **600 s** on `429`. One coroutine in the engine's lifespan; per-intent `asyncio.Queue` (not per-session — multi-intent runs need correct fan-in); `maxsize=8` with **drop-oldest** so a stalled agent can't backpressure the poller; clean cancellation on shutdown. The loop must wrap the sync `_jules_api._request` in `asyncio.to_thread(...)` (httpx is sync today) so stdio request handling does not block per HTTP call.
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
**watched-sessions registry** at the **state-aware adaptive cadence** above
(10 s in the high-attention window after any change → 30 s idle → 300 s deep
idle; jitter ±2 s; exp-backoff to 600 s on `429`). On each cycle, for every
watched sid, it calls `await asyncio.to_thread(_jules_api.jules_get, sid)` +
a tiny `activities(only_kinds="agentMessaged,planGenerated", page_size=5)`,
runs `_classify(prev, curr, last_agent_msg_id) → WatchEvent | None`, and puts
the event on the **per-intent** `asyncio.Queue` (`maxsize=8`, drop-oldest).
The `watch` tool awaits the queue with `timeout = min(caller_timeout, 25 s)`
and emits a `noop` **heartbeat** at 20 s to keep stdio alive even if no
change has occurred.

**Race / correctness invariants** the implementation must hold:
- **Per-intent queue, not per-session** — multi-intent runs (e.g. `delegate.fan_out`) need correct fan-in; each `watch(intent_id=I)` drains events for every sid that `OBSERVED_OF → JulesSession ← SERVES → Intent I`.
- **Drop-oldest backpressure** — a stalled agent never blocks the poller; the agent sees the *latest* state on next `watch`, not a backlog.
- **Timeout cap ≤ 25 s + 20 s heartbeat** — stdio request handling has implementation limits; never block longer than the upstream client tolerates.
- **Terminal-stickiness** — `FAILED`/`CANCELLED` is **sticky** in the classifier (lesson-08 §2: a FAILED session can briefly oscillate back to `IN_PROGRESS` under eventual-consistency lag; the classifier must NOT flip back).
- **Baseline-seed on first observation** of a sid suppresses the storm of stale terminal events (`watch_jules.py:430-435`).
- **Re-emit on new `agentMessaged` id** even at the same `AWAITING_USER_FEEDBACK` state (carry a per-session `last_agent_msg_id` memo; `watch_jules.py:444-451`).
- **Clean lifespan cancellation** — on shutdown the poll task is cancelled; any in-flight `to_thread` HTTP request is allowed to finish (it has its own 60 s timeout via `httpx.Client`).

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

### `recover` flow (returns immediately; the poll loop owns the probes)

The verb is a **non-blocking effect**: it kicks off the recovery state machine
and returns. The agent learns the outcome via subsequent `WatchEvent`s.

```python
def recover(session):
    state, branch_on_remote = _verify_truth(session)         # GitHub MCP list-branches; independent
    if state != "COMPLETED":              return {"status": "no_op", "state": state}
    if branch_on_remote:                  return {"status": "already_done", "branch": ref, "pr_url": …}
    patch = _patch_summary(session)                          # 1 API call
    if patch["files"] == 0:
        _emit(session, action="dispatch_fresh", instruction="…")
        return {"status": "empty"}
    # Register the session with the poll loop; the loop performs the canonical
    # probe-wait-recheck (~5 min between probes, max 3 attempts per JULES_PROTOCOL §8).
    _recovery_in_flight[session] = {"attempt": 0, "next_probe_at": now() + 5*60, "started_at": now()}
    _api.jules_message(session, _PROBE_PROMPT)               # probe #1, fire-and-return
    return {"status": "probing", "attempt": 1}
```

The poll loop's per-cycle hook then:

```python
for sid, st in list(_recovery_in_flight.items()):
    _, branch_on_remote = _verify_truth(sid)
    if branch_on_remote:                                # Jules pushed in response — done
        _emit(sid, action="verify_pr", instruction=…, evidence={"branch": ref, "pr_url": …})
        del _recovery_in_flight[sid]; continue
    if now() < st["next_probe_at"]:                     continue            # wait the 5-min window
    if st["attempt"] >= 3:                              # exhausted; hand off to the agent
        plan = _build_recovery_plan(sid)                # the apply_patch tool's output
        _emit(sid, action="recover_apply_plan", instruction=…, evidence={"plan": plan})
        del _recovery_in_flight[sid]; continue
    st["attempt"] += 1; st["next_probe_at"] = now() + 5*60
    _api.jules_message(sid, _PROBE_PROMPT)              # next probe
```

`_build_recovery_plan(sid)` is the body of `apply_patch` — it parses every
output's unidiff (iterating with `current_base` propagation across multi-output
patches), classifies each file (add/modify/delete/rename), and emits an
ordered list of `{tool, args}` calls for the agent to execute via the GitHub
MCP. The verb itself never reaches across the capability boundary; the agent
runs the plan. Pseudocode for the planner:

```python
def _build_recovery_plan(sid, branch=None, base=None):
    branch = branch or f"agency-recover-{sid}"; base = base or _current_branch()
    ops = [{"tool": "mcp__github__create_branch", "args": {"branch": branch, "from_branch": base}}]
    current_base = base
    for out in _api.jules_get_full(sid).get("outputs", []):
        diff = out["changeSet"]["gitPatch"]["unidiffPatch"]
        files = _parse_unidiff(diff)                    # [{path, op, new_path?, content?}]
        # Adds + modifies in one push_files; deletes (incl. rename sources) per file.
        upserts = [(f["path"], f["content"]) for f in files if f["op"] in ("add", "modify")]
        renames = [(f["path"], f["new_path"], f["content"]) for f in files if f["op"] == "rename"]
        if upserts:  ops.append({"tool": "mcp__github__push_files",
                                 "args": {"branch": branch, "files": upserts,
                                          "message": f"recover({sid}) chunk"}})
        for src, dst, content in renames:
            ops.append({"tool": "mcp__github__push_files",
                        "args": {"branch": branch, "files": [(dst, content)],
                                 "message": f"rename {src}->{dst}"}})
            ops.append({"tool": "mcp__github__delete_file",
                        "args": {"branch": branch, "path": src,
                                 "message": f"rename source {src}"}})
        for f in files:
            if f["op"] == "delete":
                ops.append({"tool": "mcp__github__delete_file",
                            "args": {"branch": branch, "path": f["path"]}})
        current_base = branch                            # next patch chains onto the recovered branch
    ops.append({"tool": "mcp__github__create_pull_request",
                "args": {"base": base, "head": branch,
                         "title": f"Recover Jules session {sid}",
                         "body": _recovery_pr_body(sid)}})
    return {"branch": branch, "base_branch": base, "ops": ops, "pr_title": …, "pr_body": …}
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

## Refinement notes (post spec-panel)

The spec-panel review (`REVIEW.md` beside this file) gave a **conditional accept**
on the original draft. This refinement folds in its 5 must-fixes:

1. **`apply_patch` → recovery plan**, not in-verb cross-MCP calls.
2. **Cadence → state-aware adaptive** (10 s high-attention → 30 s idle → 300 s deep-idle; backs off to 600 s on `429`), reconciling the user's "every 10 s" with the proven 30 s baseline.
3. **Sync httpx in async lifespan** → wrap with `asyncio.to_thread(...)`.
4. **`recover` rearchitected** → returns `status=probing` immediately; probe-wait-recheck (~5 min × 3) lives in the poll loop; outcome delivered as a `verify_pr` or `recover_apply_plan` `WatchEvent`. **This unifies the entire state machine through the WatchEvent stream** — the spec's central thesis.
5. **Watch protocol race spec hardened** — per-intent (not per-session) queue with `maxsize=8` drop-oldest; `timeout ≤ 25 s` with 20 s `noop` heartbeat; terminal-stickiness; multi-output patch chaining with `current_base` propagation + rename handling.

Also resolved by the refinement: **Q1** (cadence) and **Q2** (GitHub-MCP) below.

## Open Questions / Needs Research

1. ~~10 s cadence vs Jules quota.~~ **RESOLVED** — state-aware adaptive cadence (Done-When), default 10 s in the 5-min high-attention window then 30/300 s idle, 600 s on `429`. Exposed as `agency.jules.watch_cadence` for tuning.
2. ~~`apply_patch` and the GitHub MCP dependency.~~ **RESOLVED** — `apply_patch` returns a **recovery plan** (ordered `{tool, args}` ops) that the agent executes via the GitHub MCP. The verb stays inside the agency capability boundary; cross-MCP driving is the agent's job. Multi-output chaining (`current_base` propagation per JULES-REVIEW-LOOP §5) and rename handling (`push_files`+`delete_file`) are in the planner.
3. **Watched-session registry persistence across MCP-server restarts.** Two options: (a) persist `JulesSession` nodes in the bi-temporal graph (the canon: one graph) and re-seed the watcher on lifespan startup from all not-`is_terminal` sessions; (b) ephemeral, agent re-arms after restart. Recommend (a) — graph-native, survives restarts, one source of truth. Confirm before implement.
4. **Auto-approve-plan policy.** Lesson-15 §6 wants a quota guard; lesson-15 §1 wants automatic re-arming; the plan-approval-timeout window argues for `approve_awaiting(confidence_threshold)`. Default: **never auto-approve**; opt-in `policy=auto-if-affects-only` checks the plan's touched files against the spec's `affects:` and approves if subset.
5. **`status_all` page-bound.** Recommend `max_pages=20` with `truncated: true`. Confirm the bound.
6. **`patch_body` token cap.** Default 4096 bytes is conservative; some recovery flows want the whole patch. Recommend keeping the default low and forcing explicit `max_bytes=` for larger reads, so a careless call cannot blow the agent's context.
7. **The probe prompt text** — what does `_PROBE_PROMPT` say? Should it carry the recovery context ("your state is COMPLETED but no branch on origin — push and reply with the PR URL; if already pushed, reply with the SHA")? Lesson-12 + JULES-REVIEW-LOOP §8 inform this; pin one canonical string and hold it.
8. **Re-emission memo for `agentMessaged`.** The classifier needs per-session `last_agent_msg_id` to re-emit when the same `AWAITING_USER_FEEDBACK` state carries a new question (`watch_jules.py:444-451`). Cheap; pin the memo placement (in the watched-session registry node? in a separate in-memory dict?).

## Evidence

- `research/NOTES-jules-capability.md` — the original gap note.
- `research/capability-specs/specs/jules-orchestration.md` — the parity record (post-vision-alignment).
- Reference impl: `the-agency-system/jules-plugin/mcp-server/src/jules_mcp/tools/{lifecycle,patches,bulk,aliases}.py` and `lib/{sessions_state,watch_jules}.py` @ `0a6a9e7…`.
- Doctrine: `the-agency-system/Plan/JULES_PROTOCOL.md`, `JULES-REVIEW-LOOP.md`; `_lessons-learned/02,08,10,11,12,15`.
- MCP wake constraint: `https://modelcontextprotocol.io/specification` (notifications carry no model-visible payload); `https://gofastmcp.com` (lifespan + background-task pattern); R3 audit.
- Canon: `CORE.md:9-18, 33-35, 38-45, 131-133`; `CAPABILITY-CLUSTERS.md:26-43` (no new primitive; middleware = engine).
