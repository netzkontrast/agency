"""Spec 104 Slice 2 — 4 more deterministic prose-analysis verbs.

Continues Spec 104 Slice 1 (count_words, analyze_readability,
check_filter_words) with 4 more driver-free analysis verbs honoring
the Slice-1 pattern: deterministic, body-only inputs, ToolResult
output with `passed`/payload.

- scan_proper_nouns(body) — regex over Title-Case words; returns
  sorted unique list. For continuity / world-bible cross-reference.
- check_dialogue_attribution(body) — counts plain `said`/`asked`
  attributions vs flowery alternatives (`exclaimed`, `muttered`,
  `ejaculated`). Editorial best-practice: invisible attributions
  preferred.
- check_show_dont_tell(body) — count telling verbs (feel/felt/
  realize/notice/wonder). Independent from check_filter_words
  (which checks adverbs); these flag interior-monologue tells.
- check_content_warnings(body) — scan for canonical content-warning
  topics (violence/sex/substance/death/etc.) against a documented
  set. Returns matched categories.
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 104 slice 2") -> str:
    iid = e.intent.capture(purpose, "prose checks", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


# ─────────────────────── registration ───────────────────────


def test_slice2_registers_four_prose_verbs() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    expected = {"scan_proper_nouns", "check_dialogue_attribution",
                "check_show_dont_tell", "check_content_warnings"}
    missing = expected - set(cap.verbs)
    assert not missing, f"missing: {missing}"
    e.memory.close()


# ─────────────────────── scan_proper_nouns ───────────────────────


def test_scan_proper_nouns_returns_sorted_unique() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    body = "Alice met Bob at the diner. Then Charlie arrived. Alice waved."
    data, _ = _invoke(e, iid, "scan_proper_nouns", body=body)
    assert data["proper_nouns"] == ["Alice", "Bob", "Charlie"]
    assert data["count"] == 3
    e.memory.close()


def test_scan_proper_nouns_skips_sentence_initial_lower_case_no_false_positives() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    body = "The morning was clear. She walked to the park. Then George arrived."
    data, _ = _invoke(e, iid, "scan_proper_nouns", body=body)
    # The/She/Then are sentence-initial — must NOT count.
    assert data["proper_nouns"] == ["George"]
    e.memory.close()


def test_scan_proper_nouns_empty_body() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "scan_proper_nouns", body="")
    assert data["proper_nouns"] == []
    assert data["count"] == 0
    e.memory.close()


# ─────────────────────── check_dialogue_attribution ───────────────────────


def test_check_dialogue_attribution_clean_passes() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    body = '"Hi," she said. "Are you ready?" he asked. "Yes," she said.'
    data, _ = _invoke(e, iid, "check_dialogue_attribution", body=body)
    assert data["passed"] is True
    assert data["flowery_count"] == 0
    assert data["plain_count"] == 3
    e.memory.close()


def test_check_dialogue_attribution_flowery_flagged() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    body = ('"Watch out!" he exclaimed. "I see it," she muttered. '
            '"Of course," he ejaculated.')
    data, _ = _invoke(e, iid, "check_dialogue_attribution", body=body)
    assert data["passed"] is False
    assert data["flowery_count"] == 3
    assert "exclaimed" in data["flowery_hits"]
    e.memory.close()


# ─────────────────────── check_show_dont_tell ───────────────────────


def test_check_show_dont_tell_clean_passes() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    body = "The door swung open. Sunlight spilled across the floor."
    data, _ = _invoke(e, iid, "check_show_dont_tell", body=body)
    assert data["passed"] is True
    assert data["tell_count"] == 0
    e.memory.close()


def test_check_show_dont_tell_flags_telling_verbs() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    body = ("She felt sad. He realized something was wrong. "
            "She noticed his face. They wondered if it would end.")
    data, _ = _invoke(e, iid, "check_show_dont_tell", body=body)
    assert data["passed"] is False
    assert data["tell_count"] >= 4
    assert "felt" in data["tells"]
    e.memory.close()


# ─────────────────────── check_content_warnings ───────────────────────


def test_check_content_warnings_clean_body_returns_no_warnings() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    body = "She walked through the meadow. Bees danced. The sun was warm."
    data, _ = _invoke(e, iid, "check_content_warnings", body=body)
    assert data["warnings"] == []
    e.memory.close()


def test_check_content_warnings_detects_canonical_categories() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    body = ("The knife pierced his chest. Blood pooled. "
            "She drank the whiskey and lit a cigarette.")
    data, _ = _invoke(e, iid, "check_content_warnings", body=body)
    assert "violence" in data["warnings"]
    assert "substance" in data["warnings"]
    e.memory.close()
