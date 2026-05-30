"""The plugin-development capability — everything needed to develop a good plugin:
skill creation (TDD-for-docs, with the CSO rules enforced as compute) and
plugin/marketplace authoring, in the agency capability model.

A REAL capability (template rendering + rule-checking is real compute — it
mutates nothing external), role-tagged:

- `scaffold` (act)         — generate a Claude Code plugin manifest (`.claude-plugin/plugin.json`).
- `author_skill` (act)     — the *skill creator*: emit a SKILL.md (frontmatter + body).
- `author_command` (act)   — emit a slash-command markdown file.
- `marketplace_entry` (act)— emit a marketplace.json plugin entry.
- `step_doc` (act)         — prestructure one chain step's resulting document.
- `lint_skill` (transform) — the EXECUTABLE port of the writing-skills CSO rules:
                             validate a skill's name + description against the
                             "Use when…", hyphen-only-name, third-person, and
                             length rules. Judgment-as-code.
- `help` (transform)       — map the engine's capabilities (macroskills) to their
                             verbs (the harness-in-harness micro-skills): the
                             discovery surface a Claude Code plugin exposes as `help`.

Each `act` verb returns an `artefact` so the Registry records a PRODUCES edge —
the authored document is provenance, edged to the intent it SERVES.
"""
from __future__ import annotations

import json
import re

from ..capability import CapabilityBase, verb
from ..ontology import OntologyExtension
from .. import templates

DEFAULT_TOOLS = "  - Read\n  - Write\n  - Edit"
# kebab-case per the Agent Skills spec: lowercase letters/numbers/hyphens, no
# leading/trailing hyphen, no consecutive hyphens.
_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_FIRST_PERSON = re.compile(r"\b(I|I'll|I'm|my|me|we|we'll)\b", re.IGNORECASE)


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


def lint_skill(name: str, description: str) -> dict:
    """The writing-skills CSO rules + the Agent Skills spec limits, as enforceable
    compute. Returns the violations a baseline-tested human reviewer would flag —
    judgment ported (kebab-case ≤64 name; ≤1024 description; 'Use when…';
    third-person)."""
    v: list[str] = []
    if not _NAME_RE.match(name or ""):
        v.append("name must be kebab-case (lowercase letters, numbers, hyphens; "
                 "no leading/trailing or consecutive hyphen)")
    if len(name or "") > 64:
        v.append("name exceeds 64 chars")
    if not (description or "").lower().startswith("use when"):
        v.append("description must start with 'Use when…' (triggering conditions)")
    if _FIRST_PERSON.search(description or ""):
        v.append("description must be third person (no first-person pronouns)")
    if len(description or "") > 1024:
        v.append("description exceeds the 1024-char spec limit")
    elif len(description or "") > 500:
        v.append("description should be under 500 chars")
    return {"ok": not v, "violations": v}


def help_map(caps: dict) -> dict:
    """Map macroskills (capabilities) -> micro-skills (verbs). `caps` is the live
    registry view `{capability: [verb, ...]}`; the engine INJECTS it (the `inject`
    convention) so this verb stays pure. Returns a tiny doc + the structured map
    (token-efficient delta) under one `result` payload."""
    ordered = {k: sorted(caps[k]) for k in sorted(caps)}
    lines = ["# agency — capabilities (macroskills) and their verbs (micro-skills)", ""]
    for name, verbs in ordered.items():
        lines.append(f"- **{name}** — {', '.join(verbs)}")
    lines += [
        "",
        "## Discovery",
        "",
        "There is no separate 'remember to use the skill' layer — discovery IS the contract:",
        "",
        "- `search` finds a capability/verb or a discipline by symptom;",
        "- `get_schema` discloses just what you need (a verb's signature, a discipline's current phase);",
        "- `execute` runs it — and the run is recorded provenance (an Invocation, or a skill walk, that SERVES the intent).",
        "",
        "Walk a discipline one phase at a time (`develop.checklist` lists its steps); a hard gate halts until",
        "confirmed, and a phase bound to a verb EXECUTES rather than merely documents. Fetch a discipline's",
        "heavy how-to on demand with `develop.reference` (T3 progressive disclosure) — invoking a discipline IS",
        "the recorded walk, so there is nothing extra to remember.",
    ]
    return {"result": {"doc": "\n".join(lines) + "\n", "map": ordered}}


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
    schemas=dict(templates.REQUIRED),                    # the strict artefact schemas this capability generates
)

class PluginCapability(CapabilityBase):
    name = "plugin"
    home = "capability"
    ontology = plugin_ontology

    # the act verbs are pure template renders (module functions above); the class
    # methods are thin verb wrappers so the capability is authored in the class form.
    @verb(role="act")
    def scaffold(self, name: str, version: str, description: str) -> dict:
        return scaffold(name, version, description)

    @verb(role="act")
    def author_skill(self, name: str, description: str, body: str) -> dict:
        return author_skill(name, description, body)

    @verb(role="act")
    def author_command(self, name: str, description: str, body: str) -> dict:
        return author_command(name, description, body)

    @verb(role="act")
    def marketplace_entry(self, name: str, version: str, description: str, source: str) -> dict:
        return marketplace_entry(name, version, description, source)

    @verb(role="act")
    def step_doc(self, step: str, output: str, status: str = "done",
                 inputs: str = "", notes: str = "") -> dict:
        return step_doc(step, output, status, inputs, notes)

    @verb(role="transform")
    def lint_skill(self, name: str, description: str) -> dict:
        return lint_skill(name, description)

    @verb(role="transform")
    def help(self) -> dict:
        "Map the engine's capabilities (macroskills) to their verbs — via ctx.registry."
        caps = {n: list(self.ctx.registry.get(n).verbs) for n in self.ctx.registry.names()}
        return help_map(caps)
