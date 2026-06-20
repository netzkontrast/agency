import pytest
from agency.capabilities.novel.budget import apply_output_budget, recall_overflow, _OVERFLOW_STORE, MAX_BODY_BYTES

def test_budget_prefix_byte_stability():
    items = [{"id": 1, "title": "Ch 1"}, {"id": 2, "title": "Ch 2"}]
    res1 = apply_output_budget("work-1", "1.0", "hash123", items)
    res2 = apply_output_budget("work-1", "1.0", "hash123", items)

    assert res1.data["prefix"] == res2.data["prefix"]
    import json
    assert len(json.dumps(res1.data["prefix"])) == len(json.dumps(res2.data["prefix"]))

def test_budget_overflow_relational():
    large_string = "x" * 1000
    items = [{"id": i, "content": large_string} for i in range(10)]
    res = apply_output_budget("work-1", "1.0", "hash123", items, max_bytes=4000)

    assert res.data["body"]["overflow_handle"] is not None
    assert res.data["body"]["shown"] < res.data["body"]["total"]

def test_budget_recall_fidelity():
    large_string = "x" * 1000
    items = [{"id": i, "content": large_string} for i in range(10)]
    res = apply_output_budget("work-1", "1.0", "hash123", items, max_bytes=4000)

    handle = res.data["body"]["overflow_handle"]
    recall_res = recall_overflow(handle)
    assert recall_res.data["items"] == items

def test_budget_fields_projection_strictly():
    items = [{"title": "Ch 1", "wc": 2000, "status": "draft"}]
    res = apply_output_budget("work-1", "1.0", "hash123", items, fields=["title", "wc"])
    assert res.data["body"]["items"] == [{"title": "Ch 1", "wc": 2000}]

    res_err = apply_output_budget("work-1", "1.0", "hash123", items, fields=["title", "unknown"])
    assert res_err.error.code == "FIELDS_UNKNOWN"

def test_budget_overflow_handle_missing():
    res = recall_overflow("stale-handle")
    assert res.error.code == "OVERFLOW_HANDLE_MISSING"
