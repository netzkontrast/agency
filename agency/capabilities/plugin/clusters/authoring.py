"""Authoring cluster — scaffolding + skill/command/marketplace/step-doc renders.

The pure template-render functions (no `self`, no `ctx`) live here as module
functions; `AuthoringMixin` carries the thin `@verb` wrappers. Behaviour and
signatures are verbatim from the pre-split `plugin._main`.
"""
from __future__ import annotations

import json

from ....capability import CapabilityBase, verb
from .... import templates

DEFAULT_TOOLS = "  - Read\n  - Write\n  - Edit"


def scaffold(name: str, version: str, description: str) -> dict:
    body = json.dumps(templates.manifest_obj(name, version, description), indent=2)
    return {"result": body, "artefact": {
        "kind": "plugin-manifest", "name": name, "version": version,
        "description": description, "body": body}}


def author_skill(name: str, description: str, body: str,
                 allowed_tools: str = DEFAULT_TOOLS, title: str | None = None) -> dict:
    # C1 (Codex review 6059c74 / templates.py:51) — same class of bug as the
    # description-escape fix: a name carrying a newline or YAML indicator chars
    # would inject frontmatter keys before lint_skill caught it. Defense in
    # depth — CSO kebab-case lint runs after, but the SKILL.md artefact must
    # never be rendered invalid in the first place.
    rendered = templates.SKILL_MD.substitute(
        name=templates._yaml_scalar(name),
        description=templates._yaml_scalar(description), body=body,
        allowed_tools=allowed_tools, title=title or name)
    return {"result": rendered, "artefact": {
        "kind": "skill-md", "name": name, "description": description, "body": rendered}}


def author_command(name: str, description: str, body: str) -> dict:
    rendered = templates.COMMAND_MD.substitute(
        description=templates._yaml_scalar(description), body=body)
    return {"result": rendered, "artefact": {
        "kind": "command-md", "name": name, "description": description, "body": rendered}}


def marketplace_entry(name: str, version: str, description: str, source: str) -> dict:
    body = json.dumps(templates.marketplace_obj(name, version, description, source), indent=2)
    return {"result": body, "artefact": {
        "kind": "marketplace-entry", "name": name, "version": version,
        "description": description, "source": source, "body": body}}


def step_doc(step: str, output: str, status: str = "done",
             inputs: str = "", notes: str = "") -> dict:
    rendered = templates.STEP_DOC.substitute(
        step=step, output=output, status=status, inputs=inputs, notes=notes)
    return {"result": rendered, "artefact": {
        "kind": "step-doc", "step": step, "output": output, "body": rendered}}


class AuthoringMixin(CapabilityBase):
    """Verbs that RENDER plugin artefacts (act-role; pure template substitution)."""

    @verb(role="act")
    def scaffold(self, name: str, version: str, description: str) -> dict:
        """Render the plugin scaffold (plugin.json + .mcp.json).

        Inputs: name (plugin slug), version (semver), description (str).
        Returns: ``{result: {plugin_json, mcp_json}}``.
        chain_next: write the rendered files; commit; install.
        """
        return scaffold(name, version, description)

    @verb(role="act")
    def author_skill(self, name: str, description: str, body: str) -> dict:
        """Render a CSO-compliant SKILL.md.

        Inputs: name (skill slug), description (trigger phrase), body (markdown).
        Returns: ``{result: <skill_md_str>}``.
        chain_next: ``plugin.lint_skill(name=, description=)`` then write.
        """
        return author_skill(name, description, body)

    @verb(role="act")
    def author_command(self, name: str, description: str, body: str) -> dict:
        """Render a slash-command markdown stub.

        Inputs: name (command name), description (str), body (markdown).
        Returns: ``{result: <command_md_str>}``.
        chain_next: write to ``commands/<name>.md``.
        """
        return author_command(name, description, body)

    @verb(role="act")
    def marketplace_entry(self, name: str, version: str, description: str, source: str) -> dict:
        """Render a marketplace.json entry.

        Inputs: name (plugin slug), version (semver), description (str),
                source (git URL or local path).
        Returns: ``{result: <entry_dict>}``.
        chain_next: merge into ``.claude-plugin/marketplace.json``.
        """
        return marketplace_entry(name, version, description, source)

    @verb(role="act")
    def step_doc(self, step: str, output: str, status: str = "done",
                 inputs: str = "", notes: str = "") -> dict:
        """Render a step-doc markdown block (audit trail entry).

        Inputs: step (title), output (deliverable), status (done|partial|skip),
                inputs (str, optional), notes (str, optional).
        Returns: ``{result: <markdown_str>}``.
        chain_next: append to the working step-doc file.
        """
        return step_doc(step, output, status, inputs, notes)
