"""Spec 171 Slice 2 — the live node-id-guard coverage sweep + WARN→error promotion.

The typed ``GuardFinding`` shape shipped in Slice 1 but was dormant. Slice 2 derives,
over the LIVE registry, every ``<label>_id`` param read via a bare ``recall``/
``get_node`` without a label check, and gates the lint's promotion to ``error`` on the
sweep being clean. A verb whose signature can't be resolved is flagged
``GUARD_LINT_UNRESOLVED`` (manual review), never silently passed.
"""
from __future__ import annotations

import asyncio
import tempfile

from agency.capability import CapabilityBase, verb
from agency.engine import Engine
from agency._node_id_sweep import sweep
from agency.toolresult import Codes


def test_guard_lint_unresolved_code_exists():
    assert Codes.GUARD_LINT_UNRESOLVED == "guard_lint_unresolved"


def test_live_registry_sweep_is_clean_and_ready():
    e = Engine(":memory:")
    try:
        rep = sweep(e.registry)
        # the invariant the whole spec hinges on: zero unguarded *_id params live.
        assert rep["violation_count"] == 0, rep["violations"]
        assert rep["unresolved"] == [], rep["unresolved"]
        assert rep["ready"] is True
    finally:
        e.memory.close()


class _Bad(CapabilityBase):
    name = "badcap"
    home = "memory"

    @verb(role="act")
    def peek(self, ctx, research_id: str) -> dict:
        """Reads a research id with no label check (deliberate fixture).

        Inputs: research_id (str). Returns: {node}. chain_next: none.
        """
        return {"node": ctx.memory.recall(research_id)}


def test_unguarded_fixture_verb_is_flagged_error_and_breaks_ready():
    e = Engine(":memory:", extra_capabilities=[_Bad.as_capability()],
               _require_skill_doc=False)
    try:
        rep = sweep(e.registry)
        viols = [v for v in rep["violations"] if v["verb_id"] == "badcap.peek"]
        assert viols, rep["violations"]
        v = viols[0]
        assert v["param_name"] == "research_id"
        assert v["expected_label"] == "Research"
        assert v["severity"] == "error"        # promoted (the sweep is the gate)
        assert rep["ready"] is False            # a violation breaks coverage
    finally:
        e.memory.close()


def test_agency_doctor_reports_node_id_guard_coverage_ready():
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)

    async def main():
        return await mcp.call_tool("agency_doctor", {})

    try:
        res = asyncio.run(main())
        cov = res.structured_content["node_id_guard_coverage"]
        assert cov["ready"] is True          # Spec 170 consumer signal
        assert cov["violations"] == 0
        assert cov["unresolved"] == 0
    finally:
        e.memory.close()
