"""develop — discipline-walk templates + scaffolds.

Folder-form per Spec 060 §Phase 3. Re-exports the symbols
tests/external callers used from the pre-migration single-file form
so the folder migration is invisible at the import boundary.
"""
from ._main import (  # noqa: F401
    DEV_SKILLS,
    DevelopCapability,
    REFERENCES,
    checklist,
    scaffold_capability,
)
