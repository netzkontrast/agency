"""shell — a token-efficient, recorded, templated host-command boundary (Spec 073).

Folder-form per Spec 060 §Phase 3 / Spec 286 Goal 4. Re-exports the public
surface the engine + tests reach for (`_apply_filter`, `_ALLOWED_TOOLS`,
`_TEMPLATES`) so existing `from agency.capabilities.shell import …` keeps working.
"""
from ._main import (  # noqa: F401
    _ALLOWED_TOOLS,
    _TEMPLATES,
    ShellCapability,
    _apply_filter,
    capture_filter,
)
