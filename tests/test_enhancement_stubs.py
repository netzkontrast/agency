"""Wave 3-12 enhancement-stub catalogue tests."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from agency._enhancement_stubs import (
    EnhancementSliceStub,
    STUBS,
    catalogue_spec_ids,
)


def test_stub_typed_shape():
    s = EnhancementSliceStub(spec_id="178", slug="x", wave=3)
    assert s.spec_id == "178"
    assert s.status == "slice1_typed_stub"


def test_stub_rejects_invalid_spec_id():
    with pytest.raises(ValueError):
        EnhancementSliceStub(spec_id="x", slug="s", wave=3)
    with pytest.raises(ValueError):
        EnhancementSliceStub(spec_id="9999", slug="s", wave=3)


def test_stub_rejects_empty_slug():
    with pytest.raises(ValueError):
        EnhancementSliceStub(spec_id="178", slug="", wave=3)


def test_stub_rejects_invalid_wave():
    with pytest.raises(ValueError):
        EnhancementSliceStub(spec_id="178", slug="s", wave=0)
    with pytest.raises(ValueError):
        EnhancementSliceStub(spec_id="178", slug="s", wave=13)


def test_stub_rejects_invalid_status():
    with pytest.raises(ValueError):
        EnhancementSliceStub(spec_id="178", slug="s", wave=3,
                              status="bogus")                          # type: ignore


def test_catalogue_has_substantial_entries():
    """The catalogue covers waves 3-12 (substantial Slice 1 batch)."""
    assert len(STUBS) >= 50
    waves = {s.wave for s in STUBS}
    assert waves >= {3, 4, 5, 6, 7}


def test_catalogue_spec_ids_unique():
    """No duplicate spec_ids in the catalogue."""
    ids = [s.spec_id for s in STUBS]
    assert len(ids) == len(set(ids))


def test_catalogue_covers_drafted_specs_under_plan():
    """LIVE INVARIANT: the catalogue covers every Plan/NNN-… drafted
    spec in the 178-277 range (minus 195, which has Slice 3 SHIPPED).
    A new drafted spec under Plan/ MUST register a stub here."""
    repo = Path(__file__).parent.parent
    plan = repo / "Plan"
    drafted: set[str] = set()
    for d in sorted(plan.iterdir()):
        if not d.is_dir():
            continue
        m = re.match(r"^(\d{3})-(.+)$", d.name)
        if not m:
            continue
        sid = m.group(1)
        n = int(sid)
        if 178 <= n <= 278 and sid != "195":
            drafted.add(sid)
    missing = drafted - catalogue_spec_ids()
    assert missing == set(), (
        f"Plan/ has drafted specs without an EnhancementSliceStub: {sorted(missing)}. "
        f"Add them to _CATALOG in agency/_enhancement_stubs.py")
