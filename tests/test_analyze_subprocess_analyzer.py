"""Spec 286 — the shared SubprocessAnalyzer template scaffold.

Locks the degrade-silently contract the ruff/bandit/radon wrappers used to
each re-implement: missing tool / subprocess failure / error return code /
unparseable JSON all yield ``[]``; only a clean run reaches ``map_payload``.
"""
from __future__ import annotations

import subprocess
import types

import pytest

from agency.capabilities.analyze._subprocess_analyzer import (
    SubprocessAnalyzer, _SUBPROCESS_TIMEOUT)
from agency.capabilities.analyze._findings import make_finding


class _StubAnalyzer(SubprocessAnalyzer):
    tool = "stubtool"
    label = "stubtool"

    def argv(self, root):
        return ["stubtool", root]

    def ok_returncode(self, rc):
        return rc <= 1          # mirror the ruff/bandit tolerance

    def empty_payload(self):
        return []

    def map_payload(self, payload):
        return [make_finding(rule=item["rule"], severity="warn",
                             file=item["file"], line=1, message="m", evidence="e")
                for item in payload]


def _fake_run(stdout="", returncode=0):
    def _run(argv, **kwargs):
        # the template MUST pass the shared timeout + capture flags
        assert kwargs["timeout"] == _SUBPROCESS_TIMEOUT
        assert kwargs["capture_output"] is True and kwargs["text"] is True
        return types.SimpleNamespace(stdout=stdout, stderr="", returncode=returncode)
    return _run


def test_missing_tool_returns_empty(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda t: None)
    assert _StubAnalyzer().run(".") == []


def test_subprocess_failure_returns_empty(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda t: "/usr/bin/stubtool")

    def _boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="stubtool", timeout=_SUBPROCESS_TIMEOUT)
    monkeypatch.setattr("subprocess.run", _boom)
    assert _StubAnalyzer().run(".") == []


def test_error_returncode_returns_empty(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda t: "/usr/bin/stubtool")
    monkeypatch.setattr("subprocess.run", _fake_run(stdout="[]", returncode=2))
    assert _StubAnalyzer().run(".") == []


def test_findings_present_returncode_is_ok(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda t: "/usr/bin/stubtool")
    monkeypatch.setattr(
        "subprocess.run",
        _fake_run(stdout='[{"rule": "X1", "file": "a.py"}]', returncode=1))
    out = _StubAnalyzer().run(".")
    assert len(out) == 1 and out[0].rule == "X1"


def test_bad_json_returns_empty(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda t: "/usr/bin/stubtool")
    monkeypatch.setattr("subprocess.run", _fake_run(stdout="not json{", returncode=0))
    assert _StubAnalyzer().run(".") == []


def test_empty_stdout_uses_empty_payload(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda t: "/usr/bin/stubtool")
    monkeypatch.setattr("subprocess.run", _fake_run(stdout="", returncode=0))
    assert _StubAnalyzer().run(".") == []


def test_hooks_are_abstract():
    base = SubprocessAnalyzer()
    with pytest.raises(NotImplementedError):
        base.argv(".")
    with pytest.raises(NotImplementedError):
        base.ok_returncode(0)
    with pytest.raises(NotImplementedError):
        base.map_payload([])
