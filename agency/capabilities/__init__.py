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

# Spec 060 back-compat (canonical: agency.capabilities.jules.*).
# Register module aliases in sys.modules + as package attributes so
# legacy imports like `from agency.capabilities import _jules_api` AND
# `from agency.capabilities._jules_api import _request` AND
# `monkeypatch.setattr(_jules_api, "x", ...)` all reach the SAME
# canonical module objects under `agency.capabilities.jules.*`.
import sys as _sys
from .jules import (
    api as _jules_api,
    patch as _jules_patch,
    preambles as _jules_preambles,
    skills as _jules_skills,
    watch as _jules_watch,
)
_sys.modules['agency.capabilities._jules_api'] = _jules_api
_sys.modules['agency.capabilities._jules_patch'] = _jules_patch
_sys.modules['agency.capabilities._jules_preambles'] = _jules_preambles
_sys.modules['agency.capabilities._jules_skills'] = _jules_skills
_sys.modules['agency.capabilities._jules_watch'] = _jules_watch


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
