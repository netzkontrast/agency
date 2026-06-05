"""Spec 039 + Spec 055 — distribution surface tests.

Spec 055 (pipx-only, 2026-06-03) removed the legacy `.venv` bootstrap
path. The bin/agency-mcp shim is now a thin PATH router; the only
canonical install is `pipx install agency`. These tests reflect that.
"""
import json
import os

import pytest


# ---------------------------------------------------------------------------
# Console-script entrypoint declarations (pyproject.toml contract).
# ---------------------------------------------------------------------------


def test_pyproject_declares_three_console_scripts():
    """Spec 039 §"Distribution": three entries on [project.scripts] —
    agency (CLI), agency-mcp (MCP server), agency-doctor (bare-CLI doctor)."""
    import tomllib
    with open(os.path.join(os.path.dirname(__file__), "..", "pyproject.toml"),
              "rb") as f:
        data = tomllib.load(f)
    scripts = data["project"]["scripts"]
    assert scripts.get("agency") == "agency.cli:main"
    assert scripts.get("agency-mcp") == "agency.__main__:main"
    assert scripts.get("agency-doctor") == "agency.__main__:doctor_main"


def test_pyproject_registers_e2e_marker():
    """Spec 039 §"End-to-end tests": `e2e` pytest marker registered."""
    import tomllib
    with open(os.path.join(os.path.dirname(__file__), "..", "pyproject.toml"),
              "rb") as f:
        data = tomllib.load(f)
    markers = data["tool"]["pytest"]["ini_options"].get("markers", [])
    assert any(m.startswith("e2e") for m in markers)


# ---------------------------------------------------------------------------
# agency.__main__.doctor_main()
# ---------------------------------------------------------------------------


def test_doctor_main_callable():
    from agency import __main__
    assert callable(getattr(__main__, "doctor_main", None))


def test_doctor_main_prints_json_to_stdout(capsys):
    """Spec 039: doctor_main() prints the agency_doctor JSON payload."""
    from agency.__main__ import doctor_main
    rc = doctor_main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert "ok" in payload
    assert "python_version" in payload
    assert "deps" in payload
    assert "embedder" in payload         # Spec 045
    # Spec 055 (pipx-only): install_method is one of two values now.
    assert "install_method" in payload
    assert payload["install_method"] in ("pipx-or-pip-on-path", "degraded")
    assert (rc == 0 and payload["ok"]) or (rc == 1 and not payload["ok"])


