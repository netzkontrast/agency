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


class Engine:
    def __init__(self, path: str, jules_client=None, vcs_backend=None,
                 embedder=None, web_search=None, runner=None,
                 extra_capabilities=None, surface: str | None = None):
        self.surface = resolve_surface(surface)
        # Spec 073 — the toolchain runner boundary (stubbable; default shells out).
        from ._runner import SubprocessRunner
        self.runner = runner or SubprocessRunner()
        self.jules_client = jules_client or JulesClient()       # boundary: the real Jules backend by default
        self.vcs_backend = vcs_backend or GitClient()           # boundary: real git/gh for workspace + branch
        # Spec 045 — semantic-recall backend. Default is TF-IDF (zero-dep);
        # AGENCY_EMBEDDER=bge-small-en + [recall] extra activates BGE.
        # Tests inject a stub. `agency_doctor` reports `embedder.name`.
        if embedder is None:
            from .capabilities._embed import resolve_embedder
            embedder = resolve_embedder()
        self.embedder = embedder
        # Spec 044 + Spec 052 — web-search boundary. v1 default is the
        # DuckDuckGo zero-config client (resolve_web_search()); env
        # AGENCY_WEB_BACKEND can pick alternatives. Tests stub via
        # Engine(web_search=...).
        if web_search is None:
            from .capabilities.research._web import resolve_web_search
            web_search = resolve_web_search()
        self.web_search = web_search
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
        # Spec 031 §A — bootstrap-time skill_doc validation.
        # Any capability that declares verbs MUST declare a skill_doc; otherwise
        # the per-capability skill emit pipeline (Spec 031 Phase 2) cannot render
        # a SKILL.md for it. Fail loud at engine startup, not at install time.
        #
        # Phase-1 transition: until Phase 4 migration lands skill_doc on every
        # shipped capability, validation is opt-in via AGENCY_SKILL_DOC_REQUIRED
        # env. This shim is REMOVED at the Phase 4 checkpoint (after Task 4.5)
        # once migration is complete. Spec 032 unifies this with the broader
        # AGENCY_BOOTSTRAP_LINT={strict,warn,off} env var (panel F-10).
        import os as _os
        if _os.environ.get("AGENCY_SKILL_DOC_REQUIRED", "").lower() == "true":
            for _cap_name in self.registry.names():
                _cap = self.registry.get(_cap_name)
                if _cap.verbs and getattr(_cap, "skill_doc", None) is None:
                    raise ValueError(
                        f"capability {_cap_name!r} declares verbs but no skill_doc — "
                        f"add `skill_doc = SkillDoc(description='Use when …', "
                        f"overview='…', triggers=[…], canonical_example='…')` to "
                        f"the capability class per Spec 031 §A. See "
                        f"agency/capabilities/reflect/_main.py for the reference shape."
                    )
        # the boundary object surfaced on ctx.client; `memory`/`intent_id` are
        # injected per-call by the Registry itself, and the registry is on ctx.
        self.registry.injectors = {"client": lambda: self.jules_client,
                                   "vcs": lambda: self.vcs_backend,
                                   "embedder": lambda: self.embedder,
                                   "runner": lambda: self.runner}
        self.memory = Memory(path, ont=self.ontology)           # enforce the EFFECTIVE ontology
        self.intent = Intent(self.memory)
        self.lifecycle = Lifecycle(self.memory)
        # Spec 021 — the single engine Monitor channel. Capabilities fan events
        # in via ctx.emit_monitor(...); one tail -F on this log surfaces them.
        from ._monitor import MonitorEmitter, resolve_monitor_log_path
        self.monitor = MonitorEmitter(resolve_monitor_log_path(db_path=path))

    def _wire(self, mcp: FastMCP, cap_name: str, verb: str, spec: dict) -> None:
        """Auto-wire ONE MCP tool for a capability verb from its fn signature.
        Injected params (`inject`) are resolved by the Registry, so they are not
        exposed in the tool's schema."""
        reg, mem = self.registry, self.memory
        fn, inject = spec["fn"], list(spec.get("inject", []))
        user_params = [p for n, p in inspect.signature(fn).parameters.items() if n not in inject]

        def impl(**kwargs):
            intent_id = kwargs.pop("intent_id")
            agent_id = kwargs.pop("agent_id", "") or None
            result, _ = reg.invoke(mem, intent_id, cap_name, verb, agent_id=agent_id, **kwargs)
            # Spec 001 + Spec 019 — wire-shape contract.
            # Internal verbs return either a bare rich dict (e.g.
            # ``{status, session, url}``) OR ``{"result": <delta>}`` for
            # ok-path detection at the engine boundary. The wire shape
            # crossing to the code-mode caller strips that envelope IFF
            # the inner value is itself a dict (the lean code-mode
            # contract per CORE.md "search · get_schema · execute" +
            # GOALS.md goal #5). Scalar inner values get re-wrapped
            # because MCP tool returns must be JSON objects.
            # `plugin.lint_capability` enforces docstrings describe the
            # wire shape, not the internal envelope.
            out = result["result"] if isinstance(result, dict) and "result" in result else result
            return out if isinstance(out, dict) else {"result": out}

        params = []
        for p in user_params:
            ann = p.annotation if p.annotation is not inspect.Parameter.empty else str
            default = p.default if p.default is not inspect.Parameter.empty else inspect.Parameter.empty
            params.append(inspect.Parameter(p.name, inspect.Parameter.KEYWORD_ONLY, annotation=ann, default=default))
        params.append(inspect.Parameter("intent_id", inspect.Parameter.KEYWORD_ONLY, annotation=str))
        params.append(inspect.Parameter("agent_id", inspect.Parameter.KEYWORD_ONLY, annotation=str, default=""))

        impl.__signature__ = inspect.Signature(params)
        impl.__name__ = f"capability_{cap_name}_{verb}"
        # Spec 023 Phase 3: tighten the FastMCP tool description to the BRIEF
        # slice (first-sentence) instead of the full docstring. Cuts ~58% of
        # catalog tokens; full doc remains reachable via get_schema.
        raw = (fn.__doc__ or "").strip()
        brief = parse_slices(raw)["brief"]
        impl.__doc__ = brief or raw or f"{cap_name}.{verb} ({spec['role']})"
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
        def agency_doctor() -> dict:
            """Health-check substrate tool — diagnose silent-failure modes.

            Reports python version, dep imports, DB reachability, and the
            two env vars users hit problems with (JULES_API_KEY,
            CLAUDE_PROJECT_DIR). The KEY VALUE is NEVER in the report —
            only its presence/absence. ``next_steps`` carries
            copy-pasteable fixes for any issue found.

            Covers F2 (Jules-key inheritance) + F5 (system python3 vs
            plugin venv) from the KP Fehlerbericht.

            Inputs: none.
            Returns: ``{ok, python_version, deps, db, env, next_steps}``.
            chain_next: ``next_steps`` are literal calls/commands.
            """
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

            return {
                "ok": len(next_steps) == 0,
                "python_version": ".".join(str(v) for v in sys.version_info[:3]),
                "deps": deps,
                "db": {"path": db_path, "exists": db_exists, "writable": db_writable},
                "env": {
                    "JULES_API_KEY": jules_status,
                    "CLAUDE_PROJECT_DIR": project_dir,
                },
                # Spec 045 — the live semantic-recall backend (so users
                # can confirm whether AGENCY_EMBEDDER took effect, or
                # whether the BGE fallback to TF-IDF happened silently).
                "embedder": self.embedder.name,
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
                "next_steps": next_steps,
            }

        @mcp.tool
        def agency_welcome() -> dict:
            """One-shot onboarding payload — the canonical first call.

            Replaces the "read three files to know how to start" tax on
            fresh MCP clients. Returns the bootstrap example, the install
            example, the live capability map, and the resolved graph DB
            path. No ``intent_id`` required (pure introspection — no graph
            writes regardless of caller state).

            Inputs: none.
            Returns: ``{bootstrap_example, install_example, capabilities,
                       capability_tier, db_path, next: [step1, step2, step3]}``.
            ``capability_tier`` (Spec 068) is the tier-0 discovery payload — one
            line per capability (``{name, gist, verbs}``); browse it, then drill
            into ONE capability via ``search('<capability>')`` / ``get_schema``
            instead of dumping every verb (progressive disclosure at the
            discovery layer — ~83% cheaper than the flat verb catalog).
            ``capabilities`` (names only) is kept for back-compat.
            chain_next: call ``agency_install`` then ``intent_bootstrap``, then
            browse ``capability_tier`` and ``search('<capability>')`` to drill in.
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
                ]
            else:
                next_steps = [
                    f"search('<keyword>') — discover a capability_*_* verb",
                    f"memory_graph_provenance('{last_intent}') — see what served the last intent",
                ]
            return {
                "state": state,
                "intents_count": intents_count,
                "last_intent": last_intent,
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
                "db_path": resolve_db_path(None),
                "next": next_steps,
            }

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
