"""Spec 392 — per-intent session activity auto-append.

Every capability call appends one line to ``.agency/sessions/<intent>.activity.md``
(append-only, grow-only; owner directive). Off by default on a bare Engine; the
production server opts in via ``enable_session_autolog``.
"""
from __future__ import annotations

import os

from agency.engine import Engine
from agency._session_log import activity_log_path


def _confirmed_intent(eng):
    iid = eng.intent.capture("p", "d", "a")
    eng.intent.confirm(iid)
    return iid


def test_autolog_appends_a_line_per_call_and_grows(tmp_path):
    eng = Engine(str(tmp_path / "s.db"))
    eng.enable_session_autolog()
    try:
        iid = _confirmed_intent(eng)
        eng.registry.invoke(eng.memory, iid, "reflect", "note",
                            scope="observation", text="first")
        path = activity_log_path(eng.memory, iid)
        assert os.path.exists(path), "activity log created on first call"
        first = open(path, encoding="utf-8").read()
        assert "reflect.note" in first

        eng.registry.invoke(eng.memory, iid, "reflect", "note",
                            scope="observation", text="second")
        second = open(path, encoding="utf-8").read()
        # append-only growth: the file is LONGER and keeps BOTH lines (rule 9).
        assert len(second) > len(first)
        assert second.count("reflect.note") == 2
    finally:
        eng.memory.close()


def test_autolog_is_off_by_default_on_a_bare_engine(tmp_path):
    eng = Engine(str(tmp_path / "s.db"))               # no enable_session_autolog()
    try:
        iid = _confirmed_intent(eng)
        eng.registry.invoke(eng.memory, iid, "reflect", "note",
                            scope="observation", text="x")
        assert not os.path.exists(activity_log_path(eng.memory, iid)), \
            "a bare Engine must not write session files unless opted in"
    finally:
        eng.memory.close()
