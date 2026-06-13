# Goals — the agency Claude Code plugin

The "why" in one page. The canon ([`CORE.md`](CORE.md)) is the "how"; the
operational docs ([`../../AGENTS.md`](../../AGENTS.md),
[`../../AGENCY_PROTOCOL.md`](../../AGENCY_PROTOCOL.md)) are the "do."

> **These are aspirations, not a status board.** A goal is the direction the
> vision pulls toward — it *stands* whether or not the code has reached it yet.
> Read this page for **intent**, never for "what's shipped." Shipped state lives
> in the spec/status layer ([`../../TODO.md`](../../TODO.md) + the per-capability
> living specs), and it changes commit to commit; the goals do not. Where the
> current build still falls short of a goal, that gap is named in *italics* — not
> to demote the goal, but to keep the page honest about the distance left to run.

## Goals

1. **Token-efficient agentic loops.** Code-mode chains tool calls inside a
   sandbox so only the final delta crosses back; progressive disclosure keeps
   the full tool list out of context; the dispatch-decision heuristic keeps work
   inline unless a task is genuinely context-heavy.

2. **Provenance as a free byproduct.** Every action records `SERVES` the
   intent in one bi-temporal append-only graph, so cross-concern questions are a
   single traversal. The graph IS the moat — the aim is that there is never a
   parallel tracking system to keep in sync.

3. **Agent-uniform lifecycle.** An agent IS a Lifecycle parameterization —
   Jules, Claude Code, future LLMs — sharing one hard-gate pattern, one `SERVES`
   edge, one recovery flow. The aim is no special-casing per agent.

4. **Open set of capabilities.** Adding a capability should be *adding a folder*
   under `agency/capabilities/<name>/` — no central registry, no manifest; the
   engine `discover()`s by reflection. The contract stays small enough that the
   open set remains canon-faithful.
   *Distance: a few capabilities still live as bare modules (`intent.py`,
   `shell.py`, `skills.py`) rather than folders; the folder-per-capability
   invariant is the target, not yet uniform.*

5. **Code-mode IS the contract.** The whole wire surface is three verbs —
   `search` · `get_schema` · `execute` — reached identically over MCP and the
   bash CLI; discovery + invocation, nothing else.
   *Distance: a bare-name verb alias was explored and **cancelled** (Spec 069);
   the contract is deliberately the three verbs, and per-verb tools are reached
   through `execute`, not aliased at the top level.*

6. **Doctrine evolves through dogfooding.** Running the system on itself surfaces
   real lessons; lessons land in the graph as `Reflection` nodes; the aim is that
   they **fold back into the specs** so the improvement loop closes.
   *Distance: today the fold-back is manual — the automatic
   observation→spec-amendment path (Spec 014) is **not yet built**, so the loop
   is closed by hand, not by the engine. Closing it for real is still ahead.*

7. **Graph is the store; files are a rendered view.** Working artefacts belong in
   the graph; markdown is rendered on demand for external readers.
   *Bounded exception (intentional, not a contradiction): the canon/doctrine docs
   themselves — `CORE.md`, `AGENTS.md`, `AGENCY_PROTOCOL.md`, this file — live as
   files because their audience is humans outside the graph. The aim holds for
   **working** artefacts; the canon is the named carve-out (CLAUDE.md rule 2).*

8. **Harness-in-harness composition.** The agency is itself a Claude Code plugin;
   Jules dispatch is itself a sub-harness; the substrate supports the recursion.
   The aim is to compose with the larger ecosystem rather than replace it.

## Non-goals

- A flat four-verb surface (rejected — code-mode is the only contract).
- Fixed domains in the core (domains live in `examples/`).
- `manifest.toml`-style registration (reflection discovers; never reintroduce).
- Markdown as primary store for working artefacts (the graph is the store).
- A separate `sessions.json` for Jules state (use `JulesSession` nodes).

## How the goals show up (and where they fall short)

| Goal | Code surface | Status today |
|---|---|---|
| 1 — Token efficiency | `agency/engine.py` CodeMode wiring; `delegate.dispatch-decision`; tiered discovery (068) + name-budget lint (067) | Realized |
| 2 — Provenance | `agency/memory.py` `_intent_chain` / `provenance` | Realized |
| 3 — Agent-uniform | `agency/skill.py` SkillRun; hard-gate persistence | Realized |
| 4 — Open set | `agency/capabilities/__init__.py` `discover()`; Spec 016 | Mostly — 3 caps still bare modules |
| 5 — Code-mode | `fastmcp…code_mode` + `agency/cli.py` | Realized (bare-name alias cancelled, 069) |
| 6 — Dogfood loop | `dogfood.collect` + `reflect.batch_note` | **Partial — fold-back is manual; Spec 014 unbuilt** |
| 7 — Graph-as-store | the `Reflection` node pattern | Realized for working artefacts; canon docs are the named exception |
| 8 — Harness-in-harness | `jules.dispatch` + the watcher; `delegate.fan_out` | Realized |

If a proposed change weakens one of these goals, it needs an explicit
trade-off argument in the spec body and panel review.
