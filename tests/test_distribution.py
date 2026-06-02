"""Spec 039 — distribution surface tests.

Pure unit tests for the new entry points + the discovery-shim logic.
The heavy E2E (`test_e2e_mcp_stdio.py`) is marked @pytest.mark.e2e
and exercises the whole pipx-install + JSON-RPC roundtrip.
"""
import json
import os
import subprocess

import pytest


# ---------------------------------------------------------------------------
# Console-script entrypoint declarations (pyproject.toml contract).
# ---------------------------------------------------------------------------


def test_pyproject_declares_three_console_scripts():
    """Spec 039 §"Distribution": three entries must be on
    [project.scripts] — agency (CLI), agency-mcp (MCP server),
    agency-doctor (bare-CLI doctor)."""
    import tomllib
    with open(os.path.join(os.path.dirname(__file__), "..", "pyproject.toml"),
              "rb") as f:
        data = tomllib.load(f)
    scripts = data["project"]["scripts"]
    assert scripts.get("agency") == "agency.cli:main"
    assert scripts.get("agency-mcp") == "agency.__main__:main"
    assert scripts.get("agency-doctor") == "agency.__main__:doctor_main"


def test_pyproject_registers_e2e_marker():
    """Spec 039 §"End-to-end tests": the `e2e` pytest marker must be
    registered to avoid PytestUnknownMarkWarning."""
    import tomllib
    with open(os.path.join(os.path.dirname(__file__), "..", "pyproject.toml"),
              "rb") as f:
        data = tomllib.load(f)
    markers = data["tool"]["pytest"]["ini_options"].get("markers", [])
    assert any(m.startswith("e2e") for m in markers), \
        "the 'e2e' marker is not registered in pyproject"


# ---------------------------------------------------------------------------
# agency.__main__.doctor_main()
# ---------------------------------------------------------------------------


def test_doctor_main_callable():
    """The agency-doctor console-script target exists and is callable."""
    from agency import __main__
    assert callable(getattr(__main__, "doctor_main", None))


def test_doctor_main_prints_json_to_stdout(capsys):
    """Spec 039 §"Done When" line 72-76: doctor_main() prints the
    agency_doctor JSON payload to stdout (token-safe, scriptable)."""
    from agency.__main__ import doctor_main
    rc = doctor_main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    # The payload IS the agency_doctor response shape (Spec 030).
    assert "ok" in payload
    assert "python_version" in payload
    assert "deps" in payload
    assert "embedder" in payload         # Spec 045 added this field
    # Spec 039 §"Distribution" line 101-102 — install-method reporting.
    assert "install_method" in payload
    assert payload["install_method"] in (
        "pipx-or-pip-on-path", "marketplace-venv", "marketplace-shim",
        "degraded", "unknown",
    )
    # Exit code matches doctor's verdict.
    assert (rc == 0 and payload["ok"]) or (rc == 1 and not payload["ok"])


# ---------------------------------------------------------------------------
# Discovery shim — the resolution logic the bash shims AND the
# `agency_mcp_binary` test fixture both apply.
# ---------------------------------------------------------------------------


def _resolve_agency_mcp_python(plugin_root: str | None = None,
                                path_env: str | None = None,
                                venv_python: str | None = None,
                                ) -> str:
    """Pure-Python mirror of the bash discovery shim's resolution.

    Order: PATH agency-mcp > <plugin_root>/.venv/bin/agency-mcp >
    <plugin_root>/bin/agency-mcp (bootstrap fallback). Returns the
    resolved binary path. Raises FileNotFoundError if none.

    ``path_env`` overrides PATH lookup for the duration of this call
    only — does NOT touch os.environ (which would pollute the test
    suite's subsequent subprocess calls).
    """
    import shutil
    p = shutil.which("agency-mcp", path=path_env)
    if p:
        return p
    if plugin_root and venv_python:
        candidate = os.path.join(plugin_root, ".venv", "bin", "agency-mcp")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    if plugin_root:
        candidate = os.path.join(plugin_root, "bin", "agency-mcp")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise FileNotFoundError("agency-mcp not found via PATH, venv, or bin/")


def test_shim_picks_path_first(tmp_path, monkeypatch):
    """When agency-mcp is on PATH AND a venv exists, PATH wins."""
    # Set up PATH version.
    path_bin = tmp_path / "path_bin"
    path_bin.mkdir()
    path_mcp = path_bin / "agency-mcp"
    path_mcp.write_text("#!/bin/sh\necho path\n")
    path_mcp.chmod(0o755)
    # Set up venv version.
    plugin_root = tmp_path / "plugin"
    venv_bin = plugin_root / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    venv_mcp = venv_bin / "agency-mcp"
    venv_mcp.write_text("#!/bin/sh\necho venv\n")
    venv_mcp.chmod(0o755)
    venv_python = venv_bin / "python"
    venv_python.write_text("#!/bin/sh\n")
    venv_python.chmod(0o755)
    # Empty rest of PATH; only path_bin available.
    resolved = _resolve_agency_mcp_python(
        plugin_root=str(plugin_root),
        path_env=str(path_bin),
        venv_python=str(venv_python))
    assert resolved == str(path_mcp)


def test_shim_falls_back_to_venv(tmp_path):
    """When PATH lacks agency-mcp but venv has it, venv wins."""
    plugin_root = tmp_path / "plugin"
    venv_bin = plugin_root / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    venv_mcp = venv_bin / "agency-mcp"
    venv_mcp.write_text("#!/bin/sh\n")
    venv_mcp.chmod(0o755)
    venv_python = venv_bin / "python"
    venv_python.write_text("#!/bin/sh\n")
    venv_python.chmod(0o755)
    # Empty PATH — only the venv path is available.
    empty_path = str(tmp_path / "empty")
    os.makedirs(empty_path, exist_ok=True)
    resolved = _resolve_agency_mcp_python(
        plugin_root=str(plugin_root),
        path_env=empty_path,
        venv_python=str(venv_python))
    assert resolved == str(venv_mcp)


def test_shim_raises_when_nothing_found(tmp_path):
    """Spec 039 §"Subprocess lifecycle discipline" line 132-136: shim
    failure modes are EXPLICIT — no silent hang, no infinite re-bootstrap."""
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError):
        _resolve_agency_mcp_python(
            plugin_root=str(tmp_path / "missing-plugin"),
            path_env=str(empty),
            venv_python=None)


# ---------------------------------------------------------------------------
# Install-collision guard (Spec 039 line 86-91 / Nygard).
# ---------------------------------------------------------------------------


def test_collision_guard_silent_when_no_plugin_root(capsys, monkeypatch):
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    from agency.__main__ import _warn_on_install_collision
    _warn_on_install_collision()
    captured = capsys.readouterr()
    assert captured.err == ""


def test_collision_guard_warns_on_two_different_paths(tmp_path, monkeypatch,
                                                       capsys):
    """When both ${CLAUDE_PLUGIN_ROOT}/.venv/bin/agency-mcp AND a
    DIFFERENT agency-mcp on PATH exist, the guard emits a stderr
    warning naming both paths."""
    # Set up a fake plugin root + venv agency-mcp.
    plugin_root = tmp_path / "plugin"
    venv_bin = plugin_root / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    venv_mcp = venv_bin / "agency-mcp"
    venv_mcp.write_text("#!/bin/sh\nexit 0\n")
    venv_mcp.chmod(0o755)
    # Different PATH agency-mcp.
    path_bin = tmp_path / "path"
    path_bin.mkdir()
    path_mcp = path_bin / "agency-mcp"
    path_mcp.write_text("#!/bin/sh\nexit 0\n")
    path_mcp.chmod(0o755)

    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setenv("PATH", str(path_bin))
    from agency.__main__ import _warn_on_install_collision
    _warn_on_install_collision()
    captured = capsys.readouterr()
    assert "two install paths" in captured.err
    assert str(path_mcp) in captured.err
    assert str(venv_mcp) in captured.err


def test_shim_exits_127_when_nothing_resolves(tmp_path, monkeypatch):
    """Spec 039 §"Subprocess lifecycle discipline" line 132-136: when
    NEITHER PATH nor venv nor a successful bootstrap exists, the shim
    exits 127 with a diagnostic — no silent hang, no infinite loop.

    Builds a hermetic plugin tree with the shim + a deliberately-
    failing bin/agency-install, and an empty PATH. The shim must
    print the diagnostic to stderr and exit 127 within a few seconds.
    """
    repo = os.path.abspath(
        os.path.join(os.path.dirname(__file__), ".."))
    plugin_root = tmp_path / "plugin"
    plugin_bin = plugin_root / "bin"
    plugin_bin.mkdir(parents=True)
    # Copy the real shim under test.
    import shutil as _sh
    _sh.copy(os.path.join(repo, "bin", "agency-mcp"),
              plugin_bin / "agency-mcp")
    os.chmod(plugin_bin / "agency-mcp", 0o755)
    # Deliberately-failing bootstrap.
    install_stub = plugin_bin / "agency-install"
    install_stub.write_text("#!/bin/sh\necho 'agency-install: simulated failure' >&2\nexit 1\n")
    os.chmod(install_stub, 0o755)
    # Sandboxed PATH: includes /bin and /usr/bin so bash + standard
    # utilities resolve, but agency-mcp does NOT — that's the whole
    # point of the test.
    sandbox_path = "/usr/bin:/bin"

    env = os.environ.copy()
    env["PATH"] = sandbox_path
    env["CLAUDE_PLUGIN_ROOT"] = str(plugin_root)
    result = subprocess.run(
        [str(plugin_bin / "agency-mcp")],
        env=env, capture_output=True, timeout=10,
    )
    assert result.returncode == 127
    assert b"bootstrap failed" in result.stderr or \
        b"resolved no binary" in result.stderr


def test_collision_guard_silent_on_same_realpath(tmp_path, monkeypatch,
                                                  capsys):
    """If the two paths resolve to the SAME real binary (symlink to
    the same target), don't warn — it's not actually a collision."""
    plugin_root = tmp_path / "plugin"
    venv_bin = plugin_root / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    real_target = tmp_path / "real-agency-mcp"
    real_target.write_text("#!/bin/sh\nexit 0\n")
    real_target.chmod(0o755)
    venv_mcp = venv_bin / "agency-mcp"
    venv_mcp.symlink_to(real_target)
    path_bin = tmp_path / "path"
    path_bin.mkdir()
    path_mcp = path_bin / "agency-mcp"
    path_mcp.symlink_to(real_target)

    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    monkeypatch.setenv("PATH", str(path_bin))
    from agency.__main__ import _warn_on_install_collision
    _warn_on_install_collision()
    captured = capsys.readouterr()
    assert "two install paths" not in captured.err
