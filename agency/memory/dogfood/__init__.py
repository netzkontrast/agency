"""dogfood — graph-native observation ledgers (Spec 017 + 020 v2).

Folder-form per Spec 060 §Phase 3 — promoted from `dogfood.py` so the
capability can ship its own `templates/` + `schemas/` subfolders. The
discovery surface remains the capability class re-exported here.
"""
from ._main import DogfoodCapability  # noqa: F401
