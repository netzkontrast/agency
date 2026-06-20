"""Acceptance — user-facing config capability (Spec 334 Slice 8).

Behaviour: get / set / list verbs over the unified config, driven through the
real Engine registry (records provenance like any verb). Safety floor: set
refuses secrets, list redacts them, bad keys error cleanly (no traceback).
"""
from __future__ import annotations

import tempfile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import invoke
from agency import _config
from agency.engine import Engine

scenarios("features/config_capability.feature")


@pytest.fixture
def engine(tmp_path, monkeypatch):
    # Isolate the unified config at a tmp path and clear envs the scenarios
    # assert default/file sources for, so resolution is deterministic.
    monkeypatch.setenv("AGENCY_CONFIG", str(tmp_path / ".agency" / "config.yaml"))
    for var in ("AGENCY_EMBEDDER", "AGENCY_DB", "JULES_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    _config._READ_CACHE.clear()
    e = Engine(tempfile.mktemp(suffix=".db"))
    yield e
    e.memory.close()


@pytest.fixture
def confirmed_intent(engine):
    iid = engine.intent.capture("config acceptance", "behaviour", "verified")
    engine.intent.confirm(iid)
    return iid


@when(parsers.parse('I get config "{key}"'), target_fixture="cfg_result")
def _get(engine, confirmed_intent, key):
    res, _ = invoke(engine, confirmed_intent, "config", "get", key=key)
    return res


@when(parsers.parse('I set config "{key}" to "{value}"'), target_fixture="cfg_result")
def _set(engine, confirmed_intent, key, value):
    res, _ = invoke(engine, confirmed_intent, "config", "set", key=key, value=value)
    return res


@when("I list config", target_fixture="cfg_result")
def _list(engine, confirmed_intent):
    res, _ = invoke(engine, confirmed_intent, "config", "list")
    return res


@then(parsers.parse('the config result value is "{value}" with source "{source}"'))
def _check_value(cfg_result, value, source):
    assert cfg_result.get("value") == value, cfg_result
    assert cfg_result.get("source") == source, cfg_result


@then(parsers.parse('the config listing includes "{key}"'))
def _listing_includes(cfg_result, key):
    assert key in (cfg_result.get("values") or {}), cfg_result


@then(parsers.parse('the secret "{key}" is redacted in the listing'))
def _redacted(cfg_result, key):
    entry = (cfg_result.get("values") or {}).get(key)
    assert entry is not None, cfg_result
    assert entry.get("value") in ("set", "unset"), entry


@then(parsers.parse('the config result is an error mentioning "{needle}"'))
def _error(cfg_result, needle):
    assert "error" in cfg_result, cfg_result
    assert needle in cfg_result["error"].lower(), cfg_result
