"""Spec 286 Phase-2 / A7 — `WireEnvelope`: the ONE owner of the wire-shape rule.

The "strip / re-wrap `{result}`" rule (Spec 019) and the Spec 282 failure
envelope (`{ok, error:{code,message,severity,retryable,trace_id}}`) were
duplicated across `engine._wire`/`engine._shape_wire_result` and
`cli._structured`. A wire-contract change meant editing every copy (shotgun
surgery). This module consolidates the rule behind one class so callers depend
on it (DIP) and the rule lives in exactly one place.

Two responsibilities, two methods:

- :meth:`WireEnvelope.unwrap` — the Spec 019 success-shape rule. An inner
  ``{"result": <delta>}`` is unwrapped to ``<delta>`` iff ``<delta>`` is itself
  a dict; a scalar delta is re-wrapped as ``{"result": <scalar>}`` because MCP
  tool returns must be JSON objects; a rich dict without ``result`` passes
  through unchanged.

- :meth:`WireEnvelope.shape` — the full registry-return → wire-dict shaping
  (Spec 282). On a FAILED invocation it emits the typed error envelope so the
  caller can branch on ``severity`` / ``retryable`` and stop retrying permanent
  failures; on success it delegates to :meth:`unwrap`.

The wire output (what an MCP client / bash CLI receives) is byte-identical to
the pre-consolidation behaviour — this is the hottest path of the
`search`/`get_schema`/`execute` contract, so the rule is moved, not changed.
"""
from __future__ import annotations

from typing import Any, Optional


class WireEnvelope:
    """Owns the wire-shape rule for the `search`/`get_schema`/`execute`
    contract. Stateless — methods are ``@staticmethod`` so any caller
    (engine wire impl, engine shaper, CLI structured-content reader) routes
    through the same single implementation without an instance dependency."""

    @staticmethod
    def unwrap(result: Any) -> Any:
        """Spec 019 — the strip-`{result}`-iff-dict rule.

        - ``{"result": <dict>}``  → ``<dict>``  (lean code-mode shape; caller
          reads keys directly, no ``r["result"]["x"]`` boilerplate).
        - ``{"result": <scalar>}`` → ``{"result": <scalar>}`` (re-wrapped — an
          MCP tool return must be a JSON object, so a bare scalar can't cross).
        - rich dict WITHOUT ``result`` → identical (passes through).

        This is the exact rule the engine's ``_wire`` success path and the
        CLI's ``_structured`` previously inlined. Idempotent on an already-shaped
        wire dict: a rich dict (no top-level ``result``) round-trips unchanged,
        and a ``{"result": <scalar>}`` re-wrap survives a second pass.

        ``unwrap`` == :meth:`strip` (drop the ``result`` key) + the MCP
        scalar-re-wrap guard (a non-dict can't cross as a tool return).
        """
        out = WireEnvelope.strip(result)
        return out if isinstance(out, dict) else {"result": out}

    @staticmethod
    def strip(result: Any) -> Any:
        """Spec 019 — the pure strip-`{result}` half of the rule, WITHOUT the
        scalar re-wrap. ``{"result": <x>}`` → ``<x>`` (dict OR scalar); any
        other value passes through.

        This is the rule ``cli._structured`` runs on the engine's ALREADY-shaped
        ``structured_content``: the engine re-wraps a scalar to ``{"result":
        <scalar>}`` so the MCP return is a JSON object; the bash CLI prints the
        bare scalar to stdout, so it strips that wrapper back off (no re-wrap).
        Keeping it here means the strip half of the wire rule has ONE home too —
        :meth:`unwrap` is ``strip`` followed by the MCP scalar-re-wrap guard.
        """
        if isinstance(result, dict) and "result" in result:
            return result["result"]
        return result

    @staticmethod
    def shape_failure(*, code: str, message: str, severity: str,
                      trace_id: str) -> dict:
        """Spec 282 — build the typed failure envelope from its parts.

        Returns ``{"ok": False, "error": {code, message, severity, retryable,
        trace_id}}`` where ``retryable`` is derived from the severity
        (only TRANSIENT failures are worth retrying). A bare ``null`` told the
        caller nothing, so the ingest driver retried every impossible call ~34×;
        this envelope lets the caller branch on ``error.severity`` /
        ``error.retryable`` and stop retrying ``permanent`` failures.
        """
        from .toolresult import Severity
        return {"ok": False, "error": {
            "code": code, "message": message, "severity": severity,
            "retryable": severity == Severity.TRANSIENT, "trace_id": trace_id}}

    @staticmethod
    def shape(result: Any, *, outcome: Optional[str], error: str,
              error_severity: str, trace_id: str) -> dict:
        """Spec 282 — shape a registry return into the wire dict.

        ``outcome`` / ``error`` / ``error_severity`` are read off the recorded
        Invocation node by the caller (the engine), keeping this class free of a
        Memory dependency. On a FAILED invocation, parse the recorded
        ``"code: message"`` error string and emit the typed envelope (deriving
        the severity from the code/message when the node didn't record one). On
        success, delegate to :meth:`unwrap` — the Spec 019 rule, unchanged.
        """
        if outcome == "failed":
            err = error or ""
            code, sep, msg = err.partition(": ")
            if not sep:                       # error string had no "code: msg" split
                code, msg = "", err
            sev = error_severity
            if not sev:
                from .toolresult import classify_severity
                sev = classify_severity(code, message=msg)
            return WireEnvelope.shape_failure(
                code=code, message=msg, severity=sev, trace_id=trace_id)
        return WireEnvelope.unwrap(result)
