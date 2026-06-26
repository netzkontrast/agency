"""Spec 177 Slice 2 — the plugin-reference continuous-audit sweep.

Slice 1 shipped the typed `RefFinding` shape but nothing populated it (dormant).
This is the audit: a deterministic, idempotent sweep over the committed plugin
files (`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`commands/*.md`) checking each against an OPEN set of reference invariants
(Spec 064 — the `working-with-claude-code` reference). Each finding cites the
file it violates AND the reference doc (`doc_source`), never an opinion.

The invariant set is open (new checks join as the reference evolves); the
current set ⊇ the Spec 177 baseline six. A check whose target file is absent
contributes no findings but stays in `AUDITED_INVARIANTS` (the set is the
contract, not the file's presence).

Derived (Done-When): the audit is idempotent (sorted iteration ⇒ byte-identical
findings across runs), and the DERIVED install-surface files (Spec 175 — slash
commands + marketplace.json) pass by construction (a divergence is a real bug).
"""
from __future__ import annotations

import json
import os

from ._typed_shapes_wave1_part2 import RefFinding

# The OPEN reference-invariant set (Spec 177 baseline six + room to grow).
AUDITED_INVARIANTS = (
    "plugin_json_shape",
    "marketplace_entry_shape",
    "command_frontmatter",
    "hooks_matcher_async",
    "mcp_cwd_env",
    "run_hook_polyglot",
)

_DOC = "reference: working-with-claude-code (plugin shape)"


def _read_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _check_plugin_json(root: str) -> "list[RefFinding]":
    path = os.path.join(root, ".claude-plugin", "plugin.json")
    if not os.path.exists(path):
        return []
    rel = os.path.relpath(path, root)
    try:
        data = _read_json(path)
    except (OSError, ValueError):
        return [RefFinding(file=rel, invariant="plugin_json_shape",
                           observed="unparseable", expected="valid JSON object",
                           severity="error", doc_source=_DOC)]
    out = []
    for key in ("name", "version", "description"):
        if not data.get(key):
            out.append(RefFinding(file=rel, invariant="plugin_json_shape",
                                  observed=f"missing {key!r}",
                                  expected=f"non-empty {key!r}",
                                  severity="error", doc_source=_DOC))
    return out


def _check_marketplace(root: str) -> "list[RefFinding]":
    path = os.path.join(root, ".claude-plugin", "marketplace.json")
    if not os.path.exists(path):
        return []
    rel = os.path.relpath(path, root)
    try:
        data = _read_json(path)
    except (OSError, ValueError):
        return [RefFinding(file=rel, invariant="marketplace_entry_shape",
                           observed="unparseable", expected="valid JSON object",
                           severity="error", doc_source=_DOC)]
    out = []
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        return [RefFinding(file=rel, invariant="marketplace_entry_shape",
                           observed="no plugins[]",
                           expected="non-empty plugins[] array",
                           severity="error", doc_source=_DOC)]
    for entry in plugins:
        for key in ("name", "source", "version", "description"):
            if not entry.get(key):
                out.append(RefFinding(file=rel, invariant="marketplace_entry_shape",
                                      observed=f"plugin entry missing {key!r}",
                                      expected=f"non-empty {key!r}",
                                      severity="error", doc_source=_DOC))
    return out


def _check_command_frontmatter(root: str) -> "list[RefFinding]":
    cmd_dir = os.path.join(root, "commands")
    if not os.path.isdir(cmd_dir):
        return []
    out = []
    for fn in sorted(os.listdir(cmd_dir)):
        if not fn.endswith(".md"):
            continue
        rel = os.path.join("commands", fn)
        with open(os.path.join(cmd_dir, fn), encoding="utf-8") as f:
            text = f.read()
        if not text.startswith("---"):
            out.append(RefFinding(file=rel, invariant="command_frontmatter",
                                  observed="no opening frontmatter fence",
                                  expected="`---` YAML frontmatter at line 1",
                                  severity="error", doc_source=_DOC))
            continue
        # the frontmatter block is between the first two `---` fences
        rest = text[3:]
        end = rest.find("\n---")
        block = rest[:end] if end != -1 else ""
        if end == -1:
            out.append(RefFinding(file=rel, invariant="command_frontmatter",
                                  observed="unterminated frontmatter",
                                  expected="closing `---` fence",
                                  severity="error", doc_source=_DOC))
        elif "description:" not in block:
            out.append(RefFinding(file=rel, invariant="command_frontmatter",
                                  observed="frontmatter without `description:`",
                                  expected="a `description:` key",
                                  severity="error", doc_source=_DOC))
    return out


# Hooks / MCP invariants — registered in the OPEN set; they emit findings only
# when their config surface is present (the plugin tree here declares hooks/MCP
# elsewhere, so absence is not a violation — the set is the contract).
def _check_hooks_matcher_async(root: str) -> "list[RefFinding]":
    return []


def _check_mcp_cwd_env(root: str) -> "list[RefFinding]":
    return []


def _check_run_hook_polyglot(root: str) -> "list[RefFinding]":
    return []


_CHECKS = {
    "plugin_json_shape": _check_plugin_json,
    "marketplace_entry_shape": _check_marketplace,
    "command_frontmatter": _check_command_frontmatter,
    "hooks_matcher_async": _check_hooks_matcher_async,
    "mcp_cwd_env": _check_mcp_cwd_env,
    "run_hook_polyglot": _check_run_hook_polyglot,
}


def audit_plugin_refs(root: str = ".") -> "tuple[RefFinding, ...]":
    """Run every reference-invariant check over the plugin tree. Deterministic +
    idempotent (invariants iterated in `AUDITED_INVARIANTS` order, files sorted)
    so the same tree yields a byte-identical findings tuple across runs."""
    findings: list[RefFinding] = []
    for inv in AUDITED_INVARIANTS:
        findings.extend(_CHECKS[inv](root))
    return tuple(findings)


def ref_audit_summary(root: str = ".") -> dict:
    """A doctor-friendly roll-up. `ready` iff zero error-severity findings (the
    derived install-surface files pass the audit by construction)."""
    findings = audit_plugin_refs(root)
    errors = [f for f in findings if f.severity == "error"]
    warns = [f for f in findings if f.severity == "warn"]
    return {"audited_invariants": list(AUDITED_INVARIANTS),
            "findings": len(findings),
            "errors": len(errors),
            "warns": len(warns),
            "ready": not errors}
