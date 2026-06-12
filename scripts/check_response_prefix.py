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
    OS_ENVIRON = "os_environ"          # os.environ[...] / os.environ.get / os.getenv


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
def _is_attr_call(node: ast.Call, owner: str, attr: str) -> bool:
    """Match `<owner>.<attr>(...)` — e.g. `time.time()`. Used for the
    fully-qualified-module-form calls."""
    fn = node.func
    if not isinstance(fn, ast.Attribute) or fn.attr != attr:
        return False
    receiver = fn.value
    if isinstance(receiver, ast.Name) and receiver.id == owner:
        return True
    return False


def _is_double_attr_call(node: ast.Call, top: str, mid: str, leaf: str) -> bool:
    """Match `<top>.<mid>.<leaf>(...)` — e.g. `datetime.datetime.now()`."""
    fn = node.func
    if not isinstance(fn, ast.Attribute) or fn.attr != leaf:
        return False
    mid_attr = fn.value
    if not isinstance(mid_attr, ast.Attribute) or mid_attr.attr != mid:
        return False
    top_name = mid_attr.value
    return isinstance(top_name, ast.Name) and top_name.id == top


def _is_bare_call(node: ast.Call, name: str) -> bool:
    """Match `<name>(...)` — the from-import form (e.g. `uuid4()` after
    `from uuid import uuid4`)."""
    fn = node.func
    return isinstance(fn, ast.Name) and fn.id == name


def _is_environ_access(node: ast.AST) -> bool:
    """Match `os.environ[...]` (Subscript) or `os.environ.get(...)`."""
    if isinstance(node, ast.Subscript):
        base = node.value
        if isinstance(base, ast.Attribute) and base.attr == "environ" \
                and isinstance(base.value, ast.Name) and base.value.id == "os":
            return True
    if isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Attribute) and fn.attr == "get":
            recv = fn.value
            if isinstance(recv, ast.Attribute) and recv.attr == "environ" \
                    and isinstance(recv.value, ast.Name) and recv.value.id == "os":
                return True
    return False


def _is_os_getenv(node: ast.Call) -> bool:
    """Match `os.getenv(...)`."""
    return _is_attr_call(node, "os", "getenv")


def classify_call(node: ast.AST) -> ViolationKind | None:
    """Return the `ViolationKind` if `node` is a known prefix-poison
    call site; else None."""
    if isinstance(node, ast.Call):
        if _is_attr_call(node, "time", "time"):
            return ViolationKind.TIME_TIME
        if _is_attr_call(node, "uuid", "uuid4") or _is_bare_call(node, "uuid4"):
            return ViolationKind.UUID4
        if _is_double_attr_call(node, "datetime", "datetime", "now") \
                or _is_attr_call(node, "datetime", "now"):
            return ViolationKind.DATETIME_NOW
        if _is_os_getenv(node):
            return ViolationKind.OS_ENVIRON
        # os.environ.get(...) is a Call whose receiver chain hits environ
        if _is_environ_access(node):
            return ViolationKind.OS_ENVIRON
    if isinstance(node, ast.Subscript):
        if _is_environ_access(node):
            return ViolationKind.OS_ENVIRON
    return None


def audit_source(src: str, path: str) -> list[PrefixViolation]:
    """Walk one source file's AST; return every prefix-poison call site.

    Malformed Python yields an empty list (the audit is conservative —
    parse errors are surfaced elsewhere, not here)."""
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError:
        return []
    out: list[PrefixViolation] = []
    for node in ast.walk(tree):
        kind = classify_call(node)
        if kind is None:
            continue
        out.append(PrefixViolation(
            loc=FileLoc(path=path, line=getattr(node, "lineno", 0)),
            kind=kind,
        ))
    return out


def audit_tree(root: Path) -> PrefixReport:
    """Walk every `*.py` under `root` (or `root` itself if it's a file);
    aggregate violations into a `PrefixReport`. Sorted by `(path, line)`
    for deterministic output (Spec 149 idempotence)."""
    root = Path(root)
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
