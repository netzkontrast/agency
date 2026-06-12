"""Spec 170 Slice 1 — typed DoctorField/Section/Report + invariants."""
from __future__ import annotations

import pytest

from agency._doctor_shapes import (
    DoctorField,
    DoctorReport,
    DoctorSection,
    FieldSource,
)


def test_field_typed_shape():
    f = DoctorField(key="anthropic", value="ready", ready=True, hint=None,
                     source="extra")
    assert f.key == "anthropic"
    assert f.ready is True
    assert f.hint is None


def test_field_ready_false_requires_non_empty_hint():
    """Spec 170 invariant: ready=False ⇒ hint non-empty (pipx-HINT pattern)."""
    with pytest.raises(ValueError):
        DoctorField(key="x", value="", ready=False, hint=None,
                     source="env")
    with pytest.raises(ValueError):
        DoctorField(key="x", value="", ready=False, hint="",
                     source="env")


def test_field_ready_false_accepts_non_empty_hint():
    f = DoctorField(key="x", value="", ready=False,
                     hint="install pip install agency[anthropic]", source="extra")
    assert f.ready is False
    assert "install" in f.hint


def test_field_source_must_be_valid():
    with pytest.raises(ValueError):
        DoctorField(key="x", value="", ready=True, hint=None,
                     source="bogus")                                  # type: ignore[arg-type]


def test_section_typed_shape():
    s = DoctorSection(name="anthropic", fields=(
        DoctorField(key="backend", value="claude-api", ready=True,
                     hint=None, source="extra"),
    ))
    assert s.name == "anthropic"
    assert len(s.fields) == 1


def test_section_rejects_empty_name():
    with pytest.raises(ValueError):
        DoctorSection(name="", fields=())


def test_report_typed_shape():
    r = DoctorReport(sections=(
        DoctorSection(name="hooks", fields=(
            DoctorField(key="plugin_enabled", value=True,
                         ready=True, hint=None, source="registry"),
        )),
    ))
    assert len(r.sections) == 1
    assert r.sections[0].name == "hooks"


def test_report_to_dict_round_trips():
    """`DoctorReport.to_dict()` serializes to a JSON-friendly dict
    preserving field order + section order."""
    r = DoctorReport(sections=(
        DoctorSection(name="hooks", fields=(
            DoctorField(key="enabled", value=True, ready=True,
                         hint=None, source="registry"),
            DoctorField(key="foreign", value=[], ready=True,
                         hint=None, source="registry"),
        )),
        DoctorSection(name="anthropic", fields=(
            DoctorField(key="backend", value="none", ready=False,
                         hint="pip install agency[anthropic]", source="extra"),
        )),
    ))
    d = r.to_dict()
    assert list(d.keys()) == ["hooks", "anthropic"]
    assert list(d["hooks"].keys()) == ["enabled", "foreign"]


def test_invariant_walker_reports_no_violations_on_clean_report():
    """`DoctorReport.invariant_violations()` returns the empty list when
    every ready=False field has a hint + every source is valid."""
    r = DoctorReport(sections=(
        DoctorSection(name="x", fields=(
            DoctorField(key="a", value=1, ready=True, hint=None,
                         source="env"),
            DoctorField(key="b", value=None, ready=False,
                         hint="set AGENCY_X=yes", source="env"),
        )),
    ))
    assert r.invariant_violations() == []


def test_field_source_set_equals_documented_set():
    """The valid `source` values are exactly {env, extra, graph,
    registry} — Spec 170 Slice 1 contract."""
    assert set(FieldSource.__args__) == {"env", "extra", "graph", "registry"}
