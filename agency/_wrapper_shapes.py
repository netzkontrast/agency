"""Spec 166 Slice 2 — derive the analyzer-wrapper registry from the live modules.

Slice 1 shipped the typed `WrapperShape` but nothing populated it (dormant), and
the doctor's `analyze_extras` hand-listed `("ruff", "bandit", "radon")` behind an
`AGENCY-DRIFT` tag. This deriver reads each analyzer wrapper module's
`EXTERNAL_TOOL` / `EXTERNAL_EXTRA` / `AXIS_PREFIXES` so the external-tool set and
the wrapper registry DERIVE from the modules — a new wrapper that declares
`EXTERNAL_TOOL` auto-appears, killing the drift (rule 8).

`external_tools()` is the derived replacement for the hand-listed tuple;
`derive_wrapper_shapes()` builds one typed `WrapperShape` per prefix-emitting
external wrapper (the `WrapperShape` invariant requires ≥ 1 prefix, so a
prefix-less metrics tool like radon is a tool but not a shape).
"""
from __future__ import annotations

from ._typed_shapes_wave1_part2 import WrapperShape


def _analyzer_modules():
    from .capabilities.analyze import (_architecture, _bandit, _paths,
                                       _performance, _quality, _radon, _ruff,
                                       _security)
    return (_ruff, _bandit, _radon, _quality, _security, _performance,
            _architecture, _paths)


def external_tools(modules=None) -> "tuple[str, ...]":
    """The external CLI tools the analyzer wrappers declare via ``EXTERNAL_TOOL``
    — the DERIVED replacement for the doctor's hand-listed tuple. Sorted."""
    modules = modules if modules is not None else _analyzer_modules()
    tools = {t for m in modules if (t := getattr(m, "EXTERNAL_TOOL", None))}
    return tuple(sorted(tools))


def _prefixes_of(mod) -> "tuple[str, ...]":
    return tuple(sorted(p for ps in getattr(mod, "AXIS_PREFIXES", {}).values()
                        for p in ps))


def derive_wrapper_shapes(modules=None) -> "tuple[WrapperShape, ...]":
    """One typed `WrapperShape` per external, prefix-emitting analyzer wrapper.
    Composes each module's `EXTERNAL_TOOL` / `EXTERNAL_EXTRA` / `AXIS_PREFIXES`."""
    modules = modules if modules is not None else _analyzer_modules()
    out = []
    for m in modules:
        tool = getattr(m, "EXTERNAL_TOOL", None)
        prefixes = _prefixes_of(m)
        if tool and prefixes:
            extra = getattr(m, "EXTERNAL_EXTRA", "analyze")
            out.append(WrapperShape(tool_name=tool, axis_prefixes=prefixes,
                                    extras=(extra,)))
    return tuple(out)


def wrapper_shapes_summary(modules=None) -> dict:
    """A doctor-friendly roll-up. `ready` iff every declared external tool also
    derives a shape OR is a known prefix-less metrics tool — i.e. the registry
    derives cleanly from the modules (no hand-listing)."""
    shapes = derive_wrapper_shapes(modules)
    tools = external_tools(modules)
    return {"wrappers": len(shapes),
            "external_tools": list(tools),
            "shape_tools": sorted(s.tool_name for s in shapes),
            "ready": bool(tools)}
