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


# ── Codex review on PR #134 — fixes ────────────────────────────────────────
def test_classify_resolves_import_alias_for_time():
    """Codex review: `import time as t; t.time()` must be flagged. The
    classifier compares against the canonical module via an alias map."""
    src = (
        "import time as t\n"
        "def f():\n"
        "    return t.time()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations)


def test_classify_resolves_from_import_for_time():
    """`from time import time; time()` is the from-import form."""
    src = (
        "from time import time\n"
        "def f():\n"
        "    return time()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations)


def test_classify_resolves_aliased_from_import_for_uuid4():
    """`from uuid import uuid4 as make_id; make_id()` aliases the call."""
    src = (
        "from uuid import uuid4 as make_id\n"
        "def f():\n"
        "    return make_id()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UUID4 for v in violations)


def test_classify_resolves_from_os_import_getenv():
    """`from os import getenv; getenv("X")` is the bare-name form."""
    src = (
        "from os import getenv\n"
        "def f():\n"
        "    return getenv('HOME')\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.OS_ENVIRON for v in violations)


def test_classify_resolves_from_os_import_environ():
    """`from os import environ; environ["X"]` reads via the bare name."""
    src = (
        "from os import environ\n"
        "def f():\n"
        "    return environ['HOME']\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.OS_ENVIRON for v in violations)


def test_classify_flags_os_environ_copy_and_items():
    """Codex review: direct reads like .copy() / .items() were missed
    before. All `os.environ.<anything>` is a request-time env read."""
    src = (
        "import os\n"
        "def f():\n"
        "    return os.environ.copy()\n"
        "def g():\n"
        "    return os.environ.items()\n"
        "def h():\n"
        "    return os.environ.keys()\n"
    )
    violations = audit_source(src, path="x.py")
    # All three should be flagged.
    assert sum(1 for v in violations if v.kind == ViolationKind.OS_ENVIRON) >= 3


def test_classify_flags_datetime_now_via_from_import():
    """`from datetime import datetime; datetime.now()` is the most common
    form — classifier resolves the bare `datetime` name."""
    src = (
        "from datetime import datetime\n"
        "def f():\n"
        "    return datetime.now()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.DATETIME_NOW for v in violations)


def test_classify_flags_aliased_datetime_now():
    """`import datetime as dt; dt.datetime.now()` aliases the module."""
    src = (
        "import datetime as dt\n"
        "def f():\n"
        "    return dt.datetime.now()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.DATETIME_NOW for v in violations)


def test_audit_tree_raises_on_missing_root(tmp_path):
    """Codex review: a typo'd or moved path must NOT silently report
    zero violations. Slice 2.2's gate depends on this signaling."""
    from scripts.check_response_prefix import PrefixAuditError
    missing = tmp_path / "does-not-exist"
    with pytest.raises(PrefixAuditError):
        audit_tree(missing)


# ── UNSORTED_DICT — json.dumps without sort_keys=True ─────────────────────
def test_classify_flags_json_dumps_without_sort_keys():
    """Codex review: Spec 146's lint checklist includes unsorted-dict
    prefix builders. `json.dumps(d)` without `sort_keys=True` lets
    hash-order leak into the prefix across runs."""
    src = (
        "import json\n"
        "def f(d):\n"
        "    return json.dumps(d)\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UNSORTED_DICT for v in violations)


def test_classify_passes_json_dumps_with_sort_keys():
    """The canonical-JSON form (sort_keys=True) is fine and must NOT
    flag — it's exactly the discipline Spec 146 Slice 1 ships in
    `agency/_envelope.py`'s `canonical_json`."""
    src = (
        "import json\n"
        "def f(d):\n"
        "    return json.dumps(d, sort_keys=True, separators=(',', ':'))\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.UNSORTED_DICT for v in violations)


def test_classify_flags_aliased_json_dumps():
    """`from json import dumps; dumps(d)` is the bare-name form."""
    src = (
        "from json import dumps\n"
        "def f(d):\n"
        "    return dumps(d)\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UNSORTED_DICT for v in violations)
