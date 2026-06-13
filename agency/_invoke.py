"""Spec 286 Phase-1 / A3 — the `Registry.invoke` decomposition.

`Registry.invoke` was a ~105-line god-method fusing five responsibilities. This
module extracts each into a single-purpose, OOP collaborator; `Registry.invoke`
becomes a thin orchestrator that wires them: **guard → inject → record →
call(try/except) → process**.

The decomposition is a PURE STRUCTURAL extraction — behaviour-preserving for the
moat's chokepoint:

- every graph node / edge recorded today (Invocation + SERVES, Agent upsert +
  PERFORMED_BY, Artefact + PRODUCES),
- every error message (the SERVES-guard `ValueError`),
- the Spec 282 `error_severity` classification (verb-exception path + ToolResult
  failure path),
- the Spec 284 `param_enums` thread (it rides on the verb `spec`, untouched),
- the `CapabilityContext` built for `inject=["ctx"]` (so `ctx.host` /
  `ctx.get_driver` / sibling `ctx.call` still resolve),
- the wire-result shape (ToolResult unwrap to `.data`, trace_id stamp,
  outcome/error/warnings/archived_to updates, the `{artefact}` dict path),
- the `(result, invocation_id)` return tuple,

are ALL identical. The collaborators only relocate the existing logic.

Spec 283 (render hook) + Spec 282-E (permanent-failure dedup) ride on the
:class:`ResultProcessor` post-invocation HOOK seam introduced here — this slice
ships the clean extension point (default no-op), NOT those behaviours.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from .memory import Memory


class IntentGuard:
    """Spec 286-A3 — the SERVES intent-guard (one responsibility).

    The SERVES edge is the moat's foundation (C5, Codex review 6059c74): reject
    any invocation whose ``intent_id`` does not resolve to a labeled ``Intent``
    BEFORE any side-effect runs. A mistyped / forged ``intent_id`` would
    otherwise mint an orphan ``Invocation`` the provenance traversal can't see,
    while real ``effect`` verbs still mutate the world.

    Behaviour-preserving: raises the EXACT same ``ValueError`` (same message,
    naming ``intent_bootstrap`` + the bash side-pipe) the inline guard raised.
    """

    def require_intent(self, memory: Memory, intent_id: str) -> None:
        intent_node = memory.g.get_node(intent_id)
        if intent_node is None or "Intent" not in (intent_node.get("labels") or []):
            # Spec 029 §B (F6): point at the substrate tool that mints an intent
            # AND keep the bash side-pipe acknowledged (message is asserted by
            # tests/test_serves_guard_message.py — keep it byte-identical).
            raise ValueError(
                f"intent_id {intent_id!r} is not an Intent node. "
                f"Mint one with the `intent_bootstrap` MCP substrate tool "
                f"(purpose, deliverable, acceptance) or "
                f"`python -m agency.cli intent ...` (bash side-pipe). "
                f"Call `agency_welcome` for the full onboarding payload."
            )


class ParameterInjector:
    """Spec 286-A3 — builds the verb call kwargs (one responsibility).

    Pure construction: walks the verb spec's ``inject`` list and fills the
    ``call`` dict. An explicit arg always wins (never overwritten). ``ctx`` is
    built as a :class:`CapabilityContext`; ``memory`` / ``intent_id`` are
    injected by name; any other name resolves through the registry's derived
    ``injectors`` table (Spec 286-A2 — derived from the DriverRegistry alias
    map). ``param_enums`` is NOT a runtime inject — it rides on the verb spec
    and is surfaced by ``engine._wire`` at schema time — so it is preserved
    untouched here (no projection happens in the call-build path).
    """

    def __init__(self, registry: "Any") -> None:
        # The owning Registry — for `self.ontology`, `self.injectors`,
        # `self.engine`, `self.drivers` (read live so engine bootstrap order
        # and test injection still apply).
        self._registry = registry

    def build_call(self, spec: dict, memory: Memory, intent_id: str,
                   agent_id: Optional[str], depth: int, args: dict) -> dict:
        # Local import avoids an import cycle (capability imports this module).
        from .capability import CapabilityContext
        reg = self._registry
        call = dict(args)
        for name in spec.get("inject", []):
            if name in call:                              # an explicit arg always wins
                continue
            if name == "ctx":
                call["ctx"] = CapabilityContext(
                    memory=memory, ontology=reg.ontology, registry=reg,
                    intent_id=intent_id, agent_id=agent_id,
                    client=(reg.injectors["client"]()
                            if "client" in reg.injectors else None),
                    depth=depth, engine=getattr(reg, "engine", None),
                    drivers=getattr(reg, "drivers", None))
            elif name == "memory":
                call["memory"] = memory
            elif name == "intent_id":
                call["intent_id"] = intent_id
            elif name in reg.injectors:
                call[name] = reg.injectors[name]()
        return call


class InvocationRecorder:
    """Spec 286-A3 — records the ``Invocation`` provenance (one responsibility).

    Records the ``Invocation`` node (capability / verb / role) + the SERVES edge
    to the intent BEFORE the verb runs (so a verb that raises still leaves an
    auditable, intent-served Invocation). When an ``agent_id`` is supplied, an
    idempotent ``Agent`` upsert + a PERFORMED_BY edge keep the performer visible
    in audits (Codex review d5758b2).

    On a verb exception it stamps ``outcome=failed`` + ``error`` +
    ``error_severity`` (Spec 282 ``classify_severity`` — the known
    graph-contention string → TRANSIENT; an unexpected type → FATAL), preserving
    the inline behaviour exactly.
    """

    def open(self, memory: Memory, intent_id: str, cap_name: str, verb: str,
             role: str, agent_id: Optional[str]) -> str:
        inv = memory.record("Invocation", {
            "capability": cap_name, "verb": verb, "role": role,
        })
        memory.link(inv, intent_id, "SERVES")
        if agent_id:
            # Ensure the agent_id resolves to a labeled Agent node so
            # `memory.provenance()`'s `MATCH ->(a:Agent)` picks it up. When the
            # caller passes agent_id directly (MCP/CLI `jules.dispatch`) without
            # first opening a Lifecycle, this idempotent upsert keeps the
            # performer visible in audits.
            if memory.recall(agent_id) is None:
                memory.record("Agent", {"runtime": "external"}, node_id=agent_id)
            memory.link(inv, agent_id, "PERFORMED_BY")  # 'BY' is a Cypher reserved word
        return inv

    def record_exception(self, memory: Memory, inv: str, exc: BaseException) -> None:
        # Spec 282: classify the raising exception so provenance carries the
        # retry-semantics axis. The known graph-contention error ("Failed to set
        # property 'vfrom' on edge N") → transient; an unexpected type → fatal.
        from .toolresult import classify_severity
        sev = classify_severity("", exc=exc, message=str(exc))
        memory.update(inv, {"outcome": "failed",
                            "error": f"{type(exc).__name__}: {exc}",
                            "error_severity": sev})


class ResultProcessor:
    """Spec 286-A3 — the ToolResult unwrap + side-effect recording (one
    responsibility).

    When a verb returns the in-sandbox :class:`~agency.toolresult.ToolResult`
    envelope, this records its metadata as ``Invocation`` side-effects (typed
    error + Spec 282 severity, warnings, archived_to), stamps
    ``error.trace_id`` to the invocation id when the verb left it empty (Spec
    059), converts ``artefacts_written`` into ``Artefact`` nodes + PRODUCES
    edges (C4), and replaces ``result`` with the unwrapped ``.data`` so the wire
    shape stays the lean code-mode contract (CORE.md:9-18). Plain-dict returns
    carrying ``{"artefact": {...}}`` get the same Artefact + PRODUCES treatment.

    **Post-invocation HOOK seam (Spec 286-A3).** After the side-effects are
    recorded, every registered ``post_invocation`` hook is called with the
    signature::

        hook(memory, invocation_id, intent_id, label, result) -> None

    where ``label`` is the verb-result label hint (``None`` here — reserved for
    the render hook to fill from the produced node) and ``result`` is the
    UNWRAPPED data (post ``.data`` unwrap), matching what the caller receives.
    The list defaults empty, so the seam is a no-op until a hook registers — no
    behaviour change. Spec 283's render hook (auto-render-on-mutation) and Spec
    282-E's permanent-failure dedup attach here later; this slice ships only the
    clean extension point.
    """

    def __init__(self) -> None:
        # Registered post-invocation callbacks. Default empty → no-op seam.
        self.post_invocation: list[
            Callable[[Memory, str, str, Optional[str], Any], None]
        ] = []

    def register_post_invocation(
        self,
        hook: Callable[[Memory, str, str, Optional[str], Any], None],
    ) -> None:
        """Append a post-invocation hook (Spec 286-A3 seam). Called AFTER
        side-effects are recorded, in registration order. Each hook is
        ``hook(memory, invocation_id, intent_id, label, result) -> None``;
        return value ignored."""
        self.post_invocation.append(hook)

    def process(self, memory: Memory, inv: str, intent_id: str,
                result: Any) -> Any:
        from .toolresult import ToolResult
        label: Optional[str] = None
        if isinstance(result, ToolResult):
            # Spec 059: stamp error.trace_id = inv when the verb didn't supply
            # one. Both ToolResult and TypedError are frozen, so the stamp is
            # `dataclasses.replace` (rebuild, not mutate). The caller's explicit
            # trace_id wins — we only fill the empty case.
            if result.error is not None and not result.error.trace_id:
                from dataclasses import replace
                new_error = replace(result.error, trace_id=inv)
                result = replace(result, error=new_error)
            updates: dict = {}
            if not result.ok:                                # ok=False alone marks the run failed
                updates["outcome"] = "failed"                # (Codex review d5758b2)
            if result.error is not None:                     # TypedError carries the message
                updates["outcome"] = "failed"
                updates["error"] = f"{result.error.code}: {result.error.message}"
                # Spec 282: record the orthogonal severity so a census can
                # separate permanent retries from real signal. Re-classify if
                # the verb attached a TypedError without a severity.
                from .toolresult import classify_severity
                updates["error_severity"] = (
                    result.error.severity
                    or classify_severity(result.error.code,
                                         message=result.error.message))
            if result.warnings:
                updates["warnings"] = list(result.warnings)
            if result.archived_to:
                updates["archived_to"] = result.archived_to
            if updates:
                memory.update(inv, updates)
            # C4 (Codex review 6059c74): convert `artefacts_written` into
            # Artefact nodes + PRODUCES edges, the envelope's documented purpose.
            for path in (result.artefacts_written or []):
                art = memory.record("Artefact", {"kind": "file", "path": str(path)})
                memory.link(inv, art, "PRODUCES")
            result = result.data
        if isinstance(result, dict) and result.get("artefact"):
            art = memory.record("Artefact", dict(result["artefact"]))
            memory.link(inv, art, "PRODUCES")
        # Post-invocation hook seam (Spec 286-A3). Default empty → no-op.
        for hook in self.post_invocation:
            hook(memory, inv, intent_id, label, result)
        return result
