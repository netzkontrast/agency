"""Spec 242 — codex entity matching: word-boundary + fuzzy.

Decidable matches are whole-word regex hits with word-boundary-aligned spans
and confidence None; "raven" never matches inside "ravenous" (the substring
trap that motivated the spec). The fuzzy pass is driver-backed, advisory
(judged), and degrades gracefully to judged=[] when no driver is wired.
Malformed driver spans are rejected (MATCH_INVALID); a malformed raw-regex
trigger invalidates only its own entry (CODEX_ENTRY_INVALID).
"""
from __future__ import annotations

import tempfile

from agency.engine import Engine


def _fresh() -> Engine:
    return Engine(tempfile.mktemp(suffix=".db"))


def _iid(e: Engine) -> str:
    iid = e.intent.capture("spec 242", "codex fuzzy match", "verified")
    e.intent.confirm(iid)
    return iid


def _invoke(e, iid, verb, **kw):
    r, _ = e.registry.invoke(e.memory, iid, "novel", verb, **kw)
    return r


def _codex(e, iid):
    nid = _invoke(e, iid, "create_novel", title="R", author="A")["novel_id"]
    raven = _invoke(e, iid, "create_codex_entry", novel_id=nid, slug="raven",
                    name="Raven", kind="minor-character", body="The bird.",
                    triggers="raven")["entry_id"]
    seb = _invoke(e, iid, "create_codex_entry", novel_id=nid,
                  slug="sebastian", name="Sebastian", kind="minor-character",
                  body="The butler.", triggers="Sebastian")["entry_id"]
    return nid, raven, seb


class FakeMatchDriver:
    """Mocked Spec-147 driver: maps the known typo to Sebastian."""

    model_id = "fake-fuzzy-1"

    def __init__(self, suggestions):
        self.suggestions = suggestions
        self.calls = 0

    def fuzzy_match(self, text, entries):
        self.calls += 1
        return self.suggestions


_TEXT = "The ravenous Sebatsian glared at the raven."


def test_raven_never_matches_ravenous_and_spans_align() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, raven, _ = _codex(e, iid)
    out = _invoke(e, iid, "match_codex_entries", novel_id=nid, text=_TEXT)
    hits = [m for m in out["decidable"] if m["entry_id"] == raven]
    assert len(hits) == 1                          # NOT the "ravenous" prefix
    for m in out["decidable"]:
        s, t = m["span"]
        assert _TEXT[s:t].lower() == m["surface_form"].lower()
        assert s == 0 or not _TEXT[s - 1].isalnum()      # boundary before
        assert t == len(_TEXT) or not _TEXT[t].isalnum()  # boundary after
        assert m["confidence"] is None
        assert m["kind"] == "whole_word"
    assert out["judged"] == [] and out["fuzzy_status"] == "off"
    assert out["total"] == len(out["decidable"])
    # legacy shape survives for Spec-132 consumers
    assert out["matches"][0]["trigger_hit"] == "raven"
    e.memory.close()


def test_fuzzy_flags_typo_via_mocked_driver() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, _, seb = _codex(e, iid)
    start = _TEXT.index("Sebatsian")
    e.drivers.register("codex_match", FakeMatchDriver([
        {"entry_id": seb, "span": (start, start + len("Sebatsian")),
         "confidence": 0.85}]))
    out = _invoke(e, iid, "match_codex_entries", novel_id=nid, text=_TEXT,
                  fuzzy=True)
    assert out["fuzzy_status"] == "ok"
    assert len(out["judged"]) == 1
    j = out["judged"][0]
    assert j["kind"] == "fuzzy" and j["confidence"] == 0.85
    assert j["surface_form"] == "Sebatsian" and j["entry_id"] == seb
    assert j["model_id"] == "fake-fuzzy-1"        # interpretable later
    assert out["total"] == len(out["decidable"]) + 1
    # judged is advisory — decidable unchanged by the fuzzy pass
    assert all(m["confidence"] is None for m in out["decidable"])
    e.memory.close()


def test_fuzzy_degrades_gracefully_without_driver() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, raven, _ = _codex(e, iid)
    out = _invoke(e, iid, "match_codex_entries", novel_id=nid, text=_TEXT,
                  fuzzy=True)
    assert out["judged"] == []
    assert out["fuzzy_status"] == "driver_unavailable"
    assert any(m["entry_id"] == raven for m in out["decidable"])
    e.memory.close()


def test_malformed_driver_span_rejected_as_match_invalid() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, _, seb = _codex(e, iid)
    e.drivers.register("codex_match", FakeMatchDriver([
        {"entry_id": seb, "span": (10, 9999), "confidence": 0.9}]))
    out = _invoke(e, iid, "match_codex_entries", novel_id=nid, text=_TEXT,
                  fuzzy=True)
    assert out["judged"] == []
    assert any(i["code"] == "match_invalid" for i in out["invalid"])
    e.memory.close()


def test_malformed_raw_regex_names_entry_others_still_match() -> None:
    e = _fresh()
    iid = _iid(e)
    nid, raven, _ = _codex(e, iid)
    _invoke(e, iid, "create_codex_entry", novel_id=nid, slug="broken",
            name="Broken", kind="concept", body="bad regex",
            triggers="re:(unclosed")
    out = _invoke(e, iid, "match_codex_entries", novel_id=nid, text=_TEXT)
    assert any(i["code"] == "codex_entry_invalid" and i["slug"] == "broken"
               for i in out["invalid"])
    assert any(m["entry_id"] == raven for m in out["decidable"])
    e.memory.close()


def test_unknown_novel_is_typed_codex_not_found() -> None:
    e = _fresh()
    iid = _iid(e)
    assert _invoke(e, iid, "match_codex_entries", novel_id="novel:nope",
                   text=_TEXT) is None
    e.memory.close()
