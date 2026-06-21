# Spec-panel review — 012 Jules complete lifecycle + long-polling watcher

> Multi-expert panel: **Wiegers** (requirements quality / testability), **Nygard**
> (failure modes / operability), **Fowler** (interface design, single-responsibility),
> **Newman** (boundary integrity / API evolution), **Gregor Hohpe** (message
> ordering, queue semantics), **Lisa Crispin** (edge-case + concurrency tests).
> Grounded in `CORE.md` / `CAPABILITY-CLUSTERS.md`, the-agency-system reference
> impl (`@0a6a9e7`), and the MCP/FastMCP constraints the spec itself cites.

---

## Verdict

**Conditionally accept — refine before implement.** The spec gets the big
shape right (no new primitive, watcher = engine middleware, long-polling = the
realistic wake mechanism, recover-as-one-verb absorbs the §8 ritual). It also
correctly identifies and closes the 50 % verb-surface gap. **But it has six
concrete must-fix correctness issues** (mostly source-faithfulness drift from
the proven poller and JULES_PROTOCOL §8) plus two architectural questions whose
"hand-waved" resolutions will bite at integration time. Open Questions are
mostly sharp, but **Q2** (the GitHub-MCP dependency) is a blocking architecture
question that the spec defers to a not-yet-extant cross-MCP driver story.

Confidence the design is correct **after** the must-fix list lands: ~0.85.
Today: ~0.65.

---

## 1. Vision-alignment findings

| # | Verdict | Citation |
|---|---|---|
| V1 | ✅ **No new top-level concept.** Watcher = engine middleware in the lifespan; `jules` stays the one effect/transform capability. Matches `CORE.md:16-18` ("Cross-cutting guards … are engine middleware, **not** concepts") and the `CAPABILITY-CLUSTERS.md:26-43` "few primitives" verdict. The spec is explicit about this. |
| V2 | ✅ **Capability-owned ontology.** `JulesSession`/`JulesAlias`/`JulesWatchEvent`/`JulesPatch` nodes + `OBSERVED_OF`/`RECOVERED_BY`/`ALIAS_OF` edges declared as `OntologyExtension`; matches `CORE.md:131-133` (capability-contributed schemata, strict merge). |
| V3 | ✅ **One bi-temporal graph.** Sessions, transitions, recovery, aliases all land as graph nodes (the canon's "cross-concern provenance is one traversal" — `CORE.md:38-45`). Q3 resolves the persistence question correctly (option a — graph-native). |
| V4 | ✅ **`COMPLETED ≠ done` preserved** as the silent-fail recovery flow's anchor (`CORE.md:33-35`). The three `COMPLETED` variants in the WatchAction table are exactly the lesson distilled. |
| V5 | ⚠️ **Code-mode contract drift in the example.** The agent loop snippet in §"watch protocol" uses tool name `capability_jules_watch` — correct per the engine's auto-wiring (`engine.py:_wire` → `capability_<cap>_<verb>`) — but the example calls `(await call_tool(...))["data"]`, which **depends on Spec 001's unresolved Q2** (the `ToolResult` envelope). If the engine ships unwrapped today (current `engine.py:74` returns `out if isinstance(out, dict)` raw, not `{ok, data, ...}`), this snippet is wrong. **Add a "depends on 001 Q2 resolution" note**, or hedge the example to `result["data"] if "data" in result else result`. |
| V6 | ⚠️ **Wave numbering inconsistent.** Frontmatter says `wave: 2`; `Plan/000-overview.md` implementation-order block lists 012 nowhere (the table tops out at 011). Either (a) extend 000-overview with row 012 in the table + dep-graph, or (b) drop `wave: 2`. Today it asserts a wave that's not codified upstream. |

Net: V5 + V6 are doc-hygiene, not vision violations. The four-concepts moat
holds.

---

## 2. Source-faithfulness corrections

The drift items, with the canonical reference path the spec must match.

| # | Issue (spec) | Reference truth | Severity |
|---|---|---|---|
| F1 | **Poll cadence**: spec defaults to **10 s**. | The proven poller defaults to **30 s** with `max_interval=300` and `interval * 1.5` adaptive backoff on no-change (`the-agency-system/jules-plugin/lib/watch_jules.py:180-183, 499`). The JULES-REVIEW-LOOP § "Watch" uses `interval_seconds=180` (3 min). 10 s is **6×** faster than anything proven and will run hot against the same daily-quota account that runs implementation sessions. | **HIGH** — answer Q1 by adopting 30 s base with adaptive backoff, expose 10 s as opt-in. |
| F2 | **Backoff knob**: spec uses exponential, capped at 60 s, halving on 429. | Reference uses `min(interval * 1.5, max_interval)` on every no-change cycle (`watch_jules.py:499`) — i.e. backoff is **idle-driven**, not 429-driven. The 429 path is `time.sleep(min(interval * 2, max_interval))` (`:391, :400`). Spec conflates the two. | **MEDIUM** — be explicit: idle backoff (×1.5, cap 300 s) + 429 backoff (×2, cap 300 s) is the canon; cap=60 s undersells. |
| F3 | **Baseline seed**: spec says "first observation suppresses terminal storm". | Correct in shape; the canonical guard is **only seed terminal states from history**, **not** non-terminal (`watch_jules.py:430-435` — `if state in TERMINAL_STATES: last_state[sid] = state`). `--session` mode skips seeding entirely (`:430` — `not args.session`). Spec must mirror both nuances or the orchestrator's single-session arm will silently swallow the first transition. | **MEDIUM** — pin the seed rule exactly. |
| F4 | **Agent-message re-emission**: spec table row "same state + new `agentMessaged`" → `answer_agent_question`. | Correct, but the canonical impl re-emits on **content change**, keyed by `last_agent_msg[sid]` (`watch_jules.py:444-451`). Spec's Q5 is exactly this — but the classifier must store the **text**, not an `id`, because activity ids are not stable across pagination. | **MEDIUM** — answer Q5 by mirroring the canonical text-memo, not an "id". |
| F5 | **`AWAITING_USER_FEEDBACK` instruction** says "never leave it idle — sessions waiting on their own question time out and FAIL." | Correct (lesson-02 verbatim) **but inconsistent with the `recover_silent_fail` row**, which suggests `jules.message` is reliable. Lesson-10 says message is **racy** — `jules_message` is "context injection, not control plane" (`10-jules-message-can-revive-but-unreliable.md`). The instruction for `recover_silent_fail` should say "**one probe** via message, then **always** fall back to apply_patch on the next cycle" — i.e. message is best-effort, not a step the classifier *waits* on. Spec's `recover` flow gets this right; the instruction string should match. | **LOW** — sharpen wording. |
| F6 | **`recover` patch-apply**: spec says "**`mcp__github__create_branch` + `push_files` + per-file `delete_file` + `create_pull_request`**". | JULES_PROTOCOL §8 names `create_or_update_file` per file (`JULES_PROTOCOL.md:162`), and the JULES-REVIEW-LOOP §5 explicitly chose `push_files` only **after** weighing rate-limit pain (`JULES-REVIEW-LOOP.md:411-449` — push_files batches adds/modifies, delete_file handles deletes + rename sources). Spec is **on the modern path** — good — but must also (a) call out **renames need a delete_file on the source-side** (the renamed-from path), and (b) call out **multi-output sessions iterate patches with `current_base` chaining** (`:407-450`). Today's spec under-specifies both. | **HIGH** — spec the rename-handling and the multi-output base-chaining; otherwise the apply will silently produce malformed PRs on the (rare-but-real) multi-patch session. |
| F7 | **`patch_body` cap**: spec defaults `max_bytes=4096`. | Reference defaults **`60000`** (`patches.py:262`). 4 KB is too aggressive — every realistic recovery patch exceeds it and the agent must opt-in twice. Either keep 60 KB and call it out, or set 16 KB and document the cap. **4 KB will make `patch_body` useless by default.** | **MEDIUM** — raise to 16-60 KB; if you keep a low cap, justify it. |
| F8 | **`status` / `jules_get` shape**: spec says `verify` calls `list-branches` "via the existing `vcs` boundary from spec-002, augmented with `remote_exists` per spec-006 F3". | Cross-spec citation chain: 002 is the boundary; 006 F3 is correct (red-team `verify` independence). But `_vcs.py` today has **no `remote_exists` method** (`/home/user/agency/agency/capabilities/_vcs.py` shows `worktree/run/state/finish` only) and 002 hasn't shipped that augmentation. Spec must either (a) add `VCSBackend.remote_exists(ref) -> bool` as a **named augmentation in 012's affects**, or (b) gate 012 on 006 actually delivering it. As written, the dependency is asserted but no edge actually carries it. | **HIGH** — wire the dependency, or own the augmentation. |
| F9 | **`apply_patch` boundary**: spec proposes the verb directly invokes `mcp__github__*` tools. | This crosses the boundary contract: `mcp__github__*` are **other** MCP servers' tools; the agency engine has no cross-MCP driver registry today (cf. Q2 admits this). The reference impl uses `mcp__github__*` because the **orchestrator** (Claude Code) calls them, not the Jules MCP. **The verb shouldn't pretend to call them itself** until the cross-MCP driver story lands. | **HIGH** — either (a) make `apply_patch` a `transform` that **returns the recovery plan** (a list of `{tool, args}` invocations for the agent to execute), or (b) gate the verb on 002's cross-MCP driver shipping. The "(b) once the cross-MCP driver story lands (touches Spec 002)" answer in Q2 is doing too much work — the spec must pick. |

---

## 3. `WatchEvent` shape + `INSTRUCTIONS` critique

The table is the heart of the spec. It's mostly right; below are the
specific deltas.

### Strengths

- Closed-enum `WatchAction` is the right design move (lints, A/Bs, ports).
- `evidence` separated from `instruction` is correct — keeps the agent-visible
  surface terse and lets the agent fetch heavy data on demand.
- Per-action verb-driven instructions (≤ 280 chars) is good token discipline.

### Missing transitions (must-add rows)

| Transition | Issue |
|---|---|
| `*` → `QUEUED` (first observation, `--session` mode) | Spec says "suppressed: baseline-seed" but baseline-seed only applies to **terminal** historical states (F3). When an agent arms a watch on a **brand-new** session, the first event is the only signal it's running. The table should emit `noop` (matches "Planning started.") but with a non-empty instruction "Session armed; awaiting work." Otherwise the agent's first `watch` blocks for the full 30 s before any signal. |
| `PLANNING` → `IN_PROGRESS` (the `require_plan_approval=False` path) | Missing. Some sessions never hit `AWAITING_PLAN_APPROVAL` (lesson: the JULES-REVIEW-LOOP fix-round dispatches with `require_plan_approval=False` for **reviewer** sessions — `JULES-REVIEW-LOOP.md:146`). Spec collapses to `* → IN_PROGRESS`, which is fine in shape but should be explicit. |
| `AWAITING_PLAN_APPROVAL` → `IN_PROGRESS` (after approve_plan) | Missing. The agent needs the "plan was approved, work is progressing" affirmation so its loop knows the approve_plan call landed. Today it falls through `*→IN_PROGRESS` (`noop`) — acceptable, but undermines the "tailored, complete, clear" goal. |
| `*` → `CANCELLED` | Spec already covers, but `actor` in evidence isn't reliably available from the API (lesson-08, lesson-12). Mark `actor` as best-effort or remove. |
| **Re-emit guard**: same state, new agent message | Spec covers, but **must specify**: re-emit applies **only** to `AWAITING_USER_FEEDBACK`, not to every state (`watch_jules.py:447`). Otherwise a chatty `IN_PROGRESS` session re-emits on every progressUpdated. |

### Wording deltas

- `recover_silent_fail` instruction: "Call jules.recover — it will probe once,
  then apply the patch via the GitHub MCP." → After F9 above, change to "**…
  then return a recovery plan; execute via the GitHub MCP tools.**" Phrasing
  must not lie about who calls the GitHub tools.
- `dispatch_fresh` instruction for `COMPLETED + 0-file patch`: "Re-dispatch
  with the **same** prompt" — partially wrong. Lesson-12 says these are
  candidates for **revised** prompts ("genuine empty session ... revised
  prompt"). Soften to "Re-dispatch with a tightened prompt — the original
  produced no artefact."
- `*` → `FAILED` instruction: "`message` cannot revive FAILED." — too strong.
  Lesson-10 documents that FAILED *can* briefly transition back to
  `IN_PROGRESS` on a message, but it's **unreliable**. Reword to "Do not rely
  on `message` to revive — dispatch fresh."

### Token-efficiency / unambiguity

- ≤ 280 chars is good. **Budget the `evidence` blob** too — spec says ≤ 200
  tokens *per event*, but `evidence: {plan_steps, url}` for `review_and_approve_plan`
  is fine, while `{files, lines, bytes}` for `recover_silent_fail` is okay only
  if `files` is **a count, not a list**. Pin this (the instructions table
  shows `{files}` in the instruction template, which reads as a count — but
  the `evidence` row could grow to the full filename list). Cap evidence to
  ≤ 256 bytes serialized.
- Add a **`schema_version`** field to `WatchEvent` (1) so the closed enum can
  evolve without breaking existing watchers. Free; costs no tokens; saves a
  migration headache.

---

## 4. Watch-protocol critique (race conditions, lifecycle)

### Race conditions

| # | Race | Spec handling | Verdict |
|---|---|---|---|
| R1 | **Baseline-seed storm**: poller starts, sees N stale terminal sessions, fires N events into N queues. | Spec cites `watch_jules.py:430-435` correctly: seed terminal states from history into `last_state` before the first emit. | ✅ Correct in principle. **But add**: seed must run on **every lifespan restart**, not just first-ever boot. The graph-native session registry (Q3) is the cleanest source. |
| R2 | **Queue-fill before subscribe**: agent calls `watch`, but the poller already fired an event into the queue before the agent's `watch` blocked on it. | Spec is silent. | **MUST-FIX**: per-session `asyncio.Queue` with no max — the poller `put_nowait`s every transition, the agent's first `watch` drains them in order. Spec must state this explicitly + a `max_queued=8` ceiling so a stuck agent doesn't unbounded-grow. |
| R3 | **Multi-agent watch on same session**: two `execute()` blocks each await `watch(sid)`. | Spec is silent — does each get the event, or one? | **MUST-FIX**: pick one. The reference `combined_watcher.py` semantic is "one consumer per session"; FastMCP's typical pattern is broadcast. Recommend: **per-`intent_id` queue** (each lifecycle gets its own copy), or document that calls collide and the second blocks. The current shape implies queue-per-session, which fails this case. |
| R4 | **Lifespan cancellation**: shutdown signal arrives mid-poll. | Spec says "clean cancellation on shutdown" but doesn't specify the protocol. | **MUST-FIX**: spec the `asyncio.CancelledError` handling — drain in-flight HTTP, close `httpx.AsyncClient`, flush pending `WatchEvent`s to the graph as `aborted`. The reference daemon has signal handlers (`watch_jules.py:345-350`); the in-process equivalent is `try/finally` around `await asyncio.sleep(interval)`. |
| R5 | **MCP request timeout vs `watch` timeout**: `watch(timeout=30)` blocks server-side ≤ 30 s, but MCP clients may have shorter request timeouts. | Spec is silent. | **MUST-FIX**: clamp `timeout` to ≤ 25 s (FastMCP defaults the request timeout to ~30 s on stdio), and emit a heartbeat `noop` at ≤ 20 s to keep the channel alive. The "agent loops on `watch`" pattern fails if a single call times out at the transport layer. |
| R6 | **Eventual-consistency state oscillation** (lesson-08 §2: `IN_PROGRESS` after `FAILED`). | Spec is silent. | **MUST-FIX**: classifier must **not flip back from terminal to non-terminal**. Once `last_state[sid] ∈ TERMINAL`, the only allowed transition is to another terminal state (or a `repaired` flag). |

### Lifecycle concerns

- Spec says "one coroutine in the engine's lifespan". The engine today is
  the `Engine` class building a `FastMCP` instance (`engine.py:39-58`); there
  is no explicit lifespan hook in the code yet. **Spec must call out** the
  exact insertion point (FastMCP's `lifespan` parameter is a context manager,
  per the cited gofastmcp.com docs). `agency/__main__.py:24` calls
  `mcp.run()` directly — needs the lifespan injected at construction.
- The `_jules_watch.start(engine)` API in `## Files` is the right hook but
  doesn't specify (a) what start returns, (b) the cancellation contract,
  (c) re-seeding on restart. Add a 3-line API stub in the spec.

---

## 5. `recover` flow critique vs JULES_PROTOCOL §8

The flow in `### \`recover\` flow (the silent-fail one-shot)`:

```
state, branch_on_remote = _verify_truth(sid)
if state != COMPLETED:                return {"done": False, ...}
if branch_on_remote:                  return {"done": True, ...}
patch = _patch_summary(sid)
if patch["files"] == 0:               return {"action": "dispatch_fresh"}
message(sid, "your state is COMPLETED but no branch on origin — push and reply with PR URL")
await asyncio.sleep(10)
if (state, branch_on_remote) := _verify_truth(sid); branch_on_remote:
    return {"done": True, ...}
return _apply_patch_via_github_mcp(sid, branch=f"agency-recover-{sid}", base=current_branch)
```

| # | Check | Verdict |
|---|---|---|
| C1 | Verify branch on remote before trusting `COMPLETED`. | ✅ Matches §8 "Step 1 — verify". |
| C2 | Single message-probe then fall back. | ⚠️ §8-Appendix and CLAUDE.md both say "**2-3 probes** at ~5 minutes each before falling back". Spec collapses to 1 probe + 10 s wait. **This is too aggressive** — 10 s is well under Jules's typical 5-min push-flow latency. The right pattern is **`max_probes=2` (default), probe-interval `5 min`** — and the watcher's event-loop is the right place to manage it, not an in-verb `asyncio.sleep(10)`. |
| C3 | API extraction + GitHub-MCP push. | ⚠️ Spec says "`apply_patch_via_github_mcp`"; per F9 above, the verb can't call those tools itself unless 002's cross-MCP driver ships. Resolve. |
| C4 | Multi-output sessions iterate patches with `current_base` chaining. | ❌ Missing entirely. JULES-REVIEW-LOOP §5 `:407-450` is explicit: patches are dependent; second-patch base = `target_branch` (the in-progress branch on origin). Spec's pseudocode does one patch. **MUST-ADD**: "iterate all outputs; chain base across patches." |
| C5 | Co-authored-by Jules in recovery PR body. | ❌ Missing. §8-Appendix mandates `Co-authored-by: google-labs-jules[bot] <…>` (`JULES_PROTOCOL.md:163`). |
| C6 | "Never re-dispatch a fresh Jules session for the same work" except for genuine empty-patch failures. | ✅ Spec gets this right (3rd branch returns `dispatch_fresh` only when `patch.files == 0`). |
| C7 | `recover` is a single verb (the §8 ritual absorbed). | ✅ Matches lesson-15 §3 ("expose `jules_recover(sid, max_probes=2, on_exhaust='subagent')`"). The spec's verb signature should include `max_probes` and `probe_interval_s` parameters to make this tunable; lesson-15 names them explicitly. |
| C8 | "Never `git apply + git push`" for signing reasons. | ✅ Spec calls this out correctly. |

Net: C2 (probe count + interval) and C4 (multi-patch chaining) and C5
(co-authored-by) are the three correctness gaps. C3 is the bigger
architectural snag.

---

## 6. Concurrency / engine concerns

The spec proposes an asyncio background task in FastMCP's lifespan while
the same engine serves stdio. Spot-checks:

| # | Concern | Risk |
|---|---|---|
| K1 | **Stdio is single-process, single-event-loop.** FastMCP runs the server coroutine on the asyncio loop; an `asyncio.create_task(_poll_loop())` shares the loop. | ✅ Safe. The Jules client is `httpx.AsyncClient` (or the sync vendored client). **Important**: the current `_jules_api._request` is **sync** (`httpx.Client`, not `AsyncClient`) — the poller MUST `await asyncio.to_thread(...)` or it will block stdio request handling for the duration of every HTTP call. The spec is silent on this. **MUST-FIX**: either port `_jules_api` to async, or `to_thread` every Jules call from the poll loop. |
| K2 | **GraphQLite `record` from background task.** Memory writes from the background task while a stdio request is mid-write. | The repo's memory layer is a single SQLite connection (`memory.py`). SQLite serializes writes — safe in WAL mode, but the engine doesn't explicitly enable WAL. **MUST-CHECK**: confirm `Memory(path)` opens with `journal_mode=WAL` and `isolation_level=None` (deferred transactions); otherwise the background task will contend with stdio requests on the BEGIN IMMEDIATE step. |
| K3 | **`asyncio.Queue` per session — unbounded growth.** Sessions that never get `watch`ed (e.g. the agent died, but `recover` still polls them). | **MUST-FIX**: per-session queue `maxsize=8`; on overflow, drop oldest and emit a `degraded` warning. The reference watcher writes to a JSONL log; in-memory we need eviction. |
| K4 | **Quota interaction.** The watcher itself consumes `list_sessions` + per-session `get` calls, against the same 100/day account that the implementation sessions burn. | ⚠️ Each polled session = 2 calls / cycle × 6 cycles/min × N sessions. At N=10 active sessions, that's 120 calls/min sustained — the API will rate-limit (`429`) before quota burns. Spec's "10 s with backoff to 60 s on 429" is the right shape but the **idle backoff** (F2) is what saves the day in practice. **Strong recommendation**: default 30 s (matching the proven baseline), document the math. |
| K5 | **`message → wait 10s → re-verify` inside a verb call** (the `recover` flow). | The verb call holds the MCP request open for 10 + N seconds. R5 (request timeout) applies. **MUST-FIX**: either (a) move the probe-wait-recheck cycle into the **poll loop** (one cycle later), so `recover` returns immediately with `status=probing` and the next `watch` event delivers the outcome, or (b) document the verb may block ≤ probe_interval_s. (a) is the canonical pattern and aligns with the watcher's role. |

---

## 7. Open Questions triage

| # | Question | Resolved? | Recommendation |
|---|---|---|---|
| Q1 | 10 s vs 30 s base cadence + auto-backoff | **Resolvable from source.** | Default **30 s** (matches `watch_jules.py:180`). Expose `agency.jules.watch_cadence` knob. 10 s is opt-in. |
| Q2 | `apply_patch` and the GitHub-MCP dependency | **Blocking.** | Pick **option (a)**: `apply_patch` returns a recovery **plan** (the list of `{tool, args}` invocations) and the agent executes. This avoids gating on a cross-MCP driver that doesn't exist. Once 002's driver lands, swap to option (b). The plan-return shape also lets the agent dry-run / preview before applying. |
| Q3 | Watched-session registry persistence | **Resolved.** | Spec answers (a) — graph-native. ✅ |
| Q4 | Auto-approve-plan policy | **Resolved enough to ship.** | Default `policy="never"`; opt-in `policy="auto-if-affects-only"` with `affects_path` parameter. Matches lesson-15 §5 (`jules_plan_review`). |
| Q5 | Watch re-emission on agent-message text change | **Resolvable from source.** | Memo the **text** (not an id — activity ids aren't stable across pages; `watch_jules.py:447-451`). |
| Q6 | `status_all` pagination bound | **Resolved.** | `max_pages=20`, `truncated=true` — already matches reference (`bulk.py:5`). ✅ |
| Q7 | `patch_body` cap | **Resolvable from source.** | Default **16 KB** (between 4 KB and 60 KB). Force `max_bytes=` for larger reads. Reference uses 60 KB; agency's context-economy is tighter. |

**Net**: Q2 is the only sharp blocker. Q1, Q5, Q7 are answerable from the
reference today. Q3, Q4, Q6 are settled.

---

## Must-fix list (in priority order)

1. **F9 / Q2**: pick a path for `apply_patch` / `recover`'s GitHub-MCP
   dependency. Recommend: verb returns a **recovery plan** the agent
   executes; do NOT pretend cross-MCP calls land inside the verb.
2. **F8**: wire `VCSBackend.remote_exists(ref) -> bool` in 012's affects, or
   gate 012 on 006 actually delivering it. The current cross-spec citation
   has no implementation edge.
3. **F1 + K4**: default poll cadence **30 s** (idle backoff to 300 s), not
   10 s. Document the call-rate math.
4. **K1**: the poll loop **must** wrap the sync `_jules_api._request` in
   `asyncio.to_thread`, or port `_jules_api` to `httpx.AsyncClient`.
   Otherwise stdio request handling stalls per HTTP call.
5. **F6 / C4**: spec multi-output patch iteration with `current_base`
   chaining + rename-source `delete_file` handling. Today's `apply_patch`
   pseudocode misses both.
6. **R2 + R3 + R5**: spec the queue semantics (max_size=8, drop-oldest,
   per-intent or per-session? recommend per-intent for multi-agent
   correctness), the 25 s timeout clamp, and the keep-alive heartbeat.
7. **K5 / C2**: move probe-wait-recheck out of the `recover` verb into the
   poll loop. `recover` returns `status=probing` immediately; the next
   `watch` event delivers the outcome. Probe count default **2**, interval
   default **5 min** (matching §8).
8. **F3 + R1 + R6**: pin the baseline-seed rule (terminal-only,
   re-seeded on every lifespan restart) and the terminal-stickiness
   invariant (last_state ∈ TERMINAL → only terminal→terminal allowed).
9. **C5**: `Co-authored-by: google-labs-jules[bot] <…>` in recovery PR
   body. Trivial; required by §8-Appendix.
10. **V5**: hedge or block the `result["data"]` example call on 001 Q2.
11. **WatchEvent table**: add `schema_version: 1`; cap `evidence` to
    ≤ 256 bytes serialized; clarify re-emit applies only to
    `AWAITING_USER_FEEDBACK`; reword `recover_silent_fail` /
    `dispatch_fresh` / `FAILED` instructions per § 3 wording deltas.
12. **F4 / Q5**: classifier stores last agent **message text**, not id.

---

## Evidence ledger

- Vision canon: `/home/user/agency/docs/vision/CORE.md:9-18, 16-18, 33-35, 38-45, 131-133`; `/home/user/agency/docs/vision/CAPABILITY-CLUSTERS.md:26-43`; `/home/user/agency/Plan/000-overview.md` (impl-order block does not yet list spec 012).
- Reference poller: `/home/user/the-agency-system/jules-plugin/lib/watch_jules.py:43-50, 110-145, 180-200, 393-499`.
- Reference MCP tools: `/home/user/the-agency-system/jules-plugin/mcp-server/src/jules_mcp/tools/{lifecycle.py:43-329, patches.py:9-298, bulk.py:5-157, aliases.py:39-54}`.
- Doctrine: `/home/user/the-agency-system/Plan/JULES_PROTOCOL.md:150-167` (§8-Appendix); `/home/user/the-agency-system/Plan/JULES-REVIEW-LOOP.md:336-465` (§5 recovery, multi-patch chaining, push_files vs delete_file).
- Lessons: `_lessons-learned/02-agent-messaged-and-wait-kills-sessions.md`, `08-jules-mcp-tool-gaps.md`, `09-watcher-pattern-idiom.md`, `10-jules-message-can-revive-but-unreliable.md`, `12-completed-without-pr-or-state-mismatch.md`, `15-manual-ops-the-mcp-should-automate.md`.
- Current Agency Jules code: `/home/user/agency/agency/capabilities/jules.py:25-143`; `/home/user/agency/agency/capabilities/_jules_api.py:31-300`; `/home/user/agency/agency/capabilities/_vcs.py:18-67` (no `remote_exists` today).
- Engine substrate: `/home/user/agency/agency/engine.py:39-80`; `/home/user/agency/agency/__main__.py:19-25` (no lifespan hook today).
- MCP/FastMCP constraints: cited in-spec (modelcontextprotocol.io/specification — notifications carry no model-visible payload; gofastmcp.com — lifespan + background-task pattern); panel reading consistent with the spec's R3 audit assertions.
