"""Spec 042 — analyze.quality axis (decidable lint rules only).

Rules shipped (v1):
  Q001 — unused-import (warn). AST-based: imported name never read.
  Q002 — long-line (warn). Line length > 100 chars.
  Q003 — long-function (warn). Function body > 80 LOC.
  Q004 — long-file (warn). File LOC > 500.

NO taste-judgement ("name is unclear" → not shipped per Spec 042
§"Why decidable-only").
"""
from __future__ import annotations

import ast
import os

from ._findings import Finding, make_finding
from ._walk import python_files as _python_files, read_text as _read


# Severity assignments pinned per rule-id (Spec 042 §"Severity-
# assignment rule per axis"). v1: all quality rules are warn-severity
# until cyclomatic >20 / build-blocker variants ship.
SEVERITY: dict[str, str] = {
    "Q001": "warn",
    "Q002": "warn",
    "Q003": "warn",
    "Q004": "warn",
}

_LINE_LIMIT = 100
_FUNC_LOC_LIMIT = 80
_FILE_LOC_LIMIT = 500


# ---------------------------------------------------------------------------
# Q001 — unused-import (AST).
# ---------------------------------------------------------------------------


def _imported_names(tree: ast.AST) -> list[tuple[str, int, str]]:
    """Return [(local_name, lineno, evidence), ...] for every top-level
    import. ``from __future__ import …`` is skipped — those are
    compile-time directives, not name bindings."""
    out: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".")[0]
                out.append((local, node.lineno, f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "__future__":
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                out.append((local, node.lineno,
                            f"from {module} import {alias.name}"))
    return out


def _exported_names(tree: ast.AST) -> set[str]:
    """Names listed in ``__all__ = [...]`` at module level — these are
    re-exports, so the imports backing them must be considered used."""
    exported: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            exported.add(elt.value)
    return exported


def _names_used(tree: ast.AST) -> set[str]:
    """Set of every Name.id read in the module (excluding the import
    statements themselves)."""
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            # the root of an attribute chain (`os.path.join` → `os`)
            base = node
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name):
                used.add(base.id)
    return used


def _check_unused_imports(path: str, src: str, tree: ast.AST) -> list[Finding]:
    out: list[Finding] = []
    used = _names_used(tree) | _exported_names(tree)
    for local, lineno, evidence in _imported_names(tree):
        if local not in used:
            out.append(make_finding(
                rule="Q001", severity=SEVERITY["Q001"],
                file=path, line=lineno,
                message=f"unused import: {local!r}",
                evidence=evidence,
            ))
    return out


# ---------------------------------------------------------------------------
# Q002 — long-line.
# ---------------------------------------------------------------------------


def _check_long_lines(path: str, src: str) -> list[Finding]:
    out: list[Finding] = []
    for i, line in enumerate(src.splitlines(), start=1):
        if len(line) > _LINE_LIMIT:
            out.append(make_finding(
                rule="Q002", severity=SEVERITY["Q002"],
                file=path, line=i,
                message=f"line length {len(line)} > {_LINE_LIMIT}",
                evidence=line.strip(),
            ))
    return out


# ---------------------------------------------------------------------------
# Q003 — long-function.
# ---------------------------------------------------------------------------


def _check_long_functions(path: str, src: str, tree: ast.AST) -> list[Finding]:
    out: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", None) or node.lineno
            loc = end - node.lineno + 1
            if loc > _FUNC_LOC_LIMIT:
                out.append(make_finding(
                    rule="Q003", severity=SEVERITY["Q003"],
                    file=path, line=node.lineno,
                    message=f"function {node.name!r} body {loc} LOC > {_FUNC_LOC_LIMIT}",
                    evidence=f"def {node.name}(...)",
                ))
    return out


# ---------------------------------------------------------------------------
# Q004 — long-file.
# ---------------------------------------------------------------------------


def _check_long_file(path: str, src: str) -> list[Finding]:
    loc = src.count("\n") + (0 if src.endswith("\n") else 1)
    if loc > _FILE_LOC_LIMIT:
        return [make_finding(
            rule="Q004", severity=SEVERITY["Q004"],
            file=path, line=1,
            message=f"file LOC {loc} > {_FILE_LOC_LIMIT}",
            evidence=os.path.basename(path),
        )]
    return []


# ---------------------------------------------------------------------------
# Entry point.
# ---------------------------------------------------------------------------


def scan(root: str) -> list[Finding]:
    """Walk ``root`` for .py files; return all Q-axis findings."""
    findings: list[Finding] = []
    for path in _python_files(root):
        src = _read(path)
        if src is None:
            continue
        findings.extend(_check_long_lines(path, src))
        findings.extend(_check_long_file(path, src))
        try:
            tree = ast.parse(src, filename=path)
        except SyntaxError:
            continue   # syntax errors aren't quality findings (Pylint/ruff handle)
        findings.extend(_check_unused_imports(path, src, tree))
        findings.extend(_check_long_functions(path, src, tree))
    return findings
