"""Acceptance — unified config doctor (Spec 334 Slice 4).

agency_doctor surfaces a `config` block (every registered key's resolved value +
source, secrets redacted) and folds validation issues (bad enum value, unknown
key) into next_steps; `agency-doctor --write-config` repairs a missing config.
Drives the real wire tool (`call_tool`) and the CLI entry (`doctor_main`).
"""
from __future__ import annotations

import os

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency import _config
from agency.engine import Engine
from conftest import call_tool

scenarios("features/config_doctor.feature")


@pytest.fixture
def deng(tmp_path, monkeypatch):
    cfg = os.path.join(str(tmp_path), ".agency", "config.yaml")
    os.makedirs(os.path.dirname(cfg), exist_ok=True)
    monkeypatch.setenv("AGENCY_CONFIG", cfg)
    monkeypatch.delenv("AGENCY_FRUGAL_LEVEL", raising=False)
    monkeypatch.delenv("AGENCY_INTENT", raising=False)
    e = Engine(":memory:")
    yield {"engine": e, "cfg": cfg, "mp": monkeypatch, "report": None}
    e.memory.close()


@given("a doctor engine with a clean config")
def _clean(deng):
    return deng


@given(parsers.parse('a doctor engine whose file sets frugal level to "{level}"'))
def _bad(deng, level):
    _config.config_set("frugal.level", level, path=deng["cfg"])
    return deng


@when("agency_doctor runs")
def _run(deng):
    deng["report"] = call_tool(deng["engine"], "agency_doctor", {})


@when("I run doctor with --write-config")
def _write_config(deng):
    from agency.__main__ import doctor_main
    doctor_main(["--write-config"])


@then(parsers.parse('the doctor config reports "{dotted}" from source "{source}"'))
def _reports(deng, dotted, source):
    values = deng["report"]["config"]["values"]
    assert values[dotted]["source"] == source, values[dotted]


@then("the doctor config redacts every secret")
def _redacts(deng):
    values = deng["report"]["config"]["values"]
    secrets = _config.secret_keys()
    assert secrets, "no secret keys registered"
    for dotted in secrets:
        assert values[dotted]["value"] in ("set", "unset"), \
            f"{dotted} leaked: {values[dotted]!r}"


@then(parsers.parse('the doctor next_steps mention "{needle}"'))
def _mentions(deng, needle):
    steps = deng["report"]["next_steps"]
    assert any(needle in s for s in steps), steps


@then("the project config exists")
def _exists(deng):
    assert os.path.exists(deng["cfg"])


@then(parsers.parse('the project frugal level is "{level}"'))
def _level(deng, level):
    assert (_config._read(deng["cfg"]).get("frugal") or {}).get("level") == level
