"""Novel cross-cap integration — 3 verbs that route through other capabilities.

Per the goal's tight-integration contract (Spec 114 verb-first routing):

- dispatch_novel_research(question, domain) → calls research.lead to mint
  a Research node; records NovelClaim with the new research_id; the
  novel cap delegates research orchestration to the research cap.
- render_chapter_brief(chapter_id, research_intent_id="") → chains
  prompt.brief_render over chapter context to produce a research-dossier
  artefact tied to the chapter.
- storyform_critical_pass(novel_id) → walks thinking.apply_full_review
  on the novel's storyform body (or premise as fallback); produces
  thinking-analysis artefact.

Each verb's invocation auto-records a SERVES edge from the called verb's
Invocation back to the same intent — the provenance moat that distinguishes
verb-first routing from raw cross-call.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "novel xcap integration") -> str:
    iid = e.intent.capture(purpose, "cross-cap", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, cap: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, cap, verb, **kw)


# ─────────────────────── registration ───────────────────────


def test_registers_three_xcap_verbs() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    expected = {"dispatch_novel_research",
                "render_chapter_brief",
                "storyform_critical_pass"}
    missing = expected - set(cap.verbs)
    assert not missing, f"missing: {missing}"
    e.memory.close()


# ─────────────────────── dispatch_novel_research ───────────────────────


def test_dispatch_novel_research_mints_research_node_via_research_cap() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "novel", "dispatch_novel_research",
                      question="Was the Stasi's HVA section active in 1987?",
                      domain="historical")
    assert data["research_id"].startswith("research:")
    # Research node minted on the substrate research cap (proves x-cap call).
    node = e.memory.recall(data["research_id"])
    assert node is not None
    # Both intents (this verb's serving + the inner research.lead call)
    # link back to the SAME iid via SERVES edges.
    rows = e.memory.g.query(
        "MATCH (i:Invocation)-[r:SERVES]->(t:Intent) WHERE t.id = $iid "
        "AND i.capability IN ['novel', 'research'] RETURN i.capability",
        {"iid": iid})
    caps = {r["i.capability"] for r in rows}
    assert {"novel", "research"} <= caps
    e.memory.close()


def test_dispatch_novel_research_rejects_invalid_domain() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "novel", "dispatch_novel_research",
                        question="x", domain="not-a-domain")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "INVALID_ARGUMENT" in err
    e.memory.close()


# ─────────────────────── render_chapter_brief ───────────────────────


def test_render_chapter_brief_produces_dossier_artefact() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    # Seed a novel + chapter
    novel, _ = _invoke(e, iid, "novel", "create_novel",
                       title="Test Novel", author="Tester")
    chap, _ = _invoke(e, iid, "novel", "create_chapter",
                      novel_id=novel["novel_id"], number=1,
                      title="Opening", body="The night was clear.")
    data, _ = _invoke(e, iid, "novel", "render_chapter_brief",
                      chapter_id=chap["chapter_id"])
    assert data["artefact"]["kind"] == "research-dossier"
    assert "Test Novel" in data["artefact"]["body"]
    assert "Opening" in data["artefact"]["body"]
    e.memory.close()


def test_render_chapter_brief_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "novel", "render_chapter_brief",
                        chapter_id="chapter:nope")
    assert data is None
    assert "NOT_FOUND" in e.memory.recall(inv).get("error", "")
    e.memory.close()


# ─────────────────────── storyform_critical_pass ───────────────────────


def test_storyform_critical_pass_produces_thinking_analysis_artefact() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "novel", "create_novel",
                       title="Test Novel", author="X")
    data, _ = _invoke(e, iid, "novel", "storyform_critical_pass",
                      novel_id=novel["novel_id"])
    # The thinking.apply_full_review artefact kind.
    assert data["artefact"]["kind"] == "thinking-analysis"
    # Proves the x-cap call: thinking cap invocation served the same intent.
    rows = e.memory.g.query(
        "MATCH (i:Invocation)-[r:SERVES]->(t:Intent) WHERE t.id = $iid "
        "AND i.capability = 'thinking' RETURN i.verb",
        {"iid": iid})
    assert rows  # thinking cap call recorded
    e.memory.close()


def test_storyform_critical_pass_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "novel", "storyform_critical_pass",
                        novel_id="novel:nope")
    assert data is None
    assert "NOT_FOUND" in e.memory.recall(inv).get("error", "")
    e.memory.close()
