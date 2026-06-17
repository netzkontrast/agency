"""Acceptance — agency_reload: mid-session capability reload (Spec 302 Slice 2).

Uses the filesystem (writes a temp capability into the package) so it exercises
the real discover() path; cleans up in finally + drops the temp cap via a final
reload.
"""
from __future__ import annotations

import os
import tempfile
import textwrap

import pytest

from agency.engine import Engine

_TMP_CAP = "agency/capabilities/reloadprobe.py"
_SRC = textwrap.dedent('''# agency-scaffold: v1
"""reloadprobe — a mid-session-reload probe capability.

Use when: validating that agency_reload picks up a new capability live.
Triggers:
- A reload test needs a fresh capability to appear
- Verifying a new verb is invocable without a restart
Red flags:
- Trusting reload without a test -> add this probe
- Shipping the reload tool untested -> run this scenario
"""
from agency.capability import CapabilityBase, verb
from agency.ontology import OntologyExtension


class ReloadprobeCapability(CapabilityBase):
    name = "reloadprobe"
    home = "capability"
    ontology = OntologyExtension()

    @verb(role="transform")
    def ping(self) -> dict:
        """Return a reload sentinel.

        Inputs: (none).
        Returns: {result: reloaded}.
        chain_next: (terminal).
        """
        return {"result": "reloaded"}
''')


def _drop_pycache():
    d = "agency/capabilities/__pycache__"
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.startswith("reloadprobe"):
                os.remove(os.path.join(d, f))


def test_agency_reload_picks_up_a_new_capability_mid_session():
    eng = Engine(tempfile.mktemp(suffix=".db"))
    eng.build_mcp(codemode=True)            # so the live MCP is held for re-wiring
    try:
        assert "reloadprobe" not in eng.registry.names()
        # idempotent reload — nothing changes
        r0 = eng.reload()
        assert r0["reloaded"] and r0["added"] == [] and r0["removed"] == []

        # add a capability ON DISK, then reload mid-session
        with open(_TMP_CAP, "w", encoding="utf-8") as f:
            f.write(_SRC)
        r1 = eng.reload()
        assert "reloadprobe" in r1["added"], r1
        assert r1["rewired_tools"] >= 1, r1
        assert "reloadprobe" in eng.registry.names()

        # the new verb is invocable WITHOUT a restart
        iid = eng.intent.capture("p", "d", "a")
        eng.intent.confirm(iid)
        res, _ = eng.registry.invoke(eng.memory, iid, "reloadprobe", "ping",
                                     agent_id="a")
        assert res == {"result": "reloaded"}, res
    finally:
        if os.path.exists(_TMP_CAP):
            os.remove(_TMP_CAP)
        _drop_pycache()
        r2 = eng.reload()
        assert "reloadprobe" in r2["removed"], r2
        eng.memory.close()
