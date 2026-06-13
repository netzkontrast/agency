# agency-scaffold: v1
"""The plugin-development capability — everything needed to develop a good plugin:

Plugin ports the plugin-development craft into compute: scaffolds, skill and command authoring, marketplace entries, and the lint rules that enforce the authoring doctrine.

Use when: building or extending a Claude Code plugin — scaffolding a manifest, authoring a skill or command, or linting a capability against the authoring doctrine.
Triggers:
- A new plugin skill or command needing CSO-clean structure
- A capability that may violate the authoring doctrine
- A lint finding whose remedy is unclear
Red flags:
- Shipping a capability without linting → run capability_plugin_lint_capability
- Hand-writing a SKILL.md → render it via capability_plugin_author_skill
"""
from __future__ import annotations

from ...capability import ArtefactSchemas, CapabilityBase
from ...ontology import OntologyExtension

# Cluster mixins (Spec 286 P3) — PluginCapability is composed from these.
from .clusters import AuthoringMixin, LintMixin, PublishMixin, ReferenceMixin

# --- Re-exports: the symbols tests + substrate consumers import from this module.
# The heavy logic now lives in the cluster modules; these aliases preserve the
# pre-split `plugin._main.<symbol>` / `plugin.<symbol>` import surface.
from .clusters.authoring import (  # noqa: F401
    DEFAULT_TOOLS,
    author_command,
    author_skill,
    marketplace_entry,
    scaffold,
    step_doc,
)
from .clusters.reference import help_map  # noqa: F401
from .clusters.lint import (  # noqa: F401
    _REMEDIATION,
    _STANDING_ACCEPTS,
    _accepted_kinds,
    _check_reserved_names,
    _split_accepted,
    _tool_names,
    _with_remediation,
    lint_capability,
    lint_explain,
    lint_skill,
    lint_skill_doc,
    lint_surface,
)


# --- this capability's OWN ontology fragment (merged onto the core by the engine).
# The plugin-dev node types, its template-schemas, and its two skills live HERE,
# with the capability that owns them — not hard-wired into the core ontology.

# skill creation as TDD-for-docs. The Iron Law — "NO SKILL WITHOUT A FAILING TEST
# FIRST" — is ENFORCED by phase ordering: GREEN (authoring)
# is unreachable until RED produced its baseline. RED → GREEN → lint → REFACTOR →
# deploy(hard gate); GREEN + lint are bound to REAL verbs.
SKILL_CREATION_SKILL = {
    "name": "skill-creation",
    "kind": "authoring",
    "phases": [
        {"index": 1, "name": "red-baseline",
         "produces": ["baseline", "rationalizations"]},
        {"index": 2, "name": "green-author", "produces": ["skill_md"],
         "invoke": {"capability": "plugin", "verb": "author_skill"},
         "inputs": ["name", "description", "body"]},
        {"index": 3, "name": "lint", "produces": ["lint"],
         "invoke": {"capability": "plugin", "verb": "lint_skill"},
         "inputs": ["name", "description"]},
        {"index": 4, "name": "refactor",
         "produces": ["rationalization_table", "red_flags"]},
        {"index": 5, "name": "deploy", "produces": ["user_confirmed"], "gate": "hard"},
    ],
}

# the complete plugin-authoring chain: each phase emits a prestructured document.
PLUGIN_DEV_SKILL = {
    "name": "plugin-dev",
    "kind": "authoring",
    "phases": [
        {"index": 1, "name": "manifest", "produces": ["manifest"],
         "invoke": {"capability": "plugin", "verb": "scaffold"},
         "inputs": ["name", "version", "description"]},
        {"index": 2, "name": "skill", "produces": ["skill_md"],
         "invoke": {"capability": "plugin", "verb": "author_skill"},
         "inputs": ["name", "description", "body"]},
        {"index": 3, "name": "command", "produces": ["command_md"],
         "invoke": {"capability": "plugin", "verb": "author_command"},
         "inputs": ["name", "description", "body"]},
        {"index": 4, "name": "marketplace", "produces": ["entry"],
         "invoke": {"capability": "plugin", "verb": "marketplace_entry"},
         "inputs": ["name", "version", "description", "source"]},
        {"index": 5, "name": "confirm", "produces": ["user_confirmed"], "gate": "hard"},
    ],
}

plugin_ontology = OntologyExtension(
    nodes={
        "Plugin":  ["name", "version", "description"],   # a Claude Code plugin manifest
        "Command": ["name", "description"],              # a slash command
    },
    skills={"skill-creation": SKILL_CREATION_SKILL, "plugin-dev": PLUGIN_DEV_SKILL},
    # Spec 060 — schemas migrated from `templates.REQUIRED` Python dict
    # to file-based `plugin/schemas/*.json` declarations. The engine's
    # `load_capability_folders` discovers them at bootstrap and merges
    # them into this OntologyExtension's `schemas` dict before
    # `Ontology.extend` runs.
)


class PluginCapability(AuthoringMixin, LintMixin, PublishMixin, ReferenceMixin,
                       CapabilityBase):
    """The plugin-development capability — ONE registered capability composed from
    four cluster mixins (authoring / lint / publish / reference) via multiple
    inheritance (Spec 286 P3). The verbs are carried by the mixins verbatim; the
    capability declares the shared identity + ontology + skill_doc source (this
    module's docstring).
    """
    name = "plugin"
    home = "capability"
    artefact_schemas = ArtefactSchemas.from_module(__file__)
    ontology = plugin_ontology
