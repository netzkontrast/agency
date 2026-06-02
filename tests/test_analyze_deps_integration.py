"""Spec 050 — analyze deps integration tests.

Each wrapper degrades silently when its tool is missing — but when
present, the findings join the agency-native rules in the standard
Spec 042 Finding shape.
"""
import os
import shutil
import tempfile
from unittest import mock

import pytest

from agency.capabilities.analyze import _bandit, _quality, _radon, _ruff
from agency.capabilities.analyze._findings import Finding


def _write(tmpdir, name, body):
    path = os.path.join(tmpdir, name)
    with open(path, "w") as f:
        f.write(body)
    return path


# ---------------------------------------------------------------------------
# _ruff.scan
# ---------------------------------------------------------------------------


def test_ruff_silent_when_missing(tmp_path):
    """When ruff isn't on PATH, scan returns [] without raising."""
    _write(str(tmp_path), "x.py", "import sys\nx = 1\n")
    with mock.patch.object(shutil, "which", return_value=None):
        findings = _ruff.scan(str(tmp_path))
    assert findings == []


def test_ruff_finds_long_line_when_present(tmp_path):
    """When ruff IS installed, E501 (long-line) findings appear."""
    if shutil.which("ruff") is None:
        pytest.skip("ruff not installed; install via pip install -e .[analyze]")
    long_line = "x = " + "1 + " * 30 + "1"
    _write(str(tmp_path), "L.py", long_line + "\n")
    findings = _ruff.scan(str(tmp_path))
    # Expect at least one E501 (line-too-long).
    assert any(f["rule"] == "E501" for f in findings)
    # Shape matches agency Finding contract.
    f = findings[0]
    assert "severity" in f and f["severity"] in ("info", "warn", "fail")
    assert "file" in f and "line" in f and "message" in f and "evidence" in f


def test_ruff_finds_unused_import_when_present(tmp_path):
    if shutil.which("ruff") is None:
        pytest.skip("ruff not installed")
    _write(str(tmp_path), "u.py", "import sys\nx = 1\n")
    findings = _ruff.scan(str(tmp_path))
    assert any(f["rule"] == "F401" for f in findings)


# ---------------------------------------------------------------------------
# _bandit.scan
# ---------------------------------------------------------------------------


def test_bandit_silent_when_missing(tmp_path):
    _write(str(tmp_path), "x.py", "x = 1\n")
    with mock.patch.object(shutil, "which", return_value=None):
        findings = _bandit.scan(str(tmp_path))
    assert findings == []


def test_bandit_finds_eval_when_present(tmp_path):
    if shutil.which("bandit") is None:
        pytest.skip("bandit not installed")
    _write(str(tmp_path), "e.py", "def run(x): return eval(x)\n")
    findings = _bandit.scan(str(tmp_path))
    # B307 is bandit's code for use of eval.
    assert any(f["rule"].startswith("B") for f in findings)


# ---------------------------------------------------------------------------
# _radon.cyclomatic
# ---------------------------------------------------------------------------


def test_radon_silent_when_missing(tmp_path):
    _write(str(tmp_path), "x.py", "x = 1\n")
    with mock.patch.object(shutil, "which", return_value=None):
        findings = _radon.cyclomatic(str(tmp_path))
    assert findings == []


def test_radon_finds_high_complexity_when_present(tmp_path):
    if shutil.which("radon") is None:
        pytest.skip("radon not installed")
    # A function with high cyclomatic complexity (many branches).
    body = "def fn(x):\n"
    for i in range(15):
        body += f"    if x == {i}: return {i}\n"
    body += "    return -1\n"
    _write(str(tmp_path), "c.py", body)
    findings = _radon.cyclomatic(str(tmp_path))
    assert findings, "expected cyclomatic finding for 15-branch function"
    assert any(f["rule"].startswith("Q005") for f in findings)


# ---------------------------------------------------------------------------
# Integration: _quality.scan composes ruff + radon when present.
# ---------------------------------------------------------------------------


def test_quality_scan_composes_internal_plus_external(tmp_path):
    """When ruff is installed, _quality.scan returns BOTH internal
    Q001-Q004 findings AND ruff's E*/F*/W* findings — no double-
    coverage suppression."""
    if shutil.which("ruff") is None:
        pytest.skip("ruff not installed")
    _write(str(tmp_path), "mix.py",
            "import sys\n"
            "x = " + "1 + " * 30 + "1\n")
    findings = _quality.scan(str(tmp_path))
    rules = {f["rule"] for f in findings}
    # internal:
    assert "Q001" in rules or "Q002" in rules
    # ruff:
    assert "F401" in rules or "E501" in rules


def test_quality_scan_silent_external_fallback(tmp_path):
    """When ruff is missing, _quality.scan returns ONLY internal
    findings (no exception)."""
    _write(str(tmp_path), "u.py", "import sys\nx = 1\n")
    with mock.patch("shutil.which", return_value=None):
        findings = _quality.scan(str(tmp_path))
    # Internal Q001 still fires.
    assert any(f["rule"] == "Q001" for f in findings)
    # No ruff codes.
    assert not any(f["rule"].startswith(("E", "F", "W")) for f in findings)
