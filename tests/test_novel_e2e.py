"""Spec 108 Slice 1 — novel E2E provenance walk.

Drives the full novel-cluster pipeline on a fresh DB and asserts the
provenance chain captures every step. Per Spec 108 §"Done When":
"the 101 master row flips to Shipped once 108 ships Green".

Pipeline walked:
  capture_idea → promote_idea (Idea→Novel + PROMOTED_TO edge)
  → create_chapter (×N, CHAPTER_OF edge)
  → capture_claim (research, NovelClaim + SERVES)
  → count_words + check_filter_words (prose analysis on chapter body)
  → chapter_report (aggregate)
  → set_novel_status (drafting → revising)
  → render_manuscript (manuscript artefact)
  → pre_draft_gate (composite verb shipped here)

The assertion: every shipped verb leaves a SERVES Invocation edge to
the intent, so `memory.provenance(intent_id)` returns the complete
chain — the "release audit is one graph traversal" contract from CORE.md.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 108 e2e") -> str:
    iid = e.intent.capture(purpose, "novel pipeline", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


def test_pre_draft_gate_composes_storyform_research_chapters() -> None:
    """Spec 108 §"4 composite gate verbs" — pre_draft_gate composes
    storyform-presence + research-claims-present + chapter-outline.
    """
    e = _fresh()
    iid = _confirmed_iid(e)
    # Mint a Novel without any of the gate's prerequisites.
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    data, inv = _invoke(e, iid, "pre_draft_gate", novel_id=novel["novel_id"])
    assert data is None  # gate fails — no chapters, no research, no storyform
    err = e.memory.recall(inv).get("error", "")
    assert "GATE_FAILED" in err
    e.memory.close()


def test_pre_draft_gate_passes_with_all_prereqs() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    _invoke(e, iid, "create_chapter",
            novel_id=novel["novel_id"], number=1, title="A")
    _invoke(e, iid, "capture_claim",
            text="t", source_uri="u", domain="historical")
    # Storyform-presence: Slice 1 stub — a Storyform node on the novel.
    e.memory.record("Storyform", {"novel": novel["novel_id"]})
    data, _ = _invoke(e, iid, "pre_draft_gate", novel_id=novel["novel_id"])
    assert data is not None
    assert data["passed"] is True
    assert data["checks"] == {
        "chapter_outline": True, "research_present": True,
        "storyform_present": True,
    }
    e.memory.close()


def test_full_novel_pipeline_provenance_e2e() -> None:
    """The load-bearing E2E test — every shipped verb fires once, then
    `memory.provenance(intent_id)` returns the complete chain.

    Drives the pipeline that Spec 108's §"E2E test" enumerates:
    capture_idea → promote_idea → create_chapter (×3) → capture_claim
    → analyze prose → chapter_report → set_novel_status → render_manuscript
    → pre_draft_gate.
    """
    e = _fresh()
    iid = _confirmed_iid(e, "ship a novel end-to-end")
    # 1. Capture the idea
    idea, _ = _invoke(e, iid, "capture_idea",
                      text="A phreaker novel set in 1984 BBS culture")
    # 2. Promote to a Novel
    novel, _ = _invoke(e, iid, "promote_idea",
                       idea_id=idea["idea_id"],
                       title="Modem Daze", author="The Phreakers")
    nid = novel["novel_id"]
    # 3. Add 3 chapters
    for n, title, body in [
        (1, "Connection", "He really just wanted to dial in."),
        (2, "Discovery", "She found the file on the BBS."),
        (3, "Confrontation", "The sysop watched the logs."),
    ]:
        _invoke(e, iid, "create_chapter",
                novel_id=nid, number=n, title=title, body=body)
    # 4. Capture some research claims
    _invoke(e, iid, "capture_claim",
            text="In 1984 ~60K BBS nodes operated globally",
            source_uri="https://archive.org/x", domain="historical")
    _invoke(e, iid, "capture_claim",
            text="HST modems shipped at 9600 baud by 1984",
            source_uri="https://archive.org/y", domain="technological")
    # 5. Prose analysis on a chapter body
    wc, _ = _invoke(e, iid, "count_words",
                    body="He really just wanted to dial in.")
    assert wc["word_count"] == 7
    fw, _ = _invoke(e, iid, "check_filter_words",
                    body="He really just wanted to dial in.")
    assert fw["filter_count"] == 2  # really + just
    # 6. Aggregate report
    rep, _ = _invoke(e, iid, "chapter_report", novel_id=nid)
    assert rep["chapter_count"] == 3
    # 7. Status progression
    _invoke(e, iid, "set_novel_status",
            novel_id=nid, status="drafting")
    _invoke(e, iid, "set_novel_status",
            novel_id=nid, status="revising")
    # 8. Pre-draft gate (composite)
    e.memory.record("Storyform", {"novel": nid})
    gate_data, _ = _invoke(e, iid, "pre_draft_gate", novel_id=nid)
    assert gate_data["passed"] is True
    # 9. Render the manuscript
    ms, _ = _invoke(e, iid, "render_manuscript", novel_id=nid)
    assert ms["artefact"]["kind"] == "manuscript"
    assert ms["artefact"]["chapter_count"] == 3
    # Provenance: every step SERVES the intent. Audit is one traversal.
    prov = e.memory.provenance(iid)
    serves = prov.get("serves") or []
    verbs_fired = {s.get("verb") for s in serves}
    expected = {
        "capture_idea", "promote_idea", "create_chapter",
        "capture_claim", "count_words", "check_filter_words",
        "chapter_report", "set_novel_status", "pre_draft_gate",
        "render_manuscript",
    }
    missing = expected - verbs_fired
    assert not missing, f"verbs missing from provenance: {missing}"
    # Artefacts: manuscript MUST be in the provenance
    arts = prov.get("artefacts") or []
    art_kinds = {a.get("kind") for a in arts}
    assert "manuscript" in art_kinds, art_kinds
    e.memory.close()
