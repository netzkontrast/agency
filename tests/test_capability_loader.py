"""Spec 032 §B — capability folder loader (path-safe, lint-clean)."""
import os
from pathlib import Path

import pytest

from agency.capability import (
    Capability, CapabilityBase, RenderTemplates, ArtefactSchemas,
    TemplateDoc, SchemaDoc,
)
from agency._capability_loader import load_capability_folders


def _make_cap_with_templates(tmp_path, files: dict[str, str]):
    """Helper: build a fake capability with templates/ folder + files."""
    folder = tmp_path / "templates"
    folder.mkdir()
    for name, body in files.items():
        (folder / name).write_text(body)

    class _Cap(CapabilityBase):
        name = "testcap"
    _Cap.render_templates = RenderTemplates(folder=folder)
    return _Cap


def _make_cap_with_schemas(tmp_path, files: dict[str, str]):
    """Helper: build a fake capability with schemas/ folder + files."""
    folder = tmp_path / "schemas"
    folder.mkdir()
    for name, body in files.items():
        (folder / name).write_text(body)

    class _Cap(CapabilityBase):
        name = "testcap"
    _Cap.artefact_schemas = ArtefactSchemas(folder=folder)
    return _Cap


def test_loader_returns_empty_for_cap_without_folders():
    cap = Capability(name="x", home="capability", verbs={})
    templates, schemas = load_capability_folders(cap)
    assert templates == {}
    assert schemas == {}


def test_loader_loads_templates(tmp_path):
    cap = _make_cap_with_templates(tmp_path, {
        "greeting.md": "Hello $name!",
    })
    templates, schemas = load_capability_folders(cap)
    assert "greeting" in templates
    # The loaded value is a string.Template
    assert templates["greeting"].substitute(name="World") == "Hello World!"
    assert schemas == {}


def test_loader_loads_schemas_simple_shape(tmp_path):
    import json
    cap = _make_cap_with_schemas(tmp_path, {
        "foo.json": json.dumps({"required": ["a", "b"]}),
    })
    templates, schemas = load_capability_folders(cap)
    assert "foo" in schemas
    assert schemas["foo"] == {"required": ["a", "b"]}


def test_loader_loads_schemas_draft07_shape(tmp_path):
    import json
    cap = _make_cap_with_schemas(tmp_path, {
        "foo.json": json.dumps({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "required": ["a"],
            "properties": {"a": {"type": "string"}},
        }),
    })
    templates, schemas = load_capability_folders(cap)
    assert "foo" in schemas
    assert "$schema" in schemas["foo"]  # full shape preserved


def test_loader_rejects_kebab_case_violation(tmp_path):
    cap = _make_cap_with_templates(tmp_path, {
        "BadName.md": "x",
    })
    with pytest.raises(ValueError) as ei:
        load_capability_folders(cap)
    assert "kebab" in str(ei.value).lower() or "BadName" in str(ei.value)


def test_loader_rejects_underscore_filename(tmp_path):
    cap = _make_cap_with_templates(tmp_path, {
        "bad_name.md": "x",
    })
    with pytest.raises(ValueError):
        load_capability_folders(cap)


def test_loader_rejects_missing_folder(tmp_path):
    folder = tmp_path / "nonexistent"

    class _Cap(CapabilityBase):
        name = "testcap"
    _Cap.render_templates = RenderTemplates(folder=folder)
    with pytest.raises(ValueError) as ei:
        load_capability_folders(_Cap)
    assert "does not exist" in str(ei.value).lower() or "nonexistent" in str(ei.value)


def test_loader_rejects_empty_folder(tmp_path):
    folder = tmp_path / "templates"
    folder.mkdir()  # empty

    class _Cap(CapabilityBase):
        name = "testcap"
    _Cap.render_templates = RenderTemplates(folder=folder)
    with pytest.raises(ValueError) as ei:
        load_capability_folders(_Cap)
    msg = str(ei.value).lower()
    assert "empty" in msg or "no files" in msg or "didn't fulfill" in msg.lower() or "didnt fulfill" in msg


def test_loader_handles_multiple_template_extensions(tmp_path):
    cap = _make_cap_with_templates(tmp_path, {
        "alpha.md": "alpha",
        "beta.tpl": "beta",
        "gamma.sh": "gamma",
    })
    templates, _ = load_capability_folders(cap)
    assert set(templates) == {"alpha", "beta", "gamma"}
