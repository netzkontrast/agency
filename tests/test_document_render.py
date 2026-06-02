"""Spec 043 — document.render: 4 graph→markdown scopes.

Each scope has a fixed output schema (Wiegers — contract-pinned, not
vibes). Tests verify the schema's structural markers + token counts.
"""
import tempfile

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    i = engine.intent.capture(
        "test document.render",
        "rendered markdown matches schema",
        "tokens count is non-zero for non-empty content",
    )
    engine.intent.confirm(i)
    return i


def _call(engine, iid, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, "document", "render",
        agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# install-artefacts scope
# ---------------------------------------------------------------------------


def test_render_install_artefacts(engine, iid):
    # Seed two install-artefact Reflections.
    engine.registry.invoke(engine.memory, iid, "reflect", "note",
                           agent_id="agent:t", scope="technical",
                           text="ignored")
    # Direct memory.record for the kind=install-artefact ones (the
    # reflect.note verb doesn't take a `kind` param in v1).
    a1 = engine.memory.record("Reflection", {
        "scope": "technical", "kind": "install-artefact",
        "name": "plugin.json", "body": '{"name": "agency"}',
        "text": "rendered into plugin.json on install"})
    a2 = engine.memory.record("Reflection", {
        "scope": "technical", "kind": "install-artefact",
        "name": ".mcp.json", "body": '{"servers": {}}',
        "text": "rendered into .mcp.json on install"})
    r = _call(engine, iid, scope="install-artefacts")
    assert r["scope"] == "install-artefacts"
    assert r["node_count"] == 2
    # Schema: H1 + one H2 per artefact (sorted by name).
    assert r["content"].startswith("# Install artefacts\n")
    assert "## .mcp.json\n" in r["content"]
    assert "## plugin.json\n" in r["content"]
    # .mcp.json comes BEFORE plugin.json (alphabetical).
    assert r["content"].index("## .mcp.json") < r["content"].index("## plugin.json")
    # Body fenced.
    assert "```\n" in r["content"]
    assert r["tokens"] > 0


def test_render_install_artefacts_empty(engine, iid):
    r = _call(engine, iid, scope="install-artefacts")
    assert r["node_count"] == 0
    assert r["content"].startswith("# Install artefacts\n")


# ---------------------------------------------------------------------------
# reflections scope
# ---------------------------------------------------------------------------


def test_render_reflections_newest_first(engine, iid):
    for txt in ("first thing", "second thing", "third thing"):
        engine.registry.invoke(engine.memory, iid, "reflect", "note",
                               agent_id="agent:t", scope="technical", text=txt)
    r = _call(engine, iid, scope="reflections")
    assert r["node_count"] == 3
    assert "# Reflections (intent=all)\n" in r["content"]
    # Newest (third) appears BEFORE earliest (first).
    assert r["content"].index("third thing") < r["content"].index("first thing")


def test_render_reflections_intent_scoped_filter(engine, iid):
    """Code-review F1 regression: filtering by intent must traverse
    the OBSERVED_DURING edge — Reflection nodes don't carry intent_id
    as a property, so a property-based filter would silently match
    nothing (the original implementation's bug).
    """
    # Note a Reflection under THIS intent.
    engine.registry.invoke(engine.memory, iid, "reflect", "note",
                           agent_id="agent:t", scope="technical",
                           text="under this intent")
    # Mint a SECOND intent and note a Reflection under it.
    other = engine.intent.capture("other", "x", "x")
    engine.intent.confirm(other)
    engine.registry.invoke(engine.memory, other, "reflect", "note",
                           agent_id="agent:t", scope="technical",
                           text="under other intent")
    # Render scoped to the first intent.
    r = _call(engine, iid, scope="reflections", for_intent_id=iid)
    assert "under this intent" in r["content"]
    assert "under other intent" not in r["content"]


def test_render_reflections_text_truncated_to_500(engine, iid):
    long = "x" * 1000
    engine.registry.invoke(engine.memory, iid, "reflect", "note",
                           agent_id="agent:t", scope="technical", text=long)
    r = _call(engine, iid, scope="reflections")
    # Truncation marker appears.
    assert "…" in r["content"] or "x" * 500 in r["content"]
    # And the body is NOT 1000 chars.
    assert "x" * 600 not in r["content"]


# ---------------------------------------------------------------------------
# provenance scope
# ---------------------------------------------------------------------------


def test_render_provenance(engine, iid):
    r = _call(engine, iid, scope="provenance", for_intent_id=iid)
    assert r["scope"] == "provenance"
    assert f"# Intent {iid} provenance\n" in r["content"]
    assert "## Acceptance" in r["content"]
    assert "## Invocations" in r["content"]
    assert "## Artefacts" in r["content"]


def test_render_provenance_no_intent_id(engine, iid):
    r = _call(engine, iid, scope="provenance", for_intent_id="")
    assert "# Intent (none) provenance" in r["content"]


# ---------------------------------------------------------------------------
# capability-catalogue scope
# ---------------------------------------------------------------------------


def test_render_capability_catalogue(engine, iid):
    r = _call(engine, iid, scope="capability-catalogue")
    assert r["scope"] == "capability-catalogue"
    assert r["content"].startswith("# Capability catalogue\n")
    # Each capability gets an H2.
    assert "## reflect" in r["content"]
    assert "## delegate" in r["content"]
    assert "## document" in r["content"]
    # Footer counts.
    assert "capabilities" in r["content"]
    assert "verbs" in r["content"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_unknown_scope_returns_error(engine, iid):
    r = _call(engine, iid, scope="no-such-scope")
    assert "error" in r
    assert r["content"] == ""


def test_unsupported_format_returns_error(engine, iid):
    r = _call(engine, iid, scope="reflections", format="html")
    assert "error" in r


def test_render_is_pure_no_graph_writes(engine, iid):
    """render is a transform — calling it must not change the node count."""
    before = len(list(engine.memory.find("Reflection")))
    _call(engine, iid, scope="capability-catalogue")
    after = len(list(engine.memory.find("Reflection")))
    assert before == after
