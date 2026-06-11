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

Spec 059 adds the convenience layer: ``Codes`` sugar, ``.success(...)`` /
``.failure(...)`` keyword-only constructors, and the ``next_cursor`` opt-in
pagination field. Registry.invoke stamps ``error.trace_id`` via
``dataclasses.replace`` since the dataclass is frozen.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


class Codes:
    """Non-binding string-constant sugar for common failure codes
    (Spec 059). ``TypedError.code`` accepts ANY string by Spec 001's
    free-string discipline; these constants only exist so call sites
    DRY their failure paths."""
    VALIDATION_FAILED = "validation_failed"
    DEPENDENCY_MISSING = "dependency_missing"
    GATE_FAILED = "gate_failed"
    NOT_FOUND = "not_found"
    UNSUPPORTED = "unsupported"
    BOUNDARY_ERROR = "boundary_error"
    INTERNAL = "internal"
    UNSPECIFIED = "unspecified"   # ok=False with no structured error
    # Spec 151 Slice 1 — promoted from heavily-used literal-string call
    # sites (e.g. novel cap argument-validation paths). Value MUST stay
    # uppercase "INVALID_ARGUMENT" to match the existing live convention
    # (40+ call sites + assertions across tests/test_music_lifecycle.py,
    # tests/test_novel_lifecycle*.py, tests/test_thinking_capability.py,
    # tests/test_prompt_capability.py, …). Migrating call sites from the
    # literal `"INVALID_ARGUMENT"` to `Codes.INVALID_ARGUMENT` must NOT
    # change the emitted `TypedError.code`. Other Codes constants use a
    # lowercase value (Spec 059 convention); this constant is the
    # documented exception so the backfill stays a pure refactor.
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    # Spec 150 — dogfood amendment classifier failure modes.
    AMENDMENT_BAD_SPEC = "amendment_bad_spec"     # proposal cites a non-existent spec_id
    AMENDMENT_NO_SOURCE = "amendment_no_source"   # source_reflections is empty (provenance break)
    AMENDMENT_VAGUE = "amendment_vague"           # rationale below the 40-char floor
    AMENDMENT_UNCONFIRMED = "amendment_unconfirmed"   # live write requested, confirm_token mismatch


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
    next_cursor: Optional[str] = None         # Spec 059 — opt-in pagination for paged read verbs

    @classmethod
    def success(cls, *, data: Any = None,
                warnings: Optional[list] = None,
                next_suggested_tools: Optional[list] = None,
                artefacts_written: Optional[list] = None,
                archived_to: str = "",
                next_cursor: Optional[str] = None) -> "ToolResult":
        """Spec 059 — convenience ctor for the success path. All kwargs
        are keyword-only to keep call sites self-documenting."""
        return cls(
            data=data, ok=True,
            warnings=list(warnings or []),
            next_suggested_tools=list(next_suggested_tools or []),
            artefacts_written=list(artefacts_written or []),
            archived_to=archived_to,
            next_cursor=next_cursor,
        )

    @classmethod
    def failure(cls, code: str, message: str, *,
                warnings: Optional[list] = None,
                trace_id: str = "") -> "ToolResult":
        """Spec 059 — convenience ctor for the failure path. Builds the
        attached ``TypedError`` in-place. ``trace_id`` is left as-is when
        supplied; otherwise ``Registry.invoke`` stamps it post-call."""
        return cls(
            data=None, ok=False,
            warnings=list(warnings or []),
            error=TypedError(code=code, message=message, trace_id=trace_id),
        )
