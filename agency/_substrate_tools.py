"""Substrate tools as a registered set — Spec 286 Phase 2 / A5.

The engine exposes a handful of WIRE TOOLS that are **not** capability verbs:
``lifecycle_gate`` · ``lifecycle_open`` · ``lifecycle_move`` ·
``lifecycle_close`` · ``memory_graph_provenance`` · ``hook_event`` ·
``intent_bootstrap`` · ``agency_install`` · ``agency_doctor`` ·
``agency_welcome``. They live outside the per-capability auto-wire because they
**mint or inspect** rather than SERVE an intent — they legitimately bypass the
SERVES intent-guard (``requires_intent=False``).

Before A5 these were ~6-7 nested ``@mcp.tool`` closures inside
``Engine.build_mcp`` (a ~500-line god-method dominated by the
``agency_doctor`` / ``agency_welcome`` bodies). This module models each as a
first-class :class:`SubstrateTool` object — independently readable and unit-
testable — and ``build_mcp`` becomes a registration loop over
:data:`SUBSTRATE_TOOLS`.

**Wire contract (SACRED).** Each tool keeps the EXACT tool name, signature
(param names + types + defaults), docstring (the wire description), and return
shape it had as a nested closure. FastMCP introspects the function FastMCP is
handed; each :class:`SubstrateTool` defines its impl with the real signature
directly (no ``*args``/``**kwargs`` masking) and binds ``engine`` via closure,
so FastMCP still reads identical names/types/defaults. The naming follows the
existing substrate convention (flat names, no ``capability_`` prefix).
"""
from __future__ import annotations

from fastmcp import Context


class SubstrateTool:
    """One engine-substrate wire tool.

    A :class:`SubstrateTool` is a callable-factory: :meth:`bind` takes the live
    engine and returns the function FastMCP will introspect + register. The
    subclass supplies that function via :meth:`make_impl`, defining it with the
    EXACT public signature (param names, types, defaults), name and docstring
    the tool must present on the wire — FastMCP reads those off the returned
    function, so this preserves the schema byte-for-byte.

    ``requires_intent=False`` on every substrate tool documents (and lets the
    registration loop assert) that these legitimately bypass the SERVES intent-
    guard that every ``capability_*_*`` verb is subject to: they mint/inspect,
    they do not SERVE an intent.
    """

    #: Wire tool name (must match ``make_impl``'s function ``__name__``).
    name: str = ""
    #: Substrate tools bypass the SERVES intent-guard by design.
    requires_intent: bool = False

    def make_impl(self, engine):
        """Return the function FastMCP introspects + registers.

        The returned callable MUST carry the exact name, signature, docstring
        and annotations the wire tool presents today; ``engine`` is captured by
        closure rather than appearing in the signature.
        """
        raise NotImplementedError

    def bind(self, engine):
        """Build the impl and assert its identity matches :attr:`name`."""
        impl = self.make_impl(engine)
        assert impl.__name__ == self.name, (
            f"{type(self).__name__}.make_impl produced {impl.__name__!r}, "
            f"expected wire name {self.name!r}")
        return impl


class LifecycleGate(SubstrateTool):
    name = "lifecycle_gate"

    def make_impl(self, engine):
        mem = engine.memory

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
            if not approved and engine.lifecycle.status(lifecycle_id) != "input-required":
                # Spec 339/344 — route the pause through the SOLE state writer so
                # the blocked transition emits a durable transition Event (the
                # guard keeps the old raw-update idempotency on a re-reject).
                engine.lifecycle.move(lifecycle_id, "input-required")
            return {"approved": approved, "gate_id": g}

        return lifecycle_gate


class LifecycleOpen(SubstrateTool):
    name = "lifecycle_open"

    def make_impl(self, engine):
        def lifecycle_open(intent_id: str, kind: str = "task", agent: str = "",
                           parameterization: str = "") -> dict:
            """Open a Lifecycle in ``submitted`` SERVING the given intent (Spec 339).

            The wire surface of the Lifecycle PILLAR's ``open`` — the canonical
            way to mint a unit of work's state machine (peer to
            ``intent_bootstrap`` for Intent). Takes ``intent_id`` explicitly (it
            SERVES, it does not mint the intent). ``kind`` (task | session | gate
            | dispatch …) and ``parameterization`` (the agent-as-Lifecycle seam,
            e.g. ``"remote-async"``) are optional.

            Inputs:
              - ``intent_id`` (str, required) — the intent this lifecycle serves
              - ``kind`` (str, optional) — default ``"task"``
              - ``agent`` (str, optional) — DISPATCHED_TO ``agent:<agent>``
              - ``parameterization`` (str, optional) — the 342 seam
            Returns: ``{lifecycle_id, state: "submitted"}``
            chain_next: ``lifecycle_move(lifecycle_id, to_state=…)`` to advance.
            """
            lid = engine.lifecycle.open(intent_id, kind=kind, agent=agent,
                                        parameterization=parameterization)
            return {"lifecycle_id": lid, "state": engine.lifecycle.status(lid)}

        return lifecycle_open


class LifecycleMove(SubstrateTool):
    name = "lifecycle_move"

    def make_impl(self, engine):
        def lifecycle_move(lifecycle_id: str, to_state: str,
                           evidence: str = "") -> dict:
            """Transition a Lifecycle to ``to_state`` — the SOLE state writer (Spec 339).

            Validates ``to_state`` against the closed A2A enum and refuses a
            no-op (raises ``ValueError`` the wire envelope surfaces as a typed
            error). The full transition-table guard (340) and transition events
            (344) layer on this one chokepoint.

            Inputs:
              - ``lifecycle_id`` (str, required)
              - ``to_state`` (str, required) — a valid LifecycleState value
              - ``evidence`` (str, optional)
            Returns: ``{lifecycle_id, state: <to_state>}``
            chain_next: ``lifecycle_close(lifecycle_id, outcome=…)`` to finish.
            """
            state = engine.lifecycle.move(lifecycle_id, to_state, evidence=evidence)
            return {"lifecycle_id": lifecycle_id, "state": state}

        return lifecycle_move


class LifecycleClose(SubstrateTool):
    name = "lifecycle_close"

    def make_impl(self, engine):
        def lifecycle_close(lifecycle_id: str, outcome: str = "completed",
                            evidence: str = "") -> dict:
            """Drive a Lifecycle to a terminal outcome through ``move`` (Spec 339).

            ``outcome`` must be a terminal/failure state (completed | failed |
            canceled). Not a parallel writer — it routes through ``move``.

            Inputs:
              - ``lifecycle_id`` (str, required)
              - ``outcome`` (str, optional) — default ``"completed"``
              - ``evidence`` (str, optional)
            Returns: ``{lifecycle_id, state: <outcome>}``
            """
            state = engine.lifecycle.close(lifecycle_id, outcome=outcome,
                                           evidence=evidence)
            return {"lifecycle_id": lifecycle_id, "state": state}

        return lifecycle_close


class MemoryGraphProvenance(SubstrateTool):
    name = "memory_graph_provenance"

    def make_impl(self, engine):
        mem = engine.memory

        def memory_graph_provenance(intent_id: str) -> dict:
            "Cross-concern provenance for an intent — one graph traversal."
            return mem.provenance(intent_id)

        return memory_graph_provenance


class AgencyReload(SubstrateTool):
    name = "agency_reload"

    def make_impl(self, engine):
        def agency_reload() -> dict:
            """Reload capabilities mid-session WITHOUT restarting the server
            (Spec 302).

            Substrate — NO intent required. Purges the ``agency.capabilities.*``
            module subtree and re-imports it fresh from disk (so EDITED code in a
            ``<cap>/_main.py`` or ``clusters/*.py`` submodule is picked up, not
            just brand-new caps), rebuilds the registry + effective ontology in
            place, and wires genuinely-new verbs onto the live MCP. Code-mode
            ``execute`` reaches the new surface immediately; a non-code-mode
            client must re-list tools to see brand-new verbs. Use after
            editing/adding a capability when
            ``agency_doctor.surface_freshness.fresh`` is False — no reinstall, no
            session restart.

            Inputs: (none).
            Returns: ``{reloaded, capability_count, capability_set_hash, added,
                    removed, rewired_tools, reimported}``.
            chain_next: ``agency_welcome`` to read the refreshed surface.
            """
            return engine.reload()

        return agency_reload


class HookEvent(SubstrateTool):
    name = "hook_event"

    def make_impl(self, engine):
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

        return hook_event


class IntentBootstrap(SubstrateTool):
    name = "intent_bootstrap"

    def make_impl(self, engine):
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

        return intent_bootstrap


class AgencyInstall(SubstrateTool):
    name = "agency_install"

    def make_impl(self, engine):
        def agency_install(target: str = "", agent: str = "") -> dict:
            """Scaffold .agency/ + a CLAUDE.md onboarding snippet in the target repo.

            Closes the missing MCP install path: previously only available
            via ``python -m agency.install --scaffold-db``. Idempotent —
            re-running on a populated tree is a no-op for any file already
            present. The CLAUDE.md snippet is bounded by explicit markers,
            so user content outside the markers is never touched.

            Spec 333 — with ``agent`` (one of cursor/windsurf/cline/kiro/copilot/
            agents/claude/all), install agency into that agent's native rules
            instead (the surface_card projected per host; fenced-block merge,
            per-adapter report).

            Inputs:
              - ``target`` (str, optional) — default = ``CLAUDE_PROJECT_DIR``
                env → cwd (mirrors the Spec 020 scaffold target).
              - ``agent`` (str, optional) — a Spec 333 agent target.
            Returns: ``{target, scaffolded, …}`` (default) or
                     ``{target, agents: {name: {ok, wrote|error}}}`` (--agent).
            chain_next: ``intent_bootstrap`` to mint the first Intent.
            """
            from .install import install_op
            if not agent:
                return install_op(target or None)
            from . import _install_adapters as ia
            root = ia.resolve_root(target)
            return {"target": root,
                    "agents": ia.install_agents(ia.resolve_names([agent]), root, engine)}

        return agency_install


class AgencyDoctor(SubstrateTool):
    name = "agency_doctor"

    def make_impl(self, engine):
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
                # Spec 390 — honest signal: `sampling`/`elicitation` are ADVERTISED
                # (the bound Context exposes the method + the flag is on), NOT a
                # guarantee. Actual client support is verified only at call time; a
                # request the client declines raises HostUnavailable and the walker
                # falls back to an `input-required` pause you resume by supplying the
                # value — the universal mid-chain interaction, client-independent.
                "note": ("advertised; verified at call time — declines fall back to "
                         "an input-required pause you resume with the value"),
            }
            import os
            import sys
            import importlib.metadata as _md
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
            if requested_emb and requested_emb != engine.embedder.name:
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
                        f"backend; resolved to {engine.embedder.name!r}. "
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
            # networkx (Spec 051) backs analyze.architecture's cycle enumeration
            # + degree metrics. It is a LIBRARY, not a CLI, so report by
            # distribution version rather than `which`.
            try:
                analyze_extras["networkx"] = _md.version("networkx")
            except _md.PackageNotFoundError:
                analyze_extras["networkx"] = "missing"

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

            # Spec 151 Slice 3 — codes-coverage health. Engine-side audit of
            # ToolResult.failure() typing (imports agency._codes_coverage, NOT
            # the dev-only scripts/ tree) so a drop in Codes coverage is visible
            # at runtime. Wrapped: a diagnostic must never crash the doctor.
            try:
                from ._codes_coverage import audit_tree as _codes_audit
                _cc = _codes_audit(os.path.dirname(os.path.abspath(__file__)))
                codes_coverage = {
                    "fraction": round(_cc.fraction, 3),
                    "covered": _cc.covered_sites,
                    "offenders": len(_cc.offenders),
                    "computed": _cc.expr_sites,
                    "orphan_codes": sorted(_cc.orphan_codes),
                }
            except Exception as _e:  # noqa: BLE001 — never crash the doctor
                codes_coverage = {"error": f"{type(_e).__name__}: {_e}"}

            # Spec 153 Slice 3 — schema-coverage health + priority ranking.
            # Engine-side audit (agency._schema_coverage); the engine already
            # holds the live ontology, so no second Engine boot. Uncovered
            # labels are ranked by live node-count so authors write the
            # highest-traffic schemas first. Wrapped: never crash the doctor.
            try:
                from pathlib import Path as _Path
                from ._schema_coverage import (audit_schemas, truly_inline_schemas,
                                               engine_loaded_schema_titles)
                _sroot = _Path(os.path.dirname(os.path.abspath(__file__)))
                _merged = dict(engine.ontology.schemas)
                _inline = truly_inline_schemas(_sroot, _merged)
                _loaded = engine_loaded_schema_titles(_merged)
                _sc = audit_schemas(_sroot, ontology_labels=set(engine.ontology.nodes),
                                    ontology_schemas=_inline,
                                    engine_loaded_titles=_loaded)
                _ranked = sorted(
                    ((lbl, len(list(engine.memory.find(lbl)))) for lbl in _sc.uncovered),
                    key=lambda t: (-t[1], t[0]))
                schema_coverage = {
                    "fraction": round(_sc.coverage_fraction, 3),
                    "covered": len(_sc.covered),
                    "uncovered": len(_sc.uncovered),
                    "total_labels": _sc.total_ontology_labels,
                    "non_node_schemas": len(_sc.non_node_schemas),
                    "dormant_schemas": sorted(_sc.dormant_schemas),
                    "priority_uncovered": [{"label": _l, "nodes": _n}
                                           for _l, _n in _ranked[:10]],
                }
            except Exception as _e2:  # noqa: BLE001 — never crash the doctor
                schema_coverage = {"error": f"{type(_e2).__name__}: {_e2}"}

            # Spec 334 Slice 4 — unified-config health. Report every registered
            # key's resolved value + source (secrets redacted to presence) and
            # fold any validation issue (bad enum value, unknown key) into
            # next_steps so the doctor's `ok` reflects config sanity. Wrapped:
            # a config read must never crash the doctor.
            try:
                from . import _config as _cfg
                config_block = {"values": _cfg.config_report(),
                                "issues": _cfg.config_validate()}
                next_steps.extend(config_block["issues"])
            except Exception as _e3:  # noqa: BLE001 — never crash the doctor
                config_block = {"error": f"{type(_e3).__name__}: {_e3}"}

            # Spec 332 Slice 5 — surface the frugal discipline status first-class
            # (level + source + whether the M2 per-verb stamp is firing), so "is
            # frugal on?" is one glance. Derived from the config block +
            # frugal_prefix — no duplicated logic. Wrapped: never crash the doctor.
            try:
                from . import _frugal as _fr
                _lvl = (config_block.get("values") or {}).get("frugal.level", {})
                frugal_block = {"level": _lvl.get("value"),
                                "source": _lvl.get("source"),
                                "stamp_active": bool(_fr.frugal_prefix())}
            except Exception as _e4:  # noqa: BLE001 — never crash the doctor
                frugal_block = {"error": f"{type(_e4).__name__}: {_e4}"}

            # Spec 333 Slice 5 — which agents agency is installed into (instruction
            # files carrying the agency fenced block in the project dir).
            try:
                from ._install_adapters import installed_agents as _ia
                installed = _ia(project_dir or os.getcwd())
            except Exception:  # noqa: BLE001 — never crash the doctor
                installed = []

            # Spec 171 Slice 2 — node-id-guard coverage: ready iff the live registry
            # sweep is clean (zero unguarded *_id params AND every verb signature
            # resolved; else GUARD_LINT_UNRESOLVED). The Spec 170 consumer signal +
            # the WARN→error lint-promotion gate.
            try:
                from ._node_id_sweep import sweep as _nid_sweep
                _nid = _nid_sweep(engine.registry)
                node_id_guard_coverage = {
                    "ready": _nid["ready"],
                    "violations": _nid["violation_count"],
                    "unresolved": len(_nid["unresolved"]),
                }
            except Exception:  # noqa: BLE001 — never crash the doctor
                node_id_guard_coverage = {"ready": None, "violations": 0, "unresolved": 0}

            # Spec 173 Slice 2 — reflection-link coverage: ready iff every live
            # Reflection carries BOTH SERVES + OBSERVED_DURING (the WARN→error
            # promotion gate + the Spec 150 classifier's attribution guarantee).
            try:
                from ._reflection_link_sweep import sweep as _refl_sweep
                _refl = _refl_sweep(engine.memory)
                reflection_link_coverage = {"ready": _refl["ready"],
                                            "unlinked": _refl["unlinked"]}
            except Exception:  # noqa: BLE001 — never crash the doctor
                reflection_link_coverage = {"ready": None, "unlinked": 0}

            # Spec 175 Slice 2 — install-surface coverage: the whole install
            # surface derived as ONE typed object from live sources (registry
            # capability rows, pyproject extras, curated slash-command family).
            # `ready` iff every documented row/extra/command derives (so a new
            # capability/extra/walkable skill auto-appears, a removed one drops).
            try:
                from ._install_surface import derive_install_surface as _dis
                _surf = _dis(engine)
                install_surface_coverage = {
                    "rows": len(_surf.readme_capability_rows),
                    "extras": len(_surf.userconfig_extras),
                    "commands": len(_surf.slash_commands),
                    "ready": (bool(_surf.readme_capability_rows)
                              and bool(_surf.userconfig_extras)
                              and bool(_surf.slash_commands)),
                }
            except Exception:  # noqa: BLE001 — never crash the doctor
                install_surface_coverage = {"ready": None, "rows": 0,
                                            "extras": 0, "commands": 0}

            # Spec 176 Slice 2 — sessionstart-capture readiness: does the session
            # already SERVE an Intent? `ready` iff an open Intent exists (the
            # idempotency read — a session is never orphan). The non-blocking
            # auto_ad_hoc fallback guarantees this once SessionStart has run.
            try:
                from ._intent_capture import open_intent_id as _open_iid
                _oid = _open_iid(engine.memory)
                sessionstart_capture = {"ready": bool(_oid),
                                        "intent_id": _oid,
                                        "open_intents": len(engine.memory.find("Intent"))}
            except Exception:  # noqa: BLE001 — never crash the doctor
                sessionstart_capture = {"ready": None, "intent_id": "",
                                        "open_intents": 0}

            # Spec 169 Slice 2/4 — CI coverage-gate (verb-test-coverage dimension):
            # one GateResult per capability from the live test-gap report; `ready`
            # iff every capability has ≥ 1 test. Lets the operator see a regression
            # (a new cap without a test) BEFORE it reaches CI.
            try:
                from ._coverage_gate import gate_summary as _gate_summary
                coverage_gate = _gate_summary(engine)
            except Exception:  # noqa: BLE001 — never crash the doctor
                coverage_gate = {"ready": None, "capabilities": 0,
                                 "passing": 0, "failing": []}

            # Spec 172 Slice 2 — analyzer-axis registry: the live analyzer
            # wrappers' AXIS_PREFIXES composed into the typed AxisRegistry;
            # `ready` iff zero prefix collisions AND no malformed declarations
            # (longest-prefix-first, order-independent). A new analyzer's
            # prefixes auto-appear; a colliding one trips the guard.
            try:
                from ._axis_registry_sweep import axis_registry_summary
                _axis = axis_registry_summary()
                axis_registry_coverage = {"ready": _axis["ready"],
                                          "entries": _axis.get("entries", 0),
                                          "collisions": _axis.get("collision_count", 0)}
            except Exception:  # noqa: BLE001 — never crash the doctor
                axis_registry_coverage = {"ready": None, "entries": 0,
                                          "collisions": 0}

            # Spec 163 Slice 2 — SkillDoc derive-status: every live capability's
            # SkillDoc rendered from its live `skill_doc` must be byte-equal to
            # the one derived from its module docstring (the derivability
            # invariant). `ready` iff zero drift + zero missing.
            try:
                from ._skilldoc_derive import skilldoc_derive_summary
                _sd = skilldoc_derive_summary(engine.registry)
                skilldoc_derive_coverage = {"ready": _sd["ready"],
                                            "skills": _sd["skills"],
                                            "byte_equal": _sd["byte_equal"],
                                            "drift": len(_sd["drift"]),
                                            "missing": len(_sd["missing"])}
            except Exception:  # noqa: BLE001 — never crash the doctor
                skilldoc_derive_coverage = {"ready": None, "skills": 0,
                                            "byte_equal": 0, "drift": 0,
                                            "missing": 0}

            # Spec 167 Slice 2 — architecture metrics: the import graph projected
            # into typed ArchMetrics (cycles / fan-out / fan-in / god-module).
            # `ready` iff the fan-out/fan-in edge-count identity holds.
            try:
                from ._arch_metrics import arch_metrics_summary
                architecture_metrics = arch_metrics_summary()
            except Exception:  # noqa: BLE001 — never crash the doctor
                architecture_metrics = {"ready": None, "metrics": 0,
                                        "cycles": 0, "god_modules": 0}

            # Spec 177 Slice 2 — plugin-reference continuous-audit: the committed
            # plugin files (plugin.json / marketplace.json / commands/*.md) swept
            # against the open reference-invariant set. `ready` iff zero
            # error-severity findings (the derived install surface passes).
            try:
                from ._plugin_ref_audit import ref_audit_summary
                plugin_ref_audit = ref_audit_summary(project_dir or os.getcwd())
            except Exception:  # noqa: BLE001 — never crash the doctor
                plugin_ref_audit = {"ready": None, "findings": 0, "errors": 0,
                                    "warns": 0, "audited_invariants": []}

            # Spec 201 item 8 — the rich token-backend report (available tiers,
            # preferred, last-used, band-check). Best-effort.
            try:
                from ._tokens import token_backend_report
                _token_backend_report_val = token_backend_report(
                    engine.drivers.get("token_counter"))
            except Exception:  # noqa: BLE001 — never crash the doctor
                _token_backend_report_val = {"available": ["proxy"],
                                             "preferred": "proxy",
                                             "last_used": "proxy",
                                             "band_check_ok": None}

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
                "embedder": engine.drivers.get("embedder").name,
                # Spec 082 / 286-A2 — the live token-count backend (count_tokens /
                # tiktoken / proxy), so a silent fallback to the proxy is visible.
                "token_backend": _token_backend_report_val,
                # Spec 092 G3 / 286-A2 — the live LLM-decider backend (openrouter /
                # anthropic / none), never the key. Custom-injected clients may
                # omit backend() — the registry returns "custom".
                "llm_backend": engine.drivers.backend("llm"),
                # Spec 147 / 286-A2 — the canonical AnthropicDriver readiness
                # (api-key-present / model-id-resolved / managed-agents-capable),
                # never the key. Custom-injected drivers may omit readiness().
                "anthropic_driver": engine.drivers.readiness("anthropic"),
                # Spec 050 — which optional [analyze] tools are active.
                "analyze_extras": analyze_extras,
                # Spec 054 — drift indicators. v1 ships the
                # capabilities_without_tests check (cheap; just file
                # lookup); install-regen-drift defers to the
                # scripts/check-drift script (would require a heavy
                # subprocess otherwise).
                "drift": engine._drift_signals(),
                # Spec 151 Slice 3 — live Codes-coverage fraction +
                # offender/orphan counts (engine-side audit above).
                "codes_coverage": codes_coverage,
                # Spec 153 Slice 3 — live schema-coverage fraction + priority
                # ranking of uncovered labels by graph node-count.
                "schema_coverage": schema_coverage,
                # Spec 171 Slice 2 — node-id-guard coverage (ready iff sweep clean).
                "node_id_guard_coverage": node_id_guard_coverage,
                # Spec 173 Slice 2 — reflection-link coverage (ready iff every
                # Reflection has both SERVES + OBSERVED_DURING).
                "reflection_link_coverage": reflection_link_coverage,
                # Spec 175 Slice 2 — install-surface coverage (whole install
                # surface derived as one typed object; ready iff all derive).
                "install_surface_coverage": install_surface_coverage,
                # Spec 176 Slice 2 — sessionstart-capture readiness (ready iff
                # the session already SERVES an Intent; auto_ad_hoc fallback).
                "sessionstart_capture": sessionstart_capture,
                # Spec 169 Slice 2/4 — CI coverage-gate (verb-test-coverage;
                # ready iff every capability has a test).
                "coverage_gate": coverage_gate,
                # Spec 172 Slice 2 — analyzer-axis registry (ready iff zero
                # prefix collisions + no malformed AXIS_PREFIXES).
                "axis_registry_coverage": axis_registry_coverage,
                # Spec 163 Slice 2 — SkillDoc derive-status (ready iff every
                # SkillDoc is byte-equal to its docstring-derived render).
                "skilldoc_derive_coverage": skilldoc_derive_coverage,
                # Spec 167 Slice 2 — architecture metrics (ready iff the
                # fan-out/fan-in edge identity holds over the import graph).
                "architecture_metrics": architecture_metrics,
                # Spec 177 Slice 2 — plugin-reference audit (ready iff zero
                # error-severity findings over the committed plugin files).
                "plugin_ref_audit": plugin_ref_audit,
                # Spec 334 Slice 4 — unified-config: resolved values + sources
                # (secrets redacted) + validation issues (also in next_steps).
                "config": config_block,
                # Spec 332 Slice 5 — the frugal discipline status at a glance.
                "frugal": frugal_block,
                # Spec 333 Slice 5 — agents agency is installed into.
                "installed_agents": installed,
                # Spec 302 Slice 3 — time-to-first-successful-call: a fresh user
                # can bootstrap an intent + invoke a verb end-to-end (proven on a
                # throwaway in-memory engine, so the live graph is untouched).
                "onboarding": engine._onboarding_probe(),
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

        return agency_doctor


class AgencyWelcome(SubstrateTool):
    name = "agency_welcome"

    def make_impl(self, engine):
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
            # `_capability_tier` lives on the engine module; lazy-import here so
            # this module can be imported by engine.py without a cycle.
            from .engine import _capability_tier
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
                    "search('<keyword>') — discover a capability_*_* verb",
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
            # Spec 375 — the concept pillars (intent · lifecycle · memory): the
            # non-capability spine every session rides. Surfaced at onboarding so
            # a fresh agent learns the concepts, not just the verbs. Static source
            # ⇒ stays in the cache-stable prefix below.
            from ._pillars import load_pillars
            pillar_list = [{"name": p["name"],
                            "description": (p.get("description") or "").strip()}
                           for p in load_pillars()]
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
                # Spec 375 — the four concepts' non-capability pillars.
                "pillars": pillar_list,
            }
            # Spec 332 M2 — the frugal discipline rides the onboarding payload's
            # cache-stable prefix too (byte-stable at a fixed level; off omits).
            try:
                from . import _frugal
                prefix.update(_frugal.frugal_prefix())
            except Exception:
                pass
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

        return agency_welcome


# The registered set — `Engine.build_mcp` iterates this and `@mcp.tool`-
# decorates each tool's bound impl. Order is presentation-only (FastMCP keys by
# name); kept matching the historical inline order for diff-stability.
SUBSTRATE_TOOLS: tuple[SubstrateTool, ...] = (
    LifecycleGate(),
    LifecycleOpen(),
    LifecycleMove(),
    LifecycleClose(),
    MemoryGraphProvenance(),
    HookEvent(),
    IntentBootstrap(),
    AgencyInstall(),
    AgencyDoctor(),
    AgencyWelcome(),
    AgencyReload(),
)
