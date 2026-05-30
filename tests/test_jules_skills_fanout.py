"""Spec 013 Phase 9 — `jules-fanout` skill.

3 phases: plan-batch -> fan-out (bound to `delegate.fan_out`) -> join HARD GATE.
The `delegate` capability owns the fan-out machinery; this skill is the
canonical composition that names Jules as the driver.
"""
import tempfile

import pytest

from agency.engine import Engine
from agency.skill import SkillRun


class _StubJulesClient:
    """Stub backend so `delegate.fan_out(driver="jules", driver_verb="dispatch", ...)`
    spawns real child invocations without hitting the Jules REST API."""
    def create(self, **kw):
        return {"id": f"sessions/{abs(hash(kw.get('prompt','')))%1000}",
                "state": "QUEUED", "url": "https://jules.google.com/x"}
    def get(self, session): return {"id": session, "state": "QUEUED"}
    def list(self, page_size, page_token=""): return {"sessions": []}
    def activities(self, session, page_size, only_kinds, page_token=""): return {"activities": []}
    def plan(self, session, max_pages): return {"steps": []}
    def approve_plan(self, session): return {"ok": True}
    def message(self, session, prompt): return {"ok": True}
    def resolve_source(self, owner, repo): return {"source": f"sources/{owner}-{repo}"}
    def get_full(self, session): return {"id": session, "outputs": []}
    def status_all(self, page_size, max_pages): return {"sessions": [], "total": 0}
    def approve_awaiting(self, limit): return {"approved": []}
    def quota(self, daily_limit): return {"active_today": 0, "headroom": 0}
    def patch(self, session): return {"total_files": 0, "outputs": []}


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"), jules_client=_StubJulesClient())


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "fan out two Jules dispatches",
        "skill walks; delegate.fan_out spawns 2 children",
        "join hard gate elicits before completion",
    )
    engine.intent.confirm(intent)
    return intent


def test_skill_registered_on_jules_ontology(engine):
    assert "jules-fanout" in engine.ontology.skills
    sk = engine.ontology.skill("jules-fanout")
    assert [p["name"] for p in sk["phases"]] == ["plan-batch", "fan-out", "join"]


def test_join_is_the_hard_gate(engine):
    sk = engine.ontology.skill("jules-fanout")
    gates = [p for p in sk["phases"] if p.get("gate") == "hard"]
    assert len(gates) == 1 and gates[0]["name"] == "join"


def test_walk_fans_out_two_children_then_hard_gates(engine, iid):
    items = [
        {"prompt": "task A", "source": "netzkontrast/agency", "starting_branch": "main"},
        {"prompt": "task B", "source": "netzkontrast/agency", "starting_branch": "main"},
    ]
    sk = engine.ontology.skill("jules-fanout")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)

    # Phase 1 — plan-batch: document phase, caller supplies items.
    res = run.submit({"items": items})
    assert res["status"] == "working"

    # Phase 2 — fan-out: binds to delegate.fan_out(driver="jules", verb="dispatch", ...).
    res = run.submit({
        "driver": "jules",
        "driver_verb": "dispatch",
        "items": items,
        "quota": 8,
    })
    assert res["status"] == "working"
    assert run.current()["name"] == "join"

    # Phase 3 — join HARD GATE.
    res = run.submit({"child_outcomes": [{"id": "c1", "state": "done"},
                                          {"id": "c2", "state": "done"}]})
    assert res["status"] == "input-required"
    assert res["gate"] == "hard"
    assert not run.done

    res = run.submit({"child_outcomes": [{"id": "c1", "state": "done"},
                                          {"id": "c2", "state": "done"}]},
                     confirmed=True)
    assert res["status"] == "completed"
    assert run.done

    # The fan-out spawned 2 Delegation/child Lifecycle nodes for this intent.
    rows = engine.memory.g.query(
        "MATCH (d:Delegation)-[:SERVES]->(i:Intent) "
        "WHERE i.id = $iid RETURN d",
        {"iid": iid},
    )
    assert len(rows) == 1
    assert rows[0]["d"]["properties"]["count"] == 2


def test_phases_record_provenance(engine, iid):
    items = [{"prompt": "x", "source": "netzkontrast/agency", "starting_branch": "main"}]
    sk = engine.ontology.skill("jules-fanout")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"items": items})
    run.submit({"driver": "jules", "driver_verb": "dispatch",
                "items": items, "quota": 4})
    run.submit({"child_outcomes": [{"id": "c1"}]}, confirmed=True)
    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:HAS_PHASE]->(p:Phase) "
        "WHERE s.name = $sn RETURN p",
        {"sn": "jules-fanout"},
    )
    assert len(rows) == 3
