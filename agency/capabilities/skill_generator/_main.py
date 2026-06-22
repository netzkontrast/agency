# agency-scaffold: v1
"""skill_generator — generate a deploy-ready skill in one call.

Skill_generator produces a deploy-ready skill in a single call, emitting a CSO-clean SKILL.md from a name and description.

Use when: a deploy-ready skill should be produced in one call — a complete, CSO-clean SKILL.md generated from a description.
Triggers:
- A new skill needed without hand-assembling its files
- A skill idea that should become a deployable artefact
"""
from __future__ import annotations

import inspect

from ...capability import CapabilityBase, verb


def _public_signature(fn) -> str:
    """The author-facing call signature of a verb — `self`, `ctx`, and any
    declared `@verb(inject=[…])` params stripped (the engine supplies them; an
    author referencing the verb never passes them). Derived from the live
    function, not authored (rule 2)."""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return "()"
    injected = {"self", "ctx"} | set(getattr(fn, "_verb", {}).get("inject", []))
    params = [p for n, p in sig.parameters.items() if n not in injected]
    return str(sig.replace(parameters=params))


def build_grounding(cap, spec_text: str = "") -> dict:
    """Spec 374 Slice 1 — the structured grounding a skill-creator prompt fills
    (Slice 2), AND the graceful no-host fallback an author reads by hand: a
    capability's LIVE verbs + signatures + docstrings + ontology, plus an
    optional governing-spec excerpt.

    Pure + deterministic (no host LLM, no I/O) — it reads the registry object
    and nothing else, so the same capability yields the same bytes (A7).
    Docstrings are carried in FULL (rule 9 — a skill authored from a clipped
    docstring would teach a clipped skill)."""
    verbs = []
    for name in sorted(cap.verbs):
        fn = cap.verbs[name].get("fn")
        verbs.append({
            "name": name,
            "role": cap.role(name),
            "signature": _public_signature(fn) if fn else "()",
            "doc": (fn.__doc__ or "") if fn else "",
        })
    ont = cap.ontology
    ontology = {
        "nodes": sorted(getattr(ont, "nodes", {}) or {}),
        "edges": sorted(getattr(ont, "edges", set()) or set()),
        "skills": sorted(getattr(ont, "skills", {}) or {}),
    }
    return {"capability": cap.name, "home": cap.home,
            "verbs": verbs, "ontology": ontology, "spec": spec_text}


class SkillGeneratorCapability(CapabilityBase):
    name = "skill_generator"
    home = "capability"

    @verb(role="transform")
    def ground(self, capability: str, spec_text: str = "") -> dict:
        """Build the authoring grounding for a capability — its live verbs,
        signatures, docstrings, and ontology — the structured input a
        skill-creator prompt fills, and the no-host fallback an author reads.

        Inputs: capability (a name in the live registry), spec_text (optional
                governing-spec excerpt to ground the author in).
        Returns: ``{result: {capability, home, verbs:[{name,role,signature,doc}],
                 ontology:{nodes,edges,skills}, spec}}``; or ``{error, available}``
                 when the capability is unknown.
        chain_next: ``skill_generator`` samples the host with this grounding to
                    draft a schema-valid skill (Spec 374 Slice 2).
        """
        try:
            cap = self.ctx.registry.get(capability)
        except KeyError:
            return {"result": {"error": f"unknown capability {capability!r}",
                               "available": self.ctx.registry.names()}}
        return {"result": build_grounding(cap, spec_text=spec_text)}

    @verb(role="act")
    def generate(self, name: str, description: str, body: str) -> dict:
        """Author a SKILL.md and lint it against the CSO rules, flagging if not deploy-ready.

        Inputs: name (skill slug), description (str — the trigger phrase),
                body (str — the SKILL.md content).
        Returns: ``{name, skill_md, ok, violations}`` (wire shape).
        chain_next: caller writes ``skills/<name>/SKILL.md`` if ``ok=True``;
                    otherwise iterates on ``violations``.
        """
        skill_md = self.ctx.call("plugin", "author_skill",
                                 name=name, description=description, body=body)["result"]
        lint = self.ctx.call("plugin", "lint_skill", name=name, description=description)
        return {"result": {"name": name, "skill_md": skill_md,
                           "ok": lint["ok"], "violations": lint["violations"]}}
