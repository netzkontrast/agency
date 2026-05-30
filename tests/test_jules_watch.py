import asyncio
import pytest
from agency.capabilities._jules_watch import INSTRUCTIONS, _classify, Watcher

def test_instructions_complete():
    assert len(INSTRUCTIONS) == 9
    assert "noop" in INSTRUCTIONS
    assert "review_and_approve_plan" in INSTRUCTIONS
    assert "answer_agent_question" in INSTRUCTIONS
    assert "verify_pr" in INSTRUCTIONS
    assert "recover_silent_fail" in INSTRUCTIONS
    assert "recover_apply_plan" in INSTRUCTIONS
    assert "dispatch_fresh" in INSTRUCTIONS
    assert "inspect_and_resume" in INSTRUCTIONS
    assert "terminal" in INSTRUCTIONS

def test_classify_transitions():
    # 1. baseline-seed
    assert _classify(None, {"id": "1", "state": "QUEUED"}, None, False, None) is None

    # 2. same state + same agent msg
    prev = {"id": "1", "state": "AWAITING_USER_FEEDBACK"}
    curr = {"id": "1", "state": "AWAITING_USER_FEEDBACK", "_last_agent_msg_id": "m1"}
    assert _classify(prev, curr, "m1", False, None) is None

    # 3. same state + new agent msg
    curr["_agent_message"] = "test msg"
    curr["url"] = "http"
    res = _classify(prev, curr, "m0", False, None)
    assert res is not None
    assert res["action"] == "answer_agent_question"
    assert res["instruction"] == INSTRUCTIONS["answer_agent_question"].format(agent_message="test msg")

    # 4. terminal-stickiness
    prev = {"id": "1", "state": "FAILED"}
    curr = {"id": "1", "state": "IN_PROGRESS"}
    assert _classify(prev, curr, None, False, None) is None

    # 5. verify action mappings
    assert _classify({"state": "QUEUED"}, {"id": "1", "state": "PLANNING"}, None, False, None)["action"] == "noop"

    res = _classify({"state": "PLANNING"}, {"id": "1", "state": "AWAITING_PLAN_APPROVAL", "plan_steps": 5, "url": "x"}, None, False, None)
    assert res["action"] == "review_and_approve_plan"
    assert res["evidence"]["plan_steps"] == 5

    assert _classify({"state": "QUEUED"}, {"id": "1", "state": "IN_PROGRESS"}, None, False, None)["action"] == "noop"

    res = _classify({"state": "IN_PROGRESS"}, {"id": "1", "state": "COMPLETED", "branch": "b1", "pr_url": "u"}, None, True, None)
    assert res["action"] == "verify_pr"

    res = _classify({"state": "IN_PROGRESS"}, {"id": "1", "state": "COMPLETED"}, None, False, {"files": 2, "lines": 10, "bytes": 200})
    assert res["action"] == "recover_silent_fail"
    assert res["evidence"]["files"] == 2

    res = _classify({"state": "IN_PROGRESS"}, {"id": "1", "state": "COMPLETED", "_prompt_hash": "h"}, None, False, {"files": 0, "lines": 0, "bytes": 0})
    assert res["action"] == "dispatch_fresh"

    res = _classify({"state": "IN_PROGRESS"}, {"id": "1", "state": "COMPLETED", "_prompt_hash": "h"}, None, False, None)
    assert res["action"] == "dispatch_fresh"

    res = _classify({"state": "IN_PROGRESS"}, {"id": "1", "state": "FAILED", "error": "err", "url": "u"}, None, False, None)
    assert res["action"] == "dispatch_fresh"
    assert "FAILED: err" in res["instruction"]

    res = _classify({"state": "IN_PROGRESS"}, {"id": "1", "state": "PAUSED", "url": "u"}, None, False, None)
    assert res["action"] == "inspect_and_resume"

    res = _classify({"state": "IN_PROGRESS"}, {"id": "1", "state": "CANCELLED", "cause": "usr"}, None, False, None)
    assert res["action"] == "terminal"

@pytest.mark.asyncio
async def test_queue_drop_oldest():
    watcher = Watcher()
    q = watcher._get_queue("intent_1")
    for i in range(10): # maxsize is 8
        watcher._put_event("intent_1", {"index": i})

    assert q.qsize() == 8
    first = await q.get()
    assert first["index"] == 2 # 0 and 1 were dropped

def test_cadence_calculator():
    now = 1000.0
    def fake_time():
        return now

    watcher = Watcher(time_func=fake_time)

    # Empty
    assert watcher._calc_cadence() == 30.0

    # 10s for first 5 mins
    watcher.arm(None, "intent_1", "sid_1")
    assert watcher._calc_cadence() == 10.0

    # Move forward 4 mins
    now = 1000.0 + 4 * 60
    assert watcher._calc_cadence() == 10.0

    # Move forward 6 mins (30s)
    now = 1000.0 + 6 * 60
    assert watcher._calc_cadence() == 30.0

    # Move forward 21 mins (300s)
    now = 1000.0 + 21 * 60
    assert watcher._calc_cadence() == 300.0

    # 429 backoff
    watcher._429_count = 1
    assert watcher._calc_cadence() == 20.0

    watcher._429_count = 5 # 10 * 32 = 320
    assert watcher._calc_cadence() == 320.0

    watcher._429_count = 10
    assert watcher._calc_cadence() == 600.0

@pytest.mark.asyncio
async def test_recovery_cycle():
    now = 1000.0
    def fake_time():
        return now

    class FakeEngine:
        pass


    watcher = Watcher(time_func=fake_time)

    # Simulate jules.recover adding to in_flight
    watcher.recovery_in_flight["sid_1"] = {
        "attempt": 0,
        "next_probe_at": now + 5*60,
        "started_at": now,
        "intent_id": "intent_1"
    }

    # Mock jules api and verify_truth
    api_calls = []

    async def mock_jules_message(sid, prompt):
        api_calls.append(("message", sid, prompt))

    async def mock_verify_truth(sid):
        # We'll say branch is not on remote
        return None, False

    async def mock_build_recovery_plan(sid):
        return {"plan": "mock_plan"}

    async def loop_body():
        for sid, st in list(watcher.recovery_in_flight.items()):
            _, branch_on_remote = await mock_verify_truth(sid)
            if branch_on_remote:
                watcher._put_event(st["intent_id"], {"action": "verify_pr"})
                del watcher.recovery_in_flight[sid]
                continue

            if watcher.time_func() < st["next_probe_at"]:
                continue

            if st["attempt"] >= 3:
                plan = await mock_build_recovery_plan(sid)
                watcher._put_event(st["intent_id"], {"action": "recover_apply_plan", "evidence": {"plan": plan}})
                del watcher.recovery_in_flight[sid]
                continue

            st["attempt"] += 1
            st["next_probe_at"] = watcher.time_func() + 5*60
            await mock_jules_message(sid, "PROBE_PROMPT")

    # Attempt 0 -> wait 5 min
    await loop_body()
    assert len(api_calls) == 0
    assert watcher.recovery_in_flight["sid_1"]["attempt"] == 0

    # Attempt 1
    now += 5*60
    await loop_body()
    assert len(api_calls) == 1
    assert watcher.recovery_in_flight["sid_1"]["attempt"] == 1

    # Attempt 2
    now += 5*60
    await loop_body()
    assert len(api_calls) == 2
    assert watcher.recovery_in_flight["sid_1"]["attempt"] == 2

    # Attempt 3
    now += 5*60
    await loop_body()
    assert len(api_calls) == 3
    assert watcher.recovery_in_flight["sid_1"]["attempt"] == 3

    # Exhaust
    now += 5*60
    await loop_body()
    assert len(api_calls) == 3
    assert "sid_1" not in watcher.recovery_in_flight

    # Check queue
    q = watcher._get_queue("intent_1")
    event = await q.get()
    assert event["action"] == "recover_apply_plan"
