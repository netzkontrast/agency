"""``document.explain`` — code → educational text via composition.

NO LLM. The 'education' comes from arranging deterministic features:
signature, brief slice, ast-walked call sites, semantic-recall hits.
See Spec 043 §"Explain is composition, not generation".
"""
from __future__ import annotations

import ast
import importlib
import inspect
import os
from typing import Any


# Budgets per depth (cl100k tokens). Implementation truncates at chars
# (~4 chars/token average) when no tiktoken is available.
_DEPTH_BUDGETS = {"brief": 200, "standard": 600, "deep": 2500}
_CHAR_PER_TOKEN = 4   # coarse fallback when tiktoken not yet imported


def _resolve(target: str) -> tuple[str, Any]:
    """Return (kind, obj) for ``target``. kind ∈ {file, module, symbol}.

    - 'agency/capabilities/x.py' → (file, AST)
    - 'agency.capabilities.x'    → (module, module object)
    - 'agency.capabilities.x.f'  → (symbol, function/class)
    """
    if os.path.isfile(target) and target.endswith(".py"):
        with open(target, encoding="utf-8") as fh:
            src = fh.read()
        return "file", (target, src, ast.parse(src))
    # Try module-import path.
    try:
        mod = importlib.import_module(target)
        return "module", mod
    except ImportError:
        pass
    # Try module.symbol form.
    if "." in target:
        mod_path, _, sym = target.rpartition(".")
        try:
            mod = importlib.import_module(mod_path)
            if hasattr(mod, sym):
                return "symbol", getattr(mod, sym)
        except ImportError:
            pass
    raise ValueError(f"cannot resolve target {target!r}")


def _signature(obj) -> str:
    """``inspect.signature`` with a graceful fallback."""
    try:
        return f"{obj.__name__}{inspect.signature(obj)}"
    except (ValueError, TypeError):
        return getattr(obj, "__name__", str(obj))


def _brief_doc(obj) -> str:
    """First sentence of ``obj``'s docstring (Spec 023 brief)."""
    doc = inspect.getdoc(obj) or ""
    if not doc:
        return ""
    # First sentence — same heuristic as agency/disclosure.py's first
    # sentence (period-terminated or first line).
    for end in (". ", ".\n", ".\t"):
        if end in doc:
            return doc.split(end, 1)[0].strip() + "."
    return doc.splitlines()[0].strip()


def _render_file(target_tuple) -> dict:
    """Render kind=file: walk top-level defs + their briefs."""
    path, src, tree = target_tuple
    parts = [f"# {os.path.basename(path)}\n\n"]
    # Module-level docstring's brief.
    if (tree.body and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        first_sent = tree.body[0].value.value.strip().split(".", 1)[0]
        parts.append(f"_{first_sent}._\n\n")
    parts.append("## Top-level definitions\n\n")
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parts.append(f"- **{node.name}** (function, line {node.lineno})\n")
        elif isinstance(node, ast.ClassDef):
            parts.append(f"- **{node.name}** (class, line {node.lineno})\n")
    return {"content": "".join(parts)}


def _render_symbol(obj) -> dict:
    """Render kind=symbol: signature + brief + body sketch."""
    parts = [f"# `{getattr(obj, '__name__', str(obj))}`\n\n"]
    parts.append(f"**Signature:** `{_signature(obj)}`\n\n")
    brief = _brief_doc(obj)
    if brief:
        parts.append(f"**Brief:** {brief}\n\n")
    # Add docstring at standard/deep depths (caller truncates by budget).
    full_doc = inspect.getdoc(obj) or ""
    if full_doc and full_doc != brief:
        parts.append(f"**Docstring:**\n\n{full_doc}\n\n")
    return {"content": "".join(parts)}


def _render_module(mod) -> dict:
    """Render kind=module: brief + list of public callables/classes."""
    parts = [f"# `{mod.__name__}`\n\n"]
    brief = _brief_doc(mod)
    if brief:
        parts.append(f"_{brief}_\n\n")
    parts.append("## Public surface\n\n")
    for name in sorted(getattr(mod, "__all__", None) or [
            n for n in dir(mod) if not n.startswith("_")]):
        obj = getattr(mod, name, None)
        if obj is None:
            continue
        kind = "class" if inspect.isclass(obj) else (
            "function" if inspect.isfunction(obj) or inspect.ismethod(obj) else "value")
        b = _brief_doc(obj)
        parts.append(f"- **{name}** _({kind})_ — {b}\n" if b
                     else f"- **{name}** _({kind})_\n")
    return {"content": "".join(parts)}


def explain(target: str, depth: str = "standard") -> dict:
    """Deterministic code → markdown explanation.

    Inputs: ``target`` (file path | module | module.symbol),
            ``depth`` ∈ {brief, standard, deep}.
    Returns: ``{content, tokens}``. ``content`` is markdown; ``tokens``
    is the approximate cl100k count (char//4 fallback when tiktoken
    isn't importable in the running env).
    """
    budget = _DEPTH_BUDGETS.get(depth, _DEPTH_BUDGETS["standard"])
    char_budget = budget * _CHAR_PER_TOKEN
    kind, payload = _resolve(target)
    if kind == "file":
        out = _render_file(payload)
    elif kind == "module":
        out = _render_module(payload)
    else:  # symbol
        out = _render_symbol(payload)
    content = out["content"]
    # Brief drops everything past the first H1+section; deep returns full.
    if depth == "brief":
        # Keep only the first paragraph block after the H1 title.
        head, _, _ = content.partition("\n## ")
        content = head.rstrip() + "\n"
    # Enforce char budget (a generous proxy for token budget).
    if len(content) > char_budget:
        content = content[:char_budget - 1] + "…"
    return {
        "content": content,
        "tokens": _count_tokens(content),
    }


def _count_tokens(text: str) -> int:
    """Spec 082 — route through the ONE token-count boundary (count_tokens →
    tiktoken → proxy) instead of a duplicated inline tiktoken-else-proxy helper."""
    from ..._tokens import count_tokens
    return count_tokens(text)
