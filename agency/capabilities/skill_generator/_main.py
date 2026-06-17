# agency-scaffold: v1
"""skill_generator — generate a deploy-ready skill in one call.

Skill_generator produces a deploy-ready skill in a single call, emitting a CSO-clean SKILL.md from a name and description.

Use when: a deploy-ready skill should be produced in one call — a complete, CSO-clean SKILL.md generated from a description.
Triggers:
- A new skill needed without hand-assembling its files
- A skill idea that should become a deployable artefact
"""
from __future__ import annotations

from ...capability import CapabilityBase, verb




class SkillGeneratorCapability(CapabilityBase):
    name = "skill_generator"
    home = "capability"

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
