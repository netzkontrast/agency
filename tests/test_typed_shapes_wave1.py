"""Spec 171 + 175 + 176 Slice 1 — batch typed shapes tests."""
from __future__ import annotations

import pytest

from agency._typed_shapes_wave1 import (
    CapabilityRow,
    CommandFile,
    GuardFinding,
    InstallSurface,
    IntentCapture,
)


# ── Spec 171 — GuardFinding ───────────────────────────────────────────
def test_guard_typed_shape():
    g = GuardFinding(verb_id="capability_x_y", param_name="intent_id",
                      expected_label="Intent", severity="error",
                      file="agency/x.py", line=10)
    assert g.verb_id == "capability_x_y"
    assert g.severity == "error"


def test_guard_rejects_empty_fields():
    with pytest.raises(ValueError):
        GuardFinding(verb_id="", param_name="p", expected_label="L",
                      severity="error")


def test_guard_rejects_invalid_severity():
    with pytest.raises(ValueError):
        GuardFinding(verb_id="x", param_name="p", expected_label="L",
                      severity="bogus")


# ── Spec 175 — InstallSurface ────────────────────────────────────────
def test_capability_row_typed_shape():
    r = CapabilityRow(name="analyze", verb_count=12,
                       description="Multi-axis decidable analysis")
    assert r.verb_count == 12


def test_capability_row_rejects_negative_count():
    with pytest.raises(ValueError):
        CapabilityRow(name="x", verb_count=-1, description="d")


def test_command_file_typed_shape():
    c = CommandFile(name="agency-tdd", path="commands/agency-tdd.md")
    assert c.name == "agency-tdd"


def test_command_file_rejects_empty():
    with pytest.raises(ValueError):
        CommandFile(name="", path="x")


def test_install_surface_typed_shape():
    s = InstallSurface(
        marketplace_desc="A test plugin",
        readme_capability_rows=(
            CapabilityRow(name="a", verb_count=1, description="d"),),
        slash_commands=(
            CommandFile(name="a", path="commands/a.md"),),
        userconfig_extras=("anthropic",),
        generated_at="2026-06-12T10:00:00Z",
    )
    assert len(s.readme_capability_rows) == 1


def test_install_surface_rejects_empty_desc():
    with pytest.raises(ValueError):
        InstallSurface(marketplace_desc="",
                        readme_capability_rows=(),
                        slash_commands=(),
                        userconfig_extras=(),
                        generated_at="t")


# ── Spec 176 — IntentCapture ─────────────────────────────────────────
def test_intent_capture_typed_shape():
    c = IntentCapture(intent_id="intent:x", captured_at="2026-06-12",
                       source="sessionstart",
                       artefact_ids=("artefact:a",), turns=4)
    assert c.source == "sessionstart"


def test_intent_capture_rejects_invalid_source():
    with pytest.raises(ValueError):
        IntentCapture(intent_id="x", captured_at="t",
                       source="bogus")


def test_intent_capture_rejects_negative_turns():
    with pytest.raises(ValueError):
        IntentCapture(intent_id="x", captured_at="t",
                       source="manual", turns=-1)
