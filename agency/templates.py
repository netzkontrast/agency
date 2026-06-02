"""Templates — the prestructure for the resulting document of each step of a chain.

A small library of *living document* skeletons a Capability `act` fills in. A
Template pairs with a
strict Schema (`REQUIRED`) — the generate/validate layer from CORE: a Capability
generates an Artefact `DERIVED_FROM` a Template that `VALIDATES_AGAINST` its
Schema. Markdown docs use `string.Template` (`$field`, brace-safe for bodies
that contain `{}`); the JSON plugin manifest is generated structurally
(`manifest_obj`) so it is always valid JSON.
"""
from __future__ import annotations

from pathlib import Path as _Path
from string import Template
from urllib.parse import urlparse

_RENDER_DIR = _Path(__file__).parent / "render"


def _load_render_template(name: str) -> Template:
    """Load a template body from agency/render/<name> as a string.Template.

    Spec 032 §H — engine-owned templates live as files in agency/render/.
    """
    path = _RENDER_DIR / name
    return Template(path.read_text())


def _yaml_scalar(s: str) -> str:
    """Return a YAML 1.2 single-line scalar safe to splice into frontmatter.

    Leaves CSO-clean descriptions (e.g. `Use when …`) as PLAIN scalars
    untouched; only single-quotes when the value carries characters that would
    actually break frontmatter parsing — newlines collapsed to a space, leading
    YAML indicator chars, `: ` (key indicator) or ` #` (comment indicator),
    edge whitespace. Doubles internal `'` per YAML spec."""
    text = (s or "").replace("\n", " ").replace("\r", " ")
    if not text:
        return "''"
    unsafe = (
        text[0] in "!&*[]{}|>'\"#%@`?-:," or text[0].isspace()
        or text[-1].isspace()
        or ": " in text or " #" in text
    )
    if not unsafe:
        return text
    return "'" + text.replace("'", "''") + "'"


def _github_repo(source: str) -> str | None:
    """`owner/repo` iff `source` is a real github.com URL (parsed by hostname, not a
    substring — so `github.com.evil.tld` is NOT treated as GitHub). Else None."""
    u = urlparse(source)
    if u.scheme not in ("http", "https") or u.hostname not in ("github.com", "www.github.com"):
        return None
    path = u.path.strip("/")
    return (path[:-4] if path.endswith(".git") else path) or None

# Backwards-compat re-exports: bodies live in agency/render/ as files
# (Spec 032 §H). Loaded on import so module-level
# `from agency.templates import SKILL_MD` keeps working.
#
# - SKILL_MD: a Claude Code SKILL.md — frontmatter + body. This is what the
#   *skill creator* emits; it is the unit a plugin ships.
# - COMMAND_MD: a Claude Code slash command — frontmatter (description) +
#   the prompt body.
# - STEP_DOC: the prestructured *step document*: one chain step's result as
#   a living doc (inputs it consumed, the output it produced, notes),
#   generalized to any chain step.
SKILL_MD = _load_render_template("skill-md.tpl")
COMMAND_MD = _load_render_template("command-md.tpl")
STEP_DOC = _load_render_template("step-doc.md")

# Strict required-field schema per template kind (the validate side of the
# generate/validate pair). Recorded as a Schema node powers `validate_schema`.
REQUIRED: dict[str, list[str]] = {
    "plugin-manifest": ["name", "version", "description"],
    "skill-md": ["name", "description", "body"],
    "command-md": ["name", "description", "body"],
    "marketplace-entry": ["name", "version", "description", "source"],
    "step-doc": ["step", "output"],
}


def manifest_obj(name: str, version: str, description: str) -> dict:
    """The canonical `.claude-plugin/plugin.json` shape (Claude Code install
    descriptor). Generated structurally so the artefact is always valid JSON.
    Per the plugin spec: `author` is an OBJECT, `keywords` an ARRAY, and component
    paths are relative and start with `./`."""
    return {
        "name": name,
        "version": version,
        "description": description,
        "author": {"name": "agency"},
        "keywords": ["agency", "code-mode", "capabilities"],
        "skills": "./skills/",
        "commands": "./commands/",
    }


def marketplace_obj(name: str, version: str, description: str, source: str) -> dict:
    """One entry of a Claude Code `marketplace.json` `plugins` array. Per the
    marketplace schema `source` is a relative-path string OR a github object. A
    plain path (`./local`, `plugins/foo`, `owner/repo`) is kept verbatim as a
    string; only a github URL is normalised to `{source: github, repo}` (the
    ambiguous bare `owner/repo` is treated as a path, never auto-github'd)."""
    repo = _github_repo(source) if isinstance(source, str) else None
    src = {"source": "github", "repo": repo} if repo else source
    return {"name": name, "version": version, "description": description, "source": src}
