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
from string import Template as _Template
from typing import Any, Callable, ClassVar, Optional

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

    def role(self, verb: str) -> str:
        return self.verbs[verb]["role"]


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
    MAX_DEPTH: int = 16

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

    def render(self, template: str, **vars: Any) -> str:
        return _Template(self.ontology.templates[template]).substitute(**vars)

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

    def find(self, label: str, as_of: Optional[int] = None):
        return self.memory.find(label, as_of=as_of)


def verb(role: str, inject: Optional[list] = None) -> Callable:
    """Mark a CapabilityBase method as a verb (its role, + any extra injects beyond
    the always-injected `ctx`)."""
    def deco(fn: Callable) -> Callable:
        fn._verb = {"role": role, "inject": list(inject or [])}
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


@dataclass
class WalkerSkills:
    """Phase-graph schemas this capability owns (Spec 031 §13).

    Single-responsibility: what skill-walks this capability provides.
    Schemas keep the existing dict shape ({name, kind, phases:[...]}).
    Merges into OntologyExtension.skills at engine bootstrap; OntologyExtension
    keeps the merge target unchanged for backwards compatibility.
    """
    schemas: dict[str, dict] = field(default_factory=dict)


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
    skill_doc: ClassVar["SkillDoc | None"] = None
    walker_skills: ClassVar["WalkerSkills | None"] = None

    def __init__(self, ctx: CapabilityContext):
        self.ctx = ctx

    @classmethod
    def as_capability(cls) -> Capability:
        verbs = {mname: _wrap_method(cls, mname, member, getattr(member, "_verb"))
                 for mname, member in inspect.getmembers(cls, predicate=callable)
                 if getattr(member, "_verb", None)}
        return Capability(name=cls.name, home=cls.home, verbs=verbs, ontology=cls.ontology)


class Registry:
    def __init__(self) -> None:
        self._caps: dict[str, Capability] = {}
        # engine-supplied verb-param providers (the `inject` convention), e.g.
        # {"client": () -> jules_client, "caps": () -> the live verb map}. The
        # per-call `memory` and `intent_id` are injected by name from invoke().
        self.injectors: dict[str, Callable[[], Any]] = {}
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
                    depth=_depth, engine=getattr(self, "engine", None))
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
