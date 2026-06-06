"""Spec 060 Phase 1 — bootstrap wire-up RED.

The keystone gap that Spec 032 left inert: `load_capability_folders` is
imported only by tests; no production code calls it. After this spec
lands, `Engine.__init__` calls the loader for every registered cap and
merges the file-discovered templates + schemas into the cap's
OntologyExtension before `ontology.extend` runs.

Two things must be true post-bootstrap:
1. Every capability that ships a `templates/` or `schemas/` folder
   has its file-discovered entries reachable via
   `engine.ontology.templates[name]` / `engine.ontology.schemas[name]`.
2. The merge raises ValueError when the SAME name is declared both in
   the OntologyExtension dict AND as a file (force clean migrations).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agency.capability import (
    ArtefactSchemas,
    CapabilityBase,
    OntologyExtension,
    RenderTemplates,
    verb,
)
from agency.engine import Engine


# ---------------------------------------------------------------------------
# A test capability that ships a template + a schema folder.
# ---------------------------------------------------------------------------


def _make_cap_with_folders(tmp_path: Path) -> type:
    """Build a capability class whose render_templates + artefact_schemas
    point at a freshly populated tmp_path tree."""
    templates_dir = tmp_path / "templates"
    schemas_dir = tmp_path / "schemas"
    templates_dir.mkdir()
    schemas_dir.mkdir()
    (templates_dir / "greeting.md").write_text(
        "# Hello $name\n\n"
        "<!-- AGENT: greet the user warmly and verify their session. -->\n"
    )
    (schemas_dir / "greeter-payload.json").write_text(
        '{"required": ["name", "session_id"]}'
    )

    class _BootstrapCap(CapabilityBase):
        name = "bootstrap_test"
        home = "memory"
        ontology = OntologyExtension(nodes={})
        render_templates = RenderTemplates(folder=templates_dir)
        artefact_schemas = ArtefactSchemas(folder=schemas_dir)

        @verb(role="transform")
        def ping(self) -> dict:
            """Trivial verb to register the cap.

            Inputs: none.
            Returns: ``{ok}``.
            chain_next: terminal.
            """
            return {"ok": True}

    return _BootstrapCap


def test_engine_loads_file_templates_at_bootstrap(tmp_path):
    cap_cls = _make_cap_with_folders(tmp_path)
    e = Engine(tempfile.mktemp(suffix=".db"),
                extra_capabilities=[cap_cls.as_capability()], _require_skill_doc=False)
    # Post-bootstrap: the file-discovered template must be reachable
    # through the merged engine ontology.
    assert "greeting" in e.ontology.templates, (
        f"file-discovered template 'greeting' missing from engine "
        f"ontology; got keys={sorted(e.ontology.templates)}")
    tpl = e.ontology.templates["greeting"]
    # The loader returns string.Template objects; inspect via .template.
    body = tpl.template if hasattr(tpl, "template") else str(tpl)
    assert "Hello $name" in body
    assert "<!-- AGENT:" in body, (
        "agent-instruction block must survive the load (Spec 060 §"
        "Agent-instruction doctrine)")


def test_engine_loads_file_schemas_at_bootstrap(tmp_path):
    cap_cls = _make_cap_with_folders(tmp_path)
    e = Engine(tempfile.mktemp(suffix=".db"),
                extra_capabilities=[cap_cls.as_capability()], _require_skill_doc=False)
    assert "greeter-payload" in e.ontology.schemas, (
        f"file-discovered schema 'greeter-payload' missing from engine "
        f"ontology; got keys={sorted(e.ontology.schemas)}")


def test_ctx_template_accessor(tmp_path):
    """`ctx.template(name)` reads a per-cap template via the engine
    ontology — substrate accessor symmetric to `ctx.record` / `ctx.recall`."""
    cap_cls = _make_cap_with_folders(tmp_path)
    e = Engine(tempfile.mktemp(suffix=".db"),
                extra_capabilities=[cap_cls.as_capability()], _require_skill_doc=False)
    iid = e.intent.capture_and_confirm("t", "x", "x", owner="user")
    # Invoke the verb (any verb) to build a real CapabilityContext via
    # the wiring path; we read via the engine's ontology proxy instead.
    from agency.capability import CapabilityContext
    ctx = CapabilityContext(
        memory=e.memory, ontology=e.ontology, registry=e.registry,
        intent_id=iid, agent_id="agent:test", engine=e)
    tpl = ctx.template("greeting")
    body = tpl.template if hasattr(tpl, "template") else str(tpl)
    assert "Hello $name" in body
    # Unknown name raises clearly.
    with pytest.raises(KeyError, match="missing"):
        ctx.template("missing")


def test_collision_dict_plus_file_raises(tmp_path):
    """A schema declared in both the OntologyExtension dict AND as a file
    is a doctrinal collision — bootstrap must fail loud with a clear
    message pointing at both locations (forces clean migrations)."""
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    (schemas_dir / "collide.json").write_text('{"required": ["x"]}')

    class _CollideCap(CapabilityBase):
        name = "collide_test"
        home = "memory"
        # Same name declared in BOTH places — must error.
        ontology = OntologyExtension(
            nodes={}, schemas={"collide": ["y"]})
        artefact_schemas = ArtefactSchemas(folder=schemas_dir)

        @verb(role="transform")
        def ping(self) -> dict:
            """Trivial.

            Inputs: none.
            Returns: ``{ok}``.
            chain_next: terminal.
            """
            return {"ok": True}

    with pytest.raises(ValueError, match=r"collide.*declared both"):
        Engine(tempfile.mktemp(suffix=".db"),
                extra_capabilities=[_CollideCap.as_capability()], _require_skill_doc=False)
