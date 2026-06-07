"""Spec 083 — the boundary to the Anthropic Skills API (`/v1/skills`).

Lazy, like `JulesClient`: needs the `anthropic` SDK (`pip install -e .[publish]`) +
`ANTHROPIC_API_KEY`, and raises a clear error AT CALL TIME when absent — so the
default never imports `anthropic` and `plugin.publish_skill(dry_run=True)` works
offline. Tests inject a stub; the real upload path is opt-in (`dry_run=False`).

The wire binding is VERIFIED against anthropic SDK 0.107.0 (`tests/test_skills_api_binding.py`
re-checks it whenever the SDK is importable): `beta.skills.create` takes
``display_title`` + ``files`` (a LIST of uploads, SKILL.md at the root — NOT a zip) and
returns ``.id`` + ``.latest_version``; ``beta.skills.versions.create`` takes ``skill_id``
+ ``files`` and returns ``.version``.
"""
from __future__ import annotations

import os


def _uploads(files: dict) -> list[tuple[str, bytes]]:
    """Turn a ``{path: content}`` package into the SDK's ``files`` upload list —
    ``(filename, content_bytes)`` tuples (FileTypes), preserving the relative path as
    the filename so ``references/…`` lands under the skill's top-level directory."""
    return [(path, content.encode() if isinstance(content, str) else content)
            for path, content in files.items()]


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
        uploads = _uploads(files)
        if existing_id:                                  # pragma: no cover - needs a key
            v = client.beta.skills.versions.create(skill_id=existing_id, files=uploads)
            return {"skill_id": existing_id, "version": str(getattr(v, "version", "?"))}
        s = client.beta.skills.create(display_title=name, files=uploads)   # pragma: no cover
        return {"skill_id": s.id, "version": str(s.latest_version or "1")}
