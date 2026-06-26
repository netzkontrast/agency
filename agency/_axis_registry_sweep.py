"""Spec 172 Slice 2 — derive the analyzer-axis registry from the live wrappers.

Slice 1 shipped the typed `AxisRegistry` (prefix → analyzer_id, with `resolve`)
but nothing populated it from the live analyzer set (dormant). This is the
deriver: it COMPOSES every analyzer wrapper's module-level `AXIS_PREFIXES`
(Spec 057/166/167 — `analyze/_ruff.py`, `_bandit.py`, …) into the typed registry,
sorted **longest-prefix-first** so `resolve("A001")` returns the owner of the
longest matching prefix (`"A0"` before `"A"`), and the result is **order-
independent** (deterministic sort, not load order).

Two guards run at build:
  - **collision** — two analyzers claim the SAME prefix for DIFFERENT axes →
    `Codes.AXIS_PREFIX_COLLISION` (the build reports it rather than silently
    picking a winner). Same-axis overlaps are idempotently unioned.
  - **malformed** — an analyzer's `AXIS_PREFIXES` carries a non-string / empty
    prefix → `Codes.AXIS_PREFIX_MALFORMED`, fail-fast at build (never at first
    use).

The default analyzer set is the one `analyze/_main.py::_build_axis_registry`
already unions, so the derived registry and the live lookup cannot drift.
"""
from __future__ import annotations

from ._typed_shapes_wave1_part2 import AxisRegistry
from .toolresult import Codes


def _default_modules():
    """The live analyzer wrapper set (mirrors `analyze/_main.py`)."""
    from .capabilities.analyze import (_architecture, _bandit, _paths,
                                       _performance, _quality, _radon, _ruff,
                                       _security)
    return (_quality, _security, _performance, _architecture, _paths,
            _ruff, _bandit, _radon)


def _collect(modules):
    """Yield `(prefix, axis, module_name)` triples from each module's
    `AXIS_PREFIXES`, validating shape. Raises `ValueError` (carrying
    `Codes.AXIS_PREFIX_MALFORMED`) on a non-string / empty prefix or axis."""
    triples = []
    for mod in modules:
        prefixes = getattr(mod, "AXIS_PREFIXES", {})
        for axis, ps in prefixes.items():
            if not isinstance(axis, str) or not axis:
                raise ValueError(
                    f"{Codes.AXIS_PREFIX_MALFORMED}: {mod.__name__} declares a "
                    f"non-string/empty axis {axis!r}")
            for p in ps:
                if not isinstance(p, str) or not p:
                    raise ValueError(
                        f"{Codes.AXIS_PREFIX_MALFORMED}: {mod.__name__} axis "
                        f"{axis!r} has a non-string/empty prefix {p!r}")
                triples.append((p, axis, mod.__name__))
    return triples


def detect_collisions(modules=None) -> "list[tuple[str, str, str]]":
    """Every prefix claimed for ≥ 2 DIFFERENT axes, as `(prefix, axis_a, axis_b)`
    with the two axes sorted (so the report is order-independent). Same-axis
    overlaps are NOT collisions."""
    if modules is None:
        modules = _default_modules()
    by_prefix: dict[str, set] = {}
    for p, axis, _mod in _collect(modules):
        by_prefix.setdefault(p, set()).add(axis)
    collisions = []
    for p, axes in by_prefix.items():
        if len(axes) > 1:
            ordered = sorted(axes)
            collisions.append((p, ordered[0], ordered[1]))
    return sorted(collisions)


def derive_axis_registry(modules=None) -> AxisRegistry:
    """The typed `AxisRegistry` from the live analyzer wrappers, prefixes sorted
    **longest-first then lexically** (longest-prefix-first resolution, fully
    order-independent). A collision raises `ValueError` (carrying
    `Codes.AXIS_PREFIX_COLLISION`) — use :func:`axis_registry_summary` for the
    non-raising report."""
    if modules is None:
        modules = _default_modules()
    collisions = detect_collisions(modules)
    if collisions:
        p, a, b = collisions[0]
        raise ValueError(
            f"{Codes.AXIS_PREFIX_COLLISION}: prefix {p!r} owned by both "
            f"{a!r} and {b!r}")
    # Dedup same-axis overlaps, then sort longest-first (then lexical) so resolve
    # is longest-prefix-first and the result is independent of load order.
    pairs = {p: axis for p, axis, _mod in _collect(modules)}
    ordered = tuple(sorted(pairs.items(), key=lambda kv: (-len(kv[0]), kv[0])))
    return AxisRegistry(prefixes=ordered)


def axis_registry_summary(modules=None) -> dict:
    """A doctor-friendly roll-up. `ready` iff zero collisions AND the registry
    builds (no malformed prefixes). Never raises — a build failure is reported,
    not thrown, so the doctor stays robust."""
    try:
        collisions = detect_collisions(modules)
        if collisions:
            return {"ready": False, "entries": 0,
                    "collision_count": len(collisions),
                    "collisions": collisions,
                    "code": Codes.AXIS_PREFIX_COLLISION}
        reg = derive_axis_registry(modules)
        return {"ready": True, "entries": len(reg.prefixes),
                "collision_count": 0, "collisions": [],
                "prefixes": [p for p, _a in reg.prefixes]}
    except ValueError as exc:
        return {"ready": False, "entries": 0, "collision_count": 0,
                "collisions": [], "code": Codes.AXIS_PREFIX_MALFORMED,
                "error": str(exc)}
