"""Capabilities — discovered by REFLECTION, not hand-wired.

Drop a module in this package that defines a `Capability` instance OR a
`CapabilityBase` subclass at module level; `discover()` finds both via the stdlib
reflection APIs (`pkgutil.iter_modules` to walk this package's directory +
`importlib` to import each module + `isinstance`/`issubclass` to pick them out).
The engine calls `discover()` and registers everything, and auto-wires one MCP
tool per verb from the verb signature (`inspect.signature`). Adding a capability =
adding a file. No registration code, no per-tool boilerplate.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil

from ..capability import Capability, CapabilityBase


def discover() -> list[Capability]:
    """Every `Capability` (instance) or `CapabilityBase` subclass defined at the
    top level of any non-private module in this package OR in a Spec-291 pillar
    package (agency/<pillar>/), in stable order."""
    found: list[Capability] = []
    # Legacy `capabilities/` + the pillar packages. A pillar package only exists
    # once its caps are reorg'd into it (Spec 291); until then `agency.<pillar>`
    # is the plain substrate module (no `__path__`) and is skipped. This keeps
    # discovery correct at every incremental step of the reorg.
    packages = [(list(__path__), __name__)]
    for pillar in ("intent", "capability", "lifecycle", "memory"):
        try:
            mod = importlib.import_module(f"agency.{pillar}")
        except Exception:
            continue
        if hasattr(mod, "__path__"):          # a package (reorg'd), not the substrate module
            packages.append((list(mod.__path__), mod.__name__))
    for path, pkg_name in packages:
        for info in sorted(pkgutil.iter_modules(path), key=lambda i: i.name):
            if info.name.startswith("_"):
                continue
            module = importlib.import_module(f"{pkg_name}.{info.name}")
            for value in vars(module).values():
                if isinstance(value, Capability) and value not in found:
                    found.append(value)
                elif (inspect.isclass(value) and issubclass(value, CapabilityBase)
                      and value is not CapabilityBase):
                    cap = value.as_capability()
                    if cap not in found:
                        found.append(cap)
    return found
