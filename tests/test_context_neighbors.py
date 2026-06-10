"""Spec 125 — CapabilityContext.neighbors(node_id, edge, direction).

One-hop edge traversal on the substrate context. Closes the deferred F4
advisory: domain caps declared CHAPTER_OF / SCENE_OF / etc. edges but the
verbs fall back to full-label `find()`+filter scans because the substrate
exposes no traversal shorthand.

Test plan:
  - neighbors returns property dicts (same shape as find())
  - direction="in" finds nodes pointing AT the target id
  - direction="out" finds nodes the source points at
  - empty result when no matching edges
  - unknown node id → []
  - default direction is "in"
  - novel call-site behavior parity: CHAPTER_OF returns the same chapters
    that find("Chapter")+filter produces
  - limit kwarg caps the row count
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
        "test neighbors substrate",
        "ctx.neighbors traverses one edge",
        "matches find()+filter shape",
        owner="user",
    )


def _call(engine, iid, cap, verb, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, cap, verb,
        agent_id="agent:test", **kw)
    return r


# ---------------------------------------------------------------------------
# Substrate shape.
# ---------------------------------------------------------------------------


def test_neighbors_method_exists():
    from agency.capability import CapabilityContext
    assert hasattr(CapabilityContext, "neighbors")


def test_neighbors_returns_property_dicts(engine, iid):
    novel_id = _call(engine, iid, "novel", "create_novel",
                     title="Test Novel", author="A.N. Author")["novel_id"]
    ch1 = _call(engine, iid, "novel", "create_chapter",
                novel_id=novel_id, number=1, title="Ch 1")["chapter_id"]
    ch2 = _call(engine, iid, "novel", "create_chapter",
                novel_id=novel_id, number=2, title="Ch 2")["chapter_id"]

    # Reach into the registry to get a context for a probe.
    from agency.capability import CapabilityContext
    ctx = CapabilityContext(
        memory=engine.memory, ontology=engine.registry.ontology,
        registry=engine.registry, intent_id=iid, agent_id="agent:test",
        client=None, depth=0, engine=engine, drivers=None)

    chapters = ctx.neighbors(novel_id, "CHAPTER_OF", direction="in")
    assert isinstance(chapters, list)
    assert len(chapters) == 2
    # Each is a property dict (same shape as find()).
    ids = {c["id"] for c in chapters}
    assert ids == {ch1, ch2}


def test_neighbors_direction_in_is_default(engine, iid):
    novel_id = _call(engine, iid, "novel", "create_novel",
                     title="Default Dir", author="A")["novel_id"]
    ch1 = _call(engine, iid, "novel", "create_chapter",
                novel_id=novel_id, number=1, title="Ch 1")["chapter_id"]

    from agency.capability import CapabilityContext
    ctx = CapabilityContext(
        memory=engine.memory, ontology=engine.registry.ontology,
        registry=engine.registry, intent_id=iid, agent_id="agent:test",
        client=None, depth=0, engine=engine, drivers=None)

    explicit = ctx.neighbors(novel_id, "CHAPTER_OF", direction="in")
    default = ctx.neighbors(novel_id, "CHAPTER_OF")
    assert {c["id"] for c in explicit} == {c["id"] for c in default} == {ch1}


def test_neighbors_direction_out(engine, iid):
    novel_id = _call(engine, iid, "novel", "create_novel",
                     title="Outbound", author="A")["novel_id"]
    ch1 = _call(engine, iid, "novel", "create_chapter",
                novel_id=novel_id, number=1, title="Ch 1")["chapter_id"]

    from agency.capability import CapabilityContext
    ctx = CapabilityContext(
        memory=engine.memory, ontology=engine.registry.ontology,
        registry=engine.registry, intent_id=iid, agent_id="agent:test",
        client=None, depth=0, engine=engine, drivers=None)

    # CHAPTER_OF goes Chapter -> Novel, so the OUT direction from a chapter
    # finds the parent novel.
    novels = ctx.neighbors(ch1, "CHAPTER_OF", direction="out")
    assert len(novels) == 1
    assert novels[0]["id"] == novel_id


def test_neighbors_no_match_returns_empty(engine, iid):
    novel_id = _call(engine, iid, "novel", "create_novel",
                     title="Empty", author="A")["novel_id"]

    from agency.capability import CapabilityContext
    ctx = CapabilityContext(
        memory=engine.memory, ontology=engine.registry.ontology,
        registry=engine.registry, intent_id=iid, agent_id="agent:test",
        client=None, depth=0, engine=engine, drivers=None)

    assert ctx.neighbors(novel_id, "CHAPTER_OF") == []


def test_neighbors_unknown_id_returns_empty(engine, iid):
    from agency.capability import CapabilityContext
    ctx = CapabilityContext(
        memory=engine.memory, ontology=engine.registry.ontology,
        registry=engine.registry, intent_id=iid, agent_id="agent:test",
        client=None, depth=0, engine=engine, drivers=None)
    assert ctx.neighbors("novel:does-not-exist", "CHAPTER_OF") == []


def test_neighbors_invalid_direction_raises(engine, iid):
    from agency.capability import CapabilityContext
    ctx = CapabilityContext(
        memory=engine.memory, ontology=engine.registry.ontology,
        registry=engine.registry, intent_id=iid, agent_id="agent:test",
        client=None, depth=0, engine=engine, drivers=None)
    with pytest.raises(ValueError):
        ctx.neighbors("anything", "CHAPTER_OF", direction="sideways")


def test_neighbors_limit_caps_rows(engine, iid):
    novel_id = _call(engine, iid, "novel", "create_novel",
                     title="Many Chapters", author="A")["novel_id"]
    for n in range(1, 8):
        _call(engine, iid, "novel", "create_chapter",
              novel_id=novel_id, number=n, title=f"Ch {n}")

    from agency.capability import CapabilityContext
    ctx = CapabilityContext(
        memory=engine.memory, ontology=engine.registry.ontology,
        registry=engine.registry, intent_id=iid, agent_id="agent:test",
        client=None, depth=0, engine=engine, drivers=None)

    all_ch = ctx.neighbors(novel_id, "CHAPTER_OF")
    assert len(all_ch) == 7
    capped = ctx.neighbors(novel_id, "CHAPTER_OF", limit=3)
    assert len(capped) == 3


# ---------------------------------------------------------------------------
# Behaviour parity: neighbors() must match the find()+filter scan it replaces.
# ---------------------------------------------------------------------------


def test_neighbors_parity_with_find_filter(engine, iid):
    """The replaced pattern was:
       [c for c in ctx.find("Chapter") if c.get("novel") == novel_id]
    neighbors(novel_id, "CHAPTER_OF") must return the same set.
    """
    novel_id = _call(engine, iid, "novel", "create_novel",
                     title="Parity", author="A")["novel_id"]
    other_id = _call(engine, iid, "novel", "create_novel",
                     title="Other", author="B")["novel_id"]
    for n in range(1, 4):
        _call(engine, iid, "novel", "create_chapter",
              novel_id=novel_id, number=n, title=f"Ch {n}")
    # And one chapter under the other novel — must NOT leak.
    _call(engine, iid, "novel", "create_chapter",
          novel_id=other_id, number=1, title="Other Ch 1")

    from agency.capability import CapabilityContext
    ctx = CapabilityContext(
        memory=engine.memory, ontology=engine.registry.ontology,
        registry=engine.registry, intent_id=iid, agent_id="agent:test",
        client=None, depth=0, engine=engine, drivers=None)

    via_neighbors = sorted(c["id"] for c in
                           ctx.neighbors(novel_id, "CHAPTER_OF"))
    via_scan = sorted(c["id"] for c in ctx.find("Chapter")
                      if c.get("novel") == novel_id)
    assert via_neighbors == via_scan
    assert len(via_neighbors) == 3
