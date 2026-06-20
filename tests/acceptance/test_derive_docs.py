"""Acceptance — derive-docs fence rewrite (Spec 149 Slice 2.2).

Tests the HTML-comment fence mechanism:
  <!-- derived:<id> --> ... <!-- /derived:<id> -->

The code ships in `scripts/derive_docs.py`; these scenarios guard the
observable write-side behaviour (fence content replaced; prose preserved;
idempotent; unclosed fence raises; no-fence → unchanged; live dry-run
completes).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, scenario, scenarios, then, when

scenarios("features/derive_docs.feature")


# ── helpers ───────────────────────────────────────────────────────────────────

_HAND_PROSE_BEFORE = "# My Spec\n\nSome hand-written prose.\n\n"
_HAND_PROSE_AFTER = "\n\nMore hand-written prose below.\n"


def _spec_with_fence(affects_file: str) -> str:
    return (
        f"---\nspec_id: \"test\"\naffects:\n  - {affects_file}\n---\n"
        + _HAND_PROSE_BEFORE
        + "<!-- derived:test-count -->\n"
        + "_placeholder_\n"
        + "<!-- /derived:test-count -->\n"
        + _HAND_PROSE_AFTER
    )


def _spec_with_unclosed_fence() -> str:
    return (
        "---\nspec_id: \"test\"\naffects: []\n---\n"
        "# Spec\n\n<!-- derived:test-count -->\n_content_\n"
        # intentionally missing the closing marker
    )


def _spec_no_fences(affects_file: str) -> str:
    return (
        f"---\nspec_id: \"test\"\naffects:\n  - {affects_file}\n---\n"
        "# Spec\n\nNo fences here.\n"
    )


# ── Given steps ───────────────────────────────────────────────────────────────

@given("a spec.md with a test-count fence and affects \"tests/test_foo.py\"",
       target_fixture="fence_ctx")
def _given_fence_with_affects():
    return {
        "text": _spec_with_fence("tests/test_foo.py"),
        "affects_file": "tests/test_foo.py",
        "result": None,
        "result2": None,
        "error": None,
    }


@given("7 collected tests for \"tests/test_foo.py\"", target_fixture="fence_ctx")
def _given_7_tests(fence_ctx):
    fence_ctx["counts"] = {"tests/test_foo.py": 7}
    return fence_ctx


@given("3 collected tests for \"tests/test_foo.py\"", target_fixture="fence_ctx")
def _given_3_tests(fence_ctx):
    fence_ctx["counts"] = {"tests/test_foo.py": 3}
    return fence_ctx


@given("a spec.md with an unclosed test-count fence", target_fixture="fence_ctx")
def _given_unclosed_fence():
    return {
        "text": _spec_with_unclosed_fence(),
        "counts": {},
        "result": None,
        "error": None,
    }


@given("a spec.md with no derived fences", target_fixture="fence_ctx")
def _given_no_fences():
    return {
        "text": _spec_no_fences("tests/test_foo.py"),
        "affects_file": "tests/test_foo.py",
        "counts": {"tests/test_foo.py": 5},
        "result": None,
        "error": None,
    }


# ── When steps ────────────────────────────────────────────────────────────────

@when("I apply derivations to the spec text")
def _apply_derivations(fence_ctx):
    from scripts.derive_docs import apply_derivations_to_spec_text, Derivation
    affects = [fence_ctx.get("affects_file", "")] if fence_ctx.get("affects_file") else []
    counts = fence_ctx.get("counts", {})
    test_count = sum(counts.get(f, 0) for f in affects)
    d = Derivation(spec_id="test", test_count=test_count,
                   affects_files=tuple(affects))
    try:
        fence_ctx["result"] = apply_derivations_to_spec_text(fence_ctx["text"], d)
    except ValueError as e:
        fence_ctx["error"] = e
        fence_ctx["result"] = None


@when("I apply derivations to the result again")
def _apply_derivations_again(fence_ctx):
    from scripts.derive_docs import apply_derivations_to_spec_text, Derivation
    affects = [fence_ctx.get("affects_file", "")] if fence_ctx.get("affects_file") else []
    counts = fence_ctx.get("counts", {})
    test_count = sum(counts.get(f, 0) for f in affects)
    d = Derivation(spec_id="test", test_count=test_count,
                   affects_files=tuple(affects))
    fence_ctx["result2"] = apply_derivations_to_spec_text(fence_ctx["result"], d)


def _spec_with_stale_fence(affects_file: str, stale_count: int) -> str:
    return (
        f"---\nspec_id: \"test\"\naffects:\n  - {affects_file}\n---\n"
        "# Spec\n\n"
        "<!-- derived:test-count -->\n"
        f"_test_count: **{stale_count}** (derived from `affects:` {affects_file})_\n"
        "<!-- /derived:test-count -->\n"
    )


def _spec_with_current_fence(affects_file: str, count: int) -> str:
    return (
        f"---\nspec_id: \"test\"\naffects:\n  - {affects_file}\n---\n"
        "# Spec\n\n"
        "<!-- derived:test-count -->\n"
        f"_test_count: **{count}** (derived from `affects:` {affects_file})_\n"
        "<!-- /derived:test-count -->\n"
    )


# ── drift-check Given steps ───────────────────────────────────────────────

@given("a spec.md with a stale test-count fence showing \"42\" but 7 collected tests",
       target_fixture="drift_ctx")
def _given_stale_fence():
    from scripts.derive_docs import Derivation
    affects_file = "tests/test_foo.py"
    text = _spec_with_stale_fence(affects_file, stale_count=42)
    d = Derivation(spec_id="test", test_count=7, affects_files=(affects_file,))
    return {"text": text, "derivation": d, "result": None}


@given("a spec.md with an up-to-date test-count fence showing \"7\" and 7 collected tests",
       target_fixture="drift_ctx")
def _given_current_fence():
    from scripts.derive_docs import Derivation
    affects_file = "tests/test_foo.py"
    text = _spec_with_current_fence(affects_file, count=7)
    d = Derivation(spec_id="test", test_count=7, affects_files=(affects_file,))
    return {"text": text, "derivation": d, "result": None}


@given("a spec.md with no derived fences and 5 collected tests",
       target_fixture="drift_ctx")
def _given_no_fences_drift():
    from scripts.derive_docs import Derivation
    affects_file = "tests/test_foo.py"
    text = _spec_no_fences(affects_file)
    d = Derivation(spec_id="test", test_count=5, affects_files=(affects_file,))
    return {"text": text, "derivation": d, "result": None}


# ── drift-check When steps ────────────────────────────────────────────────

@when("I check the spec text for derived-zone drift")
def _check_drift(drift_ctx):
    from scripts.derive_docs import spec_has_drift
    drift_ctx["result"] = spec_has_drift(drift_ctx["text"], drift_ctx["derivation"])


# ── drift-check Then steps ────────────────────────────────────────────────

@then("drift is detected and a diff hint is returned")
def _drift_detected(drift_ctx):
    assert drift_ctx["result"] is not None, "expected drift to be detected but got None"
    assert isinstance(drift_ctx["result"], str) and len(drift_ctx["result"]) > 0, (
        "expected a non-empty diff hint string")


@then("no drift is detected")
def _no_drift(drift_ctx):
    assert drift_ctx["result"] is None, (
        f"expected no drift but got: {drift_ctx['result']!r}")


# ── live --check step ─────────────────────────────────────────────────────

@when("I run derive-docs --check on the live repo", target_fixture="check_result")
def _run_derive_docs_check():
    repo = Path(__file__).parent.parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "scripts.derive_docs",
         "--check",
         "--plan-root", str(repo / "Plan"),
         "--repo-root", str(repo)],
        cwd=str(repo), capture_output=True, text=True, timeout=180,
    )
    return result


@then("it exits 0")
def _check_exits_0(check_result):
    assert check_result.returncode == 0, (
        f"expected exit 0 but got {check_result.returncode}:\n"
        f"stdout: {check_result.stdout[:500]}\n"
        f"stderr: {check_result.stderr[:500]}")


@when("I run derive-docs in dry-run mode on the live repo",
      target_fixture="dry_run_result")
def _run_derive_docs_dry():
    repo = Path(__file__).parent.parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "scripts.derive_docs",
         "--plan-root", str(repo / "Plan"),
         "--repo-root", str(repo)],
        cwd=str(repo), capture_output=True, text=True, timeout=180,
    )
    return result


# ── Then steps ────────────────────────────────────────────────────────────────

@then("the test-count fence content shows \"7\"")
def _fence_shows_7(fence_ctx):
    assert fence_ctx["result"] is not None, f"Got error: {fence_ctx.get('error')}"
    assert "**7**" in fence_ctx["result"], (
        f"Expected '**7**' in fence content; got:\n{fence_ctx['result']}")


@then("the hand prose outside the fence is unchanged")
def _prose_unchanged(fence_ctx):
    result = fence_ctx["result"]
    assert _HAND_PROSE_BEFORE in result, "prose before fence was altered"
    assert _HAND_PROSE_AFTER in result, "prose after fence was altered"


@then("the two results are identical")
def _idempotent(fence_ctx):
    assert fence_ctx["result"] == fence_ctx["result2"], (
        "second apply produced a different result — not idempotent")


@then("a DeriveError is raised with code \"derive_fence_broken\"")
def _unclosed_raises(fence_ctx):
    from scripts.derive_docs import DeriveError
    from agency.toolresult import Codes
    err = fence_ctx["error"]
    assert err is not None, "expected DeriveError but no error was raised"
    assert isinstance(err, DeriveError), (
        f"expected DeriveError (ValueError subclass) but got {type(err).__name__}: {err}")
    assert err.code == Codes.DERIVE_FENCE_BROKEN, (
        f"expected code {Codes.DERIVE_FENCE_BROKEN!r} but got {err.code!r}")
    msg = str(err).lower()
    assert "unclosed" in msg or "fence" in msg, (
        f"error message does not mention unclosed fence: {err}")


@then("the output is identical to the input")
def _no_fence_unchanged(fence_ctx):
    assert fence_ctx["result"] == fence_ctx["text"], (
        "spec with no fences was modified")


@then("it completes without error and reports at least one spec")
def _dry_run_ok(dry_run_result):
    assert dry_run_result.returncode == 0, (
        f"derive-docs exited {dry_run_result.returncode}:\n"
        f"stdout: {dry_run_result.stdout[:500]}\n"
        f"stderr: {dry_run_result.stderr[:500]}")
    assert "specs" in dry_run_result.stdout.lower(), (
        f"output does not mention specs:\n{dry_run_result.stdout[:300]}")
