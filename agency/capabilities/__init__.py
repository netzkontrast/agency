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
    top level of any non-private module in this package, in stable order."""
    found: list[Capability] = []
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda i: i.name):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{info.name}")
        for value in vars(module).values():
            if isinstance(value, Capability) and value not in found:
                found.append(value)
            elif (inspect.isclass(value) and issubclass(value, CapabilityBase)
                  and value is not CapabilityBase):
                found.append(value.as_capability())
    return found
