"""Spec 108 Slice 2 — 3 more composite gates (beta-ready / query-ready / publish-ready).

Continues Spec 108 Slice 1 (pre_draft_gate) with the rest of the
publication-lifecycle gate stack:

- beta_ready_gate(novel_id) — all chapters drafted, no draft-status
  chapters remaining; manuscript renderable.
- query_ready_gate(novel_id) — novel status reaches "querying"
  prerequisites; render_blurb + render_query_letter available;
  content warnings scanned.
- publish_ready_gate(novel_id) — manuscript_coherence_check passes
  (no chapter gaps); novel status set to "published"-ready.

All gates compose verbs already shipped across Slices 1-2 of 101-107.
No new drivers; pure cross-verb composition.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 108 slice 2") -> str:
    iid = e.intent.capture(purpose, "gates", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


def _seed_novel_with_chapters(e: Engine, iid: str, n_chapters: int = 3,
                                 body: str = "draft body content"):
    novel, _ = _invoke(e, iid, "create_novel",
                       title="Test Novel", author="Tester")
    nid = novel["novel_id"]
    chapter_ids = []
    for i in range(1, n_chapters + 1):
        c, _ = _invoke(e, iid, "create_chapter",
                       novel_id=nid, number=i,
                       title=f"Chapter {i}", body=body)
        chapter_ids.append(c["chapter_id"])
    return nid, chapter_ids


# ─────────────────────── registration ───────────────────────


def test_slice2_registers_three_more_gates() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    expected = {"beta_ready_gate", "query_ready_gate", "publish_ready_gate"}
    missing = expected - set(cap.verbs)
    assert not missing, f"missing: {missing}"
    e.memory.close()


# ─────────────────────── beta_ready_gate ───────────────────────


def test_beta_ready_gate_blocks_when_no_chapters_drafted() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    nid, _ = _seed_novel_with_chapters(e, iid)
    # All chapters still status="outlined"
    data, inv = _invoke(e, iid, "beta_ready_gate", novel_id=nid)
    assert data is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_beta_ready_gate_passes_when_all_chapters_drafted() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    nid, cids = _seed_novel_with_chapters(e, iid)
    for cid in cids:
        _invoke(e, iid, "set_chapter_status",
                chapter_id=cid, status="drafted")
    data, _ = _invoke(e, iid, "beta_ready_gate", novel_id=nid)
    assert data["passed"] is True
    assert data["checks"]["all_chapters_drafted"] is True
    e.memory.close()


def test_beta_ready_gate_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "beta_ready_gate", novel_id="novel:nope")
    assert data is None
    assert "NOT_FOUND" in e.memory.recall(inv).get("error", "")
    e.memory.close()


# ─────────────────────── query_ready_gate ───────────────────────


def test_query_ready_gate_blocks_when_status_not_beta() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    nid, cids = _seed_novel_with_chapters(e, iid)
    # status still concept; not beta-or-later
    data, inv = _invoke(e, iid, "query_ready_gate", novel_id=nid)
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "GATE_FAILED" in err
    e.memory.close()


def test_query_ready_gate_passes_at_beta_with_clean_content() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    nid, cids = _seed_novel_with_chapters(
        e, iid, body="The morning was clear. Birds sang.")
    for cid in cids:
        _invoke(e, iid, "set_chapter_status",
                chapter_id=cid, status="revised")
    _invoke(e, iid, "set_novel_status", novel_id=nid, status="beta")
    data, _ = _invoke(e, iid, "query_ready_gate", novel_id=nid)
    assert data["passed"] is True
    assert "status_beta_or_later" in data["checks"]
    e.memory.close()


# ─────────────────────── publish_ready_gate ───────────────────────


def test_publish_ready_gate_blocks_on_chapter_gaps() -> None:
    """publish_ready_gate composes manuscript_coherence_check; chapter
    sequence with a gap (1, 3 — missing 2) blocks."""
    e = _fresh()
    iid = _confirmed_iid(e)
    novel, _ = _invoke(e, iid, "create_novel", title="X", author="Y")
    nid = novel["novel_id"]
    _invoke(e, iid, "create_chapter", novel_id=nid,
            number=1, title="A", body="body")
    _invoke(e, iid, "create_chapter", novel_id=nid,
            number=3, title="C", body="body")
    _invoke(e, iid, "set_novel_status", novel_id=nid, status="querying")
    data, inv = _invoke(e, iid, "publish_ready_gate", novel_id=nid)
    assert data is None
    assert "GATE_FAILED" in e.memory.recall(inv).get("error", "")
    e.memory.close()


def test_publish_ready_gate_passes_contiguous_at_querying() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    nid, cids = _seed_novel_with_chapters(e, iid, n_chapters=3)
    for cid in cids:
        _invoke(e, iid, "set_chapter_status",
                chapter_id=cid, status="final")
    _invoke(e, iid, "set_novel_status", novel_id=nid, status="querying")
    data, _ = _invoke(e, iid, "publish_ready_gate", novel_id=nid)
    assert data["passed"] is True
    assert data["checks"]["status_at_querying_or_later"] is True
    e.memory.close()


def test_publish_ready_gate_not_found() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "publish_ready_gate", novel_id="novel:nope")
    assert data is None
    assert "NOT_FOUND" in e.memory.recall(inv).get("error", "")
    e.memory.close()
