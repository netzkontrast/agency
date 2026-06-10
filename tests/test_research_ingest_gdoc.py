"""Spec 126 — research.ingest_gdoc + research.record_ingested_source.

The verb itself does NO I/O; it composes a dispatch contract for the
orchestrator to hand to the Agent tool. A sibling verb records the
Artefact after the dispatched subagent returns metadata. The Google
Drive MCP call is structurally isolated to a subagent's throwaway
context, so the orchestrator's main context never sees a doc body.

Test plan:
  - URL/file_id resolution: docs.google.com, drive.google.com, bare id, invalid
  - Default dest path uses .agency/sources/gdoc-<id>.md
  - Dispatch contract carries the four named tools (+ no Read / no Grep)
  - Prompt forbids body echo and mandates structured JSON return
  - record_ingested_source emits Artefact + SERVES + PRODUCES edges
  - record_ingested_source is idempotent on (intent_id, sha256)
  - record_ingested_source rejects unknown intent_id
"""
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    return engine.intent.capture_and_confirm(
        "ingest gdoc sources",
        "research corpus on disk",
        "artefacts recorded under intent",
        owner="user",
    )


def _call(engine, iid, verb, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, "research", verb,
        agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# Verb registration.
# ---------------------------------------------------------------------------


def test_ingest_gdoc_verbs_registered(engine):
    verbs = set(engine.registry.get("research").verbs)
    assert {"ingest_gdoc", "record_ingested_source"} <= verbs


# ---------------------------------------------------------------------------
# Source resolution: URL forms → file_id.
# ---------------------------------------------------------------------------


_FID = "1AbCxyz_-fileid_BcD1234567890eFgH"   # realistic 33-char Drive file_id


def test_resolves_docs_url(engine, iid):
    r = _call(engine, iid, "ingest_gdoc",
              source=f"https://docs.google.com/document/d/{_FID}/edit")
    assert r["file_id"] == _FID


def test_resolves_drive_url(engine, iid):
    r = _call(engine, iid, "ingest_gdoc",
              source=f"https://drive.google.com/file/d/{_FID}/view")
    assert r["file_id"] == _FID


def test_resolves_bare_file_id(engine, iid):
    r = _call(engine, iid, "ingest_gdoc", source=_FID)
    assert r["file_id"] == _FID


def test_rejects_invalid_source(engine, iid):
    r = _call(engine, iid, "ingest_gdoc", source="not a url or id ☃")
    assert r["error"] == "INVALID_SOURCE"


# ---------------------------------------------------------------------------
# Default dest computation.
# ---------------------------------------------------------------------------


def test_default_dest_under_agency_sources(engine, iid):
    r = _call(engine, iid, "ingest_gdoc", source=_FID)
    assert r["dest"] == f".agency/sources/gdoc-{_FID}.md"


def test_explicit_dest_preserved(engine, iid):
    r = _call(engine, iid, "ingest_gdoc",
              source=_FID,
              dest=".agency/sources/research-brief.md")
    assert r["dest"] == ".agency/sources/research-brief.md"


# ---------------------------------------------------------------------------
# Dispatch contract shape.
# ---------------------------------------------------------------------------


def test_dispatch_contract_action(engine, iid):
    r = _call(engine, iid, "ingest_gdoc", source=_FID)
    assert r["action"] == "dispatch_subagent"


def test_dispatch_contract_tools_are_isolated(engine, iid):
    r = _call(engine, iid, "ingest_gdoc", source=_FID)
    tools = set(r["tools"])
    # The four named tools must be present.
    assert "mcp__Google_Drive__download_file_content" in tools
    assert "mcp__Google_Drive__get_file_metadata" in tools
    assert "Write" in tools
    assert "Bash" in tools
    # Read/Grep would let the subagent echo the body back — structurally forbidden.
    assert "Read" not in tools
    assert "Grep" not in tools


def test_dispatch_contract_prompt_forbids_body_echo(engine, iid):
    r = _call(engine, iid, "ingest_gdoc", source=_FID)
    prompt = r["prompt"]
    assert _FID in prompt
    # The prompt must explicitly forbid echoing the doc body and
    # mandate a single JSON line return.
    assert "do not echo" in prompt.lower() or "do not output the body" in prompt.lower()
    assert "json" in prompt.lower()
    assert "path" in prompt and "sha256" in prompt and "title" in prompt


def test_dispatch_contract_recommends_haiku(engine, iid):
    r = _call(engine, iid, "ingest_gdoc", source=_FID)
    assert r["model"] == "haiku"


def test_dispatch_contract_callback_kwargs(engine, iid):
    r = _call(engine, iid, "ingest_gdoc", source=_FID)
    cb = r["after"]
    assert cb["verb"] == "research.record_ingested_source"
    assert cb["kwargs"]["intent_id"] == iid
    assert _FID in cb["kwargs"]["source_url"]
    assert cb["kwargs"]["dest"] == f".agency/sources/gdoc-{_FID}.md"


# ---------------------------------------------------------------------------
# record_ingested_source — provenance.
# ---------------------------------------------------------------------------


_SHA = "abc123" * 10 + "abcd"   # 64 hex chars


def _record(engine, iid, **overrides):
    kw = dict(
        source_url="https://docs.google.com/document/d/1AbCxyz/edit",
        dest=".agency/sources/gdoc-1AbCxyz.md",
        bytes=12345,
        lines=420,
        sha256=_SHA,
        title="Research Brief: Nordic Folklore",
    )
    kw.update(overrides)
    return _call(engine, iid, "record_ingested_source", **kw)


def test_record_returns_artefact_id(engine, iid):
    r = _record(engine, iid)
    assert r.get("artefact_id")
    assert "error" not in r


def test_record_creates_artefact_node(engine, iid):
    r = _record(engine, iid)
    node = engine.memory.g.get_node(r["artefact_id"])
    assert node is not None
    props = node["properties"]
    assert props["kind"] == "ingested-source"
    assert props["path"] == ".agency/sources/gdoc-1AbCxyz.md"
    assert props["bytes"] == 12345
    assert props["lines"] == 420
    assert props["sha256"] == _SHA
    assert props["title"] == "Research Brief: Nordic Folklore"


def test_record_serves_intent(engine, iid):
    r = _record(engine, iid)
    rows = engine.memory.g.query(
        "MATCH (a:Artefact)-[:SERVES]->(i:Intent) "
        "WHERE a.id = $aid AND i.id = $iid RETURN a",
        {"aid": r["artefact_id"], "iid": iid})
    assert len(rows) == 1


def test_record_emits_produces_edge(engine, iid):
    r = _record(engine, iid)
    rows = engine.memory.g.query(
        "MATCH (i:Intent)-[:PRODUCES]->(a:Artefact) "
        "WHERE a.id = $aid AND i.id = $iid RETURN a",
        {"aid": r["artefact_id"], "iid": iid})
    assert len(rows) == 1


def test_record_idempotent_on_sha(engine, iid):
    r1 = _record(engine, iid)
    r2 = _record(engine, iid)
    assert r1["artefact_id"] == r2["artefact_id"]


def test_record_distinct_sha_distinct_artefact(engine, iid):
    r1 = _record(engine, iid)
    r2 = _record(engine, iid, sha256="ffffff" * 10 + "ffff")
    assert r1["artefact_id"] != r2["artefact_id"]


# Unknown-intent rejection is handled by the registry at invoke time
# (capability.py:579-586); the verb itself doesn't need a defensive
# guard — the path to it is gated.
