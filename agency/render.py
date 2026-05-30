"""Adaptive disclosure renderer — Spec 023 Phase 1.

A pure rendering pass over Capability/Verb/Skill nodes. Takes the canonical
docstring (which Spec 016 Hint #7 already shapes) and emits a token-tight
slice keyed by (surface × depth × format).

`render_verb` is the single entry point for the verb-node case used by
`engine.search` and `engine.get_schema`. `parse_slices` is the docstring
cleaver — exposed for unit testing and for registration-time caching.

Surface (`mcp` / `bash`) governs example syntax (call_tool vs CLI). Most
verb prose is surface-agnostic; the renderer only differs at `format=snippet`
where the code-example syntax differs by harness.

Depth (`brief` / `standard` / `deep`):
- `brief`     — name + role + brief (the first-paragraph one-liner)
- `standard`  — brief + Inputs + Returns
- `deep`      — standard + chain_next + the rest of the docstring body

Format (`markdown` / `json` / `snippet`):
- `markdown`  — human-readable text
- `json`      — structured dict (caller serializes)
- `snippet`   — surface-appropriate code block

Non-Spec-016-Hint-#7-compliant docstrings (no `Inputs:` / `Returns:` /
`chain_next:` markers) fall back to brief-only at every depth; the omitted
markers do not render empty sections.
"""
from __future__ import annotations

import re
from typing import Any, Union


_INPUTS_RE = re.compile(r"^\s*Inputs:\s*(.+?)(?=^\s*(?:Returns:|chain_next:|$))",
                        re.MULTILINE | re.DOTALL)
_RETURNS_RE = re.compile(r"^\s*Returns:\s*(.+?)(?=^\s*(?:Inputs:|chain_next:|$))",
                         re.MULTILINE | re.DOTALL)
_CHAIN_RE = re.compile(r"^\s*chain_next:\s*(.+?)(?=^\s*(?:Inputs:|Returns:|$))",
                       re.MULTILINE | re.DOTALL)


def _clean(s: str) -> str:
    """Collapse whitespace; strip trailing punctuation-only lines."""
    return " ".join(s.split()).strip()


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z`(]|$)")


def _first_sentence(text: str) -> str:
    """First sentence-ish unit of `text`. Falls back to first line if no
    sentence terminator is found. The cleavage rule for `brief`."""
    cleaned = _clean(text)
    parts = _SENTENCE_END.split(cleaned, maxsplit=1)
    return parts[0]


def parse_slices(docstring: str) -> dict[str, str]:
    """Cleave a docstring into its Spec 016 Hint #7 slices.

    Returns: {brief, inputs, returns, chain_next, body}. Missing markers
    yield empty strings (never None — render-time absence == empty).

    `brief` is the FIRST SENTENCE of the docstring (Phase 7 refinement:
    Spec-016-Hint-#7-compliant docstrings have their lead-line as the
    gist, but legacy docstrings often run multiple sentences in the first
    paragraph — taking just the first sentence keeps the brief tight even
    on non-compliant docs, where the second sentence is usually elaboration
    that belongs in `body` / depth=deep)."""
    out = {"brief": "", "inputs": "", "returns": "", "chain_next": "", "body": ""}
    if not docstring:
        return out

    # brief = first sentence of the first paragraph
    first_para, _, rest = docstring.strip().partition("\n\n")
    out["brief"] = _first_sentence(first_para)

    if not rest:
        return out

    m = _INPUTS_RE.search(rest)
    if m:
        out["inputs"] = _clean(m.group(1))
    m = _RETURNS_RE.search(rest)
    if m:
        out["returns"] = _clean(m.group(1))
    m = _CHAIN_RE.search(rest)
    if m:
        out["chain_next"] = _clean(m.group(1))

    # body = everything in `rest` MINUS the marker blocks
    body = rest
    for pat in (_INPUTS_RE, _RETURNS_RE, _CHAIN_RE):
        body = pat.sub("", body)
    out["body"] = _clean(body)
    return out


# ---- format dispatch ------------------------------------------------------


def _render_markdown(name: str, role: str, slices: dict[str, str], depth: str) -> str:
    lines = [f"**{name}** _(role: {role})_", "", slices["brief"]]
    if depth in ("standard", "deep"):
        if slices["inputs"]:
            lines += ["", f"Inputs: {slices['inputs']}"]
        if slices["returns"]:
            lines += ["", f"Returns: {slices['returns']}"]
    if depth == "deep":
        if slices["chain_next"]:
            lines += ["", f"chain_next: {slices['chain_next']}"]
        if slices["body"]:
            lines += ["", slices["body"]]
    return "\n".join(lines)


def _render_json(name: str, role: str, slices: dict[str, str], depth: str) -> dict:
    out: dict[str, Any] = {"name": name, "role": role, "brief": slices["brief"]}
    if depth in ("standard", "deep"):
        if slices["inputs"]:
            out["inputs"] = slices["inputs"]
        if slices["returns"]:
            out["returns"] = slices["returns"]
    if depth == "deep":
        if slices["chain_next"]:
            out["chain_next"] = slices["chain_next"]
        if slices["body"]:
            out["body"] = slices["body"]
    return out


def _render_snippet(name: str, role: str, slices: dict[str, str], surface: str) -> str:
    """A paste-and-go invocation example, syntax matched to the surface."""
    inputs_hint = slices["inputs"] or "..."
    if surface == "mcp":
        body = (
            f'r = await call_tool("{name}", {{ {inputs_hint} }})\n'
            f"return r"
        )
        return f"```python\n{body}\n```"
    # bash
    body = (
        f'agency --db .agency/session.db execute --code \\\n'
        f'  "return await call_tool(\\"{name}\\", {{ {inputs_hint} }})"'
    )
    return f"```bash\n{body}\n```"


def render_verb(name: str,
                role: str,
                docstring: str,
                *,
                surface: str,
                depth: str,
                format: str) -> Union[str, dict]:
    """Render a single verb node per (surface, depth, format).

    Inputs: name (verb id), role (act|transform|effect), docstring, surface
            (mcp|bash), depth (brief|standard|deep), format (markdown|json|snippet).
    Returns: str for markdown/snippet; dict for json.
    chain_next: engine.search dispatches matches through this; install.py
                composes skill bodies via render(skill, ...) in Phase 8.
    """
    slices = parse_slices(docstring)
    if format == "json":
        return _render_json(name, role, slices, depth)
    if format == "snippet":
        return _render_snippet(name, role, slices, surface)
    return _render_markdown(name, role, slices, depth)
