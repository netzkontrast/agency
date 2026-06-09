"""Spec 110 Slice 1 — thinking capability tests.

Covers 10 method verbs + 1 composite verb + 1 walkable skill.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine
from agency.skill import SkillRun


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 110") -> str:
    iid = e.intent.capture(purpose, "deliverable", "acceptance")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "thinking", verb, **kw)


def test_thinking_capability_registers_11_verbs() -> None:
    """8 founding + 2 net-new + 1 composite = 11 verbs (Slice 1)."""
    e = _fresh()
    cap = e.registry._caps["thinking"]
    expected = {"decompose", "assumptions", "premortem",
                "first_principles", "inversion", "steelman",
                "second_order", "tradeoffs",
                # net-new in Spec 110
                "red_team", "socratic",
                # composite
                "apply_full_review"}
    assert set(cap.verbs) == expected
    e.memory.close()


def test_thinking_capability_lint_clean() -> None:
    from agency.capabilities.plugin import lint_capability
    e = Engine(":memory:", _require_skill_doc=False)
    res = lint_capability(e.registry._caps["thinking"])
    assert res["ok"] is True
    assert res.get("mode") == "block"
    assert len(res.get("violations", [])) == 0
    e.memory.close()


# ─────────────────────────── methods return scaffolds ───────────────────────

@pytest.mark.parametrize("method,extras", [
    ("decompose", {}),
    ("assumptions", {}),
    ("premortem", {}),
    ("first_principles", {}),
    ("inversion", {}),
    ("steelman", {"position": "ship the slice"}),
    ("second_order", {"n_steps": 4}),
    ("tradeoffs", {"options": "sqlite,postgres",
                    "criteria": "ops,latency,cost"}),
    ("red_team", {"n_attacks": 3}),
    ("socratic", {"n_questions": 4}),
])
def test_method_returns_scaffold(method, extras) -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, method, subject="ship spec 110", **extras)
    assert data["method"] == method
    assert "steps" in data
    assert len(data["steps"]) >= 3
    assert "output_schema" in data
    e.memory.close()


def test_method_defaults_subject_to_serving_intent() -> None:
    """When `subject` is empty, methods default to the serving intent's
    deliverable (Spec 091 pattern preserved)."""
    e = _fresh()
    iid = _confirmed_iid(e, purpose="ship 110")
    data, _ = _invoke(e, iid, "decompose")    # no subject argument
    assert data["subject"] != ""
    assert data["subject"] != "the current goal"
    e.memory.close()


def test_red_team_distinct_from_steelman() -> None:
    """steelman: argument against your POSITION; red_team: failure paths
    against your SYSTEM. Distinct method names; distinct output schemas."""
    e = _fresh()
    iid = _confirmed_iid(e)
    rt, _ = _invoke(e, iid, "red_team", subject="ship 110")
    sm, _ = _invoke(e, iid, "steelman", subject="ship 110",
                     position="ship now")
    assert rt["method"] == "red_team"
    assert sm["method"] == "steelman"
    assert "attacks" in rt["output_schema"]
    assert "counter_argument" in sm["output_schema"]
    e.memory.close()


def test_socratic_n_questions_threaded_through_scaffold() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "socratic", subject="x", n_questions=7)
    assert data["n_questions"] == 7
    assert any("7" in step for step in data["steps"])
    e.memory.close()


# ─────────────────────────── composite ───────────────────────────

def test_apply_full_review_produces_thinking_analysis_artefact() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "apply_full_review",
                      subject="ship 110", depth="standard")
    assert data["artefact"]["kind"] == "thinking-analysis"
    assert data["artefact"]["depth"] == "standard"
    # Sequence runs all 8 founding methods
    assert len(data["artefact"]["scaffolds"]) == 8
    methods = {s["method"] for s in data["artefact"]["scaffolds"]}
    expected_methods = {"decompose", "assumptions", "premortem",
                         "first_principles", "inversion", "steelman",
                         "second_order", "tradeoffs"}
    assert methods == expected_methods
    # Artefact PRODUCES'd against the intent
    prov = e.memory.provenance(iid)
    assert any(a["kind"] == "thinking-analysis" for a in prov["artefacts"])
    e.memory.close()


def test_apply_full_review_rejects_unknown_depth() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "apply_full_review",
                        subject="x", depth="nonsense")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "INVALID_ARGUMENT" in err
    e.memory.close()


def test_apply_full_review_defaults_subject_to_intent() -> None:
    e = _fresh()
    iid = _confirmed_iid(e, purpose="ship 110 thinking cap")
    data, _ = _invoke(e, iid, "apply_full_review", depth="shallow")
    # Subject defaulted to serving intent's deliverable
    assert data["artefact"]["subject"] != "the current goal"
    e.memory.close()


# ─────────────────────────── walkable skill ───────────────────────────

def test_critical_thinking_pass_skill_is_five_phased() -> None:
    e = _fresh()
    sk = e.ontology.skill("critical-thinking-pass")
    assert sk["kind"] == "workflow"
    assert len(sk["phases"]) == 5
    assert sk["phases"][-1].get("gate") == "hard"
    e.memory.close()


def test_critical_thinking_pass_walks_through_synthesis() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("critical-thinking-pass")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"sub_problems_listed": "yes"},
        {"load_bearing_marked": "yes"},
        {"failure_causes_listed": "yes"},
        {"counter_argument_tested": "yes"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"recommendation": "ship"},
                      confirmed=True)["status"] == "completed"
    e.memory.close()


# ─────────────────────────── ontology bites ───────────────────────────

def test_thinking_finding_severity_enum_bites() -> None:
    e = _fresh()
    with pytest.raises(ValueError):
        e.memory.record("ThinkingFinding",
                          {"method": "red_team",
                           "subject": "x", "severity": "nonsense"})
    e.memory.close()
