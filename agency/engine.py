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
        self._hook_handlers = {"*": _default_hook_handler}

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
        """
        from .toolresult import Severity, classify_severity
        node = self.memory.recall(inv) or {}
        if node.get("outcome") == "failed":
            err = node.get("error", "") or ""
            code, sep, msg = err.partition(": ")
            if not sep:                       # error string had no "code: msg" split
                code, msg = "", err
            sev = node.get("error_severity") or classify_severity(code, message=msg)
            return {"ok": False, "error": {
                "code": code, "message": msg, "severity": sev,
                "retryable": sev == Severity.TRANSIENT, "trace_id": inv}}
        out = result["result"] if isinstance(result, dict) and "result" in result else result
        return out if isinstance(out, dict) else {"result": out}

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
        # AGENCY-DRIFT: capability-list — capabilities without a
        # tests/test_<name>_*.py file convention; Spec 053 markers
        # depend on the file-naming convention.
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tests_dir = os.path.join(repo_root, "tests")
        missing_tests: list[str] = []
        if os.path.isdir(tests_dir):
            test_files = set(os.listdir(tests_dir))
            for cap_name in self.registry.names():
                if cap_name.startswith("_"):
                    continue
                if not any(f.startswith(f"test_{cap_name}_") or
                            f == f"test_{cap_name}.py"
                            for f in test_files):
                    missing_tests.append(cap_name)
        return {
            "capabilities_without_tests": sorted(missing_tests),
            "capability_count": len(list(self.registry.names())),
        }

    def build_mcp(self, codemode: bool = True) -> FastMCP:
        if codemode and not HAVE_CODEMODE:                  # fail loud, not a silent raw-tool fallback
            raise RuntimeError("code-mode requested but unavailable; install fastmcp[code-mode]")
        transforms = ([CodeMode(sandbox_provider=MontySandboxProvider(limits=_sandbox_limits()))]
                      if (codemode and HAVE_CODEMODE) else [])
        mcp = FastMCP("agency", transforms=transforms, lifespan=self._make_lifespan())
        mem = self.memory

        # every capability verb -> one MCP tool, by reflection (no hand-wiring)
        for cap_name in self.registry.names():
            cap = self.registry.get(cap_name)
            for verb, spec in cap.verbs.items():
                self._wire(mcp, cap_name, verb, spec)

        # engine-substrate tools (not capabilities): a human-in-the-loop gate that
        # needs `ctx.elicit`, and the provenance traversal over the graph.
        @mcp.tool
        async def lifecycle_gate(question: str, intent_id: str, lifecycle_id: str, ctx: Context) -> dict:
            "An intent-verification gate that ELICITS a human/agent decision mid-flow "
            "(askuser-in-the-flow): a tiny prompt streams out, the answer resumes the chain. "
            "Records the outcome to the provenance graph."
            # guard: the lifecycle must SERVE the given intent (no cross-intent gates)
            if not mem.g.query("MATCH (l:Lifecycle)-[:SERVES]->(i:Intent) "
                               "WHERE l.id = $lid AND i.id = $iid RETURN i",
                               {"lid": lifecycle_id, "iid": intent_id}):
                return {"approved": False, "error": "lifecycle does not serve the given intent"}
            res = await ctx.elicit(question, response_type=["approve", "reject"])
            approved = getattr(res, "data", None) == "approve"
            g = mem.record("Gate", {"name": "human-confirm", "question": question, "passed": approved})
            mem.link(lifecycle_id, g, "PASSED" if approved else "BLOCKED_ON")
            if not approved:                              # a rejected gate pauses the lifecycle for re-entry
                mem.update(lifecycle_id, {"state": "input-required"})
            return {"approved": approved, "gate_id": g}

        @mcp.tool
        def memory_graph_provenance(intent_id: str) -> dict:
            "Cross-concern provenance for an intent — one graph traversal."
            return mem.provenance(intent_id)

        @mcp.tool
        def hook_event(event: dict) -> dict:
            """Route ONE Claude Code hook event to its handler (Spec 076).

            Substrate — NO intent required (like intent_bootstrap). The single
            `hooks/dispatch` entry pipes every event's stdin JSON here; the engine
            routes by ``hook_event_name`` to a registered handler (open set),
            recording an Event node and linking it OBSERVED_DURING the active
            AGENCY_INTENT when set.

            Inputs: event (the hook payload dict — carries hook_event_name,
                    session_id, and event-specific fields).
            Returns: ``{recorded: <event_id|None>, event: <name>, …}``.
            chain_next: terminal — the event is provenance in the graph.
            """
            return engine.dispatch_hook(event or {})

        # Spec 029 §A — engine-substrate bootstrap tools. Substrate, not capability:
        # they live outside the per-capability auto-wire because intent_bootstrap
        # mints the FIRST Intent (no existing intent_id to SERVES against) and
        # agency_welcome / agency_install are pure introspection / scaffold ops.
        # Naming follows the existing substrate convention (lifecycle_gate /
        # memory_graph_provenance) — flat names, no capability_ prefix.
        engine = self

        @mcp.tool
        def intent_bootstrap(purpose: str, deliverable: str, acceptance: str,
                             parent_intent_id: str = "",
                             owner: str = "") -> dict:
            """Mint AND confirm an Intent — the canonical MCP bootstrap.

            The ONLY substrate tool that does not require an existing
            ``intent_id`` (every capability verb does — see the SERVES guard
            in ``capability.py``). Returns ``{intent_id, status, owner,
            parent_intent_id, next}``. Isomorphic with ``python -m
            agency.cli intent …``.

            Spec 048 — Intent chaining + owners:
              - ``parent_intent_id`` (optional) — link this intent back to
                an existing parent via PARENT_INTENT, so a complete session
                traces to the root user-prompt intent.
              - ``owner`` (optional) — closed enum: user / agent / subagent
                / jules / system. Default-by-presence: 'user' when no
                parent; 'agent' when a parent is supplied.

            Inputs:
              - ``purpose`` (str, required) — non-empty: the why
              - ``deliverable`` (str, required) — non-empty: the what
              - ``acceptance`` (str, required) — non-empty: how to verify
              - ``parent_intent_id`` (str, optional) — Spec 048 chain anchor
              - ``owner`` (str, optional) — Spec 048 owner enum override
            Returns: ``{intent_id, status: "confirmed", owner,
            parent_intent_id, next: <example>}``
            chain_next: pass ``intent_id`` to any ``capability_*_*`` verb.
            """
            # Spec 029 §A error contract (Wiegers/Nygard): name the field
            # in the message so the caller can fix the call without grep.
            for field, value in (("purpose", purpose),
                                  ("deliverable", deliverable),
                                  ("acceptance", acceptance)):
                if not value or not value.strip():
                    raise ValueError(
                        f"intent_bootstrap: {field!r} must be non-empty")
            iid = engine.intent.capture_and_confirm(
                purpose, deliverable, acceptance,
                parent_intent_id=parent_intent_id, owner=owner)
            # Read back the resolved owner (default-by-presence may have
            # applied) so the caller sees the truth, not their hint.
            resolved = engine.memory.recall(iid) or {}
            example = (
                "await call_tool('capability_plugin_help', "
                f"{{'intent_id': '{iid}'}})"
            )
            return {
                "intent_id": iid,
                "status": "confirmed",
                "owner": resolved.get("owner", "user"),
                "parent_intent_id": resolved.get("parent_intent_id", ""),
                "next": example,
            }

        @mcp.tool
        def agency_install(target: str = "") -> dict:
            """Scaffold .agency/ + a CLAUDE.md onboarding snippet in the target repo.

            Closes the missing MCP install path: previously only available
            via ``python -m agency.install --scaffold-db``. Idempotent —
            re-running on a populated tree is a no-op for any file already
            present. The CLAUDE.md snippet is bounded by explicit markers,
            so user content outside the markers is never touched.

            Inputs:
              - ``target`` (str, optional) — default = ``CLAUDE_PROJECT_DIR``
                env → cwd (mirrors the Spec 020 scaffold target).
            Returns: ``{target, scaffolded, gitattributes_updated,
                       claude_md_path, claude_md_updated, next}``.
            chain_next: ``intent_bootstrap`` to mint the first Intent.
            """
            from .install import install_op
            return install_op(target or None)

        @mcp.tool
        def agency_doctor(_host_ctx: Context = None) -> dict:
            """Health-check substrate tool — diagnose silent-failure modes.

            Reports python version, dep imports, DB reachability, and the
            two env vars users hit problems with (JULES_API_KEY,
            CLAUDE_PROJECT_DIR). The KEY VALUE is NEVER in the report —
            only its presence/absence. ``next_steps`` carries
            copy-pasteable fixes for any issue found.

            Covers F2 (Jules-key inheritance) + F5 (system python3 vs
            plugin venv) from the KP Fehlerbericht.

            Spec 285 — the ``host`` block reports whether the live client
            supports MCP sampling / elicitation and whether the
            ``sampling_enabled`` cost flag is on, so a session can see if it's
            in sample/elicit mode or envelope-fallback mode.

            Inputs: none.
            Returns: ``{ok, python_version, deps, db, env, host, next_steps}``.
            chain_next: ``next_steps`` are literal calls/commands.
            """
            from ._host_bridge import HostBridge
            _bridge = HostBridge(_host_ctx, sampling_enabled=engine.sampling_enabled)
            host_block = {
                "sampling": _bridge.can_sample(),
                "elicitation": _bridge.can_elicit(),
                "sampling_enabled": engine.sampling_enabled,
            }
            import os, sys, importlib.metadata as _md
            from ._db_path import resolve_db_path

            deps: dict = {}
            for name in ("fastmcp", "graphqlite", "tiktoken"):
                try:
                    deps[name] = _md.version(name)
                except _md.PackageNotFoundError:
                    deps[name] = "missing"

            db_path = resolve_db_path(None)
            db_exists = os.path.exists(db_path)
            try:
                parent = os.path.dirname(db_path) or "."
                db_writable = (
                    os.access(parent, os.W_OK) if os.path.isdir(parent)
                    else (os.access(os.path.dirname(parent) or ".", os.W_OK))
                )
            except OSError:
                db_writable = False

            jules_status = "set" if os.environ.get("JULES_API_KEY") else "missing"
            project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

            next_steps: list = []
            if deps.get("graphqlite") == "missing":
                next_steps.append(
                    "graphqlite missing — install the plugin venv: "
                    "`pip install -e .[dev]` from the agency repo "
                    "(F5: system python3 silent-fail)"
                )
            if deps.get("fastmcp") == "missing":
                next_steps.append(
                    "fastmcp missing — `pip install 'fastmcp[code-mode]>=3.3.0'`"
                )
            if not db_writable:
                next_steps.append(
                    f"DB path {db_path!r} parent not writable — "
                    f"call `agency_install` to scaffold .agency/ or fix perms"
                )
            if jules_status == "missing":
                next_steps.append(
                    "JULES_API_KEY missing — set `user_config.jules_api_key` "
                    "in the plugin's Claude Code config, then RELOAD the "
                    "plugin (the server reads the value at start time only). "
                    "For Jules / no-MCP: `export JULES_API_KEY=...` before "
                    "launching."
                )
            # Spec 055 (pipx-only doctrine, 2026-06-03): the install
            # method is exactly one of {pipx-or-pip-on-path, degraded}.
            # Legacy enums (marketplace-venv, marketplace-shim) were
            # removed alongside bin/agency-install + .venv bootstrap.
            import shutil
            agency_mcp_on_path = shutil.which("agency-mcp")
            agency_on_path = shutil.which("agency")
            if agency_mcp_on_path:
                install_method = "pipx-or-pip-on-path"
            else:
                install_method = "degraded"
                next_steps.append(
                    "agency-mcp not on PATH — install via "
                    "`pipx install git+https://github.com/netzkontrast/agency`."
                )

            # Spec 045 §"agency_doctor reports embedder": surface a silent
            # fallback. Differentiate the two failure modes — known backend
            # with missing dep (actionable: install) vs. unknown backend
            # name (actionable: fix the env var). Single source of truth
            # for the known set lives in _embed.KNOWN_EMBEDDERS.
            requested_emb = os.environ.get("AGENCY_EMBEDDER", "").strip()
            if requested_emb and requested_emb != self.embedder.name:
                from .capabilities._embed import KNOWN_EMBEDDERS
                if requested_emb == "bge-small-en":
                    next_steps.append(
                        "AGENCY_EMBEDDER='bge-small-en' requested but "
                        "sentence-transformers is not installed — "
                        "`pip install -e .[recall]` to enable."
                    )
                elif requested_emb not in KNOWN_EMBEDDERS:
                    valid = ", ".join(repr(b) for b in sorted(KNOWN_EMBEDDERS))
                    next_steps.append(
                        f"AGENCY_EMBEDDER={requested_emb!r} is not a known "
                        f"backend; resolved to {self.embedder.name!r}. "
                        f"Valid values: {valid}."
                    )

            # Spec 050 — report which `[analyze]` extras are
            # installed. Each wrapper degrades silently, but users
            # benefit from knowing whether ruff/bandit/radon are
            # active.
            # AGENCY-DRIFT: analyze-extras-list — keep this tuple
            #   synced with pyproject [analyze] extras AND the
            #   wrapper modules in agency/capabilities/analyze/.
            analyze_extras: dict[str, str] = {}
            for tool in ("ruff", "bandit", "radon"):
                if shutil.which(tool):
                    try:
                        analyze_extras[tool] = _md.version(tool)
                    except _md.PackageNotFoundError:
                        analyze_extras[tool] = "on-path"
                else:
                    analyze_extras[tool] = "missing"

            # Spec 280 Slice 1 — hooks install verification + foreign-hook
            # wrapping. Reads `.claude/settings.json` (project-level) and
            # reports plugin-enabled, CLI-on-PATH, hook-scripts-present,
            # any foreign hooks detected. `next_steps` aggregates repair
            # pointers.
            from ._hooks import check_install
            import json as _json
            settings_path = (
                os.path.join(project_dir, ".claude", "settings.json")
                if project_dir
                else os.path.join(os.getcwd(), ".claude", "settings.json"))
            user_settings: dict = {}
            try:
                with open(settings_path) as _f:
                    user_settings = _json.load(_f)
            except (FileNotFoundError, _json.JSONDecodeError, OSError):
                user_settings = {}
            # Codex review on PR #138: in a normal marketplace/pipx
            # install the running `agency-mcp` code is imported from
            # pipx/site-packages, but the hook files live in the
            # Claude plugin tree at `${CLAUDE_PLUGIN_ROOT}/hooks`.
            # Prefer that env var when set so the doctor reports
            # `hook_scripts_present=True` in the actual install layout;
            # fall back to `__file__` only for source-tree usage.
            plugin_root = (
                os.environ.get("CLAUDE_PLUGIN_ROOT")
                or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            hooks_status = check_install(
                user_settings,
                env={"AGENCY_SETTINGS_PATH": settings_path},
                plugin_root=plugin_root,
                cli_available=bool(agency_on_path),
            )
            # Hook next-steps stay on `doctor.hooks.next_steps` —
            # informational surface for users who want hooks to fire.
            # They are NOT rolled into the doctor's top-level `next_steps`
            # because plugin-enabled / cli-on-path are USER concerns
            # (a maintainer working in the agency repo intentionally has
            # neither in CI); flipping the `ok` invariant on them would
            # erode the doctor's health contract (Spec 030).

            return {
                "ok": len(next_steps) == 0,
                "python_version": ".".join(str(v) for v in sys.version_info[:3]),
                "deps": deps,
                "db": {"path": db_path, "exists": db_exists, "writable": db_writable},
                "env": {
                    "JULES_API_KEY": jules_status,
                    "CLAUDE_PROJECT_DIR": project_dir,
                },
                # Spec 280 — hooks install verification.
                "hooks": hooks_status.to_dict(),
                # Spec 045 / 286-A2 — the live semantic-recall backend, read
                # uniformly from the DriverRegistry (so users can confirm whether
                # AGENCY_EMBEDDER took effect, or the BGE→TF-IDF fallback fired).
                # The embedder reports its identity via `.name`, not `.backend`.
                "embedder": self.drivers.get("embedder").name,
                # Spec 082 / 286-A2 — the live token-count backend (count_tokens /
                # tiktoken / proxy), so a silent fallback to the proxy is visible.
                "token_backend": self.drivers.backend("token_counter"),
                # Spec 092 G3 / 286-A2 — the live LLM-decider backend (openrouter /
                # anthropic / none), never the key. Custom-injected clients may
                # omit backend() — the registry returns "custom".
                "llm_backend": self.drivers.backend("llm"),
                # Spec 147 / 286-A2 — the canonical AnthropicDriver readiness
                # (api-key-present / model-id-resolved / managed-agents-capable),
                # never the key. Custom-injected drivers may omit readiness().
                "anthropic_driver": self.drivers.readiness("anthropic"),
                # Spec 050 — which optional [analyze] tools are active.
                "analyze_extras": analyze_extras,
                # Spec 054 — drift indicators. v1 ships the
                # capabilities_without_tests check (cheap; just file
                # lookup); install-regen-drift defers to the
                # scripts/check-drift script (would require a heavy
                # subprocess otherwise).
                "drift": self._drift_signals(),
                # Spec 039 §"Distribution" line 101-102: which install
                # method is the running server using? Helps users debug
                # pipx-vs-marketplace mismatches and the install-
                # collision guard (line 86-91 — silent shadow detection).
                "install_method": install_method,
                "agency_mcp_path": agency_mcp_on_path or "",
                "agency_path": agency_on_path or "",
                "host": host_block,
                "next_steps": next_steps,
            }

        @mcp.tool
        def agency_welcome() -> dict:
            """One-shot onboarding payload — the canonical first call.

            Replaces the "read three files to know how to start" tax on
            fresh MCP clients. Returns the wire contract, code-mode
            chaining example, the bootstrap example, the live capability
            map, the walkable discipline-skills roster, and the resolved
            graph DB path. No ``intent_id`` required (pure introspection —
            no graph writes regardless of caller state).

            Inputs: none.
            Returns: ``{wire_contract, code_mode_example, bootstrap_example,
                       install_example, capabilities, capability_tier,
                       discipline_skills, docs, db_path, next}``.
            ``wire_contract`` (CORE.md) names the 3 lean substrate tools —
            ``search`` · ``get_schema`` · ``execute`` — every other call
            travels through ``execute`` as a chained Python block (one
            return crosses the wire, no per-call overhead). ``code_mode_example``
            shows the canonical chain: bootstrap an intent, call a verb,
            note a reflection — all in one block. ``capability_tier``
            (Spec 068) is the tier-0 discovery payload (one line per
            capability — browse it, then drill into ONE via
            ``search('<capability>')`` instead of dumping every verb).
            ``discipline_skills`` (Spec 114) lists the walkable skills
            that should be walked rather than improvised on every
            session: brainstorm / implement / skill_walk / session_init.
            chain_next: call ``execute`` with the code_mode_example as
            template; substitute the verb names for your task.
            """
            from ._db_path import resolve_db_path
            # Spec 029 OQ-3: token budget bit. Names-only keeps the welcome
            # payload under 1 KB regardless of how many verbs each capability
            # carries; agents discover verbs by calling capability_plugin_help
            # or search('<keyword>') with the intent_id from intent_bootstrap.
            caps = sorted(engine.registry.names())
            # Spec 030 §C — state-aware onboarding. The welcome doubles as a
            # session-resumption tool: a fresh graph leads with bootstrap,
            # a populated one leads with discovery + provenance.
            intents = list(engine.memory.find("Intent"))
            intents_count = len(intents)
            last_intent = ""
            if intents:
                # newest first by valid-from (graphqlite's bi-temporal stamp)
                last = max(intents, key=lambda r: r.get("vfrom", 0))
                last_intent = last.get("id", "") or ""
            state = "in_progress" if intents_count > 0 else "fresh"
            if state == "fresh":
                next_steps = [
                    "agency_install — scaffold .agency/ if missing",
                    "intent_bootstrap — mint the intent every verb SERVES",
                    "execute(code_mode_example) — chain verbs in one block",
                ]
            else:
                next_steps = [
                    f"search('<keyword>') — discover a capability_*_* verb",
                    f"memory_graph_provenance('{last_intent}') — see what served the last intent",
                    "execute(code_mode_example) — chain verbs in one block",
                ]
            # Spec 114 §"verb-first action routing" — walkable skills
            # bounding session work. Names only; drill via `search`.
            discipline_skills = [
                "develop.brainstorm", "develop.write_spec",
                "develop.implement", "develop.skill_walk",
                "develop.session_init",
            ]
            # Spec 146 Slice 1 — output-prefix discipline. Split the welcome
            # payload into a cache-friendly `prefix` (byte-stable across calls
            # when the registry is unchanged) and a per-call `body`. The
            # wrapping LLM driver applies `cache_control: {type:"ephemeral"}`
            # on the prefix; per-call churn (state, intents_count, last_intent,
            # db_path, next) lives in `body` and never invalidates the cache.
            from ._envelope import (
                ResponseEnvelope,
                capability_set_hash,
                ontology_hash,
            )
            prefix = {
                # Per-build identity — what THIS substrate build is.
                "schema_version": 1,
                "capability_set_hash": capability_set_hash(caps),
                "ontology_hash": ontology_hash(engine.ontology.nodes),
                # Spec 282 Workstream G — sandbox constraints surfaced up front
                # so an agent batches correctly instead of discovering the
                # limits by failing mid-ingest (the KP run hit both). The
                # welcome budget was loosened (user directive 2026-06-13) so
                # this onboarding field can read clearly rather than cramped.
                "sandbox_constraints": {
                    "max_call_tool_per_execute_block": 50,
                    "no_file_io": ("no open() in the code-mode sandbox — persist "
                                   "via capability verbs, not the filesystem"),
                    "partial_writes_persist": ("a failed call_tool aborts the rest "
                                               "of the block, but prior graph writes "
                                               "are NOT rolled back — make batches "
                                               "idempotent against ground truth"),
                    "guidance": ("batch <=45 call_tool per block; split larger work "
                                 "across blocks or use the CLI lane "
                                 "(python -m agency.cli execute)"),
                },
                # CORE.md — the lean wire contract. EVERY interaction is one
                # of these three; per-verb tools are reached via `execute` as
                # chained call_tool() within a Python block.
                "wire_contract": ["search", "get_schema", "execute"],
                # CORE.md — `execute` runs ONE Python block; chained
                # `await call_tool(...)` calls cross no extra wire hops; one
                # return value crosses back. The example is the canon.
                "code_mode_example": (
                    "execute({'code': '''\n"
                    "iid = (await call_tool(\"intent_bootstrap\","
                    " {\"purpose\":\"<why>\",\"deliverable\":\"<what>\","
                    "\"acceptance\":\"<verify>\"}))[\"intent_id\"]\n"
                    "r = await call_tool(\"capability_<cap>_<verb>\","
                    " {\"intent_id\": iid, \"agent_id\":\"agent:me\"})\n"
                    "await call_tool(\"capability_reflect_note\","
                    " {\"intent_id\": iid, \"agent_id\":\"agent:me\","
                    " \"scope\":\"observation\",\"text\":\"<lesson>\"})\n"
                    "return r\n'''})"
                ),
                "bootstrap_example": (
                    "call_tool('intent_bootstrap', "
                    "{'purpose': '<why>', 'deliverable': '<what>', "
                    "'acceptance': '<verify>'})"
                ),
                "install_example": "call_tool('agency_install', {})",
                "capabilities": caps,
                # Spec 068 — tier-0 discovery: browse the capability tier here,
                # then drill into one via search('<capability>') / get_schema,
                # instead of dumping every verb (progressive disclosure at the
                # discovery layer; CORE.md §Skills). `capabilities` (names) kept
                # for back-compat.
                "capability_tier": _capability_tier(engine.registry),
                "discipline_skills": discipline_skills,
            }
            body = {
                "state": state,
                "intents_count": intents_count,
                "last_intent": last_intent,
                "db_path": resolve_db_path(None),
                "next": next_steps,
            }
            envelope = ResponseEnvelope(prefix=prefix, body=body)
            merged = envelope.to_dict()
            # `_prefix_keys` declares the split so wrapping drivers can apply
            # `cache_control` cleanly. Listed AFTER the merge so the keyset is
            # an honest report of which keys ended up in the prefix half.
            merged["_prefix_keys"] = sorted(prefix.keys())
            return merged

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
