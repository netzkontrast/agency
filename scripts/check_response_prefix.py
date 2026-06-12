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
                bound = alias.asname or alias.name
                am.modules[bound] = alias.name
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
    """Recognize ANY read of os.environ — subscript, attribute access
    (.copy / .items / .keys / .values), call (.get), or being passed as
    an argument (e.g. `dict(os.environ)`). Codex review on PR #134:
    Subscript + .get were the only forms flagged before."""
    # `os.environ` (qualified) or `environ` (from-import) name match.
    def _names_environ(n: ast.AST) -> bool:
        if isinstance(n, ast.Attribute):
            return _attr_chain_is(n, "os", "environ", am)
        if isinstance(n, ast.Name):
            tup = am.bare_attrs.get(n.id)
            return tup == ("os", "environ")
        return False

    # Subscript: os.environ["X"] / environ["X"]
    if isinstance(node, ast.Subscript) and _names_environ(node.value):
        return True
    # Attribute access on os.environ (.copy / .items / .keys / .values / etc.)
    # Note: this matches `<environ>.<anything>` as a read; sufficient since
    # there's no write surface on `os.environ` we want to allow at prefix
    # build time.
    if isinstance(node, ast.Attribute) and _names_environ(node.value):
        return True
    return False


def _is_unsorted_dumps(node: ast.Call, am: AliasMap) -> bool:
    """`json.dumps(...)` without `sort_keys=True` — hash-order leak.
    Recognizes both `json.dumps` (canonical) and aliased forms."""
    fn = node.func
    # Qualified `json.dumps(...)`
    if isinstance(fn, ast.Attribute) and fn.attr == "dumps":
        recv = fn.value
        if isinstance(recv, ast.Name):
            canonical = _resolve_module(recv.id, am)
            if canonical == "json":
                return not _has_sort_keys_true(node)
    # Bare `dumps(...)` from `from json import dumps`
    if isinstance(fn, ast.Name):
        tup = am.bare_funcs.get(fn.id)
        if tup and tup[0] == "json" and tup[1] == "dumps":
            return not _has_sort_keys_true(node)
    return False


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
    if isinstance(node, (ast.Subscript, ast.Attribute)):
        if _is_environ_chain(node, am):
            return ViolationKind.OS_ENVIRON
    return None


def audit_source(src: str, path: str) -> list[PrefixViolation]:
    """Walk one source file's AST; return every prefix-poison call site.

    Builds the per-file alias map first so import aliases
    (`import time as t`, `from uuid import uuid4 as make_id`) resolve
    against canonical names. Malformed Python yields an empty list."""
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError:
        return []
    am = _build_alias_map(tree)
    out: list[PrefixViolation] = []
    seen: set[tuple[int, int]] = set()                             # de-dup nested matches
    for node in ast.walk(tree):
        kind = classify_call(node, am)
        if kind is None:
            continue
        # De-dup: outer Call may wrap an inner Attribute that BOTH match
        # (e.g. `os.environ.get(...)` is both a Call AND walks an
        # Attribute on os.environ). Pin by (line, col).
        key = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
        if key in seen:
            continue
        seen.add(key)
        out.append(PrefixViolation(
            loc=FileLoc(path=path, line=getattr(node, "lineno", 0)),
            kind=kind,
        ))
    return out


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
