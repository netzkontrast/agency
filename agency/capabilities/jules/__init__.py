"""jules — the agent capability (folder form per Spec 060 §Phase 3,
absorbs Spec 028).

Re-exports the symbols engine.py + tests historically imported from
the pre-migration single-file form.
"""
from ._main import (  # noqa: F401
    JULES_STATES,
    WATCH_ACTIONS,
    JulesBackend,
    JulesCapability,
    JulesClient,
)
