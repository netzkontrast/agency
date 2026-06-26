"""Spec 173 Slice 2 — live reflection-link coverage sweep + WARN→error promotion.

The dormant Slice-1 ``LinkFinding`` shape is now load-bearing: a graph sweep requires
every live ``Reflection`` to carry BOTH ``SERVES`` and ``OBSERVED_DURING``. The lint
promotes to ``error`` gated on the sweep being clean; the no-Intent write-path
invariant is enforced upstream by the substrate IntentGuard.
"""
from __future__ import annotations

import asyncio
import tempfile

import pytest

from agency.engine import Engine
from agency._reflection_link_sweep import sweep
from agency.toolresult import Codes


def test_codes_exist():
    assert Codes.REFLECTION_NO_INTENT == "reflection_no_intent"
    assert Codes.REFLECTION_PARTIAL_LINKS == "reflection_partial_links"


def test_note_written_reflection_passes_sweep():
    e = Engine(":memory:")
    try:
        iid = e.intent.capture("p", "d", "a")
        e.intent.confirm(iid)
        e.registry.invoke(e.memory, iid, "reflect", "note",
                          scope="observation", text="hi")
        rep = sweep(e.memory)
        assert rep["ready"] is True, rep
        assert rep["unlinked"] == 0
    finally:
        e.memory.close()


def test_partial_reflection_missing_observed_during_trips_sweep():
    e = Engine(":memory:")
    try:
        iid = e.intent.capture("p", "d", "a")
        e.intent.confirm(iid)
        # a Reflection with ONLY SERVES (the partial-write the gate forbids)
        rid = e.memory.record("Reflection", {"scope": "observation", "text": "x"})
        e.memory.link(rid, iid, "SERVES")
        rep = sweep(e.memory)
        miss = [f for f in rep["findings"] if f["reflection_id"] == rid]
        assert miss and miss[0]["missing_edge"] == "OBSERVED_DURING"
        assert miss[0]["severity"] == "error"
        assert rep["ready"] is False
        assert rep["partial_code"] == Codes.REFLECTION_PARTIAL_LINKS
    finally:
        e.memory.close()


def test_note_without_a_confirmed_intent_is_blocked_pointing_at_bootstrap():
    # Spec 173 item 7 — the substrate IntentGuard makes a Reflection write
    # impossible without a SERVES target, naming intent_bootstrap.
    e = Engine(":memory:")
    try:
        with pytest.raises(ValueError) as exc:
            e.registry.invoke(e.memory, "intent:bogus", "reflect", "note",
                              scope="observation", text="x")
        assert "intent_bootstrap" in str(exc.value)
    finally:
        e.memory.close()


def test_agency_doctor_reports_reflection_link_coverage_ready():
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)

    async def main():
        return await mcp.call_tool("agency_doctor", {})

    try:
        res = asyncio.run(main())
        cov = res.structured_content["reflection_link_coverage"]
        assert cov["ready"] is True
        assert cov["unlinked"] == 0
    finally:
        e.memory.close()
