"""analyze — multi-axis decidable code analysis (Spec 042).

Folder-form capability. The implementation lives in ``_main.py``;
this module re-exports ``AnalyzeCapability`` so the engine's
discovery (which walks ``agency/capabilities/`` looking for
``CapabilityBase`` subclasses) finds it.
"""
from ._main import AnalyzeCapability

__all__ = ["AnalyzeCapability"]
