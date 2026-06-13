#!/usr/bin/env python3
"""Phase B — generate a capability-indexed *living spec* from the REFACTORED code.

Rule 2 applied to specs: the spec's generated sections (Verbs / Ontology /
Skills) are DERIVED from the live registry, never hand-maintained — re-run to
refresh. The single authored section is ``## Why`` (intent / trade-offs the code
can't express); a per-pillar subagent fills it. Generated against the
post-286-refactor engine, so the surface reflects the clean four-pillar
architecture.

Usage:  python scripts/gen-living-spec.py <capability>|--all
Writes: Plan/living/<pillar>/<capability>.md
"""
from __future__ import annotations

import inspect
import sys
import tempfile
from datetime import date
from pathlib import Path

from agency.engine import Engine

# cap -> pillar (primary concept it completes; CORE.md §"Four complete pillars").
PILLAR = {
    "intent": "intent", "thinking": "intent", "dogfood": "intent",
    "reflect": "memory", "analyze": "memory", "research": "memory", "document": "memory",
    "plugin": "capability", "skill_generator": "capability", "skills": "capability",
    "prompt": "capability", "music": "capability", "novel": "capability",
    "develop": "lifecycle", "gate": "lifecycle", "delegate": "lifecycle",
    "subagent": "lifecycle", "jules": "lifecycle", "workspace": "lifecycle", "branch": "lifecycle",
}
_SKIP = {"self", "ctx", "intent_id", "agent_id"}


def _params(fn) -> str:
    try:
        sig = inspect.signature(fn)
    except (ValueError, TypeError):
        return ""
    out = []
    for n, p in sig.parameters.items():
        if n in _SKIP or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        req = p.default is inspect.Parameter.empty
        out.append(f"**{n}**" if req else n)
    return " · ".join(out)


def _purpose(fn) -> str:
    doc = (inspect.getdoc(fn) or "").strip()
    return doc.splitlines()[0] if doc else ""


def _cap_purpose(cap) -> str:
    """The capability's one-line purpose, from its derived ``skill_doc`` (which
    is itself derived from the capability's module docstring — rule 2), NOT the
    compiled ``Capability`` dataclass repr."""
    sd = getattr(cap, "skill_doc", None)
    if sd and getattr(sd, "overview", ""):
        return sd.overview.split(". ")[0].strip().rstrip(".")
    if sd and getattr(sd, "description", ""):
        return sd.description.strip().rstrip(".")
    return cap.name


def gen(cap_name: str, reg) -> str:
    cap = reg.get(cap_name)
    pillar = PILLAR.get(cap_name, "capability")
    ont = cap.ontology
    nodes = getattr(ont, "nodes", {}) or {}
    edges = getattr(ont, "edges", set()) or set()
    enums = getattr(ont, "enums", {}) or {}
    skills = sorted(getattr(cap, "walker_skills", {}) or {})

    L = [
        "---",
        f"capability: {cap_name}",
        f"pillar: {pillar}",
        "vision_goals: []        # TODO(why-author): which GOALS.md goals this serves",
        "status: living",
        f"last_generated: {date.today().isoformat()}",
        "sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this",
        "---",
        "",
        f"# {cap_name} — {_cap_purpose(cap)} ({pillar} pillar)",
        "",
        "## Why",
        "<!-- AUTHORED (the only hand-written section). The intent + trade-offs the",
        "     code can't express. A per-pillar subagent fills this from the archived",
        "     specs in sources:. Everything below is GENERATED — do not hand-edit. -->",
        "_TODO: authored intent._",
        "",
        f"## Verbs (generated · {len(cap.verbs)})",
        "",
        "| Verb | Role | Params (**required**) | Purpose |",
        "|---|---|---|---|",
    ]
    for v in sorted(cap.verbs):
        spec = cap.verbs[v]
        fn = spec.get("fn") if hasattr(spec, "get") else getattr(spec, "fn", None)
        role = spec.get("role") if hasattr(spec, "get") else getattr(spec, "role", "")
        L.append(f"| `{cap_name}.{v}` | {role} | {_params(fn)} | {_purpose(fn)} |")

    L += ["", "## Ontology (generated)", ""]
    if nodes:
        L.append("**Nodes:** " + " · ".join(f"`{n}`({', '.join(p)})" for n, p in nodes.items()))
    if edges:
        L.append("**Edges:** " + " · ".join(f"`{e}`" for e in sorted(edges)))
    if enums:
        L.append("**Enums:** " + " · ".join(f"`{k}` ∈ {{{', '.join(sorted(map(str, vs)))}}}" for k, vs in enums.items()))
    if not (nodes or edges or enums):
        L.append("_(no ontology extension)_")

    L += ["", "## Skills (generated)", ""]
    L.append(" · ".join(f"`{s}`" for s in skills) if skills else "_(no walkable skills)_")
    L += ["", "<!-- doc-source: agency/capabilities/" + cap_name + " -->", ""]
    return "\n".join(L)


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else "--all"
    eng = Engine(tempfile.mktemp(suffix=".db"))
    reg = eng.registry
    names = sorted(reg.names()) if arg == "--all" else [arg]
    root = Path("Plan/living")
    for name in names:
        pillar = PILLAR.get(name, "capability")
        out = root / pillar / f"{name}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(gen(name, reg))
        print(f"wrote {out}")
    eng.memory.close()


if __name__ == "__main__":
    main()
