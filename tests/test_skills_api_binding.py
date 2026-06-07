"""Prove-what-shipped — verify the live Skills API + count_tokens bindings against
the real anthropic SDK.

The `# pragma: no cover` upload path in `_skills_client.py` was a GUESS (it used a zip
`file=`; the real API takes a `files` LIST with SKILL.md at root). These tests re-check
the binding against the installed SDK so a future SDK change that breaks our boundary
fails loudly. They `importorskip("anthropic")` — CI installs only `[dev]` (no SDK) and
skips them; they run wherever `[publish]`/`[tokens]` is installed.
"""
import inspect

import pytest

from agency.capabilities.plugin._skills_client import _uploads


def test_uploads_builds_filename_content_tuples():
    # pure helper — always runs, no SDK needed
    ups = dict(_uploads({"SKILL.md": "hi", "references/find.md": b"raw"}))
    assert ups["SKILL.md"] == b"hi"                     # str → bytes
    assert ups["references/find.md"] == b"raw"          # bytes pass through, path preserved


def _params(fn) -> set:
    return set(inspect.signature(fn).parameters)


def test_skills_create_binding_matches_skills_client():
    anthropic = pytest.importorskip("anthropic")
    c = anthropic.Anthropic(api_key="x")
    assert {"display_title", "files"} <= _params(c.beta.skills.create)
    from anthropic.types.beta.skill_create_response import SkillCreateResponse
    assert {"id", "latest_version"} <= set(SkillCreateResponse.model_fields)


def test_versions_create_binding_matches_skills_client():
    anthropic = pytest.importorskip("anthropic")
    c = anthropic.Anthropic(api_key="x")
    assert {"skill_id", "files"} <= _params(c.beta.skills.versions.create)
    from anthropic.types.beta.skills.version_create_response import VersionCreateResponse
    assert "version" in VersionCreateResponse.model_fields


def test_count_tokens_binding_matches_token_counter():
    anthropic = pytest.importorskip("anthropic")
    c = anthropic.Anthropic(api_key="x")
    assert {"model", "messages"} <= _params(c.messages.count_tokens)
    from anthropic.types import MessageTokensCount
    assert "input_tokens" in MessageTokensCount.model_fields
