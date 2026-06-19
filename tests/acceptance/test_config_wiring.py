"""Acceptance — unified config wiring (Spec 328 Slice 3).

The three zero-manual-step generation points: `agency install` (here:
`install.scaffold_agency_dir`) creates the annotated config; the SessionStart
hook REPAIRS an existing one non-destructively but never creates one in an
arbitrary cwd. Drives the real seams (`agency.install`, `Engine.dispatch_hook`).
"""
from __future__ import annotations

import os

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency import _config, install
from agency.engine import Engine

scenarios("features/config_wiring.feature")


@pytest.fixture
def proj(tmp_path, monkeypatch):
    root = str(tmp_path)
    os.makedirs(os.path.join(root, ".agency"), exist_ok=True)
    cfg_path = os.path.join(root, ".agency", "config.yaml")
    monkeypatch.setenv("AGENCY_CONFIG", cfg_path)
    monkeypatch.delenv("AGENCY_FRUGAL_LEVEL", raising=False)
    monkeypatch.delenv("AGENCY_INTENT", raising=False)
    return {"root": root, "cfg": cfg_path, "mp": monkeypatch}


@given("a clean project directory")
def _clean_proj(proj):
    return proj


@when("agency scaffolds the project")
def _scaffold_project(proj):
    install.scaffold_agency_dir(proj["root"])


@given("the project config has been scaffolded")
def _proj_scaffolded(proj):
    _config.config_scaffold(path=proj["cfg"])


@given(parsers.parse('the user edits the project frugal level to "{level}"'))
def _proj_edit(proj, level):
    with open(proj["cfg"], encoding="utf-8") as f:
        text = f.read()
    with open(proj["cfg"], "w", encoding="utf-8") as f:
        f.write(text.replace("level: full", f"level: {level}"))


@given(parsers.parse('a new capability registers a config section "{section}" key "{name}" default "{default}"'))
def _register_new(section, name, default):
    _config.register_config_section(section, [_config.ConfigKey(name=name, default=default)])


@when("a SessionStart hook fires for the project")
def _session_start(proj):
    e = Engine(":memory:")
    try:
        e.dispatch_hook({"hook_event_name": "SessionStart", "session_id": "w1"})
    finally:
        e.memory.close()


@then("the project config exists")
def _exists(proj):
    assert os.path.exists(proj["cfg"])


@then("the project config does not exist")
def _not_exists(proj):
    assert not os.path.exists(proj["cfg"])


@then(parsers.parse('the project frugal level is "{level}"'))
def _level(proj, level):
    assert (_config._read(proj["cfg"]).get("frugal") or {}).get("level") == level


@then("the project config lists every registered key")
def _lists_all(proj):
    data = _config._read(proj["cfg"])
    for section, keys in _config._REGISTRY.items():
        sec = data.get(section) or {}
        for k in keys:
            assert k.name in sec, f"{section}.{k.name} missing"


@then(parsers.parse('the project config lists "{dotted}"'))
def _lists(proj, dotted):
    section, _, name = dotted.partition(".")
    assert name in (_config._read(proj["cfg"]).get(section) or {}), dotted
