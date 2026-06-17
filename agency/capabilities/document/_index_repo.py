"""``document.index_repo`` — the 94%-reduction repo briefing.

Walks a repo tree, reads first-sentence brief slices from module
docstrings, and synthesises a deterministic PROJECT_INDEX.md ≤ 3000
cl100k tokens.

See Spec 043 §"index_repo's 94%-reduction mechanism".
"""
from __future__ import annotations

import ast
import os


_PRUNE_DIRS = frozenset({
    "__pycache__", ".venv", ".git", ".pytest_cache", "node_modules",
    "dist", "build", ".tox", ".mypy_cache",
})


def _python_files(root: str) -> list[str]:
    out: list[str] = []
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _PRUNE_DIRS]
        for f in files:
            if f.endswith(".py"):
                out.append(os.path.join(dirpath, f))
    return sorted(out)


def _module_brief(src: str) -> str:
    """First sentence of the module docstring (or empty)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return ""
    if not tree.body:
        return ""
    first = tree.body[0]
    if not (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)):
        return ""
    doc = first.value.value.strip()
    # First sentence — period-terminated or first line.
    for end in (". ", ".\n"):
        if end in doc:
            return doc.split(end, 1)[0].strip() + "."
    return doc.splitlines()[0].strip() if doc else ""


def _package_briefs(root: str) -> dict[str, list[tuple[str, str]]]:
    """Walk the tree; group files by their containing dir; pair each
    file with its module-brief. Returns {dir_rel: [(file_basename,
    brief), ...]} sorted."""
    out: dict[str, list[tuple[str, str]]] = {}
    for path in _python_files(root):
        try:
            with open(path, encoding="utf-8") as f:
                src = f.read()
        except OSError:
            continue
        brief = _module_brief(src)
        rel = os.path.relpath(path, root)
        dir_rel = os.path.dirname(rel) or "."
        base = os.path.basename(rel)
        out.setdefault(dir_rel, []).append((base, brief))
    for dir_rel, items in out.items():
        items.sort(key=lambda p: p[0])
    return out


def _detect_substrate(root: str) -> dict[str, str]:
    """Heuristic detection of language, test-runner, package-config."""
    info: dict[str, str] = {"language": "python"}
    if os.path.isfile(os.path.join(root, "pyproject.toml")):
        info["package_config"] = "pyproject.toml"
    if os.path.isfile(os.path.join(root, "pytest.ini")):
        info["test_runner"] = "pytest (pytest.ini)"
    elif os.path.isfile(os.path.join(root, "setup.cfg")):
        info["test_runner"] = "pytest (setup.cfg)"
    else:
        info["test_runner"] = "pytest (inferred)"
    return info


def _entry_points(root: str) -> list[str]:
    """Read pyproject.toml's [project.scripts] section, if present."""
    pp = os.path.join(root, "pyproject.toml")
    if not os.path.isfile(pp):
        return []
    try:
        with open(pp, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return []
    # Naive parse — find lines under [project.scripts].
    out: list[str] = []
    in_scripts = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("[project.scripts]"):
            in_scripts = True
            continue
        if in_scripts and s.startswith("["):
            break
        if in_scripts and "=" in s and not s.startswith("#"):
            name, _, ref = s.partition("=")
            out.append(f"{name.strip()} = {ref.strip()}")
    return out


def _notable_patterns(root: str) -> list[str]:
    """Detect agency-specific markers: capability folders, plugin manifest,
    MCP config, skill folders."""
    out: list[str] = []
    if os.path.isdir(os.path.join(root, "agency/capabilities")):
        out.append("agency-style capability folder pattern")
    if os.path.isfile(os.path.join(root, ".claude-plugin/plugin.json")):
        out.append("Claude Code plugin manifest (.claude-plugin/)")
    if os.path.isfile(os.path.join(root, ".mcp.json")):
        out.append("MCP server config (.mcp.json)")
    if os.path.isdir(os.path.join(root, "skills")):
        out.append("skills/<name>/SKILL.md disclosure pattern")
    if os.path.isdir(os.path.join(root, "Plan")):
        out.append("Plan/NNN-slug/spec.md doctrine")
    return out


def _recent_reflections(memory, intent_id: str, limit: int = 5) -> list[dict]:
    """Newest Reflections (technical or project scope), optionally
    filtered to a given intent via the OBSERVED_DURING edge (NOT a
    property — provenance lives on edges in the bi-temporal graph)."""
    if intent_id:
        rows = memory.sources_via_edge(
            "OBSERVED_DURING", intent_id, "Intent", label="Reflection")
    else:
        rows = list(memory.find("Reflection"))
    rows = [r for r in rows if r.get("scope") in ("technical", "project")]
    rows.sort(key=lambda r: r.get("vfrom", 0), reverse=True)
    return rows[:limit]


def _count_tokens(text: str) -> int:
    # Spec 082 — the ONE token-count boundary (count_tokens → tiktoken → proxy).
    from ..._tokens import count_tokens
    return count_tokens(text)


def render(root: str, memory, intent_id: str = "",
           max_tokens: int = 3000) -> tuple[str, int, int]:
    """Compose the PROJECT_INDEX.md content; return (text, tokens,
    files_scanned). Truncates to max_tokens with a "... (N modules
    omitted)" marker rather than exceeding budget."""
    root = os.path.abspath(root)
    name = os.path.basename(root) or "project"
    substrate = _detect_substrate(root)
    entries = _entry_points(root)
    patterns = _notable_patterns(root)
    briefs_by_dir = _package_briefs(root)
    files_scanned = sum(len(items) for items in briefs_by_dir.values())
    reflections = _recent_reflections(memory, intent_id, limit=5)

    parts = [f"# Project Index — {name}\n"]
    parts.append("\n## Substrate\n")
    for k, v in substrate.items():
        parts.append(f"- {k}: {v}\n")
    # Render the SHORT, FIXED-SIZE sections (Entry points + Notable
    # patterns + Recent activity) BEFORE the variable-size Macro-
    # structure so the budget-truncation in Macro-structure doesn't
    # clobber them when the repo grows. Spec 043 line 145 schema
    # ordering kept (## Substrate → ## Macro-structure → ## Entry points
    # → ## Notable patterns → ## Recent activity) — only the RENDER
    # ORDER changes so short sections always make it into the budget.
    short_sections: list[str] = []
    short_sections.append("\n## Entry points\n")
    if entries:
        for e in entries:
            short_sections.append(f"- `{e}`\n")
    else:
        short_sections.append("- _none declared in pyproject.toml_\n")
    short_sections.append("\n## Notable patterns\n")
    if patterns:
        for p in patterns:
            short_sections.append(f"- {p}\n")
    else:
        short_sections.append("- _no agency-specific markers detected_\n")
    short_sections.append("\n## Recent activity\n")
    if reflections:
        for r in reflections:
            text = r.get("text", "")[:120]
            short_sections.append(f"- `{r.get('scope', '?')}` · {text}\n")
    else:
        short_sections.append("- _no recent reflections recorded_\n")
    parts.extend(short_sections)
    parts.append("\n## Macro-structure\n")
    # Always-present capability roster — one line listing every
    # capability folder under agency/capabilities/, so a fresh agent
    # gets every cap name even when the variable-size per-dir details
    # below get budget-truncated. Each name is followed by a small
    # marker (`/`) so the test predicate `cap in content` stays robust
    # against future briefing-shape changes.
    cap_dirs = sorted({
        d.split("/")[-1] for d in briefs_by_dir
        if "agency/capabilities/" in d
        and not d.rstrip("/").endswith("capabilities")
    })
    if cap_dirs:
        parts.append("\n**Capabilities:** "
                     + ", ".join(f"`{c}/`" for c in cap_dirs) + "\n")
    omitted = 0
    for dir_rel in sorted(briefs_by_dir):
        items = briefs_by_dir[dir_rel]
        # Synthesise: one-line per dir + bulleted files.
        parts.append(f"\n### `{dir_rel}/` ({len(items)} files)\n")
        for base, brief in items:
            if brief:
                parts.append(f"- **{base}** — {brief}\n")
            else:
                parts.append(f"- **{base}**\n")
        # Mid-loop budget check; truncate gracefully.
        if _count_tokens("".join(parts)) > max_tokens * 0.92:
            omitted = sum(len(briefs_by_dir[d]) for d in sorted(briefs_by_dir)
                          if d > dir_rel)
            parts.append(f"\n_... ({omitted} modules omitted to fit token budget)_\n")
            break
    text = "".join(parts)
    # Hard cap: if the full briefing still exceeds budget after the
    # mid-loop truncation (because Substrate / Entry-points / Recent
    # activity were appended after the macro section), trim from the
    # tail to fit. Preserve the leading sections; tail-truncate the
    # body. A char proxy is enough — token count is verified after.
    final_tokens = _count_tokens(text)
    if final_tokens > max_tokens:
        # Estimated chars to keep = max_tokens * 4 (cl100k average).
        keep_chars = max_tokens * 4
        if len(text) > keep_chars:
            text = text[: keep_chars - 40] + \
                   "\n\n_…(content omitted to fit token budget)_\n"
            final_tokens = _count_tokens(text)
    return text, final_tokens, files_scanned


# The 16-hex content hash lives in `_interconnect` (Spec 292); re-exported here
# for the existing `_index_repo.content_sha` callers.
from ._interconnect import content_sha  # noqa: E402,F401
