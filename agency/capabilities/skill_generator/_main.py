"""skill_generator — generate a deploy-ready skill in one call.

A composition capability: it doesn't reimplement skill authoring, it COMPOSES the
existing `plugin` verbs via `ctx.call` — author the SKILL.md, then validate it
against the CSO rules — and reports whether the result is deploy-ready. A clean
demonstration of capability→capability composition (every delegated call is
recorded as an Invocation that SERVES the intent).
"""
from __future__ import annotations

from ...capability import CapabilityBase, verb


class SkillGeneratorCapability(CapabilityBase):
    name = "skill_generator"
    home = "capability"

    @verb(role="act")
    def generate(self, name: str, description: str, body: str) -> dict:
        """Author a SKILL.md and lint it against the CSO rules; flag if not deploy-ready.

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
