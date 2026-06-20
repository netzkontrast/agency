"""Engine — one FastMCP server + one graph.

**Code-mode IS the contract** (lean: no separate four-verb surface). The engine
exposes exactly `search` / `get_schema` / `execute`; the underlying tools
(capabilities, gate, provenance) are discovered via `search` and called from
inside `execute` (`await call_tool(name, params)`). This is the same surface a
bash agent drives via `agency/cli.py` — so MCP and bash are isomorphic by
construction. Tool names are MCP-conformant `capability_<capability>_<verb>`.

**Capabilities are self-registering.** The engine does not hand-wire a tool per
verb. It `discover()`s every `Capability` in the `capabilities/` package
(reflection) and AUTO-WIRES one MCP tool per verb from the verb function's
signature (`inspect.signature`). Adding a capability is adding a file — no
registration code, no per-tool boilerplate. Params named in a verb's `inject`
list (e.g. `client`, `caps`) are supplied by the engine, not the caller.
"""
from __future__ import annotations

import inspect
import re
from contextlib import asynccontextmanager

from fastmcp import Context, FastMCP

try:
    from fastmcp.experimental.transforms.code_mode import CodeMode, MontySandboxProvider
    HAVE_CODEMODE = True
except ImportError:  # pragma: no cover
    HAVE_CODEMODE = False


# Bounded sandbox limits — without these, an infinite loop or runaway
# allocation in an `execute` script ties up the whole MCP server. Codex
# review ccb8f03 / engine.py:94. Tunable via env: AGENCY_SANDBOX_MAX_SECS
# (default 30), AGENCY_SANDBOX_MAX_MEM_MB (default 512).
def _sandbox_limits() -> dict:
    import os as _os
    return {
        "max_duration_secs": float(_os.environ.get("AGENCY_SANDBOX_MAX_SECS", "30")),
        "max_memory": int(_os.environ.get("AGENCY_SANDBOX_MAX_MEM_MB", "512")) * 1024 * 1024,
    }

from .capabilities import discover_capabilities
from .capabilities._vcs import GitClient
from .capabilities.jules import JulesClient
from .capability import Registry
from .intent import Intent
from .lifecycle import Lifecycle
from .memory import Memory
from .ontology import Ontology
from .disclosure import parse_slices


_SURFACES = ("mcp", "bash")


def resolve_surface(arg: str | None = None) -> str:
    """Spec 023 §Done When — surface resolution.

    Precedence: arg > env (AGENCY_SURFACE) > auto. Auto resolution falls
    back to ``mcp`` (panel F3.2 — the more-capable surface is the safer
    default when introspection is unavailable; an MCP-equipped agent
    reading bash prose cannot execute it, but a bash agent reading MCP
    prose can still parse the structure).

    Inputs: arg (None/empty treated as unset).
    Returns: 'mcp' | 'bash'.
    chain_next: Engine.__init__ caches this on self.surface for the lifetime
                of the engine (deploy-time, not per-call).
    """
    if arg:
        if arg not in _SURFACES:
            raise ValueError(
                f"unknown surface {arg!r}; expected one of {_SURFACES}"
            )
        return arg
    import os as _os
    env = _os.environ.get("AGENCY_SURFACE", "").strip()
    if env in _SURFACES:
        return env
    # Unknown env value: silent fallback. Mistyping AGENCY_SURFACE should
    # not crash the engine — user-set env vars are common, surface is not
    # safety-critical.
    return "mcp"


def _capability_tier(registry) -> list:
    """Spec 068 — the tier-0 discovery payload: one line per capability
    (``{name, gist, verbs}`` — gist = the capability module's docstring first
    line; ``verbs`` = its verb count). This is the cheap entry the agent browses
    FIRST, then drills into one capability via ``search('<capability>')`` /
    ``get_schema`` — progressive disclosure at the discovery layer (CORE.md
    §Skills, Spec 072), far cheaper than a flat dump of every verb."""
    import sys
    tier = []
    for name in sorted(registry.names()):
        cap = registry.get(name)
        gist = getattr(cap, "home", "") or ""
        for spec in cap.verbs.values():
            fn = getattr(spec.get("fn"), "__capability_method__", spec.get("fn"))
            mod = sys.modules.get(getattr(fn, "__module__", "") or "")
            doc = (getattr(mod, "__doc__", "") or "").strip()
            if doc:
                g = doc.split("\n", 1)[0].strip()
                # strip the redundant leading "name — " (name is its own field)
                if g.lower().startswith(name.lower()):
                    g = g[len(name):].lstrip(" —–-:").strip() or g
                gist = g[:72].rstrip()
                break
        tier.append({"name": name, "gist": gist, "verbs": len(cap.verbs)})
    return tier


_SPEC_MD_RE = re.compile(r"(^|/)Plan/\d{3}-[^/]+/spec\.md$")

# ONE source of truth for raw-tool → agency-verb routing, read by BOTH the
# BoundaryUse shadow (Slice 1 provenance, mutating tools) AND the PreToolUse
# suggestion (Slice 2) so the two cannot drift. Each row:
# (predicate(tool, tool_input) -> bool, verb, why, suggest).
#
# `suggest` is the correctness gate (Codex review #154). A route is SUGGESTED
# only when the verb is a genuine agency COMPANION whose required args are known
# up-front and which is reachable from a normal session. Suggestions are
# ADVISORY — a companion that records provenance (Goal 2), NOT a drop-in
# replacement for the raw tool and NOT a deny/block — so the additionalContext is
# a nudge and the raw tool still runs (PreToolUse `additionalContext` is advisory
# by design; we deliberately do not deny/`updatedInput`). Routes without a true
# companion are shadow-only or omitted, never a false "call instead":
#   - git commit → branch.commit_smart: composes the conventional message
#     (companion run alongside the commit) → suggested.
#   - spec.md edit → dogfood.note: records the observation so it folds back
#     (Goal 6 companion to the edit) → suggested.
#   - git push → branch.finish: merge/pr, NOT a push — shadow-only.
#   - Grep/Glob: `search` is capability-DISCOVERY, not code search — omitted.
#   - Task: subagent.develop needs post-work gate results — omitted.
# Suggested verbs MUST resolve to a live MCP tool —
# `test_every_suggestion_resolves_to_a_live_verb` guards it (dormant-surface).
# AGENCY-DRIFT: raw-tool-routes — follow-up: derive via recommend.route / Spec
# 188 suggest_drill so the surface is discovered, not memorized.
_RAW_ROUTES: list[tuple] = [
    (lambda t, tin: t == "Bash"
        and str(tin.get("command") or "").strip().startswith("git commit"),
     "branch.commit_smart",
     "companion: compose the conventional-commit message via this verb",
     True),
    (lambda t, tin: t == "Bash"
        and str(tin.get("command") or "").strip().startswith("git push"),
     "branch.finish", "finish the branch (merge/pr) through the verb when done",
     False),
    (lambda t, tin: t in ("Write", "Edit")
        and bool(_SPEC_MD_RE.search(str(tin.get("file_path") or ""))),
     "dogfood.note",
     "companion: also record a spec observation so it folds back (Goal 6)",
     True),
]
# The guard's inventory of every SUGGESTED target (verb, why).
_ALL_SUGGESTIONS: list[tuple[str, str]] = [(v, w) for _p, v, w, s in _RAW_ROUTES if s]


def _route_for(tool: str, tool_input: dict):
    """The first `_RAW_ROUTES` row whose predicate matches → `(verb, why)`, or
    None. Used by the BoundaryUse SHADOW (provenance — any matching route)."""
    for pred, verb, why, _suggest in _RAW_ROUTES:
        if pred(tool, tool_input or {}):
            return verb, why
    return None


def _verb_shadow_for(tool: str, payload: dict) -> tuple[str, str]:
    """Spec 195 Slice 1 — the capability verb a raw MUTATING tool call BYPASSED
    (for the BoundaryUse node) + the FULL argument (command / file path). Reads
    the shared `_RAW_ROUTES` table; falls back to a generic shell.run /
    capability_verb_for shadow for an unmatched mutating tool. Only Write/Edit/Bash
    reach here (see `_default_hook_handler`). No-truncate policy: the argument is
    captured in full (warn-not-cut), so the moat audit records what actually ran."""
    from ._capture import keep_full
    route = _route_for(tool, payload)
    if tool == "Bash":
        cmd = keep_full(str(payload.get("command") or "").strip(), label="Bash command")
        if route is not None:
            return route[0], cmd
        head = cmd.split()[0] if cmd else ""
        return f"shell.run({head!r})", cmd
    if tool in ("Write", "Edit"):
        path = keep_full(str(payload.get("file_path") or ""), label=f"{tool} path")
        if route is not None:
            return route[0], path
        return f"capability_verb_for({path!r})", path
    return "", ""


def _suggest_mcp_calls(event: dict) -> list[tuple[str, str]]:
    """Spec 195 Slice 2 — the agency MCP call a raw tool should use INSTEAD,
    from `_RAW_ROUTES`. Only `suggest=True` rows are emitted (true effect-
    equivalents whose args are known up-front — Codex review #154)."""
    tool = (event or {}).get("tool_name") or ""
    tin = (event or {}).get("tool_input") or {}
    for pred, verb, why, suggest in _RAW_ROUTES:
        if suggest and pred(tool, tin):
            return [(verb, why)]
    return []


def _ann_to_json_type(annotation) -> str:
    """Best-effort Python annotation → JSON-schema type for a verb param.

    Handles BOTH real types and STRING annotations: capability verbs use
    `from __future__ import annotations`, so `inspect.signature` yields strings
    ('str', 'dict', 'int | None'); comparing those against real type objects
    would mistype every param as 'string' (the bug cli._ann_kind also guards)."""
    import typing
    name = (annotation if isinstance(annotation, str)
            else getattr(annotation, "__name__", ""))
    by_name = {"str": "string", "int": "integer", "float": "number",
               "bool": "boolean", "dict": "object", "list": "array",
               "Dict": "object", "List": "array"}
    # A `str | None` string annotation starts with the base type name.
    base = name.split("|", 1)[0].split("[", 1)[0].strip()
    if base in by_name:
        return by_name[base]
    origin = typing.get_origin(annotation)
    if origin is dict:
        return "object"
    if origin is list:
        return "array"
    return "string"


def _verb_input_schema(engine, cap: str, verb: str) -> dict | None:
    """The JSON-schema of a capability verb's CALLER params (intent_id/agent_id
    are auto-injected at the wire, so omitted). Derived from the live registry
    signature — Spec 195 Slice 2's "derive from the registry"."""
    import inspect
    try:
        capability = engine.registry.get(cap)
    except Exception:
        return None
    spec = getattr(capability, "verbs", {}).get(verb)
    if spec is None:
        return None
    fn = getattr(spec, "fn", None) or (spec.get("fn") if isinstance(spec, dict) else None)
    inject = set(getattr(spec, "inject", None)
                 or (spec.get("inject", []) if isinstance(spec, dict) else []))
    if fn is None:
        return None
    props: dict = {}
    required: list[str] = []
    for name, p in inspect.signature(fn).parameters.items():
        if name in ("self", "intent_id", "agent_id") or name in inject:
            continue
        if p.kind in (inspect.Parameter.VAR_POSITIONAL,
                      inspect.Parameter.VAR_KEYWORD):
            continue        # *args/**kwargs aren't wire params (mirrors _wire)
        props[name] = {"type": _ann_to_json_type(p.annotation)}
        if p.default is inspect.Parameter.empty:
            required.append(name)
    # The wire auto-injects intent_id from AGENCY_INTENT, but when that env var
    # is unset (or the agent must target a specific intent) the call hits the
    # SERVES guard. Surface intent_id as an OPTIONAL param so the agent can pass
    # it (Codex review #154); it stays out of `required` (the env default wins).
    props["intent_id"] = {"type": "string",
                          "description": "optional — defaults from AGENCY_INTENT"}
    return {"type": "object", "properties": props, "required": required}


def _resolve_mcp_suggestion(engine, suggestion: str) -> dict | None:
    """Resolve a `cap.verb` companion to a callable form.

    Codex review #154: in this plugin's code-mode the PUBLIC MCP tools are
    `search`/`get_schema`/`execute` — `capability_<cap>_<verb>` is NOT directly
    invocable from a normal session; verbs are reached via `execute`'s
    `call_tool`. So a suggestion resolves to `mcp__agency__execute` plus the
    `call_tool` snippet + the verb's input schema, not a bare `capability_*`."""
    if "." not in suggestion:
        return None
    cap, verb = suggestion.split(".", 1)
    schema = _verb_input_schema(engine, cap, verb)
    if schema is None:
        return None
    tool = f"capability_{cap}_{verb}"
    return {"mcp_tool": "mcp__agency__execute", "verb": tool, "schema": schema,
            "snippet": f'await call_tool("{tool}", {{...}})'}


def _pre_tool_use_handler(engine, event: dict) -> dict:
    """Spec 195 Slice 2 — the PreToolUse handler. Records the Event + BoundaryUse
    (via the default handler) and, when the raw tool has an agency COMPANION
    verb, returns it (reachable via `mcp__agency__execute`) + its schema as
    `hookSpecificOutput.additionalContext`. ADVISORY (a provenance companion,
    Goal 2 — not a replacement, not a deny): the raw tool still runs."""
    import json as _json
    base = _default_hook_handler(engine, event)
    calls = []
    for suggestion, why in _suggest_mcp_calls(event):
        resolved = _resolve_mcp_suggestion(engine, suggestion)
        if resolved is not None:
            calls.append({**resolved, "why": why})
    if calls:
        base["agency_suggestion"] = calls
        lines = ["This raw tool bypasses agency provenance. Advisory — run the "
                 "agency companion via `mcp__agency__execute` (the raw tool still "
                 "runs; this is a nudge, not a replacement):"]
        for c in calls:
            lines.append(f"- {c['why']}\n"
                         f"  via `{c['mcp_tool']}`: {c['snippet']}\n"
                         f"  args schema: {_json.dumps(c['schema'], sort_keys=True)}")
        base["hookSpecificOutput"] = {
            "hookEventName": "PreToolUse",
            "additionalContext": "\n".join(lines),
        }
    # Spec 349a — fan PreToolUse out to declared event subscriptions (the frugal
    # first-use hint is the reference subscriber); merge their fragments into
    # additionalContext. Dedup'd + fail-isolated in `_events.run`.
    from . import _events
    frags = _events.run(engine, "PreToolUse", event)
    if frags:
        ctx = (base.get("hookSpecificOutput") or {}).get("additionalContext", "")
        base["hookSpecificOutput"] = {
            "hookEventName": "PreToolUse",
            "additionalContext": "\n".join([ctx, *frags]) if ctx else "\n".join(frags),
        }
    return base


# Spec 336 S2 — the high-volume tool events routed to the ephemeral store, not
# the durable graph. Everything else stays a (low-volume) graph Event.
_TOOLCALL_EVENTS = frozenset({"PreToolUse", "PostToolUse"})


def _default_hook_handler(engine, event: dict) -> dict:
    """Spec 076 — the default event handler. The handler surface is an OPEN SET;
    register a per-event override via ``engine.register_hook_handler``.

    Spec 336 S2 — high-volume tool events (PreToolUse/PostToolUse) are captured in
    FULL into the EPHEMERAL tool-call store (``engine.toolcalls``), NOT as ``Event``
    nodes: keeping every tool call's full payload in the bi-temporal graph bloated
    session.db (~95% of nodes were Events). Lifecycle events
    (UserPromptSubmit/Stop/SubagentStop/SessionStart) still record a durable graph
    ``Event`` linked OBSERVED_DURING the active intent (``AGENCY_INTENT``). The
    ``toolcalls`` capability reads the store; the Stop-hook export distils it.

    No-truncate (Spec 336 S1): the captured input/response is stored in FULL —
    ``keep_full`` warns on an unusually large value instead of cutting it.

    Spec 195 Slice 1 — a raw mutating ``PreToolUse`` (Write/Edit/Bash) under an
    active intent ALSO records a typed ``BoundaryUse`` (the low-volume bypass
    SIGNAL) in the durable graph, independent of the capture reroute."""
    import json as _json
    import os as _os
    from ._capture import keep_full
    name = (event or {}).get("hook_event_name") or "unknown"
    session = (event or {}).get("session_id") or "unknown"
    tool = (event or {}).get("tool_name")
    iid = _os.environ.get("AGENCY_INTENT", "")

    if name in _TOOLCALL_EVENTS:
        # FULL capture to the ephemeral store — off the durable graph. A capture
        # failure must never break the session.
        phase = "pre" if name == "PreToolUse" else "post"
        # Spec 336 S3 / Spec 337 — EVERY captured tool's output is routed through
        # the per-tool capture-filter for a clean structured `filtered` view.
        # Bash uses the profile registry (Spec 337); non-Bash tools have their own
        # profiles (Read → locator, mcp__github__* → decision fields, etc.).
        # Capture & filter only — execution is unchanged; output_json is always FULL.
        filtered = ""
        try:
            from .capabilities.shell import capture_filter
            tin = event.get("tool_input") or {}
            resp = event.get("tool_response")
            tool_name = tool or ""
            if tool_name == "Bash":
                cmd = tin.get("command", "") if isinstance(tin, dict) else ""
            elif tool_name == "Read":
                cmd = tin.get("file_path", "") if isinstance(tin, dict) else ""
            elif tool_name in ("Edit", "Write"):
                cmd = tin.get("file_path", "") if isinstance(tin, dict) else ""
            else:
                cmd = _json.dumps(tin, default=str) if isinstance(tin, dict) else str(tin or "")
            out = resp if isinstance(resp, str) else (
                _json.dumps(resp, default=str) if resp else "")
            filtered = capture_filter(cmd, out, tool=tool_name, spec=None)
        except Exception:                                       # noqa: BLE001
            filtered = ""
        try:
            engine.toolcalls.record(
                phase=phase, tool=tool or "", session=session, intent=iid,
                input_json=keep_full(_json.dumps(event.get("tool_input") or {},
                                                 default=str), label=f"{name} input"),
                output_json=keep_full(_json.dumps(event.get("tool_response") or {},
                                                  default=str), label=f"{name} output"),
                filtered=filtered)
        except Exception:                                       # noqa: BLE001
            pass
        _record_boundary_use(engine, name, tool, event, session, iid)
        return {"recorded": None, "event": name, "toolcall": True}

    # --- lifecycle events: a durable graph Event (low-volume) ---
    props = {"name": name, "session": session}
    if tool:
        props["tool"] = tool
    eid = engine.memory.record("Event", props)
    # Spec 292 — the Session Graph: link the event into its Session node.
    if session and session != "unknown":
        sid = f"session:{session}"
        if engine.memory.recall(sid) is None:
            engine.memory.record("Session", {"session_id": session,
                                              "status": "open"}, node_id=sid)
        engine.memory.link(eid, sid, "IN_SESSION")
    if iid and engine.memory.recall_typed(iid, "Intent") is not None:
        engine.memory.link(eid, iid, "OBSERVED_DURING")
    return {"recorded": eid, "event": name}


def _record_boundary_use(engine, name, tool, event, session, iid) -> None:
    """Spec 195 — the BoundaryUse moat audit for raw mutating tools under an active
    intent. Stays in the durable graph (low-volume bypass signal), independent of
    the Spec 336 capture reroute. No-op without a valid active intent."""
    if not iid or engine.memory.recall_typed(iid, "Intent") is None:
        return
    if name != "PreToolUse" or tool not in ("Write", "Edit", "Bash"):
        return
    from ._capture import keep_full
    tin = event.get("tool_input") or {}
    verb_shadow, summary = _verb_shadow_for(tool, tin)
    target = keep_full(str(tin.get("command") or "")
               or str(tin.get("file_path") or ""), label=f"{tool} target")
    bid = engine.memory.record("BoundaryUse", {
        "tool":             tool,
        "argument_summary": summary or f"<{tool} no payload>",
        "target":           target,
        "verb_shadow":      verb_shadow,
        "intent_id":        iid,
        "session":          session,
    })
    engine.memory.link(bid, iid, "SERVES")


def _active_intent(engine, *, fallback_latest: bool = False):
    """The session's active intent as ``(intent_id, props)`` — the env-bound
    ``AGENCY_INTENT`` when valid, else (with ``fallback_latest``) the most
    recently recorded Intent. ``("", None)`` when none applies. Shared by the
    hook handlers (Spec 292)."""
    import os as _os
    iid = _os.environ.get("AGENCY_INTENT", "")
    props = engine.memory.recall_typed(iid, "Intent") if iid else None
    if props is not None:
        return iid, props
    if fallback_latest:
        intents = engine.memory.find("Intent")
        if intents:
            latest = max(intents, key=lambda n: n.get("vfrom", 0))
            return latest["id"], latest
    return "", None


def _user_prompt_submit_handler(engine, event: dict) -> dict:
    """Spec 292 — UserPromptSubmit injection (sync, blocking by doctrine).

    Records the Event AND returns an ``inject`` context block (surfaced to the
    prompt by the dispatcher) that wires in the ``intent`` + ``thinking``
    capabilities so the agent STARTS by surfacing assumptions and asking
    clarifying questions instead of guessing. This is the assumption-guard: the
    cheapest place to stop an agent acting on an unstated assumption is before
    the turn runs."""
    base = _default_hook_handler(engine, event)
    _, intent = _active_intent(engine)
    guard = (
        "[agency] Before acting, AVOID ASSUMPTIONS: list your load-bearing "
        "assumptions (intent.assumptions) and, if any are ambiguous or the "
        "request is underspecified, ASK clarifying questions FIRST "
        "(thinking.socratic / AskUserQuestion) rather than guessing.")
    if intent:
        ctx = (f"[agency] Active intent: {intent.get('purpose', '')} "
               f"— deliverable: {intent.get('deliverable', '')}; "
               f"acceptance: {intent.get('acceptance', '')}.")
        inject = ctx + "\n" + guard
    else:
        inject = ("[agency] No active intent — consider intent_bootstrap to "
                  "anchor this work.\n" + guard)
    # Spec 332 M1 — append the frugal discipline (compact every prompt, full at
    # ultra, nothing at off). Degrades silently: a render failure never breaks
    # the turn (the assumption-guard precedent).
    inject = _append_frugal(inject, prompt=True)
    return {**base, "inject": inject}


def _append_frugal(inject: str, *, prompt: bool) -> str:
    """Spec 332 M1 — append the frugal discipline to an inject block. ``prompt``
    True = the per-prompt cadence (compact, full at ultra); False = session
    start (always full). ``off`` adds nothing. Never raises."""
    try:
        from . import _frugal
        level = _frugal.frugal_level()
        if level == "off":
            return inject
        if prompt:
            mode = "full" if level == "ultra" else "compact"
            text = _frugal.render(level, mode=mode)
        else:
            # SessionStart: the configurable full help (Spec 348 mandatory wiring).
            text = _frugal.session_inject_text(level)
    except Exception:
        return inject
    if not text:
        return inject
    return (inject + "\n[agency] " + text) if inject else ("[agency] " + text)


def _session_start_handler(engine, event: dict) -> dict:
    """Spec 332 M1 / Spec 348 / Spec 349a — inject the full frugal discipline at
    session start, delivered VIA THE EVENT BUS with a once-per-session dedup so the
    deep card lands exactly ONCE even though SessionStart fires on startup AND
    resume AND every compaction (a direct inject repeated the heavy card each
    time). Records the Event (default handler) first; the `frugal.session_inject`
    subscriber returns the deep card (fail-open to EMIT). Degrades silently. Spec
    334 Slice 3 — also repair an existing config (add newly-registered sections),
    non-destructively."""
    from . import _events
    base = _default_hook_handler(engine, event)
    _maybe_repair_config()
    frags = _events.run(engine, "SessionStart", event)
    inject = "\n".join(f"[agency] {f}" for f in frags if f)
    return {**base, "inject": inject}


def _maybe_repair_config() -> None:
    """Spec 334 Slice 3 — repair an EXISTING ``.agency/config.yaml`` on session
    start: add any newly-registered sections non-destructively (a freshly
    installed capability's keys appear without clobbering user edits). It never
    CREATES a config — a hook must not scaffold ``.agency/`` into an arbitrary
    cwd; creation is ``install``/``setup``. Best-effort: never raises."""
    try:
        import os as _os
        from . import _config
        path = _config._resolve_config_path()
        if _os.path.exists(path):
            _config.config_scaffold(path)
    except Exception:
        pass


def _session_end_handler(engine, event: dict) -> dict:
    """Spec 292 — on SessionEnd, record the Event AND auto-archive the session
    as a Document (``document.session``): the four concepts — Intent · Capability
    · Lifecycle · Memory — are rendered into ``.agency/sessions/`` so a closed
    session is durable, not ephemeral. Best-effort: a missing intent or an
    archive failure never raises (a hook must never break session teardown)."""
    base = _default_hook_handler(engine, event)
    iid, _ = _active_intent(engine, fallback_latest=True)
    if not iid:
        return {**base, "archived": None}
    try:
        res, _ = engine.registry.invoke(
            engine.memory, iid, "document", "session",
            agent_id="agent:session-end", for_intent_id=iid)
        doc_id = res.get("document_id")
        # Attach the archived Document to the Session node + close the session,
        # so the Session Graph holds the restorable session-end snapshot.
        session = (event or {}).get("session_id") or "unknown"
        if doc_id and session != "unknown":
            sid = f"session:{session}"
            if engine.memory.recall(sid) is not None:
                engine.memory.link(doc_id, sid, "IN_SESSION")
                engine.memory.update(sid, {"status": "closed"})
        # Spec 336 S4 — distil the ephemeral tool-call capture into a durable
        # ToolcallExport (top calls + responses + new-spec suggestions) written to
        # .agency/sessions/. Best-effort: never breaks teardown.
        toolcall_export = None
        try:
            tx, _ = engine.registry.invoke(
                engine.memory, iid, "toolcalls", "export",
                agent_id="agent:session-end", apply=True)
            toolcall_export = tx.get("export_id")
        except Exception:                                       # noqa: BLE001
            pass
        return {**base, "archived": doc_id, "written": res.get("written"),
                "toolcall_export": toolcall_export}
    except Exception:                                           # noqa: BLE001
        return {**base, "archived": None}


class Engine:
    def __init__(self, path: str, jules_client=None, vcs_backend=None,
                 embedder=None, web_search=None, runner=None,
                 extra_capabilities=None, surface: str | None = None,
                 token_counter=None, skills_client=None, llm_client=None,
                 anthropic_driver=None, drivers=None,
                 sampling_enabled: bool | None = None,
                 _require_skill_doc: bool = True):
        self.surface = resolve_surface(surface)
        # Spec 336 S2 — the ephemeral tool-call store lives beside the graph db
        # (resolved lazily so a fresh engine on `:memory:` gets an in-memory store).
        self._db_path = path
        self._toolcalls = None
        # Spec 285 OQ3 — server-initiated sampling cost control. Explicit kwarg
        # wins; else AGENCY_SAMPLING_ENABLED env; else on. Read by HostBridge
        # (via CapabilityContext.host) + surfaced in agency_doctor.
        from ._host_bridge import sampling_enabled_default
        self.sampling_enabled = (sampling_enabled if sampling_enabled is not None
                                 else sampling_enabled_default())
        # Spec 286-A2 — the engine's boundary objects live in ONE place: the
        # DriverRegistry (`self.drivers`). The former triplication — bespoke
        # `self.<boundary>` attrs + a `DriverRegistry({...})` + a parallel
        # `injectors` lambda dict — collapses here:
        #   * an explicitly-injected boundary (the constructor kwarg, for test
        #     injection) registers as a CONCRETE driver and wins;
        #   * otherwise the per-boundary lazy DEFAULT registers as a FACTORY
        #     and is constructed on first `ctx.get_driver(name)`/`inject=[…]`
        #     use (the old `if x is None: import…; x=…()` resolution moves
        #     verbatim into the factory closure).
        # The bespoke `self.jules_client` / `.embedder` / … attributes are now
        # thin read-through properties over the registry (see below) so any
        # external code / test reading `engine.embedder` still resolves.
        from .capability import DriverRegistry
        self.drivers = DriverRegistry()

        def _factory(import_path, attr, *args):
            def make():
                mod = __import__(import_path, fromlist=[attr])
                return getattr(mod, attr)(*args)
            return make

        # name -> (injected boundary | None, lazy default factory). Spec 073 /
        # 045 / 044+052 / 082 / 083 / 092 / 147 rationale preserved per-boundary.
        _boundary_defaults = {
            # Spec 073 — toolchain runner (stubbable; default shells out).
            "runner":       (runner, _factory("agency._runner", "SubprocessRunner")),
            # boundary: the real Jules backend by default.
            "jules":        (jules_client, JulesClient),
            # boundary: real git/gh for workspace + branch.
            "vcs":          (vcs_backend, GitClient),
            # Spec 045 — semantic-recall backend. Default TF-IDF (zero-dep);
            # AGENCY_EMBEDDER=bge-small-en + [recall] extra activates BGE.
            "embedder":     (embedder, _factory("agency.capabilities._embed", "resolve_embedder")),
            # Spec 044 + 052 — web-search boundary. v1 default is the DuckDuckGo
            # zero-config client; env AGENCY_WEB_BACKEND can pick alternatives.
            "web_search":   (web_search, _factory("agency.capabilities.research._web", "resolve_web_search")),
            # Spec 082 — token-count boundary (count_tokens → tiktoken → proxy).
            "token_counter": (token_counter, _factory("agency._tokens", "resolve_token_counter")),
            # Spec 083 — Anthropic Skills API boundary (plugin.publish_skill).
            "skills_client": (skills_client, _factory("agency.capabilities.plugin._skills_client", "SkillsClient")),
            # Spec 092 G3 — the LLM-decider boundary (an `llm` Driver).
            "llm":          (llm_client, _factory("agency._llm", "LLMClient")),
            # Spec 147 — the canonical AnthropicDriver boundary. The SDK imports
            # lazily so this costs nothing without the [anthropic] extra.
            "anthropic":    (anthropic_driver, _factory("agency._drivers._anthropic", "AnthropicDriver")),
        }
        for _name, (_injected, _default_factory) in _boundary_defaults.items():
            if _injected is not None:
                self.drivers.register(_name, _injected)
            else:
                self.drivers.register_factory(_name, _default_factory)
        # Host-supplied extra drivers (Engine(..., drivers={...})) override the
        # defaults under the same name (e.g. music_state).
        if drivers:
            for _name, _driver in drivers.items():
                self.drivers.register(_name, _driver)

        self.registry = Registry()
        self.registry.engine = self                       # so CapabilityContext can reach engine-attached state
        self._onboarding_cache: dict | None = None        # Spec 302 — doctor probe cache
        self._extra_capabilities = list(extra_capabilities or [])  # Spec 302 — re-added on reload()
        self.ontology = Ontology.core()                         # the base, then each capability extends it
        # discovered core capabilities, plus any external ones the host supplies —
        # the extension point: an out-of-tree capability registers + extends exactly
        # like a core one (no need to live in the capabilities package).
        # Dedupe by capability name — discover() may already have
        # found a cap that the host also passes as `extra_capabilities`
        # (e.g. plugin.lint_capability re-registers the cap for
        # consumer-contract validation in an in-memory engine; without
        # dedupe the ontology.extend collides on skill/schema names).
        # First-wins: discover()'d caps take precedence over re-supplied
        # extras with the same name.
        seen_names: set[str] = set()
        for cap in list(discover_capabilities()) + list(extra_capabilities or []):
            if cap.name in seen_names:
                continue
            seen_names.add(cap.name)
            self._register_capability(cap)
        # the Registry needs the effective ontology to build a CapabilityContext
        self.registry.ontology = self.ontology
        # Spec 031 §A + Spec 080 — bootstrap-time skill_doc REQUIREMENT.
        # Every capability that declares verbs MUST declare a skill_doc; the
        # per-capability emit pipeline renders a complete Agent Skill from it
        # (SKILL.md + references/ + scripts/). Spec 080 migrated all shipped
        # capabilities + flipped this from opt-in to ALWAYS required: a
        # verb-bearing capability without a skill_doc is now a hard bootstrap
        # failure (fail loud at engine start, not silently at install time).
        for _cap_name in (self.registry.names() if _require_skill_doc else ()):
            _cap = self.registry.get(_cap_name)
            if _cap.verbs and getattr(_cap, "skill_doc", None) is None:
                raise ValueError(
                    f"capability {_cap_name!r} declares verbs but no skill_doc — "
                    f"add `skill_doc = SkillDoc(description='Use when …', "
                    f"overview='…', triggers=[…], canonical_example='…')` to "
                    f"the capability class per Spec 080 §coverage (co-located with "
                    f"the verbs — see any agency/capabilities/<cap>/_main.py), and "
                    f"validate via `develop.validate_skill('<cap>')`."
                )
        # Spec 002 / 286-A2 — the boundary table (built above) IS the source of
        # truth. The Registry's `inject=[...]` table is DERIVED from it: each
        # injector NAME maps to a driver NAME, and the lambda reads the live
        # registry (lazy default materialized on first use). `ctx.client` (the
        # `client` injector) resolves to the Jules driver, exactly as before.
        # A future boundary needs no new injectors key; verbs reach any driver
        # via `ctx.get_driver(name)`. The map is the ONLY place an injector
        # alias diverges from its driver name (`client` -> `jules`).
        self.registry.drivers = self.drivers
        _INJECTOR_TO_DRIVER = {
            "client": "jules", "vcs": "vcs", "embedder": "embedder",
            "runner": "runner", "skills_client": "skills_client",
        }
        self.registry.injectors = {
            inj: (lambda d=drv: self.drivers.get(d))
            for inj, drv in _INJECTOR_TO_DRIVER.items()
        }
        self.memory = Memory(path, ont=self.ontology)           # enforce the EFFECTIVE ontology
        self.intent = Intent(self.memory)
        # Spec 021 — the single engine Monitor channel. Capabilities fan events
        # in via ctx.emit_monitor(...); one tail -F on this log surfaces them.
        # Built BEFORE the Lifecycle so the substrate can emit transition
        # telemetry onto it (Spec 344).
        from ._monitor import MonitorEmitter, resolve_monitor_log_path
        self.monitor = MonitorEmitter(resolve_monitor_log_path(db_path=path))
        self.lifecycle = Lifecycle(self.memory, monitor=self.monitor)  # Spec 344 — emits transitions
        # Spec 076 — the unified hook-handler surface (open set). "*" is the
        # default catch-all; register_hook_handler adds per-event overrides.
        self._hook_handlers = {"*": _default_hook_handler,
                               "PreToolUse": _pre_tool_use_handler,
                               "UserPromptSubmit": _user_prompt_submit_handler,
                               "SessionStart": _session_start_handler,  # Spec 332 M1
                               "SessionEnd": _session_end_handler}

    # Spec 286-A2 — the bespoke boundary attributes are now thin read-through
    # properties over the DriverRegistry (`self.drivers`), the single source of
    # truth. External code / tests that read `engine.embedder` / `.jules_client`
    # / … still resolve (and materialize the lazy default on first read), but the
    # boundary lives in exactly one place. The property NAME maps to the driver
    # NAME (`jules_client` -> "jules", `vcs_backend` -> "vcs", `llm_client` ->
    # "llm", `anthropic_driver` -> "anthropic"; the rest are 1:1).
    @property
    def runner(self):
        return self.drivers.get("runner")

    @property
    def jules_client(self):
        return self.drivers.get("jules")

    @property
    def vcs_backend(self):
        return self.drivers.get("vcs")

    @property
    def embedder(self):
        return self.drivers.get("embedder")

    @property
    def web_search(self):
        return self.drivers.get("web_search")

    @property
    def token_counter(self):
        return self.drivers.get("token_counter")

    @property
    def skills_client(self):
        return self.drivers.get("skills_client")

    @property
    def llm_client(self):
        return self.drivers.get("llm")

    @property
    def anthropic_driver(self):
        return self.drivers.get("anthropic")

    @property
    def toolcalls(self):
        """Spec 336 S2 — the ephemeral tool-call store (lazy; beside the graph db,
        or in-memory for a `:memory:` engine). High-volume pre/post tool capture
        lives here, OFF the durable graph; the `toolcalls` capability reads it."""
        if self._toolcalls is None:
            from . import _toolcalls
            self._toolcalls = _toolcalls.ToolcallStore(
                _toolcalls.resolve_path(self._db_path))
        return self._toolcalls

    def register_hook_handler(self, event_name: str, fn) -> None:
        """Spec 076 — register a per-event hook handler (open set). ``fn(engine,
        event) -> dict``. Overrides the default for ``event_name``; use "*" to
        replace the catch-all."""
        self._hook_handlers[event_name] = fn

    def dispatch_hook(self, event: dict) -> dict:
        """Spec 076 — route ONE Claude Code hook event to its handler. The single
        dispatcher (`hooks/dispatch`) pipes every event here by name; an exact
        handler wins, else the "*" catch-all. Never raises on a malformed event —
        capture must not break the session."""
        name = (event or {}).get("hook_event_name") or "unknown"
        handler = self._hook_handlers.get(name) or self._hook_handlers.get("*")
        if handler is None:
            return {"recorded": None, "event": name, "skipped": True}
        return handler(self, event)

    def _shape_wire_result(self, result, inv: str) -> dict:
        """Spec 282 — shape the registry return into the wire dict.

        On a FAILED invocation, surface a TYPED error envelope carrying the
        severity (compat break, authorized): a bare ``null`` told the caller
        nothing, so the ingest driver retried every impossible call ~34×.
        Now the caller can branch on ``error.severity`` / ``error.retryable``
        and stop retrying ``permanent`` failures.

        On success, the lean code-mode contract is unchanged (Spec 001/019):
        an inner dict crosses as-is; a scalar is re-wrapped as
        ``{"result": <scalar>}`` because MCP returns must be JSON objects.

        Spec 286-A7: the shape rule lives in one place — :class:`WireEnvelope`.
        The engine only reads the recorded Invocation node (outcome / error /
        severity) and hands the parts to ``WireEnvelope.shape``; the envelope
        owns the strip/re-wrap + failure-envelope logic.
        """
        from ._wire_envelope import WireEnvelope
        node = self.memory.recall(inv) or {}
        shaped = WireEnvelope.shape(
            result,
            outcome=node.get("outcome"),
            error=node.get("error", "") or "",
            error_severity=node.get("error_severity") or "",
            trace_id=inv,
        )
        # Spec 332 M2 — stamp the frugal discipline on every verb's wire return
        # (byte-stable at a fixed level; `off`/`stamp_every_verb=false` omits it).
        # Additive + degrades silently: a stamp must never break or reshape a
        # verb that already speaks `frugal`.
        if isinstance(shaped, dict) and "frugal" not in shaped:
            try:
                from . import _frugal
                stamp = _frugal.frugal_prefix()
                if stamp:
                    shaped = {**stamp, **shaped}
            except Exception:
                pass
        return shaped

    def _wire(self, mcp: FastMCP, cap_name: str, verb: str, spec: dict) -> None:
        """Auto-wire ONE MCP tool for a capability verb from its fn signature.
        Injected params (`inject`) are resolved by the Registry, so they are not
        exposed in the tool's schema.

        Spec 001 + Spec 019 — wire-shape contract. Internal verbs return either
        a bare rich dict OR ``{"result": <delta>}``; the failure path now
        returns the Spec 282 typed error envelope. The shaping lives in
        ``_shape_wire_result`` so it is unit-testable without a live MCP."""
        reg, mem = self.registry, self.memory
        fn, inject = spec["fn"], list(spec.get("inject", []))
        user_params = [p for n, p in inspect.signature(fn).parameters.items() if n not in inject]

        def impl(**kwargs):
            # Spec 018 Win 3 — implicit intent default. An explicit intent_id
            # always wins; when omitted (or empty), fall back to the
            # AGENCY_INTENT env so a long session against ONE intent need not
            # repeat it on every call. With neither, the empty id flows to the
            # SERVES guard, which raises its helpful bootstrap error.
            import os as _os
            # Spec 285 — capture the live FastMCP Context (FastMCP injects it as
            # the `_host_ctx` kwarg, excluded from the tool schema because it is
            # annotated `Context`). Bind it request-scoped so capability verbs
            # reach `ctx.host` (sampling / elicitation); reset in `finally` so a
            # Context never outlives its call. None when no client is attached.
            from ._host_bridge import bind_host_context, reset_host_context
            host_ctx = kwargs.pop("_host_ctx", None)
            token = bind_host_context(host_ctx)
            try:
                intent_id = kwargs.pop("intent_id", "") or _os.environ.get("AGENCY_INTENT", "")
                agent_id = kwargs.pop("agent_id", "") or None
                result, inv = reg.invoke(mem, intent_id, cap_name, verb, agent_id=agent_id, **kwargs)
                return self._shape_wire_result(result, inv)
            finally:
                reset_host_context(token)

        # Spec 284 — projected-enum surfacing. A verb may declare
        # `param_enums={param: members}`; we wrap that param's annotation so the
        # tool's JSON inputSchema carries `enum` (surfaced by get_schema full
        # detail + raw MCP clients), and we fold a concise hint into the
        # description (the one field the code-mode `detailed` renderer shows).
        # `json_schema_extra` is schema-only — pydantic does NOT validate against
        # it, so rich free text still reaches the verb to be projected.
        param_enums = spec.get("param_enums") or {}
        enum_hints: list[str] = []
        params = []
        for p in user_params:
            ann = p.annotation if p.annotation is not inspect.Parameter.empty else str
            default = p.default if p.default is not inspect.Parameter.empty else inspect.Parameter.empty
            members = param_enums.get(p.name)
            if members:
                from typing import Annotated
                from pydantic import Field
                members_sorted = sorted(members)
                ann = Annotated[ann, Field(json_schema_extra={"enum": members_sorted})]
                enum_hints.append(f"{p.name} ∈ {{{', '.join(members_sorted)}}}")
            params.append(inspect.Parameter(p.name, inspect.Parameter.KEYWORD_ONLY, annotation=ann, default=default))
        # Spec 018 Win 3: intent_id is wire-optional (default "") so a call may
        # omit it and resolve via the AGENCY_INTENT env (see impl above).
        params.append(inspect.Parameter("intent_id", inspect.Parameter.KEYWORD_ONLY, annotation=str, default=""))
        params.append(inspect.Parameter("agent_id", inspect.Parameter.KEYWORD_ONLY, annotation=str, default=""))
        # Spec 285: a `Context`-annotated param FastMCP injects + excludes from
        # the tool's user-facing schema (same mechanism as lifecycle_gate's
        # `ctx`). Bound request-scoped in impl so verbs reach `ctx.host`.
        params.append(inspect.Parameter("_host_ctx", inspect.Parameter.KEYWORD_ONLY, annotation=Context, default=None))

        impl.__signature__ = inspect.Signature(params)
        impl.__name__ = f"capability_{cap_name}_{verb}"
        # Spec 023 Phase 3: tighten the FastMCP tool description to the BRIEF
        # slice (first-sentence) instead of the full docstring. Cuts ~58% of
        # catalog tokens; full doc remains reachable via get_schema.
        raw = (fn.__doc__ or "").strip()
        brief = parse_slices(raw)["brief"]
        doc = brief or raw or f"{cap_name}.{verb} ({spec['role']})"
        # Spec 284 — append the projected-enum members so they reach the
        # default code-mode `detailed`/`brief` view (which renders only the
        # description, not per-param enum/description).
        if enum_hints:
            doc = f"{doc} Enums: {'; '.join(enum_hints)}."
        impl.__doc__ = doc
        impl.__annotations__ = {p.name: p.annotation for p in params}
        impl.__annotations__["return"] = dict
        # Spec 025 R2 (Codex): propagate the verb's `tags` to FastMCP's Tool
        # metadata so `search(tags=["skill:*"])` actually finds the verb.
        # Without this the tags lived only on the internal verb spec and
        # the public discovery surface couldn't reach them.
        mcp.tool(impl, tags=set(spec.get("tags") or ()) or None)

    def _make_lifespan(self):
        """Build the FastMCP lifespan that starts the Jules watcher on enter
        and stops it cleanly on exit. Closes over `self` so the lifespan
        callable (which receives the FastMCP server, not the engine) can
        reach engine state. Idempotent — `jules.watch.start` only attaches
        a watcher if one isn't already present."""
        engine = self

        @asynccontextmanager
        async def lifespan(server):
            from agency.capabilities.jules import watch as _jules_watch
            from ._monitor import MonitorEvent
            engine.monitor.maybe_rotate()           # Spec 021 — bound the SLOG on session enter
            engine.monitor.emit(MonitorEvent(source="engine", kind="server_start",
                                             message="MCP server started"))
            _jules_watch.start(engine)              # attaches engine._jules_watcher + starts poll loop
            try:
                yield {}                             # lifespan state available via Context
            finally:
                await _jules_watch.stop(engine)     # cancels the poll loop cleanly
                engine.monitor.emit(MonitorEvent(source="engine", kind="server_stop",
                                                 message="MCP server stopped"))

        return lifespan

    def _drift_signals(self) -> dict:
        """Spec 054 — drift indicators surfaced via agency_doctor.

        Cheap checks only (file-existence lookups; no subprocesses).
        Heavy checks (install regen diff) live in scripts/check-drift.
        """
        import os
        # AGENCY-DRIFT: capability-list — a capability is "tested" if a
        # flat tests/test_<name>_*.py OR an acceptance tests/acceptance/
        # test_<name>.py exists (Spec 302: the acceptance-suite is the
        # primary convention now, so the flat-only check false-flagged
        # every acceptance-tested capability as untested).
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_files: set[str] = set()
        for sub in ("tests", os.path.join("tests", "acceptance")):
            d = os.path.join(repo_root, sub)
            if os.path.isdir(d):
                test_files |= set(os.listdir(d))
        missing_tests: list[str] = []
        for cap_name in self.registry.names():
            if cap_name.startswith("_"):
                continue
            if not any(f.startswith(f"test_{cap_name}_") or f == f"test_{cap_name}.py"
                       for f in test_files):
                missing_tests.append(cap_name)
        return {
            "capabilities_without_tests": sorted(missing_tests),
            "capability_count": len(self.registry.names()),
            "surface_freshness": self._surface_freshness(),
        }

    def _onboarding_probe(self) -> dict:
        """Spec 302 Slice 3 — time-to-first-successful-call: prove the critical
        path (discover → bootstrap an intent → invoke a verb → record provenance)
        actually works for a fresh user. Runs against a throwaway in-memory
        engine so it never pollutes the live graph; returns the wall-clock ms.

        Cached per engine lifetime (the path is deterministic for a fixed
        capability set) so repeated ``agency_doctor`` calls don't re-spin a full
        engine; ``reload()`` invalidates the cache."""
        if self._onboarding_cache is not None:
            return self._onboarding_cache
        import time
        t0 = time.perf_counter()
        probe = None
        try:
            probe = Engine(":memory:")
            iid = probe.intent.capture_and_confirm(
                "onboarding probe", "first verb call succeeds", "result returned")
            res, _ = probe.registry.invoke(
                probe.memory, iid, "reflect", "note",
                agent_id="agent:doctor", scope="observation", text="probe")
            ok = isinstance(res, dict) and not res.get("error")
            served = isinstance(res, dict) and probe.memory.has_edge(
                res.get("result", ""), iid, "SERVES")
            out = {"ok": bool(ok),
                   "ms": round((time.perf_counter() - t0) * 1000, 1),
                   "provenance_recorded": bool(served),
                   "steps": ["intent_bootstrap", "reflect.note", "SERVES edge"]}
        except Exception as exc:                                # noqa: BLE001
            out = {"ok": False, "error": str(exc)[:140]}
        finally:
            if probe is not None:
                probe.memory.close()
        self._onboarding_cache = out
        return out

    def _surface_freshness(self) -> dict:
        """Spec 302 — detect a STALE installed surface: compare the live
        capability-set hash against the one stamped into the generated
        ``.claude-plugin/plugin.json`` at last ``agency install``. A mismatch
        means capabilities changed but the plugin surface wasn't regenerated
        (so a running MCP client sees an out-of-date verb set). ``fresh=None``
        when no stamp is found (older install)."""
        import json
        import os
        from ._envelope import capability_set_hash
        live = capability_set_hash(self.registry.names())
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        manifest = os.path.join(repo_root, ".claude-plugin", "plugin.json")
        try:
            with open(manifest, encoding="utf-8") as f:
                recorded = json.load(f).get("_surface_hash", "")
        except (OSError, ValueError):
            recorded = ""
        fresh = (recorded == live) if recorded else None
        out = {"fresh": fresh, "live_hash": live[:12],
               "installed_hash": recorded[:12] if recorded else ""}
        if fresh is False:
            out["hint"] = ("installed plugin surface is stale — run "
                           "`python -m agency.install` to regenerate it")
        return out

    def build_mcp(self, codemode: bool = True) -> FastMCP:
        if codemode and not HAVE_CODEMODE:                  # fail loud, not a silent raw-tool fallback
            raise RuntimeError("code-mode requested but unavailable; install fastmcp[code-mode]")
        transforms = ([CodeMode(sandbox_provider=MontySandboxProvider(limits=_sandbox_limits()))]
                      if (codemode and HAVE_CODEMODE) else [])
        mcp = FastMCP("agency", transforms=transforms, lifespan=self._make_lifespan())

        # every capability verb -> one MCP tool, by reflection (no hand-wiring)
        for cap_name in self.registry.names():
            cap = self.registry.get(cap_name)
            for verb, spec in cap.verbs.items():
                self._wire(mcp, cap_name, verb, spec)

        # engine-substrate tools (not capabilities) — Spec 286 Phase 2 / A5.
        # Previously ~6-7 nested `@mcp.tool` closures over `self`/`mem`; now a
        # registered set of `SubstrateTool` objects (agency/_substrate_tools.py),
        # each `flagged requires_intent=False` — they legitimately bypass the
        # SERVES intent-guard (they mint/inspect; they don't SERVE an intent),
        # unlike every `capability_*_*` verb wired above. Each tool's `bind`
        # returns a function carrying the EXACT wire name/signature/docstring/
        # return shape it had inline, so FastMCP introspects an identical schema.
        from ._substrate_tools import SUBSTRATE_TOOLS
        for substrate_tool in SUBSTRATE_TOOLS:
            assert substrate_tool.requires_intent is False, (
                f"{substrate_tool.name}: substrate tools must bypass the "
                f"SERVES intent-guard (requires_intent=False)")
            mcp.tool(substrate_tool.bind(self))

        # Spec 023 Phase 3 (substrate parity): the @mcp.tool-decorated
        # substrate tools above carry their full docstrings into FastMCP's
        # catalog by default. _wire() already tightens capability verbs to
        # the brief slice; mirror the same treatment for substrate tools so
        # search results stay token-bounded regardless of how rich a
        # Hint-#7 docstring grows.
        for key, tool in self._iter_mcp_tools(mcp):
            name = getattr(tool, "name", "") or ""
            if name.startswith("capability_"):
                continue   # already tightened in _wire
            raw = (getattr(tool, "description", "") or "").strip()
            if not raw:
                continue
            brief = parse_slices(raw)["brief"]
            if brief and brief != raw:
                tool.description = brief

        self._mcp = mcp   # Spec 302 — held so agency_reload can wire new verbs in
        return mcp

    @staticmethod
    def _iter_mcp_tools(mcp):
        """Yield ``(key, tool)`` for every registered tool on a FastMCP server.
        The ONE place that reaches into FastMCP internals (``provider._components``)
        — fragile, pending a public tool-enumeration API; both the docstring-
        tightening loop and ``_wired_tool_names`` go through here."""
        for provider in getattr(mcp, "providers", ()):
            for key, tool in getattr(provider, "_components", {}).items():
                if key.startswith("tool:"):
                    yield key, tool

    def _wired_tool_names(self) -> set[str]:
        """Best-effort set of `capability_*` tool names registered on the live
        MCP server (Spec 302 — so reload only wires genuinely-new verbs)."""
        mcp = getattr(self, "_mcp", None)
        if mcp is None:
            return set()
        # keys look like `tool:capability_x_y@<provider>`; prefer the tool's own
        # clean .name, falling back to the parsed key.
        return {getattr(tool, "name", "") or key.split(":", 1)[1].split("@", 1)[0]
                for key, tool in self._iter_mcp_tools(mcp)}

    def _register_capability(self, cap) -> None:
        """Merge a capability's file-discovered templates/schemas into its
        ontology (Spec 060 Phase 1), register it, and extend the effective
        ontology. Shared by ``__init__`` and ``reload()`` so both bootstrap
        paths stay identical — a collision between an ``OntologyExtension`` dict
        entry and a same-named file is a doctrinal violation (force clean
        migrations)."""
        from ._capability_loader import load_capability_folders
        file_templates, file_schemas = load_capability_folders(cap)
        for tname, body in file_templates.items():
            if tname in cap.ontology.templates:
                raise ValueError(
                    f"template {tname!r} declared both in {cap.name}'s "
                    f"OntologyExtension and as a file under "
                    f"{cap.name}/templates/{tname}.* — pick one source")
            cap.ontology.templates[tname] = body
        for sname, schema in file_schemas.items():
            if sname in cap.ontology.schemas:
                raise ValueError(
                    f"schema {sname!r} declared both in {cap.name}'s "
                    f"OntologyExtension and as a file under "
                    f"{cap.name}/schemas/{sname}.json — pick one source")
            cap.ontology.schemas[sname] = schema
        self.registry.register(cap)
        self.ontology.extend(cap.ontology, cap.name)

    def reload(self) -> dict:
        """Spec 302 — re-discover capabilities mid-session WITHOUT restarting the
        server, picking up EDITED code (not just brand-new caps). Purges every
        ``agency.capabilities.*`` submodule from ``sys.modules`` so ``discover()``
        re-imports each capability — including its ``_main`` / ``clusters``
        submodules — fresh from disk, then rebuilds the registry + effective
        ontology IN PLACE and wires genuinely-new verbs onto the live MCP.
        Host-supplied ``extra_capabilities`` are preserved (re-added as-is).
        Code-mode `execute` reaches the new surface immediately; a non-code-mode
        client must re-list tools to see new verbs.

        Why a purge, not ``importlib.reload``: reloading a capability PACKAGE does
        not recurse into its submodules, so a verb edited in ``<cap>/_main.py``
        stayed cached. Purging forces a clean re-import of the whole subtree.

        Returns ``{reloaded, capability_count, capability_set_hash, added,
        removed, rewired_tools, reimported}``. Best-effort + fail-safe: an import
        error during re-discovery leaves the previous registry intact."""
        import sys
        from ._envelope import capability_set_hash
        from .capabilities import discover_capabilities
        from .ontology import Ontology

        before = set(self.registry.names())
        # Purge the capability subtree so the next import reads disk afresh. Keep
        # the ``agency.capabilities`` package itself (``discover`` lives there);
        # drop every submodule/subpackage beneath it (``…develop``,
        # ``…develop._main``, ``…prompt.clusters.frameworks``, …).
        purged = [m for m in list(sys.modules)
                  if m.startswith("agency.capabilities.")]
        for m in purged:
            sys.modules.pop(m, None)
        try:
            fresh = {c.name: c for c in discover_capabilities()}
            for cap in self._extra_capabilities:    # preserve host-supplied extras
                fresh.setdefault(cap.name, cap)
        except Exception as exc:                                # noqa: BLE001
            return {"reloaded": False, "error": str(exc),
                    "capability_count": len(before)}
        # rebuild the effective ontology + re-register caps in place, via the
        # SAME path as __init__ (so file templates/schemas re-merge too).
        self.ontology = Ontology.core()
        for name in list(self.registry._caps):
            if name not in fresh:
                self.registry._caps.pop(name, None)
        for cap in fresh.values():
            self._register_capability(cap)
        self.registry.ontology = self.ontology
        self.registry.engine = self
        self.memory.ont = self.ontology
        self._onboarding_cache = None    # capability set changed — re-probe lazily
        after = set(self.registry.names())
        # wire genuinely-new verbs onto the live MCP (existing ones re-dispatch).
        rewired = 0
        mcp = getattr(self, "_mcp", None)
        if mcp is not None:
            have = self._wired_tool_names()
            for cap_name in after:
                for verb, spec in self.registry.get(cap_name).verbs.items():
                    if f"capability_{cap_name}_{verb}" not in have:
                        try:
                            self._wire(mcp, cap_name, verb, spec)
                            rewired += 1
                        except Exception:                       # noqa: BLE001
                            pass
        return {"reloaded": True, "capability_count": len(after),
                "capability_set_hash": capability_set_hash(after),
                "added": sorted(after - before),
                "removed": sorted(before - after),
                "rewired_tools": rewired,
                "reimported": len(purged)}
