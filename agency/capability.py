"""Capability — the craft (the open concept). Verbs are capability-defined and
role-tagged: act (craft write) · transform (stateless compute) · effect
(external side-effect). Invoking a capability records an Invocation in Memory,
edged SERVES->intent (and BY->agent / PRODUCES->artefact when relevant).

Two authoring forms (both valid — the Capability set is open):
- functional: a `Capability(name, home, verbs={verb: {"role", "fn", "inject"}})`;
- a class: subclass `CapabilityBase`, set `name`/`home`/`ontology`, decorate
  verb-methods with `@verb(role=...)`, and use `self.ctx` (a `CapabilityContext`).
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from pathlib import Path
from string import Template as _Template
from typing import Any, Callable, ClassVar, Optional, Protocol, runtime_checkable

from .memory import Memory
from .ontology import OntologyExtension
from ._verb import Verb


@dataclass
class Capability:
    name: str
    home: str                       # which concept it primarily is
    # Spec 286-A4 — verbs are typed `Verb` value objects (verb name -> Verb).
    # `Verb` is a drop-in for the former untyped dict via its Mapping bridge,
    # so subscript readers (`spec["fn"]`) still work during the transition.
    verbs: dict[str, Verb]
    # the capability's OWN ontology fragment (node types, edges, enums, skills,
    # template-schemas) — merged onto the core by the engine. Empty = core only.
    ontology: OntologyExtension = field(default_factory=OntologyExtension)
    # Spec 060 — file-based template/schema declarations. The engine's
    # bootstrap (engine.py) reads these to call `load_capability_folders`
    # and merges the discovered entries into `ontology`. `None` means
    # the capability ships no file-based extension (the default —
    # back-compat with caps that pre-date Spec 032/060).
    render_templates: Optional["RenderTemplates"] = None
    artefact_schemas: Optional["ArtefactSchemas"] = None
    # PR review round 8 (r_skilldoc_through_as_capability) — class-form
    # caps declare `skill_doc` + `walker_skills` as class attributes;
    # `as_capability` must carry them onto the returned dataclass so
    # `install.generate()` finds them. None = no skill doc declared.
    skill_doc: Optional["SkillDoc"] = None
    walker_skills: Optional["WalkerSkills"] = None
    # Spec 349b §2 — declarative event-bus subscriptions (DATA on the cap). The
    # engine's bootstrap loop reads these + `module` to resolve each handler by
    # name and register it on the pillar event bus (`agency/_events.py`).
    subscriptions: tuple = ()
    module: str = ""
    # Spec 342 — a `home="lifecycle"` member may declare the parameterization
    # (a key into the machine registry, machines.json) its dispatched children
    # run under: `jules` → "remote-async", a review-gated `subagent` → "reviewed".
    # The dispatch path (delegate.fan_out) reads this and opens the child on that
    # machine, so verify/in-review is enforced. "" = the default a2a machine.
    parameterization: str = ""

    def role(self, verb: str) -> str:
        return self.verbs[verb].role


class DriverMissing(LookupError):
    """Spec 002 — raised by ``DriverRegistry.get`` when no driver is registered
    under a name. The wrapping capability converts it to a typed
    ``ToolResult.failure(NOT_FOUND)`` (D-3); it is a ``LookupError`` so existing
    ``except KeyError``/``except LookupError`` paths still catch it."""


@runtime_checkable
class Boundary(Protocol):
    """Spec 002 — marker for ANY injected external dependency (an I/O seam isolated
    for deterministic testing: Jules REST, git/gh, the embedder, a shell runner, the
    token counter, the Skills API). No members — a memberless ``runtime_checkable``
    Protocol is a no-op ``isinstance`` (PEP 544), so this imposes NO behaviour change
    on the concrete clients."""


@runtime_checkable
class Driver(Boundary, Protocol):
    """Spec 002 — a ``Boundary`` reached BY NAME through ``ctx.get_driver(name)``.
    Option B: there is NO uniform ``dispatch(op, **kw)``. Each concrete driver keeps
    its own typed, named methods (``JulesClient.create``, ``GitClient.branch``); the
    uniform contract every driver shares is the RETURN TYPE (``ToolResult``, Spec 001),
    produced by the *capability* that wraps the boundary — not a uniform method name."""


class DriverRegistry:
    """Spec 002 / Spec 286-A2 — the engine's ONE boundary home. ``Registry.injectors``
    generalized to a named table: a domain tool-cluster plugs in by registering a
    driver under a name and needs NO new ``Engine`` kwarg and NO new ``injectors``
    key. Named lookup + a uniform result type (via the wrapping verb) is the value.

    Spec 286-A2 — the registry now also owns the *lazy default* for each boundary.
    Register a zero-arg factory via :meth:`register_factory`; the boundary is not
    constructed until first :meth:`get`, and an explicitly-registered driver (test
    injection) always wins over its factory. This collapses the engine's former
    triplication (bespoke ``self.<boundary>`` attrs + a ``DriverRegistry({...})``
    + a parallel ``injectors`` lambda dict) into this single table.
    """

    def __init__(self, drivers: Optional[dict[str, Any]] = None):
        self._drivers: dict[str, Any] = dict(drivers or {})
        # lazy zero-arg factories; consulted by get() only when no concrete
        # driver is already registered under the name. Materialized on first
        # use and then cached in _drivers (so a factory runs at most once).
        self._factories: dict[str, Callable[[], Any]] = {}

    def register(self, name: str, driver: Any) -> None:
        """Register (or replace) a concrete driver under ``name``. An explicit
        driver always shadows any factory for the same name."""
        self._drivers[name] = driver

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """Spec 286-A2 — register a lazy zero-arg factory for ``name``. The driver
        is constructed on first :meth:`get` (and cached). A concrete driver already
        registered under ``name`` (e.g. a test-injected stub) wins — the factory is
        never called."""
        self._factories[name] = factory

    def get(self, name: str) -> Any:
        if name in self._drivers:
            return self._drivers[name]
        factory = self._factories.get(name)
        if factory is not None:
            driver = factory()
            self._drivers[name] = driver        # cache: factory runs at most once
            return driver
        raise DriverMissing(
            f"no driver registered under {name!r}; have {sorted(self.names())}"
        )

    def has(self, name: str) -> bool:
        return name in self._drivers or name in self._factories

    def names(self) -> list[str]:
        """All known boundary names — concrete + lazily-registered factories."""
        return sorted(set(self._drivers) | set(self._factories))

    # Spec 286-A2 — uniform readiness probes so `agency_doctor` reads boundary
    # health from ONE place (the registry) instead of N bespoke getattr lambdas.
    def backend(self, name: str, default: Any = "custom") -> Any:
        """The boundary's backend identity. Reads a ``.backend`` attribute (str)
        or callable, falling back to ``default`` for custom-injected drivers that
        omit it. Materializes the lazy default on first probe."""
        drv = self.get(name)
        attr = getattr(drv, "backend", None)
        if attr is None:
            return default
        return attr() if callable(attr) else attr

    def readiness(self, name: str, default: Optional[dict] = None) -> dict:
        """The boundary's readiness dict (e.g. AnthropicDriver's api-key-present /
        model-id-resolved). Falls back to ``{"backend": "custom"}`` for custom-
        injected drivers that omit ``readiness()``."""
        drv = self.get(name)
        fn = getattr(drv, "readiness", None)
        if fn is None:
            return dict(default or {"backend": "custom"})
        return fn()


@dataclass
class CapabilityContext:
    """The one typed handle a verb receives (via `inject: ["ctx"]`, or always for a
    CapabilityBase method). A DELEGATOR over the engine's services — never a new
    public surface. Code-mode stays the only contract; this is internal."""
    memory: Memory
    ontology: Any                       # ontology.Ontology (annotation only; avoids an import cycle)
    registry: "Registry"
    intent_id: str
    agent_id: Optional[str] = None
    client: Any = None                  # boundary objects (e.g. the Jules backend)
    depth: int = 0
    engine: Any = None                  # the owning Engine; for verbs that need engine-attached state
                                        # (e.g. the long-lived watcher singleton at engine._jules_watcher)
    drivers: Any = None                 # Spec 002 — the engine's DriverRegistry (None in bare unit tests)
    MAX_DEPTH: int = 16

    def get_driver(self, name: str) -> Any:
        """Spec 002 — fetch a named external Driver from the engine's DriverRegistry.
        Raises ``DriverMissing`` when no DriverRegistry is attached or the name is
        unregistered (the wrapping capability converts it to a typed failure)."""
        if self.drivers is None:
            raise DriverMissing(f"no DriverRegistry on this context (name={name!r})")
        return self.drivers.get(name)

    def production_enabled(self, domain: str) -> bool:
        """True iff the production MCP runtime flipped ``domain``'s auto-wiring
        flag on the engine (Spec 286 A8 — ONE typed accessor instead of each
        cluster base reaching into ``ctx.engine._<domain>_production``).

        ``agency/__main__.py`` sets ``engine._<domain>_production = True`` for the
        live server; a bare ``Engine`` built by a unit test has no flag, so
        driver-backed verbs keep their typed ``DEPENDENCY_MISSING`` contract
        (the enforcement blast-radius stays bounded — CLAUDE.md heuristic)."""
        return getattr(self.engine, f"_{domain}_production", False) is True

    @property
    def host(self) -> Any:
        """Spec 285 — the request-scoped `HostBridge` to the host LLM (sampling)
        and the user (elicitation). Reads the live FastMCP Context bound by
        `engine._wire` for this call, plus the engine's `sampling_enabled` flag.
        With no bound Context (CLI / bare tests), the bridge's `can_*()` report
        False and callers fall back (Spec 279 envelope / input-required pause)."""
        from ._host_bridge import HostBridge, current_host_context
        return HostBridge(current_host_context(),
                          sampling_enabled=getattr(self.engine, "sampling_enabled", None))

    @property
    def toolcalls(self):
        """Spec 336 S2 — the engine's ephemeral tool-call store (the `toolcalls`
        capability reads it). ``None`` on a bare context with no engine attached."""
        return self.engine.toolcalls if self.engine is not None else None

    @property
    def lifecycle(self):
        """Spec 339 — the Lifecycle PILLAR substrate (``engine.lifecycle``), the
        canonical ``open · move · close`` write frame. A member capability mints/
        advances a Lifecycle through ``ctx.lifecycle.open(ctx.intent_id, …)`` /
        ``.move(lid, to_state)`` / ``.close(lid, outcome=…)`` instead of hand-
        rolling ``record_and_serve("Lifecycle", …)`` + raw ``state`` writes — so
        ``move`` stays the SOLE state writer. ``None`` on a bare context with no
        engine attached (bare unit tests fall back, like ``toolcalls``)."""
        return self.engine.lifecycle if self.engine is not None else None

    def spawn(self, cap: str, verb: str, **args) -> tuple:
        """Invoke a sibling capability and return BOTH its result and the recorded
        Invocation id (so a caller can edge to it). Depth-guarded against cycles."""
        if self.depth >= self.MAX_DEPTH:
            raise ValueError(f"capability call depth exceeded ({self.MAX_DEPTH}) — possible cycle")
        return self.registry.invoke(self.memory, self.intent_id, cap, verb,
                                    agent_id=self.agent_id, _depth=self.depth + 1, **args)

    def call(self, cap: str, verb: str, **args) -> Any:
        """Delegate to a sibling capability — records an Invocation that SERVES the
        intent (provenance by construction). Guarded against runaway recursion."""
        return self.spawn(cap, verb, **args)[0]

    def emit_monitor(self, source: str, kind: str, message: str,
                     intent_id: Optional[str] = None) -> None:
        """Spec 021 — fan one event onto the engine's single Monitor channel.

        Sugar over ``self.engine.monitor.emit(MonitorEvent(...))`` so verbs
        don't import the dataclass. Auto-fills ``intent_id`` from the serving
        intent and ``ts`` (in the emitter). Silent no-op when no engine/monitor
        is attached (e.g. bare unit tests) — emitting is best-effort
        notification, never load-bearing.

        Inputs: source (capability name), kind (event kind — see
                `_monitor.CANONICAL_KINDS`; open string), message (one-line
                summary; truncated to the atomic-append budget by the emitter),
                intent_id (override; defaults to the ctx's serving intent).
        Returns: None.
        chain_next: the agent receives the line via the `agency-engine` monitor.
        """
        engine = self.engine
        monitor = getattr(engine, "monitor", None) if engine is not None else None
        if monitor is None:
            return
        from ._monitor import MonitorEvent
        try:
            monitor.emit(MonitorEvent(
                source=source, kind=kind, message=message,
                intent_id=intent_id or self.intent_id or "",
            ))
        except OSError:
            # Best-effort: a full disk / unwritable AGENCY_MONITOR_LOG / rotation
            # permission error must NEVER fail a load-bearing verb (e.g.
            # jules.dispatch after the remote session is already created, where a
            # raised error could prompt a duplicate retry). Drop the notification.
            pass

    def render(self, template: str, **vars: Any) -> str:
        # Spec 060 round 9 — `ontology.templates` carries BOTH bare strings
        # (dict-form declarations) and `string.Template` instances (file-
        # form loader output). `_Template(string)` works for the string
        # case but `_Template(Template)` TypeErrors. Detect both shapes.
        tpl = self.ontology.templates[template]
        if isinstance(tpl, _Template):
            return tpl.substitute(**vars)
        return _Template(tpl).substitute(**vars)

    def schema(self, name: str) -> list:
        return list(self.ontology.schemas.get(name, []))

    def validate(self, label: str, props: dict) -> list:
        return self.ontology.violations(label, props)

    def record(self, label: str, props: dict, node_id: Optional[str] = None) -> str:
        return self.memory.record(label, props, node_id)

    def record_and_serve(self, label: str, props: dict, *,
                         parent: str = "", edge: str = "") -> str:
        """Spec 286 — record a node and link it ``SERVES`` the serving intent
        in one call, optionally edging it to a ``parent`` first.

        Collapses the ubiquitous ``act``-verb boilerplate::

            nid = self.ctx.record(label, {...})
            self.ctx.link(nid, self.ctx.intent_id, "SERVES")

        into ``nid = self.ctx.record_and_serve(label, {...})``. When
        ``parent`` and ``edge`` are given, the node is first linked to the
        parent (``link(nid, parent, edge)``) — matching the
        record→parent-edge→SERVES shape (e.g. novel ``CHAPTER_OF`` /
        ``SCENE_OF``). The parent edge is recorded BEFORE the SERVES edge,
        preserving the existing call order. Returns the new node id.
        """
        nid = self.memory.record(label, props)
        if parent and edge:
            self.memory.link(nid, parent, edge)
        self.memory.link(nid, self.intent_id, "SERVES")
        return nid

    def link(self, src: str, dst: str, rel: str, props: Optional[dict] = None) -> None:
        self.memory.link(src, dst, rel, props)

    def recall(self, node_id: str, as_of: Optional[int] = None):
        return self.memory.recall(node_id, as_of=as_of)

    def recall_typed(self, node_id: str, label: str):
        """Properties of a node iff it exists AND carries ``label`` (Spec 056).
        Delegates to ``Memory.recall_typed`` — the type-safe id guard."""
        return self.memory.recall_typed(node_id, label)

    def update(self, node_id: str, props: dict) -> None:
        """Update a node's mutable properties — graph-canonical write
        (Spec 048 bi-temporal: a new revision, NOT a destructive overwrite).
        Symmetric with ``record``/``link``/``recall``; lets a verb flip a
        status / append metadata without dropping to ``ctx.memory.update``.
        """
        self.memory.update(node_id, props)

    def supersede(self, node_id: str, changes: dict) -> str:
        """Append-only amend (Spec 293): close the old version + create a new
        one linked ``SUPERSEDED_BY``. Returns the new node id. The write-side
        twin of ``update`` for entities that must keep full history."""
        return self.memory.supersede(node_id, changes)

    def retract(self, node_id: str) -> int:
        """Bi-temporal soft delete (Spec 293): close the node's valid window so
        current reads drop it while history is retained. Returns the close tick."""
        return self.memory.retract(node_id)

    def find(self, label: str, as_of: Optional[int] = None):
        return self.memory.find(label, as_of=as_of)

    def neighbors(self, node_id: str, edge: str,
                  direction: str = "in", limit: int = 100) -> list[dict]:
        """One-hop edge traversal (Spec 125). Returns property dicts of nodes
        connected to ``node_id`` via an ``edge``-typed relationship.

        ``direction="in"`` (default) finds nodes pointing AT ``node_id``
        (e.g. children via CHAPTER_OF). ``direction="out"`` finds nodes
        ``node_id`` points at (e.g. parent via CHAPTER_OF from a chapter).

        Closes the F4 dormant-edge advisory: declare an edge ⇒ traverse it
        via ``ctx.neighbors``; ``find()`` + Python filter on a foreign-key
        property is the anti-pattern this method retires.

        Spec 286 A1 — delegates to ``Memory.neighbors`` (the GraphStore read
        surface); raw Cypher lives only in ``memory.py``.
        """
        return self.memory.neighbors(node_id, edge, direction=direction, limit=limit)

    def query_nodes(self, label: str, where: Optional[dict] = None) -> list[dict]:
        """Labeled nodes filtered by exact property match (Spec 286 A1).
        Delegates to ``Memory.query_nodes``."""
        return self.memory.query_nodes(label, where=where)

    def nodes_serving(self, intent_id, label: Optional[str] = None,
                      where: Optional[dict] = None) -> list[dict]:
        """Nodes with a SERVES edge to an intent (Spec 286 A1).
        Delegates to ``Memory.nodes_serving``."""
        return self.memory.nodes_serving(intent_id, label=label, where=where)

    def sources_via_edge(self, edge: str, target_id, target_label: str,
                         label: Optional[str] = None,
                         where: Optional[dict] = None) -> list[dict]:
        """Nodes pointing at ``target_id`` via ``edge`` (Spec 286 A1).
        Delegates to ``Memory.sources_via_edge``."""
        return self.memory.sources_via_edge(edge, target_id, target_label,
                                            label=label, where=where)

    def edge_pairs(self, edge: str, src_label: Optional[str] = None,
                   dst_label: Optional[str] = None) -> list[tuple[dict, dict]]:
        """Every ``edge`` relationship as (src, dst) property-dict pairs
        (Spec 286 A1). Delegates to ``Memory.edge_pairs``."""
        return self.memory.edge_pairs(edge, src_label=src_label, dst_label=dst_label)

    def has_edge(self, src_id: str, dst_id, edge: str,
                 src_label: Optional[str] = None,
                 dst_label: Optional[str] = None) -> bool:
        """True iff ``src_id`` --``edge``--> ``dst_id`` exists (Spec 286 A1).
        Delegates to ``Memory.has_edge``."""
        return self.memory.has_edge(src_id, dst_id, edge,
                                    src_label=src_label, dst_label=dst_label)

    def artefacts_produced_under(self, intent_id) -> list[dict]:
        """Artefacts PRODUCED by an Invocation serving ``intent_id`` (Spec 286
        A1). Delegates to ``Memory.artefacts_produced_under``."""
        return self.memory.artefacts_produced_under(intent_id)

    def labels_of(self, node_id: str) -> list[str]:
        """The label set of a node (Spec 286 A1).
        Delegates to ``Memory.labels_of``."""
        return self.memory.labels_of(node_id)

    def template(self, name: str) -> "Template":
        """Spec 060 — load a template by stem from the engine's merged
        ontology. Engine bootstrap discovers per-capability `templates/`
        folders + merges them with declared `OntologyExtension.templates`
        entries; this accessor is the read side.

        Inputs: name (str — the template's kebab-case file stem).
        Returns: `string.Template` body; the agent applies `.substitute(
                 **fields)` for rendering, OR reads `.template` directly
                 for the verbatim body incl. `<!-- AGENT: -->` blocks
                 (Spec 060 agent-instruction doctrine).
        Raises: KeyError when no template with that name is registered.
        chain_next: caller renders OR forwards the body to a verb that
                    persists the resulting Artefact.
        """
        templates = getattr(self.ontology, "templates", {}) or {}
        if name not in templates:
            raise KeyError(
                f"template {name!r} not registered in ontology — "
                f"declare it via OntologyExtension.templates or ship "
                f"a file at <cap>/templates/{name}.md (Spec 060)")
        return templates[name]


def verb(role: str, inject: Optional[list] = None,
         name: Optional[str] = None,
         param_enums: Optional[dict] = None,
         param_shapes: Optional[dict] = None) -> Callable:
    """Mark a CapabilityBase method as a verb (its role, + any extra injects beyond
    the always-injected `ctx`). `name` lets a verb register under a different
    public name than its Python method (e.g. `import_` → `import` when the
    natural verb name collides with a Python keyword).

    Spec 284 — `param_enums` maps a parameter name to its canonical member set
    (an iterable, typically the same module constant the ontology enum
    references — single source). `engine._wire` surfaces those members in
    `get_schema` (JSON `enum` + a description hint) without forcing wire-level
    rejection, so a *projected enum* param can accept rich free text and project
    it in the verb body. See `agency/_enums.py::project_enum`.

    Spec 390 — `param_shapes` maps a parameter name to a short literal of its
    required nested object/array shape (e.g. ``{"context": "[{id, text}]"}``).
    `engine._wire` folds it into the tool description as a "Shapes:" hint so
    `get_schema` shows the shape instead of a bare ``any[]`` — description-only,
    no wire-level validation (a list/object param stays permissive)."""
    def deco(fn: Callable) -> Callable:
        fn._verb = {"role": role, "inject": list(inject or []), "name": name,
                    "param_enums": dict(param_enums or {}),
                    "param_shapes": dict(param_shapes or {})}
        return fn
    return deco


def requires_driver(name: str, as_: Optional[str] = None) -> Callable:
    """Spec 286 P3 #4 — a ``CapabilityBase`` verb decorator that owns the
    fetch-or-fail idiom so the verb body never repeats it.

    Replaces the 2-line guard that was copy-pasted at ~70 single-driver verb
    sites::

        # before
        @verb(role="effect")
        def publish_asset(self, album, key, body=""):
            cloud, _fail = self._require_drv("music_cloud")
            if _fail: return _fail
            ...use cloud...

        # after
        @verb(role="effect")
        @requires_driver("music_cloud", as_="cloud")
        def publish_asset(self, album, key, body="", *, cloud):
            ...use cloud...   # cloud is guaranteed present

    At call time the wrapper runs ``self._require_drv(name)`` (so the
    capability's own override — e.g. ``_MusicBase``'s lazy production-driver
    auto-wiring — still fires) and:

    * on success injects the driver as a keyword argument under ``as_`` (or
      ``name`` when ``as_`` is omitted) and calls the verb body;
    * on a ``DriverMissing`` miss SHORT-CIRCUITS to the EXACT same typed
      ``DEPENDENCY_MISSING`` ``ToolResult`` ``_require_drv`` returns today —
      so the failure shape (code / message / severity) is byte-identical.

    The injected parameter is HIDDEN from the verb's public signature (it is
    not a user-facing input), so ``get_schema`` / the wire contract are
    unchanged. The verb body declares the injected name as a (keyword-only)
    parameter and assumes the driver is present.

    Decorator order — apply ``@requires_driver`` BELOW ``@verb`` (i.e.
    ``@verb`` outermost). Both orders are MADE TO WORK: ``requires_driver``
    propagates any ``_verb`` metadata it finds on the wrapped function up to
    the wrapper, and ``verb`` overwrites ``_verb`` on whatever it decorates —
    so ``@verb`` / ``@requires_driver`` and ``@requires_driver`` / ``@verb``
    both register the verb correctly. The recommended, documented order is
    ``@verb`` then ``@requires_driver`` (verb on top), matching the migrated
    call sites.

    Stack the decorator twice for a 2-driver verb (each injects its own
    kwarg); verbs needing a more bespoke multi-driver dance stay on the raw
    ``_require_drv`` 2-tuple helper.
    """
    import functools

    kw_name = as_ or name

    def deco(fn: Callable) -> Callable:
        # The verb's user-facing signature is the wrapped fn's params MINUS
        # the injected driver param (and minus `self`, handled by _wrap_method).
        # We compute it here so __signature__ on the wrapper hides `kw_name`.
        try:
            sig = inspect.signature(fn)
            visible = [p for n, p in sig.parameters.items() if n != kw_name]
            hidden_sig = inspect.Signature(visible)
        except (ValueError, TypeError):
            hidden_sig = None

        @functools.wraps(fn)
        def wrapper(self, *args, **kw):
            driver, fail = self._require_drv(name)
            if fail:
                return fail
            kw[kw_name] = driver
            return fn(self, *args, **kw)

        # Propagate verb metadata regardless of decorator order: if @verb ran
        # first (below us), carry its `_verb` up; if @verb runs after (above
        # us) it overwrites this wrapper's `_verb` — either order registers.
        meta = getattr(fn, "_verb", None)
        if meta is not None:
            wrapper._verb = meta
        if hidden_sig is not None:
            wrapper.__signature__ = hidden_sig
        # Stamp the injected name so a second stacked @requires_driver / future
        # introspection can see what this layer injects.
        wrapper.__requires_driver__ = getattr(fn, "__requires_driver__", ()) + (
            (name, kw_name),)
        return wrapper

    return deco


def _wrap_method(cls: type, public: str, mname: str, member: Callable,
                 meta: dict) -> Verb:
    # user params = the method's signature minus `self` (ctx is injected, not user-facing)
    params = [p for n, p in inspect.signature(member).parameters.items() if n != "self"]

    def fn(ctx, **kw):
        return getattr(cls(ctx), mname)(**kw)

    fn.__name__ = mname
    fn.__doc__ = member.__doc__
    fn.__signature__ = inspect.Signature(params)
    # Spec 016 P4: expose the underlying class so lint_capability (and any
    # future introspector) can reach the source file the verb was authored
    # in — the closure above otherwise hides it behind capability.py.
    fn.__capability_cls__ = cls
    fn.__capability_method__ = member
    # Spec 286-A4 — a typed Verb, not a free dict. `tags` defaults to an empty
    # set; `Registry.register` strips manual `skill:*` tags and `_wire_skill_tags`
    # appends the legitimate ones post-registration.
    return Verb(name=public, role=meta["role"], fn=fn,
                inject=["ctx"] + meta["inject"],
                param_enums=dict(meta.get("param_enums") or {}),
                param_shapes=dict(meta.get("param_shapes") or {}))


@dataclass
class SkillDoc:
    """Rendering metadata for the per-capability SKILL.md emission (Spec 031 §13).

    Single-responsibility: how this capability is documented to a fresh agent.
    No phase-graphs (those live on WalkerSkills); no verb impls (those are
    @verb methods on the capability class).
    """
    description: str
    overview: str
    triggers: list[str]
    canonical_example: str
    red_flags: list[str] = field(default_factory=list)
    required_subskills: list[str] = field(default_factory=list)
    verb_briefs: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_module(cls, module, cap_name: str,
                    verb_names: list[str]) -> "Optional[SkillDoc]":
        """Spec 080 — derive a SkillDoc from a capability's MODULE docstring.

        The docstring is the single source: ``Use when:`` / ``Triggers:`` /
        ``Red flags:`` sections carry the judgment; overview + example derive for
        free. Returns ``None`` when the docstring has no ``Use when:`` marker (the
        capability must then set ``skill_doc`` explicitly). Used by
        ``as_capability`` so a capability that doesn't declare a literal still
        gets a complete Agent Skill from its docstring — no redundant strings."""
        from .disclosure import parse_module_skill
        doc = getattr(module, "__doc__", None)
        parsed = parse_module_skill(doc, cap_name, list(verb_names))
        if parsed is None:
            return None
        return cls(**parsed)


@dataclass
class WalkerSkills:
    """Phase-graph schemas this capability owns (Spec 031 §13).

    Single-responsibility: what skill-walks this capability provides.
    Schemas keep the existing dict shape ({name, kind, phases:[...]}).
    Merges into OntologyExtension.skills at engine bootstrap; OntologyExtension
    keeps the merge target unchanged for backwards compatibility.
    """
    schemas: dict[str, dict] = field(default_factory=dict)


# Spec 081 — canonical role ordering for a derived usage-walk: read/compute first,
# then side-effects, then state-changing acts, then gates.
_USAGE_ROLE_ORDER = ("transform", "effect", "act", "gate")


def derive_usage_skill(cap_name: str, verbs: dict) -> dict:
    """Derive a `<cap>-usage` walkable skill from a capability's verbs (Spec 081).

    Clusters the verbs by role into ≤5 work-phases (canonical order: transform →
    effect → act → gate), each naming the verbs it drives, and appends a hard
    `confirm` gate — so a fresh agent can `develop.skill_walk('<cap>-usage', …)`
    to learn how to drive the capability's MCP surface. A scaffold that guarantees
    coverage; high-value capabilities AUTHOR a richer discipline instead (which, as
    a declared `ontology.skills`, overrides this)."""
    by_role: dict[str, list[str]] = {}
    for vname, spec in verbs.items():
        by_role.setdefault(spec.get("role", "transform"), []).append(vname)
    phases: list[dict] = []
    idx = 1
    for role in _USAGE_ROLE_ORDER:
        if role not in by_role:
            continue
        phases.append({"index": idx, "name": f"use-{role}",
                       "produces": [f"{role}_result"], "verbs": sorted(by_role[role])})
        idx += 1
        if idx > 5:          # cap at 5 work-phases + the confirm gate = 6 total
            break
    phases.append({"index": idx, "name": "confirm",
                   "produces": ["outcome_confirmed"], "gate": "hard"})
    return {"name": f"{cap_name}-usage", "kind": "usage", "phases": phases}


@dataclass
class TemplateDoc:
    """Rendering metadata for ONE template the capability ships (Spec 032 §A).

    Drives one row in the SKILL.md ## Templates table generated by Spec 031's
    install pipeline. A capability with templates that need NO documentation
    can ship them without a TemplateDoc — they'll appear with the filename
    as the only hint.
    """
    description: str
    canonical_example: str


@dataclass
class SchemaDoc:
    """Rendering metadata for ONE schema the capability ships (Spec 032 §A).

    Drives one row in the SKILL.md ## Schemas table. Same shape + purpose as
    TemplateDoc.
    """
    description: str
    canonical_example: str


@dataclass
class RenderTemplates:
    """The capability's owned templates (Spec 032 §A).

    `folder` is the absolute path to the capability's templates/ folder.
    Use the `from_module` classmethod to resolve it relative to the
    capability module's __file__ (avoids `Path(__file__).parent` boilerplate
    and packaging issues — panel F-7).

    `docs` is a dict mapping filename stem to TemplateDoc. Templates without
    a matching doc still load + materialise as Template nodes; they just
    appear without rendering metadata in the SKILL.md table.
    """
    folder: Path
    docs: dict[str, "TemplateDoc"] = field(default_factory=dict)

    @classmethod
    def from_module(cls, module_file: str, subfolder: str = "templates",
                    docs: Optional[dict] = None) -> "RenderTemplates":
        """Resolve folder relative to the capability module's __file__."""
        return cls(folder=Path(module_file).parent / subfolder,
                   docs=docs or {})


@dataclass
class ArtefactSchemas:
    """The capability's owned schemas (Spec 032 §A).

    Same shape as RenderTemplates but for schemas/ folder + SchemaDoc dict.
    """
    folder: Path
    docs: dict[str, "SchemaDoc"] = field(default_factory=dict)

    @classmethod
    def from_module(cls, module_file: str, subfolder: str = "schemas",
                    docs: Optional[dict] = None) -> "ArtefactSchemas":
        """Resolve folder relative to the capability module's __file__."""
        return cls(folder=Path(module_file).parent / subfolder,
                   docs=docs or {})


class CapabilityBase:
    """Optional class form: subclass, set `name`/`home`/`ontology`, decorate
    verb-methods with `@verb(...)`, and reach services via `self.ctx`. Compiled to
    a plain `Capability` by `as_capability()`, so discovery + auto-wiring are
    unchanged. The functional form remains equally valid."""
    name: str = ""
    home: str = "capability"
    ontology: OntologyExtension = OntologyExtension()
    # Spec 031 §13 — rendering metadata + walker schemas.
    # `skill_doc` is REQUIRED for any capability with >=1 verb (validated at
    # engine bootstrap, Task 1.2); `walker_skills` is optional always.
    skill_doc: ClassVar[Optional[SkillDoc]] = None
    walker_skills: ClassVar[Optional[WalkerSkills]] = None
    # Spec 032 §A — template + schema file-based extensions.
    render_templates: ClassVar[Optional[RenderTemplates]] = None
    artefact_schemas: ClassVar[Optional[ArtefactSchemas]] = None
    # Spec 349b §2 — declarative event-bus subscriptions (a tuple of
    # `_events.Subscription`). Empty by default; `as_capability` carries them +
    # the module onto the compiled `Capability` for the bootstrap loop.
    subscriptions: ClassVar[tuple] = ()
    # Spec 342 — the parameterization (machine-registry key) a member cap's
    # dispatched children run under; carried onto the compiled Capability so
    # delegate.fan_out reads it. "" = default a2a (no observer).
    parameterization: ClassVar[str] = ""

    def __init__(self, ctx: CapabilityContext):
        self.ctx = ctx

    def _require_drv(self, name: str) -> tuple[Any, Any]:
        """Cleanup helper (Spec 097 review-driven): get a named Driver or return
        a typed DEPENDENCY_MISSING ToolResult. Replaces a 4-line
        ``try: drv = self.ctx.get_driver(name) except DriverMissing: return
        ToolResult.failure("DEPENDENCY_MISSING", ...)`` idiom that was repeated
        60+ times across the music cluster.

        Verb-level usage::

            drv, fail = self._require_drv("music_state")
            if fail: return fail

        Returns ``(driver, None)`` on success, ``(None, ToolResult)`` on missing.
        The 2-tuple shape avoids type ambiguity that a single-return helper
        would introduce (a Driver could theoretically be a ToolResult).
        """
        from .toolresult import ToolResult, Codes
        try:
            return self.ctx.get_driver(name), None
        except DriverMissing:
            return None, ToolResult.failure(
                Codes.DEPENDENCY_MISSING,
                f"no {name!r} driver registered")

    @classmethod
    def as_capability(cls) -> Capability:
        verbs = {}
        for mname, member in inspect.getmembers(cls, predicate=callable):
            meta = getattr(member, "_verb", None)
            if not meta:
                continue
            public = meta.get("name") or mname
            verbs[public] = _wrap_method(cls, public, mname, member, meta)
        # Spec 060 fix: deepcopy the ontology so capability instances
        # don't share dict references via the class-level default
        # `CapabilityBase.ontology = OntologyExtension()`. Bootstrap
        # mutations (file-loaded templates/schemas merging into
        # cap.ontology.{templates,schemas}) would otherwise leak across
        # caps that inherit the same default instance.
        import copy as _copy
        # Spec 080 — a capability's skill_doc is DERIVED from its module docstring
        # (single source) unless it sets one explicitly. So a drop-in capability
        # folder needs only a well-formed docstring; no redundant SkillDoc literal.
        skill_doc = getattr(cls, "skill_doc", None)
        if skill_doc is None:
            import sys as _sys
            module = _sys.modules.get(cls.__module__)
            if module is not None:
                skill_doc = SkillDoc.from_module(module, cls.name, list(verbs))
        ontology = _copy.deepcopy(cls.ontology)
        # Spec 081 — every capability ships a WALKABLE skill. A cap that authored
        # no `ontology.skills` gets a DERIVED `<cap>-usage` phase-graph (verbs
        # clustered by role → walk via develop.skill_walk). Authored skills are
        # the override — never replaced.
        if verbs and not getattr(ontology, "skills", None):
            ontology.skills[f"{cls.name}-usage"] = derive_usage_skill(cls.name, verbs)
        return Capability(
            name=cls.name, home=cls.home, verbs=verbs,
            ontology=ontology,
            render_templates=cls.render_templates,
            artefact_schemas=cls.artefact_schemas,
            # PR review round 8 — preserve class-form authoring metadata
            # so install.generate() finds the SKILL.md spec and
            # walker_skills configuration even after class→dataclass
            # conversion.
            skill_doc=skill_doc,
            walker_skills=getattr(cls, "walker_skills", None),
            # Spec 349b §2 — carry declarative subscriptions + the source module
            # so the engine's bootstrap loop can resolve each handler by name.
            subscriptions=tuple(getattr(cls, "subscriptions", ()) or ()),
            module=cls.__module__,
            # Spec 342 — carry the parameterization declaration so delegate.fan_out
            # opens dispatched children on the declared machine.
            parameterization=getattr(cls, "parameterization", ""))


class Registry:
    def __init__(self) -> None:
        self._caps: dict[str, Capability] = {}
        # engine-supplied verb-param providers (the `inject` convention), e.g.
        # {"client": () -> jules_client, "caps": () -> the live verb map}. The
        # per-call `memory` and `intent_id` are injected by name from invoke().
        self.injectors: dict[str, Callable[[], Any]] = {}
        self.drivers: Any = None        # Spec 002 — the engine's DriverRegistry (named boundary table)
        self.ontology: Any = None       # the effective Ontology; set by the engine (for ctx)
        # Spec 286-A3 — `invoke` is now an orchestrator over four single-purpose
        # collaborators (guard → inject → record → call → process). The Registry
        # holds them; the wire contract + provenance are byte-identical.
        from ._invoke import (
            IntentGuard, ParameterInjector, InvocationRecorder, ResultProcessor,
        )
        self._guard = IntentGuard()
        self._injector = ParameterInjector(self)
        self._recorder = InvocationRecorder()
        self._processor = ResultProcessor()  # holds the post-invocation hook seam

    def register(self, cap: Capability) -> None:
        # Spec 286-A4 — normalise functional-form verbs (raw `{role, fn, ...}`
        # dicts passed to `Capability(verbs={...})`) into typed `Verb` value
        # objects. Class-form caps already arrive as `Verb`s from
        # `as_capability`; `Verb.from_spec` passes those through unchanged.
        cap.verbs = {name: Verb.from_spec(name, spec)
                     for name, spec in cap.verbs.items()}
        # Spec 025 Phase 1: every verb carries a `tags` set. Manual `skill:*`
        # tags are stripped — only phase-invoke wiring (below, in
        # `_wire_skill_tags`) legitimately creates them. This preserves the
        # discovery invariant: `tags=["skill:X"]` filters to exactly the verbs
        # that participate in skill X's phase graph.
        for verb in cap.verbs.values():
            verb.tags = {t for t in verb.tags if not t.startswith("skill:")}
        self._caps[cap.name] = cap
        self._wire_skill_tags(cap)

    def _wire_skill_tags(self, cap: Capability) -> None:
        """Walk `cap.ontology.skills`; for every phase with
        `invoke={capability, verb}`, tag the bound verb `skill:<skillname>`.

        Cross-capability wiring: the `develop.review` skill binds to
        `delegate.fan_out`, so this method (called once per registered
        cap) tags verbs on OTHER capabilities. It is idempotent and
        order-insensitive: when a skill names a verb whose capability is
        not yet registered, we re-walk on every register call. Cheap —
        skills are O(handful)."""
        for owner_name, owner_cap in self._caps.items():
            skills = getattr(owner_cap.ontology, "skills", {}) or {}
            for skill_name, schema in skills.items():
                for phase in schema.get("phases", ()):
                    invoke = phase.get("invoke")
                    if not invoke:
                        continue
                    target_cap = self._caps.get(invoke.get("capability"))
                    if target_cap is None:
                        continue
                    target_verb = target_cap.verbs.get(invoke.get("verb"))
                    if target_verb is None:
                        continue
                    target_verb.tags.add(f"skill:{skill_name}")

    def get(self, name: str) -> Capability:
        return self._caps[name]

    def names(self) -> list[str]:
        return sorted(self._caps)

    def invoke(self, memory: Memory, intent_id: str, cap_name: str, verb: str,
               agent_id: Optional[str] = None, _depth: int = 0, **args) -> tuple[Any, str]:
        """Spec 286-A3 — orchestrate the four invocation collaborators:
        **guard → inject → record → call(try/except) → process**. Each step's
        logic lives in a single-purpose class (`agency/_invoke.py`); this method
        only sequences them. Behaviour — provenance nodes/edges, error messages,
        Spec 282 severity, the ToolResult unwrap to `.data`, the
        `(result, invocation_id)` return — is identical to the former inline
        body (the moat's chokepoint stays byte-stable).
        """
        cap = self._caps[cap_name]
        spec = cap.verbs[verb]
        # 1. inject — build the verb call kwargs (ctx / memory / intent_id +
        #    derived injectors). Pure construction; no side-effects.
        call = self._injector.build_call(spec, memory, intent_id, agent_id,
                                         _depth, args)
        # 2. guard — reject a non-Intent intent_id BEFORE any side-effect (the
        #    SERVES edge is the moat's foundation). Raises the same ValueError.
        self._guard.require_intent(memory, intent_id)
        # 3. record — open the Invocation (+ SERVES, agent upsert + PERFORMED_BY)
        #    BEFORE calling, so a verb that raises still leaves an auditable run.
        inv = self._recorder.open(memory, intent_id, cap_name, verb,
                                  spec.role, agent_id)
        # 4. call — invoke the verb; on exception stamp outcome=failed + the
        #    Spec 282 severity, then re-raise.
        try:
            result = spec.fn(**call)
        except Exception as e:
            self._recorder.record_exception(memory, inv, e)
            raise
        # 5. process — ToolResult unwrap + side-effect recording (trace_id stamp,
        #    outcome/error/warnings/archived_to, artefacts → Artefact+PRODUCES,
        #    the {artefact} dict path), then the post-invocation hook seam. Returns
        #    the unwrapped `.data`.
        result = self._processor.process(memory, inv, intent_id, result)
        return result, inv
