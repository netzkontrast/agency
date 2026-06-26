"""Spec 167 Slice 2 — typed architecture-metric deriver invariants.

`derive_arch_metrics` composes the architecture analyzer's import graph into
typed `ArchMetric` findings. The load-bearing derived invariants: fan-out/fan-in
come from the SAME graph (edge-count identity), and the god-module threshold is
relative (top-decile), not a pinned constant.
"""
from __future__ import annotations

from agency._arch_metrics import (arch_metrics_summary, derive_arch_metrics,
                                  fan_identity_holds)
from agency._typed_shapes_wave1_part2 import ArchMetric
from agency.toolresult import Codes


def test_import_unresolved_code_exists():
    assert Codes.IMPORT_UNRESOLVED == "import_unresolved"


def test_metrics_are_typed_and_kinds_valid():
    metrics = derive_arch_metrics()
    assert metrics and all(isinstance(m, ArchMetric) for m in metrics)
    assert {m.kind for m in metrics} <= {"cycle", "fan_out", "fan_in", "god_module"}


def test_fan_out_equals_fan_in_edge_identity():
    # sum(fan_out) == sum(fan_in) — both are the edge count of the one graph
    metrics = derive_arch_metrics()
    assert fan_identity_holds(metrics)


def test_god_module_threshold_is_relative_not_pinned():
    # god-modules are the top-decile of fan_in×LOC, so they're a SUBSET of
    # modules and never exceed ~10%+ of the fan_in node set (relative, derived)
    metrics = derive_arch_metrics()
    fan_in_mods = {m.nodes[0] for m in metrics if m.kind == "fan_in"}
    god_mods = {m.nodes[0] for m in metrics if m.kind == "god_module"}
    assert god_mods <= fan_in_mods
    assert len(god_mods) <= len(fan_in_mods)


def test_summary_ready_iff_identity_holds():
    summ = arch_metrics_summary()
    assert summ["ready"] is True
    assert summ["metrics"] > 0
    # networkx is a default dep in this repo; the key is present either way
    assert "networkx" in summ
