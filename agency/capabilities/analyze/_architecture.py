"""Spec 042 — analyze.architecture axis (dependency graph + structural).

Rules shipped (v1):
  A001 — circular import (fail). Detected by Tarjan's SCC on the
         file→imports graph.
  A002 — large file (warn). File LOC > 600.
  A003 — medium file (info). File LOC > 400 (Spec 042 thresholds).

NO project-context smells beyond cycles + LOC; package fan-in/fan-out
is computed but not surfaced as a finding in v1 (too noisy without
project-specific thresholds).
"""
from __future__ import annotations

# Spec 057 — the rule prefixes this module's findings carry (axis registry).
AXIS_PREFIXES: dict[str, frozenset[str]] = {"architecture": frozenset({"A"})}

import ast
import os

from ._findings import Finding, make_finding
from ._walk import python_files as _python_files, read_text as _read


SEVERITY: dict[str, str] = {
    "A001": "fail",
    "A002": "warn",
    "A003": "info",
}

_LARGE_LOC = 600
_MEDIUM_LOC = 400


# ---------------------------------------------------------------------------
# Import graph (file path → set of modules imported via `from . import X` /
# `from .X import Y`). Resolved to file paths within the scanned tree.
# ---------------------------------------------------------------------------


def _module_name(root: str, path: str) -> str:
    """Compute a dotted module name relative to ``root``."""
    rel = os.path.relpath(path, root)
    base, _ = os.path.splitext(rel)
    parts = base.split(os.sep)
    # Drop trailing __init__ — `pkg/__init__.py` IS `pkg`.
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _imports(tree: ast.AST, current_module: str,
             root_pkg: str = "", is_init: bool = False) -> set[str]:
    """Return the set of intra-tree module names this file imports.

    Resolves relative imports against ``current_module``:
      - ``from . import X``     → siblings of current_module
      - ``from .pkg import X``  → pkg + each alias as a submodule
      - ``from .. import X``    → walks up one package level

    Absolute imports inside the scanned tree (e.g. ``from agency.foo
    import bar``) are emitted in BOTH forms — unstripped (``agency.foo``,
    matching graph keys when the scan root is the package's parent) AND
    stripped (``foo``, matching keys when the scan root is the package
    itself). The SCC walker filters edges to in-graph modules so
    emitting both candidates is cheap and correct across both layouts.
    Pure-external absolutes (``import os``) fall through and are filtered
    out by the walker.
    """
    out: set[str] = set()
    pkg_parts = current_module.split(".") if current_module else []
    # The package containing this module = drop the trailing module name.
    # Exception: for ``pkg/__init__.py`` (`current_module='pkg'`), the
    # PACKAGE IS the current module, so `from . import x` resolves to
    # `pkg.x`, not `x`. Drop the trailing segment only for non-__init__
    # files.
    parent_pkg = pkg_parts if is_init else pkg_parts[:-1]

    def _emit_absolute(mod: str, alias_names: list[str]) -> None:
        if not mod:
            return
        out.add(mod)
        for n in alias_names:
            if n != "*":
                out.add(f"{mod}.{n}")
        # Also emit stripped variants (for the case where the scan root
        # IS the package — e.g. root='agency' makes graph keys 'foo'
        # rather than 'agency.foo').
        if root_pkg and mod == root_pkg:
            # PR review round 8 (r_root_pkg_absolute): `from agency
            # import foo` resolves the aliases (`foo`) themselves as
            # in-tree submodules when the scan root IS the package.
            for n in alias_names:
                if n != "*":
                    out.add(n)
        elif root_pkg and mod.startswith(root_pkg + "."):
            stripped = mod[len(root_pkg) + 1:]
            out.add(stripped)
            for n in alias_names:
                if n != "*":
                    out.add(f"{stripped}.{n}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # `import pkg.sub` → emit both unstripped + stripped (when
            # root_pkg-prefixed) so the walker matches against either
            # graph-key naming scheme.
            for alias in node.names:
                name = alias.name
                out.add(name)
                if root_pkg and name.startswith(root_pkg + "."):
                    out.add(name[len(root_pkg) + 1:])
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        level = node.level or 0
        if level == 0:
            # Absolute import — emit both unstripped + stripped variants.
            mod = node.module or ""
            _emit_absolute(mod, [a.name for a in node.names])
            continue
        # `level - 1` levels above parent_pkg gives the base for the
        # relative reference. `from . import X` (level=1) means siblings
        # of current_module → base = parent_pkg itself.
        steps_up = level - 1
        if steps_up > len(parent_pkg):
            continue       # walks above the scan root; ignore
        base = parent_pkg[:len(parent_pkg) - steps_up]
        if node.module:
            mod_parts = base + node.module.split(".")
            base_mod = ".".join(mod_parts)
            out.add(base_mod)
            # Each alias MAY be a submodule (e.g. `from .pkg import sub`
            # where sub is `pkg/sub.py`). Add both possibilities; the
            # SCC walker filters edges to modules outside the graph.
            for alias in node.names:
                if alias.name != "*":
                    out.add(".".join(mod_parts + [alias.name]))
        else:
            # `from . import X, Y` — each alias is a sibling/submodule.
            for alias in node.names:
                if alias.name != "*":
                    out.add(".".join(base + [alias.name]))
    return out


def _build_graph(root: str) -> tuple[dict[str, set[str]], dict[str, str]]:
    """Return (graph: module → imports, mod_to_path: module → file)."""
    graph: dict[str, set[str]] = {}
    mod_to_path: dict[str, str] = {}
    # The root package name lets _imports resolve absolute intra-tree
    # imports (e.g. `from agency.foo import bar`) against the same dotted
    # naming the SCC walker uses.
    root_pkg = os.path.basename(os.path.abspath(root.rstrip(os.sep)))
    for path in _python_files(root):
        src = _read(path)
        if src is None:
            continue
        try:
            tree = ast.parse(src, filename=path)
        except SyntaxError:
            continue
        mod = _module_name(root, path)
        mod_to_path[mod] = path
        is_init = os.path.basename(path) == "__init__.py"
        graph[mod] = _imports(tree, mod, root_pkg=root_pkg, is_init=is_init)
    return graph, mod_to_path


def _scc_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Tarjan's SCC; return every strongly-connected component with
    > 1 node (those are the cycles)."""
    index_counter = [0]
    stack: list[str] = []
    lowlinks: dict[str, int] = {}
    index: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    result: list[list[str]] = []

    def strongconnect(node: str) -> None:
        index[node] = index_counter[0]
        lowlinks[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)
        on_stack[node] = True
        for succ in graph.get(node, ()):
            if succ not in graph:
                continue       # ignore edges to nodes outside the scan
            if succ not in index:
                strongconnect(succ)
                lowlinks[node] = min(lowlinks[node], lowlinks[succ])
            elif on_stack.get(succ):
                lowlinks[node] = min(lowlinks[node], index[succ])
        if lowlinks[node] == index[node]:
            comp: list[str] = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                comp.append(w)
                if w == node:
                    break
            if len(comp) > 1:
                result.append(comp)

    for node in list(graph):
        if node not in index:
            strongconnect(node)
    return result


def _check_cycles(graph: dict[str, set[str]],
                  mod_to_path: dict[str, str]) -> list[Finding]:
    out: list[Finding] = []
    for cycle in _scc_cycles(graph):
        # Report ONE finding per cycle, anchored at the first module.
        anchor_mod = sorted(cycle)[0]
        anchor_path = mod_to_path.get(anchor_mod, "")
        if not anchor_path:
            continue
        out.append(make_finding(
            rule="A001", severity=SEVERITY["A001"],
            file=anchor_path, line=1,
            message=f"circular import: {' → '.join(sorted(cycle))} → ...",
            evidence=" ↔ ".join(sorted(cycle)),
        ))
    return out


def _check_file_size(path: str, src: str) -> list[Finding]:
    loc = src.count("\n") + (0 if src.endswith("\n") else 1)
    if loc > _LARGE_LOC:
        return [make_finding(
            rule="A002", severity=SEVERITY["A002"],
            file=path, line=1,
            message=f"file LOC {loc} > {_LARGE_LOC} — split by purpose (CLAUDE.md Rule #2)",
            evidence=os.path.basename(path),
        )]
    if loc > _MEDIUM_LOC:
        return [make_finding(
            rule="A003", severity=SEVERITY["A003"],
            file=path, line=1,
            message=f"file LOC {loc} > {_MEDIUM_LOC} — approaching split threshold",
            evidence=os.path.basename(path),
        )]
    return []


def scan(root: str) -> list[Finding]:
    findings: list[Finding] = []
    # Cycles run once over the import graph.
    graph, mod_to_path = _build_graph(root)
    findings.extend(_check_cycles(graph, mod_to_path))
    # Per-file size walks.
    for path in _python_files(root):
        src = _read(path)
        if src is None:
            continue
        findings.extend(_check_file_size(path, src))
    return findings
