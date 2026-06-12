"""Spec 173 Slice 1 — typed LinkFinding tests."""
from __future__ import annotations

import pytest

from agency._link_finding import LinkFinding


def test_typed_shape():
    f = LinkFinding(reflection_id="reflection:abc",
                     missing_edge="SERVES", severity="error",
                     file="x.py", line=42)
    assert f.reflection_id == "reflection:abc"
    assert f.missing_edge == "SERVES"
    assert f.severity == "error"


def test_default_file_and_line():
    f = LinkFinding(reflection_id="reflection:abc",
                     missing_edge="OBSERVED_DURING", severity="warn")
    assert f.file == ""
    assert f.line == 0


def test_rejects_empty_reflection_id():
    with pytest.raises(ValueError):
        LinkFinding(reflection_id="", missing_edge="SERVES",
                     severity="error")


def test_rejects_invalid_edge():
    with pytest.raises(ValueError):
        LinkFinding(reflection_id="r:x", missing_edge="BOGUS",
                     severity="error")


def test_rejects_invalid_severity():
    with pytest.raises(ValueError):
        LinkFinding(reflection_id="r:x", missing_edge="SERVES",
                     severity="bogus")


def test_rejects_negative_line():
    with pytest.raises(ValueError):
        LinkFinding(reflection_id="r:x", missing_edge="SERVES",
                     severity="error", line=-1)


def test_frozen_blocks_mutation():
    f = LinkFinding(reflection_id="r:x", missing_edge="SERVES",
                     severity="error")
    with pytest.raises(Exception):
        f.severity = "warn"
