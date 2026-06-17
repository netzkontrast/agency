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

from .capabilities import discover
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


def _verb_shadow_for(tool: str, payload: dict) -> tuple[str, str]:
    """Spec 195 Slice 1 — derive the capability verb a raw tool call
    BYPASSED, plus a short argument summary for the BoundaryUse node.

    Hard-coded routing for the most common bypass patterns (mirrors the
    Spec 280 dispatcher advisory hints). Slice 2 derives this from the
    live registry via Spec 188 `suggest_drill`."""
    if tool == "Bash":
        cmd = str(payload.get("command") or "").strip()
        head = cmd.split()[0] if cmd else ""
        if cmd.startswith("git commit"):
            return "branch.commit_smart", cmd[:200]
        if cmd.startswith("git push"):
            return "branch.finish_branch", cmd[:200]
        if (cmd.startswith("pytest") or cmd.startswith("python -m pytest")
                or cmd.startswith("python3 -m pytest")):
            return "develop.test", cmd[:200]
        return f"shell.run({head!r})", cmd[:200]
    if tool in ("Write", "Edit"):
        import re as _re
        path = str(payload.get("file_path") or "")
        if _re.search(r"(^|/)Plan/\d{3}-[^/]+/spec\.md$", path):
            return "dogfood.observe", path[:200]
        return f"capability_verb_for({path!r})", path[:200]
    return "", ""


def _default_hook_handler(engine, event: dict) -> dict:
    """Spec 076 — the default event handler: record an `Event` node (substrate
    provenance, no intent required) and, for tool events, capture a trimmed
    payload via the shell filter. Links the Event OBSERVED_DURING the active
    intent (``AGENCY_INTENT`` — Spec 018 Win 3) when one is set, so events during
    an intent become its provenance. The handler surface is an OPEN SET; register
    a per-event override via ``engine.register_hook_handler``.

    Spec 195 Slice 1 — when the event is a `PreToolUse` on raw
    Write/Edit/Bash AND an active intent is set, ALSO record a typed
    `BoundaryUse{tool, target, verb_shadow, argument_summary, intent_id,
    session}` node so `dogfood.boundary_use_audit` can surface the
    bypass rate. SERVES the intent so a single graph traversal recovers
    the full audit."""
    import json as _json
    import os as _os
    name = (event or {}).get("hook_event_name") or "unknown"
    session = (event or {}).get("session_id") or "unknown"
    props = {"name": name, "session": session}
    tool = (event or {}).get("tool_name")
    if tool:
        props["tool"] = tool
        payload = event.get("tool_input") or event.get("tool_response") or {}
        from .capabilities.shell import _apply_filter
        props["summary"] = _apply_filter(_json.dumps(payload, default=str), "head:5")[:500]
    eid = engine.memory.record("Event", props)
    # Spec 292 — the Session Graph: link every event into a Session node keyed
    # by session_id, so the complete session is restorable from the graph.
    if session and session != "unknown":
        sid = f"session:{session}"
        if engine.memory.recall(sid) is None:
            engine.memory.record("Session", {"session_id": session,
                                              "status": "open"}, node_id=sid)
        engine.memory.link(eid, sid, "IN_SESSION")
    iid = _os.environ.get("AGENCY_INTENT", "")
    if iid and engine.memory.recall_typed(iid, "Intent") is not None:
        engine.memory.link(eid, iid, "OBSERVED_DURING")
        # Spec 195 Slice 1 — BoundaryUse capture for raw mutating tools.
        # PreToolUse is when the bypass actually happens; reads + post
        # events don't poison the moat (Open Q1: mutating-only).
        if name == "PreToolUse" and tool in ("Write", "Edit", "Bash"):
            tin = event.get("tool_input") or {}
            verb_shadow, summary = _verb_shadow_for(tool, tin)
            target = (str(tin.get("command") or "")
                       or str(tin.get("file_path") or ""))[:200]
            bid = engine.memory.record("BoundaryUse", {
                "tool":             tool,
                "argument_summary": summary or f"<{tool} no payload>",
                "target":           target,
                "verb_shadow":      verb_shadow,
                "intent_id":        iid,
                "session":          session,
            })
            engine.memory.link(bid, iid, "SERVES")
            engine.memory.link(bid, eid, "RECORDED_BY")
    return {"recorded": eid, "event": name}


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
    return {**base, "inject": inject}


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
        return {**base, "archived": doc_id, "written": res.get("written")}
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
        from ._capability_loader import load_capability_folders
        for cap in list(discover()) + list(extra_capabilities or []):
            if cap.name in seen_names:
                continue
            seen_names.add(cap.name)
            # Spec 060 Phase 1: merge file-discovered templates +
            # schemas INTO cap.ontology BEFORE the engine ontology
            # extends. Each entry is additive; a collision between an
            # OntologyExtension dict entry and a same-named file is
            # a doctrinal violation (force clean migrations).
            file_templates, file_schemas = load_capability_folders(cap)
            for tname, body in file_templates.items():
                if tname in cap.ontology.templates:
                    raise ValueError(
                        f"template {tname!r} declared both in "
                        f"{cap.name}'s OntologyExtension and as a file "
                        f"under {cap.name}/templates/{tname}.* — "
                        f"pick one source")
                cap.ontology.templates[tname] = body
            for sname, schema in file_schemas.items():
                if sname in cap.ontology.schemas:
                    raise ValueError(
                        f"schema {sname!r} declared both in "
                        f"{cap.name}'s OntologyExtension and as a file "
                        f"under {cap.name}/schemas/{sname}.json — "
                        f"pick one source")
                cap.ontology.schemas[sname] = schema
            self.registry.register(cap)
            self.ontology.extend(cap.ontology, cap.name)
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
        self.lifecycle = Lifecycle(self.memory)
        # Spec 021 — the single engine Monitor channel. Capabilities fan events
        # in via ctx.emit_monitor(...); one tail -F on this log surfaces them.
        from ._monitor import MonitorEmitter, resolve_monitor_log_path
        self.monitor = MonitorEmitter(resolve_monitor_log_path(db_path=path))
        # Spec 076 — the unified hook-handler surface (open set). "*" is the
        # default catch-all; register_hook_handler adds per-event overrides.
        self._hook_handlers = {"*": _default_hook_handler,
                               "UserPromptSubmit": _user_prompt_submit_handler,
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
        return WireEnvelope.shape(
            result,
            outcome=node.get("outcome"),
            error=node.get("error", "") or "",
            error_severity=node.get("error_severity") or "",
            trace_id=inv,
        )

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
            engine.monitor.maybe_rotate()           # Spec 021 — bound the SLOG on session enter
            _jules_watch.start(engine)              # attaches engine._jules_watcher + starts poll loop
            try:
                yield {}                             # lifespan state available via Context
            finally:
                await _jules_watch.stop(engine)     # cancels the poll loop cleanly

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
            "capability_count": len(list(self.registry.names())),
            "surface_freshness": self._surface_freshness(),
        }

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
        live = capability_set_hash(list(self.registry.names()))
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        manifest = os.path.join(repo_root, ".claude-plugin", "plugin.json")
        recorded = ""
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
        for provider in getattr(mcp, "providers", ()):
            for key, tool in getattr(provider, "_components", {}).items():
                if not key.startswith("tool:"):
                    continue
                name = getattr(tool, "name", "") or ""
                if name.startswith("capability_"):
                    continue   # already tightened in _wire
                raw = (getattr(tool, "description", "") or "").strip()
                if not raw:
                    continue
                brief = parse_slices(raw)["brief"]
                if brief and brief != raw:
                    tool.description = brief

        return mcp
