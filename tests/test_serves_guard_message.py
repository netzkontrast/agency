"""Spec 029 §B — SERVES-guard error message teaches the next call.

Closes F6 (Mittel/DX): the discovery loop dead-ended on
``ValueError: intent_id 'x' is not an Intent node`` with no pointer to
how to get one. The new message names ``intent_bootstrap``."""
import pytest

from agency.engine import Engine


def test_serves_guard_error_mentions_intent_bootstrap(tmp_path):
    e = Engine(str(tmp_path / "graph.db"))
    try:
        with pytest.raises(ValueError) as ei:
            e.registry.invoke(e.memory, "intent:does-not-exist", "plugin", "help")
    finally:
        e.memory.close()
    msg = str(ei.value)
    assert "intent_bootstrap" in msg
    assert "agency.cli intent" in msg            # bash side-pipe still acknowledged
