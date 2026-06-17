"""Acceptance — agency_reload: mid-session capability reload (Spec 302 Slice 2).

Injects a probe capability by monkeypatching ``discover`` — NOT by writing into
the shared ``agency/capabilities/`` package (which would let parallel xdist
workers' ``discover()`` see the extra cap and break exact-capability-set
invariants).
"""
from __future__ import annotations

import tempfile

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


def test_agency_reload_picks_up_a_new_capability_mid_session(monkeypatch):
    from agency.engine import Engine
    import agency.capabilities as capmod

    eng = Engine(tempfile.mktemp(suffix=".db"))
    eng.build_mcp(codemode=True)            # so the live MCP is held for re-wiring
    try:
        assert "reloadprobe" not in eng.registry.names()
        # idempotent reload — nothing changes
        r0 = eng.reload()
        assert r0["reloaded"] and r0["added"] == [] and r0["removed"] == []

        # inject the probe cap into discovery, then reload mid-session. reload()
        # does `from .capabilities import discover` at call time, so patching the
        # module attribute is honoured.
        real = capmod.discover
        extra = ReloadprobeCapability.as_capability()
        monkeypatch.setattr(capmod, "discover", lambda: [*real(), extra])

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

        # un-patch → reload drops it again
        monkeypatch.setattr(capmod, "discover", real)
        r2 = eng.reload()
        assert "reloadprobe" in r2["removed"], r2
    finally:
        eng.memory.close()
