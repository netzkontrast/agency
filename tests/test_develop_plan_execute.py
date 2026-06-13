"""Spec 287 — develop `plan-execute` discipline + Plan/PlanStep provenance.

A first-class plan-authoring → execution-with-checkpoints discipline
(superpowers writing-plans + executing-plans + subagent-driven-development;
superclaude sc-workflow + sc-task). The plan is graph provenance (rule 2):
`draft_plan` mints a `Plan` + `PlanStep` nodes SERVING the intent; the
walkable skill drives author → hard-gate sign-off → execute → checkpoints.
"""
from __future__ import annotations


def _invoke(engine, iid, verb, **args):
    raw, _ = engine.registry.invoke(engine.memory, iid, "develop", verb, **args)
    return raw["result"] if isinstance(raw, dict) and "result" in raw else raw


# --- draft_plan: bite-sized plan as graph nodes ----------------------------


def test_draft_plan_mints_plan_and_steps(engine, iid):
    out = _invoke(engine, iid, "draft_plan", title="Ship feature X",
                  steps='["write a failing test", "implement", "verify"]')
    assert out["count"] == 3
    assert out["plan_id"] and len(out["step_ids"]) == 3
    plan = engine.memory.recall(out["plan_id"])
    assert plan["title"] == "Ship feature X"
    psteps = [s for s in engine.memory.find("PlanStep")
              if s.get("plan") == out["plan_id"]]
    assert len(psteps) == 3
    assert all(s["state"] == "pending" for s in psteps)
    assert sorted(int(s["index"]) for s in psteps) == [1, 2, 3]


def test_draft_plan_accepts_newline_steps(engine, iid):
    out = _invoke(engine, iid, "draft_plan", title="t",
                  steps="step a\nstep b\n")
    assert out["count"] == 2


def test_draft_plan_serves_intent(engine, iid):
    out = _invoke(engine, iid, "draft_plan", title="t", steps='["a"]')
    # the Plan node SERVES the serving intent (the provenance moat)
    serving = engine.memory.neighbors if False else None  # neighbors is on ctx, not memory
    rows = engine.memory.g.query(
        "MATCH (p:Plan)-[:SERVES]->(i:Intent) WHERE i.id = $iid RETURN p",
        {"iid": iid})
    assert any(r["p"]["properties"].get("id") == out["plan_id"]
               or r["p"]["properties"].get("title") == "t" for r in rows)


# --- record_step_outcome: execution state ----------------------------------


def test_record_step_outcome_updates_state(engine, iid):
    plan = _invoke(engine, iid, "draft_plan", title="t", steps='["a", "b"]')
    sid = plan["step_ids"][0]
    out = _invoke(engine, iid, "record_step_outcome", step_id=sid,
                  outcome="done", evidence="tests pass")
    assert out["state"] == "done"
    node = engine.memory.recall(sid)
    assert node["state"] == "done" and node["evidence"] == "tests pass"


def test_record_step_outcome_rejects_bad_outcome(engine, iid):
    plan = _invoke(engine, iid, "draft_plan", title="t", steps='["a"]')
    out = _invoke(engine, iid, "record_step_outcome",
                  step_id=plan["step_ids"][0], outcome="finished")
    assert "error" in out and "done" in out["error"]


# --- plan_status: read-side roll-up ----------------------------------------


def test_plan_status_reports_steps_and_completion(engine, iid):
    plan = _invoke(engine, iid, "draft_plan", title="t", steps='["a", "b"]')
    st = _invoke(engine, iid, "plan_status", plan_id=plan["plan_id"])
    assert st["complete"] is False and len(st["steps"]) == 2
    assert [s["index"] for s in st["steps"]] == [1, 2]
    for sid in plan["step_ids"]:
        _invoke(engine, iid, "record_step_outcome", step_id=sid, outcome="done")
    st2 = _invoke(engine, iid, "plan_status", plan_id=plan["plan_id"])
    assert st2["complete"] is True


# --- the walkable discipline -----------------------------------------------


def test_plan_execute_skill_registered_with_hard_gates(engine):
    skills = engine.registry.get("develop").ontology.skills
    assert "plan-execute" in skills
    phases = skills["plan-execute"]["phases"]
    names = [p["name"] for p in phases]
    assert names == ["frame", "draft-plan", "plan-signoff",
                     "execute-step", "checkpoint", "synthesize"]
    hard = {p["name"] for p in phases if p.get("gate") == "hard"}
    assert {"plan-signoff", "checkpoint", "synthesize"} <= hard
    draft = next(p for p in phases if p["name"] == "draft-plan")
    assert draft["invoke"] == {"capability": "develop", "verb": "draft_plan"}
    assert draft["produces"] == ["plan"]          # single produce (invoke contract)


def test_plan_execute_walk_pauses_at_signoff(engine, iid):
    res = _invoke(engine, iid, "skill_walk", name="plan-execute",
                  inputs={"requirements": "ship X", "title": "Ship X",
                          "steps": '["write test", "implement"]'})
    assert res["status"] == "input-required"
    assert res["phase"] == "plan-signoff"
    assert res["skill_id"]
    # the bound draft-plan phase ran for real → a Plan with 2 steps exists
    plans = engine.memory.find("Plan")
    assert plans, "draft-plan phase should have minted a Plan node"
    assert len([s for s in engine.memory.find("PlanStep")]) == 2
