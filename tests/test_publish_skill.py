"""Spec 083 — plugin.publish_skill packages + uploads a capability's Agent Skill."""
import tempfile

import pytest

from agency.engine import Engine


class _StubSkills:
    """Stub Skills API client — records uploads, never hits the network."""
    def __init__(self):
        self.calls = []

    def publish(self, name, files, existing_id=None):
        self.calls.append((name, dict(files), existing_id))
        return {"skill_id": "skill_stub123", "version": "1"}


@pytest.fixture
def engine():
    e = Engine(tempfile.mktemp(suffix=".db"), skills_client=_StubSkills())
    try:
        yield e
    finally:
        e.memory.close()


@pytest.fixture
def iid(engine):
    i = engine.intent.capture("publish", "upload shell's Agent Skill", "manifest + provenance")
    engine.intent.confirm(i)
    return i


def _call(e, iid, cap, verb, **kw):
    res, _ = e.registry.invoke(e.memory, iid, cap, verb, **kw)
    return res["result"] if isinstance(res, dict) and "result" in res else res


def test_dry_run_returns_manifest_without_uploading(engine, iid):
    out = _call(engine, iid, "plugin", "publish_skill", name="shell")  # dry_run default
    assert out["uploaded"] is False
    assert "SKILL.md" in out["files"]                       # SKILL.md at package root
    assert any(f.startswith("references/") for f in out["files"])
    assert out["bytes"] > 0
    assert engine.skills_client.calls == []                 # nothing uploaded


def test_upload_packages_and_records_provenance(engine, iid):
    out = _call(engine, iid, "plugin", "publish_skill", name="shell", dry_run=False)
    assert out["uploaded"] is True and out["skill_id"] == "skill_stub123"
    name, files, _ = engine.skills_client.calls[0]
    assert name == "shell" and "SKILL.md" in files          # root-level SKILL.md uploaded
    # a published-skill Artefact serves the intent
    arts = engine.memory.find("Artefact")
    assert any(a.get("kind") == "published-skill" and a.get("skill_id") == "skill_stub123"
               for a in arts)


def test_underscore_capability_publishes_a_spec_legal_name(engine, iid):
    out = _call(engine, iid, "plugin", "publish_skill", name="skill_generator", dry_run=False)
    assert out["uploaded"] is True
    assert engine.skills_client.calls[0][0] == "skill-generator"   # hyphenated (Agent Skills spec)


def test_unknown_capability_errors_cleanly(engine, iid):
    out = _call(engine, iid, "plugin", "publish_skill", name="no-such-cap")
    assert out.get("error")
    assert engine.skills_client.calls == []
