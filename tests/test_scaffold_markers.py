"""Spec 158 Slice 1 — scaffold-marker audit tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_scaffold_markers import (
    MARKER,
    MarkerStatus,
    CapabilityMarker,
    ScaffoldReport,
    audit_tree,
    main,
)


def _scaffold_cap(tmp_path: Path, name: str, with_marker: bool,
                   folder: bool = False) -> None:
    caps = tmp_path / "capabilities"
    caps.mkdir(exist_ok=True)
    body = f"# {MARKER}\n" if False else ""    # avoid contaminating with inline marker
    if folder:
        d = caps / name
        d.mkdir()
        text = (MARKER + "\n" if with_marker else "") + f'"""{name} cap."""\n'
        (d / "_main.py").write_text(text)
    else:
        path = caps / f"{name}.py"
        text = (MARKER + "\n" if with_marker else "") + f'"""{name} cap."""\n'
        path.write_text(text)


def test_audit_reports_marker_present_on_simple_cap(tmp_path):
    _scaffold_cap(tmp_path, "alpha", with_marker=True, folder=False)
    rep = audit_tree(tmp_path)
    assert len(rep.markers) == 1
    assert rep.markers[0].status == MarkerStatus.PRESENT
    assert rep.markers[0].name == "alpha"
    assert rep.fraction == 1.0


def test_audit_reports_marker_missing(tmp_path):
    _scaffold_cap(tmp_path, "beta", with_marker=False, folder=False)
    rep = audit_tree(tmp_path)
    assert len(rep.markers) == 1
    assert rep.markers[0].status == MarkerStatus.MISSING
    assert rep.fraction == 0.0


def test_audit_handles_folder_form_capability(tmp_path):
    _scaffold_cap(tmp_path, "gamma", with_marker=True, folder=True)
    rep = audit_tree(tmp_path)
    assert len(rep.markers) == 1
    assert rep.markers[0].status == MarkerStatus.PRESENT
    assert rep.markers[0].name == "gamma"


def test_audit_skips_private_modules(tmp_path):
    _scaffold_cap(tmp_path, "delta", with_marker=True, folder=False)
    # Underscore-prefixed file (_internal.py) is not a capability
    (tmp_path / "capabilities" / "_internal.py").write_text("# internal\n")
    rep = audit_tree(tmp_path)
    assert {m.name for m in rep.markers} == {"delta"}


def test_audit_flags_folder_without_main_as_unknown(tmp_path):
    caps = tmp_path / "capabilities"
    caps.mkdir()
    (caps / "epsilon").mkdir()
    # no _main.py inside
    rep = audit_tree(tmp_path)
    assert len(rep.markers) == 1
    assert rep.markers[0].status == MarkerStatus.UNKNOWN


def test_audit_fraction_is_present_over_present_plus_missing(tmp_path):
    _scaffold_cap(tmp_path, "a", with_marker=True, folder=False)
    _scaffold_cap(tmp_path, "b", with_marker=False, folder=False)
    _scaffold_cap(tmp_path, "c", with_marker=True, folder=True)
    rep = audit_tree(tmp_path)
    assert len(rep.present) == 2
    assert len(rep.missing) == 1
    assert abs(rep.fraction - (2 / 3)) < 1e-9


def test_cli_strict_passes_when_all_marked(tmp_path):
    _scaffold_cap(tmp_path, "x", with_marker=True, folder=False)
    rc = main(["--root", str(tmp_path), "--strict"])
    assert rc == 0


def test_cli_strict_fails_when_any_missing(tmp_path):
    _scaffold_cap(tmp_path, "y", with_marker=False, folder=False)
    rc = main(["--root", str(tmp_path), "--strict"])
    assert rc == 1


def test_live_tree_invariant_every_capability_has_marker():
    """LIVE INVARIANT: every capability under `agency/capabilities/`
    must carry the `# agency-scaffold: v1` marker (Spec 158 Slice 1
    coverage goal). A new capability without the marker fails this
    test, forcing the author to add it."""
    repo = Path(__file__).parent.parent
    rep = audit_tree(repo / "agency")
    assert rep.missing == [], (
        "the live tree has capabilities WITHOUT the `# agency-scaffold: v1` "
        "marker — add the marker on line 1 of each:\n"
        + "\n".join(f"  {m.name}  ({m.path})" for m in rep.missing))
    # Slice 2 promotes to a CI gate via scripts/check-drift extension.
