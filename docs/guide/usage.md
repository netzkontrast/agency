# Using the engine

The engine's whole public surface is three verbs — `search`, `get_schema`,
`execute` — exposed three isomorphic ways. Pick the surface that fits where you
are; the contract and the results are identical.

## The three surfaces

| Surface | Who uses it | How |
|---|---|---|
| **bash CLI** | a shell, a script, a bash-only agent | `python -m agency.cli …` |
| **MCP** | Claude Code / any MCP client | the `agency` MCP server (`search`/`get_schema`/`execute` tools) |
| **Skills** | Claude Code | the installed `help` skill + `/agency:help` command |

They are isomorphic by construction — the CLI drives the exact same code-mode
surface the MCP transport does, over the same graph.

## The loop: search → get_schema → execute

Everything is a graph that `SERVES` an **Intent**, so first bootstrap one (the CLI
prints its id):

```bash
python -m agency.cli --db g.db intent \
  --purpose "lint a skill" --deliverable "violations" --acceptance "clean"
# -> {"intent_id": "intent:abcd1234"}
```

**Discover** a tool by what you want to do:

```bash
python -m agency.cli --db g.db search "lint a skill"
# -> ranked match: capability_plugin_lint_skill
```

**Disclose** just the schema you'll use (context-mode — you load only this):

```bash
python -m agency.cli --db g.db get-schema capability_plugin_lint_skill
```

**Execute** a code block that chains tools in a sandbox and returns only a delta
(code-mode — many calls in, one small result out):

```bash
python -m agency.cli --db g.db execute --code '
  r = await call_tool("capability_plugin_lint_skill",
                      {"name": "fix-auth", "description": "Use when the auth test fails",
                       "intent_id": "intent:abcd1234"})
  return {"violations": len(r["violations"])}
'
```

Every command prints **one JSON document** to stdout (scriptable; errors come back
as `{"error": …}`, never a raw traceback).

## Why this is token-efficient

- **Code-mode:** chain ten tool calls inside one `execute` and only the final
  small value crosses back into context — not ten tool results.
- **Context-mode:** `search` returns a ranked pointer, `get_schema` returns one
  signature, a skill's `current()` returns one phase. You never hold the whole
  tool catalogue or a whole skill in the window. Heavy how-to is pulled on demand
  with `develop.reference`.

## Walking a discipline (skills)

Disciplines (tdd, debug, review, execute, …) are **Lifecycle templates** you walk
one phase at a time. Ask for the steps, then submit each phase's outputs; a hard
gate pauses until you confirm. List the steps:

```bash
python -m agency.cli --db g.db execute --code '
  return await call_tool("capability_develop_checklist",
                         {"discipline": "tdd", "intent_id": "intent:abcd1234"})
'
# -> steps: red -> green -> refactor -> verify (hard gate)
```

A phase **bound to a verb** executes for real when walked with the engine (e.g.
`review`'s dispatch phase drives `delegate.fan_out`); an unbound phase is a
document step you fill in by hand.

## In Claude Code

Install the plugin (see [getting-started.md](../getting-started.md)), then run
`/agency:help` to get the capability→verb map, or let Claude `search`/`execute`
against the MCP server directly. The bash recipes above map 1:1 to MCP tool calls.
