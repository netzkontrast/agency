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


def _build_alias_map(tree: ast.Module) -> AliasMap:
    """Walk top-level Import / ImportFrom nodes; build the per-file
    alias map used by the classifier."""
    am = AliasMap()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    # `import os as o` → bind `o` to canonical `os`.
                    am.modules[alias.asname] = alias.name
                else:
                    # `import os.path` binds the TOP-LEVEL `os` per Python
                    # semantics (a later `os.environ` is resolved against
                    # that), not the dotted `os.path` string (Codex review
                    # on PR #134).
                    top = alias.name.split(".", 1)[0]
                    am.modules[top] = top
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                bound = alias.asname or alias.name
                # Track functions/values brought in via from-import
                # against their canonical module so the classifier can
                # match either form.
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


def _is_environ_chain(node: ast.AST, am: AliasMap) -> bool:
    """Recognize ANY read of os.environ — the bare attribute itself
    (e.g. `dict(os.environ)`), subscript (`os.environ["X"]`), attribute
    access (`.copy` / `.items` / `.keys` / `.values`), call (`.get`).
    Codex review on PR #134: bare reads passed as values were missed
    before (only Subscript + chained Attribute flagged)."""
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
        # datetime.datetime.now() — qualified path
        if isinstance(fn, ast.Attribute) and fn.attr == "now":
            mid = fn.value
            if isinstance(mid, ast.Attribute) and mid.attr == "datetime":
                top = mid.value
                if isinstance(top, ast.Name) and _resolve_module(top.id, am) == "datetime":
                    return ViolationKind.DATETIME_NOW
            # datetime.now() — `from datetime import datetime; datetime.now()`
            if isinstance(mid, ast.Name):
                tup = am.bare_attrs.get(mid.id)
                if tup == ("datetime", "datetime"):
                    return ViolationKind.DATETIME_NOW
                # qualified `datetime.now()` with `datetime` as the module
                # (rare but legitimate alias path):
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
    + assignment targets + for / with / except / walrus / comprehension
    targets), WITHOUT recursing into nested function or class scopes —
    those have their own scope. Used to detect when an inner reference
    SHADOWS a module-level import.

    Codex review on PR #134: `from time import time; def render(time):
    return time()` must NOT classify the bare `time()` as `time.time` —
    the parameter shadows the import."""
    names: set[str] = set()
    if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        args = fn.args
        for a in args.posonlyargs + args.args + args.kwonlyargs:
            names.add(a.arg)
        if args.vararg:
            names.add(args.vararg.arg)
        if args.kwarg:
            names.add(args.kwarg.arg)

    class _LocalCollector(ast.NodeVisitor):
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
    return names


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

    def __init__(self, am: AliasMap, path: str) -> None:
        self.am = am
        self.path = path
        # scopes[0] is the module scope; module-level imports are the
        # alias map's source of truth, so we don't track module-level
        # rebindings as shadowing. Inner scopes shadow the alias map.
        self.scopes: list[set[str]] = []
        self.violations: list[PrefixViolation] = []
        self.seen: set[tuple[int, int]] = set()

    def _enter(self, locals_: set[str]) -> None:
        self.scopes.append(locals_)

    def _exit(self) -> None:
        self.scopes.pop()

    def _is_shadowed(self, name: str | None) -> bool:
        if name is None:
            return False
        for scope in self.scopes:
            if name in scope:
                return True
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:            # noqa: N802
        # Defaults + decorators + annotations evaluate in the ENCLOSING
        # scope, BEFORE parameters are bound (Codex review on PR #134
        # round 3 + round 4):
        #   `import time; def f(now=time.time()): ...` — default runs
        #   at def-time in the module scope (round 3).
        #   `def build(x: time.time()): ...` — parameter annotations
        #   also run at def-time (round 4), unless `from __future__
        #   import annotations` is active (then they're strings and
        #   our AST sees the unevaluated expression as dead code; that
        #   case is rarer and harmless to flag).
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
        if node.returns is not None:
            self.visit(node.returns)
        # Parameter annotations on every arg family (positional / kwarg /
        # *args / **kwargs).
        for arg in (list(node.args.posonlyargs) + list(node.args.args)
                    + list(node.args.kwonlyargs)):
            if arg.annotation is not None:
                self.visit(arg.annotation)
        if node.args.vararg is not None and node.args.vararg.annotation is not None:
            self.visit(node.args.vararg.annotation)
        if node.args.kwarg is not None and node.args.kwarg.annotation is not None:
            self.visit(node.args.kwarg.annotation)
        self._enter(_collect_function_locals(node))
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
        self._enter(_collect_function_locals(node))
        self.visit(node.body)
        self._exit()

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
        self._enter(names)
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
    auditor = _ScopedAuditor(am, path)
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


# ── CLI entry ─────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", default="agency/_envelope.py",
                        help="file or directory to audit (default: "
                             "agency/_envelope.py — the prefix builder)")
    args = parser.parse_args(argv)
    rep = audit_tree(Path(args.root))
    print(f"prefix lint: {len(rep.violations)} violations across "
          f"{rep.total_files} files")
    for v in rep.violations[:30]:
        print(f"  {v.loc.path}:{v.loc.line}  {v.kind.value}")
    if len(rep.violations) > 30:
        print(f"  ... and {len(rep.violations) - 30} more")
    # Slice 2.1: informational. Slice 2.2 promotes to:
    #     return 0 if not rep.violations else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
