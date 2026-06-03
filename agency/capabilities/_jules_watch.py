"""Spec 060 back-compat shim — canonical module is `jules/watch.py`."""
from .jules.watch import *  # noqa: F401, F403
from .jules.watch import (  # noqa: F401
    INSTRUCTIONS,
    Watcher,
    _classify,
    start,
    stop,
)
