"""Shared file-walking helpers for the analyze axes (DRY).

Every axis (_quality, _security, _performance, _architecture) needs
the same: walk a tree for ``.py`` files (skipping ``__pycache__``,
``.venv``, ``.git``, etc.), and read each file safely. Extracting here
keeps the per-axis modules focused on their lint logic.
"""
from __future__ import annotations

import os


_PRUNE_DIRS = frozenset({
    "__pycache__", ".venv", ".git", ".pytest_cache", "node_modules",
})


def python_files(root: str) -> list[str]:
    """Walk ``root`` for Python source files. Prunes common non-source
    dirs. ``root`` may be a single .py file (treated as a 1-element list)."""
    if os.path.isfile(root) and root.endswith(".py"):
        return [root]
    out: list[str] = []
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _PRUNE_DIRS]
        for f in files:
            if f.endswith(".py"):
                out.append(os.path.join(dirpath, f))
    return out


def read_text(path: str) -> str | None:
    """Read a file's text; return None on I/O or decode error (so the
    scanner can skip without raising)."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None
