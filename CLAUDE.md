# agency — Claude Code plugin

This repo **is** the `agency` plugin: **ONE FastMCP engine + ONE bi-temporal
GraphQLite graph**, designed as **four concepts** over one substrate. The repo
holds the **Concept, the Vision canon (v4), the Plan — and the first running
code** (`seed/`). The canon in `docs/vision/` is authoritative — **the canon
wins; code serves it.**

> **Supersedes v2.1.** The three-domain model (agentic / workflow / context) and
> capability/aspect/lazy-domaining are superseded. 5W1H is now a lens, not the
> architecture. Read [`docs/vision/CORE.md`](docs/vision/CORE.md) first.

## The model (detail: docs/vision/CORE.md)

Four concepts + one substrate (the Engine):

- **Intent** *(human-owned)* — purpose + acceptance, deliverable as an attribute
  (why/what merged). `capture · confirm · amend` (amend via supersede).
  Everything edges back via `SERVES`. See [specs/intent.md](docs/vision/specs/intent.md).
- **Capability** *(the craft — open set)* — invokable actions; verbs are
  capability-defined and role-tagged `act` / `transform` / `effect`. Discover via
  `<capability>.help`. See [specs/capability.md](docs/vision/specs/capability.md).
- **Lifecycle** *(state + gates)* — the task/agent state-machine. Write frame
  `open · move · close`; observe frame `read · find · check · watch`. A2A-aligned
  states; an agent is a Lifecycle parameterization; `COMPLETED ≠ done`. See
  [specs/lifecycle.md](docs/vision/specs/lifecycle.md).
- **Memory** *(the moat)* — one bi-temporal append-only graph; `record · link ·
  supersede` + `recall · find · validate`; `project(query, budget)`.
  Cross-concern provenance is one traversal. See [specs/memory.md](docs/vision/specs/memory.md).

**Engine** = the substrate, NOT a concept: the four-verb contract + `execute(code)`
code-mode. Guards (quality-score, loop-detection, compaction, `Slot`/quota) are
engine middleware. See [specs/engine.md](docs/vision/specs/engine.md).

## Skills are atomic, gated step-graphs

A skill is a **Lifecycle template: a graph of atomic Capability steps + Gates**,
walked via code-mode with progressive disclosure (only the next step's
instruction loads). Gates / intent-verification / askuser are `ctx.elicit` steps:
the Lifecycle pauses at `input-required`, the answer resumes it, the outcome is a
`Gate`. See [specs/skills-and-gates.md](docs/vision/specs/skills-and-gates.md).

## Naming (structure-first, self-describing)

Concepts: `intent`, `capability`, `lifecycle`, `memory`. Tool names
`<concept>_<capability>_<verb>` — underscores, ≤64 chars, no dots; the client
injects the `mcp__` prefix.

## Where to look

| Task | Open |
|---|---|
| The authoritative v4 model | `docs/vision/CORE.md` |
| Reading order for the canon | `docs/vision/README.md` |
| The model, narrative | `docs/vision/OVERVIEW.md` |
| The runtime + context-engineering commitments | `docs/vision/ARCHITECTURE.md` |
| A worked walkthrough (now executable in `seed/`) | `docs/vision/EXAMPLE.md` |
| The Engine substrate | `docs/vision/specs/engine.md` |
| A concept contract | `docs/vision/specs/{intent,capability,lifecycle,memory}.md` |
| Atomic step-graphs + elicitation | `docs/vision/specs/skills-and-gates.md` |
| Every skill/function mapped to v4 | `docs/vision/PORTING-ROADMAP.md` |
| Terms | `docs/vision/VOCABULARY.md` |
| Durable lessons | `docs/vision/LESSONS.md` |
| What's next | `docs/ROADMAP.md` |
| The running seed | `seed/README.md` |

## Scope discipline

The canon documents the full four-concept model. The first RUNNING code is
`seed/` — a proof-of-concept (not the shipped engine) that proves the moat,
code-mode chaining, and gate/elicitation. Everything else is **"specced — not
built."** Do not claim other code is implemented.

## How to work

- Design before code: `superpowers:brainstorming` → `superpowers:writing-plans`
  → `superpowers:executing-plans`. New skills via `superpowers:writing-skills`.
- Analysis / design / spec review: the `sc:` (superclaude) skills.
- Claude Code plugin / MCP / hook mechanics: the
  `superpowers-developing-for-claude-code` plugin.
- Add a capability = register its role-tagged verbs; its Lifecycle, gates, and
  Memory edges follow from invoking it (every `call_tool` records an Invocation
  that `SERVES` the Intent). No eager cross-concern scaffolding.

## Dev

- Keep `docs/vision/` authoritative; develop on the active feature branch.
- The seed runs on the real substrate: `cd seed && pip install -r requirements.txt && pytest -q`.
- Additive commits only — never rewrite history or force-push.
