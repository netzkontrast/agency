"""Bash-callable engine — the L3 layer of the harness-in-harness ladder (Click).

A bash-only agent (Jules, Codex, a raw LLM with a shell) has no MCP client and no
Skill loader. This CLI exposes the engine over argv/stdin/stdout against a
PERSISTED graph (`--db`), so state survives across separate invocations. Two
surfaces, one engine:

1. **Code-mode** (`search` / `get-schema` / `execute`) — the canonical contract,
   isomorphic with the MCP transport: same engine, same results.
2. **Per-verb commands** (Spec 079) — every capability verb is mirrored as
   `agency <capability> <verb> --param … --intent-id …`, AUTO-GENERATED from the
   live registry (no per-verb boilerplate; adding a capability adds its commands
   for free). This lets a shell-only agent USE the capabilities directly instead
   of hand-writing `execute --code 'await call_tool(...)'`. The commands route
   through the SAME engine path (`call_tool` → `registry.invoke`) — same
   provenance, same SERVES guard — so they are a convenience layer, not a second
   contract. `--intent-id` defaults to `$AGENCY_INTENT` (Spec 018 Win 3).

    agency --db graph.db search "lint skill"
    agency --db graph.db shell run --command "git status" --intent-id intent:abc
    agency --db graph.db develop checklist --discipline tdd      # AGENCY_INTENT set
    echo 'return await call_tool(...)' | agency --db graph.db execute

Every command prints a single JSON document to stdout (token-safe, scriptable).
"""
from __future__ import annotations

import asyncio
import inspect
import json
import os
import sys

import click

from .engine import Engine


def _structured(result):
    sc = result.structured_content
    if isinstance(sc, dict):
        return sc.get("result", sc)
    if sc is not None:
        return sc
    # scalar returns (e.g. execute returning an int) arrive as text content
    if result.content:
        txt = result.content[0].text
        try:
            return json.loads(txt)
        except (ValueError, TypeError):
            return txt
    return None


# --- shared engine plumbing ---------------------------------------------------

def _resolve_db(db_value):
    """Spec 020 DB resolution (--db > AGENCY_DB > ./.agency/session.db > ~/.agency.db),
    ensuring the parent dir exists for fresh installs."""
    from ._db_path import resolve_db_path
    db_path = resolve_db_path(db_value)
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    return db_path


def _call_engine_tool(db_value, name, params, codemode=True):
    """Build an engine on the resolved DB, call ONE tool, return (result, rc).

    `codemode=True` exposes the code-mode contract (search/get-schema/execute);
    `codemode=False` wires each capability verb as a directly-callable tool (the
    per-verb command path). Always emits ONE JSON document, never a raw traceback
    (Spec 018 Win 7)."""
    db_path = _resolve_db(db_value)
    engine = Engine(db_path)
    mcp = engine.build_mcp(codemode=codemode)
    try:
        result = _structured(asyncio.run(mcp.call_tool(name, params)))
        rc = 0
    except Exception as e:                       # one JSON document on every path
        result = {"error": type(e).__name__, "message": str(e)}
        rc = 1
    finally:
        engine.memory.close()
    return result, rc


def _emit(result, rc):
    click.echo(json.dumps(result))
    return rc


def _db(ctx):
    return (ctx.obj or {}).get("db")


# --- the group + legacy subcommands (behaviour-preserving) --------------------

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--db", default=None,
              help="path to the graph DB (default: per Spec 020 resolution order)")
@click.pass_context
def cli(ctx, db):
    """agency — bash-callable engine (code-mode is the contract)."""
    ctx.ensure_object(dict)
    ctx.obj["db"] = db


@cli.command()
@click.argument("query")
@click.pass_context
def search(ctx, query):
    """Discover tools/capabilities."""
    return _emit(*_call_engine_tool(_db(ctx), "search", {"query": query}))


@cli.command(name="get-schema")
@click.argument("tools", nargs=-1, required=True)
@click.pass_context
def get_schema(ctx, tools):
    """Get the schema of one or more tools."""
    return _emit(*_call_engine_tool(_db(ctx), "get_schema", {"tools": list(tools)}))


@cli.command()
@click.option("--code", default=None, help="code to run (else read from stdin)")
@click.pass_context
def execute(ctx, code):
    """Run a code block that chains tools; returns a delta."""
    code = code if code is not None else sys.stdin.read()
    return _emit(*_call_engine_tool(_db(ctx), "execute", {"code": code}))


@cli.command()
@click.option("--purpose", required=True)
@click.option("--deliverable", required=True)
@click.option("--acceptance", required=True)
@click.pass_context
def intent(ctx, purpose, deliverable, acceptance):
    """Capture + confirm an Intent; prints its id.

    The one verb that bootstraps state without an existing intent, so a bash-only
    agent is self-sufficient (isomorphic with the `intent_bootstrap` MCP tool)."""
    db_path = _resolve_db(_db(ctx))
    engine = Engine(db_path)
    try:
        iid = engine.intent.capture_and_confirm(purpose, deliverable, acceptance)
        out, rc = {"intent_id": iid}, 0
    except Exception as e:
        out, rc = {"error": type(e).__name__, "message": str(e)}, 1
    finally:
        engine.memory.close()
    return _emit(out, rc)


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("root", required=False)
@click.option("--scaffold-db", is_flag=True,
              help="also create .agency/ + .gitattributes binary marker (Spec 020)")
@click.option("--scaffold-only", is_flag=True,
              help="scaffold .agency/ ONLY (do NOT write the plugin install surface)")
@click.option("--dry-run", is_flag=True, help="print would-write paths; touch nothing")
def install(root, scaffold_db, scaffold_only, dry_run):
    """Regenerate the plugin install (and optionally scaffold .agency/)."""
    from . import install as install_mod
    sub_argv: list[str] = []
    if root:
        sub_argv.append(root)
    if scaffold_db:
        sub_argv.append("--scaffold-db")
    if scaffold_only:
        sub_argv.append("--scaffold-only")
    if dry_run:
        sub_argv.append("--dry-run")
    return install_mod.main(sub_argv)


@cli.command()
@click.pass_context
def welcome(ctx):
    """Onboarding payload (live capability list + bootstrap example)."""
    return _emit(*_call_engine_tool(_db(ctx), "agency_welcome", {}))


@cli.command()
@click.pass_context
def doctor(ctx):
    """Health check (python/deps/DB/JULES_API_KEY)."""
    return _emit(*_call_engine_tool(_db(ctx), "agency_doctor", {}))


@cli.command()
@click.argument("intent_id")
@click.pass_context
def provenance(ctx, intent_id):
    """Cross-concern provenance for an intent; one graph traversal."""
    return _emit(*_call_engine_tool(_db(ctx), "memory_graph_provenance",
                                    {"intent_id": intent_id}))


@cli.group(invoke_without_command=True)
@click.pass_context
def hook(ctx):
    """Hook surface: Spec 076 event dispatch + Spec 280 self-test/uninstall.

    Default (no subcommand): route a Claude Code hook event (JSON on stdin)
    to the engine's handler. The unified `hooks/dispatch` entry pipes every
    event's stdin JSON to this command; the engine records it as provenance.
    No intent required.
    """
    if ctx.invoked_subcommand is not None:
        return
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except ValueError as e:
        return _emit({"error": "JSONDecodeError", "message": str(e)}, 1)
    return _emit(*_call_engine_tool(_db(ctx), "hook_event", {"event": event}))


@hook.command(name="self-test")
@click.option("--plugin-root", default=None,
              help="Plugin root containing hooks/. Default: derived from the "
                   "agency package location.")
@click.pass_context
def hook_self_test(ctx, plugin_root):                                  # noqa: ARG001
    """Spec 280 Slice 1.5 — verify the hook dispatcher path end-to-end.

    Runs each event with a synthetic JSON payload against `hooks/dispatch`
    + reports per-event {ok, stderr_hint?, exit_code}. Best-effort: a
    missing CLI or unparseable payload doesn't crash the test — we report
    the failure mode."""
    import subprocess
    if plugin_root is None:
        plugin_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
    dispatcher = os.path.join(plugin_root, "hooks", "dispatch")
    if not os.path.exists(dispatcher):
        return _emit(
            {"ok": False, "error": "DISPATCHER_MISSING",
             "path": dispatcher}, 2)
    cases: list[tuple[str, dict, str]] = [
        ("SessionStart",
         {"hook_event_name": "SessionStart", "session_id": "self-test"},
         ""),
        ("PreToolUse-Bash-git-commit",
         {"hook_event_name": "PreToolUse", "tool_name": "Bash",
          "tool_input": {"command": "git commit -m x"}},
         "branch.commit_smart"),
        ("PreToolUse-Bash-pytest",
         {"hook_event_name": "PreToolUse", "tool_name": "Bash",
          "tool_input": {"command": "pytest tests/"}},
         "develop.test"),
        ("PreToolUse-Edit-spec",
         {"hook_event_name": "PreToolUse", "tool_name": "Edit",
          "tool_input": {"file_path": "Plan/280-foo/spec.md"}},
         "dogfood.observe"),
        ("PostToolUse",
         {"hook_event_name": "PostToolUse", "tool_name": "Bash"},
         ""),
    ]
    results = []
    all_ok = True
    for name, payload, want_hint in cases:
        proc = subprocess.run(
            ["bash", dispatcher],
            input=json.dumps(payload),
            text=True, capture_output=True, timeout=10)
        ok = proc.returncode == 0
        hint_seen = want_hint in proc.stderr if want_hint else True
        case_ok = ok and hint_seen
        all_ok = all_ok and case_ok
        results.append({
            "case":      name,
            "exit_code": proc.returncode,
            "want_hint": want_hint,
            "hint_seen": hint_seen,
            "stderr":    (proc.stderr or "")[:240],
            "ok":        case_ok,
        })
    return _emit({"ok": all_ok, "results": results}, 0 if all_ok else 1)


@hook.command(name="wrap", context_settings={"ignore_unknown_options": True})
@click.option("--command", required=True,
              help="The foreign hook command to run verbatim.")
@click.pass_context
def hook_wrap(ctx, command):                                           # noqa: ARG001
    """Spec 280 — run a wrapped foreign hook with stdin passthrough.

    This is the wrap target the install side-effect points foreign-hook
    entries at. Behavior:

    1. Spawn `bash -c "<command>"` with the parent's stdin / stdout /
       stderr (so the foreign hook receives the Claude Code event
       payload verbatim and writes back the same way).
    2. Best-effort record an `Event(kind="hook-wrap-run", command,
       exit_code)` so the provenance moat covers the wrapped hook
       without requiring an active intent (Codex review on PR #138:
       hooks fire OUTSIDE any agency intent context).
    3. Exit with the wrapped command's exit code so the foreign hook's
       block/allow semantics are preserved (a sync foreign hook that
       used to exit 2 still blocks the tool).

    The wrap is NOT a public allowlist bypass (Codex P1): it's not
    exposed via `shell.run` and only fires for entries the install
    side-effect rewrote (which the user authored themselves).
    """
    import subprocess
    import os as _os
    proc = subprocess.run(
        ["bash", "-c", command],
        stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)

    # Best-effort Event recording — never crash the hook on failure.
    try:
        db_path = _resolve_db(_db(ctx))
        eng = Engine(db_path)
        try:
            eng.memory.record("Event", {
                "name":      "hook-wrap-run",
                "command":   command[:200],
                "exit_code": proc.returncode,
            })
        finally:
            eng.memory.close()
    except Exception:
        pass
    sys.exit(proc.returncode)


@hook.command(name="uninstall")
@click.option("--claude-settings-path", default=None,
              help="Path to `.claude/settings.json` (default: "
                   "$PWD/.claude/settings.json).")
@click.pass_context
def hook_uninstall(ctx, claude_settings_path):                         # noqa: ARG001
    """Spec 280 Slice 5 — restore `.claude/settings.json` from `.bak`.

    Reverses the install side-effect by moving `.bak` back to
    `settings.json`. Best-effort unwrap of foreign hooks (we ignored
    them on install if they had no `.bak`).
    """
    import shutil
    settings_path = (
        claude_settings_path
        or os.path.join(os.getcwd(), ".claude", "settings.json"))
    backup = settings_path + ".bak"
    if not os.path.exists(backup):
        return _emit(
            {"ok": False, "error": "NO_BACKUP",
             "path": backup,
             "hint": ("no .bak found — install was never run on this "
                      "settings file, or the .bak was deleted")},
            2)
    shutil.copyfile(backup, settings_path)
    return _emit({"ok": True, "restored_from": backup,
                   "settings_path": settings_path}, 0)


# --- Spec 079: auto-generated per-verb commands (mirror the live registry) -----

def _ann_kind(ann) -> str:
    """Classify a verb param's annotation into a CLI option kind. Handles BOTH
    real types and string annotations — capabilities use `from __future__ import
    annotations`, so `inspect.signature` yields strings ('dict', 'str', …)."""
    if ann is inspect.Parameter.empty:
        return "str"
    name = (ann if isinstance(ann, str) else getattr(ann, "__name__", "")).lower()
    if name == "bool":
        return "flag"
    if name == "int":
        return "int"
    if name.startswith("dict") or name.startswith("list"):
        return "json"
    return "str"


def _make_verb_command(cap_name, verb_name, spec):
    """Build a Click command that mirrors ONE capability verb. Options come from
    the verb's signature (minus injected params — the same elision `engine._wire`
    does); `--intent-id`/`--agent-id` are the wire params; dict/list params + a
    `--json` escape hatch parse as JSON."""
    fn = spec["fn"]
    inject = set(spec.get("inject", []))
    user_params = [p for n, p in inspect.signature(fn).parameters.items()
                   if n not in inject]
    brief = ((fn.__doc__ or "").strip().split("\n", 1)[0]
             or f"{cap_name}.{verb_name} ({spec.get('role', '')})")

    json_params = set()
    options = []
    for p in user_params:
        opt = "--" + p.name.replace("_", "-")
        required = p.default is inspect.Parameter.empty
        kind = _ann_kind(p.annotation)
        if kind == "flag":
            options.append(click.Option([opt], is_flag=True, default=False))
        elif kind == "int":
            options.append(click.Option([opt], type=int, required=required,
                                        default=None if required else p.default))
        elif kind == "json":
            json_params.add(p.name)
            options.append(click.Option([opt], type=str, required=required,
                                        default=None, help="JSON value"))
        else:
            options.append(click.Option([opt], type=str, required=required,
                                        default=None if required else p.default))
    options.append(click.Option(["--intent-id"], default="",
                                help="serving intent (defaults to $AGENCY_INTENT)"))
    options.append(click.Option(["--agent-id"], default="",
                                help="optional performer agent id"))
    has_json = "json" not in {p.name for p in user_params}
    if has_json:
        options.append(click.Option(["--json", "json_blob"], default="",
                                    help="extra params as a JSON object"))

    def callback(**kwargs):
        ctx = click.get_current_context()
        intent_id = kwargs.pop("intent_id", "")
        agent_id = kwargs.pop("agent_id", "")
        json_blob = kwargs.pop("json_blob", "") if has_json else ""
        call: dict = {}
        from click.core import ParameterSource
        for p in user_params:
            provided = ctx.get_parameter_source(p.name) == ParameterSource.COMMANDLINE
            if not provided and p.default is not inspect.Parameter.empty:
                continue                          # let the verb apply its own default
            v = kwargs.get(p.name)
            if v is None:
                continue
            if p.name in json_params:
                try:
                    v = json.loads(v)
                except ValueError as e:
                    return _emit({"error": "JSONDecodeError",
                                  "message": f"--{p.name.replace('_', '-')}: {e}"}, 1)
            call[p.name] = v
        if json_blob:
            try:
                call.update(json.loads(json_blob))
            except ValueError as e:
                return _emit({"error": "JSONDecodeError", "message": f"--json: {e}"}, 1)
        if intent_id:
            call["intent_id"] = intent_id
        if agent_id:
            call["agent_id"] = agent_id
        name = f"capability_{cap_name}_{verb_name}"
        return _emit(*_call_engine_tool(_db(ctx), name, call, codemode=False))

    return click.Command(name=verb_name, params=options, callback=callback,
                         help=brief, short_help=brief[:60])


def _add_capability_commands(group):
    """Mount one command group per capability (its verbs as subcommands), reading
    the LIVE registry via discover(). A capability whose name collides with a
    legacy command is skipped (the legacy command wins) — Spec 079 OQ-3."""
    from .capabilities import discover
    reserved = set(group.commands)
    for cap in discover():
        if cap.name in reserved:
            continue
        cap_group = click.Group(name=cap.name,
                                help=f"{cap.name} capability — {len(cap.verbs)} verb(s)")
        for verb_name, spec in sorted(cap.verbs.items()):
            cap_group.add_command(_make_verb_command(cap.name, verb_name, spec))
        group.add_command(cap_group)


# Build the per-verb surface ONCE at import time (discover() is already triggered
# by the Engine import above; re-adding on each main() call would duplicate).
_add_capability_commands(cli)


def main(argv: list[str] | None = None) -> int:
    """Entry point — returns an int rc (console-script + tests both call this)."""
    try:
        rv = cli.main(args=argv, standalone_mode=False)
        return rv if isinstance(rv, int) else 0
    except SystemExit as e:                       # --help / usage exit
        return e.code if isinstance(e.code, int) else 0
    except click.ClickException as e:             # usage/no-such-command → clean rc
        e.show()
        return e.exit_code


if __name__ == "__main__":
    sys.exit(main())
