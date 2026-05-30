"""Phase 2 RED — surface resolution: arg > env > auto, fallback `mcp`.

Spec 023 §Done When "Surface resolution" — single source of truth for which
form the engine renders. The spike (Phase 2.1) confirmed fastmcp's Context
does NOT expose the calling client's tool list, so introspection is not
available — `auto` resolves via env, then falls back to `mcp` (panel F3.2:
the more-capable surface is the safer default).
"""
from __future__ import annotations

import os

import pytest

from agency.engine import resolve_surface


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv("AGENCY_SURFACE", raising=False)


# ---- precedence: arg > env > auto -----------------------------------------


def test_explicit_arg_wins_over_env(monkeypatch):
    monkeypatch.setenv("AGENCY_SURFACE", "bash")
    assert resolve_surface(arg="mcp") == "mcp"


def test_env_wins_when_no_arg(monkeypatch):
    monkeypatch.setenv("AGENCY_SURFACE", "bash")
    assert resolve_surface(arg=None) == "bash"


def test_fallback_to_mcp_when_neither(monkeypatch):
    # No arg, no env → panel F3.2 fallback = mcp (more-capable surface)
    assert resolve_surface(arg=None) == "mcp"


# ---- validation ------------------------------------------------------------


def test_unknown_arg_raises():
    with pytest.raises(ValueError):
        resolve_surface(arg="websocket")


def test_unknown_env_falls_back_silently(monkeypatch):
    # Env is user-set; mistyping it should not crash the engine.
    monkeypatch.setenv("AGENCY_SURFACE", "GIBBERISH")
    assert resolve_surface(arg=None) == "mcp"


def test_empty_string_arg_treated_as_unset():
    # The CLI passes argparse defaults as "" sometimes; treat as None.
    assert resolve_surface(arg="") == "mcp"


# ---- Engine integration ---------------------------------------------------


def test_engine_surface_attribute_uses_resolver():
    from agency.engine import Engine
    e = Engine(":memory:", surface="bash")
    try:
        assert e.surface == "bash"
    finally:
        e.memory.close()


def test_engine_surface_default_is_mcp(monkeypatch):
    monkeypatch.delenv("AGENCY_SURFACE", raising=False)
    from agency.engine import Engine
    e = Engine(":memory:")
    try:
        assert e.surface == "mcp"
    finally:
        e.memory.close()
