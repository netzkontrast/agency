"""Spec 282 — ``retry_transient``: the correct retry primitive.

Replaces the anti-pattern that produced the evidence retry storm
(``scripts/ingest_canon.py`` looping ``for attempt in range(1, 40)`` "while
progress is made"): retry a call ONLY when its result is a wire error envelope
classified ``transient``. A ``permanent``/``fatal`` failure — or a success —
returns immediately, so an impossible call (bad enum, missing arg) is never
hammered.

The call is expected to return the Spec 282 wire shape on failure:
``{"ok": False, "error": {"severity": "...", "retryable": bool, ...}}``.
Any other return is treated as success and returned as-is.
"""
from __future__ import annotations

import time
from typing import Any, Callable

from .toolresult import Severity


def _is_transient(result: Any) -> bool:
    """True iff ``result`` is a wire error envelope marked transient."""
    if not isinstance(result, dict):
        return False
    err = result.get("error")
    if not isinstance(err, dict):
        return False
    return err.get("severity") == Severity.TRANSIENT


def retry_transient(call: Callable[[], Any], *, attempts: int = 4,
                    backoff: float = 2.0,
                    sleep: Callable[[float], None] = time.sleep) -> Any:
    """Run ``call()``; retry up to ``attempts`` times with exponential
    ``backoff`` ONLY while the result is a transient failure.

    Returns the first non-transient result (a success or a permanent/fatal
    failure), or the last transient result once ``attempts`` is exhausted.
    ``sleep`` is injectable so tests run instantly.
    """
    if attempts < 1:
        attempts = 1
    result: Any = None
    for i in range(attempts):
        result = call()
        if not _is_transient(result):
            return result
        if i < attempts - 1:
            sleep(backoff ** i)
    return result
