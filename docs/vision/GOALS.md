# Goals — the agency Claude Code plugin

The "why" in one page. The canon ([`CORE.md`](CORE.md)) is the "how"; the
operational docs ([`../../AGENTS.md`](../../AGENTS.md),
[`../../AGENCY_PROTOCOL.md`](../../AGENCY_PROTOCOL.md)) are the "do."

## Goals

1. **Token-efficient agentic loops.** Code-mode chains tool calls inside a
   sandbox; only the final delta crosses back. Progressive disclosure means
   the full tool list never loads into context. The dispatch-decision
   heuristic keeps work inline unless the task is genuinely context-heavy.

2. **Provenance as a free byproduct.** Every action records `SERVES` the
   intent in one bi-temporal append-only graph. Cross-concern queries are a
   single traversal. The graph IS the moat; there's no parallel tracking
   system to keep in sync.

3. **Agent-uniform lifecycle.** An agent IS a Lifecycle parameterization —
   Jules, Claude Code, future LLMs. Same hard-gate pattern; same `SERVES`
   edge; same recovery flow. No special-casing per agent.

4. **Open set of capabilities.** Adding a capability = adding a file (or
   folder). No central registry, no manifest. The engine `discover()`s by
   reflection. The contract is small enough that the open set stays
   canon-faithful.

5. **Code-mode IS the contract.** The entire wire surface is three verbs
   (`search` · `get_schema` · `execute`), exposed isomorphically over MCP,
   Skills, and a bash CLI. Discovery + invocation, nothing else.

6. **Doctrine evolves through dogfooding.** Running the system on itself
   surfaces real lessons; lessons land in the graph as `Reflection` nodes;
   nodes fold back into specs. The improvement loop closes.

7. **Graph is the store; files are a rendered view.** Working artefacts
   live in the graph. Markdown is for external readers (canon docs,
   PR descriptions, audit exports) — never the primary store.

8. **Harness-in-harness composition.** The agency is itself a Claude Code
   plugin; Jules dispatch is itself a sub-harness; the recursion is
   supported by the substrate. The plugin composes with the larger
   ecosystem rather than replacing it.

## Non-goals

- A flat four-verb surface (rejected — code-mode is the only contract).
- Fixed domains in the core (domains live in `examples/`).
- `manifest.toml`-style registration (reflection discovers; never reintroduce).
- Markdown as primary store (graph is the store).
- A separate `sessions.json` for Jules state (use `JulesSession` nodes).

## How the goals show up

| Goal | Code surface | Doctrine page |
|---|---|---|
| 1 — Token efficiency | `agency/engine.py` CodeMode wiring; `delegate.dispatch-decision` skill; tiered discovery (Spec 068) + name-budget lint (Spec 067) | [CORE.md](CORE.md) §"Engine" + §"Naming" |
| 2 — Provenance | `agency/memory.py` `_intent_chain` / `provenance` | [CORE.md](CORE.md) §"Memory" |
| 3 — Agent-uniform | `agency/skill.py` SkillRun; Codex C3 hard-gate persistence | [AGENCY_PROTOCOL.md](../../AGENCY_PROTOCOL.md) |
| 4 — Open set | `agency/capabilities/__init__.py` `discover()`; Spec 016 | [CAPABILITY-CLUSTERS.md](CAPABILITY-CLUSTERS.md) |
| 5 — Code-mode | `fastmcp.experimental.transforms.code_mode` + `agency/cli.py` | [CORE.md](CORE.md) §"Engine" |
| 6 — Dogfood loop | `dogfood.collect` + `reflect.batch_note` + Spec 014 | [AGENTS.md](../../AGENTS.md) |
| 7 — Graph-as-store | The `Reflection` node pattern; `reflect.batch_note` | [CLAUDE.md](../../CLAUDE.md) rule 2 |
| 8 — Harness-in-harness | `jules.dispatch` + the watcher; `delegate.fan_out` | [AGENCY_PROTOCOL.md](../../AGENCY_PROTOCOL.md) |

If a proposed change weakens one of these goals, it needs an explicit
trade-off argument in the spec body and panel review.
