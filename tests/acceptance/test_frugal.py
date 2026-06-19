"""Acceptance — frugal core discipline level + render (Spec 326 Slice 1).

Behaviour: the active level resolves via Spec 328 config (default full, env wins,
invalid falls back, set persists); render() emits the ladder + safety floor at a
level; off is empty; the compact render is token-bounded but names the floor.
"""
from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency import _frugal
from agency.engine import Engine

scenarios("features/frugal.feature")


@pytest.fixture
def feng(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENCY_CONFIG", str(tmp_path / ".agency" / "config.yaml"))
    monkeypatch.delenv("AGENCY_FRUGAL_LEVEL", raising=False)
    monkeypatch.delenv("AGENCY_INTENT", raising=False)
    e = Engine(":memory:")
    yield {"engine": e, "mp": monkeypatch}
    e.memory.close()


@given("a frugal engine with no level override", target_fixture="feng_ctx")
def _eng_default(feng):
    return feng


@given(parsers.parse('a frugal engine with level "{level}"'), target_fixture="feng_ctx")
def _eng_level(feng, level):
    feng["mp"].setenv("AGENCY_FRUGAL_LEVEL", level)
    return feng


@when("a UserPromptSubmit event fires", target_fixture="injected")
def _ups(feng_ctx):
    out = feng_ctx["engine"].dispatch_hook(
        {"hook_event_name": "UserPromptSubmit", "session_id": "f1", "prompt": "hi"})
    return out.get("inject", "")


@when("a SessionStart event fires", target_fixture="injected")
def _ss(feng_ctx):
    out = feng_ctx["engine"].dispatch_hook(
        {"hook_event_name": "SessionStart", "session_id": "f1"})
    return out.get("inject", "")


@then(parsers.parse('the injected text contains "{needle}"'))
def _inj_has(injected, needle):
    assert needle in injected, injected


@then(parsers.parse('the injected text does not contain "{needle}"'))
def _inj_hasnt(injected, needle):
    assert needle not in injected, injected


@then("the injected text contains every safety-floor marker")
def _inj_floor(injected):
    for m in _frugal.SAFETY_FLOOR_MARKERS:
        assert m in injected, f"missing floor marker: {m!r}"


@pytest.fixture
def fx(tmp_path, monkeypatch):
    monkeypatch.delenv("AGENCY_FRUGAL_LEVEL", raising=False)
    return {"path": str(tmp_path / ".agency" / "config.yaml"), "mp": monkeypatch}


@given("no AGENCY_FRUGAL_LEVEL and an empty config file")
def _clean(fx):
    return fx


@given(parsers.parse('the env var AGENCY_FRUGAL_LEVEL is "{value}"'))
def _set_env(fx, value):
    fx["mp"].setenv("AGENCY_FRUGAL_LEVEL", value)


@when("I read the frugal level", target_fixture="level")
def _read(fx):
    return _frugal.frugal_level(path=fx["path"])


@when(parsers.parse('I set the frugal level to "{value}"'))
def _set(fx, value):
    _frugal.set_frugal_level(value, path=fx["path"])


@when(parsers.parse('I render the discipline at "{level}"'), target_fixture="rendered")
def _render(level):
    return _frugal.render(level)


@when(parsers.parse('I render the discipline at "{level}" compact'), target_fixture="rendered")
def _render_compact(level):
    return _frugal.render(level, mode="compact")


@then(parsers.parse('the level is "{value}"'))
def _level_is(level, value):
    assert level == value


@then(parsers.parse('a fresh read of the frugal level is "{value}"'))
def _fresh_level(fx, value):
    assert _frugal.frugal_level(path=fx["path"]) == value


@then(parsers.parse('the render contains "{needle}"'))
def _contains(rendered, needle):
    assert needle in rendered, rendered


@then("the render contains every safety-floor marker")
def _floor(rendered):
    for marker in _frugal.SAFETY_FLOOR_MARKERS:
        assert marker in rendered, f"missing floor marker: {marker!r}"


@then(parsers.parse("the compact render is at most {n:d} characters"))
def _short(rendered, n):
    assert len(rendered) <= n, f"{len(rendered)} chars: {rendered!r}"


@then(parsers.parse('the compact render contains "{needle}"'))
def _compact_contains(rendered, needle):
    assert needle in rendered, rendered


@then("the render is empty")
def _empty(rendered):
    assert rendered == ""
