"""Spec 042 — analyze.architecture (the architecture axis).

Dependency graph + structural metrics: import cycles (fail), package
fan-in/fan-out (warn), files > 600 LOC (warn), files > 400 LOC (info).
"""
import os

from agency.capabilities.analyze import _architecture


def _write(tmpdir: str, name: str, body: str) -> str:
    path = os.path.join(tmpdir, name)
    with open(path, "w") as f:
        f.write(body)
    return path


def test_circular_import_flagged_as_fail(tmp_path):
    # a.py imports b; b.py imports a — direct cycle.
    pkg = tmp_path
    _write(str(pkg), "__init__.py", "")
    _write(str(pkg), "a.py", "from . import b\nVALUE = 1\n")
    _write(str(pkg), "b.py", "from . import a\nVALUE = 2\n")
    findings = _architecture.scan(str(pkg))
    cycle_hits = [f for f in findings if f["rule"] == "A001"]
    assert len(cycle_hits) >= 1
    assert cycle_hits[0]["severity"] == "fail"


def test_large_file_warn(tmp_path):
    body = "\n".join(f"x{i} = {i}" for i in range(620)) + "\n"
    _write(str(tmp_path), "huge.py", body)
    findings = _architecture.scan(str(tmp_path))
    large = [f for f in findings if f["rule"] == "A002"]
    assert len(large) == 1
    assert large[0]["severity"] == "warn"


def test_medium_file_info(tmp_path):
    body = "\n".join(f"x{i} = {i}" for i in range(420)) + "\n"
    _write(str(tmp_path), "med.py", body)
    findings = _architecture.scan(str(tmp_path))
    med = [f for f in findings if f["rule"] == "A003"]
    assert len(med) == 1
    assert med[0]["severity"] == "info"


def test_no_cycle_no_finding(tmp_path):
    pkg = tmp_path
    _write(str(pkg), "__init__.py", "")
    _write(str(pkg), "a.py", "VALUE = 1\n")
    _write(str(pkg), "b.py", "from . import a\nVALUE = 2\n")
    findings = _architecture.scan(str(pkg))
    assert not [f for f in findings if f["rule"] == "A001"]
