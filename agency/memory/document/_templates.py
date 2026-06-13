"""Markdown rendering primitives shared across render scopes.

Each render scope owns its own template function in ``_render.py``;
this module exposes the LOW-LEVEL builders (H1/H2 headers, fenced
code blocks, markdown tables) so the template code stays declarative.
"""
from __future__ import annotations


def h1(text: str) -> str:
    return f"# {text}\n"


def h2(text: str) -> str:
    return f"\n## {text}\n"


def fenced(body: str, lang: str = "") -> str:
    return f"\n```{lang}\n{body.rstrip()}\n```\n"


def italic_footer(text: str) -> str:
    return f"\n*{text}*\n"


def table(headers: list[str], rows: list[list[str]]) -> str:
    """Render a GitHub-flavoured markdown table. Columns separated by
    ``|``; first row is headers; second row is the ``---`` separator."""
    if not headers:
        return ""
    head = "| " + " | ".join(headers) + " |\n"
    sep = "| " + " | ".join(["---"] * len(headers)) + " |\n"
    body = "".join(
        "| " + " | ".join(str(c) for c in row) + " |\n" for row in rows
    )
    return "\n" + head + sep + body


def truncate(text: str, limit: int) -> str:
    """Truncate ``text`` to ``limit`` chars with an ellipsis marker."""
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"
