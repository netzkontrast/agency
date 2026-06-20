from agency.engine import Engine
from agency.lifecycle import Lifecycle

def test_resume():
    m = Engine(":memory:").memory
    lc = Lifecycle(m)
    intent_id = m.record("Intent", {"purpose": "test", "deliverable": "test", "acceptance": "test", "status": "active", "owner": "user"})
    lc_id = lc.open(intent_id)
    m.update(lc_id, {"phase": "phase-2"})
    lc.move(lc_id, "working")
    lc.move(lc_id, "input-required")

    res = lc.resume(lc_id)
    assert res["state"] == "working"
    assert res["lifecycle_id"] == lc_id
    assert res["resume_from"] == "phase-2"
    assert lc.status(lc_id) == "working"

    # Check invalid resume
    lc.move(lc_id, "completed")
    try:
        lc.resume(lc_id)
        assert False
    except ValueError as e:
        assert "not resumable" in str(e)

    m.close()
