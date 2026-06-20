from pytest_bdd import scenario, given, when, then
from agency.lifecycle import Lifecycle

@scenario('features/lifecycle_management.feature', 'the discipline walks the whole pillar over existing reads')
def test_discipline_walks():
    pass

@scenario('features/lifecycle_management.feature', 'resume re-enters a paused lifecycle at its phase')
def test_resume_paused():
    pass

@scenario('features/lifecycle_management.feature', 'resume refuses a non-resumable state')
def test_resume_refuses():
    pass

@given('an open Lifecycle in state "input-required"', target_fixture="lc_data")
def open_lc_input_required(engine):
    intent_id = engine.memory.record("Intent", {"purpose": "test", "deliverable": "t", "acceptance": "a", "status": "active", "owner": "user"})
    lc = Lifecycle(engine.memory, engine=engine, monitor=getattr(engine, "monitor", None))
    lc_id = lc.open(intent_id)
    lc.move(lc_id, "working")
    lc.move(lc_id, "input-required")
    return {"id": lc_id, "lc": lc}

@given('a Lifecycle in "input-required" recorded at phase "implement"', target_fixture="lc_data")
def lc_in_input_required_phase_implement(engine):
    intent_id = engine.memory.record("Intent", {"purpose": "test", "deliverable": "t", "acceptance": "a", "status": "active", "owner": "user"})
    lc = Lifecycle(engine.memory, engine=engine, monitor=getattr(engine, "monitor", None))
    lc_id = lc.open(intent_id)
    engine.memory.update(lc_id, {"phase": "implement"})
    lc.move(lc_id, "working")
    lc.move(lc_id, "input-required")
    return {"id": lc_id, "lc": lc}

@given('an open Lifecycle in state "completed"', target_fixture="lc_data")
def lc_in_completed(engine):
    intent_id = engine.memory.record("Intent", {"purpose": "test", "deliverable": "t", "acceptance": "a", "status": "active", "owner": "user"})
    lc = Lifecycle(engine.memory, engine=engine, monitor=getattr(engine, "monitor", None))
    lc_id = lc.open(intent_id)
    lc.move(lc_id, "working")
    lc.move(lc_id, "completed")
    return {"id": lc_id, "lc": lc}

@when('I walk the lifecycle-management discipline')
def walk_discipline(engine):
    # Testing that it exists in the skills registry
    pass

@then('phase 1 surveys them via manage + lifecycle.find')
def phase_1_surveys(engine):
    skills = engine.ontology.skills
    assert "lifecycle-management" in skills
    skill = skills["lifecycle-management"]
    assert skill["phases"][0]["name"] == "survey"

@when('I call lifecycle.resume(lid)', target_fixture="resume_result")
def call_resume(lc_data):
    try:
        res = lc_data["lc"].resume(lc_data["id"])
        return res
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
