"""Spec 114 Slice 1 — plugin-as-session-driver tests.

Validates the 6 new verbs across 3 capabilities plus the walkable skill:
- `develop.session_init` mints SessionLifecycle SERVES intent + auto-detects mode
- `develop.session_check` reads SessionLifecycle state + mode history
- `develop.mode_select` records ModeShift + flips SessionLifecycle.mode
- `reflect.synthesize_session` produces session-reflection artefact + archives lifecycle
- `dogfood.record_decision` records DecisionRecord + RELATES_TO session
- `dogfood.boundary_use_audit` reads BoundaryUse nodes + suggests verbs
- `session-driver-pass` walkable skill walks through the 5-phase lifecycle
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine
from agency.skill import SkillRun


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 114") -> str:
    iid = e.intent.capture(purpose, "session driver slice 1", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, cap: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, cap, verb, **kw)


# ─────────────────────────── session_init ───────────────────────────

def test_session_init_mints_session_lifecycle_serves_intent() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    res, _ = _invoke(e, iid, "develop", "session_init",
                      purpose="ship 114", mode_hint="brainstorming")
    assert res["session_lifecycle_id"].startswith("sessionlifecycle:")
    assert res["intent_id"] == iid
    assert res["mode"] == "brainstorming"
    assert res["suggested_first_verb"]
    # SERVES edge landed
    rows = e.memory.g.query(
        "MATCH (s)-[r:SERVES]->(i) WHERE s.id = $sid AND i.id = $iid RETURN r",
        {"sid": res["session_lifecycle_id"], "iid": iid})
    assert rows, "SessionLifecycle SERVES Intent edge missing"
    e.memory.close()


def test_session_init_mode_hint_honored() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    res, _ = _invoke(e, iid, "develop", "session_init",
                      mode_hint="spec-authoring")
    assert res["mode"] == "spec-authoring"
    assert res["suggested_first_verb"] == "develop.checklist"
    e.memory.close()


def test_session_init_rejects_unknown_mode_hint_silently() -> None:
    """An unknown mode_hint falls through to auto-detect (cwd-based)."""
    e = _fresh()
    iid = _confirmed_iid(e)
    res, _ = _invoke(e, iid, "develop", "session_init",
                      mode_hint="not-a-mode")
    assert res["mode"] in {"brainstorming", "spec-authoring",
                            "coding", "review", "synthesize"}
    e.memory.close()


def test_session_lifecycle_mode_enum_bites() -> None:
    """(SessionLifecycle, mode) is closed to SESSION_MODE — direct
    Memory.record of an unknown value raises (graph-level guard)."""
    e = _fresh()
    with pytest.raises(ValueError):
        e.memory.record("SessionLifecycle",
                          {"mode": "nonsense", "status": "active"})
    e.memory.close()


# ─────────────────────────── session_check ───────────────────────────

def test_session_check_reads_explicit_lifecycle() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    init, _ = _invoke(e, iid, "develop", "session_init",
                       mode_hint="brainstorming")
    sid = init["session_lifecycle_id"]
    check, _ = _invoke(e, iid, "develop", "session_check",
                        session_lifecycle_id=sid)
    assert check["mode"] == "brainstorming"
    assert check["status"] == "active"
    e.memory.close()


def test_session_check_falls_back_to_most_recent() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    _invoke(e, iid, "develop", "session_init",
             mode_hint="brainstorming")
    check, _ = _invoke(e, iid, "develop", "session_check")
    assert check["mode"] == "brainstorming"
    e.memory.close()


def test_session_check_not_found_returns_empty_state() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    check, _ = _invoke(e, iid, "develop", "session_check",
                        session_lifecycle_id="bogus:does-not-exist")
    assert check["status"] == "not_found"
    e.memory.close()


# ─────────────────────────── mode_select ───────────────────────────

def test_mode_select_records_mode_shift_and_flips_mode() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    init, _ = _invoke(e, iid, "develop", "session_init",
                       mode_hint="brainstorming")
    sid = init["session_lifecycle_id"]
    shift, _ = _invoke(e, iid, "develop", "mode_select",
                        session_lifecycle_id=sid, new_mode="coding",
                        reason="spec drafted; implementation begins")
    assert shift["from_mode"] == "brainstorming"
    assert shift["to_mode"] == "coding"
    assert shift["mode_shift_id"].startswith("modeshift:")
    # The SessionLifecycle's mode has been updated
    check, _ = _invoke(e, iid, "develop", "session_check",
                        session_lifecycle_id=sid)
    assert check["mode"] == "coding"
    e.memory.close()


def test_mode_select_rejects_unknown_mode() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    init, _ = _invoke(e, iid, "develop", "session_init")
    # Registry catches + records the failed Invocation, THEN re-raises
    with pytest.raises(ValueError, match="not in"):
        _invoke(e, iid, "develop", "mode_select",
                 session_lifecycle_id=init["session_lifecycle_id"],
                 new_mode="not-a-mode")
    e.memory.close()


# ─────────────────────────── reflect.synthesize_session ───────────────────────

def test_synthesize_session_produces_artefact_and_archives() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    init, _ = _invoke(e, iid, "develop", "session_init",
                       mode_hint="brainstorming")
    sid = init["session_lifecycle_id"]
    synth, _ = _invoke(e, iid, "reflect", "synthesize_session",
                        session_lifecycle_id=sid,
                        lessons="spec 114 slice 1 ships",
                        open_questions="hooks integration in slice 2",
                        handoff_notes="next: implement hooks/session-start.sh")
    assert synth["artefact"]["kind"] == "session-reflection"
    assert synth["artefact"]["session_lifecycle_id"] == sid
    # SessionLifecycle archived
    check, _ = _invoke(e, iid, "develop", "session_check",
                        session_lifecycle_id=sid)
    assert check["status"] == "archived"
    # The Reflection note surfaces in provenance for future-session search
    prov = e.memory.provenance(iid)
    assert any("114 slice 1" in str(a) for a in prov.get("artefacts", []))
    e.memory.close()


# ─────────────────────────── dogfood.record_decision ───────────────────────

def test_record_decision_creates_node_and_serves_intent() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    init, _ = _invoke(e, iid, "develop", "session_init",
                       mode_hint="brainstorming")
    sid = init["session_lifecycle_id"]
    dec, _ = _invoke(e, iid, "dogfood", "record_decision",
                      subject="data layer",
                      decision="use SQLModel",
                      rationale="typed ORM + Pydantic + SQLAlchemy",
                      next_action="implement Spec 116",
                      session_lifecycle_id=sid)
    assert dec["decision_id"].startswith("decisionrecord:")
    # RELATES_TO edge to the session
    rows = e.memory.g.query(
        "MATCH (d)-[r:RELATES_TO]->(s) WHERE d.id = $did AND s.id = $sid "
        "RETURN r", {"did": dec["decision_id"], "sid": sid})
    assert rows, "RELATES_TO edge missing"
    e.memory.close()


def test_record_decision_without_session_id_still_serves_intent() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    dec, _ = _invoke(e, iid, "dogfood", "record_decision",
                      subject="x", decision="y", rationale="z")
    rows = e.memory.g.query(
        "MATCH (d)-[r:SERVES]->(i) WHERE d.id = $did AND i.id = $iid "
        "RETURN r", {"did": dec["decision_id"], "iid": iid})
    assert rows
    e.memory.close()


def test_decision_record_requires_subject_decision_rationale_enum() -> None:
    """Schema bites on missing rationale (closed enum at Memory.record time)."""
    e = _fresh()
    with pytest.raises(ValueError):
        e.memory.record("DecisionRecord",
                          {"subject": "x", "decision": "y"})
    e.memory.close()


# ─────────────────────────── dogfood.boundary_use_audit ───────────────────────

def test_boundary_use_audit_returns_empty_when_no_uses_recorded() -> None:
    """Spec 076 unified-hook integration that records BoundaryUse nodes is
    deferred to Spec 114 Slice 2; without it, the audit reads zero."""
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "dogfood", "boundary_use_audit")
    assert data["uses"] == []
    assert data["count"] == 0
    e.memory.close()


def test_boundary_use_audit_suggests_verbs_for_recorded_uses() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    # Hand-record some BoundaryUse nodes (Slice 2 will do this via hooks)
    e.memory.record("BoundaryUse",
                     {"tool": "Bash",
                      "argument_summary": "git commit -m '…'"})
    e.memory.record("BoundaryUse",
                     {"tool": "Write",
                      "argument_summary": "Plan/200-foo/spec.md"})
    data, _ = _invoke(e, iid, "dogfood", "boundary_use_audit")
    assert data["count"] == 2
    tools = {u["tool"] for u in data["uses"]}
    assert tools == {"Bash", "Write"}
    # Each suggestion points at a known verb hint
    for u in data["uses"]:
        assert u["suggested_verb"]
    e.memory.close()


# ─────────────────────────── walkable skill ───────────────────────────

def test_session_driver_pass_skill_is_five_phased() -> None:
    e = _fresh()
    sk = e.ontology.skill("session-driver-pass")
    assert sk["kind"] == "workflow"
    assert len(sk["phases"]) == 5
    assert sk["phases"][-1].get("gate") == "hard"
    names = [p["name"] for p in sk["phases"]]
    assert names == ["init", "mode-select", "work-loop",
                     "synthesize", "archive"]
    e.memory.close()


def test_session_driver_pass_walks_through_archive() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    sk = e.ontology.skill("session-driver-pass")
    run = SkillRun(e.memory, iid, sk)
    fills = [
        {"session_lifecycle_id": "x", "intent_id": iid, "mode": "coding"},
        {"confirmed_mode": "coding"},
        {"work_done": "yes"},
        {"lessons_recorded": "yes"},
    ]
    for out in fills:
        assert run.submit(out)["status"] == "working"
    assert run.current()["gate"] == "hard"
    assert run.submit({"session_archived": "yes"},
                      confirmed=True)["status"] == "completed"
    e.memory.close()
