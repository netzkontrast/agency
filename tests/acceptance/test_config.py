"""Acceptance — unified config resolver + registry (Spec 334 Slice 1).

Behaviour: a registered key resolves env > file > default; config_set persists;
registered sections appear in the live set. Calls agency._config directly, the
same way test_install.py drives agency.install.
"""
from __future__ import annotations

import os

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


# ── Spec 334 Slice 2 — scaffold generator ─────────────────────────────────────
@when("I scaffold the config")
@when("I scaffold the config again")
def _scaffold(cfg):
    _config.config_scaffold(path=cfg["path"])


@given("the config has been scaffolded")
def _scaffolded(cfg):
    _config.config_scaffold(path=cfg["path"])


@given("the JULES_API_KEY env is unset")
def _no_jules(cfg):
    cfg["mp"].delenv("JULES_API_KEY", raising=False)


@given("the config file is corrupt")
def _corrupt(cfg):
    os.makedirs(os.path.dirname(cfg["path"]), exist_ok=True)
    cfg["corrupt"] = "this: is: not: valid: [[[\n"
    with open(cfg["path"], "w", encoding="utf-8") as f:
        f.write(cfg["corrupt"])


@then("the config file is unchanged")
def _unchanged(cfg):
    with open(cfg["path"], encoding="utf-8") as f:
        assert f.read() == cfg["corrupt"]


@then(parsers.parse('the secret value is empty with source "{source}"'))
def _secret_empty(resolved, source):
    assert resolved["value"] in ("", None), resolved
    assert resolved["source"] == source, resolved


@given(parsers.parse('the user edits the frugal level to "{level}" with a "{comment}" comment'))
def _user_edit(cfg, level, comment):
    with open(cfg["path"], encoding="utf-8") as f:
        text = f.read()
    text = text.replace("level: full", f"level: {level}  {comment}")
    with open(cfg["path"], "w", encoding="utf-8") as f:
        f.write(text)


@given(parsers.parse('a new capability registers a config section "{section}" key "{name}" default "{default}"'))
def _register_new(section, name, default):
    _config.register_config_section(section, [_config.ConfigKey(name=name, default=default)])




@then("the config file lists every registered key")
def _lists_all(cfg):
    data = _config._read(cfg["path"])
    for section, keys in _config._REGISTRY.items():
        sec = data.get(section) or {}
        for k in keys:
            assert k.name in sec, f"{section}.{k.name} missing from scaffold"


@then("the frugal level line carries a comment")
def _level_comment(cfg):
    with open(cfg["path"], encoding="utf-8") as f:
        lines = [ln for ln in f if "level:" in ln]
    assert any("#" in ln for ln in lines), lines


@then(parsers.parse('the frugal level default is "{value}"'))
def _frugal_default(cfg, value):
    assert (_config._read(cfg["path"]).get("frugal") or {}).get("level") == value


@then(parsers.parse('the frugal level is still "{value}"'))
def _frugal_still(cfg, value):
    assert (_config._read(cfg["path"]).get("frugal") or {}).get("level") == value


@then("every secret key is written as an env reference")
def _secrets_ref(cfg):
    data = _config._read(cfg["path"])
    secrets = _config.secret_keys()
    assert secrets, "no secret keys registered"
    for dotted in secrets:
        section, _, name = dotted.partition(".")
        val = (data.get(section) or {}).get(name, "")
        assert str(val).startswith("${env:"), f"{dotted} leaked literal: {val!r}"


@then(parsers.parse('the comment "{comment}" is preserved'))
def _comment_preserved(cfg, comment):
    with open(cfg["path"], encoding="utf-8") as f:
        assert comment in f.read()


@then(parsers.parse('the config file lists "{dotted}"'))
def _file_lists(cfg, dotted):
    section, _, name = dotted.partition(".")
    assert name in (_config._read(cfg["path"]).get(section) or {}), dotted
