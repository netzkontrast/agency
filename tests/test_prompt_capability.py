"""Spec 109 Slice 1 — prompt capability tests.

Covers 7 user verbs + 2 gate verbs + 2 walkable skills + 2 templates.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine
from agency.skill import SkillRun


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 109") -> str:
    iid = e.intent.capture(purpose, "deliverable", "acceptance")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "prompt", verb, **kw)


# ─────────────────────────── surface invariants ───────────────────────────

def test_prompt_capability_registers_9_verbs() -> None:
    """7 user + 2 gate = 9 verbs total (Slice 1 surface)."""
    e = _fresh()
    cap = e.registry._caps["prompt"]
    expected = {"intent_capture", "catalog_list", "brief_render",
                "brief_audit", "brief_finalize",
                "engineer", "audit",
                "token_budget_gate", "audit_gate"}
    assert set(cap.verbs) == expected
    e.memory.close()


def test_prompt_capability_registers_two_walkable_skills() -> None:
    e = _fresh()
    cap = e.registry._caps["prompt"]
    assert {"dossier-author", "prompt-engineering-pass"} == set(cap.ontology.skills)
    e.memory.close()


def test_prompt_capability_lint_clean_in_block_mode() -> None:
    from agency.capabilities.plugin import lint_capability
    e = Engine(":memory:", _require_skill_doc=False)
    res = lint_capability(e.registry._caps["prompt"])
    assert res["ok"] is True
    assert res.get("mode") == "block"
    assert len(res.get("violations", [])) == 0
    e.memory.close()


# ─────────────────────────── intent_capture ───────────────────────────

def test_intent_capture_records_research_intent_node() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "intent_capture",
                      seed_query="how did 80s modems shape phreaker culture",
                      topic="phreakers + modems",
                      deliverable="dossier",
                      success_criteria="primary sources cited")
    assert data["deliverable"] == "dossier"
    assert data["intent_id"].startswith("researchintent:")
    # SERVES edge to the serving intent
    rows = e.memory.g.query(
        "MATCH (r)-[s:SERVES]->(i) WHERE r.id = $rid AND i.id = $iid RETURN s",
        {"rid": data["intent_id"], "iid": iid})
    assert rows
    e.memory.close()


def test_intent_capture_rejects_unknown_deliverable() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "intent_capture",
                        seed_query="x", topic="t",
                        deliverable="nonsense")
    assert data is None
    assert "INVALID_ARGUMENT" in e.memory.recall(inv).get("error", "")
    e.memory.close()


# ─────────────────────────── catalog_list ───────────────────────────

def test_catalog_list_returns_seed_modules() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "catalog_list")
    assert data["count"] == 6
    cats = {m["category"] for m in data["modules"]}
    assert cats == {"A", "B", "C"}
    e.memory.close()


def test_catalog_list_filters_by_category() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "catalog_list", category="A")
    assert data["count"] == 3
    assert all(m["category"] == "A" for m in data["modules"])
    e.memory.close()


def test_catalog_list_rejects_unknown_category() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "catalog_list", category="Z")
    assert data is None
    assert "INVALID_ARGUMENT" in e.memory.recall(inv).get("error", "")
    e.memory.close()


# ─────────────────────────── brief_render ───────────────────────────

def test_brief_render_produces_research_dossier_artefact() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    intent_res, _ = _invoke(e, iid, "intent_capture",
                             seed_query="x", topic="modems",
                             deliverable="dossier",
                             success_criteria="primary cites")
    brief_res, _ = _invoke(e, iid, "brief_render",
                            research_intent_id=intent_res["intent_id"],
                            module_ids="M01,M03,M06")
    assert brief_res["artefact"]["kind"] == "research-dossier"
    body = brief_res["result"]
    assert "modems" in body
    assert "M01" in body and "M03" in body and "M06" in body
    # RENDERS_FROM edge landed
    rows = e.memory.g.query(
        "MATCH (b:ResearchBrief)-[r:RENDERS_FROM]->(i:ResearchIntent) "
        "WHERE i.id = $iid RETURN r",
        {"iid": intent_res["intent_id"]})
    assert rows
    e.memory.close()


def test_brief_render_not_found_intent() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "brief_render",
                        research_intent_id="bogus:does-not-exist")
    assert data is None
    assert "NOT_FOUND" in e.memory.recall(inv).get("error", "")
    e.memory.close()


# ─────────────────────────── brief_audit + brief_finalize ──────────────

def test_brief_audit_records_audit_node_and_status() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    intent_res, _ = _invoke(e, iid, "intent_capture",
                             seed_query="x", topic="t",
                             deliverable="dossier")
    brief_res, _ = _invoke(e, iid, "brief_render",
                            research_intent_id=intent_res["intent_id"])
    audit, _ = _invoke(e, iid, "brief_audit",
                       brief_id=brief_res["artefact"]["brief_id"])
    assert "clarity_score" in audit
    assert audit["status"] in {"passed", "failed"}
    assert audit["audit_id"].startswith("briefaudit:")
    # AUDITS edge landed
    rows = e.memory.g.query(
        "MATCH (a)-[r:AUDITS]->(b:ResearchBrief) "
        "WHERE b.id = $bid RETURN r",
        {"bid": brief_res["artefact"]["brief_id"]})
    assert rows
    e.memory.close()


def test_brief_finalize_flips_status() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    intent_res, _ = _invoke(e, iid, "intent_capture",
                             seed_query="x", topic="t",
                             deliverable="dossier")
    brief_res, _ = _invoke(e, iid, "brief_render",
                            research_intent_id=intent_res["intent_id"])
    fin, _ = _invoke(e, iid, "brief_finalize",
                     brief_id=brief_res["artefact"]["brief_id"])
    assert fin["finalized"] is True
    e.memory.close()


# ─────────────────────────── engineer + audit ───────────────────────────

def test_engineer_renders_prompt_instance_within_budget() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "engineer",
                      builder_kind="dialogue-prompt",
                      context="A phreaker dialing into BBS",
                      constraints="[under 100 words; period setting]")
    assert data["artefact"]["kind"] == "prompt-instance"
    assert data["artefact"]["builder_kind"] == "dialogue-prompt"
    assert "approx_tokens" in data["artefact"]
    assert data["artefact"]["approx_tokens"] > 0
    e.memory.close()


def test_engineer_refuses_over_budget_prompt() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    # Very tight budget
    data, inv = _invoke(e, iid, "engineer",
                        builder_kind="dialogue-prompt",
                        context="x " * 200,           # ~400 chars
                        constraints="y " * 200,
                        max_tokens=10)
    assert data is None
    assert "INVALID_ARGUMENT" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_audit_general_case_scores_prompt() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "audit",
                      prompt_body="# Sample prompt\n[constraint A]\n[constraint B]\n")
    assert "clarity_score" in data
    assert data["status"] in {"passed", "failed"}
    e.memory.close()


def test_audit_penalizes_vague_words() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    clean, _ = _invoke(e, iid, "audit",
                       prompt_body="Write a poem [tight, sharp] about modems.")
    vague, _ = _invoke(e, iid, "audit",
                       prompt_body="Maybe write something really kind of cool about modems.")
    assert vague["clarity_score"] < clean["clarity_score"]
    e.memory.close()


# ─────────────────────────── token_budget_gate ───────────────────────────

def test_token_budget_gate_passes_under_budget() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, _ = _invoke(e, iid, "token_budget_gate",
                      lifecycle_id=lc,
                      prompt_body="short prompt",
                      max_tokens=100)
    assert data["passed"] is True
    e.memory.close()


def test_token_budget_gate_blocks_over_budget() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    data, inv = _invoke(e, iid, "token_budget_gate",
                        lifecycle_id=lc,
                        prompt_body="x " * 200,
                        max_tokens=10)
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "GATE_FAILED" in err and "token-budget" in err
    assert e.memory.recall(lc).get("state") == "input-required"
    e.memory.close()


def test_audit_gate_blocks_low_clarity() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    lc = e.lifecycle.open(iid)
    # No bracket markers AND vague words → low score
    data, inv = _invoke(e, iid, "audit_gate",
                        lifecycle_id=lc,
                        prompt_body="Just maybe write something kind of like that.",
                        min_score=70)
    assert data is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    e.memory.close()


# ─────────────────────────── walkable skills ───────────────────────────

def test_dossier_author_skill_is_five_phased() -> None:
    e = _fresh()
    sk = e.ontology.skill("dossier-author")
    assert sk["kind"] == "workflow"
    assert len(sk["phases"]) == 5
    assert sk["phases"][-1].get("gate") == "hard"
    e.memory.close()


def test_prompt_engineering_pass_skill_is_six_phased() -> None:
    e = _fresh()
    sk = e.ontology.skill("prompt-engineering-pass")
    assert sk["kind"] == "workflow"
    assert len(sk["phases"]) == 6
    assert sk["phases"][-1].get("gate") == "hard"
    e.memory.close()


def test_dossier_author_skill_walks_through_finalize() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("dossier-author")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"intent_recorded": "yes"},
        {"catalog_modules_chosen": "M01,M03,M06"},
        {"brief_body_rendered": "yes"},
        {"audit_findings": "passed"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"brief_finalized": "yes"},
                      confirmed=True)["status"] == "completed"
    e.memory.close()


def test_research_intent_deliverable_enum_bites_at_record_time() -> None:
    e = _fresh()
    with pytest.raises(ValueError):
        e.memory.record("ResearchIntent",
                          {"seed_query": "x", "topic": "t",
                           "deliverable": "nonsense"})
    e.memory.close()
