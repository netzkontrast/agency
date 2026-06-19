"""Acceptance — multi-agent self-installer (Spec 327).

surface_card → per-agent adapters (compact projection: frugal discipline + entry
pointers, NOT the full verb index); idempotent fenced-block merge; per-adapter
report; uninstall removes only the block. Drives agency._install_adapters.
"""
from __future__ import annotations

import os

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from agency import _frugal, _install_adapters as ia
from conftest import call_tool

scenarios("features/installer.feature")

_CURSOR = ".cursor/rules/agency.mdc"
_COPILOT = ".github/copilot-instructions.md"
_WINDSURF = ".windsurf/rules/agency.md"
_USER_TEXT = "# My project rules\n\nAlways write tests.\n"


@pytest.fixture
def proj(tmp_path, engine, monkeypatch):
    return {"root": str(tmp_path), "engine": engine, "report": None, "mp": monkeypatch}


def _read(proj, rel):
    with open(os.path.join(proj["root"], rel), encoding="utf-8") as f:
        return f.read()


@given("a clean installer project")
def _clean(proj):
    return proj


@given(parsers.parse('agency is installed for agent "{name}"'))
@when(parsers.parse('I install agency for agent "{name}"'))
@when(parsers.parse('I install agency for agent "{name}" again'))
def _install(proj, name):
    proj["report"] = ia.install_agents([name], proj["root"], proj["engine"])


@given("a user-authored copilot instructions file")
def _user_copilot(proj):
    path = os.path.join(proj["root"], _COPILOT)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_USER_TEXT)


@when("I install agency for all instruction agents")
def _install_all(proj):
    proj["report"] = ia.install_agents(ia.INSTRUCTION_AGENTS, proj["root"], proj["engine"])


@when(parsers.parse('I uninstall agency for agent "{name}"'))
def _uninstall(proj, name):
    proj["report"] = ia.uninstall_agents([name], proj["root"])


@then("the cursor rules file exists with valid frontmatter")
def _cursor_front(proj):
    content = _read(proj, _CURSOR)
    assert content.startswith("---"), content[:40]
    assert "alwaysApply" in content and "description:" in content, content[:120]


@then("the cursor file contains the frugal discipline")
def _cursor_frugal(proj):
    content = _read(proj, _CURSOR)
    assert "YAGNI" in content
    for marker in _frugal.SAFETY_FLOOR_MARKERS:
        assert marker in content, f"missing floor marker {marker!r}"


@then("the cursor file contains the agency CLI entry pointer")
def _cursor_cli(proj):
    assert "agency <cap> <verb>" in _read(proj, _CURSOR)


@then("the cursor file does not inline the full verb index")
def _cursor_no_index(proj):
    # The compact projection lists capability NAMES + entry pointers — never the
    # per-verb tool ids (which all carry the `capability_` prefix).
    assert "capability_" not in _read(proj, _CURSOR)


@then("the cursor file carries the pipx bootstrap line")
def _cursor_boot(proj):
    assert "pipx install" in _read(proj, _CURSOR)


@then("the cursor file has exactly one agency block")
def _one_block(proj):
    assert _read(proj, _CURSOR).count(ia.FENCE_START) == 1


@then("the user content is preserved")
def _user_kept(proj):
    assert "Always write tests." in _read(proj, _COPILOT)


@then("an agency block is appended to the copilot file")
def _block_appended(proj):
    content = _read(proj, _COPILOT)
    assert ia.FENCE_START in content and "YAGNI" in content


@then("no agency block remains in the copilot file")
def _no_block(proj):
    assert ia.FENCE_START not in _read(proj, _COPILOT)


@then("every requested adapter is reported")
def _all_reported(proj):
    assert set(proj["report"]) == set(ia.INSTRUCTION_AGENTS)


@then("the cursor and agents adapters succeeded")
def _cursor_agents_ok(proj):
    assert proj["report"]["cursor"]["ok"] and proj["report"]["agents"]["ok"], proj["report"]


@then("the windsurf file's discipline matches the live frugal render")
def _windsurf_live(proj):
    assert _frugal.render(mode="full") in _read(proj, _WINDSURF)


@when(parsers.parse('I call agency_install for agent "{name}" over the wire'))
def _install_wire(proj, name):
    proj["mp"].setenv("CLAUDE_PROJECT_DIR", proj["root"])
    proj["report"] = call_tool(proj["engine"], "agency_install",
                               {"target": proj["root"], "agent": name})


@then("the doctor lists cursor as an installed agent")
def _doctor_lists(proj):
    rep = call_tool(proj["engine"], "agency_doctor", {})
    assert "cursor" in rep.get("installed_agents", []), rep.get("installed_agents")


@then("every installed agent file carries every safety-floor marker")
def _all_floor(proj):
    seen = set()
    for name in ia.INSTRUCTION_AGENTS:
        for rel, _front in ia._TARGETS[name]:
            path = os.path.join(proj["root"], rel)
            if not os.path.exists(path):
                continue
            content = _read(proj, rel)
            for marker in _frugal.SAFETY_FLOOR_MARKERS:
                assert marker in content, f"{rel} dropped floor marker {marker!r}"
            seen.add(rel)
    assert seen, "no adapter files written"
