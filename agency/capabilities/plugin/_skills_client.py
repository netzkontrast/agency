"""Spec 083 — the boundary to the Anthropic Skills API (`/v1/skills`).

Lazy, like `JulesClient`: needs the `anthropic` SDK (`pip install -e .[publish]`) +
`ANTHROPIC_API_KEY`, and raises a clear error AT CALL TIME when absent — so the
default never imports `anthropic` and `plugin.publish_skill(dry_run=True)` works
offline. Tests inject a stub; the real upload path is opt-in (`dry_run=False`).
"""
from __future__ import annotations

import io
import os
import zipfile


class SkillsClient:
    def publish(self, name: str, files: dict, existing_id: str | None = None) -> dict:
        """Upload a skill package (``{path: content}``, SKILL.md at root) as a new
        skill or a new version of ``existing_id``. Returns ``{skill_id, version}``."""
        try:
            import anthropic
        except ImportError as exc:                       # pragma: no cover - env-gated
            raise RuntimeError(
                "Skills API needs the anthropic SDK — `pip install -e .[publish]`"
            ) from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):      # pragma: no cover - env-gated
            raise RuntimeError("Skills API needs ANTHROPIC_API_KEY")
        client = anthropic.Anthropic()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, content in files.items():
                zf.writestr(path, content)
        buf.seek(0)
        # NOTE: the exact `client.beta.skills` binding (zip field name, headers) is
        # verified against the live SDK at first real publish; the package shape
        # (SKILL.md at root + references/) follows the Agent Skills spec.
        if existing_id:                                  # pragma: no cover - env-gated
            v = client.beta.skills.versions.create(skill_id=existing_id, file=buf)
            return {"skill_id": existing_id, "version": str(getattr(v, "version", "?"))}
        s = client.beta.skills.create(display_title=name, file=buf)   # pragma: no cover
        return {"skill_id": s.id, "version": str(getattr(s, "version", "1"))}
