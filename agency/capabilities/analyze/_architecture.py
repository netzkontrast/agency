"""Spec 042 / Spec 051 — analyze.architecture axis (dependency graph + structural).

Rules shipped:
  A001 — circular import (fail). SCCs on the file→imports graph; the message
         renders the SHORTEST elementary cycle path (a → b → c → a).
  A002 — large file (warn). File LOC > 600.
  A003 — medium file (info). File LOC > 400 (Spec 042 thresholds).
  A004 — high fan-out (warn ≥ 8 / fail ≥ 15). A module imports too many
         intra-tree siblings — split into cohesive units (Spec 051).
  A005 — high fan-in (info ≥ 10). Many modules import this one — a core
         utility; surfaced, not a defect (Spec 051).
  A006 — god-module (warn). fan-in ≥ 10 AND fan-out ≥ 8 AND LOC ≥ 400 —
         the trifecta-of-smell (Spec 051).

networkx (Spec 051) backs the cycle enumeration when present (the canonical
`simple_cycles`); a pure-Python BFS is the always-available fallback. The
fan-in/out degree metrics are plain edge counting — no library needed.
"""
from __future__ import annotations

# Spec 057 — the rule prefixes this module's findings carry (axis registry).
AXIS_PREFIXES: dict[str, frozenset[str]] = {"architecture": frozenset({"A"})}

import ast
import importlib.util
import os
from collections import deque

from ._findings import Finding, make_finding
from ._walk import python_files as _python_files, read_text as _read

# networkx is a default dependency (Spec 051 / 2026-06-17 user directive); the
# find_spec guard keeps the pure-Python fallback honest if it is ever absent.
_HAS_NX = importlib.util.find_spec("networkx") is not None


SEVERITY: dict[str, str] = {
    "A001": "fail",
    "A002": "warn",
    "A003": "info",
    "A004": "warn",     # fail at ≥ _FANOUT_FAIL (set inline)
    "A005": "info",
    "A006": "warn",
}

_LARGE_LOC = 600
_MEDIUM_LOC = 400

# Tunable structural budgets (rule 8 — documented config, not a frozen snapshot;
# Open-Q 1 in Plan/051 flags these as heuristic v1 defaults pending measurement).
_FANOUT_WARN = 8
_FANOUT_FAIL = 15
_FANIN_INFO = 10
_GOD_LOC = 400


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


def _build_graph(root: str) -> tuple[dict[str, set[str]], dict[str, str], dict[str, str]]:
    """Return (graph: module → imports, mod_to_path: module → file,
    src_by_path: file → source). The source is returned so ``scan`` runs its
    size checks on the SAME read — no second walk/read of the tree."""
    graph: dict[str, set[str]] = {}
    mod_to_path: dict[str, str] = {}
    src_by_path: dict[str, str] = {}
    # The root package name lets _imports resolve absolute intra-tree
    # imports (e.g. `from agency.foo import bar`) against the same dotted
    # naming the SCC walker uses.
    root_pkg = os.path.basename(os.path.abspath(root.rstrip(os.sep)))
    for path in _python_files(root):
        src = _read(path)
        if src is None:
            continue
        src_by_path[path] = src
        try:
            tree = ast.parse(src, filename=path)
        except SyntaxError:
            continue       # unparseable — still size-checked via src_by_path
        mod = _module_name(root, path)
        mod_to_path[mod] = path
        is_init = os.path.basename(path) == "__init__.py"
        graph[mod] = _imports(tree, mod, root_pkg=root_pkg, is_init=is_init)
    return graph, mod_to_path, src_by_path


def _scc_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Strongly-connected components with > 1 node (those carry the cycles).

    Prefers networkx's battle-tested `strongly_connected_components` (Spec 051,
    polynomial — safe on dense graphs, unlike cycle enumeration); falls back to
    the hand-rolled Tarjan below when networkx is absent."""
    if _HAS_NX:
        import networkx as nx

        g = nx.DiGraph()
        g.add_nodes_from(graph)
        for node, succs in graph.items():
            for s in succs:
                if s in graph:
                    g.add_edge(node, s)
        return [sorted(c) for c in nx.strongly_connected_components(g)
                if len(c) > 1]
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


def _bfs_shortest_cycle(graph: dict[str, set[str]], scc: list[str]) -> list[str]:
    """Shortest elementary cycle within an SCC node set, as an ordered path that
    returns to its start (``[a, b, …, a]``).

    A TRUE shortest-cycle BFS over ``(node, predecessor)`` state — Codex review
    (#154): storing whole simple paths in the queue grows exponentially in a
    layered SCC before any cycle is found. This keeps only ``dist``/``pred``
    dicts (O(V) per start), so the whole search is O(V·(V+E)) — bounded.
    For each start it BFS-explores; the first edge back to ``start`` is the
    shortest cycle through that start (BFS visits in distance order); the global
    minimum over starts is the shortest cycle in the SCC."""
    nodes = set(scc)
    best: list[str] | None = None
    for start in sorted(nodes):
        pred: dict[str, str | None] = {start: None}
        dist: dict[str, int] = {start: 0}
        queue: deque[str] = deque([start])
        closer: str | None = None      # the node with an edge back to start
        while queue:
            u = queue.popleft()
            # BFS is distance-monotone; once dist[u] can't beat best, stop.
            if best is not None and dist[u] + 1 >= len(best):
                break
            for v in graph.get(u, ()):
                if v not in nodes:
                    continue
                if v == start and dist[u] >= 1:
                    closer = u           # shortest closer in BFS order
                    break
                if v not in dist:
                    dist[v] = dist[u] + 1
                    pred[v] = u
                    queue.append(v)
            if closer is not None:
                break
        if closer is not None:
            path: list[str] = []
            node: str | None = closer
            while node is not None:
                path.append(node)
                node = pred[node]
            path.reverse()
            cand = path + [start]        # start … closer → start
            if best is None or len(cand) < len(best):
                best = cand
        if best is not None and len(best) == 3:
            break        # a → b → a is the shortest possible in a multi-node SCC
    if best is None:                       # pathological; never expected for an SCC
        ordered = sorted(nodes)
        return ordered + [ordered[0]]
    return best


def _cycle_path(graph: dict[str, set[str]], scc: list[str]) -> list[str]:
    """The shortest elementary cycle path for an SCC, via the BOUNDED BFS.

    Codex review (#154): the prior `networkx.simple_cycles` enumerated EVERY
    elementary cycle just to pick the shortest — and the count grows
    exponentially in a dense SCC, so on exactly the cyclic graphs A001 reports
    it could hang / exhaust memory. The BFS finds the shortest cycle directly
    (polynomial, bounded — it stops at the first `a → b → a`), so we never
    materialize the full cycle set. networkx still backs the (polynomial) SCC
    detection in `_scc_cycles`."""
    return _bfs_shortest_cycle(graph, scc)


def _check_cycles(graph: dict[str, set[str]],
                  mod_to_path: dict[str, str]) -> list[Finding]:
    out: list[Finding] = []
    for cycle in _scc_cycles(graph):
        # Report ONE finding per cycle, anchored at the first module.
        anchor_mod = sorted(cycle)[0]
        anchor_path = mod_to_path.get(anchor_mod, "")
        if not anchor_path:
            continue
        path = _cycle_path(graph, cycle)
        out.append(make_finding(
            rule="A001", severity=SEVERITY["A001"],
            file=anchor_path, line=1,
            message=f"circular import: {' → '.join(path)}",
            evidence=" ↔ ".join(sorted(cycle)),
        ))
    return out


def _degrees(graph: dict[str, set[str]]) -> tuple[dict[str, int], dict[str, int]]:
    """(fan_in, fan_out) per module, counting only intra-tree edges (both
    endpoints in the graph). Plain edge counting — no graph library needed."""
    fan_out: dict[str, int] = {}
    fan_in: dict[str, int] = {m: 0 for m in graph}
    for m, succ in graph.items():
        intra = [s for s in succ if s in graph]
        fan_out[m] = len(intra)
        for s in intra:
            fan_in[s] = fan_in.get(s, 0) + 1
    return fan_in, fan_out


def _check_structure(graph: dict[str, set[str]], mod_to_path: dict[str, str],
                     loc_by_path: dict[str, int]) -> list[Finding]:
    """A004 fan-out / A005 fan-in / A006 god-module (Spec 051)."""
    fan_in, fan_out = _degrees(graph)
    out: list[Finding] = []
    for mod, path in mod_to_path.items():
        fo = fan_out.get(mod, 0)
        fi = fan_in.get(mod, 0)
        loc = loc_by_path.get(path, 0)
        if fo >= _FANOUT_WARN:
            sev = "fail" if fo >= _FANOUT_FAIL else "warn"
            out.append(make_finding(
                rule="A004", severity=sev, file=path, line=1,
                message=(f"high fan-out: imports {fo} intra-tree modules "
                         f"(≥ {_FANOUT_WARN}) — split into cohesive units"),
                evidence=f"fan_out={fo}"))
        if fi >= _FANIN_INFO:
            out.append(make_finding(
                rule="A005", severity=SEVERITY["A005"], file=path, line=1,
                message=(f"high fan-in: imported by {fi} intra-tree modules "
                         f"(≥ {_FANIN_INFO}) — a core utility"),
                evidence=f"fan_in={fi}"))
        if fi >= _FANIN_INFO and fo >= _FANOUT_WARN and loc >= _GOD_LOC:
            out.append(make_finding(
                rule="A006", severity=SEVERITY["A006"], file=path, line=1,
                message=(f"god-module: fan-in {fi} + fan-out {fo} + LOC {loc} "
                         f"— imports lots, imported by lots, and big"),
                evidence=f"fan_in={fi},fan_out={fo},loc={loc}"))
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
    # Cycles + structural metrics run once over the import graph. `_build_graph`
    # already read every source; reuse it for the size checks (no second read).
    graph, mod_to_path, src_by_path = _build_graph(root)
    findings.extend(_check_cycles(graph, mod_to_path))
    loc_by_path: dict[str, int] = {}
    for path, src in src_by_path.items():
        loc_by_path[path] = src.count("\n") + (0 if src.endswith("\n") else 1)
        findings.extend(_check_file_size(path, src))
    findings.extend(_check_structure(graph, mod_to_path, loc_by_path))
    return findings
