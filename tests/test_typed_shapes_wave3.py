"""Wave-3 typed-shape batch tests."""
from __future__ import annotations

import pytest

from agency._typed_shapes_wave3 import (
    ChainHint,
    ClusterCoherence,
    FanoutAgent,
    FanoutPlan,
    JudgeVerdict,
    NarrativeSection,
)


def test_judge_verdict():
    v = JudgeVerdict(axis="quality", confidence=0.9, rationale="ok",
                      findings=("F-001",))
    assert v.axis == "quality"


def test_judge_rejects_invalid_axis():
    with pytest.raises(ValueError):
        JudgeVerdict(axis="bogus", confidence=0.5, rationale="r")


def test_judge_rejects_conf_out_of_range():
    with pytest.raises(ValueError):
        JudgeVerdict(axis="quality", confidence=2.0, rationale="r")


def test_judge_rejects_long_rationale():
    with pytest.raises(ValueError):
        JudgeVerdict(axis="quality", confidence=0.5, rationale="a" * 501)


def test_narrative_section():
    s = NarrativeSection(heading="H", body="b", cite_count=3)
    assert s.heading == "H"


def test_narrative_rejects_empty():
    with pytest.raises(ValueError):
        NarrativeSection(heading="", body="b", cite_count=0)
    with pytest.raises(ValueError):
        NarrativeSection(heading="H", body="", cite_count=0)


def test_narrative_rejects_negative_cites():
    with pytest.raises(ValueError):
        NarrativeSection(heading="H", body="b", cite_count=-1)


def test_fanout_agent():
    a = FanoutAgent(role="security", query="q", timeout_s=10)
    assert a.role == "security"


def test_fanout_agent_rejects_invalid_timeout():
    with pytest.raises(ValueError):
        FanoutAgent(role="r", query="q", timeout_s=0)


def test_fanout_plan():
    p = FanoutPlan(research_id="r:1",
                    agents=(FanoutAgent(role="r", query="q"),),
                    max_parallel=2)
    assert p.max_parallel == 2


def test_fanout_plan_rejects_empty_agents():
    with pytest.raises(ValueError):
        FanoutPlan(research_id="r:1", agents=(), max_parallel=1)


def test_cluster_coherence():
    c = ClusterCoherence(cluster_id="c:1", status="coherent",
                          audited_at="t")
    assert c.status == "coherent"


def test_cluster_coherence_rejects_invalid_status():
    with pytest.raises(ValueError):
        ClusterCoherence(cluster_id="c:1", status="bogus",
                          audited_at="t")


def test_chain_hint():
    h = ChainHint(source_intent_id="intent:x",
                   target_verb="analyze.run",
                   kind="chain_next", confidence=0.8)
    assert h.kind == "chain_next"


def test_chain_hint_rejects_invalid_kind():
    with pytest.raises(ValueError):
        ChainHint(source_intent_id="x", target_verb="v",
                   kind="bogus", confidence=0.5)


def test_chain_hint_rejects_conf_out_of_range():
    with pytest.raises(ValueError):
        ChainHint(source_intent_id="x", target_verb="v",
                   kind="chain_next", confidence=1.5)
