"""Spec 177 Slice 2 — plugin-reference continuous-audit invariants.

`audit_plugin_refs` sweeps the committed plugin files against an open set of
reference invariants, producing typed `RefFinding`s. The live install-surface
files pass by construction; a malformed file trips its invariant.
"""
from __future__ import annotations

from agency._plugin_ref_audit import (AUDITED_INVARIANTS, audit_plugin_refs,
                                      ref_audit_summary)
from agency._typed_shapes_wave1_part2 import RefFinding


def test_audited_invariants_superset_of_the_baseline_six():
    baseline = {"plugin_json_shape", "hooks_matcher_async", "mcp_cwd_env",
                "run_hook_polyglot", "command_frontmatter",
                "marketplace_entry_shape"}
    assert set(AUDITED_INVARIANTS) >= baseline


def test_live_plugin_tree_passes_the_audit():
    # the derived install-surface files (Spec 175) pass by construction
    summ = ref_audit_summary(".")
    assert summ["errors"] == 0
    assert summ["ready"] is True


def test_audit_is_idempotent():
    # same tree + same reference ⇒ byte-identical findings across runs
    assert audit_plugin_refs(".") == audit_plugin_refs(".")


def test_findings_are_typed_and_cite_a_doc_source(tmp_path):
    # a malformed command file trips command_frontmatter with severity=error
    (tmp_path / "commands").mkdir()
    (tmp_path / "commands" / "agency-bad.md").write_text("no frontmatter here\n")
    findings = audit_plugin_refs(str(tmp_path))
    assert findings and all(isinstance(f, RefFinding) for f in findings)
    bad = [f for f in findings if f.invariant == "command_frontmatter"]
    assert bad and bad[0].severity == "error"
    assert bad[0].doc_source                      # cites the reference doc


def test_missing_plugin_json_field_is_flagged(tmp_path):
    import json
    plugdir = tmp_path / ".claude-plugin"
    plugdir.mkdir()
    (plugdir / "plugin.json").write_text(json.dumps({"name": "x"}))  # no version/description
    findings = audit_plugin_refs(str(tmp_path))
    invs = {f.invariant for f in findings}
    assert "plugin_json_shape" in invs
    assert all(f.severity == "error" for f in findings
               if f.invariant == "plugin_json_shape")
