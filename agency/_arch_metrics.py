"""Spec 167 Slice 2 — derive typed `ArchMetric`s from the live import graph.

Slice 1 shipped the typed `ArchMetric` shape but nothing populated it (dormant).
This is the deriver: it COMPOSES the architecture analyzer (`analyze/_architecture.py`
— Spec 051) — `_build_graph` (AST import graph), `_scc_cycles`/`_cycle_path`
(networkx-backed SCC, pure-Python fallback), and `_degrees` (fan-in/fan-out) —
into typed `ArchMetric` findings. No second graph build → the metrics and the
analyzer's findings cannot diverge (rule 2).

Derived invariants (Done-When):
  - `sum(fan_out) == sum(fan_in)` — the edge-count identity of one graph.
  - god-module threshold is RELATIVE — top-decile of `fan_in × LOC` per run,
    never a pinned constant (survives repo growth).
  - networkx missing → the analyzer's pure-Python fallback still yields metrics.
  - an unresolvable import is flagged (`Codes.IMPORT_UNRESOLVED`), partial
    metrics still flow — the build never crashes.
"""
from __future__ import annotations

import os

from ._typed_shapes_wave1_part2 import ArchMetric
from .toolresult import Codes


def _agency_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _loc(src: str) -> int:
    return src.count("\n") + 1 if src else 0


def derive_arch_metrics(root: str | None = None) -> "tuple[ArchMetric, ...]":
    """Typed architecture metrics over the import graph rooted at ``root``
    (defaults to the ``agency`` package). Cycles → one metric each (score = cycle
    length); fan-out / fan-in → one per module (score = degree); god-modules →
    the top-decile of ``fan_in × LOC``."""
    from .capabilities.analyze import _architecture as arch
    root = root or _agency_root()
    graph, mod_to_path, src_by_path = arch._build_graph(root)

    metrics: list[ArchMetric] = []

    # A001 — cycles (one metric per SCC cycle; score = cycle length).
    for scc in arch._scc_cycles(graph):
        path = arch._cycle_path(graph, scc)
        metrics.append(ArchMetric(axis_id="A001", kind="cycle",
                                  nodes=tuple(path), score=float(len(scc))))

    # A004/A005 — fan-out / fan-in per module from the SAME graph.
    fan_in, fan_out = arch._degrees(graph)
    for mod, fo in fan_out.items():
        metrics.append(ArchMetric(axis_id="A004", kind="fan_out",
                                  nodes=(mod,), score=float(fo)))
    for mod, fi in fan_in.items():
        metrics.append(ArchMetric(axis_id="A005", kind="fan_in",
                                  nodes=(mod,), score=float(fi)))

    # A006 — god-module: RELATIVE top-decile of fan_in × LOC (per-run, not pinned).
    weights: dict[str, float] = {}
    for mod in graph:
        path = mod_to_path.get(mod, "")
        loc = _loc(src_by_path.get(path, ""))
        weights[mod] = fan_in.get(mod, 0) * loc
    ranked = sorted((w for w in weights.values() if w > 0), reverse=True)
    if ranked:
        cutoff_idx = max(0, int(len(ranked) * 0.1) - 1)
        threshold = ranked[cutoff_idx]
        for mod, w in weights.items():
            if w >= threshold and w > 0:
                metrics.append(ArchMetric(axis_id="A006", kind="god_module",
                                          nodes=(mod,), score=float(w)))
    return tuple(metrics)


def fan_identity_holds(metrics) -> bool:
    """The edge-count identity: total fan-out equals total fan-in (both are the
    edge count of the one import graph)."""
    out = sum(m.score for m in metrics if m.kind == "fan_out")
    inc = sum(m.score for m in metrics if m.kind == "fan_in")
    return out == inc


def arch_metrics_summary(root: str | None = None) -> dict:
    """A doctor-friendly roll-up. `ready` iff the graph builds and the fan
    identity holds. Reports the networkx backend + an `IMPORT_UNRESOLVED` hint
    when the build can't run. Never raises."""
    from .capabilities.analyze import _architecture as arch
    try:
        metrics = derive_arch_metrics(root)
        cycles = [m for m in metrics if m.kind == "cycle"]
        return {"ready": fan_identity_holds(metrics),
                "metrics": len(metrics),
                "cycles": len(cycles),
                "god_modules": sum(1 for m in metrics if m.kind == "god_module"),
                "networkx": bool(getattr(arch, "_HAS_NX", False))}
    except Exception as exc:  # noqa: BLE001 — never crash the doctor
        return {"ready": None, "metrics": 0, "cycles": 0, "god_modules": 0,
                "networkx": bool(getattr(arch, "_HAS_NX", False)),
                "code": Codes.IMPORT_UNRESOLVED, "error": str(exc)}
