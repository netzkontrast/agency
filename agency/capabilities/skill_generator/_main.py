# agency-scaffold: v1
"""skill_generator — author a deploy-ready skill, grounded in real code.

Skill_generator builds a skill from a capability's REAL surface: `ground` reads
its live verbs + signatures + docstrings + ontology; `author` samples the host
LLM with a per-type skill-creator prompt over that grounding to draft a
schema-valid skill; `generate` renders a CSO-clean SKILL.md from a description.

Use when: a deploy-ready skill should be produced — grounded in a capability's
real verbs, not hand-assembled or hallucinated.
Triggers:
- A new skill needed without hand-assembling its files
- A skill idea that should become a deployable artefact
- Authoring a skill that must reference a capability's real verbs (not guesses)
Red flags:
- Hand-writing a SKILL.md from scratch → ground it via capability_skill_generator_ground
- Authoring a skill that references verbs not in the registry → capability_skill_generator_author grounds in the live surface
- Sampling the host at install time (breaks reproducibility, A7) → author at authoring time and commit the reviewed result
"""
from __future__ import annotations

import inspect
import json

from ...capability import CapabilityBase, verb
from ..._skill_parse import _SKILL_TYPES, _TYPE_REQUIRED, parse_skill


# Spec 374 Slice 2 — the skill-creator system rules (R1/R8/R9/F3 in brief). The
# per-type required CORE is DERIVED from `_TYPE_REQUIRED` (rule 2 — single
# source), never re-listed here.
_SKILL_CREATOR_RULES = (
    "You are a skill-creator. Author ONE agency skill as STRICT JSON (an object, "
    "no markdown, no prose outside the JSON). Rules:\n"
    "- `description` is a TRIGGER — 'Use when …' (WHEN to reach for the skill), "
    "not a summary of what it does (R1).\n"
    "- Reference ONLY verbs listed in the grounding below; a verb absent from the "
    "live registry is a hallucination and will be rejected (F3).\n"
    "- Give exactly ONE concrete example (R9); when you author phases, name each "
    "phase's degrees of freedom (R8: high|medium|low).\n"
    "- Keep the body self-contained and tight; heavy per-verb detail belongs in "
    "one-deep references (R4).\n"
)


def _skill_creator_prompt(skill_type: str, grounding: dict) -> tuple[str, str]:
    """Compose the (system, user) skill-creator prompt for a skill `type`,
    grounded in a capability's real surface (Spec 374 Slice 2). The required
    fields beyond the universal `name`/`kind`/`type`/`description` are read from
    `_TYPE_REQUIRED` (single source) so the prompt and the parser never drift."""
    required = _TYPE_REQUIRED.get(skill_type, ())
    req_phrase = ", ".join(required) if required else "(none — the capability floor)"
    system = (f"{_SKILL_CREATOR_RULES}\nThis is a '{skill_type}' skill. Beyond "
              f"name/kind/type/description, its required fields are: {req_phrase}.")
    verb_lines = "\n".join(
        f"- {v['name']}{v['signature']} [{v['role']}]: "
        f"{(v['doc'] or '').strip().splitlines()[0] if (v['doc'] or '').strip() else ''}"
        for v in grounding["verbs"])
    spec_block = (f"\nGoverning spec excerpt:\n{grounding['spec']}\n"
                  if grounding.get("spec") else "")
    keys = "name, kind, type, description" + (", " + ", ".join(required) if required else "")
    user = (f"Capability: {grounding['capability']} (home={grounding['home']}).\n"
            f"Author a '{skill_type}' skill for it.\n\n"
            f"Verbs you may reference (ONLY these):\n{verb_lines}\n\n"
            f"Ontology — nodes {grounding['ontology']['nodes']}, "
            f"edges {grounding['ontology']['edges']}, "
            f"skills {grounding['ontology']['skills']}.\n"
            f"{spec_block}\n"
            f"Return STRICT JSON with keys: {keys}.")
    return system, user


def _parse_draft(text: str) -> tuple[dict | None, str]:
    """Parse a host completion into a schema-valid skill dict (Spec 374 Slice 2).
    Strips a ```json fence if present, JSON-decodes, then validates against the
    371 schema via `parse_skill`. Returns (draft_dict, "") on success or
    (None, error) — never raises on bad model output."""
    raw = (text or "").strip()
    if raw.startswith("```"):
        inner = raw.split("```")
        raw = (inner[1] if len(inner) > 1 else "").strip()
        if raw[:4].lower() == "json":
            raw = raw[4:].strip()
    try:
        d = json.loads(raw)
    except Exception as e:
        return None, f"draft is not valid JSON: {e}"
    res = parse_skill(d)
    if not res.ok:
        return None, f"draft failed the 371 schema ({res.code}): {res.message}"
    return res.value.to_dict(), ""


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

    @verb(role="act", param_enums={"skill_type": _SKILL_TYPES})
    def author(self, capability: str, skill_type: str = "capability",
               spec_text: str = "", max_tokens: int = 8000) -> dict:
        """Draft a skill for a capability by sampling the host LLM with a per-type
        skill-creator prompt grounded in the cap's real surface (Spec 374 Slice 2).

        Authoring-time only (NOT install — A7): install renders committed skills,
        it never samples. With no sampling host the verb returns the grounding +
        the prompt so a human/agent authors by hand (graceful degrade).

        Inputs: capability (a name in the live registry), skill_type (R15:
                pillar|capability|technique|pattern|reference|discipline),
                spec_text (optional governing-spec excerpt), max_tokens (sampling
                budget).
        Returns: ``{result: {status, ...}}`` where status is ``drafted`` (carries
                 a schema-valid ``draft``), ``no-host`` (carries ``grounding`` +
                 ``prompt`` for hand-authoring), ``unparseable`` (host output
                 failed JSON/schema — carries ``raw`` + ``error``), or ``error``
                 (unknown capability).
        chain_next: review the draft, then write ``skill.yaml`` + commit (Slice 3
                    adds registry validation + the ``source_stamp``).
        """
        try:
            cap = self.ctx.registry.get(capability)
        except KeyError:
            return {"result": {"status": "error",
                               "error": f"unknown capability {capability!r}",
                               "available": self.ctx.registry.names()}}
        grounding = build_grounding(cap, spec_text=spec_text)
        system, user = _skill_creator_prompt(skill_type, grounding)
        prompt = {"system": system, "user": user}
        host = self.ctx.host
        if not host.can_sample():
            return {"result": {"status": "no-host", "type": skill_type,
                               "grounding": grounding, "prompt": prompt}}
        from ..._host_bridge import HostUnavailable
        try:
            comp = host.sample(user, system=system, max_tokens=max_tokens)
        except HostUnavailable:
            return {"result": {"status": "no-host", "type": skill_type,
                               "grounding": grounding, "prompt": prompt}}
        draft, err = _parse_draft(getattr(comp, "text", "") or "")
        if err:
            return {"result": {"status": "unparseable", "type": skill_type,
                               "error": err, "raw": getattr(comp, "text", ""),
                               "prompt": prompt}}
        return {"result": {"status": "drafted", "type": skill_type, "draft": draft}}

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
