"""Spec 032 §A — TemplateDoc / SchemaDoc / RenderTemplates / ArtefactSchemas."""
from pathlib import Path

from agency.capability import (
    TemplateDoc, SchemaDoc, RenderTemplates, ArtefactSchemas, CapabilityBase,
)


def test_template_doc_fields():
    td = TemplateDoc(
        description="Use when rendering a note",
        canonical_example="ctx.render('foo', x='y')",
    )
    assert td.description == "Use when rendering a note"


def test_schema_doc_fields():
    sd = SchemaDoc(
        description="Use when validating a foo",
        canonical_example="memory.validate_schema(id, 'schema:foo')",
    )
    assert sd.description == "Use when validating a foo"


def test_render_templates_holds_folder_and_docs_dict():
    rt = RenderTemplates(folder=Path("/tmp/templates"), docs={
        "foo": TemplateDoc(description="Use when X", canonical_example="..."),
    })
    assert rt.folder == Path("/tmp/templates")
    assert "foo" in rt.docs


def test_artefact_schemas_holds_folder_and_docs_dict():
    asch = ArtefactSchemas(folder=Path("/tmp/schemas"), docs={})
    assert asch.folder == Path("/tmp/schemas")
    assert asch.docs == {}


def test_render_templates_from_module_classmethod(tmp_path):
    fake_module_file = tmp_path / "fake_main.py"
    fake_module_file.write_text("# stub")
    (tmp_path / "templates").mkdir()
    rt = RenderTemplates.from_module(str(fake_module_file), "templates")
    assert rt.folder == tmp_path / "templates"
    assert rt.docs == {}


def test_artefact_schemas_from_module_classmethod(tmp_path):
    fake_module_file = tmp_path / "fake_main.py"
    fake_module_file.write_text("# stub")
    (tmp_path / "schemas").mkdir()
    asch = ArtefactSchemas.from_module(str(fake_module_file), "schemas")
    assert asch.folder == tmp_path / "schemas"


def test_capabilitybase_attrs_default_to_none():
    class _Cap(CapabilityBase):
        name = "test"
    assert _Cap.render_templates is None
    assert _Cap.artefact_schemas is None
