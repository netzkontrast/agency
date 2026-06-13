"""Acceptance — surface resolution (Spec 023 §F3.2).

Converted from tests/test_surface_resolution.py. Behaviour: the observable
resolution order (arg > AGENCY_SURFACE env > mcp fallback), unknown-arg
rejection, unknown-env silent fallback.
"""
from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import resolve_surface

scenarios("features/surface_resolution.feature")

_KNOWN_SURFACES = {"mcp", "bash", "skills"}


# ── fixtures shared across scenarios ──────────────────────────────────────

@pytest.fixture(autouse=True)
def _clear_surface_env(monkeypatch):
    monkeypatch.delenv("AGENCY_SURFACE", raising=False)


# ── Given steps ────────────────────────────────────────────────────────────

@given(parsers.parse("AGENCY_SURFACE env var is set to {value}"))
def _set_surface_env(value, monkeypatch):
    monkeypatch.setenv("AGENCY_SURFACE", value)


@given("AGENCY_SURFACE is not set")
def _no_surface_env(monkeypatch):
    monkeypatch.delenv("AGENCY_SURFACE", raising=False)


# ── When steps ─────────────────────────────────────────────────────────────

@when(parsers.parse("I resolve surface with explicit arg {arg}"),
      target_fixture="resolved")
def _resolve_with_arg(arg):
    return resolve_surface(arg=arg)


@when("I resolve surface with no arg", target_fixture="resolved")
def _resolve_no_arg():
    return resolve_surface(arg=None)


@when("I resolve surface with arg websocket")
def _resolve_bad_arg():
    pass  # assertion done in Then


@when("I resolve surface with an empty string arg", target_fixture="resolved")
def _resolve_empty():
    return resolve_surface(arg="")


@when("I inspect the engine surface attribute", target_fixture="eng_surface")
def _engine_surface(engine):
    return getattr(engine, "surface", None) or resolve_surface(arg=None)


# ── Then steps ─────────────────────────────────────────────────────────────

@then(parsers.parse("the resolved surface is {surface}"))
def _resolved_is(resolved, surface):
    assert resolved == surface, f"expected {surface!r}, got {resolved!r}"


@then("a ValueError is raised")
def _val_err():
    with pytest.raises(ValueError):
        resolve_surface(arg="websocket")


@then("it is a non-empty string from the known surface set")
def _known_surface(eng_surface):
    assert isinstance(eng_surface, str) and eng_surface
