"""Spec 159 Slice 1 — collect-caller audit + deprecation safety invariant.

Driven through the engine surface via the tdd skill walk on
intent:11e7f576. Each phase records a Phase node + a Reflection.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_collect_callers import (
    CallerSite,
    CollectCallersReport,
    audit_collect_callers,
)


def test_typed_shape_callsite():
    s = CallerSite(file="x.py", line=42, text="dogfood.collect(...)")
    assert s.file == "x.py"
    assert s.line == 42


def test_audit_returns_typed_report(tmp_path):
    """`audit_collect_callers(root)` returns a CollectCallersReport
    over the live tree (or any directory)."""
    rep = audit_collect_callers(tmp_path)
    assert isinstance(rep, CollectCallersReport)
    assert rep.caller_count == 0
    assert rep.callers == []


def test_audit_finds_explicit_caller(tmp_path):
    """A file calling `dogfood.collect(...)` is surfaced as a caller."""
    f = tmp_path / "x.py"
    f.write_text("def fn(): dogfood.collect()\n")
    rep = audit_collect_callers(tmp_path)
    assert rep.caller_count >= 1
    assert any(c.file.endswith("x.py") for c in rep.callers)


def test_audit_ignores_non_caller_mentions(tmp_path):
    """A docstring or comment mentioning `dogfood.collect` is NOT a
    caller — only call-syntax matches."""
    f = tmp_path / "y.py"
    f.write_text(
        '"""docstring mentioning dogfood.collect for context"""\n'
        "# comment about dogfood.collect\n"
        "x = 1\n")
    rep = audit_collect_callers(tmp_path)
    assert rep.caller_count == 0


def test_audit_ignores_init_imports(tmp_path):
    """`from dogfood import collect` is a re-export, not a caller —
    Slice 1 audits CALL syntax (`collect(...)`), not import lines."""
    f = tmp_path / "z.py"
    f.write_text("from dogfood import collect\n")
    rep = audit_collect_callers(tmp_path)
    assert rep.caller_count == 0


def test_audit_skips_pycache_and_tests(tmp_path):
    """`__pycache__` directories + the `tests/` directory are skipped
    (tests legitimately reference the verb in test fixtures)."""
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "cached.py").write_text(
        "dogfood.collect()\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_thing.py").write_text(
        "dogfood.collect()\n")
    (tmp_path / "real.py").write_text("dogfood.collect()\n")
    rep = audit_collect_callers(tmp_path)
    # Only `real.py` counts.
    assert rep.caller_count == 1
    assert rep.callers[0].file.endswith("real.py")


def test_live_tree_audit_yields_report():
    """The live `agency/` tree is auditable and returns a typed report.
    Slice 1 doesn't pin the count (rule 8); Slice 2 enforces caller_count
    is monotonically decreasing across PRs via a baseline file."""
    repo = Path(__file__).parent.parent
    rep = audit_collect_callers(repo / "agency")
    assert isinstance(rep, CollectCallersReport)
    assert rep.caller_count >= 0
    assert len(rep.callers) == rep.caller_count
