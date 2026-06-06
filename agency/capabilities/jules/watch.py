import asyncio
import random
import time
from typing import Any

from agency.capabilities.jules import api as _jules_api
from agency.capabilities._vcs import GitClient

# Spec 013 Phase 11 update: every instruction names the Jules-side tool the
# agent must call EXPLICITLY (per AGENCY_PROTOCOL.md §2 — prose alone leaves
# work in the VM). Cap relaxed to ≤ 480 chars (~120 tokens / event); the
# literal-tool-name discipline is reliable, an indirected one re-introduces
# the silent-fail mode.
INSTRUCTIONS: dict[str, str] = {
    "noop": "Working.",
    "review_and_approve_plan": (
        "Plan ready ({plan_steps} steps). Use jules.plan to read it, then "
        "jules.approve_plan within ~5 min — this state has a timeout window. "
        "Agent-side: set_plan + request_plan_review."
    ),
    "answer_agent_question": (
        "Agent asked: '{agent_message:.200s}'. Reply via jules.message with a "
        "concrete answer; never leave idle (sessions waiting on their own "
        "question time out and FAIL). Agent-side: questions must use "
        "request_user_input, NEVER message_user."
    ),
    "verify_pr": (
        "Session done; branch {branch} on origin. Verify the PR contents match "
        "the spec's `affects:`. Verify via `git ls-remote` — NEVER trust local "
        "HEAD. Use read_pr_comments + reply_to_pr_comments for review threads."
    ),
    "recover_silent_fail": (
        "COMPLETED without a branch on origin ({files} files in patch). "
        "Call jules.recover — probes once, then applies via GitHub MCP. "
        "Agent-side: pre_commit_instructions() → submit(branch_name, "
        "commit_message, title, description) is the canonical publish pair."
    ),
    "recover_apply_plan": (
        "Recovery plan ready. Execute the ops via GitHub MCP "
        "(create_branch / push_files / delete_file / create_pull_request)."
    ),
    "dispatch_fresh": (
        "COMPLETED with empty patch — genuine no-op. Re-dispatch with the "
        "same prompt naming submit + pre_commit_instructions + "
        "request_user_input + replace_with_git_merge_diff + request_code_review."
    ),
    "inspect_and_resume": (
        "PAUSED. Inspect via jules.activities + read_file/list_files, then "
        "plan_step_complete to verify state before any submit. Use "
        "jules.message to resume."
    ),
    "terminal": "CANCELLED (cause: {cause}).",
}

_PROBE_PROMPT = "Your state is COMPLETED but there is no branch on origin. Push your branch and reply with the PR URL. If already pushed, reply with the branch name and SHA."

def _classify(
    prev: dict | None,
    curr: dict,
    last_agent_msg_id: str | None,
    branch_on_remote: bool,
    patch_summary: dict | None,
    plan_unapproved: bool = False,
) -> dict | None:
    """Map a (prev, curr) state pair + side-channel facts to a WatchEvent.

    Doctrine correction (the COMPLETED-is-idle insight): in Jules's
    state machine COMPLETED does NOT mean terminal — it means
    "session-idle, ball-in-orchestrator's-court". The same state value
    is reused for: (a) plan generated and waiting for approval,
    (b) work pushed and PR open, (c) work in VM and never pushed
    (silent-fail), (d) no work needed (genuine no-op).
    `plan_unapproved` disambiguates the awaiting-approval case from
    the others — without it the classifier routed (a) to `dispatch_fresh`
    (treating a waiting session as a no-op) which silently no-opped
    the dispatch.
    """
    if prev is None:
        return None

    state = curr.get("state")
    prev_state = prev.get("state")
    sid = curr.get("id")

    if prev_state in ("FAILED", "CANCELLED"):
        return None

    if state == prev_state:
        if state == "AWAITING_USER_FEEDBACK" and last_agent_msg_id and curr.get("_last_agent_msg_id") != last_agent_msg_id:
             return {
                "action": "answer_agent_question",
                "session": sid,
                "state": state,
                "instruction": INSTRUCTIONS["answer_agent_question"].format(agent_message=curr.get("_agent_message", "")),
                "evidence": {"agent_message": curr.get("_agent_message", ""), "url": curr.get("url", "")}
            }
        return None

    if state == "QUEUED":
        return {"action": "noop", "session": sid, "state": state, "instruction": INSTRUCTIONS["noop"], "evidence": {}}
    elif state == "PLANNING":
        return {"action": "noop", "session": sid, "state": state, "instruction": "Planning started.", "evidence": {}}
    elif state == "AWAITING_PLAN_APPROVAL":
        plan_steps = curr.get("plan_steps", 0)
        return {
            "action": "review_and_approve_plan",
            "session": sid,
            "state": state,
            "instruction": INSTRUCTIONS["review_and_approve_plan"].format(plan_steps=plan_steps),
            "evidence": {"plan_steps": plan_steps, "url": curr.get("url", "")}
        }
    elif state == "IN_PROGRESS":
        return {"action": "noop", "session": sid, "state": state, "instruction": INSTRUCTIONS["noop"], "evidence": {}}
    elif state == "AWAITING_USER_FEEDBACK":
        agent_message = curr.get("_agent_message", "")
        return {
            "action": "answer_agent_question",
            "session": sid,
            "state": state,
            "instruction": INSTRUCTIONS["answer_agent_question"].format(agent_message=agent_message),
            "evidence": {"agent_message": agent_message, "url": curr.get("url", "")}
        }
    elif state == "COMPLETED":
        # COMPLETED is the union of FOUR real situations — check the most
        # specific first. Doctrine: COMPLETED ≠ terminal; it means "idle,
        # waiting on the orchestrator." See AGENCY_PROTOCOL.md §1.
        if plan_unapproved:
            # Jules generated a plan + nothing else has happened. Awaiting
            # approval. (The dispatched session's `requirePlanApproval=True`
            # parks here.) Same instruction as state=AWAITING_PLAN_APPROVAL
            # — the routing surfaces it as a real approval gate, not as
            # a no-op to be re-dispatched.
            plan_steps = curr.get("plan_steps", 0)
            return {
                "action": "review_and_approve_plan",
                "session": sid,
                "state": state,
                "instruction": INSTRUCTIONS["review_and_approve_plan"].format(plan_steps=plan_steps),
                "evidence": {"plan_steps": plan_steps, "url": curr.get("url", ""),
                             "completed_means": "awaiting plan approval"}
            }
        if branch_on_remote:
            branch = curr.get("branch", "unknown")
            return {
                "action": "verify_pr",
                "session": sid,
                "state": state,
                "instruction": INSTRUCTIONS["verify_pr"].format(branch=branch),
                "evidence": {"branch": branch, "pr_url": curr.get("pr_url", "")}
            }
        files = patch_summary.get("files", 0) if patch_summary else 0
        if files > 0:
            return {
                "action": "recover_silent_fail",
                "session": sid,
                "state": state,
                "instruction": INSTRUCTIONS["recover_silent_fail"].format(files=files),
                "evidence": {"files": files, "lines": patch_summary.get("lines", 0), "bytes": patch_summary.get("bytes", 0)}
            }
        return {
            "action": "dispatch_fresh",
            "session": sid,
            "state": state,
            "instruction": INSTRUCTIONS["dispatch_fresh"],
            "evidence": {"original_prompt_hash": curr.get("_prompt_hash", "")}
        }
    elif state == "FAILED":
        error = curr.get("error", "Unknown error")
        return {
             "action": "dispatch_fresh",
             "session": sid,
             "state": state,
             "instruction": f"FAILED: {error[:200]}. Dispatch a fresh session; `message` cannot revive FAILED.",
             "evidence": {"error": error, "url": curr.get("url", "")}
         }
    elif state == "PAUSED":
        return {
            "action": "inspect_and_resume",
            "session": sid,
            "state": state,
            "instruction": INSTRUCTIONS["inspect_and_resume"],
            "evidence": {"url": curr.get("url", "")}
        }
    elif state == "CANCELLED":
        cause = curr.get("cause", "unknown")
        return {
            "action": "terminal",
            "session": sid,
            "state": state,
            "instruction": INSTRUCTIONS["terminal"].format(cause=cause),
            "evidence": {"cause": cause}
        }

    return None

class Watcher:
    def __init__(self, time_func=time.time, sleep_func=asyncio.sleep):
        self.queues: dict[str, asyncio.Queue] = {}
        self.sessions: dict[str, dict] = {}
        self.recovery_in_flight: dict[str, dict] = {}
        self._task: asyncio.Task | None = None
        self.engine = None
        self.time_func = time_func
        self.sleep_func = sleep_func
        self._429_count = 0

    def _get_queue(self, intent_id: str) -> asyncio.Queue:
        if intent_id not in self.queues:
            self.queues[intent_id] = asyncio.Queue(maxsize=8)
        return self.queues[intent_id]

    def _put_event(self, intent_id: str, event: dict):
        q = self._get_queue(intent_id)
        if q.full():
            try:
                q.get_nowait()
            except asyncio.QueueEmpty:
                pass
        q.put_nowait(event)

    def _emit_monitor(self, sinfo: dict, event: dict) -> None:
        """Spec 022 — fan a classified transition onto the engine monitor
        channel (Spec 021), the SIDE-CHANNEL to the per-intent queue. The queue
        stays for programmatic consumers (`jules.watch`); the monitor is for
        live awareness in Claude Code without a polling loop.

        ``noop`` transitions (heartbeats, same-state) do NOT emit — OQ#1 noise
        filter. Best-effort: silent no-op when no engine/monitor is attached
        (e.g. a Watcher under unit test with no engine wired).
        """
        if event.get("action") == "noop":
            return
        engine = self.engine
        monitor = getattr(engine, "monitor", None) if engine is not None else None
        if monitor is None:
            return
        from agency._monitor import MonitorEvent
        prev = sinfo.get("last_state") or {}
        prev_state = prev.get("state") if isinstance(prev, dict) else None
        sid = event.get("session", "")
        instr = (event.get("instruction") or "")[:200]
        try:
            monitor.emit(MonitorEvent(
                source="jules",
                kind=event.get("action", "info"),
                message=f"sid={sid} {prev_state}→{event.get('state')}: {instr}",
                intent_id=sinfo.get("intent_id", ""),
            ))
        except OSError:
            pass  # best-effort — never let a log-write failure break the poll loop

    def _calc_cadence(self) -> float:
        now = self.time_func()

        if self._429_count > 0:
            return min(600, 10 * (2 ** self._429_count)) # Exp backoff on 429

        if not self.sessions:
             return 30.0

        min_elapsed = min(now - s["last_transition_at"] for s in self.sessions.values())

        if min_elapsed < 5 * 60:
            return 10.0 # 10s for first 5 mins
        elif min_elapsed < 20 * 60:
            return 30.0 # 30s for next 15 mins
        else:
            return 300.0 # 300s after 20 mins


    async def _poll_loop(self):
        last_heartbeat = self.time_func()

        while True:
            # 0. Heartbeat
            now = self.time_func()
            if now - last_heartbeat >= 20:
                for intent_id in self.queues:
                    self._put_event(intent_id, {"action": "noop", "instruction": INSTRUCTIONS["noop"], "evidence": {}})
                last_heartbeat = now

            # 1. Recovery Cycle
            for sid, st in list(self.recovery_in_flight.items()):
                vcs = GitClient()
                branch_on_remote = vcs.remote_exists(st.get("branch", ""))
                if branch_on_remote:
                    ev = {"action": "verify_pr", "session": sid,
                          "instruction": "...", "evidence": {}}
                    self._put_event(st["intent_id"], ev)
                    self._emit_monitor(st, ev)   # Spec 022 — recovery success is live too
                    del self.recovery_in_flight[sid]
                    continue

                if self.time_func() < st["next_probe_at"]:
                    continue

                if st["attempt"] >= 3:
                    try:
                        from agency.capabilities.jules import patch as _jules_patch
                        # Fetch outputs + source-derived owner/repo for the
                        # recovery plan (build_recovery_plan signature landed
                        # in PR #9: (outputs, branch, base, owner, repo, sid)).
                        sess = await asyncio.to_thread(_jules_api.jules_get_full, sid)
                        outputs = sess.get("outputs", [])
                        # source shape varies: "sources/owner-repo" (resolve_source
                        # output) or "owner/repo" directly. Owner/repo can be
                        # pre-plumbed via arm() — fall back to parsing.
                        owner = st.get("owner", "")
                        repo = st.get("repo", "")
                        if not owner or not repo:
                            src = sess.get("sourceContext", {}).get("source", "")
                            short = src.rsplit("/", 1)[-1]   # strip "sources/" prefix
                            if "-" in short:
                                owner, _, repo = short.partition("-")
                            elif "/" in src:
                                owner, _, repo = src.partition("/")
                        recover_branch = st.get("recover_branch", f"recover-{sid}")
                        base = st.get("base", "main")
                        plan = await asyncio.to_thread(
                            _jules_patch.build_recovery_plan,
                            outputs, recover_branch, base,
                            owner or "unknown", repo or "unknown", sid,
                        )
                    except Exception:
                        # _jules_patch missing OR jules_get_full failed OR
                        # parse failed — emit an empty plan so the agent
                        # can fall back to a manual recovery.
                        plan = {}

                    ev = {
                        "action": "recover_apply_plan",
                        "session": sid,
                        "state": "COMPLETED",
                        "instruction": INSTRUCTIONS["recover_apply_plan"],
                        "evidence": {"plan": plan}
                    }
                    self._put_event(st["intent_id"], ev)
                    self._emit_monitor(st, ev)   # Spec 022 — patch-apply-needed is live too
                    del self.recovery_in_flight[sid]
                    continue

                st["attempt"] += 1
                st["next_probe_at"] = self.time_func() + 5*60

                try:
                     await asyncio.to_thread(_jules_api.jules_message, sid, _PROBE_PROMPT)
                except Exception:
                     pass

            # 2. Main Watch Cycle
            for sid, sinfo in list(self.sessions.items()):
                try:
                    curr = await asyncio.to_thread(_jules_api.jules_get, sid)
                    # Pull activities including planApproved + codeChanges so we
                    # can disambiguate COMPLETED-awaiting-approval from
                    # COMPLETED-genuine-no-op (doctrine: COMPLETED ≠ terminal).
                    acts = await asyncio.to_thread(
                        _jules_api.jules_activities, sid,
                        only_kinds="agentMessaged,planGenerated,planApproved,codeChanges",
                        page_size=10,
                    )
                    # Activities arrive newest-first. Track which "later" events
                    # have fired so the plan-unapproved test works regardless of
                    # iteration order.
                    plan_generated_at = None
                    plan_approved_at = None
                    code_changes_at = None
                    if acts and "activities" in acts and acts["activities"]:
                        for act in acts["activities"]:
                            kind = act.get("kind")
                            t = act.get("createTime", "")
                            if kind == "agentMessaged" and "_last_agent_msg_id" not in curr:
                                curr["_last_agent_msg_id"] = act.get("id")
                                curr["_agent_message"] = act.get("agentMessaged", {}).get("message", "")
                            elif kind == "planGenerated":
                                if "plan_steps" not in curr:
                                    curr["plan_steps"] = len(act.get("planGenerated", {}).get("plan", {}).get("steps", []))
                                if plan_generated_at is None or t > plan_generated_at:
                                    plan_generated_at = t
                            elif kind == "planApproved":
                                if plan_approved_at is None or t > plan_approved_at:
                                    plan_approved_at = t
                            elif kind == "codeChanges":
                                if code_changes_at is None or t > code_changes_at:
                                    code_changes_at = t
                    # plan_unapproved == latest plan was generated and neither
                    # approved nor superseded by codeChanges. Comparing ISO-8601
                    # timestamp strings is correct (lexicographic order).
                    plan_unapproved = bool(plan_generated_at) and not (
                        (plan_approved_at and plan_approved_at >= plan_generated_at) or
                        (code_changes_at and code_changes_at >= plan_generated_at)
                    )

                    branch = curr.get("branch")
                    if branch:
                        vcs = GitClient()
                        branch_on_remote = await asyncio.to_thread(vcs.remote_exists, branch)
                    else:
                        branch_on_remote = False

                    try:
                        patch_summary = await asyncio.to_thread(_jules_api.jules_patch_extract, sid)
                    except Exception:
                        patch_summary = {"files": 0, "lines": 0, "bytes": 0}

                    prev = sinfo["last_state"]
                    event = _classify(prev, curr, sinfo["last_agent_msg_id"],
                                      branch_on_remote, patch_summary,
                                      plan_unapproved=plan_unapproved)

                    if event:
                        self._put_event(sinfo["intent_id"], event)
                        self._emit_monitor(sinfo, event)   # Spec 022 — live side-channel
                        sinfo["last_transition_at"] = self.time_func()

                        if event["action"] in ("terminal", "verify_pr", "dispatch_fresh"):
                            if hasattr(self, "disarm"):
                                self.disarm(self.engine, sid)

                    sinfo["last_state"] = curr
                    sinfo["last_agent_msg_id"] = curr.get("_last_agent_msg_id")

                    self._429_count = 0 # successful cycle resets
                except Exception as e:
                    if hasattr(e, "status_code") and getattr(e, "status_code") == 429:
                        self._429_count += 1
                    pass

            cadence = self._calc_cadence()
            jitter = random.uniform(-2, 2)
            try:
                await self.sleep_func(max(0.1, cadence + jitter))
            except asyncio.CancelledError:
                break

    def arm(self, engine: Any, intent_id: str, sid: str, alias: str = "") -> None:
        self.sessions[sid] = {
            "intent_id": intent_id,
            "last_state": None,
            "last_agent_msg_id": None,
            "prev_terminal": False,
            "alias": alias,
            "last_transition_at": self.time_func()
        }

    def disarm(self, engine: Any, sid: str) -> None:
        if sid in self.sessions:
            del self.sessions[sid]

    def start(self, engine: Any) -> asyncio.Task:
        self.engine = engine
        self._task = asyncio.create_task(self._poll_loop())
        return self._task

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

def start(engine: Any) -> asyncio.Task:
    """Start the watcher's poll loop, attaching the Watcher instance to the
    engine at `engine._jules_watcher`. Idempotent (re-call returns the same
    task; further `start` is a no-op once a Watcher is attached)."""
    if not hasattr(engine, '_jules_watcher'):
        engine._jules_watcher = Watcher()
    return engine._jules_watcher.start(engine)

async def stop(engine: Any):
    if hasattr(engine, '_jules_watcher'):
        await engine._jules_watcher.stop()

def arm(engine: Any, intent_id: str, sid: str, alias: str = "") -> None:
    if hasattr(engine, '_jules_watcher'):
        engine._jules_watcher.arm(engine, intent_id, sid, alias)

def disarm(engine: Any, sid: str) -> None:
    if hasattr(engine, '_jules_watcher'):
         engine._jules_watcher.disarm(engine, sid)
