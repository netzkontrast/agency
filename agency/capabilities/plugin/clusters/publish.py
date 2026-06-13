"""Publish cluster — uploads a capability's Agent Skill to the Skills API.

Single verb (`publish_skill`), an effect with `skills_client` injected.
Behaviour verbatim from the pre-split `plugin._main`.
"""
from __future__ import annotations

from ....capability import CapabilityBase, verb


class PublishMixin(CapabilityBase):
    """Verb that PUBLISHES a capability's emitted Agent Skill (Spec 083)."""

    @verb(role="effect", inject=["skills_client"])
    def publish_skill(self, skills_client, name: str, dry_run: bool = True) -> dict:
        """Publish a capability's Agent Skill to the Anthropic Skills API (Spec 083).

        Packages the capability's emitted skill (SKILL.md at root + references/) and,
        unless ``dry_run``, uploads it via /v1/skills — so the capability becomes a
        first-class Agent Skill on ANY Claude surface (API, Managed Agents, claude.ai),
        not just Claude Code. The upload is recorded as a `published-skill` Artefact.

        Inputs: cap_name (capability to publish); dry_run (True → return the package
                manifest WITHOUT uploading — the safe default; set False to publish).
        Returns: ``{skill_name, files:[…], bytes, uploaded, skill_id?, version?}``.
        chain_next: re-run with dry_run=False to upload; re-publish makes a new version.
        """
        from ....skill_emit import emit_skill, emit_references, _skill_name
        try:
            cap = self.ctx.registry.get(name)
        except KeyError:
            return {"error": f"unknown capability {name!r}"}
        if getattr(cap, "skill_doc", None) is None:
            return {"error": f"capability {name!r} has no skill_doc to publish"}
        files: dict = {}
        files.update(emit_skill(cap.name, cap.skill_doc, cap.verbs,
                                getattr(cap.ontology, "skills", None)))
        files.update(emit_references(cap.name, cap.verbs))
        prefix = f"skills/{_skill_name(cap.name)}/"
        pkg = {p[len(prefix):]: c for p, c in files.items() if p.startswith(prefix)}
        skill_name = _skill_name(cap.name)
        out = {"skill_name": skill_name, "files": sorted(pkg),
               "bytes": sum(len(c) for c in pkg.values()), "uploaded": False}
        if dry_run:
            return out
        res = skills_client.publish(skill_name, pkg)
        aid = self.ctx.record("Artefact", {"kind": "published-skill", "name": skill_name,
                                           "skill_id": res.get("skill_id", ""),
                                           "version": res.get("version", "")})
        self.ctx.link(aid, self.ctx.intent_id, "SERVES")
        self.ctx.link(aid, self.ctx.intent_id, "OBSERVED_DURING")
        out.update({"uploaded": True, "skill_id": res.get("skill_id"),
                    "version": res.get("version"), "artefact_id": aid})
        return out
