"""Spec 042 — analyze.performance axis (AST-based decidable checks).

Rules shipped (v1):
  P001 — nested-loop on the same iterable (warn). Decidable O(n²)
         hint: `for x in items: for y in items: ...`.
  P002 — string += in a loop (info). The classic O(n²) string-concat
         antipattern; '.join()' is the fix.
  P003 — unbounded `while True` with no break / sleep / return (warn).

NO profiling-based judgements ("this loop is slow" without O(n²) proof
→ deferred; profiling is the answer, not lint).
"""
from __future__ import annotations

# Spec 057 — the rule prefixes this module's findings carry (axis registry).
AXIS_PREFIXES: dict[str, frozenset[str]] = {"performance": frozenset({"P"})}

import ast

from ._findings import Finding, make_finding
from ._walk import python_files as _python_files, read_text as _read


SEVERITY: dict[str, str] = {
    "P001": "warn",
    "P002": "info",
    "P003": "warn",
}


def _iter_target_name(node: ast.For) -> str | None:
    """The variable name of a `for x in iterable:` loop's iterable, if
    it is a simple Name."""
    if isinstance(node.iter, ast.Name):
        return node.iter.id
    return None


def _check_nested_loops(path: str, src: str, tree: ast.AST) -> list[Finding]:
    """P001 — outer/inner loop both iterate over the SAME name."""
    out: list[Finding] = []
    lines = src.splitlines()

    def _scoped_for_loops(node):
        """Yield every ast.For inside `node`'s body but stop descending
        into nested function/class scopes — those aren't runtime-nested
        loops, they're definitions (PR review round 9 r3...). Without
        this guard, a `for x in items: def helper(): for y in items: ...`
        triggers a false P001."""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                   ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(child, ast.For):
                yield child
            yield from _scoped_for_loops(child)

    for outer in ast.walk(tree):
        if not isinstance(outer, ast.For):
            continue
        outer_iter = _iter_target_name(outer)
        if outer_iter is None:
            continue
        for inner in _scoped_for_loops(outer):
            if inner is outer:
                continue
            inner_iter = _iter_target_name(inner)
            if inner_iter == outer_iter:
                evidence = (lines[inner.lineno - 1].strip()
                            if 0 <= inner.lineno - 1 < len(lines)
                            else "nested for")
                out.append(make_finding(
                    rule="P001", severity=SEVERITY["P001"],
                    file=path, line=inner.lineno,
                    message=f"nested loop on {outer_iter!r} — O(n²) in collection size",
                    evidence=evidence,
                ))
                break   # one finding per outer loop
    return out


def _string_typed_names_in_scope(body) -> set[str]:
    """Walk a function body / module body for `name = "..."` /
    `name: str = "..."` assignments and return the set of locally
    string-typed names. Only direct children (not nested function/class
    bodies) so a sibling function's `s = ''` doesn't pollute this
    scope's view."""
    names: set[str] = set()
    for node in body:
        if isinstance(node, ast.Assign):
            if (isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            if (isinstance(node.annotation, ast.Name)
                    and node.annotation.id == "str"
                    and isinstance(node.target, ast.Name)):
                names.add(node.target.id)
    return names


def _check_string_concat(path: str, src: str, tree: ast.AST) -> list[Finding]:
    """P002 — `x += y` inside a `for` body, where x was initialised as a
    string literal IN THE SAME SCOPE.

    Scope-aware: a string `s = ""` in function A does NOT taint an
    integer `s = 0; s += 1` in unrelated function B. Module-level
    string assignments still apply to loops at module level. Skip int
    counters (e.g. ``total += 1``) — those aren't the antipattern the
    rule targets.
    """
    out: list[Finding] = []
    lines = src.splitlines()

    def _scan_body(body, string_names: set[str]) -> None:
        # Recursively walk this body's loops + nested function defs;
        # nested defs get their own scope-local string-name set.
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                inner = _string_typed_names_in_scope(node.body)
                _scan_body(node.body, inner)
            elif isinstance(node, ast.ClassDef):
                _scan_body(node.body, _string_typed_names_in_scope(node.body))
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                # P002 fires on any loop shape — `for`/`async for`/`while`.
                # The O(n) string-concat antipattern is identical regardless.
                for stmt in ast.walk(node):
                    if stmt is node:
                        continue
                    if (isinstance(stmt, ast.AugAssign)
                            and isinstance(stmt.op, ast.Add)
                            and isinstance(stmt.target, ast.Name)
                            and stmt.target.id in string_names):
                        evidence = (lines[stmt.lineno - 1].strip()
                                    if 0 <= stmt.lineno - 1 < len(lines)
                                    else "+= in loop")
                        out.append(make_finding(
                            rule="P002", severity=SEVERITY["P002"],
                            file=path, line=stmt.lineno,
                            message="`+=` on a string in loop — use "
                                    "''.join() / list.append() for O(n)",
                            evidence=evidence,
                        ))
                        break
            elif hasattr(node, "body") and isinstance(getattr(node, "body", None), list):
                # if/while/try/with — same scope; reuse the string_names set.
                _scan_body(node.body, string_names)

    _scan_body(tree.body, _string_typed_names_in_scope(tree.body))
    return out


def _check_unbounded_while(path: str, src: str, tree: ast.AST) -> list[Finding]:
    """P003 — `while True:` with no break / return / sleep / raise in body."""
    out: list[Finding] = []
    lines = src.splitlines()
    for node in ast.walk(tree):
        if not isinstance(node, ast.While):
            continue
        # Detect `while True:`. Python 3.8+ unifies bool literals
        # under ast.Constant; we don't support older runtimes.
        test = node.test
        if not (isinstance(test, ast.Constant) and test.value is True):
            continue
        # Check body for any break / return / raise / sleep / yield —
        # but ONLY at this `while`'s lexical scope, not nested inside an
        # inner loop or function (PR review: `while True: for x in xs:
        # break` — the `break` exits the inner `for`, not the outer
        # `while`).
        def _scope_exits(stmts) -> bool:
            for n in stmts:
                if isinstance(n, ast.Break):
                    return True   # `break` here DOES terminate this while
                if isinstance(n, ast.Return):
                    return True   # return walks the call stack out
                if isinstance(n, ast.Raise):
                    return True   # ditto
                if isinstance(n, ast.Yield):
                    return True
                # A bare ``sleep(...)`` at this scope is wrapped in
                # ast.Expr (statement) not ast.Call (expression node).
                # Inspect Expr.value to catch the common ``time.sleep(1)``
                # backoff pattern (PR review round 7 r3343808276).
                call_node = None
                if isinstance(n, ast.Call):
                    call_node = n
                elif isinstance(n, ast.Expr) and isinstance(n.value, ast.Call):
                    call_node = n.value
                if call_node is not None:
                    func = call_node.func
                    fn_name = (func.id if isinstance(func, ast.Name)
                               else (func.attr if isinstance(func, ast.Attribute) else None))
                    if fn_name == "sleep":
                        return True
                # Nested loops + nested function defs CANNOT terminate
                # the outer `while` — skip into their bodies for `Return`/
                # `Raise` (which DO walk out) but ignore `Break`s.
                if isinstance(n, (ast.For, ast.AsyncFor, ast.While)):
                    # Look only for Return / Raise / Yield / sleep inside
                    # nested loops — Break inside the nested loop is not
                    # an outer-while exit.
                    for inner in ast.walk(n):
                        if isinstance(inner, (ast.Return, ast.Raise, ast.Yield)):
                            return True
                        if isinstance(inner, ast.Call):
                            func = inner.func
                            fn_name = (func.id if isinstance(func, ast.Name)
                                       else (func.attr if isinstance(func, ast.Attribute) else None))
                            if fn_name == "sleep":
                                return True
                elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Nested function defs cannot exit the enclosing
                    # `while` — skip them entirely.
                    continue
                # if / try / with — recurse into their direct bodies.
                elif hasattr(n, "body") and isinstance(getattr(n, "body", None), list):
                    if _scope_exits(n.body):
                        return True
                # if/try also has orelse, finalbody, handlers.
                for branch_attr in ("orelse", "finalbody"):
                    branch = getattr(n, branch_attr, None)
                    if isinstance(branch, list) and _scope_exits(branch):
                        return True
                handlers = getattr(n, "handlers", None)
                if handlers:
                    for h in handlers:
                        if _scope_exits(h.body):
                            return True
            return False

        has_exit = _scope_exits(node.body)
        if not has_exit:
            evidence = (lines[node.lineno - 1].strip()
                        if 0 <= node.lineno - 1 < len(lines) else "while True:")
            out.append(make_finding(
                rule="P003", severity=SEVERITY["P003"],
                file=path, line=node.lineno,
                message="`while True:` with no break / return / sleep",
                evidence=evidence,
            ))
    return out


def scan(root: str) -> list[Finding]:
    findings: list[Finding] = []
    for path in _python_files(root):
        src = _read(path)
        if src is None:
            continue
        try:
            tree = ast.parse(src, filename=path)
        except SyntaxError:
            continue
        findings.extend(_check_nested_loops(path, src, tree))
        findings.extend(_check_string_concat(path, src, tree))
        findings.extend(_check_unbounded_while(path, src, tree))
    return findings
