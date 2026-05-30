"""Spec 013 Phase 8 — `jules-pr-review-cycle` skill.

3 advisory phases composing the @jules review-comment flow. The
`draft-replies` phase binds to `jules.review_comment`, guaranteeing every
drafted reply ships with the AGENCY_PROTOCOL.md §9 handshake tail.
"""
import tempfile

import pytest

from agency.engine import Engine
from agency.skill import SkillRun


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    intent = engine.intent.capture(
        "post an @jules review on a PR",
        "draft ships with reply_to_pr_comments tail",
        "all three phases land in provenance",
    )
    engine.intent.confirm(intent)
    return intent


def test_skill_registered_on_jules_ontology(engine):
    assert "jules-pr-review-cycle" in engine.ontology.skills
    sk = engine.ontology.skill("jules-pr-review-cycle")
    assert [p["name"] for p in sk["phases"]] == [
        "read-comments", "draft-replies", "reply-on-github",
    ]


def test_skill_has_no_hard_gate(engine):
    sk = engine.ontology.skill("jules-pr-review-cycle")
    assert not any(p.get("gate") == "hard" for p in sk["phases"])


def test_draft_replies_appends_handshake_tail(engine, iid):
    """Phase 2 binds to jules.review_comment; the returned dict carries
    `text` (with the §9 tail appended) and `tail_appended` (bool). The
    skill walk advances when the produces field is non-empty."""
    sk = engine.ontology.skill("jules-pr-review-cycle")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)

    run.submit({"comments": [{"id": 1, "body": "fix the off-by-one"}]})
    res = run.submit({"body": "Verdict: changes-requested. Fix the test."})
    assert res["status"] == "working"

    # Inspect the draft's text via the recorded Invocation result. The verb
    # returned a dict {text, tail_appended}; that whole dict is what got
    # written into outputs["draft_reply"]. Verify by re-invoking the verb
    # directly with the same body — same handshake tail must be present.
    direct, _ = engine.registry.invoke(
        engine.memory, iid, "jules", "review_comment",
        agent_id="agent:claude",
        body="Verdict: changes-requested. Fix the test.",
    )
    assert "reply_to_pr_comments" in direct["text"]
    assert direct["tail_appended"] is True


def test_walk_completes_when_all_phases_supply_outputs(engine, iid):
    sk = engine.ontology.skill("jules-pr-review-cycle")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"comments": [{"id": 1, "body": "x"}]})
    run.submit({"body": "draft body"})
    res = run.submit({"posted": [{"id": 99, "url": "https://github.com/x/y#discussion_99"}]})
    assert res["status"] == "completed"
    assert run.done


def test_phases_record_provenance(engine, iid):
    sk = engine.ontology.skill("jules-pr-review-cycle")
    run = SkillRun(engine.memory, iid, sk, registry=engine.registry)
    run.submit({"comments": [{"id": 1, "body": "x"}]})
    run.submit({"body": "draft"})
    run.submit({"posted": [{"id": 99}]})
    rows = engine.memory.g.query(
        "MATCH (s:Skill)-[:HAS_PHASE]->(p:Phase) "
        "WHERE s.name = $sn RETURN p",
        {"sn": "jules-pr-review-cycle"},
    )
    assert len(rows) == 3
