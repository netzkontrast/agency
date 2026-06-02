"""Spec 032 Phase 1 §B — path-safety tests for _capability_loader.

Panel F-9: `..` rejection is NOT sufficient — symlinks pointing outside
the capability folder are an equally dangerous escape vector. The loader's
`os.path.realpath` check defends against BOTH. These tests document the
security invariant explicitly.
"""
import os
from pathlib import Path

import pytest

from agency.capability import CapabilityBase, RenderTemplates, ArtefactSchemas
from agency._capability_loader import load_capability_folders


def _make_cap_with_templates_folder(folder: Path):
    """Helper: build a fake capability pointing at the given templates folder."""

    class _Cap(CapabilityBase):
        name = "testcap"
    _Cap.render_templates = RenderTemplates(folder=folder)
    return _Cap


def _make_cap_with_schemas_folder(folder: Path):
    class _Cap(CapabilityBase):
        name = "testcap"
    _Cap.artefact_schemas = ArtefactSchemas(folder=folder)
    return _Cap


def test_path_safety_rejects_symlink_to_outside_file_in_templates(tmp_path):
    """A symlink in templates/ pointing at a file OUTSIDE the cap folder
    is the F-9 attack vector. realpath() resolves the symlink; the
    .relative_to() check then fails because the real path is outside.
    """
    outside = tmp_path / "outside.md"
    outside.write_text("# secret content that must not leak into the graph")

    cap_dir = tmp_path / "capdir"
    cap_dir.mkdir()
    templates = cap_dir / "templates"
    templates.mkdir()
    # Plant a symlink inside templates/ pointing OUTSIDE the cap dir
    sneaky = templates / "leaky.md"
    os.symlink(outside, sneaky)

    cap = _make_cap_with_templates_folder(templates)
    with pytest.raises(ValueError) as ei:
        load_capability_folders(cap)
    msg = str(ei.value).lower()
    assert "path safety" in msg or "outside" in msg or "leaky" in msg.lower()


def test_path_safety_rejects_symlink_to_outside_file_in_schemas(tmp_path):
    """Same attack vector, schemas/ side."""
    outside = tmp_path / "outside.json"
    outside.write_text('{"secret": "exfil"}')

    cap_dir = tmp_path / "capdir"
    cap_dir.mkdir()
    schemas = cap_dir / "schemas"
    schemas.mkdir()
    sneaky = schemas / "leaky.json"
    os.symlink(outside, sneaky)

    cap = _make_cap_with_schemas_folder(schemas)
    with pytest.raises(ValueError) as ei:
        load_capability_folders(cap)
    msg = str(ei.value).lower()
    assert "path safety" in msg or "outside" in msg or "leaky" in msg.lower()


def test_path_safety_allows_symlink_to_file_inside_folder(tmp_path):
    """A symlink that resolves INSIDE the cap folder is fine.
    This is the negative-of-the-negative: the safety check must not
    over-reach and ban legitimate internal symlinks.
    """
    cap_dir = tmp_path / "capdir"
    cap_dir.mkdir()
    templates = cap_dir / "templates"
    templates.mkdir()
    # A real file
    real = templates / "real.md"
    real.write_text("real body")
    # A symlink to it (also inside templates/)
    alias = templates / "alias.md"
    os.symlink(real, alias)

    cap = _make_cap_with_templates_folder(templates)
    templates_dict, _ = load_capability_folders(cap)
    # The symlink resolves inside the folder → no ValueError raised.
    # Note: _safe_resolve uses realpath, so symlinks key under the
    # underlying file's stem ("real"), not the symlink's name ("alias").
    assert "real" in templates_dict


def test_path_safety_realpath_check_is_explicit(tmp_path):
    """Documents the security invariant: the check uses os.path.realpath,
    not just Path.resolve() — these have subtly different semantics for
    broken symlinks. realpath is the more conservative choice.

    This test is more of a documentation/regression assertion than a
    behavior probe — if the implementation drifts away from realpath
    (e.g. someone "modernizes" to Path.resolve), this test should fail
    OR the documentation in _capability_loader.py needs updating.
    """
    import inspect

    from agency import _capability_loader
    source = inspect.getsource(_capability_loader._safe_resolve)
    assert "realpath" in source, (
        "_safe_resolve must use os.path.realpath for symlink-escape defense "
        "(Spec 032 panel F-9)"
    )
