"""Spec 060 back-compat shim — the canonical module is `jules/api.py`.

External consumers (tests + engine.py) historically imported
`agency.capabilities._jules_api`; the jules folder migration moved
the module to `agency.capabilities.jules.api`. This shim preserves
the legacy import path so the migration is transparent.

Remove this shim only after every external import migrates to the
new path AND the deprecation cycle completes.
"""
from .jules.api import *  # noqa: F401, F403
from .jules.api import _api_key, _request  # noqa: F401 — private; used by tests + monkeypatching
