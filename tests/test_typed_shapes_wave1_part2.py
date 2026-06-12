"""Wave-1 batch-2 typed-shape tests."""
from __future__ import annotations

import pytest

from agency._typed_shapes_wave1_part2 import (
    ArchMetric,
    AxisRegistry,
    DeriveStatus,
    GateProjection,
    MigrationVerdict,
    RedTeamInvariant,
    RefFinding,
    WrapperShape,
)


def test_red_team_invariant():
    r = RedTeamInvariant(invariant_id="rt:clock-seed", description="d",
                          status="pass", ran_at="t")
    assert r.status == "pass"


def test_red_team_rejects_invalid_status():
    with pytest.raises(ValueError):
        RedTeamInvariant(invariant_id="x", description="d",
                          status="bogus", ran_at="t")


def test_gate_projection():
    g = GateProjection(kept=("a", "b"), dropped=("c",))
    assert g.kept == ("a", "b")


def test_gate_projection_rejects_empty_key():
    with pytest.raises(ValueError):
        GateProjection(kept=("a", ""), dropped=())


def test_derive_status_byte_equal():
    d = DeriveStatus(skill_name="brainstorm", result="byte_equal")
    assert d.bytes_drift == 0


def test_derive_status_drift_records_bytes():
    d = DeriveStatus(skill_name="x", result="drift", bytes_drift=42)
    assert d.bytes_drift == 42


def test_derive_status_rejects_negative_drift():
    with pytest.raises(ValueError):
        DeriveStatus(skill_name="x", result="drift", bytes_drift=-1)


def test_wrapper_shape():
    w = WrapperShape(tool_name="ruff", axis_prefixes=("R", "E"),
                      extras=("analyze",))
    assert "R" in w.axis_prefixes


def test_wrapper_shape_rejects_empty_prefixes():
    with pytest.raises(ValueError):
        WrapperShape(tool_name="x", axis_prefixes=(), extras=())


def test_arch_metric():
    m = ArchMetric(axis_id="A1", kind="cycle",
                    nodes=("mod_a", "mod_b"), score=3.0)
    assert m.score == 3.0


def test_arch_metric_rejects_negative_score():
    with pytest.raises(ValueError):
        ArchMetric(axis_id="x", kind="cycle", nodes=(), score=-1)


def test_axis_registry_resolve():
    r = AxisRegistry(prefixes=(("A", "analyzer:arch"),
                                ("Q", "analyzer:quality")))
    assert r.resolve("A001") == "analyzer:arch"
    assert r.resolve("Q003") == "analyzer:quality"
    assert r.resolve("Z999") is None


def test_axis_registry_rejects_duplicate_prefix():
    with pytest.raises(ValueError):
        AxisRegistry(prefixes=(("A", "x"), ("A", "y")))


def test_migration_verdict():
    m = MigrationVerdict(verb_id="capability_x_y",
                          template_node_id="t:1", schema_node_id="s:1",
                          status="migrated")
    assert m.status == "migrated"


def test_migration_verdict_rejects_invalid_status():
    with pytest.raises(ValueError):
        MigrationVerdict(verb_id="x", template_node_id="",
                          schema_node_id="", status="bogus")


def test_ref_finding():
    f = RefFinding(file="install.py", invariant="exact-three-wire-verbs",
                    observed="4", expected="3", severity="error")
    assert f.severity == "error"


def test_ref_finding_rejects_empty_invariant():
    with pytest.raises(ValueError):
        RefFinding(file="x", invariant="", observed="o",
                    expected="e", severity="error")
