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


@dataclass
class Capability:
    name: str
    home: str                       # which concept it primarily is
    verbs: dict[str, dict]          # verb -> {"role": str, "fn": callable, "inject": [...]}
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

    def role(self, verb: str) -> str:
        return self.verbs[verb]["role"]


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
    """Spec 002 — ``Registry.injectors`` generalized to a named table. A domain
    tool-cluster plugs in by registering a driver under a name and needs NO new
    ``Engine`` kwarg and NO new ``injectors`` key. Named lookup + a uniform result
    type (via the wrapping verb) is the whole value."""

    def __init__(self, drivers: Optional[dict[str, Any]] = None):
        self._drivers: dict[str, Any] = dict(drivers or {})

    def register(self, name: str, driver: Any) -> None:
        """Register (or replace) the driver under ``name``."""
        self._drivers[name] = driver

    def get(self, name: str) -> Any:
        try:
            return self._drivers[name]
        except KeyError:
            raise DriverMissing(
                f"no driver registered under {name!r}; have {sorted(self._drivers)}"
            ) from None

    def has(self, name: str) -> bool:
        return name in self._drivers

    def names(self) -> list[str]:
        return sorted(self._drivers)


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

    def link(self, src: str, dst: str, rel: str, props: Optional[dict] = None) -> None:
        self.memory.link(src, dst, rel, props)

    def recall(self, node_id: str, as_of: Optional[int] = None):
        return self.memory.recall(node_id, as_of=as_of)

    def update(self, node_id: str, props: dict) -> None:
        """Update a node's mutable properties — graph-canonical write
        (Spec 048 bi-temporal: a new revision, NOT a destructive overwrite).
        Symmetric with ``record``/``link``/``recall``; lets a verb flip a
        status / append metadata without dropping to ``ctx.memory.update``.
        """
        self.memory.update(node_id, props)

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

        Returns ``[]`` for unknown ids or no matching edges. ``limit`` caps
        the row count (default 100, matches ``analyze.graph`` shape).
        """
        if direction not in ("in", "out"):
            raise ValueError(
                f"direction must be 'in' or 'out', got {direction!r}")
        if direction == "in":
            q = (f"MATCH (n)-[:{edge}]->(t) WHERE t.id = $id "
                 f"RETURN n LIMIT {int(limit)}")
            key = "n"
        else:
            q = (f"MATCH (n)-[:{edge}]->(t) WHERE n.id = $id "
                 f"RETURN t LIMIT {int(limit)}")
            key = "t"
        rows = self.memory.g.query(q, {"id": node_id})
        return [r[key]["properties"] for r in rows]

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
         name: Optional[str] = None) -> Callable:
    """Mark a CapabilityBase method as a verb (its role, + any extra injects beyond
    the always-injected `ctx`). `name` lets a verb register under a different
    public name than its Python method (e.g. `import_` → `import` when the
    natural verb name collides with a Python keyword)."""
    def deco(fn: Callable) -> Callable:
        fn._verb = {"role": role, "inject": list(inject or []), "name": name}
        return fn
    return deco


def _wrap_method(cls: type, mname: str, member: Callable, meta: dict) -> dict:
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
    return {"role": meta["role"], "fn": fn, "inject": ["ctx"] + meta["inject"]}


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
        from .toolresult import ToolResult
        try:
            return self.ctx.get_driver(name), None
        except DriverMissing:
            return None, ToolResult.failure(
                "DEPENDENCY_MISSING",
                f"no {name!r} driver registered")

    @classmethod
    def as_capability(cls) -> Capability:
        verbs = {}
        for mname, member in inspect.getmembers(cls, predicate=callable):
            meta = getattr(member, "_verb", None)
            if not meta:
                continue
            public = meta.get("name") or mname
            verbs[public] = _wrap_method(cls, mname, member, meta)
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
            walker_skills=getattr(cls, "walker_skills", None))


class Registry:
    def __init__(self) -> None:
        self._caps: dict[str, Capability] = {}
        # engine-supplied verb-param providers (the `inject` convention), e.g.
        # {"client": () -> jules_client, "caps": () -> the live verb map}. The
        # per-call `memory` and `intent_id` are injected by name from invoke().
        self.injectors: dict[str, Callable[[], Any]] = {}
        self.drivers: Any = None        # Spec 002 — the engine's DriverRegistry (named boundary table)
        self.ontology: Any = None       # the effective Ontology; set by the engine (for ctx)

    def register(self, cap: Capability) -> None:
        # Spec 025 Phase 1: every verb spec carries a `tags` set. Manual
        # `skill:*` tags are stripped — only phase-invoke wiring (below,
        # in `_wire_skill_tags`) legitimately creates them. This preserves
        # the discovery invariant: `tags=["skill:X"]` filters to exactly
        # the verbs that participate in skill X's phase graph.
        for verb_name, spec in cap.verbs.items():
            raw = spec.get("tags") or set()
            if not isinstance(raw, set):
                raw = set(raw)
            spec["tags"] = {t for t in raw if not t.startswith("skill:")}
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
                    target_verb.setdefault("tags", set()).add(f"skill:{skill_name}")

    def get(self, name: str) -> Capability:
        return self._caps[name]

    def names(self) -> list[str]:
        return sorted(self._caps)

    def invoke(self, memory: Memory, intent_id: str, cap_name: str, verb: str,
               agent_id: Optional[str] = None, _depth: int = 0, **args) -> tuple[Any, str]:
        cap = self._caps[cap_name]
        spec = cap.verbs[verb]
        call = dict(args)
        for name in spec.get("inject", []):
            if name in call:                              # an explicit arg always wins
                continue
            if name == "ctx":
                call["ctx"] = CapabilityContext(
                    memory=memory, ontology=self.ontology, registry=self,
                    intent_id=intent_id, agent_id=agent_id,
                    client=(self.injectors["client"]() if "client" in self.injectors else None),
                    depth=_depth, engine=getattr(self, "engine", None),
                    drivers=getattr(self, "drivers", None))
            elif name == "memory":
                call["memory"] = memory
            elif name == "intent_id":
                call["intent_id"] = intent_id
            elif name in self.injectors:
                call[name] = self.injectors[name]()
        # C5 (Codex review 6059c74 / capability.py:169): the SERVES edge IS
        # the moat's foundation; reject any invocation whose intent_id does not
        # resolve to a labeled Intent BEFORE recording side effects. A
        # mistyped/forged intent_id would otherwise produce an orphan
        # Invocation that the provenance traversal cannot see, while real
        # `effect` verbs still mutate the world.
        intent_node = memory.g.get_node(intent_id)
        if intent_node is None or "Intent" not in (intent_node.get("labels") or []):
            # Spec 029 §B (F6): the previous message dead-ended on a fresh
            # MCP client — every verb needs an intent, no message named the
            # bootstrap path. Now we point at the substrate tool that mints
            # one AND keep the bash side-pipe acknowledged.
            raise ValueError(
                f"intent_id {intent_id!r} is not an Intent node. "
                f"Mint one with the `intent_bootstrap` MCP substrate tool "
                f"(purpose, deliverable, acceptance) or "
                f"`python -m agency.cli intent ...` (bash side-pipe). "
                f"Call `agency_welcome` for the full onboarding payload."
            )
        # record the Invocation BEFORE calling, so a verb that raises still leaves a
        # SERVES invocation in provenance (a failed run must be auditable too).
        inv = memory.record("Invocation", {
            "capability": cap_name, "verb": verb, "role": spec["role"],
        })
        memory.link(inv, intent_id, "SERVES")
        if agent_id:
            # Ensure the agent_id resolves to a labeled Agent node so
            # `memory.provenance()`'s `MATCH ->(a:Agent)` picks it up (Codex
            # review d5758b2 / capability.py:171). When the caller passes
            # agent_id directly (e.g. MCP/CLI `jules.dispatch(agent_id=…)`)
            # without first opening a Lifecycle, this idempotent upsert keeps
            # the performer visible in audits.
            if memory.recall(agent_id) is None:
                memory.record("Agent", {"runtime": "external"}, node_id=agent_id)
            memory.link(inv, agent_id, "PERFORMED_BY")  # 'BY' is a Cypher reserved word
        try:
            result = spec["fn"](**call)
        except Exception as e:
            memory.update(inv, {"outcome": "failed", "error": f"{type(e).__name__}: {e}"})
            raise
        # ToolResult unwrap (Spec 001, Option C): when a verb returns the in-sandbox
        # envelope, record its metadata as Invocation side-effects (typed error,
        # warnings, archived_to) and replace `result` with the unwrapped `.data` so
        # the wire shape stays the lean code-mode contract (CORE.md:9-18). Plain-dict
        # returns are unchanged. The auxiliary fields are opt-in for verbs that need
        # them (esp. spec 005's context-mode middleware which writes archived_to).
        from .toolresult import ToolResult
        if isinstance(result, ToolResult):
            # Spec 059: stamp error.trace_id = inv when the verb didn't
            # supply one. Both ToolResult and TypedError are frozen, so
            # the stamp is `dataclasses.replace` (rebuild, not mutate).
            # The caller's explicit trace_id wins — we only fill the
            # empty case.
            if (result.error is not None
                    and not result.error.trace_id):
                from dataclasses import replace
                new_error = replace(result.error, trace_id=inv)
                result = replace(result, error=new_error)
            updates: dict = {}
            if not result.ok:                                    # ok=False alone marks the run failed
                updates["outcome"] = "failed"                   # (Codex review d5758b2 / capability.py:188)
            if result.error is not None:                         # TypedError, when attached, carries the message
                updates["outcome"] = "failed"
                updates["error"] = f"{result.error.code}: {result.error.message}"
            if result.warnings:
                updates["warnings"] = list(result.warnings)
            if result.archived_to:
                updates["archived_to"] = result.archived_to
            if updates:
                memory.update(inv, updates)
            # C4 (Codex review 6059c74 / capability.py:202): convert
            # `artefacts_written` into Artefact nodes + PRODUCES edges, the
            # envelope's documented purpose. Each entry is a file path the
            # verb produced; recorded so provenance shows the file-writing
            # effect, not just a clean Invocation with the path silently
            # dropped.
            for path in (result.artefacts_written or []):
                art = memory.record("Artefact", {"kind": "file", "path": str(path)})
                memory.link(inv, art, "PRODUCES")
            result = result.data
        if isinstance(result, dict) and result.get("artefact"):
            art = memory.record("Artefact", dict(result["artefact"]))
            memory.link(inv, art, "PRODUCES")
        return result, inv
