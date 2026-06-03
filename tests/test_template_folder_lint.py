"""Spec 060 Phase 4 — `_check_template_folder` lint rule.

Doctrine bar (Spec 060 §"Templates instruct agents"): every template
shipped under a capability's `templates/` folder MUST carry at least
one `<!-- AGENT: ... -->` instruction block. Pure-rendering templates
belong in `agency/render/` (engine scope), not under a capability.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agency.capability import (
    ArtefactSchemas,
    CapabilityBase,
    OntologyExtension,
    RenderTemplates,
    verb,
)
from agency.capabilities.plugin import lint_capability


def _make_cap(name: str, folder: Path) -> type:
    class _Cap(CapabilityBase):
        pass
    _Cap.name = name
    _Cap.home = "memory"
    _Cap.ontology = OntologyExtension(nodes={})
    _Cap.render_templates = RenderTemplates(folder=folder)

    @verb(role="transform")
    def ping(self) -> dict:
        """Trivial.

        Inputs: none.
        Returns: ``{ok}``.
        chain_next: terminal.
        """
        return {"ok": True}
    _Cap.ping = ping
    return _Cap


def test_lint_passes_when_all_templates_carry_agent_block(tmp_path):
    tpls = tmp_path / "templates"
    tpls.mkdir()
    (tpls / "greeting.md").write_text(
        "# Hello\n<!-- AGENT: greet warmly -->\n")
    cap = _make_cap("tpl_good", tpls).as_capability()
    out = lint_capability(cap)
    findings = [v for v in (out["violations"] + out["warnings"])
                if v.get("kind") == "template_folder"]
    assert findings == [], f"good cap tripped template_folder: {findings}"


def test_lint_flags_template_without_agent_block(tmp_path):
    tpls = tmp_path / "templates"
    tpls.mkdir()
    (tpls / "silent.md").write_text("# Hello world\n")
    cap = _make_cap("tpl_silent", tpls).as_capability()
    out = lint_capability(cap)
    findings = [v for v in (out["violations"] + out["warnings"])
                if v.get("kind") == "template_folder"]
    assert findings, "template without <!-- AGENT: --> must trip the rule"
    assert any("silent.md" in v["verb"] for v in findings)


def test_lint_flags_non_kebab_filename(tmp_path):
    tpls = tmp_path / "templates"
    tpls.mkdir()
    (tpls / "BadName.md").write_text(
        "# x\n<!-- AGENT: do thing -->\n")
    cap = _make_cap("tpl_bad_kebab", tpls).as_capability()
    out = lint_capability(cap)
    findings = [v for v in (out["violations"] + out["warnings"])
                if v.get("kind") == "template_folder"
                and "kebab-case" in v["msg"]]
    assert findings


def test_lint_flags_missing_folder(tmp_path):
    missing = tmp_path / "does_not_exist"
    cap = _make_cap("tpl_missing", missing).as_capability()
    out = lint_capability(cap)
    findings = [v for v in (out["violations"] + out["warnings"])
                if v.get("kind") == "template_folder"
                and "does not exist" in v["msg"]]
    assert findings


def test_lint_silent_when_cap_has_no_render_templates(tmp_path):
    """A capability without `render_templates` is back-compat; rule
    must NOT fire (most caps in the tree are still this shape)."""
    class _NoTpl(CapabilityBase):
        name = "tpl_none"
        home = "memory"
        ontology = OntologyExtension(nodes={})

        @verb(role="transform")
        def ping(self) -> dict:
            """Trivial.

            Inputs: none.
            Returns: ``{ok}``.
            chain_next: terminal.
            """
            return {"ok": True}
    out = lint_capability(_NoTpl.as_capability())
    findings = [v for v in (out["violations"] + out["warnings"])
                if v.get("kind") == "template_folder"]
    assert findings == []
