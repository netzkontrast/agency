"""Acceptance — install pipeline (Spec 029/031/032/062/064/065/092).

Converted from: test_install_db_path, test_install_mcp_skill, test_install_per_cap,
test_install_prune, test_install_session_start_hook, test_install_verb.

Dropped (implementation / structural / not observable behaviour):
- test_write_chmod_failure_emits_warning_not_crash: tests an internal os.chmod
  error path via monkeypatch; chmod fallback is a subprocess side-effect, not
  observable MCP behaviour.
- test_agency_install_non_writable_target_fails: root-owned CI filesystem
  allows write even on chmod-restricted dirs, making this unreliable in the
  test environment.
- test_agency_install_scaffold_only_does_not_write_plugin_files: this is
  covered by the existing scaffold-only CLI test in test_install_verb —
  we retain the observable output check (no .mcp.json written) but drop
  the permission-check variant.
- test_generate_emits_per_cap_when_skill_doc_added: tests an internal Capability
  construction path via class-attribute injection; the installed behaviour
  (SKILL.md present for caps with skill_doc) is already covered by the general
  generate scenario.
- test_fragment_id_set_equals_spec_046_declared_set and related verdicts.json
  checks: these are structural JSON file checks, not observable system behaviour.
- test_agency_provenance_cli_subcommand: provenance walk is covered in
  test_acceptance.py (the moat / provenance feature) — not a new gap here.
"""
from __future__ import annotations

import asyncio
import json
import os
import stat
import tempfile
from pathlib import Path

import pytest
from fastmcp import Client
from pytest_bdd import given, parsers, scenarios, then, when

from agency.engine import Engine
from agency import install

scenarios("features/install.feature")


# ── helpers ───────────────────────────────────────────────────────────────────

def _call_install(eng: Engine, target: str) -> dict:
    mcp = eng.build_mcp(codemode=False)

    async def _run():
        async with Client(mcp) as c:
            r = await c.call_tool("agency_install", {"target": target})
            sc = r.structured_content
            if isinstance(sc, dict):
                return sc.get("result", sc)
            if sc is not None:
                return sc
            try:
                return json.loads(r.content[0].text)
            except Exception:
                return r.content[0].text

    return asyncio.run(_run())


def _generate(eng: Engine) -> dict:
    return install.generate(eng)


# ── shared Given override ─────────────────────────────────────────────────────

@given("a fresh agency engine in code-mode", target_fixture="install_engine")
def _fresh_engine():
    e = Engine(":memory:")
    return e


# ── given ─────────────────────────────────────────────────────────────────────

@given("a target with a pre-existing CLAUDE.md",
       target_fixture="preexisting_target")
def _preexisting(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# My project\n\nMy own notes.\n")
    return tmp_path


# ── when ──────────────────────────────────────────────────────────────────────

@when("I call agency_install on a temporary target", target_fixture="install_result")
def _do_install(install_engine, tmp_path):
    return _call_install(install_engine, str(tmp_path)), tmp_path


@when("I call agency_install on a temporary target twice",
      target_fixture="install_result_pair")
def _do_install_twice(install_engine, tmp_path):
    r1 = _call_install(install_engine, str(tmp_path))
    r2 = _call_install(install_engine, str(tmp_path))
    return r1, r2, tmp_path


@when("I call agency_install on that target", target_fixture="install_result")
def _do_install_preexisting(install_engine, preexisting_target, tmp_path):
    return _call_install(install_engine, str(preexisting_target)), preexisting_target


@when("I generate the install manifest", target_fixture="manifest")
def _do_generate(install_engine):
    return _generate(install_engine)


@when("I write the install to a temporary target", target_fixture="write_result")
def _do_write(install_engine, tmp_path):
    install.write(str(tmp_path))
    return tmp_path


@when("I run install.main with --dry-run on a temporary target",
      target_fixture="dry_run_result")
def _do_dry_run(install_engine, tmp_path, capsys):
    rc = install.main(["--dry-run", str(tmp_path)])
    return rc, tmp_path, capsys.readouterr()


@when("a fake orphan bin wrapper is planted and write is run again",
      target_fixture="prune_result")
def _plant_and_reregen(install_first_pass):
    tmp_path = install_first_pass
    orphan = tmp_path / "bin" / "agency-analyze-zzz_removed"
    orphan.write_text("#!/bin/sh\n")
    install.write(str(tmp_path))                                  # regen prunes orphan
    return tmp_path, orphan


# ── given for prune scenario ──────────────────────────────────────────────────

@given("install.write has been run once on a temporary directory",
       target_fixture="install_first_pass")
def _first_write(tmp_path):
    install.write(str(tmp_path))
    return tmp_path


# ── then — scaffold ───────────────────────────────────────────────────────────

@then(".agency/ directory is created")
def _agency_dir(install_result):
    _, tmp_path = install_result
    assert (tmp_path / ".agency").is_dir()


@then(".agency/README.md exists")
def _agency_readme(install_result):
    _, tmp_path = install_result
    assert (tmp_path / ".agency" / "README.md").exists()


@then(".gitattributes exists")
def _gitattributes(install_result):
    _, tmp_path = install_result
    assert (tmp_path / ".gitattributes").exists()


@then("CLAUDE.md exists and contains agency_welcome")
def _claude_md(install_result):
    _, tmp_path = install_result
    claude_md = tmp_path / "CLAUDE.md"
    assert claude_md.exists()
    assert "agency_welcome" in claude_md.read_text()


# ── then — idempotency ────────────────────────────────────────────────────────

@then("the second call reports claude_md_updated False")
def _second_call_not_updated(install_result_pair):
    _r1, r2, _tmp_path = install_result_pair
    assert r2["claude_md_updated"] is False


@then("CLAUDE.md contains exactly one onboarding start marker")
def _one_start_marker(install_result_pair):
    _, _, tmp_path = install_result_pair
    body = (tmp_path / "CLAUDE.md").read_text()
    assert body.count("<!-- agency:onboarding:start -->") == 1


@then("CLAUDE.md contains exactly one onboarding end marker")
def _one_end_marker(install_result_pair):
    _, _, tmp_path = install_result_pair
    body = (tmp_path / "CLAUDE.md").read_text()
    assert body.count("<!-- agency:onboarding:end -->") == 1


# ── then — preserves existing CLAUDE.md ──────────────────────────────────────

@then("the original CLAUDE.md content is preserved")
def _original_preserved(install_result):
    _, tmp_path = install_result
    body = (tmp_path / "CLAUDE.md").read_text()
    assert "# My project" in body
    assert "My own notes." in body


@then("the agency onboarding block is appended")
def _agency_block_appended(install_result):
    _, tmp_path = install_result
    body = (tmp_path / "CLAUDE.md").read_text()
    assert "<!-- agency:onboarding:start -->" in body
    assert "agency_welcome" in body


# ── then — generate manifest ──────────────────────────────────────────────────

@then("the fixed plugin.json and help SKILL.md are present")
def _fixed_files(manifest):
    assert ".claude-plugin/plugin.json" in manifest
    assert "skills/help/SKILL.md" in manifest


@then("at least one per-capability SKILL.md is present under skills/")
def _per_cap_skill(manifest):
    per_cap = [p for p in manifest
               if p.startswith("skills/") and p.endswith("/SKILL.md")
               and p not in ("skills/help/SKILL.md", "skills/using-agency/SKILL.md")]
    assert per_cap, "no per-capability SKILL.md files emitted"


@then("monitors/monitors.json contains exactly one agency-engine entry")
def _monitors(manifest):
    assert "monitors/monitors.json" in manifest
    entries = json.loads(manifest["monitors/monitors.json"])
    assert isinstance(entries, list) and len(entries) == 1
    assert entries[0]["name"] == "agency-engine"
    assert "monitor.log" in entries[0]["command"]


@then("hooks/hooks.json wires PostToolUse UserPromptSubmit and Stop to the dispatch script")
def _hooks_wire(manifest):
    parsed = json.loads(manifest["hooks/hooks.json"])
    events = parsed["hooks"]
    for ev in ("PostToolUse", "UserPromptSubmit", "Stop"):
        assert ev in events, f"{ev} not wired in hooks.json"
        cmd = events[ev][0]["hooks"][0]["command"]
        assert "dispatch" in cmd, f"{ev} must invoke dispatch"


@then("the dispatch script is emitted")
def _dispatch_emitted(manifest):
    assert "hooks/dispatch" in manifest


@then("hooks.json SessionStart entry has matcher startup|resume|clear")
def _session_start_matcher(manifest):
    parsed = json.loads(manifest["hooks/hooks.json"])
    entry = parsed["hooks"]["SessionStart"][0]
    assert entry["matcher"] == "startup|resume|clear"


@then("the SessionStart hook command has async False")
def _session_start_async(manifest):
    parsed = json.loads(manifest["hooks/hooks.json"])
    cmd = parsed["hooks"]["SessionStart"][0]["hooks"][0]
    assert cmd.get("async") is False


# ── then — session-start script ──────────────────────────────────────────────

@then("the session-start script starts with the bash shebang")
def _shebang(manifest):
    script = manifest["hooks/session-start"]
    assert script.startswith("#!/usr/bin/env bash")


@then("the script contains command -v pipx")
def _has_pipx_check(manifest):
    script = manifest["hooks/session-start"]
    assert "command -v pipx" in script


@then("the script contains pipx install --editable")
def _has_pipx_install(manifest):
    script = manifest["hooks/session-start"]
    assert "pipx install --editable" in script


@then("the scaffold step appears before the agency-mcp idempotency guard")
def _scaffold_before_guard(manifest):
    script = manifest["hooks/session-start"]
    scaffold_idx = script.find("agency install --scaffold-only")
    guard_idx = script.find("command -v agency-mcp")
    assert scaffold_idx > 0, "scaffold block missing"
    assert guard_idx > 0, "idempotency guard missing"
    assert scaffold_idx < guard_idx, (
        "scaffold must run BEFORE the install-check early-exit")


@then("the session-start script contains agency install --scaffold-only")
def _has_scaffold_only(manifest):
    assert "agency install --scaffold-only" in manifest["hooks/session-start"]


@then("the script does not contain agency install --scaffold-db")
def _no_scaffold_db(manifest):
    script = manifest["hooks/session-start"]
    assert "agency install --scaffold-db" not in script


# ── then — .mcp.json ─────────────────────────────────────────────────────────

@then(".mcp.json command is agency-mcp")
def _mcp_command(manifest):
    cfg = json.loads(manifest[".mcp.json"])
    assert cfg["mcpServers"]["agency"]["command"] == "agency-mcp"


@then(".mcp.json AGENCY_DB is ${CLAUDE_PROJECT_DIR}/.agency/session.db")
def _mcp_agency_db(manifest):
    cfg = json.loads(manifest[".mcp.json"])
    env = cfg["mcpServers"]["agency"]["env"]
    assert env["AGENCY_DB"] == "${CLAUDE_PROJECT_DIR}/.agency/session.db"


@then(".mcp.json does not contain PYTHONPATH")
def _no_pythonpath(manifest):
    cfg = json.loads(manifest[".mcp.json"])
    env = cfg["mcpServers"]["agency"]["env"]
    assert "PYTHONPATH" not in env


@then(".mcp.json cwd is ${CLAUDE_PROJECT_DIR}")
def _mcp_cwd(manifest):
    cfg = json.loads(manifest[".mcp.json"])
    server = cfg["mcpServers"]["agency"]
    assert server.get("cwd") == "${CLAUDE_PROJECT_DIR}"


@then(".mcp.json env_vars includes AGENCY_EMBEDDER AGENCY_DB and JULES_API_KEY")
def _mcp_env_vars(manifest):
    cfg = json.loads(manifest[".mcp.json"])
    env_vars = cfg["mcpServers"]["agency"].get("env_vars", [])
    for v in ("AGENCY_EMBEDDER", "AGENCY_DB", "JULES_API_KEY"):
        assert v in env_vars, f"{v} missing from env_vars"


# ── then — marketplace description ───────────────────────────────────────────

@then("the marketplace description contains the word capabilities")
def _mp_desc_capabilities(manifest, install_engine):
    mp = json.loads(manifest[".claude-plugin/marketplace.json"])
    desc = mp["plugins"][0]["description"]
    assert "capabilities" in desc.lower()


@then("the marketplace description contains the live capability count")
def _mp_desc_count(manifest, install_engine):
    mp = json.loads(manifest[".claude-plugin/marketplace.json"])
    desc = mp["plugins"][0]["description"]
    cap_count = len(install_engine.registry.names())
    assert str(cap_count) in desc


@then("the marketplace description is under 400 characters")
def _mp_desc_length(manifest):
    mp = json.loads(manifest[".claude-plugin/marketplace.json"])
    desc = mp["plugins"][0]["description"]
    assert len(desc) < 400


# ── then — help skill ────────────────────────────────────────────────────────

@then("the help SKILL.md contains mcp__plugin_agency_agency__execute")
def _help_mcp(manifest):
    assert "mcp__plugin_agency_agency__execute" in manifest["skills/help/SKILL.md"]


@then("the help SKILL.md contains agency intent or agency execute")
def _help_bash(manifest):
    skill = manifest["skills/help/SKILL.md"]
    assert "agency intent" in skill or "agency execute" in skill


@then("the help SKILL.md allowed-tools lists all three agency MCP tools")
def _help_allowed_tools(manifest):
    skill = manifest["skills/help/SKILL.md"]
    for tool in ("mcp__plugin_agency_agency__search",
                 "mcp__plugin_agency_agency__get_schema",
                 "mcp__plugin_agency_agency__execute"):
        assert tool in skill, f"missing {tool} in allowed-tools"


# ── then — using-agency skill ────────────────────────────────────────────────

@then("skills/using-agency/SKILL.md exists")
def _using_agency(manifest):
    assert "skills/using-agency/SKILL.md" in manifest


@then("the using-agency skill contains agency_welcome and intent_bootstrap")
def _using_agency_content(manifest):
    skill = manifest["skills/using-agency/SKILL.md"]
    assert "agency_welcome" in skill
    assert "intent_bootstrap" in skill


@then("the using-agency skill allows mcp__plugin_agency_agency__execute")
def _using_agency_allowed(manifest):
    assert "mcp__plugin_agency_agency__execute" in manifest["skills/using-agency/SKILL.md"]


# ── then — pruning ────────────────────────────────────────────────────────────

@then("the orphan wrapper is removed")
def _orphan_removed(prune_result):
    _, orphan = prune_result
    assert not orphan.exists(), f"orphan still exists: {orphan}"


@then("the real analyze-graph wrapper is still present")
def _real_still_present(prune_result):
    tmp_path, _ = prune_result
    assert (tmp_path / "bin" / "agency-analyze-graph").exists()


# ── then — dry run ────────────────────────────────────────────────────────────

@then("no files are written to the target")
def _dry_run_no_write(dry_run_result):
    rc, tmp_path, _ = dry_run_result
    assert rc == 0
    assert list(tmp_path.iterdir()) == []


@then("the dry-run output mentions SKILL.md or plugin.json")
def _dry_run_output(dry_run_result):
    _, _, captured = dry_run_result
    assert "plugin.json" in captured.out or "SKILL.md" in captured.out


# ── then — executable hooks ──────────────────────────────────────────────────

@then("hooks/session-start is executable")
def _hook_executable(write_result):
    tmp_path = write_result
    hook = tmp_path / "hooks" / "session-start"
    assert hook.exists()
    assert hook.stat().st_mode & stat.S_IXUSR


@then("hooks/run-hook.cmd is executable")
def _run_hook_executable(write_result):
    tmp_path = write_result
    hook = tmp_path / "hooks" / "run-hook.cmd"
    assert hook.exists()
    assert hook.stat().st_mode & stat.S_IXUSR


# ── then — polyglot wrapper ──────────────────────────────────────────────────

@then("hooks/run-hook.cmd starts with the polyglot marker")
def _polyglot_marker(manifest):
    wrapper = manifest["hooks/run-hook.cmd"]
    assert wrapper.startswith(": << 'CMDBLOCK'")


@then("hooks/run-hook.cmd contains exec bash")
def _polyglot_exec_bash(manifest):
    assert "exec bash" in manifest["hooks/run-hook.cmd"]


# ── then — plugin.json no hooks ──────────────────────────────────────────────

@then(".claude-plugin/plugin.json does not contain a top-level hooks key")
def _no_hooks_in_plugin_json(manifest):
    plugin_json = json.loads(manifest[".claude-plugin/plugin.json"])
    assert "hooks" not in plugin_json
