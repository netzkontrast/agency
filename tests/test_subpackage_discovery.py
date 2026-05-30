"""Spec 016 Phase 3 RED — folder-form capability discovery.

Hint #1 says capabilities can be a `.py` module OR a folder (subpackage)
with an `__init__.py` re-exporting a `Capability` instance or
`CapabilityBase` subclass. The `discover()` reflection-walker is the
single integration point — it must treat both forms identically.

The current implementation (`agency/capabilities/__init__.py`) uses
`pkgutil.iter_modules` + `importlib.import_module`, both of which
transparently handle subpackages. This test asserts the contract
empirically — before any future refactor breaks it.
"""
from __future__ import annotations

import importlib
import sys
import textwrap
from pathlib import Path

import pytest

from agency.capabilities import discover


@pytest.fixture
def temp_subpackage_capability(tmp_path, monkeypatch):
    """Create a folder-form capability on disk inside agency/capabilities/
    for the duration of one test. Cleans up by deleting the folder + any
    cached import; restores the registry path on teardown.

    Returns the capability NAME so the test can assert `discover()` found it.
    """
    import agency.capabilities as caps_pkg
    pkg_dir = Path(caps_pkg.__file__).parent
    subpkg_name = "ztemp_folder_form"
    subpkg_dir = pkg_dir / subpkg_name
    subpkg_dir.mkdir()
    try:
        (subpkg_dir / "__init__.py").write_text(textwrap.dedent("""
            from agency.capability import CapabilityBase, verb
            from agency.ontology import OntologyExtension

            class FolderFormCapability(CapabilityBase):
                name = "ztemp-folder-form"
                home = "capability"
                ontology = OntologyExtension()

                @verb(role="transform")
                def ping(self) -> dict:
                    '''Folder-form sentinel.

                    Inputs: (none).
                    Returns: {result: "pong"}.
                    chain_next: (terminal).
                    '''
                    return {"result": "pong"}
        """).lstrip())
        # Inner sibling file with underscore prefix MUST be skipped
        # (the boundary marker convention — Hint #1's discovery rule).
        (subpkg_dir / "_helper.py").write_text(
            "RAISE_IF_IMPORTED = 'discovery should not have walked into me'\n"
        )
        yield subpkg_name
    finally:
        for mod in list(sys.modules):
            if mod.startswith(f"agency.capabilities.{subpkg_name}"):
                del sys.modules[mod]
        # Recursive removal — __pycache__/ may exist after import
        import shutil
        shutil.rmtree(subpkg_dir, ignore_errors=True)


def test_discover_finds_folder_form_capability(temp_subpackage_capability):
    """The doctrine — Hint #1 — promises folder form works identically to
    single-file. discover() returns a Capability with the subpackage's
    declared name. Empirical proof, not Hint-text faith."""
    caps = discover()
    names = [c.name for c in caps]
    assert "ztemp-folder-form" in names, (
        f"folder-form capability not discovered; only saw: {sorted(names)}"
    )


def test_folder_form_capability_walks_through_engine(temp_subpackage_capability):
    """Discovery is necessary but not sufficient — the discovered
    capability must register cleanly + its verbs must be reachable
    through the registry. This is the consumer-contract Codex R2 taught
    us (verify the surface, not just the wiring)."""
    from agency.engine import Engine

    e = Engine(":memory:")
    try:
        # Capability discovered into the registry
        assert "ztemp-folder-form" in e.registry.names()
        # Verb reachable via engine.registry.invoke (Hint #11 test pattern)
        iid = e.intent.capture("phase 3 ping", "verify folder form works", "ok")
        e.intent.confirm(iid)
        result, _ = e.registry.invoke(
            e.memory, iid, "ztemp-folder-form", "ping"
        )
        assert result["result"] == "pong"
    finally:
        e.memory.close()
