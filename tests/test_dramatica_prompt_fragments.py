"""Spec 129 — Dramatica-as-prompt-fragments.

Three verbs on the prompt cap:
- prompt.fragment(slug) → single lookup
- prompt.fragments_for(scope, max_tokens) → multi-entry composer
- prompt.register_fragment(slug, text) → write to project overlay

Storage is hybrid: vendored bootstrap JSON + per-project YAML overlay.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agency.engine import Engine


@pytest.fixture
def engine():
    return Engine(tempfile.mktemp(suffix=".db"))


@pytest.fixture
def iid(engine):
    return engine.intent.capture_and_confirm(
        "spec 129 fragments",
        "dramatica vocabulary as prompts",
        "lookup + compose + overlay round-trip",
        owner="user")


def _call(engine, iid, verb, **kw):
    r, _ = engine.registry.invoke(
        engine.memory, iid, "prompt", verb,
        agent_id="agent:test", **kw)
    return r


@pytest.fixture(autouse=True)
def _reset_cache():
    """Each test starts with a fresh fragment-store cache + neutral CWD
    (overlay defaults to .agency/ in CWD; isolated tmp dir per test
    keeps the suite hermetic)."""
    from agency.capabilities.prompt import _main as p
    p._load_fragments.cache_clear()
    yield
    p._load_fragments.cache_clear()


# ---------------------------------------------------------------------------
# Verb registration.
# ---------------------------------------------------------------------------


def test_fragment_verbs_registered(engine):
    verbs = set(engine.registry.get("prompt").verbs)
    assert {"fragment", "fragments_for", "register_fragment"} <= verbs


# ---------------------------------------------------------------------------
# prompt.fragment — single lookup with kind-prefix resolution.
# ---------------------------------------------------------------------------


def test_fragment_canonical_lookup(engine, iid):
    r = _call(engine, iid, "fragment", slug="throughline.main")
    assert r.get("text"), f"main-throughline fragment missing: {r}"
    assert r["canonical_id"] == "throughline.main"
    assert r["kind"] == "throughline"
    assert r["tokens"] > 0


def test_fragment_archetype_lookup(engine, iid):
    r = _call(engine, iid, "fragment", slug="arc.protagonist")
    assert "Protagonist" in r["text"] or "PURSUIT" in r["text"]


def test_fragment_kind_prefix_alias_resolves(engine, iid):
    """`el.morality` resolves to `var.morality` (Spec 120 _resolve_term);
    the fragment lookup must follow the resolution."""
    r = _call(engine, iid, "fragment", slug="el.morality")
    assert r.get("text"), f"expected var.morality fragment: {r}"
    assert r["canonical_id"] == "var.morality"


def test_fragment_type_lookup(engine, iid):
    r = _call(engine, iid, "fragment", slug="type.past")
    assert r.get("text")
    assert "Past" in r["text"]


def test_fragment_no_fragment_for_unauthored(engine, iid):
    """Ontology entry exists but no fragment authored → NO_FRAGMENT."""
    r = _call(engine, iid, "fragment", slug="el.ability")
    assert r.get("error") == "NO_FRAGMENT"
    assert r["canonical_id"] == "el.ability"


def test_fragment_unknown_slug(engine, iid):
    r = _call(engine, iid, "fragment", slug="bogus.nonexistent")
    assert r.get("error") == "UNKNOWN_SLUG"


# ---------------------------------------------------------------------------
# prompt.fragments_for — multi-entry composer + token budget.
# ---------------------------------------------------------------------------


def test_fragments_for_basic_scope(engine, iid):
    scope = {
        "throughline": "mc",          # → throughline.main
        "class_id": "class.universe",
        "concern_id": "type.past",
        "problem_id": "el.self-interest",   # resolves to var.self-interest
        "solution_id": "el.morality",       # resolves to var.morality
    }
    r = _call(engine, iid, "fragments_for", scope=scope)
    canonical_ids = [f["canonical_id"] for f in r["fragments"]]
    assert "throughline.main" in canonical_ids
    assert "class.universe" in canonical_ids
    assert "type.past" in canonical_ids
    assert "var.self-interest" in canonical_ids
    assert "var.morality" in canonical_ids
    assert r["total_tokens"] > 0
    assert r["truncated_at"] is None  # default budget large enough


def test_fragments_for_archetypes(engine, iid):
    scope = {"archetypes": ["arc.protagonist", "arc.antagonist", "arc.guardian"]}
    r = _call(engine, iid, "fragments_for", scope=scope)
    canonical_ids = [f["canonical_id"] for f in r["fragments"]]
    assert canonical_ids == ["arc.protagonist", "arc.antagonist", "arc.guardian"]


def test_fragments_for_truncates_on_budget(engine, iid):
    """A tiny budget forces truncation mid-walk; truncated_at points at the
    fragment index where the cut happened."""
    scope = {
        "throughline": "mc",
        "class_id": "class.universe",
        "concern_id": "type.past",
        "problem_id": "el.self-interest",
    }
    r = _call(engine, iid, "fragments_for", scope=scope, max_tokens=120)
    assert r["truncated_at"] is not None
    assert r["total_tokens"] <= 120


def test_fragments_for_skips_unknown(engine, iid):
    scope = {"throughline": "mc", "class_id": "class.bogus"}
    r = _call(engine, iid, "fragments_for", scope=scope)
    ids = [f["canonical_id"] for f in r["fragments"]]
    assert "throughline.main" in ids
    assert "class.bogus" in r["skipped_no_fragment"]


def test_fragments_for_skips_unauthored(engine, iid):
    """Unauthored entry (no fragment yet) — included in skipped list."""
    scope = {"problem_id": "el.ability"}   # entry exists but no fragment
    r = _call(engine, iid, "fragments_for", scope=scope)
    assert r["fragments"] == []
    assert "el.ability" in r["skipped_no_fragment"]


# ---------------------------------------------------------------------------
# prompt.register_fragment — overlay write + round-trip.
# ---------------------------------------------------------------------------


def test_register_fragment_round_trip(engine, iid, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    text = "Test guidance for the Ability element — write tightly."
    r = _call(engine, iid, "register_fragment",
              slug="el.ability", text=text)
    assert r.get("canonical_id") == "el.ability"
    assert r.get("overlay_path", "").endswith("dramatica-fragments-overlay.yaml")
    # Round-trip: fragment lookup should now hit the overlay.
    r2 = _call(engine, iid, "fragment", slug="el.ability")
    assert r2.get("text") == text


def test_register_fragment_overlay_overrides_vendored(engine, iid,
                                                       tmp_path, monkeypatch):
    """Overlay wins over vendored — a project can replace a bootstrap fragment."""
    monkeypatch.chdir(tmp_path)
    override = "PROJECT OVERRIDE: Main-character throughline guidance."
    _call(engine, iid, "register_fragment",
          slug="throughline.main", text=override)
    r = _call(engine, iid, "fragment", slug="throughline.main")
    assert r["text"] == override


def test_register_fragment_unknown_slug(engine, iid, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = _call(engine, iid, "register_fragment",
              slug="bogus.zzz", text="ignored")
    # ToolResult.failure for UNKNOWN_SLUG — check via wrapper shape
    # (registry unwraps to data on success; failure surfaces as error dict).
    assert r.get("error") == "UNKNOWN_SLUG" or r.get("code") == "UNKNOWN_SLUG"
