"""Acceptance — the lifecycle-management discipline + resume + board (Spec 343).

The capstone slice: a walkable discipline orchestrating the existing pillar verbs
(genuinely walked via develop.skill_walk, recording Skill provenance);
lifecycle.resume bridging the 340 state machine to the phase walker; and the
report phase mirroring the in-flight board to a Spec 292 file peer.
"""
import os
import tempfile

from pytest_bdd import scenario, given, when, then, parsers
from agency.lifecycle import Lifecycle


@scenario('features/lifecycle_management.feature',
          'the discipline walks the whole pillar over existing reads')
def test_discipline_walks():
    pass


@scenario('features/lifecycle_management.feature',
          'resume re-enters a paused lifecycle at its phase')
def test_resume_paused():
    pass


@scenario('features/lifecycle_management.feature',
          'resume refuses a non-resumable state')
def test_resume_refuses():
    pass


@scenario('features/lifecycle_management.feature',
          'the board renders as a file peer')
def test_board_file_peer():
    pass


def _confirmed_intent(engine):
    iid = engine.intent.capture("lifecycle management", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


@given('an open Lifecycle in state "input-required"', target_fixture="lc_data")
def open_lc_input_required(engine):
    iid = _confirmed_intent(engine)
    lc = Lifecycle(engine.memory, engine=engine, monitor=getattr(engine, "monitor", None))
    lc_id = lc.open(iid)
    lc.move(lc_id, "working")
    lc.move(lc_id, "input-required")
    return {"id": lc_id, "lc": lc, "intent": iid}


@given('a Lifecycle in "input-required" recorded at phase "implement"', target_fixture="lc_data")
def lc_in_input_required_phase_implement(engine):
    iid = _confirmed_intent(engine)
    lc = Lifecycle(engine.memory, engine=engine, monitor=getattr(engine, "monitor", None))
    lc_id = lc.open(iid)
    engine.memory.update(lc_id, {"phase": "implement"})
    lc.move(lc_id, "working")
    lc.move(lc_id, "input-required")
    return {"id": lc_id, "lc": lc, "intent": iid}


@given('an open Lifecycle in state "completed"', target_fixture="lc_data")
def lc_in_completed(engine):
    iid = _confirmed_intent(engine)
    lc = Lifecycle(engine.memory, engine=engine, monitor=getattr(engine, "monitor", None))
    lc_id = lc.open(iid)
    lc.move(lc_id, "working")
    lc.move(lc_id, "completed")
    return {"id": lc_id, "lc": lc, "intent": iid}


# ── walk the discipline ───────────────────────────────────────────────────────

@when('I walk the lifecycle-management discipline', target_fixture="walk")
def walk_discipline(engine, lc_data):
    res, _ = engine.registry.invoke(
        engine.memory, lc_data["intent"], "develop", "skill_walk",
        name="lifecycle-management",
        inputs={"board_state": "x", "blockers": "x", "unblocked_lifecycles": "x",
                "progress_recorded": "x", "terminal_closed": "x", "lifecycle_board": "x"})
    return res


@then('the walk completes through the six named phases')
def walk_completes(engine, walk):
    assert walk["status"] == "completed", walk
    skill = engine.ontology.skills["lifecycle-management"]
    names = [p["name"] for p in skill["phases"]]
    assert names == ["survey", "triage", "unblock", "advance", "close", "report"], names


@then('a Skill provenance record for the walk exists serving the intent')
def walk_provenance(engine, walk, lc_data):
    sid = walk["skill_id"]
    node = engine.memory.recall(sid)
    assert node is not None and node.get("name") == "lifecycle-management", node
    assert "Skill" in engine.memory.labels_of(sid)


# ── resume ────────────────────────────────────────────────────────────────────

@when('I call lifecycle.resume(lid)', target_fixture="resume_result")
def call_resume(lc_data):
    try:
        return lc_data["lc"].resume(lc_data["id"])
    except Exception as e:
        return e


@then('it moves to "working" and returns resume_from="implement"')
def moves_to_working(resume_result, lc_data):
    assert isinstance(resume_result, dict)
    assert resume_result["state"] == "working"
    assert resume_result["resume_from"] == "implement"
    assert lc_data["lc"].status(lc_data["id"]) == "working"


@then('it raises (only input-required | auth-required are resumable)')
def raises_error(resume_result):
    assert isinstance(resume_result, ValueError)
    assert "not resumable" in str(resume_result)


# ── the board as a file peer ──────────────────────────────────────────────────

@when('the report phase mirrors the lifecycle board to a file', target_fixture="board")
def mirror_board(engine, lc_data):
    path = os.path.join(tempfile.mkdtemp(), "lifecycle-board.md")
    res, _ = engine.registry.invoke(
        engine.memory, lc_data["intent"], "document", "mirror",
        scope="lifecycle-board", apply_path=path)
    return {"path": path, "result": res}


@then('lifecycle-board.md is written with the in-flight board')
def board_written(board, lc_data):
    assert os.path.basename(board["path"]) == "lifecycle-board.md"
    assert os.path.exists(board["path"]), board["result"]
    text = open(board["path"]).read()
    assert "# Lifecycle board" in text
    assert "In flight" in text
    # the paused lifecycle is on the board (non-terminal)
    assert lc_data["id"] in text
    # the Spec 292 file-peer anchor binds the file to its Document node
    assert "agency-node:" in text
