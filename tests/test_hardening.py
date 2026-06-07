"""Spec 006 — core hardening regression tests (the four verified red-team risks).

#1 O(1) clock seed (no full scan)   #2 pagination exhaustion + loop guard
#3 jules.verify fail-closed remote   #4 the API key value is never captured.
"""
import asyncio
import inspect
import json
import subprocess
import tempfile

import pytest
from fastmcp import Client

from agency.engine import Engine
from agency.memory import Memory


def _sc(res):
    return res.structured_content if hasattr(res, "structured_content") else res


# ── #1 — O(1) clock seed via server-side max(vfrom) aggregation ──────────────────
def test_clock_seed_is_aggregation_not_full_scan():
    # regression: _max_persisted_tick must NOT load every row (`MATCH (n) RETURN n`);
    # it uses server-side max(vfrom) aggregation over nodes + edges.
    src = inspect.getsource(Memory._max_persisted_tick)
    assert "max(n.vfrom)" in src and "max(r.vfrom)" in src
    assert "RETURN n\"" not in src and "RETURN r\"" not in src


def test_clock_continues_after_reopen_no_stale_tick_reuse(tmp_path):
    db = str(tmp_path / "g.db")
    e = Engine(db)
    iid = e.intent.capture("a", "b", "c")
    e.intent.confirm(iid)
    n = e.memory.record("Reflection", {"scope": "observation", "text": "x"})
    e.memory.link(n, iid, "OBSERVED_DURING")        # last write is an EDGE
    max_before = e.memory._tick
    assert max_before > 0
    e.memory.close()

    e2 = Engine(db)                                  # reopen over the same graph
    try:
        # seeded to the TRUE max (incl. the trailing edge) — not reset, no reuse
        assert e2.memory._tick == max_before
        e2.memory.record("Reflection", {"scope": "observation", "text": "y"})
        assert e2.memory._tick > max_before          # the new write got a fresh tick
    finally:
        e2.memory.close()


# ── #2 — pagination walks to exhaustion, with a repeated-token loop guard ────────
def _patch_request(monkeypatch, responder):
    from agency.capabilities.jules import api
    monkeypatch.setattr(api, "_request", responder)
    return api


def test_paginate_walks_to_real_exhaustion(monkeypatch):
    pages = [
        {"sources": [{"name": "s1"}], "nextPageToken": "t1"},
        {"sources": [{"name": "s2"}], "nextPageToken": "t2"},
        {"sources": [{"name": "s3"}], "nextPageToken": ""},   # real exhaustion
    ]
    state = {"i": 0}

    def responder(method, path, params=None):
        page = pages[min(state["i"], len(pages) - 1)]
        state["i"] += 1
        return page

    api = _patch_request(monkeypatch, responder)
    items = api._paginate("/v1alpha/sources", {"pageSize": 100})
    assert [s["name"] for s in items] == ["s1", "s2", "s3"]    # all pages, no 10-cap stop


def test_paginate_loop_guard_stops_on_repeated_token(monkeypatch):
    def responder(method, path, params=None):
        return {"sources": [{"name": "x"}], "nextPageToken": "SAME"}   # never advances

    api = _patch_request(monkeypatch, responder)
    items = api._paginate("/v1alpha/sources", {"pageSize": 100})
    # without the seen_tokens guard this loops forever; with it, it stops once the
    # token repeats (page1 records SAME, page2 sees it → break) → exactly 2 pages.
    assert len(items) == 2


# ── #3 — jules.verify derives remote truth independently, FAIL-CLOSED ────────────
class _FakeVCS:
    def __init__(self, ok=True, exists=False):
        self.ok, self.exists = ok, exists

    def remote_exists(self, branch, remote="origin"):
        return {"ok": self.ok, "exists": self.exists, "detail": "stub", "sha": "abc"}


def _verify(vcs, **kw):
    e = Engine(tempfile.mktemp(suffix=".db"), vcs_backend=vcs)
    try:
        iid = e.intent.capture("a", "b", "c")
        e.intent.confirm(iid)
        out, _ = e.registry.invoke(e.memory, iid, "jules", "verify", **kw)
        return out
    finally:
        e.memory.close()


def test_verify_fail_closed_when_branch_absent_on_remote():
    out = _verify(_FakeVCS(ok=True, exists=False), state="completed", branch="feat")
    assert out["done"] is False and out["branch_on_remote"] is False


def test_verify_fail_closed_on_remote_lookup_error():
    out = _verify(_FakeVCS(ok=False), state="completed", branch="feat")
    assert out["done"] is False and "remote check failed" in out.get("error", "")


def test_verify_done_only_when_completed_and_on_remote():
    out = _verify(_FakeVCS(ok=True, exists=True), state="completed", branch="feat")
    assert out["done"] is True and out["branch_on_remote"] is True
    # a caller cannot claim done for a non-completed state, even if the branch is up
    out2 = _verify(_FakeVCS(ok=True, exists=True), state="in_progress", branch="feat")
    assert out2["done"] is False


# ── #4 — the API key VALUE is never captured ─────────────────────────────────────
def test_no_capture_api_key_helper_is_wired():
    # regression: there must be no function that captures the key value into state.
    out = subprocess.run(["grep", "-rn", "def capture_api_key", "agency/"],
                         capture_output=True, text=True)
    assert out.stdout.strip() == "", f"a capture_api_key helper appeared: {out.stdout}"


def test_doctor_reports_key_presence_not_value(monkeypatch):
    monkeypatch.setenv("JULES_API_KEY", "super-secret-value-xyz")
    e = Engine(tempfile.mktemp(suffix=".db"))
    mcp = e.build_mcp(codemode=False)
    try:
        async def main():
            async with Client(mcp) as client:
                return _sc(await client.call_tool("agency_doctor", {}))
        out = asyncio.run(main())
    finally:
        e.memory.close()
    assert "super-secret-value-xyz" not in json.dumps(out)     # value never leaks

    def _find(d, key):                                          # the status may be nested
        if isinstance(d, dict):
            for k, v in d.items():
                if k == key:
                    return v
                got = _find(v, key)
                if got is not None:
                    return got
        elif isinstance(d, list):
            for x in d:
                got = _find(x, key)
                if got is not None:
                    return got
        return None

    assert _find(out, "JULES_API_KEY") in ("set", "missing")   # only presence reported
