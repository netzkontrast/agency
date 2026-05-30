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

import pytest

from agency.engine import Engine


@pytest.fixture
def engine(tmp_path):
    """Disk-backed engine — drop-in for the 11 legacy
    `Engine(tempfile.mktemp(suffix=".db"))` fixture blocks. Uses
    pytest's `tmp_path` (auto-cleaned per test; no race condition).
    Adds explicit `e.memory.close()` cleanup the legacy duplicates
    lacked (latent sqlite handle leak)."""
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


@pytest.fixture
def iid(engine):
    """Captured + confirmed intent on the disk-backed engine. Drop-in
    for the 11 legacy `iid` fixture blocks. Use the default purpose/
    deliverable/acceptance unless your test specifically asserts on
    intent text (in which case call `engine.intent.capture(...)`
    directly)."""
    i = engine.intent.capture("test intent", "test deliverable", "test acceptance")
    engine.intent.confirm(i)
    return i


@pytest.fixture
def make_engine(tmp_path):
    """Factory for tests that need a non-default Engine — custom
    `jules_client`, `vcs_backend`, `surface`, or `extra_capabilities`.
    Returns a callable; each call yields a fresh Engine. All created
    engines are cleaned up at teardown.

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
        e.memory.close()
