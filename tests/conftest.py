"""Spec 016 v2 Phase 5 — shared engine/iid fixtures.

Eliminates the 13 duplicate fixture blocks the test suite carried
(claim verified verbatim by survey a7e6bd1) and removes a latent bug:
the legacy duplicates used `tempfile.mktemp(suffix=".db")` which is
deprecated since Python 2 (race condition — the predicted path isn't
guaranteed unique). This conftest uses pytest's `tmp_path` instead,
which guarantees per-test isolation and auto-cleanup.

Four fixtures, picked by survey-grounded need:
- `engine` — disk-backed (tmp_path). Drop-in for 11 legacy duplicates.
- `memory_engine` — `Engine(":memory:")`. For the ~13 inline call-sites.
- `iid` — captured + confirmed intent on `engine`. Drop-in for 11
  legacy `iid` duplicates.
- `make_engine` — factory yielding a callable for tests that pass
  custom kwargs (jules_client, surface, extra_capabilities). Replaces
  the 5 special-purpose local fixtures.

Tests that need their own pattern (e.g. test_agency.py's parameterized
fresh() factory called ~60× with custom backends) continue to own
their setup — these conftest fixtures are opt-in, not mandatory."""
from __future__ import annotations

import re

import pytest

from agency.engine import Engine


# ---------------------------------------------------------------------------
# Spec 053 — auto-mark tests by file path so `pytest -m <capname>` works
# without per-test maintenance.
# ---------------------------------------------------------------------------


# Pattern → marker. First match wins; tests that match no pattern get NO
# auto-marker (still run in default suite, just not selectable via -m).
# AGENCY-DRIFT: test-marker-patterns — update when a new capability adds
#   a tests/test_<name>_*.py file convention; mirror in pyproject's
#   [tool.pytest.ini_options].markers and scripts/test-changed mapping.
_AUTO_MARKER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"test_e2e_"),         "e2e"),
    (re.compile(r"test_analyze_"),     "analyze"),
    (re.compile(r"test_research_"),    "research"),
    (re.compile(r"test_dogfood_"),     "dogfood"),
    (re.compile(r"test_document_"),    "document"),
    (re.compile(r"test_reflect_"),     "reflect"),
    (re.compile(r"test_delegate_"),    "delegate"),
    (re.compile(r"test_dispatch_"),    "delegate"),
    (re.compile(r"test_intent_"),      "intent"),
    (re.compile(r"test_jules_"),       "jules"),
    (re.compile(r"test_distribution"), "distribution"),
    (re.compile(r"test_install_"),     "install"),
    # Spec 060 round 9 — folder-form caps that scripts/test-changed
    # selects but conftest's marker map missed: tests for these caps
    # were deselected when `-m` expressions filtered to the cap name.
    (re.compile(r"test_develop_"),         "develop"),
    (re.compile(r"test_gate_"),            "gate"),
    (re.compile(r"test_branch_"),          "branch"),
    (re.compile(r"test_workspace_"),       "workspace"),
    (re.compile(r"test_subagent_"),        "subagent"),
    (re.compile(r"test_skill_generator_"), "skill_generator"),
    (re.compile(r"test_plugin_"),          "plugin"),
    (re.compile(r"test_welcome"),      "substrate"),
    (re.compile(r"test_agency_doctor"), "substrate"),
    # Spec 094 — music cluster wave (lifecycle child + 6 sibling clusters).
    # AGENCY-DRIFT: music-cluster-markers — when a 095-100 cluster ships,
    #   add its test_music_<cluster>_ pattern here and mirror in pyproject's
    #   [tool.pytest.ini_options].markers and scripts/test-changed mapping.
    (re.compile(r"test_music_lifecycle"), "music_lifecycle"),
    (re.compile(r"test_music_lyrics"),    "music_lyrics"),
    (re.compile(r"test_music_audio"),     "music_audio"),
    (re.compile(r"test_music_catalogue"), "music_catalogue"),
    (re.compile(r"test_music_promo"),     "music_promo"),
    (re.compile(r"test_music_research"),  "music_research"),
    (re.compile(r"test_music_gates"),     "music_gates"),
    # Generic fallback so `scripts/test-cap music` picks up any test_music_*
    # that doesn't match a more specific cluster pattern (e.g. a future
    # test_music_smoke.py). Must come AFTER the specific patterns since
    # first-match wins.
    (re.compile(r"test_music_"),          "music"),
    # Spec 101 — novel cluster wave (master + Slices 102-108 sibling clusters).
    (re.compile(r"test_novel_"),          "novel"),
]


def pytest_collection_modifyitems(config, items):
    """Auto-apply markers based on the test file basename.

    Lets `pytest -m research` pick up tests in `tests/test_research_*.py`
    without any per-test annotation. No-op for files that don't match
    any pattern.
    """
    for item in items:
        # item.fspath.basename is `test_research_capability.py` etc.
        basename = getattr(item.fspath, "basename", "") or ""
        for pat, marker in _AUTO_MARKER_PATTERNS:
            if pat.search(basename):
                item.add_marker(getattr(pytest.mark, marker))
                break


@pytest.fixture
def engine(tmp_path):
    """Disk-backed engine — drop-in for the legacy
    `Engine(tempfile.mktemp(suffix=".db"))` fixture blocks (panel F6
    audit: 9 trivial drop-ins remaining + 5 custom-kwarg tests that
    need `make_engine` instead — total 14 legacy fixtures, not the
    11 v1 estimated). Uses pytest's `tmp_path` (auto-cleaned per test;
    no race condition vs the deprecated `tempfile.mktemp`). Adds
    explicit `e.memory.close()` cleanup the legacy duplicates lacked
    (latent sqlite handle leak)."""
    e = Engine(str(tmp_path / "agency.db"))
    try:
        yield e
    finally:
        e.memory.close()


@pytest.fixture
def memory_engine():
    """In-memory engine — for tests that don't need on-disk semantics
    (the inline `Engine(":memory:")` pattern, ~13 call-sites)."""
    e = Engine(":memory:")
    try:
        yield e
    finally:
        e.memory.close()


def _default_intent(eng: Engine) -> str:
    """Capture + confirm a generic test intent on the given engine.
    Shared by `iid` and `memory_iid` so the contract stays identical
    across disk/memory backends."""
    i = eng.intent.capture("test intent", "test deliverable", "test acceptance")
    eng.intent.confirm(i)
    return i


@pytest.fixture
def iid(engine):
    """Captured + confirmed intent on the DISK-backed engine. Drop-in
    for the legacy `iid` fixture blocks (9-11 tests across the suite —
    survey a7e6bd1 verified the count). Tests that assert on intent
    text should call `engine.intent.capture(...)` directly."""
    return _default_intent(engine)


@pytest.fixture
def memory_iid(memory_engine):
    """Captured + confirmed intent on the MEMORY engine — the symmetric
    counterpart to `iid` (Spec 016 v2 panel F3). Prevents the silent
    dual-engine footgun where a test requesting (memory_engine, iid)
    would have two engines: an in-memory one for the test + an unused
    disk-backed one created just to hang `iid` off."""
    return _default_intent(memory_engine)


@pytest.fixture
def make_engine(tmp_path):
    """Factory for tests that need a non-default Engine — custom
    `jules_client`, `vcs_backend`, `surface`, or `extra_capabilities`.
    Returns a callable; each call yields a fresh Engine. All created
    engines are cleaned up at teardown, each guarded so a single
    locked sqlite handle doesn't leak the rest (Spec 016 v2 panel F2).

    Usage:
        def test_with_custom_client(make_engine):
            e = make_engine(jules_client=StubJulesClient())
            ...
    """
    created: list[Engine] = []

    def _factory(**kwargs):
        kwargs.setdefault("path", str(tmp_path / f"agency_{len(created)}.db"))
        e = Engine(**kwargs)
        created.append(e)
        return e

    yield _factory
    for e in created:
        try:
            e.memory.close()
        except Exception:
            # one stuck handle (locked sqlite, double-close, etc.) must
            # not leak the rest — panel F2 fix
            pass
