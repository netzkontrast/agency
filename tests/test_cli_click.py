"""Spec 079 — Click CLI that mirrors every capability verb as a command.

The motivating user is a non-MCP agent (Jules/Codex/shell-only): instead of
hand-writing `execute --code 'await call_tool(...)'`, it runs
`agency <capability> <verb> --param … --intent-id …`. The per-verb commands are
auto-generated from the LIVE registry (no per-verb boilerplate) and route through
the same engine path; code-mode (`agency execute`) stays the canonical contract.

These tests lock: (1) the legacy subcommands still behave (the Click rewrite is
behaviour-preserving), (2) a generated verb command resolves + invokes its verb,
(3) `--intent-id` falls back to AGENCY_INTENT (Spec 018 Win 3), (4) discovery via
`--help` lists the live capability/verb surface, (5) dict params parse as JSON.
Expectations are computed from the live surface — no pinned verb counts.
"""
from __future__ import annotations

import json

import pytest

from agency.cli import main as cli_main


def _out(capsys):
    return capsys.readouterr().out.strip()


def _mint_intent(db, capsys):
    rc = cli_main(["--db", db, "intent", "--purpose", "p",
                   "--deliverable", "d", "--acceptance", "a"])
    assert rc == 0
    return json.loads(_out(capsys))["intent_id"]


# --- legacy subcommands still behave (behaviour-preserving rewrite) -----------

def test_legacy_welcome_still_works(tmp_path, capsys):
    rc = cli_main(["--db", str(tmp_path / "g.db"), "welcome"])
    out = json.loads(_out(capsys))
    assert rc == 0 and "capabilities" in out and "capability_tier" in out


def test_legacy_intent_and_provenance(tmp_path, capsys):
    db = str(tmp_path / "g.db")
    iid = _mint_intent(db, capsys)
    rc = cli_main(["--db", db, "provenance", iid])
    out = json.loads(_out(capsys))
    assert rc == 0 and "serves" in out


def test_legacy_execute_runs_code(tmp_path, capsys):
    db = str(tmp_path / "g.db")
    rc = cli_main(["--db", db, "execute", "--code", "return 6 * 7"])
    assert rc == 0 and json.loads(_out(capsys)) == 42


# --- the new per-verb command surface -----------------------------------------

def test_generated_verb_command_invokes_its_verb(tmp_path, capsys):
    """`agency develop checklist --discipline tdd` mirrors the verb and returns
    its wire delta (the unwrapped dict), routed through the engine."""
    db = str(tmp_path / "g.db")
    iid = _mint_intent(db, capsys)
    rc = cli_main(["--db", db, "develop", "checklist",
                   "--discipline", "tdd", "--intent-id", iid])
    out = json.loads(_out(capsys))
    assert rc == 0
    assert out.get("discipline") == "tdd" and out.get("steps")


def test_verb_command_records_provenance(tmp_path, capsys):
    """The generated command routes through registry.invoke — so the call is
    real provenance (an Invocation SERVES the intent), not a parallel path."""
    db = str(tmp_path / "g.db")
    iid = _mint_intent(db, capsys)
    cli_main(["--db", db, "develop", "checklist", "--discipline", "tdd",
              "--intent-id", iid])
    _out(capsys)
    # re-open the same DB and read provenance via the CLI
    rc = cli_main(["--db", db, "provenance", iid])
    prov = json.loads(_out(capsys))
    assert rc == 0
    assert any(s.get("capability") == "develop" for s in prov.get("serves", []))


def test_verb_command_intent_id_falls_back_to_env(tmp_path, capsys, monkeypatch):
    db = str(tmp_path / "g.db")
    iid = _mint_intent(db, capsys)
    monkeypatch.setenv("AGENCY_INTENT", iid)
    rc = cli_main(["--db", db, "develop", "checklist", "--discipline", "tdd"])
    out = json.loads(_out(capsys))
    assert rc == 0 and out.get("steps")


def test_dict_param_parses_as_json(tmp_path, capsys):
    """A verb param annotated dict (develop.skill_walk's `inputs`) accepts a
    JSON string and parses it before dispatch."""
    db = str(tmp_path / "g.db")
    iid = _mint_intent(db, capsys)
    inputs = json.dumps({"failing_test": "t", "implementation": "i",
                         "refactored": "r", "tests_pass": "ok"})
    rc = cli_main(["--db", db, "develop", "skill_walk", "--name", "tdd",
                   "--inputs", inputs, "--intent-id", iid])
    out = json.loads(_out(capsys))
    assert rc == 0
    assert out.get("status") == "input-required"   # pauses at the verify hard gate


# --- discovery parity via --help ----------------------------------------------

def test_root_help_lists_capability_groups(capsys):
    rc = cli_main(["--help"])
    out = capsys.readouterr().out
    # the live capability set appears as command groups
    assert "shell" in out and "develop" in out


def test_capability_help_lists_its_verbs(capsys):
    rc = cli_main(["shell", "--help"])
    out = capsys.readouterr().out
    for verb in ("run", "filter", "templates", "define"):
        assert verb in out, f"{verb} missing from `agency shell --help`"


def test_unknown_verb_is_a_clean_error(tmp_path, capsys):
    """An unknown verb under a real capability fails cleanly (non-zero rc),
    never a raw traceback."""
    rc = cli_main(["shell", "no-such-verb"])
    assert rc != 0
