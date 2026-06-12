"""Spec 146 Slice 2 — `_check_response_prefix` AST lint rule.

Spec 146 Slice 1 shipped the typed `ResponseEnvelope(prefix, body)` split
+ `agency_welcome` wired through it. The prefix is byte-stable across
calls when the registry is unchanged — but only if no non-deterministic
call (`datetime.now()` / `time.time()` / `uuid4()` / `os.environ` read
at request time) sneaks into a prefix-building function in a future PR.

This slice (2.1) ships the pure AST audit (Spec 067 family) that walks
every Python file under the substrate and flags any non-deterministic
call site. Slice 2.2 promotes the audit to a CI gate per Spec 056/058
WARN→error doctrine.

Per CLAUDE.md rule 8: the report is a relationship invariant (the set
of violations is a SUBSET of known sites), never a pinned count.

Slice 2.3+ — narrow the scan to functions REACHABLE from substrate-tool
prefix builders (reachability analysis); today the audit is conservative
(every file in the audited tree contributes). The envelope module
(`agency/_envelope.py`) is the canonical prefix builder — any violation
there is a doctrine bug.
"""
from __future__ import annotations

import argparse
import ast
import enum
import sys
from dataclasses import dataclass, field
from pathlib import Path


class ViolationKind(str, enum.Enum):
    DATETIME_NOW = "datetime_now"      # datetime.now() / datetime.datetime.now()
    TIME_TIME = "time_time"            # time.time()
    UUID4 = "uuid4"                    # uuid.uuid4() / uuid4()
    OS_ENVIRON = "os_environ"          # ANY read of os.environ (subscript, .get, .copy, .items, etc.) / os.getenv
    UNSORTED_DICT = "unsorted_dict"    # json.dumps(...) without sort_keys=True (hash-order leak)


# Module-name → canonical name. The classifier walks
# Import / ImportFrom nodes once per file to build a per-file alias map
# so calls like `import time as t; t.time()` or `from time import time`
# are recognized as `time.time` (Codex review on PR #134).
@dataclass(frozen=True)
class AliasMap:
    """Per-file alias resolution. `modules` maps the bound name to the
    canonical module name (e.g. `t -> time` from `import time as t`);
    `bare_funcs` maps a bare name to a `(module, attr)` tuple (e.g.
    `make_id -> (uuid, uuid4)` from `from uuid import uuid4 as make_id`)."""

    modules: dict[str, str] = field(default_factory=dict)
    # Bare-name imports: {bound_name: (canonical_module, attr_name)}
    bare_funcs: dict[str, tuple[str, str]] = field(default_factory=dict)
    # Bare-name imports of submodule/attribute: {bound_name: (canonical_module, attr_name)}
    # E.g. `from os import environ` → {"environ": ("os", "environ")}
    bare_attrs: dict[str, tuple[str, str]] = field(default_factory=dict)


# Known prefix-poison names per stdlib module — used to expand
# `from <module> import *` star imports (Codex review on PR #134 round 6).
# The auditor can't introspect the stdlib at audit time, so we hard-code
# the names that this audit tracks. Pre-registering them simulates the
# bindings the star import would create at runtime.
_STAR_EXPORTS: dict[str, list[tuple[str, str]]] = {
    "os":       [("getenv", "getenv"), ("environ", "environ")],
    "time":     [("time", "time")],
    "uuid":     [("uuid4", "uuid4")],
    "datetime": [("datetime", "datetime")],
    "json":     [("dumps", "dumps")],
}


def _build_alias_map(tree: ast.Module) -> AliasMap:
    """Walk MODULE-LEVEL Import / ImportFrom nodes; build the per-file
    alias map used by the classifier.

    Codex review on PR #134 round 6 — nested-scope imports must NOT
    overwrite module-level aliases: a function-local `from math import
    sqrt as time` would otherwise hijack the module-level
    `from time import time`. Walking only `tree.body` keeps the alias
    map scoped to module-level imports.

    Also handles round-6 cases:
    - `from <stdlib> import *` — pre-register the known
      prefix-poison names for that stdlib module.
    - `from .x import y` (relative; `node.level > 0`) — skip; the
      target is a package-local module, not the stdlib API we audit.
    """
    am = AliasMap()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    am.modules[alias.asname] = alias.name
                else:
                    # `import os.path` binds the TOP-LEVEL `os` per Python
                    # semantics (round-1 fix).
                    top = alias.name.split(".", 1)[0]
                    am.modules[top] = top
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            # Skip relative imports — `from .x import y` targets a
            # package-local module, not the stdlib API the classifier
            # tracks (Codex review on PR #134 round 6).
            if node.level and node.level > 0:
                continue
            for alias in node.names:
                if alias.name == "*":
                    # Star import: pre-register the documented
                    # prefix-poison names for known stdlib modules
                    # (round 6). Unknown modules are left alone — a
                    # `from custom_pkg import *` doesn't affect this
                    # audit's classifications.
                    for bound_name, canonical_attr in _STAR_EXPORTS.get(
                            node.module, []):
                        am.bare_funcs[bound_name] = (
                            node.module, canonical_attr)
                        am.bare_attrs[bound_name] = (
                            node.module, canonical_attr)
                    continue
                bound = alias.asname or alias.name
                am.bare_funcs[bound] = (node.module, alias.name)
                am.bare_attrs[bound] = (node.module, alias.name)
    return am


@dataclass(frozen=True)
class FileLoc:
    path: str
    line: int


@dataclass(frozen=True)
class PrefixViolation:
    """One non-deterministic call site in a prefix-relevant module."""

    loc: FileLoc
    kind: ViolationKind
    snippet: str = ""                                              # 1-line source slice


@dataclass
class PrefixReport:
    """The Slice 2.1 audit payload. Slice 2.2 adds `floor` + a
    `baseline` set for known historical sites (Spec 054 drift pattern)."""

    violations: list[PrefixViolation] = field(default_factory=list)
    total_files: int = 0


# ── AST classifier ────────────────────────────────────────────────────────
def _resolve_module(name: str, am: AliasMap) -> str | None:
    """Return the canonical module name for `name` if it was imported
    in this file, else None. Handles `import time` (name='time'),
    `import time as t` (name='t' → 'time'), `from x import time`
    (name='time' is in bare_attrs as ('x', 'time') — NOT a module
    alias)."""
    return am.modules.get(name)


def _attr_chain_is(value: ast.AST, expected_module: str, expected_attr: str,
                    am: AliasMap) -> bool:
    """Match `<module>.<attr>` where `<module>` may be an alias.
    Returns True for the canonical name `expected_module` (after alias
    resolution) followed by `.expected_attr`."""
    if isinstance(value, ast.Attribute) and value.attr == expected_attr:
        receiver = value.value
        if isinstance(receiver, ast.Name):
            canonical = _resolve_module(receiver.id, am)
            return canonical == expected_module
    return False


def _is_load_ctx(node: ast.AST) -> bool:
    """True when `node` carries an `ast.Load` context (Subscript /
    Attribute / Name all have `.ctx`). Codex review on PR #134 round 6:
    write-only env setup like `os.environ['TZ'] = 'UTC'` or
    `os.environ = {}` must NOT flag as an OS_ENVIRON read — no host
    env value is captured into the prefix."""
    ctx = getattr(node, "ctx", None)
    if ctx is None:
        return True                                                # default to "load"
    return isinstance(ctx, ast.Load)


def _is_environ_chain(node: ast.AST, am: AliasMap) -> bool:
    """Recognize ANY read of os.environ — the bare attribute itself
    (e.g. `dict(os.environ)`), subscript (`os.environ["X"]`), attribute
    access (`.copy` / `.items` / `.keys` / `.values`), call (`.get`).
    Codex review on PR #134: bare reads passed as values were missed
    before (only Subscript + chained Attribute flagged).

    Codex review on PR #134 round 6: when the node is the TARGET of an
    assignment / del, it's a WRITE, not a read — skip. Write-only
    initialization like `os.environ['TZ'] = 'UTC'` doesn't poison the
    prefix because no host env value flows into it."""
    # Skip Store / Del context: writes don't leak host env into the prefix.
    if not _is_load_ctx(node):
        return False
    # `os.environ` (qualified) or `environ` (from-import) name match.
    def _names_environ(n: ast.AST) -> bool:
        if isinstance(n, ast.Attribute):
            return _attr_chain_is(n, "os", "environ", am)
        if isinstance(n, ast.Name):
            tup = am.bare_attrs.get(n.id)
            return tup == ("os", "environ")
        return False

    # The node IS os.environ itself — bare attribute read passed as a
    # value (e.g. `dict(os.environ)`, `env = os.environ`, `len(environ)`).
    # Without this, only chained reads like `os.environ.copy()` matched.
    if isinstance(node, ast.Attribute) and _attr_chain_is(node, "os", "environ", am):
        return True
    if isinstance(node, ast.Name) and am.bare_attrs.get(node.id) == ("os", "environ"):
        return True
    # Subscript: os.environ["X"] / environ["X"]
    if isinstance(node, ast.Subscript) and _names_environ(node.value):
        return True
    # Attribute access on os.environ (.copy / .items / .keys / .values / etc.)
    if isinstance(node, ast.Attribute) and _names_environ(node.value):
        return True
    return False


def _payload_could_be_dict(node: ast.AST) -> bool:
    """True when a `json.dumps(payload)` payload COULD evaluate to a
    dict OR CONTAIN a dict at any nesting depth (i.e. its
    serialization is key-order-sensitive). False only when EVERY
    leaf is provably non-dict.

    Codex review on PR #134 round 3: `json.dumps(["a", "b"])` must
    NOT flag — lists with non-dict leaves have no key-order leak.

    Codex review on PR #134 round 4: `json.dumps([{"a": 1}])` MUST
    flag — the outer is a list, but the inner dict still leaks
    key-order into the prefix. Recurse into List / Tuple / Set /
    comprehension elements before clearing."""
    if isinstance(node, ast.Constant):
        return False
    # Containers: clear only if EVERY element is provably non-dict.
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return any(_payload_could_be_dict(elt) for elt in node.elts)
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        # Only the element expression ends up in the dumped output;
        # generators' iter / ifs / targets are evaluated but discarded.
        return _payload_could_be_dict(node.elt)
    # Dict / DictComp / Name / Call / Attribute / Subscript / arithmetic —
    # could be a dict (Name / Call etc. are opaque; conservative-flag).
    return True


def _dumps_payload(call: ast.Call) -> ast.AST | None:
    """Return the first-arg payload of a `json.dumps(...)` call (or
    the `obj=` kwarg form). None when neither is present."""
    if call.args:
        return call.args[0]
    for kw in call.keywords:
        if kw.arg == "obj":
            return kw.value
    return None


def _is_unsorted_dumps(node: ast.Call, am: AliasMap) -> bool:
    """`json.dumps(...)` without `sort_keys=True` — hash-order leak.
    Recognizes both `json.dumps` (canonical) and aliased forms. Only
    flags when the payload could be a dict (Codex review on PR #134
    round 3); list/constant payloads have no key-order leak."""
    fn = node.func
    matches_json_dumps = False
    # Qualified `json.dumps(...)`
    if isinstance(fn, ast.Attribute) and fn.attr == "dumps":
        recv = fn.value
        if isinstance(recv, ast.Name):
            canonical = _resolve_module(recv.id, am)
            if canonical == "json":
                matches_json_dumps = True
    # Bare `dumps(...)` from `from json import dumps`
    if isinstance(fn, ast.Name):
        tup = am.bare_funcs.get(fn.id)
        if tup and tup[0] == "json" and tup[1] == "dumps":
            matches_json_dumps = True
    if not matches_json_dumps:
        return False
    # Suppress when the payload is provably non-dict-like.
    payload = _dumps_payload(node)
    if payload is not None and not _payload_could_be_dict(payload):
        return False
    return not _has_sort_keys_true(node)


def _has_sort_keys_true(call: ast.Call) -> bool:
    """Check if `call` has `sort_keys=True` (or any truthy literal) as a
    keyword argument."""
    for kw in call.keywords:
        if kw.arg == "sort_keys":
            v = kw.value
            if isinstance(v, ast.Constant) and v.value is True:
                return True
            # Conservative: only the True literal counts. Anything
            # computed at runtime is opaque.
    return False


def classify_call(node: ast.AST, am: AliasMap | None = None) -> ViolationKind | None:
    """Return the `ViolationKind` if `node` is a known prefix-poison
    call site; else None. `am` is the per-file alias map (build via
    `_build_alias_map(tree)`); when None, the classifier falls back to
    canonical names only — useful for single-node unit tests."""
    if am is None:
        am = AliasMap(modules={"time": "time", "uuid": "uuid", "os": "os",
                               "datetime": "datetime", "json": "json"})
    if isinstance(node, ast.Call):
        fn = node.func
        # time.time() — qualified or aliased
        if isinstance(fn, ast.Attribute) and fn.attr == "time":
            recv = fn.value
            if isinstance(recv, ast.Name) and _resolve_module(recv.id, am) == "time":
                return ViolationKind.TIME_TIME
        if isinstance(fn, ast.Name):
            # Bare from-import forms.
            tup = am.bare_funcs.get(fn.id)
            if tup:
                mod, attr = tup
                if mod == "time" and attr == "time":
                    return ViolationKind.TIME_TIME
                if mod == "uuid" and attr == "uuid4":
                    return ViolationKind.UUID4
                if mod == "datetime" and attr == "datetime":
                    # `from datetime import datetime` — calling
                    # `datetime(...)` here would NOT be `now()`, but
                    # `datetime.now()` IS our concern; flagged via the
                    # Attribute branch below.
                    pass
                if mod == "os" and attr == "getenv":
                    return ViolationKind.OS_ENVIRON
        # uuid.uuid4() — qualified or aliased
        if isinstance(fn, ast.Attribute) and fn.attr == "uuid4":
            recv = fn.value
            if isinstance(recv, ast.Name) and _resolve_module(recv.id, am) == "uuid":
                return ViolationKind.UUID4
        # datetime.datetime.now() / datetime.datetime.utcnow() — qualified
        # path. Codex review on PR #134 round 6: `utcnow()` is just as
        # request-time-dependent as `now()` and must classify too.
        if isinstance(fn, ast.Attribute) and fn.attr in ("now", "utcnow"):
            mid = fn.value
            if isinstance(mid, ast.Attribute) and mid.attr == "datetime":
                top = mid.value
                if isinstance(top, ast.Name) and _resolve_module(top.id, am) == "datetime":
                    return ViolationKind.DATETIME_NOW
            # datetime.now() / datetime.utcnow() —
            # `from datetime import datetime; datetime.now()`
            if isinstance(mid, ast.Name):
                tup = am.bare_attrs.get(mid.id)
                if tup == ("datetime", "datetime"):
                    return ViolationKind.DATETIME_NOW
                if _resolve_module(mid.id, am) == "datetime":
                    return ViolationKind.DATETIME_NOW
        # os.getenv() — qualified or aliased
        if isinstance(fn, ast.Attribute) and fn.attr == "getenv":
            recv = fn.value
            if isinstance(recv, ast.Name) and _resolve_module(recv.id, am) == "os":
                return ViolationKind.OS_ENVIRON
        # json.dumps(...) without sort_keys=True
        if _is_unsorted_dumps(node, am):
            return ViolationKind.UNSORTED_DICT
        # Any read of os.environ via subscript / attribute / call (covers
        # .copy / .items / .keys / .values / .get).
        if _is_environ_chain(node, am):
            return ViolationKind.OS_ENVIRON
    if isinstance(node, (ast.Subscript, ast.Attribute, ast.Name)):
        if _is_environ_chain(node, am):
            return ViolationKind.OS_ENVIRON
    return None


# ── scope-shadow tracking (Codex review on PR #134) ───────────────────────
def _add_assignment_target(tgt: ast.AST, names: set[str]) -> None:
    """Collect names bound by an assignment target (Name / Tuple / List /
    Starred). Attribute / Subscript targets don't bind new names."""
    if isinstance(tgt, ast.Name):
        names.add(tgt.id)
    elif isinstance(tgt, (ast.Tuple, ast.List)):
        for elt in tgt.elts:
            _add_assignment_target(elt, names)
    elif isinstance(tgt, ast.Starred):
        _add_assignment_target(tgt.value, names)


def _collect_function_locals(fn: ast.AST) -> set[str]:
    """Collect names bound LOCALLY in this function's scope (parameters
    + assignment targets + for / with / except / walrus targets),
    WITHOUT recursing into nested function or class scopes — those
    have their own scope. Used to detect when an inner reference
    SHADOWS a module-level import.

    Codex review on PR #134: `from time import time; def render(time):
    return time()` must NOT classify the bare `time()` as `time.time` —
    the parameter shadows the import.

    Codex review on PR #134 round 5: `global x` / `nonlocal x` declarations
    make the name NOT-local even if it's assigned to inside the function.
    Names declared with `global` / `nonlocal` are removed from the
    collected set so the global/enclosing binding (typically an import)
    still classifies."""
    names: set[str] = set()
    nonlocal_names: set[str] = set()
    if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        args = fn.args
        for a in args.posonlyargs + args.args + args.kwonlyargs:
            names.add(a.arg)
        if args.vararg:
            names.add(args.vararg.arg)
        if args.kwarg:
            names.add(args.kwarg.arg)

    class _LocalCollector(ast.NodeVisitor):
        def visit_Global(self, node: ast.Global) -> None:                  # noqa: N802
            for n in node.names:
                nonlocal_names.add(n)

        def visit_Nonlocal(self, node: ast.Nonlocal) -> None:              # noqa: N802
            for n in node.names:
                nonlocal_names.add(n)

        def visit_Assign(self, node: ast.Assign) -> None:                  # noqa: N802
            for tgt in node.targets:
                _add_assignment_target(tgt, names)
            self.generic_visit(node)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:            # noqa: N802
            _add_assignment_target(node.target, names)
            self.generic_visit(node)

        def visit_AugAssign(self, node: ast.AugAssign) -> None:            # noqa: N802
            _add_assignment_target(node.target, names)
            self.generic_visit(node)

        def visit_NamedExpr(self, node: ast.NamedExpr) -> None:            # noqa: N802
            _add_assignment_target(node.target, names)
            self.generic_visit(node)

        def visit_For(self, node: ast.For) -> None:                        # noqa: N802
            _add_assignment_target(node.target, names)
            self.generic_visit(node)

        visit_AsyncFor = visit_For

        def visit_With(self, node: ast.With) -> None:                      # noqa: N802
            for item in node.items:
                if item.optional_vars:
                    _add_assignment_target(item.optional_vars, names)
            self.generic_visit(node)

        visit_AsyncWith = visit_With

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:    # noqa: N802
            if node.name:
                names.add(node.name)
            self.generic_visit(node)

        # Do NOT recurse into nested scopes — those have their own
        # locals collected by their own _collect_function_locals call.
        # Comprehensions (List/Set/Dict/Generator) are scoped to the
        # comprehension itself in Python 3 (Codex review on PR #134
        # round 3) — their targets do NOT leak into the function
        # scope, so don't collect them here either.
        def visit_FunctionDef(self, _node: ast.FunctionDef) -> None:       # noqa: N802
            return

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Lambda(self, _node: ast.Lambda) -> None:                 # noqa: N802
            return

        def visit_ClassDef(self, _node: ast.ClassDef) -> None:             # noqa: N802
            return

        def visit_ListComp(self, _node: ast.ListComp) -> None:             # noqa: N802
            return

        def visit_SetComp(self, _node: ast.SetComp) -> None:               # noqa: N802
            return

        def visit_DictComp(self, _node: ast.DictComp) -> None:             # noqa: N802
            return

        def visit_GeneratorExp(self, _node: ast.GeneratorExp) -> None:     # noqa: N802
            return

    body: list[ast.AST]
    if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
        body = list(fn.body)
    elif isinstance(fn, ast.Lambda):
        body = [fn.body]
    else:                                                                  # ast.Module
        body = list(getattr(fn, "body", []))
    for stmt in body:
        _LocalCollector().visit(stmt)
    # global / nonlocal: the name is NOT local even if assigned to —
    # the global/enclosing binding (typically an import) still resolves.
    return names - nonlocal_names


def _collect_class_locals(cls: ast.ClassDef) -> set[str]:
    """Collect names bound at the CLASS body level (top-level assignments
    + nested FunctionDef / ClassDef names). Used by `_ScopedAuditor` to
    shadow imports for subsequent class-body expressions
    (`from time import time; class C: time = lambda: 1; x = time()`).

    Codex review on PR #134 round 5: this case was previously reported
    as TIME_TIME even though the class-body call resolves to the
    class-local binding."""
    names: set[str] = set()
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign):
            for tgt in stmt.targets:
                _add_assignment_target(tgt, names)
        elif isinstance(stmt, (ast.AnnAssign, ast.AugAssign)):
            _add_assignment_target(stmt.target, names)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef,
                                ast.ClassDef)):
            names.add(stmt.name)
    return names


def _module_has_future_annotations(tree: ast.Module) -> bool:
    """True when the module declares `from __future__ import annotations`.

    Codex review on PR #134 round 5: with PEP 563 active, parameter
    annotations + return annotation are STRINGS (not evaluated at
    def-time), so the auditor must NOT walk them in the enclosing
    scope — they don't run."""
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module == "__future__":
            for alias in stmt.names:
                if alias.name == "annotations":
                    return True
    return False


def _top_name(node: ast.AST) -> str | None:
    """Return the top-level Name id used by `node` (the receiver of an
    attribute / subscript / call chain), for shadowing detection.
    Returns None when the chain doesn't bottom out at a Name (e.g.
    method-chains starting from a literal or a Call)."""
    if isinstance(node, ast.Call):
        return _top_name(node.func)
    if isinstance(node, ast.Attribute):
        return _top_name(node.value)
    if isinstance(node, ast.Subscript):
        return _top_name(node.value)
    if isinstance(node, ast.Name):
        return node.id
    return None


class _ScopedAuditor(ast.NodeVisitor):
    """AST walk that classifies prefix-poison call sites WHILE tracking
    function-scope shadowing. When the receiver name of a node is bound
    locally in an enclosing function scope (parameter / local
    assignment / for-target / with-as / except-as / comprehension
    target), the node's classification is SUPPRESSED — the local mask
    the import alias."""

    def __init__(self, am: AliasMap, path: str,
                  future_annotations: bool = False) -> None:
        self.am = am
        self.path = path
        # Each scope is (kind, names). kind ∈ {"function", "comp", "class"}.
        # function + comp scopes shadow visible from inside; class scopes
        # only shadow when the call is in the class body (i.e. no
        # function/comp scope is between us and the class — Python
        # class-body semantics: methods can't see class attrs by name).
        self.scopes: list[tuple[str, set[str]]] = []
        # `from __future__ import annotations` (PEP 563) — when True,
        # parameter + return annotations are STRINGS at runtime, NOT
        # evaluated at def-time. The auditor must skip them then.
        self.future_annotations = future_annotations
        # Codex review on PR #134 round 6: write-target depth. When > 0
        # we're inside the LHS of an assignment / del; nodes here are
        # writes, not reads, and must not classify. Without this,
        # `os.environ['TZ'] = 'UTC'` flags the inner `os.environ`
        # Attribute (it's Load ctx because the dict ref is loaded to be
        # subscripted-for-store).
        self._in_write_target = 0
        self.violations: list[PrefixViolation] = []
        self.seen: set[tuple[int, int]] = set()

    def _enter(self, kind: str, locals_: set[str]) -> None:
        self.scopes.append((kind, locals_))

    def _exit(self) -> None:
        self.scopes.pop()

    def _is_shadowed(self, name: str | None) -> bool:
        if name is None:
            return False
        # Walk scopes from innermost to outermost.
        # - function / comp scope: name shadows if it's there.
        # - class scope: only shadows when we HAVEN'T crossed a
        #   function/comp scope yet (Codex review on PR #134 round 5
        #   — class-body expressions see class-local bindings, but
        #   nested methods don't).
        crossed_function = False
        for kind, scope in reversed(self.scopes):
            if kind in ("function", "comp"):
                if name in scope:
                    return True
                crossed_function = True
            else:                                                  # "class"
                if not crossed_function and name in scope:
                    return True
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:            # noqa: N802
        # Defaults + decorators + annotations evaluate in the ENCLOSING
        # scope, BEFORE parameters are bound (Codex review on PR #134
        # round 3 + round 4):
        #   `import time; def f(now=time.time()): ...` — default runs
        #   at def-time in the module scope (round 3).
        #   `def build(x: time.time()): ...` — parameter annotations
        #   also run at def-time (round 4), UNLESS `from __future__
        #   import annotations` is active (round 5: PEP 563 makes
        #   annotations strings, not evaluated).
        # Visit defaults / decorators / annotations BEFORE entering the
        # function scope; manually walk the body to avoid generic_visit
        # double-walking them.
        for default in node.args.defaults:
            self.visit(default)
        for default in node.args.kw_defaults:
            if default is not None:
                self.visit(default)
        for dec in node.decorator_list:
            self.visit(dec)
        if not self.future_annotations:
            if node.returns is not None:
                self.visit(node.returns)
            # Parameter annotations on every arg family.
            for arg in (list(node.args.posonlyargs) + list(node.args.args)
                        + list(node.args.kwonlyargs)):
                if arg.annotation is not None:
                    self.visit(arg.annotation)
            if (node.args.vararg is not None
                    and node.args.vararg.annotation is not None):
                self.visit(node.args.vararg.annotation)
            if (node.args.kwarg is not None
                    and node.args.kwarg.annotation is not None):
                self.visit(node.args.kwarg.annotation)
        self._enter("function", _collect_function_locals(node))
        for stmt in node.body:
            self.visit(stmt)
        self._exit()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node: ast.Lambda) -> None:                      # noqa: N802
        # Lambda defaults also evaluate in the enclosing scope.
        for default in node.args.defaults:
            self.visit(default)
        for default in node.args.kw_defaults:
            if default is not None:
                self.visit(default)
        self._enter("function", _collect_function_locals(node))
        self.visit(node.body)
        self._exit()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:                  # noqa: N802
        # Decorators + bases + keyword args evaluate in the ENCLOSING
        # scope BEFORE the class body. Codex review on PR #134 round 5:
        # the class body itself is its own scope — assignments shadow
        # imports for SUBSEQUENT class-body expressions
        # (`from time import time; class C: time = lambda:1; x = time()`).
        # Codex review on PR #134 round 6: walk statements SEQUENTIALLY,
        # adding bindings to the class scope as we go — so a CALL that
        # appears BEFORE its same-name assignment still resolves to the
        # import (`from time import time; class C: x = time(); time =
        # lambda:1` → `x = time()` MUST classify).
        for dec in node.decorator_list:
            self.visit(dec)
        for base in node.bases:
            self.visit(base)
        for kw in node.keywords:
            self.visit(kw.value)
        cls_names: set[str] = set()
        self._enter("class", cls_names)
        for stmt in node.body:
            self.visit(stmt)
            # Add this stmt's bindings AFTER visiting it, so subsequent
            # statements see them but THIS statement doesn't.
            self._absorb_class_stmt_bindings(stmt, cls_names)
        self._exit()

    def _absorb_class_stmt_bindings(self, stmt: ast.AST,
                                     names: set[str]) -> None:
        """Pull name bindings produced by `stmt` into the class-scope
        `names` set so subsequent class-body statements see them."""
        if isinstance(stmt, ast.Assign):
            for tgt in stmt.targets:
                _add_assignment_target(tgt, names)
        elif isinstance(stmt, (ast.AnnAssign, ast.AugAssign)):
            _add_assignment_target(stmt.target, names)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef,
                                ast.ClassDef)):
            names.add(stmt.name)

    def _inside_function(self) -> bool:
        """True when at least one enclosing scope is a function (or
        comprehension — same semantics for AnnAssign annotation
        evaluation: not stored in __annotations__, never evaluated at
        runtime)."""
        return any(kind in ("function", "comp") for kind, _ in self.scopes)

    def visit_Assign(self, node: ast.Assign) -> None:                      # noqa: N802
        # Codex review on PR #134 round 6: visit RHS in load context,
        # LHS targets in write context. The write-target flag suppresses
        # classification of nodes inside assignment targets so
        # write-only env init (`os.environ['TZ'] = 'UTC'`) doesn't flag.
        self.visit(node.value)
        self._in_write_target += 1
        for tgt in node.targets:
            self.visit(tgt)
        self._in_write_target -= 1

    def visit_AugAssign(self, node: ast.AugAssign) -> None:                # noqa: N802
        self.visit(node.value)
        self._in_write_target += 1
        self.visit(node.target)
        self._in_write_target -= 1

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:                # noqa: N802
        # Value first, in load context.
        if node.value is not None:
            self.visit(node.value)
        # Codex review on PR #134 round 6: local-variable annotations
        # inside FUNCTIONS are NOT evaluated at runtime (Python 3 only
        # stores annotations in module/class `__annotations__`, never
        # on locals). Skip the annotation visit inside function scope.
        if not self._inside_function():
            self.visit(node.annotation)
        self._in_write_target += 1
        self.visit(node.target)
        self._in_write_target -= 1

    def visit_Delete(self, node: ast.Delete) -> None:                      # noqa: N802
        self._in_write_target += 1
        for tgt in node.targets:
            self.visit(tgt)
        self._in_write_target -= 1

    def _visit_comprehension(self, node: ast.AST,
                              generators: list[ast.comprehension],
                              parts: list[ast.AST]) -> None:
        """Comprehensions (List/Set/Dict/Generator) have their OWN scope
        in Python 3 (Codex review on PR #134 round 3). The first
        generator's `iter` is evaluated in the ENCLOSING scope; every
        subsequent `iter`, every `if` clause, and the element / key /
        value expressions evaluate inside the comprehension scope with
        all generator targets bound."""
        if not generators:
            return
        # First generator's iter evaluates in the enclosing scope.
        self.visit(generators[0].iter)
        names: set[str] = set()
        for gen in generators:
            _add_assignment_target(gen.target, names)
        self._enter("comp", names)
        # Subsequent generators' iters + every generator's ifs are in
        # the comp scope.
        for i, gen in enumerate(generators):
            if i > 0:
                self.visit(gen.iter)
            for cond in gen.ifs:
                self.visit(cond)
        for part in parts:
            self.visit(part)
        self._exit()

    def visit_ListComp(self, node: ast.ListComp) -> None:                  # noqa: N802
        self._visit_comprehension(node, node.generators, [node.elt])

    def visit_SetComp(self, node: ast.SetComp) -> None:                    # noqa: N802
        self._visit_comprehension(node, node.generators, [node.elt])

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:          # noqa: N802
        self._visit_comprehension(node, node.generators, [node.elt])

    def visit_DictComp(self, node: ast.DictComp) -> None:                  # noqa: N802
        self._visit_comprehension(node, node.generators, [node.key, node.value])

    def visit_Call(self, node: ast.Call) -> None:                          # noqa: N802
        self._maybe_record(node)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:                # noqa: N802
        self._maybe_record(node)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:                # noqa: N802
        self._maybe_record(node)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:                          # noqa: N802
        # Only Name nodes that resolve via the alias map (e.g. bare
        # `environ` from `from os import environ`) classify; everything
        # else short-circuits inside `classify_call`.
        self._maybe_record(node)
        self.generic_visit(node)

    def _maybe_record(self, node: ast.AST) -> None:
        # Codex review on PR #134 round 6: nodes inside an assignment
        # target are WRITES, not reads — don't classify them.
        if self._in_write_target > 0:
            return
        if self._is_shadowed(_top_name(node)):
            return
        kind = classify_call(node, self.am)
        if kind is None:
            return
        # De-dup: outer Call may wrap an inner Attribute that BOTH match
        # (e.g. `os.environ.get(...)` is both a Call AND walks an
        # Attribute on os.environ). Pin by (line, col).
        key = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
        if key in self.seen:
            return
        self.seen.add(key)
        self.violations.append(PrefixViolation(
            loc=FileLoc(path=self.path, line=getattr(node, "lineno", 0)),
            kind=kind,
        ))


def audit_source(src: str, path: str) -> list[PrefixViolation]:
    """Walk one source file's AST; return every prefix-poison call site.

    Builds the per-file alias map first so import aliases
    (`import time as t`, `from uuid import uuid4 as make_id`) resolve
    against canonical names. Tracks function-scope shadowing so a
    parameter or local that masks an import doesn't falsely classify
    (Codex review on PR #134). Malformed Python yields an empty list."""
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError:
        return []
    am = _build_alias_map(tree)
    future_annotations = _module_has_future_annotations(tree)
    auditor = _ScopedAuditor(am, path, future_annotations=future_annotations)
    auditor.visit(tree)
    return auditor.violations


class PrefixAuditError(Exception):
    """Raised by `audit_tree` when the configured root does not exist —
    Codex review on PR #134: silently treating a missing root as an
    empty directory disabled the Slice 2.2 gate on a typo'd path."""


def audit_tree(root: Path) -> PrefixReport:
    """Walk every `*.py` under `root` (or `root` itself if it's a file);
    aggregate violations into a `PrefixReport`. Sorted by `(path, line)`
    for deterministic output (Spec 149 idempotence).

    Raises `PrefixAuditError` when the configured `root` does not exist
    so a misspelled path or a generated path that moved doesn't silently
    disable the audit."""
    root = Path(root)
    if not root.exists():
        raise PrefixAuditError(
            f"audit root does not exist: {root!s} — fix the path or "
            f"create the file/directory before running the lint")
    rep = PrefixReport()
    if root.is_file():
        paths = [root]
    else:
        paths = sorted(p for p in root.rglob("*.py")
                       if "__pycache__" not in p.parts)
    for py in paths:
        rep.total_files += 1
        try:
            src = py.read_text(encoding="utf-8")
        except OSError:
            continue
        rep.violations.extend(audit_source(src, path=str(py)))
    rep.violations.sort(key=lambda v: (v.loc.path, v.loc.line))
    return rep


# ── Slice 2.2: baseline + regression gate ────────────────────────────────
@dataclass(frozen=True)
class BaselineEntry:
    """One known-historical violation site. The baseline file at
    `Plan/_planning/prefix-lint-baseline.txt` enumerates these so the
    Slice 2.2 gate flags REGRESSIONS only (Spec 054 drift pattern)."""

    path: str
    line: int
    kind: ViolationKind


@dataclass
class RegressionReport:
    """The Slice 2.2 gate payload. `ok` flips False on ANY
    new_violation; fixed_violations are surfaced so the author can
    trim the baseline."""

    new_violations: list[PrefixViolation] = field(default_factory=list)
    fixed_violations: list[BaselineEntry] = field(default_factory=list)
    ok: bool = True


def load_baseline(path: Path) -> set[BaselineEntry]:
    """Parse `<path>:<line>:<kind>` lines into a set of BaselineEntry.
    Blank lines + `#`-prefixed comments are skipped. A malformed line
    raises ValueError — fail loud so a typo doesn't silently bypass
    the gate."""
    path = Path(path)
    if not path.exists():
        return set()
    out: set[BaselineEntry] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.rsplit(":", 2)
        if len(parts) != 3:
            raise ValueError(
                f"baseline line must be `<path>:<line>:<kind>`; got {raw!r}")
        p, ln, kind = parts
        try:
            ln_i = int(ln)
        except ValueError as e:
            raise ValueError(
                f"baseline line number must be int; got {raw!r}") from e
        try:
            kind_v = ViolationKind(kind)
        except ValueError as e:
            raise ValueError(
                f"baseline kind unknown; got {raw!r}") from e
        out.add(BaselineEntry(path=p, line=ln_i, kind=kind_v))
    return out


def compare_to_baseline(rep: PrefixReport,
                         baseline: set[BaselineEntry]) -> RegressionReport:
    """Compare live violations to baseline as a MULTISET keyed by
    `(path, kind)`. Line numbers shift on every refactor, so pinning
    them produced false regressions; counting violations per (path,
    kind) catches REAL new sites without flapping on line shifts.

    new_violations: live count exceeds baseline count for some
    `(path, kind)` — the surplus sites are surfaced (first N from
    sorted order).
    fixed_violations: baseline count exceeds live — surplus baseline
    entries marked fixed so the author trims them.
    """
    from collections import Counter
    live_counter: Counter = Counter((v.loc.path, v.kind) for v in rep.violations)
    base_counter: Counter = Counter((b.path, b.kind) for b in baseline)
    new_violations: list[PrefixViolation] = []
    fixed_violations: list[BaselineEntry] = []
    for key in sorted(set(live_counter) | set(base_counter),
                       key=lambda k: (k[0], k[1].value)):
        live_n = live_counter[key]
        base_n = base_counter[key]
        if live_n > base_n:
            extras = sorted(
                (v for v in rep.violations
                 if (v.loc.path, v.kind) == key),
                key=lambda v: v.loc.line)[: live_n - base_n]
            new_violations.extend(extras)
        elif base_n > live_n:
            extras = sorted(
                (b for b in baseline if (b.path, b.kind) == key),
                key=lambda b: b.line)[: base_n - live_n]
            fixed_violations.extend(extras)
    return RegressionReport(
        new_violations=new_violations,
        fixed_violations=fixed_violations,
        ok=(len(new_violations) == 0),
    )


# ── CLI entry ─────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", default="agency/_envelope.py",
                        help="file or directory to audit (default: "
                             "agency/_envelope.py — the prefix builder)")
    parser.add_argument("--baseline", default=None,
                        help="path to baseline file enumerating known "
                             "historical violations (Spec 146 Slice 2.2 "
                             "drift gate); only regressions exit 1")
    parser.add_argument("--strict", action="store_true",
                        help="promote to gate: with --baseline, exit 1 on "
                             "regressions; without, exit 1 on any violation")
    args = parser.parse_args(argv)
    rep = audit_tree(Path(args.root))
    print(f"prefix lint: {len(rep.violations)} violations across "
          f"{rep.total_files} files")
    for v in rep.violations[:30]:
        print(f"  {v.loc.path}:{v.loc.line}  {v.kind.value}")
    if len(rep.violations) > 30:
        print(f"  ... and {len(rep.violations) - 30} more")
    if args.strict:
        if args.baseline is not None:
            baseline = load_baseline(Path(args.baseline))
            res = compare_to_baseline(rep, baseline)
            if res.new_violations:
                print(f"\nREGRESSION: {len(res.new_violations)} new "
                      f"violations not in baseline:")
                for v in res.new_violations:
                    print(f"  + {v.loc.path}:{v.loc.line}  {v.kind.value}")
            if res.fixed_violations:
                print(f"\nFIXED: {len(res.fixed_violations)} baseline "
                      f"entries no longer present — trim from "
                      f"{args.baseline}:")
                for b in res.fixed_violations:
                    print(f"  - {b.path}:{b.line}  {b.kind.value}")
            return 0 if res.ok else 1
        return 0 if not rep.violations else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
