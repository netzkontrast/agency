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


# ── Codex review on PR #134 round 2 ───────────────────────────────────────
def test_classify_flags_bare_os_environ_passed_as_value():
    """Codex review (P2): `dict(os.environ)` reads the live env at
    request time; bare-attribute reads were missed before — only
    chained forms (`.copy()` / `["X"]`) were flagged."""
    src = (
        "import os\n"
        "def f():\n"
        "    return dict(os.environ)\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.OS_ENVIRON for v in violations), \
        f"bare `os.environ` passed as a value must be flagged; got {violations!r}"


def test_classify_flags_bare_os_environ_assigned_to_local():
    """A direct assignment `env = os.environ` is still a request-time
    read of the env at prefix-build time."""
    src = (
        "import os\n"
        "def f():\n"
        "    env = os.environ\n"
        "    return env.get('HOME')\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.OS_ENVIRON for v in violations)


def test_classify_flags_bare_environ_from_os_import_as_value():
    """`from os import environ; len(environ)` reads via the bare name."""
    src = (
        "from os import environ\n"
        "def f():\n"
        "    return len(environ)\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.OS_ENVIRON for v in violations)


def test_classify_handles_dotted_import_top_level_binding():
    """Codex review (P2): `import os.path` binds the top-level `os` per
    Python semantics; a later `os.environ` read must still resolve to
    the canonical module and get flagged."""
    src = (
        "import os.path\n"
        "def f():\n"
        "    return os.environ['HOME']\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.OS_ENVIRON for v in violations), \
        f"`import os.path` should still resolve `os.environ`; got {violations!r}"


def test_classify_respects_parameter_shadowing_for_bare_time():
    """Codex review (P2): `from time import time; def render(time):
    return time()` — the parameter shadows the import; the inner call
    is to the PARAMETER, not stdlib `time.time()`. The classifier MUST
    NOT flag this once the lint is promoted to a CI gate (Slice 2.2)."""
    src = (
        "from time import time\n"
        "def render(time):\n"
        "    return time()\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.TIME_TIME for v in violations), \
        f"parameter `time` shadows import; bare call must not classify as TIME_TIME; got {violations!r}"


def test_classify_respects_local_assignment_shadowing():
    """A local rebinding (`time = something_else`) shadows the import
    too — subsequent calls to `time()` reference the local."""
    src = (
        "import time\n"
        "def f(clock):\n"
        "    time = clock\n"
        "    return time()\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.TIME_TIME for v in violations)


def test_classify_still_flags_outer_scope_when_inner_shadows():
    """Scope is hierarchical: an inner function's parameter shadows the
    import within its body, but the outer scope still resolves the
    import. The classifier MUST flag the outer call site."""
    src = (
        "import time\n"
        "def outer():\n"
        "    def inner(time):\n"
        "        return time()\n"
        "    return time.time()\n"
    )
    violations = audit_source(src, path="x.py")
    time_hits = [v for v in violations if v.kind == ViolationKind.TIME_TIME]
    assert len(time_hits) == 1, \
        f"outer `time.time()` must still be flagged; got {violations!r}"


# ── Codex review on PR #134 round 3 ───────────────────────────────────────
def test_json_dumps_list_payload_not_flagged_as_unsorted_dict():
    """Codex review (P2): `json.dumps(["a", "b"])` has no key-order
    leak — lists serialize positionally. UNSORTED_DICT should only
    fire when the payload could be dict-like."""
    src = (
        "import json\n"
        "def f():\n"
        "    return json.dumps(['a', 'b'])\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.UNSORTED_DICT for v in violations), \
        f"list payload to json.dumps must not flag UNSORTED_DICT; got {violations!r}"


def test_json_dumps_string_constant_payload_not_flagged():
    """Atomic constants (str/int/None) have no order. Don't flag."""
    src = (
        "import json\n"
        "def f():\n"
        "    return json.dumps('hello')\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.UNSORTED_DICT for v in violations)


def test_json_dumps_dict_literal_still_flagged():
    """A dict literal IS order-sensitive — must still flag without
    sort_keys=True."""
    src = (
        "import json\n"
        "def f():\n"
        "    return json.dumps({'a': 1, 'b': 2})\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UNSORTED_DICT for v in violations)


def test_json_dumps_opaque_name_flagged_conservatively():
    """When the payload is a Name (e.g. a dict variable), the lint
    can't prove it's not a dict — flag conservatively."""
    src = (
        "import json\n"
        "def f(d):\n"
        "    return json.dumps(d)\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UNSORTED_DICT for v in violations)


def test_default_expressions_evaluated_in_enclosing_scope():
    """Codex review (P2): `def f(now=time.time()): ...` — the default
    runs at def-time in the ENCLOSING scope, BEFORE the parameter is
    bound. The poisoned default leaks request-time into the prefix."""
    src = (
        "import time\n"
        "def f(now=time.time()):\n"
        "    return now\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations), \
        f"poisoned default `time.time()` must flag; got {violations!r}"


def test_default_expression_with_self_shadowing_name_still_flags():
    """`from uuid import uuid4; def f(uuid4=uuid4()): ...` — the
    default `uuid4()` evaluates in enclosing scope BEFORE the
    parameter `uuid4` exists. Still flag."""
    src = (
        "from uuid import uuid4\n"
        "def f(uuid4=uuid4()):\n"
        "    return uuid4\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UUID4 for v in violations), \
        f"poisoned default `uuid4()` must flag; got {violations!r}"


def test_comprehension_target_does_not_leak_into_function_scope():
    """Codex review (P2): comprehension loop vars are scoped to the
    comprehension in Python 3 — `[t for t in xs]` does NOT pollute
    the enclosing function. A later `time.time()` must classify."""
    src = (
        "import time\n"
        "def f(xs):\n"
        "    _ = [t for t in xs]\n"
        "    return time.time()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations)


def test_comprehension_target_does_not_leak_even_when_named_same():
    """`[time for time in xs]` doesn't leak the comp target. After
    the comprehension ends, `time` reverts to the import."""
    src = (
        "import time\n"
        "def f(xs):\n"
        "    _ = [time for time in xs]\n"
        "    return time.time()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations), \
        f"comp target `time` must not leak; got {violations!r}"


def test_comprehension_target_shadows_inside_comprehension():
    """Conversely, INSIDE the comprehension body the target DOES
    shadow — `[time() for time in xs]` calls the comp target, not
    stdlib `time()`. Must NOT classify."""
    src = (
        "from time import time\n"
        "def f(xs):\n"
        "    return [time() for time in xs]\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.TIME_TIME for v in violations), \
        f"inside-comp call to comp target `time` must not classify; got {violations!r}"


# ── Codex review on PR #134 round 4 ───────────────────────────────────────
def test_json_dumps_list_with_inner_dict_still_flagged():
    """Codex review (P2): `json.dumps([{"a": 1}])` — outer is a list,
    but the inner dict still leaks key-order. The detector must
    recurse into container elements before clearing them."""
    src = (
        "import json\n"
        "def f():\n"
        "    return json.dumps([{'a': 1, 'b': 2}])\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UNSORTED_DICT for v in violations), \
        f"list-of-dict payload must still flag UNSORTED_DICT; got {violations!r}"


def test_json_dumps_nested_list_of_lists_of_constants_not_flagged():
    """Recursion bottoms out: a list of lists of constants has no
    dict at any depth — clean."""
    src = (
        "import json\n"
        "def f():\n"
        "    return json.dumps([['a', 'b'], ['c']])\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.UNSORTED_DICT for v in violations)


def test_json_dumps_tuple_with_inner_dict_flagged():
    """Recursion works on Tuple containers too."""
    src = (
        "import json\n"
        "def f():\n"
        "    return json.dumps(({'a': 1}, 'x'))\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UNSORTED_DICT for v in violations)


def test_json_dumps_listcomp_with_dict_element_flagged():
    """`json.dumps([{"x": v} for v in xs])` — the comprehension's
    element IS a dict, so the payload is order-sensitive."""
    src = (
        "import json\n"
        "def f(xs):\n"
        "    return json.dumps([{'x': v} for v in xs])\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UNSORTED_DICT for v in violations)


def test_parameter_annotation_evaluated_in_enclosing_scope():
    """Codex review (P2): `def f(x: time.time()): ...` — the
    annotation runs at def-time in the ENCLOSING scope when no
    `from __future__ import annotations`. The poisoned annotation
    leaks request-time into the prefix across process starts."""
    src = (
        "import time\n"
        "def f(x: time.time()):\n"
        "    return x\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations), \
        f"poisoned annotation `time.time()` must flag; got {violations!r}"


def test_kwarg_annotation_with_poison_call_flagged():
    """*args / **kwargs annotations get visited too."""
    src = (
        "import uuid\n"
        "def f(**kw: uuid.uuid4()):\n"
        "    return kw\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UUID4 for v in violations)


def test_envelope_rejects_non_string_prefix_keys():
    """Codex review (P2): non-string keys (e.g. int `1`) silently
    collide with their stringified form across prefix/body halves
    once JSON is emitted. The overlap check sees the raw Python keys
    and misses the collision. ResponseEnvelope must reject non-str
    keys at construction time."""
    from agency._envelope import ResponseEnvelope
    with pytest.raises(TypeError, match="keys must be str"):
        ResponseEnvelope(prefix={1: "stable"}, body={"per-call": True})
    with pytest.raises(TypeError, match="keys must be str"):
        ResponseEnvelope(prefix={"stable": 1}, body={1: "per-call"})


def test_envelope_rejects_collision_via_int_string_coercion():
    """The motivating case: `prefix={1: "stable"}`, `body={"1":
    "per-call"}` — both serialize as the JSON key `"1"`. Must
    reject before the silent overwrite can happen."""
    from agency._envelope import ResponseEnvelope
    with pytest.raises(TypeError, match="keys must be str"):
        ResponseEnvelope(prefix={1: "stable"}, body={"1": "per-call"})


# ── Codex review on PR #134 round 5 ───────────────────────────────────────
def test_class_body_assignment_shadows_imported_name():
    """Codex review (P2): `from time import time; class C: time =
    lambda:1; x = time()` — the class-body assignment shadows the
    import for subsequent class-body expressions. Must NOT classify."""
    src = (
        "from time import time\n"
        "class C:\n"
        "    time = lambda: 1\n"
        "    x = time()\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.TIME_TIME for v in violations), \
        f"class-body shadow must suppress TIME_TIME; got {violations!r}"


def test_class_body_shadow_does_not_leak_into_methods():
    """Class-body bindings are NOT visible inside method bodies —
    they're accessed via `self.` or the class name. A method calling
    `time.time()` must still classify."""
    src = (
        "import time\n"
        "class C:\n"
        "    time = 'shadow'\n"
        "    def m(self):\n"
        "        return time.time()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations), \
        f"class shadow must NOT leak into methods; got {violations!r}"


def test_future_annotations_skips_parameter_annotation_visits():
    """Codex review (P2): with `from __future__ import annotations`
    (PEP 563), parameter + return annotations are STRINGS at runtime
    — NOT evaluated at def-time. The auditor must skip them."""
    src = (
        "from __future__ import annotations\n"
        "import time\n"
        "import uuid\n"
        "def f(x: time.time()) -> uuid.uuid4():\n"
        "    return x\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.TIME_TIME for v in violations)
    assert all(v.kind != ViolationKind.UUID4 for v in violations)


def test_future_annotations_does_not_skip_default_values():
    """Defaults are STILL evaluated at def-time even with future
    annotations — only annotations are deferred."""
    src = (
        "from __future__ import annotations\n"
        "import time\n"
        "def f(x=time.time()):\n"
        "    return x\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations)


def test_global_declaration_does_not_shadow_imported_name():
    """Codex review (P2): `import time; def f(): global time; x =
    time.time(); time = None` — the `global time` declaration means
    `time` is NOT local; the assignment writes to the global binding
    (= the import). `time.time()` still resolves to the imported
    module and must classify."""
    src = (
        "import time\n"
        "def f():\n"
        "    global time\n"
        "    x = time.time()\n"
        "    time = None\n"
        "    return x\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations), \
        f"global-declared name must NOT suppress classification; got {violations!r}"


def test_nonlocal_declaration_does_not_shadow_imported_name():
    """`nonlocal` declarations behave like `global` for shadowing —
    the name refers to an enclosing binding, not a fresh local."""
    src = (
        "import time\n"
        "def outer():\n"
        "    time_val = 0\n"
        "    def inner():\n"
        "        nonlocal time_val\n"
        "        return time.time()\n"
        "    return inner\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations)


# ── Codex review on PR #134 round 6 ───────────────────────────────────────
def test_star_import_from_os_pre_registers_known_names():
    """Codex review (P2): `from os import *; getenv('HOME')` —
    `getenv` enters scope via the star import. The auditor doesn't
    introspect os at audit time, so it pre-registers the known
    prefix-poison names for stdlib star imports."""
    src = (
        "from os import *\n"
        "def f():\n"
        "    return getenv('HOME')\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.OS_ENVIRON for v in violations), \
        f"star import getenv must classify; got {violations!r}"


def test_star_import_from_uuid_pre_registers_uuid4():
    src = (
        "from uuid import *\n"
        "def f():\n"
        "    return uuid4()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.UUID4 for v in violations)


def test_star_import_from_time_pre_registers_time():
    src = (
        "from time import *\n"
        "def f():\n"
        "    return time()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations)


def test_class_body_call_before_shadow_still_flags():
    """Codex review (P2): class body is populated SEQUENTIALLY — a
    call that appears BEFORE its same-name assignment resolves to
    the import. `from time import time; class C: x = time(); time =
    lambda:1` must still flag the `time()` call."""
    src = (
        "from time import time\n"
        "class C:\n"
        "    x = time()\n"
        "    time = lambda: 1\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations), \
        f"call before shadow must classify; got {violations!r}"


def test_nested_scope_import_does_not_overwrite_module_alias():
    """Codex review (P2): nested-scope imports don't rebind module-
    level aliases. `from time import time; def f(): return time(); def
    g(): from math import sqrt as time` — the helper's import must
    NOT poison the alias used by `f`."""
    src = (
        "from time import time\n"
        "def build():\n"
        "    return time()\n"
        "def helper():\n"
        "    from math import sqrt as time\n"
        "    return time(1.0)\n"
    )
    violations = audit_source(src, path="x.py")
    # build()'s time() should classify; helper()'s call to its OWN
    # `time` (math.sqrt) should not.
    time_hits = [v for v in violations if v.kind == ViolationKind.TIME_TIME]
    assert len(time_hits) >= 1, \
        f"build()'s time() must still classify; got {violations!r}"


def test_environ_subscript_write_does_not_flag():
    """Codex review (P2): `os.environ['TZ'] = 'UTC'` writes to the
    environment, doesn't read from it. No host value flows into the
    prefix — must NOT flag."""
    src = (
        "import os\n"
        "def f():\n"
        "    os.environ['TZ'] = 'UTC'\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.OS_ENVIRON for v in violations), \
        f"environ write must not flag as read; got {violations!r}"


def test_environ_full_rebind_does_not_flag():
    """`os.environ = {}` rebinds the module attribute — write, not
    read. Skip."""
    src = (
        "import os\n"
        "def f():\n"
        "    os.environ = {}\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.OS_ENVIRON for v in violations)


def test_environ_read_still_flags_alongside_writes():
    """Regression: a write doesn't poison; subsequent reads still do."""
    src = (
        "import os\n"
        "def f():\n"
        "    os.environ['TZ'] = 'UTC'\n"
        "    return os.environ['TZ']\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.OS_ENVIRON for v in violations)


def test_relative_from_import_does_not_classify():
    """Codex review (P2): `from .time import time` is a package-local
    module, not the stdlib API. The classifier must skip it."""
    src = (
        "from .time import time\n"
        "def f():\n"
        "    return time()\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.TIME_TIME for v in violations), \
        f"relative `.time` import must not classify; got {violations!r}"


def test_datetime_utcnow_flags():
    """Codex review (P2): `datetime.utcnow()` is just as
    request-time-dependent as `now()` — must classify."""
    src = (
        "import datetime\n"
        "def f():\n"
        "    return datetime.datetime.utcnow()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.DATETIME_NOW for v in violations)


def test_bare_datetime_utcnow_flags():
    src = (
        "from datetime import datetime\n"
        "def f():\n"
        "    return datetime.utcnow()\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.DATETIME_NOW for v in violations)


def test_local_variable_annotation_does_not_evaluate():
    """Codex review (P2): annotations on local variables inside
    functions are NOT evaluated at runtime (Python 3 only builds
    `__annotations__` for module/class scope). So a poisoned
    annotation on a local doesn't flow into the prefix; the auditor
    must skip it. `def f(): x: time.time() = 1` is clean."""
    src = (
        "import time\n"
        "def f():\n"
        "    x: time.time() = 1\n"
        "    return x\n"
    )
    violations = audit_source(src, path="x.py")
    assert all(v.kind != ViolationKind.TIME_TIME for v in violations), \
        f"local annotation `time.time()` must not flag; got {violations!r}"


def test_module_level_annotation_still_evaluates():
    """Module-level annotations ARE evaluated and stored in
    `__annotations__`. So a poisoned module-level annotation
    still flags."""
    src = (
        "import time\n"
        "x: time.time() = 1\n"
    )
    violations = audit_source(src, path="x.py")
    assert any(v.kind == ViolationKind.TIME_TIME for v in violations)


def test_canonical_json_preserves_prefix_before_body_when_body_sorts_first():
    """Codex review (P1): `json.dumps(env.to_dict(), sort_keys=True)`
    re-sorted the merged dict GLOBALLY, so a body key like `"delta"`
    would serialize ahead of a prefix key like `"schema_version"` —
    breaking the prompt-cache prefix invariant."""
    import json
    from agency._envelope import ResponseEnvelope, canonical_json
    env = ResponseEnvelope(
        prefix={"schema_version": 1},                                      # 's' > 'd'
        body={"delta": "x"},                                               # would sort first
    )
    blob = canonical_json(env)
    decoded = json.loads(blob, object_pairs_hook=list)
    keys = [k for k, _ in decoded]
    # prefix bytes MUST precede body bytes regardless of key ordering.
    assert keys == ["schema_version", "delta"], (
        f"canonical_json must keep prefix keys before body keys even when "
        f"body keys sort earlier alphabetically; got {keys!r}")


# ─────────────── Slice 2.2 — baseline + WARN→error gate ───────────────────
# Spec 146 Slice 2.2 ships:
#   - `BaselineEntry(path, line, kind)` + `load_baseline(path)` parser
#   - `compare_to_baseline(report, baseline)` → RegressionReport
#   - CLI `--baseline PATH --strict` gates: only regressions exit 1
#   - `Plan/_planning/prefix-lint-baseline.txt` enumerates the live set
#     so the gate flags REGRESSIONS only (Spec 054 drift pattern).
def test_load_baseline_parses_path_line_kind(tmp_path):
    """Baseline lines are `<path>:<line>:<kind>` — deterministic, one
    per known violation. Whitespace + blank/comment lines tolerated."""
    from scripts.check_response_prefix import load_baseline
    f = tmp_path / "baseline.txt"
    f.write_text(
        "# header\n"
        "\n"
        "agency/engine.py:42:os_environ\n"
        "agency/_runner.py:20:time_time\n"
    )
    entries = load_baseline(f)
    assert {(e.path, e.line, e.kind.value) for e in entries} == {
        ("agency/engine.py", 42, "os_environ"),
        ("agency/_runner.py", 20, "time_time"),
    }


def test_load_baseline_missing_file_returns_empty(tmp_path):
    """A missing baseline → empty set (no regression target)."""
    from scripts.check_response_prefix import load_baseline
    entries = load_baseline(tmp_path / "nope.txt")
    assert entries == set()


def test_load_baseline_rejects_malformed_line(tmp_path):
    """A line with the wrong shape (`path:line:kind`) is a doctrine
    error — fail loud so a typo doesn't silently bypass the gate."""
    from scripts.check_response_prefix import load_baseline
    f = tmp_path / "baseline.txt"
    f.write_text("agency/engine.py:not-a-number:os_environ\n")
    with pytest.raises(ValueError):
        load_baseline(f)


def test_compare_to_baseline_ok_when_report_matches_baseline():
    """No new violations, no fixed → `RegressionReport.ok == True`."""
    from scripts.check_response_prefix import (
        BaselineEntry, compare_to_baseline, FileLoc, PrefixReport)
    rep = PrefixReport(violations=[
        PrefixViolation(loc=FileLoc("a.py", 10), kind=ViolationKind.TIME_TIME)
    ])
    baseline = {BaselineEntry("a.py", 10, ViolationKind.TIME_TIME)}
    res = compare_to_baseline(rep, baseline)
    assert res.ok is True
    assert res.new_violations == []
    assert res.fixed_violations == []


def test_compare_to_baseline_flags_new_violation_as_regression():
    """A violation NOT in the baseline is a regression — gate flag."""
    from scripts.check_response_prefix import (
        BaselineEntry, compare_to_baseline, FileLoc, PrefixReport)
    rep = PrefixReport(violations=[
        PrefixViolation(loc=FileLoc("a.py", 10), kind=ViolationKind.TIME_TIME),
        PrefixViolation(loc=FileLoc("b.py", 22), kind=ViolationKind.UUID4),
    ])
    baseline = {BaselineEntry("a.py", 10, ViolationKind.TIME_TIME)}
    res = compare_to_baseline(rep, baseline)
    assert res.ok is False
    assert len(res.new_violations) == 1
    new = res.new_violations[0]
    assert (new.loc.path, new.loc.line, new.kind) == (
        "b.py", 22, ViolationKind.UUID4)


def test_compare_to_baseline_surfaces_fixed_violations():
    """A baseline entry with no matching live violation = fix → trim
    baseline. fixed_violations carries them so the gate prompts the
    author to update the baseline file."""
    from scripts.check_response_prefix import (
        BaselineEntry, compare_to_baseline, PrefixReport)
    rep = PrefixReport(violations=[])
    baseline = {BaselineEntry("a.py", 10, ViolationKind.TIME_TIME)}
    res = compare_to_baseline(rep, baseline)
    assert res.ok is True                              # fewer is fine
    assert res.fixed_violations == [
        BaselineEntry("a.py", 10, ViolationKind.TIME_TIME)]


def test_cli_strict_without_baseline_fails_on_any_violation(tmp_path, capsys):
    """`--strict` without `--baseline` → any violation exits 1."""
    from scripts.check_response_prefix import main
    src = tmp_path / "x.py"
    src.write_text("import time\ndef f(): return time.time()\n")
    rc = main(["--root", str(src), "--strict"])
    assert rc == 1


def test_cli_strict_with_matching_baseline_exits_0(tmp_path):
    """`--strict --baseline` ignores known sites; only regressions fail."""
    from scripts.check_response_prefix import main
    src = tmp_path / "x.py"
    src.write_text("import time\ndef f(): return time.time()\n")
    baseline = tmp_path / "baseline.txt"
    baseline.write_text(f"{src!s}:2:time_time\n")
    rc = main(["--root", str(src), "--strict", "--baseline", str(baseline)])
    assert rc == 0


def test_cli_strict_with_baseline_exits_1_on_new_violation(tmp_path):
    """An unknown site with `--strict --baseline` → exit 1."""
    from scripts.check_response_prefix import main
    src = tmp_path / "x.py"
    src.write_text(
        "import time\n"
        "import uuid\n"
        "def f(): return time.time()\n"
        "def g(): return uuid.uuid4()\n"
    )
    # Baseline knows only the time.time() site
    baseline = tmp_path / "baseline.txt"
    baseline.write_text(f"{src!s}:3:time_time\n")
    rc = main(["--root", str(src), "--strict", "--baseline", str(baseline)])
    assert rc == 1


def test_live_baseline_file_matches_live_substrate_violations():
    """The committed `Plan/_planning/prefix-lint-baseline.txt` MUST
    enumerate every current live `agency/` violation — invariant: the
    set of audited violations equals the baseline set. A new
    violation forces a baseline update (drift gate), and a fix forces
    a removal."""
    from scripts.check_response_prefix import (
        audit_tree, load_baseline, compare_to_baseline)
    rep = audit_tree(Path("agency"))
    baseline = load_baseline(Path("Plan/_planning/prefix-lint-baseline.txt"))
    res = compare_to_baseline(rep, baseline)
    assert res.new_violations == [], (
        "the live `agency/` audit produced violations NOT in "
        "`Plan/_planning/prefix-lint-baseline.txt`. Either fix the "
        "regression OR add the new site to the baseline (and the "
        "fix should follow soon). New sites:\n"
        + "\n".join(f"  {v.loc.path}:{v.loc.line}  {v.kind.value}"
                    for v in res.new_violations))
    assert res.fixed_violations == [], (
        "the baseline lists violations that no longer exist — trim them "
        "from `Plan/_planning/prefix-lint-baseline.txt`. Fixed sites:\n"
        + "\n".join(f"  {e.path}:{e.line}  {e.kind.value}"
                    for e in res.fixed_violations))
