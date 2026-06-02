"""Spec 042 — analyze.performance (the performance axis).

AST-based decidable performance findings: nested O(n²) on growing
collections, += in a loop (string-concat antipattern), unbounded
`while True` without sleep/break, recursive function without
@functools.lru_cache.
"""
import os

from agency.capabilities.analyze import _performance


def _write(tmpdir: str, name: str, body: str) -> str:
    path = os.path.join(tmpdir, name)
    with open(path, "w") as f:
        f.write(body)
    return path


def test_nested_loop_on_growing_list_flagged(tmp_path):
    body = (
        "def f(items):\n"
        "    out = []\n"
        "    for x in items:\n"
        "        for y in items:\n"
        "            out.append((x, y))\n"
        "    return out\n"
    )
    _write(str(tmp_path), "n.py", body)
    findings = _performance.scan(str(tmp_path))
    nested = [f for f in findings if f["rule"] == "P001"]
    assert len(nested) >= 1
    assert nested[0]["severity"] == "warn"


def test_string_concat_in_loop_flagged(tmp_path):
    body = (
        "def build(items):\n"
        "    s = ''\n"
        "    for x in items:\n"
        "        s += str(x)\n"
        "    return s\n"
    )
    _write(str(tmp_path), "c.py", body)
    findings = _performance.scan(str(tmp_path))
    concat = [f for f in findings if f["rule"] == "P002"]
    assert len(concat) == 1
    assert concat[0]["severity"] == "info"


def test_unbounded_while_true_flagged(tmp_path):
    body = (
        "def loop():\n"
        "    while True:\n"
        "        x = 1 + 1\n"
    )
    _write(str(tmp_path), "u.py", body)
    findings = _performance.scan(str(tmp_path))
    while_hits = [f for f in findings if f["rule"] == "P003"]
    assert len(while_hits) == 1


def test_well_formed_loops_are_silent(tmp_path):
    body = (
        "def good(items):\n"
        "    parts = []\n"
        "    for x in items:\n"
        "        parts.append(str(x))\n"
        "    return ''.join(parts)\n"
    )
    _write(str(tmp_path), "g.py", body)
    findings = _performance.scan(str(tmp_path))
    # No P001 (no nested loops); no P002 (.join instead of +=).
    assert not [f for f in findings if f["rule"] in ("P001", "P002")]
