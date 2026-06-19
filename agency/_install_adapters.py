"""Spec 327 — multi-agent self-installer.

One ``surface_card`` (derived from the live registry + the Spec 326 frugal
discipline) projected into each agent's native instruction format. Adapters are
pure ``card → files`` renderers; installs MERGE a fenced block so the user's
content is never clobbered (Spec 292 anchor pattern); each adapter succeeds or
fails independently (re-running is the recovery). The card is the SINGLE SOURCE —
the frugal discipline is imported from ``_frugal``, never re-authored (drift-gated).

Instruction files carry the **compact projection** — the discipline + entry
pointers (``agency search`` / ``agency <cap> <verb>`` / ``agency_welcome``), NOT
the full ~200-verb index (Goal 1; the agent discovers verbs on demand via the CLI,
exactly as an MCP client does via ``search``).
"""
from __future__ import annotations

import os

from . import _frugal

FENCE_START = "<!-- agency:auto:start -->"
FENCE_END = "<!-- agency:auto:end -->"

_BOOTSTRAP = ("If `agency` is not found: `pipx install "
              "git+https://github.com/netzkontrast/agency` "
              "(mirrors the SessionStart auto-install).")

# Wave 1 instruction-file agents. `claude` is the DEFAULT MCP path (handled in
# install_agents via install.write); Wave 2 MCP runtimes (Codex/Gemini/pi/
# opencode) are deferred to Spec 329.
INSTRUCTION_AGENTS = ("cursor", "windsurf", "cline", "kiro", "copilot", "agents")

_CURSOR_FRONT = ("---\n"
                 "description: agency — frugal discipline + the agency capability surface.\n"
                 "globs:\n"
                 "alwaysApply: true\n"
                 "---\n")
_KIRO_FRONT = "---\ntitle: agency\ninclusion: always\n---\n"

# Adapter → list of (relative path, fresh-file frontmatter). The body is shared;
# frontmatter is written only on a FRESH file (a merge preserves the user's).
_TARGETS: dict[str, list[tuple[str, str]]] = {
    "cursor":   [(".cursor/rules/agency.mdc", _CURSOR_FRONT)],
    "windsurf": [(".windsurf/rules/agency.md", "")],
    "cline":    [(".clinerules/agency.md", "")],
    "kiro":     [(".kiro/steering/agency.md", _KIRO_FRONT)],
    "copilot":  [(".github/copilot-instructions.md", ""), ("AGENTS.md", "")],
    "agents":   [("AGENTS.md", "")],
}


def surface_card(engine) -> dict:
    """The canonical descriptor every adapter projects from (single source)."""
    return {
        "frugal": _frugal.render(mode="full"),
        "bootstrap": _BOOTSTRAP,
        "capabilities": sorted(engine.registry.names()),
        "cli": "agency <cap> <verb>",
        "search": 'agency search "<task>"',
        "welcome": "agency_welcome",
    }


def _compact_body(card: dict) -> str:
    """The compact projection: the frugal discipline + entry pointers, never the
    full verb index (it lists capability NAMES, reached via the CLI on demand)."""
    caps = ", ".join(card["capabilities"])
    return (
        f"{card['bootstrap']}\n\n"
        f"# agency — frugal discipline + capability surface\n\n"
        f"{card['frugal']}\n\n"
        f"## Reaching agency (discover on demand — the full verb index is NOT inlined here)\n"
        f"- Discover: `{card['search']}` · `agency help`\n"
        f"- Run any verb: `{card['cli']}`\n"
        f"- Onboarding: `{card['welcome']}`\n"
        f"- Capabilities ({len(card['capabilities'])}): {caps}\n"
    )


def _fenced(body: str) -> str:
    return f"{FENCE_START}\n{body}\n{FENCE_END}"


def _merge(existing: str, body: str) -> str:
    """Replace the fenced agency block if present, else append a fresh one —
    never clobbering the user's surrounding content (Spec 292 anchor pattern)."""
    block = _fenced(body)
    if FENCE_START in existing and FENCE_END in existing:
        pre = existing.split(FENCE_START, 1)[0]
        post = existing.split(FENCE_END, 1)[1]
        return pre + block + post
    if existing.strip():
        return existing.rstrip() + "\n\n" + block + "\n"
    return block + "\n"


def _remove_block(existing: str) -> str:
    """Drop the fenced agency block, keep the user's surrounding content."""
    if FENCE_START not in existing or FENCE_END not in existing:
        return existing
    pre = existing.split(FENCE_START, 1)[0].rstrip()
    post = existing.split(FENCE_END, 1)[1].lstrip()
    joined = (pre + ("\n\n" if pre and post else "") + post).strip()
    return joined + "\n" if joined else ""


def install_agent(name: str, root: str, card: dict) -> list[str]:
    """Render + merge the compact projection into the agent's native file(s).
    Returns the relative paths written."""
    body = _compact_body(card)
    written: list[str] = []
    for rel, front in _TARGETS[name]:
        path = os.path.join(root, rel)
        existing = ""
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                existing = f.read()
        content = _merge(existing, body) if existing.strip() else front + _fenced(body) + "\n"
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(rel)
    return written


def install_agents(names, root: str, engine) -> dict:
    """Install each named agent INDEPENDENTLY — one failure never half-writes
    another (re-running is the idempotent recovery). Returns a per-adapter
    report ``{name: {ok, wrote|error}}``. ``claude`` delegates to the existing
    plugin install (``install.write``) so the card stays the single entry."""
    card = surface_card(engine)
    report: dict = {}
    for name in names:
        try:
            if name == "claude":
                from . import install as _install
                report[name] = {"ok": True, "wrote": _install.write(root)}
            else:
                report[name] = {"ok": True, "wrote": install_agent(name, root, card)}
        except Exception as exc:  # per-adapter isolation — report, never abort
            report[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return report


def uninstall_agents(names, root: str) -> dict:
    """Remove the agency fenced block from each agent's file(s); user content
    stays. Returns a per-adapter report."""
    report: dict = {}
    for name in names:
        if name == "claude":
            report[name] = {"ok": True, "removed": []}      # plugin uninstall is out of scope
            continue
        removed: list[str] = []
        try:
            for rel, _front in _TARGETS[name]:
                path = os.path.join(root, rel)
                if not os.path.exists(path):
                    continue
                with open(path, encoding="utf-8") as f:
                    existing = f.read()
                with open(path, "w", encoding="utf-8") as f:
                    f.write(_remove_block(existing))
                removed.append(rel)
            report[name] = {"ok": True, "removed": removed}
        except Exception as exc:
            report[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return report


def installed_agents(root: str) -> list[str]:
    """Which instruction agents have an agency block present (for the doctor)."""
    out: list[str] = []
    for name in INSTRUCTION_AGENTS:
        for rel, _front in _TARGETS[name]:
            path = os.path.join(root, rel)
            try:
                with open(path, encoding="utf-8") as f:
                    if FENCE_START in f.read():
                        out.append(name)
                        break
            except OSError:
                continue
    return out
