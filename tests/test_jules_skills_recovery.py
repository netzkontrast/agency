"""Spec 013 Phase 7 — `jules-recovery-when-stuck` skill.

Walked by the watcher's recover flow (Spec 012 §5; AGENCY_PROTOCOL.md §5).
4 phases, 1 hard gate at the end. Binds to four real verbs (jules.status,
jules.message, jules.patch); each phase is recorded in provenance.
"""
import tempfile

import pytest

from agency.engine import Engine
from agency.skill import SkillRun


class _StubJulesClient:
    """Records calls + returns canned responses for the four verbs the
    recovery skill walks."""
    def __init__(self):
        self.calls: list[tuple] = []

    def get(self, session):
        self.calls.append(("get", session))
        return {"id": session, "state": "COMPLETED",
                "url": f"https://jules.google.com/session/{session}"}

    def message(self, session, prompt):
        self.calls.append(("message", session, prompt))
        return {"ok": True}

    def patch(self, session):
        self.calls.append(("patch", session))
        return {"total_files": 1, "outputs": [
            {"index": 0, "files": 1, "lines": 10, "bytes": 200}
        ]}

    # Other Protocol methods — stubs (not exercised here).
    def create(self, **kw): return {"id": "x", "state": "QUEUED"}
    def list(self, page_size, page_token=""): return {"sessions": []}
    def activities(self, session, page_size, only_kinds, page_token=""): return {"activities": []}
    def plan(self, session, max_pages): return {"steps": []}
    def approve_plan(self, session): return {"ok": True}
    def resolve_source(self, owner, repo): return {"source": f"sources/{owner}-{repo}"}
    def get_full(self, session): return {"id": session, "outputs": []}
    def status_all(self, page_size, max_pages): return {"sessions": [], "total": 0}
    def approve_awaiting(self, limit): return {"approved": []}
    def quota(self, daily_limit): return {"active_today": 0, "headroom": 0}


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"), jules_client=_StubJulesClient())


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "recover a stuck Jules session",
        "skill walks 4 phases; hard gate at recovered",
        "all three verb-bound phases fire against the backend",
    )
    engine.intent.confirm(intent)
    return intent


def test_skill_registered_on_jules_ontology(engine):
    assert "jules-recovery-when-stuck" in engine.ontology.skills
    sk = engine.ontology.skill("jules-recovery-when-stuck")
    assert [p["name"] for p in sk["phases"]] == [
        "classify-state", "probe-once", "patch-or-empty", "recovered",
    ]


def test_only_recovered_is_a_hard_gate(engine):
    sk = engine.ontology.skill("jules-recovery-when-stuck")
    gates = [p for p in sk["phases"] if p.get("gate") == "hard"]
    assert len(gates) == 1 and gates[0]["name"] == "recovered"


def test_walk_fires_three_verb_bindings_then_hard_gate(engine, iid):
    sk = engine.ontology.skill("jules-recovery-when-stuck")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)

    # Phase 1 — classify-state binds to jules.status.
    res = run.submit({"session": "sess-stuck"})
    assert res["status"] == "working"
    assert run.current()["name"] == "probe-once"

    # Phase 2 — probe-once binds to jules.message.
    res = run.submit({"session": "sess-stuck",
                      "prompt": "your branch isn't on origin — push and reply with the PR URL, or reply EMPTY"})
    assert res["status"] == "working"
    assert run.current()["name"] == "patch-or-empty"

    # Phase 3 — patch-or-empty binds to jules.patch.
    res = run.submit({"session": "sess-stuck"})
    assert res["status"] == "working"
    assert run.current()["name"] == "recovered"

    # Phase 4 — recovered HARD GATE; needs pr_url AND confirmed.
    res = run.submit({"pr_url": "https://github.com/netzkontrast/agency/pull/42"})
    assert res["status"] == "input-required"
    assert res["gate"] == "hard"
    assert not run.done

    res = run.submit({"pr_url": "https://github.com/netzkontrast/agency/pull/42"},
                     confirmed=True)
    assert res["status"] == "completed"
    assert run.done

    # Backend got all three verb calls in order.
    client = engine.jules_client
    kinds = [c[0] for c in client.calls]
    assert kinds == ["get", "message", "patch"]


def test_walk_records_provenance(engine, iid):
    sk = engine.ontology.skill("jules-recovery-when-stuck")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"session": "sess-prov"})
    run.submit({"session": "sess-prov", "prompt": "p"})
    run.submit({"session": "sess-prov"})
    run.submit({"pr_url": "https://example/pr"}, confirmed=True)
    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:HAS_PHASE]->(p:Phase) "
        "WHERE s.name = $sn RETURN p",
        {"sn": "jules-recovery-when-stuck"},
    )
    assert len(rows) == 4


def test_empty_recovery_path_uses_sentinel_pr_url(engine, iid):
    """When the probe returns EMPTY (the agent had nothing to publish), the
    skill still completes by passing a sentinel string as pr_url. The
    walker treats any non-empty string as satisfying produces; semantics
    (sentinel vs real URL) live in the caller's interpretation."""
    sk = engine.ontology.skill("jules-recovery-when-stuck")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"session": "sess-empty"})
    run.submit({"session": "sess-empty", "prompt": "probe"})
    run.submit({"session": "sess-empty"})
    res = run.submit({"pr_url": "EMPTY"}, confirmed=True)
    assert res["status"] == "completed"
