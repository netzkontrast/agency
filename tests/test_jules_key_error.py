"""Spec 030 §A — JULES_API_KEY error names the marketplace config path.

Closes F2 (Hoch) from the KP Fehlerbericht: the current "Export it in
the shell that launched the engine" message misleads marketplace
plugin users — their key is wired via ${user_config.jules_api_key} at
MCP server start, NOT via the shell at call time.
"""
import os

import pytest

from agency.capabilities._jules_api import _api_key


def test_jules_key_error_names_user_config_and_doctor(monkeypatch):
    monkeypatch.delenv("JULES_API_KEY", raising=False)
    with pytest.raises(RuntimeError) as ei:
        _api_key()
    msg = str(ei.value)
    # The marketplace wiring path the user actually has to fix
    assert "user_config.jules_api_key" in msg
    # The substrate diagnostic that confirms the inheritance
    assert "agency_doctor" in msg
    # The Jules / no-MCP fallback (still valid)
    assert "agency.cli" in msg or "JULES_API_KEY=" in msg
