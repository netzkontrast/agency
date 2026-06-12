"""Spec 146 Slice 2 — `_check_response_prefix` AST lint rule.

Spec 146 Slice 1 shipped the typed `ResponseEnvelope(prefix, body)` split
+ `agency_welcome` wired through it. The prefix is byte-stable across
calls when the registry is unchanged — but only if no
non-deterministic call (`datetime.now()` / `time.time()` / `uuid4()` /
`os.environ` read at request time) sneaks into a prefix-building
function in a future PR.

This slice ships the pure AST audit (Spec 067 family) that walks every
Python file in the substrate's prefix-building paths and flags any
non-deterministic call site. Slice 2.2 promotes to a CI gate per
Spec 056/058 WARN→error doctrine.

Per CLAUDE.md rule 8: the report is a relationship invariant (the set
of violations is a SUBSET of known sites), never a pinned count.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_response_prefix import (
    PrefixViolation,
    PrefixReport,
    audit_source,
    audit_tree,
    classify_call,
    ViolationKind,
)


# ── pure call classification ───────────────────────────────────────────────
def test_classify_call_flags_datetime_now():
    """`datetime.now()` is non-deterministic — prefix poison."""
    src = (
        "import datetime\n"
        "def f():\n"
        "    return datetime.datetime.now()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.DATETIME_NOW for v in violations)


def test_classify_call_flags_bare_datetime_now():
    """`datetime.now()` (without the `datetime.` module prefix) is the
    most common form — must be flagged too."""
    src = (
        "from datetime import datetime\n"
        "def f():\n"
        "    return datetime.now()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.DATETIME_NOW for v in violations)


def test_classify_call_flags_time_time():
    src = (
        "import time\n"
        "def f():\n"
        "    return time.time()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations)


def test_classify_call_flags_uuid4():
    src = (
        "import uuid\n"
        "def f():\n"
        "    return uuid.uuid4()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UUID4 for v in violations)


def test_classify_call_flags_bare_uuid4():
    src = (
        "from uuid import uuid4\n"
        "def f():\n"
        "    return uuid4()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UUID4 for v in violations)


def test_classify_call_flags_os_environ_subscript():
    """`os.environ["X"]` read at request time captures the live env —
    prefix poison."""
    src = (
        "import os\n"
        "def f():\n"
        "    return os.environ['HOME']\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.OS_ENVIRON for v in violations)


def test_classify_call_flags_os_environ_get():
    src = (
        "import os\n"
        "def f():\n"
        "    return os.environ.get('HOME', '')\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.OS_ENVIRON for v in violations)


def test_classify_call_flags_os_getenv():
    src = (
        "import os\n"
        "def f():\n"
        "    return os.getenv('HOME')\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.OS_ENVIRON for v in violations)


def test_classify_call_passes_clean_source():
    """Deterministic code — empty violations list."""
    src = (
        "def f(x):\n"
        "    return x * 2\n"
    )
    assert audit_source(src, path="x.py") == []


def test_audit_source_returns_file_loc():
    src = (
        "import time\n"
        "def f():\n"
        "    return time.time()\n"
    )
    violations = audit_source(src, path="x.py")
    assert len(violations) == 1
    v = violations[0]
    assert isinstance(v, PrefixViolation)
    assert v.loc.path == "x.py"
    assert v.loc.line == 3


def test_audit_source_handles_syntax_error():
    """Malformed Python doesn't crash the audit — returns empty list."""
    assert audit_source("def broken(\n", path="x.py") == []


# ── tree audit + report shape ──────────────────────────────────────────────
def test_audit_tree_returns_typed_report(tmp_path):
    (tmp_path / "good.py").write_text("def f(): return 1\n")
    (tmp_path / "bad.py").write_text(
        "import time\ndef f(): return time.time()\n"
    )
    rep = audit_tree(tmp_path)
    assert isinstance(rep, PrefixReport)
    assert rep.total_files >= 2                                    # walked both
    assert len(rep.violations) == 1
    assert rep.violations[0].kind == ViolationKind.TIME_TIME


def test_audit_tree_is_deterministic(tmp_path):
    (tmp_path / "a.py").write_text("import time\ndef f(): return time.time()\n")
    (tmp_path / "b.py").write_text("import uuid\ndef g(): return uuid.uuid4()\n")
    r1 = audit_tree(tmp_path)
    r2 = audit_tree(tmp_path)
    # Sorted by (path, line) for stable output.
    assert [(v.loc.path, v.loc.line) for v in r1.violations] == \
           [(v.loc.path, v.loc.line) for v in r2.violations]


def test_audit_tree_skips_pycache(tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "stale.py").write_text(
        "import time\ndef f(): return time.time()\n"
    )
    (tmp_path / "ok.py").write_text("def f(): return 1\n")
    rep = audit_tree(tmp_path)
    # The __pycache__ entry must NOT count.
    assert all("__pycache__" not in v.loc.path for v in rep.violations)


# ── live-tree audit (informational; Slice 2.2 promotes to gate) ────────────
def test_live_tree_audit_runs_against_envelope_module():
    """Slice 2.1: assert the audit walks `agency/_envelope.py` (the
    Slice-1 module) without crashing. The module IS the prefix builder —
    any violation in it would be a doctrine bug."""
    repo = Path(__file__).parent.parent
    rep = audit_tree(repo / "agency" / "_envelope.py")
    assert isinstance(rep, PrefixReport)
    # _envelope.py is hand-authored clean per Slice 1 — zero violations.
    assert rep.violations == [], (
        f"Slice 1 envelope module has new prefix-poison violations: "
        f"{[(v.loc.path, v.loc.line, v.kind.value) for v in rep.violations]}")


def test_live_tree_audit_walks_engine_module():
    """Engine module contains `agency_welcome` (the prefix builder); Slice
    1 lifted its prefix-relevant code through ResponseEnvelope. Audit it
    as informational — Slice 2.2 will gate."""
    repo = Path(__file__).parent.parent
    rep = audit_tree(repo / "agency" / "engine.py")
    # engine.py legitimately uses `datetime.now()` for body fields like
    # `last_active` + reads `os.environ` for surface resolution — these
    # are BODY-side (Slice 1 envelope split). Slice 2.2 will refine the
    # audit to track reachability from prefix builders only.
    assert isinstance(rep, PrefixReport)
