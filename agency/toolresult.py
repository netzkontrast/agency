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


class Severity:
    """Spec 282 — the retry-semantics axis of a failure, ORTHOGONAL to the
    free-string ``TypedError.code``. ``code`` stays free per Spec 001's ADR
    ("closed enums fragment across capabilities"); severity is a SMALL FIXED
    engine-level vocabulary that classifies *whether retrying can ever help*,
    so it does not partition the capability surface and cannot fragment.

    Evidence (kohaerenzprotokoll/.agency/session.db, one ingest run): 513
    ``create_scene`` calls failed PERMANENTLY on a closed ``pov`` enum yet the
    driver retried each ~34× because the failure was indistinguishable from a
    TRANSIENT graph-contention error. Severity is the bit that tells them
    apart."""

    PERMANENT = "permanent"   # validation / enum / schema / not-found / gate — retry NEVER helps
    TRANSIENT = "transient"   # contention / IO / timeout / boundary — retry MAY help
    FATAL = "fatal"           # internal invariant violation / unexpected crash — abort the batch


# Substrings that mark a TRANSIENT failure when found in a code/message or the
# str() of a raising exception. The graph-contention string is the exact one
# observed under concurrent MCP+CLI writes (CLAUDE.md gotcha + Spec 282 §1).
_TRANSIENT_MARKERS = (
    "failed to set property",        # graphqlite edge-write contention
    "database is locked",
    "operationalerror",
    "timeout",
    "timed out",
    "connection",
    "temporarily unavailable",
    "resource temporarily",
)

# Exception TYPES that are transient regardless of message.
_TRANSIENT_EXC_TYPES = (
    "TimeoutError", "ConnectionError", "OSError", "IOError",
    "OperationalError", "BlockingIOError",
)

# Substrings that mark a PERMANENT (caller-fixable) failure.
_PERMANENT_MARKERS = (
    "not in", "invalid", "unknown", "required", "missing",
    "enum", "not found", "does not exist", "not an intent",
)


def classify_severity(code: str, *, exc: BaseException | None = None,
                      message: str = "") -> str:
    """Map a free-string failure ``code`` (and optionally the raising
    exception / message) to a :class:`Severity`. Spec 282 §3.

    Resolution order:
      1. An exception present → inspect its type then its text.
      2. The ``code`` against the known :class:`Codes` partition.
      3. The ``code`` / ``message`` text against marker substrings.
      4. Default → PERMANENT (we are fixing OVER-retrying, so an unclassified
         failure is conservatively *not* retried; a genuinely transient code
         should be added to ``_TRANSIENT_MARKERS``).
    """
    blob = f"{code} {message}".lower()

    if exc is not None:
        exc_name = type(exc).__name__
        if exc_name in _TRANSIENT_EXC_TYPES:
            return Severity.TRANSIENT
        exc_text = str(exc).lower()
        if any(m in exc_text for m in _TRANSIENT_MARKERS):
            return Severity.TRANSIENT
        if any(m in blob for m in _TRANSIENT_MARKERS):
            return Severity.TRANSIENT
        # An unexpected exception type that is NOT a known transient is an
        # engine bug, not a caller-fixable input → FATAL.
        return Severity.FATAL

    # No exception: classify by code/message.
    if any(m in blob for m in _TRANSIENT_MARKERS):
        return Severity.TRANSIENT

    code_l = code.lower()
    permanent_codes = {
        Codes.VALIDATION_FAILED, Codes.GATE_FAILED, Codes.NOT_FOUND,
        Codes.UNSUPPORTED, Codes.UNSPECIFIED, Codes.INVALID_ARGUMENT.lower(),
        Codes.AMENDMENT_BAD_SPEC, Codes.AMENDMENT_NO_SOURCE,
        Codes.AMENDMENT_VAGUE, Codes.AMENDMENT_UNCONFIRMED,
        Codes.SKILL_PARSE_INVALID, Codes.PHASE_MISSING_FIELD,
        Codes.PHASE_UNKNOWN_KIND,
    }
    if code_l in permanent_codes or code == Codes.INVALID_ARGUMENT:
        return Severity.PERMANENT
    if code_l in {Codes.INTERNAL}:
        return Severity.FATAL
    if any(m in blob for m in _PERMANENT_MARKERS):
        return Severity.PERMANENT
    # Spec 282 §3 documented default.
    return Severity.PERMANENT


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
    # sites (e.g. novel cap argument-validation paths). Spec 151 Slice 4
    # canonicalized this value to lowercase: EVERY Codes member's value is
    # the lowercase of its name (Spec 059 convention) — there is no
    # documented exception. The case flip changes the emitted
    # `TypedError.code` from "INVALID_ARGUMENT" to "invalid_argument";
    # tests asserting the code value were updated to the lowercase form.
    INVALID_ARGUMENT = "invalid_argument"
    # Spec 151 Slice 4 — promoted from heavily-used literal-string failure
    # codes (lowercase per Spec 059).
    BAD_REQUEST = "bad_request"
    DRIVER_REFUSAL = "driver_refusal"
    SCENE_OVERFLOW_LOST = "scene_overflow_lost"
    VOICE_BRIEF_MISSING = "voice_brief_missing"
    # Spec 150 — dogfood amendment classifier failure modes.
    AMENDMENT_BAD_SPEC = "amendment_bad_spec"     # proposal cites a non-existent spec_id
    AMENDMENT_NO_SOURCE = "amendment_no_source"   # source_reflections is empty (provenance break)
    AMENDMENT_VAGUE = "amendment_vague"           # rationale below the 40-char floor
    AMENDMENT_UNCONFIRMED = "amendment_unconfirmed"   # live write requested, confirm_token mismatch
    # Spec 152 — typed Skill/Phase parse boundary failure modes.
    SKILL_PARSE_INVALID = "skill_parse_invalid"   # top-level skill dict failed validation
    PHASE_MISSING_FIELD = "phase_missing_field"   # phase dict missing a required field
    PHASE_UNKNOWN_KIND = "phase_unknown_kind"     # unknown gate/variant on a phase
    # Spec 149 Slice 2.4 — derive-docs typed failure modes.
    DERIVE_FENCE_BROKEN = "derive_fence_broken"   # opened fence has no matching close marker
    DERIVE_AMBIGUOUS = "derive_ambiguous"         # two specs claim the same derivation source
    DERIVE_MISSING_GOAL = "derive_missing_goal"   # spec missing required frontmatter
    # Spec 171 Slice 2 — node-id-guard coverage sweep failure mode.
    GUARD_LINT_UNRESOLVED = "guard_lint_unresolved"   # AST walk can't resolve a verb signature → manual review
    # Spec 173 Slice 2 — reflection-link coverage failure modes.
    REFLECTION_NO_INTENT = "reflection_no_intent"       # Reflection write with no Intent in scope (substrate-enforced)
    REFLECTION_PARTIAL_LINKS = "reflection_partial_links"   # a Reflection carries only one of SERVES/OBSERVED_DURING
    # Spec 175 Slice 2 — install-surface regen failure mode.
    INSTALL_REGEN_PARTIAL = "install_regen_partial"     # `agency install` crashed mid-write (atomic-rename guard tripped)
    # Spec 176 Slice 2 — sessionstart intent-capture failure mode.
    CAPTURE_DEGRADED = "capture_degraded"   # capture driver failed mid-flow — partial turns persisted, resumable
    # Spec 169 Slice 2 — CI coverage-gate infra failure mode.
    GATE_INFRA_ERROR = "gate_infra_error"   # the coverage tool itself crashed — gate fails closed, never silent-pass
    # Spec 172 Slice 2 — analyzer-axis registry build failure modes.
    AXIS_PREFIX_COLLISION = "axis_prefix_collision"   # two analyzers claim the same prefix for DIFFERENT axes
    AXIS_PREFIX_MALFORMED = "axis_prefix_malformed"   # an analyzer's AXIS_PREFIXES is non-string / empty — fail fast at build


@dataclass(frozen=True)
class TypedError:
    """A failure record a verb may attach to its `ToolResult`. `code` is a
    free-string (per `the-agency-system`'s ADR — closed enums fragment across
    capabilities); `trace_id` is wired by `Registry.invoke` to the recorded
    Invocation id so the failure is traceable in one provenance hop.

    Spec 282: ``severity`` is the ORTHOGONAL retry-semantics axis (one of
    :class:`Severity`). It is derived from ``code`` by ``classify_severity``
    when not supplied explicitly. An empty severity means "unclassified" and
    is treated as non-retryable by ``retryable`` (conservative)."""
    code: str
    message: str
    trace_id: str = ""
    context: dict = field(default_factory=dict)
    severity: str = ""

    @property
    def retryable(self) -> bool:
        """Only a TRANSIENT failure is worth retrying. Spec 282."""
        return self.severity == Severity.TRANSIENT


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
                trace_id: str = "",
                severity: Optional[str] = None) -> "ToolResult":
        """Spec 059 — convenience ctor for the failure path. Builds the
        attached ``TypedError`` in-place. ``trace_id`` is left as-is when
        supplied; otherwise ``Registry.invoke`` stamps it post-call.

        Spec 282 — ``severity`` is derived from ``code``/``message`` via
        ``classify_severity`` when not given; an explicit value wins. So
        EVERY ``ToolResult.failure`` carries a retry-semantics classification
        without touching the 40+ existing call sites."""
        sev = severity if severity is not None else classify_severity(code, message=message)
        return cls(
            data=None, ok=False,
            warnings=list(warnings or []),
            error=TypedError(code=code, message=message, trace_id=trace_id,
                             severity=sev),
        )
