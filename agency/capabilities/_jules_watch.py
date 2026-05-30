import asyncio
import random
import time
from typing import Any

from agency.capabilities import _jules_api
from agency.capabilities._vcs import GitClient

INSTRUCTIONS: dict[str, str] = {
    "noop": "Working.",
    "review_and_approve_plan": "Plan ready ({plan_steps} steps). Read it via jules.plan, then jules.approve_plan within ~5 min — this state has a timeout window.",
    "answer_agent_question": "Agent asked: '{agent_message:.200s}'. Reply via jules.message with a concrete answer; never leave it idle — sessions waiting on their own question time out and FAIL.",
    "verify_pr": "Session done; branch {branch} on origin. Verify the PR contents match the spec's `affects:`.",
    "recover_silent_fail": "COMPLETED without a branch on origin ({files} files in patch). Call jules.recover — it will probe once, then apply the patch via the GitHub MCP.",
    "recover_apply_plan": "Recovery plan ready. Execute the operations via github MCP.",
    "dispatch_fresh": "COMPLETED with empty patch — genuine no-op. Re-dispatch with the same prompt (the only legitimate fresh-dispatch trigger).",
    "inspect_and_resume": "PAUSED. Inspect last activities via jules.activities, then jules.message to resume.",
    "terminal": "CANCELLED (cause: {cause})."
}

_PROBE_PROMPT = "Your state is COMPLETED but there is no branch on origin. Push your branch and reply with the PR URL. If already pushed, reply with the branch name and SHA."

def _classify(
    prev: dict | None,
    curr: dict,
    last_agent_msg_id: str | None,
    branch_on_remote: bool,
    patch_summary: dict | None
) -> dict | None:
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
        if branch_on_remote:
            branch = curr.get("branch", "unknown")
            return {
                "action": "verify_pr",
                "session": sid,
                "state": state,
                "instruction": INSTRUCTIONS["verify_pr"].format(branch=branch),
                "evidence": {"branch": branch, "pr_url": curr.get("pr_url", "")}
            }
        else:
            files = patch_summary.get("files", 0) if patch_summary else 0
            if files > 0:
                return {
                    "action": "recover_silent_fail",
                    "session": sid,
                    "state": state,
                    "instruction": INSTRUCTIONS["recover_silent_fail"].format(files=files),
                    "evidence": {"files": files, "lines": patch_summary.get("lines", 0), "bytes": patch_summary.get("bytes", 0)}
                }
            else:
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
                    self._put_event(st["intent_id"], {"action": "verify_pr", "instruction": "...", "evidence": {}})
                    del self.recovery_in_flight[sid]
                    continue

                if self.time_func() < st["next_probe_at"]:
                    continue

                if st["attempt"] >= 3:
                    try:
                        from agency.capabilities import _jules_patch
                        plan = await asyncio.to_thread(_jules_patch.build_recovery_plan, sid)
                    except ImportError:
                         # Phase 4 hasn't merged yet
                         plan = {}

                    self._put_event(st["intent_id"], {
                        "action": "recover_apply_plan",
                        "session": sid,
                        "state": "COMPLETED",
                        "instruction": INSTRUCTIONS["recover_apply_plan"],
                        "evidence": {"plan": plan}
                    })
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
                    acts = await asyncio.to_thread(_jules_api.jules_activities, sid, only_kinds="agentMessaged,planGenerated", page_size=5)
                    # Decorate curr with activities data
                    if acts and "activities" in acts and acts["activities"]:
                        for act in acts["activities"]:
                            if act.get("kind") == "agentMessaged" and "_last_agent_msg_id" not in curr:
                                curr["_last_agent_msg_id"] = act.get("id")
                                curr["_agent_message"] = act.get("agentMessaged", {}).get("message", "")
                            elif act.get("kind") == "planGenerated" and "plan_steps" not in curr:
                                 curr["plan_steps"] = len(act.get("planGenerated", {}).get("plan", {}).get("steps", []))
                            if "_last_agent_msg_id" in curr and "plan_steps" in curr:
                                break

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
                    event = _classify(prev, curr, sinfo["last_agent_msg_id"], branch_on_remote, patch_summary)

                    if event:
                        self._put_event(sinfo["intent_id"], event)
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
