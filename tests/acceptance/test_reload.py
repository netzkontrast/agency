"""Acceptance — agency_reload: mid-session capability reload (Spec 302 Slice 2).

Injects a probe capability by monkeypatching ``discover_capabilities`` — NOT by writing into
the shared ``agency/capabilities/`` package (which would let parallel xdist
workers' ``discover_capabilities()`` see the extra cap and break exact-capability-set
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
        assert "installed_sync" in r0          # Spec 302 Slice 3 — sync reported

        # inject the probe cap into discovery, then reload mid-session. reload()
        # does `from .capabilities import discover_capabilities` at call time, so patching the
        # module attribute is honoured.
        real = capmod.discover_capabilities
        extra = ReloadprobeCapability.as_capability()
        monkeypatch.setattr(capmod, "discover_capabilities", lambda: [*real(), extra])

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
        monkeypatch.setattr(capmod, "discover_capabilities", real)
        r2 = eng.reload()
        assert "reloadprobe" in r2["removed"], r2
    finally:
        eng.memory.close()


def test_reload_mirrors_a_drifted_installed_copy_and_reports_it(tmp_path):
    """Spec 302 Slice 3 — the durable fix for the stale-MCP blocker: when the
    server imports a non-editable INSTALLED copy that drifts behind the source
    checkout, reload mirrors source→installed on disk and reports the sync."""
    from agency._reload_sync import sync_installed_from_source

    src = tmp_path / "src" / "agency"
    inst = tmp_path / "inst" / "agency"
    (src / "capabilities").mkdir(parents=True)
    (inst / "capabilities").mkdir(parents=True)
    (src / "__init__.py").write_text("v = 2\n")
    (inst / "__init__.py").write_text("v = 1\n")          # core file drifted
    (src / "capabilities" / "newcap.py").write_text("x = 1\n")   # new capability

    r = sync_installed_from_source(installed=inst, source=src)

    assert r["synced"] is True, r
    assert (inst / "capabilities" / "newcap.py").read_text() == "x = 1\n"  # mirrored
    assert (inst / "__init__.py").read_text() == "v = 2\n"                 # updated
    assert "__init__.py" in r["changed"]
    assert r["core_changed"] is True          # __init__.py is outside capabilities/


def test_reload_sync_capabilities_only_change_is_not_a_core_change(tmp_path):
    """A new/edited CAPABILITY file alone never forces a restart — it hot-reloads
    in process; only changes OUTSIDE ``capabilities/`` set ``core_changed``."""
    from agency._reload_sync import sync_installed_from_source

    src = tmp_path / "src" / "agency"
    inst = tmp_path / "inst" / "agency"
    (src / "capabilities").mkdir(parents=True)
    (inst / "capabilities").mkdir(parents=True)
    (src / "__init__.py").write_text("same\n")
    (inst / "__init__.py").write_text("same\n")
    (src / "capabilities" / "adr.py").write_text("a = 1\n")    # capability-only

    r = sync_installed_from_source(installed=inst, source=src)

    assert r["synced"] is True and r["core_changed"] is False, r


def test_reload_sync_is_a_noop_for_an_editable_install(tmp_path):
    """source == installed (editable) — the common dev/CI case — never copies."""
    from agency._reload_sync import sync_installed_from_source

    pkg = tmp_path / "agency"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("x\n")

    r = sync_installed_from_source(installed=pkg, source=pkg)

    assert r["synced"] is False and r["reason"] == "editable-install", r


def test_engine_reload_syncs_installed_and_signals_restart_on_core_change(
        tmp_path, monkeypatch):
    """End-to-end: a CORE drift makes ``Engine.reload`` update the installed copy
    on disk AND return ``restart_required`` WITHOUT purging the live registry
    (the skew that the manual fix proved an in-process reload cannot bridge)."""
    import agency._reload_sync as rs
    from agency.engine import Engine

    src = tmp_path / "src" / "agency"
    inst = tmp_path / "inst" / "agency"
    (src / "capabilities").mkdir(parents=True)
    (inst / "capabilities").mkdir(parents=True)
    (src / "__init__.py").write_text("v = 2\n")
    (inst / "__init__.py").write_text("v = 1\n")          # core drift
    monkeypatch.setattr(rs, "installed_package_dir", lambda: inst)
    monkeypatch.setattr(rs, "source_package_dir", lambda: src)

    eng = Engine(tempfile.mktemp(suffix=".db"))
    eng.build_mcp(codemode=True)
    try:
        names_before = set(eng.registry.names())
        r = eng.reload()
        assert r.get("restart_required") is True, r
        assert r["installed_sync"]["core_changed"] is True, r
        assert (inst / "__init__.py").read_text() == "v = 2\n"   # installed updated
        assert set(eng.registry.names()) == names_before         # registry intact
    finally:
        eng.memory.close()


def _write_codecap_main(pkg_dir, verb_name: str) -> None:
    """A folder-capability whose verb lives in a ``_main`` SUBMODULE — the shape
    that exposed the Spec-302 reload gap (package-reload didn't recurse)."""
    (pkg_dir / "_main.py").write_text(
        '"""reloadcodecap — a reload-probe capability.\n\n'
        "Use when proving mid-session code reload.\n"
        "Triggers:\n- a reload test runs\n"
        "Red flags:\n- none\n"
        '"""\n'
        "from agency.capability import CapabilityBase, verb\n"
        "from agency.ontology import OntologyExtension\n\n\n"
        "class ReloadcodecapCapability(CapabilityBase):\n"
        "    name = 'reloadcodecap'\n"
        "    home = 'capability'\n"
        "    ontology = OntologyExtension()\n\n"
        "    @verb(role='transform')\n"
        f"    def {verb_name}(self) -> dict:\n"
        '        """A reload sentinel verb.\n\n'
        "        Inputs: (none).\n"
        f"        Returns: {{result: {verb_name}}}.\n"
        "        chain_next: (terminal).\n"
        '        """\n'
        f"        return {{'result': '{verb_name}'}}\n"
    )


def test_agency_reload_picks_up_an_edited_submodule_mid_session(tmp_path):
    """The real hot-reload contract: EDITING an existing folder-capability's
    ``_main.py`` and reloading reflects the change — not just adding a brand-new
    top-level cap. Reproduces the gap where ``importlib.reload(package)`` left the
    ``_main`` submodule cached, so a new/renamed verb stayed invisible."""
    import sys
    from agency.engine import Engine
    import agency.capabilities as capmod

    # Build the engine FIRST (the temp cap is added mid-session, like real use —
    # and so the init-time skill_doc gate doesn't see a half-built probe).
    eng = Engine(tempfile.mktemp(suffix=".db"))
    eng.build_mcp(codemode=True)
    pkg = tmp_path / "reloadcodecap"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(
        "from ._main import ReloadcodecapCapability  # noqa: F401\n")
    _write_codecap_main(pkg, "alpha")
    capmod.__path__.append(str(tmp_path))     # discovery now also walks tmp_path
    try:
        eng.reload()
        assert "alpha" in eng.registry.get("reloadcodecap").verbs

        # EDIT the submodule on disk — rename the verb — then reload.
        _write_codecap_main(pkg, "beta")
        r = eng.reload()
        verbs = eng.registry.get("reloadcodecap").verbs
        assert "beta" in verbs and "alpha" not in verbs, verbs  # submodule re-imported
        assert r["reimported"] >= 1, r                          # the subtree was purged
    finally:
        if str(tmp_path) in capmod.__path__:
            capmod.__path__.remove(str(tmp_path))
        for m in [k for k in list(sys.modules) if "reloadcodecap" in k]:
            sys.modules.pop(m, None)
        eng.memory.close()
