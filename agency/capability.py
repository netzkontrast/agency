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
from typing import Any, Callable, Optional

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
    return {"role": meta["role"], "fn": fn, "inject": ["ctx"] + meta["inject"]}


class CapabilityBase:
    """Optional class form: subclass, set `name`/`home`/`ontology`, decorate
    verb-methods with `@verb(...)`, and reach services via `self.ctx`. Compiled to
    a plain `Capability` by `as_capability()`, so discovery + auto-wiring are
    unchanged. The functional form remains equally valid."""
    name: str = ""
    home: str = "capability"
    ontology: OntologyExtension = OntologyExtension()

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
        self._caps[cap.name] = cap

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
                    depth=_depth)
            elif name == "memory":
                call["memory"] = memory
            elif name == "intent_id":
                call["intent_id"] = intent_id
            elif name in self.injectors:
                call[name] = self.injectors[name]()
        # record the Invocation BEFORE calling, so a verb that raises still leaves a
        # SERVES invocation in provenance (a failed run must be auditable too).
        inv = memory.record("Invocation", {
            "capability": cap_name, "verb": verb, "role": spec["role"],
        })
        memory.link(inv, intent_id, "SERVES")
        if agent_id:
            memory.link(inv, agent_id, "PERFORMED_BY")  # 'BY' is a Cypher reserved word
        try:
            result = spec["fn"](**call)
        except Exception as e:
            memory.update(inv, {"outcome": "failed", "error": f"{type(e).__name__}: {e}"})
            raise
        if isinstance(result, dict) and result.get("artefact"):
            art = memory.record("Artefact", dict(result["artefact"]))
            memory.link(inv, art, "PRODUCES")
        return result, inv
