"""Acceptance — frugal M2 per-verb envelope stamp (Spec 326 Slice 2).

Every capability verb's wire return carries a byte-stable compact frugal stamp
(via engine._shape_wire_result); off omits it; agency_welcome carries it in its
cache-stable prefix. Drives the real wire path (`call_tool`).
"""
from __future__ import annotations

import os

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine
from conftest import call_tool

scenarios("features/frugal_stamp.feature")


@pytest.fixture
def we(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_CONFIG", str(tmp_path / ".agency" / "config.yaml"))
    monkeypatch.delenv("AGENCY_FRUGAL_LEVEL", raising=False)
    monkeypatch.delenv("AGENCY_INTENT", raising=False)
    e = Engine(":memory:")
    yield {"engine": e, "mp": monkeypatch, "r": None}
    e.memory.close()


def _call_verb(engine):
    iid = call_tool(engine, "intent_bootstrap",
                    {"purpose": "w", "deliverable": "w", "acceptance": "w"})["intent_id"]
    return call_tool(engine, "capability_manage_create",
                     {"intent_id": iid, "agent_id": "a", "label": "Document",
                      "props": {"path": "/w.md", "content_sha": "abc"}})


@given("a frugal wire engine at the default level")
def _default(we):
    return we


@given(parsers.parse('a frugal wire engine at level "{level}"'))
def _level(we, level):
    we["mp"].setenv("AGENCY_FRUGAL_LEVEL", level)
    return we


@when("a capability verb returns over the wire")
def _verb(we):
    we["r"] = _call_verb(we["engine"])


@when("agency_welcome returns over the wire")
def _welcome(we):
    we["r"] = call_tool(we["engine"], "agency_welcome", {})


@when("agency_doctor returns over the wire")
def _doctor(we):
    we["r"] = call_tool(we["engine"], "agency_doctor", {})


@then(parsers.parse('the doctor reports frugal level "{level}"'))
def _doctor_level(we, level):
    assert we["r"]["frugal"]["level"] == level, we["r"].get("frugal")


@then("the doctor reports the per-verb stamp active")
def _doctor_stamp(we):
    assert we["r"]["frugal"]["stamp_active"] is True, we["r"].get("frugal")


@then("the wire return carries a frugal stamp naming the floor")
def _has_stamp(we):
    assert "frugal" in we["r"], we["r"]
    assert "floor" in we["r"]["frugal"], we["r"]["frugal"]


@then("the frugal stamp is byte-identical on a repeat call")
def _stable(we):
    r2 = _call_verb(we["engine"])
    assert r2["frugal"] == we["r"]["frugal"]


@then("the wire return has no frugal stamp")
def _no_stamp(we):
    assert "frugal" not in we["r"], we["r"]


@then("the welcome prefix carries the frugal stamp")
def _welcome_stamp(we):
    assert "floor" in we["r"].get("frugal", ""), we["r"]
    assert "frugal" in we["r"].get("_prefix_keys", []), we["r"].get("_prefix_keys")
