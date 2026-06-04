"""Spec 042 — analyze.quality (the quality axis).

Decidable lint findings: unused imports, line length > 100, function
length > 80 LOC, file length > 500 LOC, cyclomatic complexity > 12.

NO taste-judgement rules ("name is unclear" → not shipped).
"""
import os
import tempfile

import pytest

from agency.capabilities.analyze import _quality


def _write(tmpdir: str, name: str, body: str) -> str:
    path = os.path.join(tmpdir, name)
    with open(path, "w") as f:
        f.write(body)
    return path


def test_unused_imports_detected(tmp_path):
    body = (
        "import os\n"
        "import sys\n"   # unused
        "import json\n"  # unused
        "print(os.path.sep)\n"
    )
    path = _write(str(tmp_path), "u.py", body)
    findings = _quality.scan(str(tmp_path))
    rules = [f["rule"] for f in findings if f["file"].endswith("u.py")]
    assert rules.count("Q001") == 2     # Q001 = unused-import
    sys_finding = next(f for f in findings if f["evidence"].startswith("import sys"))
    assert sys_finding["severity"] == "warn"   # quality.unused: warn per Wiegers


def test_long_line_flagged(tmp_path):
    long = "x = " + "1 + " * 30 + "1"   # well over 100 chars
    body = f"{long}\n"
    _write(str(tmp_path), "L.py", body)
    findings = _quality.scan(str(tmp_path))
    long_hits = [f for f in findings if f["rule"] == "Q002"]
    assert len(long_hits) == 1
    assert long_hits[0]["severity"] == "warn"


def test_long_function_flagged(tmp_path):
    body_lines = ["def long_func():\n"]
    for i in range(90):
        body_lines.append(f"    x{i} = {i}\n")
    _write(str(tmp_path), "f.py", "".join(body_lines))
    findings = _quality.scan(str(tmp_path))
    long_func = [f for f in findings if f["rule"] == "Q003"]
    assert len(long_func) >= 1
    assert long_func[0]["severity"] == "warn"


def test_long_file_flagged(tmp_path):
    body = "\n".join(f"x{i} = {i}" for i in range(550)) + "\n"
    _write(str(tmp_path), "big.py", body)
    findings = _quality.scan(str(tmp_path))
    file_hits = [f for f in findings if f["rule"] == "Q004"]
    assert len(file_hits) == 1
    assert file_hits[0]["severity"] == "warn"


def test_severity_assignment_quality_axis():
    """Spec 042 §"Severity-assignment rule per axis" — quality:
       fail = build-blocker (cyclomatic>20, unused-with-Werror)
       warn = code-smell (cyclomatic 13–20, long line, function>80)
       info = style preference (function>60)
    """
    assert _quality.SEVERITY["Q001"] == "warn"  # unused-import
    assert _quality.SEVERITY["Q002"] == "warn"  # long-line
    assert _quality.SEVERITY["Q003"] == "warn"  # long-function (>80)
    assert _quality.SEVERITY["Q004"] == "warn"  # long-file (>500)


def test_future_annotations_not_flagged(tmp_path):
    """Dogfood finding: `from __future__ import annotations` is a
    compile-time directive, not a name binding — must NOT be flagged
    as unused even when no other code references 'annotations'."""
    body = (
        "from __future__ import annotations\n"
        "x = 1\n"
    )
    _write(str(tmp_path), "future.py", body)
    findings = _quality.scan(str(tmp_path))
    assert not [f for f in findings if f["rule"] == "Q001"]


def test_dunder_all_export_not_flagged(tmp_path):
    """Dogfood finding: a name listed in `__all__` is a re-export; its
    backing import must NOT be flagged as unused."""
    body = (
        "from somewhere import Thing\n"
        "__all__ = ['Thing']\n"
    )
    _write(str(tmp_path), "init.py", body)
    findings = _quality.scan(str(tmp_path))
    assert not [f for f in findings if f["rule"] == "Q001"]


def test_finding_shape_contract():
    body = "import sys\n"   # one unused import
    _write(str(tmp_path := tempfile.mkdtemp()), "x.py", body)
    findings = _quality.scan(tmp_path)
    assert findings
    for fnd in findings:
        for key in ("rule", "severity", "file", "line", "message", "evidence"):
            assert key in fnd, f"missing {key}"
        assert fnd["severity"] in ("info", "warn", "fail")
        assert isinstance(fnd["line"], int) and fnd["line"] >= 1
        assert len(fnd["message"]) <= 120
        assert len(fnd["evidence"]) <= 200
