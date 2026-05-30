"""Spec 012 Phase 6 follow-up — the watcher's recovery path must call
`_jules_patch.build_recovery_plan` with the post-PR-#9 signature:

    build_recovery_plan(outputs, branch, base, owner, repo, sid="")

The original PR #8 code passed `sid` as the sole positional arg, which
would crash at runtime once the recovery path actually fired (gated
behind 3 probe cycles, so unreachable in any test until this one).

This test stubs `_jules_api.jules_get_full` + `_jules_patch.build_recovery_plan`
and exercises the real `Watcher._poll_loop` recovery branch — locking in
the correct signature.
"""
import asyncio
from unittest.mock import patch as mock_patch

import pytest

from agency.capabilities import _jules_watch
from agency.capabilities._jules_watch import Watcher


@pytest.mark.asyncio
async def test_recovery_path_calls_build_recovery_plan_with_full_signature(monkeypatch):
    """When recovery_in_flight reaches attempt>=3, the watcher must call
    _jules_patch.build_recovery_plan with (outputs, branch, base, owner,
    repo, sid) — not the legacy (sid) shape from PR #8 pre-fix."""

    now = [1000.0]
    def fake_time():
        return now[0]

    async def fake_sleep(s):
        # Never actually sleep in tests; instead break out by raising
        # CancelledError so _poll_loop returns.
        raise asyncio.CancelledError

    watcher = Watcher(time_func=fake_time, sleep_func=fake_sleep)

    # Seed the recovery path at attempt=3 so the first loop iteration
    # exercises the build_recovery_plan branch directly.
    watcher.recovery_in_flight["sess-123"] = {
        "attempt": 3,
        "next_probe_at": now[0] - 1,    # already past probe window
        "intent_id": "intent_abc",
        "branch": "feature-x",
        "recover_branch": "recover-sess-123",
        "base": "main",
        "owner": "netzkontrast",
        "repo": "agency",
    }

    # vcs.remote_exists returns False so we stay in the recovery branch
    # (not the "branch landed on origin" short-circuit).
    monkeypatch.setattr(
        "agency.capabilities._vcs.GitClient.remote_exists",
        lambda self, branch, remote="origin": False,
    )

    # Stub _jules_api.jules_get_full to provide outputs + source info.
    fake_session = {
        "id": "sess-123",
        "state": "COMPLETED",
        "outputs": [{"changeSet": {"gitPatch": {"unidiffPatch": "diff --git a/x b/x\n"}}}],
        "sourceContext": {"source": "sources/netzkontrast-agency"},
    }
    monkeypatch.setattr(
        _jules_watch._jules_api, "jules_get_full",
        lambda sid: fake_session,
    )

    # Capture the build_recovery_plan call to assert the signature.
    captured: dict = {}
    def fake_build_recovery_plan(outputs, branch, base, owner, repo, sid=""):
        captured["outputs"] = outputs
        captured["branch"] = branch
        captured["base"] = base
        captured["owner"] = owner
        captured["repo"] = repo
        captured["sid"] = sid
        return {"branch": branch, "base_branch": base, "ops": [], "pr_title": "t", "pr_body": "b"}

    # Override the real module's attribute (other tests may have already
    # imported _jules_patch into sys.modules, so a sys.modules swap is
    # insufficient — the lazy `from … import _jules_patch` resolves to the
    # already-bound attribute on the parent package).
    from agency.capabilities import _jules_patch as real_jp
    monkeypatch.setattr(real_jp, "build_recovery_plan", fake_build_recovery_plan)

    # Drive the loop once via direct invocation; _poll_loop's sleep_func
    # raises CancelledError on the first cadence sleep, so we exit cleanly
    # after running the recovery branch.
    try:
        await watcher._poll_loop()
    except asyncio.CancelledError:
        pass

    # Verify the recovery_apply_plan event landed in the queue.
    q = watcher._get_queue("intent_abc")
    event = await q.get()
    assert event["action"] == "recover_apply_plan"
    assert event["session"] == "sess-123"

    # Verify the signature: full 6-arg form, owner/repo plumbed correctly.
    assert captured["outputs"] == fake_session["outputs"]
    assert captured["branch"] == "recover-sess-123"
    assert captured["base"] == "main"
    assert captured["owner"] == "netzkontrast"
    assert captured["repo"] == "agency"
    assert captured["sid"] == "sess-123"

    # And the session was de-armed (one-shot recovery).
    assert "sess-123" not in watcher.recovery_in_flight


@pytest.mark.asyncio
async def test_recovery_path_parses_owner_repo_from_source_when_not_preplumbed(monkeypatch):
    """When arm() did not plumb owner/repo onto st, the watcher falls back
    to parsing sourceContext.source ("sources/owner-repo" shape)."""

    now = [1000.0]
    async def fake_sleep(s):
        raise asyncio.CancelledError

    watcher = Watcher(time_func=lambda: now[0], sleep_func=fake_sleep)

    watcher.recovery_in_flight["sess-456"] = {
        "attempt": 3,
        "next_probe_at": now[0] - 1,
        "intent_id": "intent_xyz",
        "branch": "feature-y",
        # NO owner/repo/base/recover_branch — must derive from session.
    }

    monkeypatch.setattr(
        "agency.capabilities._vcs.GitClient.remote_exists",
        lambda self, branch, remote="origin": False,
    )

    monkeypatch.setattr(
        _jules_watch._jules_api, "jules_get_full",
        lambda sid: {
            "id": "sess-456",
            "outputs": [],
            "sourceContext": {"source": "sources/another-owner-someproject"},
        },
    )

    captured: dict = {}
    def fake_build_recovery_plan(outputs, branch, base, owner, repo, sid=""):
        captured.update(owner=owner, repo=repo, branch=branch, base=base)
        return {}

    from agency.capabilities import _jules_patch as real_jp
    monkeypatch.setattr(real_jp, "build_recovery_plan", fake_build_recovery_plan)

    try:
        await watcher._poll_loop()
    except asyncio.CancelledError:
        pass

    # The "sources/another-owner-someproject" string parses on the first
    # hyphen — owner="another", repo="owner-someproject" — confirms the
    # fallback path runs and produces SOMETHING reasonable rather than
    # crashing or passing "unknown".
    assert captured["owner"] == "another"
    assert "owner-someproject" in captured["repo"] or captured["repo"] == "owner-someproject"
    assert captured["branch"] == "recover-sess-456"
    assert captured["base"] == "main"
