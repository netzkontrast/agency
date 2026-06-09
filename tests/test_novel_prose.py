"""Spec 104 Slice 1 — novel prose cluster (driver-free verbs).

3 driver-free deterministic prose-analysis verbs covering Slice 1:
count_words / analyze_readability / check_filter_words. TextDriver-backed
verbs (voice signature / dialogue ratio / POV / continuity) + 3
editorial-stage composite gates land in Slice 2.
"""
from __future__ import annotations

import tempfile

import pytest

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _confirmed_iid(e: Engine, purpose: str = "spec 104") -> str:
    iid = e.intent.capture(purpose, "prose", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e: Engine, iid: str, verb: str, **kw):
    return e.registry.invoke(e.memory, iid, "novel", verb, **kw)


# ─────────────────────── verb registration ───────────────────────


def test_novel_capability_registers_prose_verbs() -> None:
    e = _fresh()
    cap = e.registry._caps["novel"]
    expected = {"count_words", "analyze_readability", "check_filter_words"}
    missing = expected - set(cap.verbs)
    assert not missing, f"missing prose verbs: {missing}"
    e.memory.close()


# ─────────────────────── count_words ───────────────────────


def test_count_words_simple_prose() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "count_words",
                      body="The quick brown fox jumps over the lazy dog.")
    assert data["word_count"] == 9
    assert data["char_count"] == 44
    e.memory.close()


def test_count_words_handles_whitespace_punctuation() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "count_words",
                      body="  Hello,   world!  This is  a test.  ")
    assert data["word_count"] == 6
    e.memory.close()


def test_count_words_empty_body() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, _ = _invoke(e, iid, "count_words", body="")
    assert data["word_count"] == 0
    assert data["char_count"] == 0
    e.memory.close()


# ─────────────────────── analyze_readability ───────────────────────


def test_analyze_readability_returns_flesch_score() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    body = ("The cat sat on the mat. The mat was red. "
            "The cat was happy. The day was bright.")
    data, _ = _invoke(e, iid, "analyze_readability", body=body)
    assert "flesch" in data
    assert isinstance(data["flesch"], float)
    assert data["flesch"] >= 80, f"unexpected flesch={data['flesch']}"
    assert data["sentences"] == 4
    e.memory.close()


def test_analyze_readability_complex_prose_lower_score() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    body = ("The metamorphosis of consciousness amid the technological "
            "singularity engenders unprecedented epistemological "
            "complications for contemporary philosophical discourse.")
    data, _ = _invoke(e, iid, "analyze_readability", body=body)
    assert data["flesch"] < 40, f"unexpected flesch={data['flesch']}"
    e.memory.close()


def test_analyze_readability_empty_body() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    data, inv = _invoke(e, iid, "analyze_readability", body="")
    assert data is None
    err = e.memory.recall(inv).get("error", "")
    assert "INVALID_ARGUMENT" in err
    e.memory.close()


# ─────────────────────── check_filter_words ───────────────────────


def test_check_filter_words_finds_density() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    body = ("She really just wanted to somehow feel actually alive. "
            "It was very quiet, really still.")
    data, _ = _invoke(e, iid, "check_filter_words", body=body)
    assert data["filter_count"] >= 5
    assert data["total_words"] > 0
    assert data["density"] > 0.1
    offenders = set(data["offenders"])
    assert {"really", "just", "very", "somehow", "actually"} <= offenders
    e.memory.close()


def test_check_filter_words_clean_prose() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    body = ("She wanted to feel alive. The room held its breath, silent.")
    data, _ = _invoke(e, iid, "check_filter_words", body=body)
    assert data["filter_count"] == 0
    assert data["density"] == 0.0
    assert data["offenders"] == []
    e.memory.close()


def test_check_filter_words_passed_signal() -> None:
    e = _fresh()
    iid = _confirmed_iid(e)
    clean, _ = _invoke(e, iid, "check_filter_words",
                       body="She walked into the room and waited.")
    assert clean["passed"] is True
    dense, _ = _invoke(e, iid, "check_filter_words",
                       body="She really just walked very slowly into "
                            "the room and just waited really quietly.")
    assert dense["passed"] is False
    e.memory.close()
