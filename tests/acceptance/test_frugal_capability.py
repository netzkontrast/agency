"""Acceptance — frugal capability (Spec 348 Slice 1, the ponytail port).

Behaviour: the discipline is a discoverable capability whose verbs wrap the core
_frugal module — read/switch the level, pull the ruleset (the MCP port), show the
help card. Config is isolated to a temp path so set_level never pollutes the repo.
"""
from __future__ import annotations

import pytest
from pytest_bdd import parsers, scenarios, then, when

from agency import _frugal
from conftest import invoke

scenarios("features/frugal_capability.feature")


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_CONFIG", str(tmp_path / ".agency" / "config.yaml"))
    monkeypatch.delenv("AGENCY_FRUGAL_LEVEL", raising=False)
    monkeypatch.delenv("AGENCY_FRUGAL_SESSION_INJECT", raising=False)


def _f(engine, intent, verb, **kw):
    r, _ = invoke(engine, intent, "frugal", verb, agent_id="agent:test", **kw)
    return r


@when("I read the frugal capability level", target_fixture="fr")
def _level(engine, confirmed_intent):
    return _f(engine, confirmed_intent, "level")


@when(parsers.parse('I set the frugal capability level to "{level}"'), target_fixture="fr")
def _set(engine, confirmed_intent, level):
    return _f(engine, confirmed_intent, "set_level", level=level)


@when(parsers.parse('I get the frugal instructions at "{level}"'), target_fixture="fr")
def _instr(engine, confirmed_intent, level):
    return _f(engine, confirmed_intent, "instructions", level=level)


@when("I get the frugal help", target_fixture="fr")
def _help(engine, confirmed_intent):
    return _f(engine, confirmed_intent, "help")


@then(parsers.parse('the reported frugal level is "{level}"'))
def _level_is(fr, level):
    assert fr["level"] == level, fr


@then("the frugal instructions name every safety-floor marker")
def _floor(fr):
    for m in _frugal.SAFETY_FLOOR_MARKERS:
        assert m in fr["instructions"], m


@then("the frugal instructions are empty")
def _instr_empty(fr):
    assert fr["instructions"] == "", fr


@then(parsers.parse('the frugal help contains "{needle}"'))
def _help_has(fr, needle):
    assert needle in fr["help"], fr["help"][:200]
