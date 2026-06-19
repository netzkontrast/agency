"""Acceptance — unified config resolver + registry (Spec 328 Slice 1).

Behaviour: a registered key resolves env > file > default; config_set persists;
registered sections appear in the live set. Calls agency._config directly, the
same way test_install.py drives agency.install.
"""
from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency import _config

scenarios("features/config.feature")


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    monkeypatch.delenv("DEMO_COLOR", raising=False)
    return {"path": str(tmp_path / ".agency" / "config.yaml"), "mp": monkeypatch}


@given(parsers.parse('a registered config key "{dotted}" default "{default}" env "{env}"'))
def _register(dotted, default, env):
    section, _, name = dotted.partition(".")
    _config.register_config_section(
        section, [_config.ConfigKey(name=name, env=env, default=default)])


@given("a clean env and an empty config file")
def _clean(cfg):
    return cfg


@given(parsers.parse('the config file sets "{dotted}" to "{value}"'))
def _file_set(cfg, dotted, value):
    _config.config_set(dotted, value, path=cfg["path"])


@given(parsers.parse('the env var DEMO_COLOR is "{value}"'))
def _set_env(cfg, value):
    cfg["mp"].setenv("DEMO_COLOR", value)


@when(parsers.parse('I resolve "{dotted}"'), target_fixture="resolved")
def _resolve(cfg, dotted):
    return _config.config_resolve(dotted, path=cfg["path"])


@when(parsers.parse('I set "{dotted}" to "{value}"'))
def _set(cfg, dotted, value):
    _config.config_set(dotted, value, path=cfg["path"])


@then(parsers.parse('the value is "{value}" with source "{source}"'))
def _check(resolved, value, source):
    assert resolved["value"] == value, resolved
    assert resolved["source"] == source, resolved


@then(parsers.parse('resolving "{dotted}" gives "{value}" with source "{source}"'))
def _resolve_check(cfg, dotted, value, source):
    r = _config.config_resolve(dotted, path=cfg["path"])
    assert r["value"] == value and r["source"] == source, r


@then(parsers.parse('"{dotted}" is in the registered keys'))
def _in_keys(dotted):
    assert dotted in _config.registered_keys()
