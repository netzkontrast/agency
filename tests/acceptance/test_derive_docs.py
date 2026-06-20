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


@then("a ValueError is raised mentioning the unclosed fence")
def _unclosed_raises(fence_ctx):
    assert fence_ctx["error"] is not None, "expected ValueError but no error was raised"
    assert isinstance(fence_ctx["error"], ValueError)
    msg = str(fence_ctx["error"]).lower()
    assert "unclosed" in msg or "fence" in msg, (
        f"error message does not mention unclosed fence: {fence_ctx['error']}")


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
