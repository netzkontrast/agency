"""reflect — durable, scope-tagged cross-session memory.

Folder-form per Spec 060 §Phase 3 — promoted from `reflect.py` so the
capability can ship its own `templates/` + `schemas/`. The
`Reflection` node + its `scope` enum + `OBSERVED_DURING` / `INFORMS`
edges live on the capability's OntologyExtension as before.
"""
from ._main import REFLECT_SCOPES, ReflectCapability  # noqa: F401
