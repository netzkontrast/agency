"""ToolResult — the in-sandbox envelope a verb may return.

Per Spec 001 (Option C, the canon-aligned, token-lean choice): the envelope is
an INTERNAL Python dataclass, NOT the wire shape. `Registry.invoke` unwraps
`ToolResult.data` so existing `cli.py`/`execute()` callers see no change; the
auxiliary fields exist as a typed contract for verbs that need to carry typed
errors, warnings, archived-output references (spec 005 context-mode middleware
writes `archived_to`), produced-artefact paths, or next-suggested-tools
alongside their primary `data`.

The lean code-mode contract (`CORE.md:9-18`) stays exactly `search` /
`get_schema` / `execute`; the envelope never crosses the agent boundary
unless the agent's `execute()` block returns the whole structure.

Verbs that don't need the envelope keep returning plain dicts — the envelope
is opt-in.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class TypedError:
    """A failure record a verb may attach to its `ToolResult`. `code` is a
    free-string (per `the-agency-system`'s ADR — closed enums fragment across
    capabilities); `trace_id` is wired by `Registry.invoke` to the recorded
    Invocation id so the failure is traceable in one provenance hop."""
    code: str
    message: str
    trace_id: str = ""
    context: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    """The in-sandbox return envelope. `data` is the primary return; everything
    else is metadata recorded as side-effects by the Engine on the Invocation."""
    data: Any
    ok: bool = True
    warnings: list = field(default_factory=list)
    next_suggested_tools: list = field(default_factory=list)
    error: Optional[TypedError] = None
    artefacts_written: list = field(default_factory=list)
    archived_to: str = ""                     # reserved for spec 005 context-mode middleware
    trace_id: str = ""
