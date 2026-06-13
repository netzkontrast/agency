# agency — Core (v4)

> See [`GOALS.md`](GOALS.md) for the **why**; this file is the **how**.
> If a change weakens a goal listed there, the spec body must carry the
> explicit trade-off argument.

> **5W1H is a lens, not the architecture** — the four concepts are the
> irreducible core. Names follow structure; the projection is an *observation*,
> not a mechanism.

## Four concepts + one substrate

**Substrate — the Engine.** One FastMCP server + one bi-temporal graph.
**Code-mode IS the contract** (lean — no four-verb surface): the public surface is
exactly `search` · `get_schema` · `execute`. The agent writes code in `execute`
that chains tools (`await call_tool(...)`); intermediate results stay in-sandbox,
only deltas cross into context. Tools are discovered via `search`. This one
contract is exposed **three isomorphic ways — MCP · Skills · a bash CLI** (the
harness-in-harness ladder) so a bash-only agent (Jules, no MCP/Skill) is a
first-class participant; proven in `agency/` (`AGENTS.md` + a bash↔MCP isomorphism
test). Cross-cutting guards (quality-score, loop-detection, compaction,
`Slot`/quota) are engine middleware, **not** concepts.

Verbs may wrap their delta as `{result: <delta>}` for engine-side ok-path
detection; the wire shape strips the wrap when `<delta>` is a dict (Spec
019). Docstrings describe the wire shape — see CAPABILITY-AUTHORING.md
§"Wire shape vs internal wrap".

**1. Intent** *(human-owned).* A supersedable node carrying **purpose +
acceptance**, with the **deliverable as an attribute** (why/what merged).
`capture → confirm`, revised via `supersede`. **Everything edges back to it via
`SERVES`.**

**2. Capability** *(the craft — open set).* An invokable action. Verbs are
capability-defined and **role-tagged**: `act` (craft write) · `transform`
(stateless compute) · `effect` (external side-effect). Discover via
`<capability>.help` (progressive disclosure ↔ `SKILL.md`).

**3. Lifecycle** *(state + gates).* The task/agent state-machine. Verb frame:
**`open · move · close`** (write) + **`read · find · check · watch`** (observe).
States align with A2A tasks (`submitted · working · input-required · completed ·
failed · canceled`). **An agent (the old "who") is a Lifecycle parameterization**
— an agent-session is a lifecycle whose transitions/observers differ (a remote
async agent inserts `verify`; `COMPLETED ≠ done`). Gates = `input-required` →
Intent re-entry.

**4. Memory** *(the moat).* One bi-temporal, append-only graph holding **every**
node — Intent, Capability invocations, Lifecycle states, artefacts — and their
edges (`SERVES`, `PRODUCES`, `DISPATCHED_TO`, `PRECEDES`, `SUPERSEDES`). Verbs:
`record · link · supersede` + `recall · find · validate`. `project(query,
budget)` → ranked, token-budgeted, supersession-aware (`as_of`) deltas. **The one
thing the SDK-native rival cannot match:** cross-concern provenance is a *single
traversal* — "every action that `SERVES` intent Q1, the agent that ran it, the
gate it passed."

## Four complete pillars — each concept a complete suite of code + tools

> **Core Vision (owner directive, 2026-06-13).** The four concepts are not just
> substrate *primitives* — the vision is that each becomes a **complete,
> first-class suite of code + tools** an agent (or human) can drive end to end.
> A pillar is "complete" when its **whole** surface — write *and* read, author
> *and* observe — is reachable through capability verbs, never hand-written
> graph queries. Today the **write/act** sides are mature; the **read/manage**
> sides are the least complete, and completing them is the current priority.

| Pillar | Write/act suite (mature) | Read/manage suite (the completion target) |
|---|---|---|
| **Intent** | `capture · confirm · supersede · chain` (parent/sub) · owners + the 8 critical-thinking methods (Spec 091) | query open intents, their acceptance status, the whole `SERVES` tree — "what are we trying to do, and are we there yet?" |
| **Capability** | author · `@verb` · the ontology + skill + verb triad · `discover()` | introspect the live registry — which verbs/skills/enums exist, their schemas, drift against the docs |
| **Lifecycle** | `open · move · close` · gates · phases · `skill_walk` · resume | **a management suite** — every in-flight task / skill / gate, what's blocked, what's next against acceptance |
| **Memory** | `record · link · supersede · project` | **a Management read-API over EVERY graph node type** — current state · open intents · research & claims · artefacts · reflections — *an API for all graph nodes*, no Cypher by hand |

**The Management capability** is the read-API the four pillars converge on: it
answers *"what is the current state — open intents, lifecycle status, research,
artefacts — across the whole graph?"* without an agent writing a single query.
It is how **Lifecycle + Memory** grow from substrate primitives into a complete
suite, and it generalizes today's partial surfaces — `analyze.graph` (census),
`memory.provenance` (one-intent traversal), and the planned `navigate`
read-projection — into **one coherent management API over all graph nodes**.
*Distance: those three partial surfaces exist; the unified, complete read-API
does not yet. Building it is the priority for completing the Memory + Lifecycle
pillars (see [`CAPABILITY-CLUSTERS.md`](CAPABILITY-CLUSTERS.md) `navigate`/management).*

## CapabilityContext — the verb's typed handle

Every verb that takes `ctx` (the default for class-form `CapabilityBase`
methods, or via `inject: ["ctx"]` for the functional form) receives a
single `CapabilityContext` object — a DELEGATOR over the engine's
services, never a parallel public surface. Eight fields:

| Field | Purpose | Example use |
|---|---|---|
| `memory` | The graph (Memory instance) | `ctx.memory.record(...)`, `ctx.memory.g.query(...)` |
| `ontology` | The merged effective ontology (read-only) | `ctx.ontology.skills["jules-fanout"]` |
| `registry` | The capability registry | `ctx.registry.invoke(...)` for cross-capability calls |
| `intent_id` | The SERVING intent (auto-injected per call) | every node `SERVES` this |
| `agent_id` | Optional performer (e.g. `agent:claude` / `agent:jules`) | provenance attribution |
| `client` | Boundary object the engine injects (e.g. `JulesClient`) | `self.ctx.client.create(...)` |
| `depth` | Recursion-depth guard for `spawn`/`call` | enforces `MAX_DEPTH=16` |
| `engine` | The owning Engine — for verbs that need engine-attached singletons (rare) | `self.ctx.engine._jules_watcher` |

See [`CAPABILITY-AUTHORING.md`](CAPABILITY-AUTHORING.md) for the
authoring contract that uses these — when each field is needed, when
it isn't, and the rules a verb's docstring must follow so the
provenance moat stays whole.

## Skills are atomic, gated, progressively-disclosed step-graphs

A "skill" is **not** a monolithic `SKILL.md` loaded wholesale. In v4 a skill is a
**Lifecycle template: a graph of atomic Capability steps + Gates**, walked
step-by-step via code-mode. Each step discloses only the *next* instruction
(`search → get_schema → execute`), so tokens are paid per atomic step, not for
the whole skill. The chain *is* an executable dataflow graph, and because every
`call_tool` records an Invocation, it mirrors itself into the provenance graph.

**Progressive disclosure applies to DISCOVERY, not just skill-walks.** GOALS #1
("the full tool list never loads into context") binds the *discovery* surface
too: `search` should disclose the **capability tier first** (≈14 macroskills, one
line each) and let the agent drill into a capability to load its verbs — the same
pay-per-tier principle as the skill walker, one level up. A flat dump of every
verb on every call is the anti-pattern (Spec 068 tiered-discovery).

**A skill name lives on TWO surfaces; they are converging.** It appears as both
the `ontology.skills` key (the walkable Lifecycle template) and the
`skills/<name>/SKILL.md` folder (the marketplace/human doc). These can diverge
today (`tdd` ↔ `test-driven-development`); the canonical direction is **one name
per skill across both surfaces** (Spec 071 skill-surface reconciliation).

**Gates / intent-verification / human-in-the-loop are `elicit` steps.** A step
can `ctx.elicit(prompt)` (ask the agent or human a one-line question and get a
typed answer), `ctx.sample(...)` (ask the caller's LLM), or `ctx.report_progress`
(stream). A gate that needs a human is just an `elicit` → the Lifecycle pauses at
`input-required`, the answer resumes it, the outcome is recorded as a `Gate`.
"askuser" is therefore not a special case — it is one node in the chain. All of
this is proven runnable in `agency/` (real `ctx.elicit` round-trip).

See [SKILL-CONTRACT.md](SKILL-CONTRACT.md) for the five-obligation contract every generated SKILL.md must satisfy (Spec 031).

## Schemas & templates (the typed/generative layer)

Both are ordinary nodes in **Memory**, forming a generate/validate pair:
- A **Schema** is the typed contract for a node / artefact / verb-params. It powers
  `validate` / `check`. **Design intent:** one schema per verb renders three ways
  (MCP `inputSchema`, the Skill's frontmatter, the bash CLI's arg parser) — the
  *isomorphism glue*. *(Not yet wired: in the engine the MCP `inputSchema` is derived
  by FastMCP from the verb signature; making the ontology schema the single source
  is the next step.)* In the engine today the ontology IS enforced on the graph
  (`record`/`link` reject missing fields, broken enums, and unknown edges).
- A **Template** is a parameterized generator. It powers `act`: a Capability
  produces an Artefact `DERIVED_FROM` the Template, which `VALIDATES_AGAINST` its
  Schema.

Proven runnable in `agency/` (a Template renders an Artefact that a Schema
validates; a missing field fails). This is how a real capability ports: its verbs
(Capability) + its schemas/templates (Memory) + its pipeline (Lifecycle).

## Dropped (and why)

- **Six-domain 5W1H** → a lens, not structure (journalistic checklist, not an
  execution theorem).
- **why/what as two domains** → merged into Intent (no workflow needs them split).
- **`(home,target)` projection as a total function** → demoted to an optional
  observation (Cyc/RDF/Ranganathan: total decomposition always leaks). No
  generating function; the AOP escape hatch is therefore unnecessary.
- **Three name renderers** → a serializer detail, not a top-level concern.

## Kept (panel-endorsed)

The **isomorphic verb frame**; the **one bi-temporal provenance graph +
`SERVES`**; **code-mode as the one lean contract** (exposed isomorphically over
MCP / Skills / bash); the **`COMPLETED ≠ done`** lesson.

## Naming

Structure-first. Concepts: `intent`, `capability`, `lifecycle`, `memory`.

**Two name surfaces — one disambiguated (the wire), one lean (code-mode).** The
**FastMCP wire name** is `<concept>_<capability>_<verb>` (underscores, ≤64, no
dots; the client injects `mcp__`) — kept, because it disambiguates when a host
loads several plugins. But the **code-mode `call_tool` surface** that `search`
advertises SHOULD expose the **bare verb** (`call_tool("dispatch_decision", …)`,
not the prefixed form): the `capability_<cap>_` prefix is pure repetition on
every discovery call (GOALS #1 — the Spec 049 audit measured 202 tokens of it
across the surface). The bare form is an **additive alias** on the code-mode
surface (alias-and-deprecate — never a wire break, Goal 5 holds); bare names must
stay unique across capabilities. Names carry a **token budget enforced by the
lint pipeline** (Spec 067), not a magic number frozen in canon.

> **Implementation status (Spec 069, cancelled 2026-06-06).** The bare alias is
> currently an *aspiration*, not shipped: FastMCP's CodeMode resolves
> `search`/`get_schema`/`call_tool` over one shared catalog, so a hidden-but-
> callable bare alias isn't possible without doubling the catalog or forking
> CodeMode. Since Spec 068 (tiered discovery) already captured the discovery
> token win, the prefix-rename was deferred; the `name_token_budget` /
> `bare_name_*` lint rules stand as documented WARNs. Revisit if CodeMode gains
> native alias support.

## Status: the installable `agency` plugin proves it (`agency/`)

> **Version-agnostic by design (Spec 072):** the live spec + test counts are the
> binding index [`TODO.md`](../../TODO.md), never frozen here — so this section
> states what is *proven*, not a count that drifts. (It once read "56 passing,
> next build delegate"; both long obsolete.)

v0.1 ships as an installable Claude Code plugin (this repo).
Built on the real substrate (graphqlite + fastmcp + Monty). Proven runnable:

- the **provenance moat** (one traversal);
- **two genuinely different capabilities** — a synchronous craft/compute
  (`plugin`) and the **REAL Jules agent** wired to the actual orchestrator
  (`jules_create`/`get`);
- **bi-temporal memory** (`as_of`); **`COMPLETED != done`** (real Jules `verify`:
  state completed AND a branch on origin);
- **code-mode is the contract** (`search`/`get_schema`/`execute`) — exposed
  isomorphically over MCP and a **bash CLI** (dogfooded over a bash-only session).
  The bash CLI ALSO mirrors every capability verb as a command (`agency <cap>
  <verb> …`, Spec 079) so a non-MCP agent reaches the capabilities directly — a
  **convenience layer** auto-generated from the live registry, routing through the
  same engine path; code-mode stays the canonical contract beneath it;
- **code-mode tool-chaining**; **gates via `elicit`**;
- **schemas & templates** (typed/generative layer);
- a **strictly enforced ontology** (`ontology.py`: per-node required-field schemas
  + an enumerated edge set + closed enums; `record`/`link`/`update` reject drift);
- a **micro-step skill walker** (`skill.py`): one phase at a time (progressive
  disclosure) through a **hard gate**, recording each phase as provenance;
- **capabilities self-register by reflection** — the engine `discover()`s every
  `Capability` in `capabilities/` and auto-wires one MCP tool per verb from the
  verb signature (`inspect.signature`): adding a capability is adding a file;
- the **plugin-development capability** — a complete port of the superpowers
  skill-creation (`writing-skills`, Iron Law enforced by phase ordering) + plugin
  authoring (manifest · SKILL.md · command · marketplace entry · CSO linter);
- a **self-hosted install** — the engine authors and validates its own
  `.claude-plugin/plugin.json` + `help` macroskill (mapping macroskills → verbs);
- an **extensible, capability-owned ontology** — the core defines a base; each
  capability contributes its own node types / skills / template-schemas
  (`Capability.ontology`), merged strictly onto the core and enforced in Memory;
- the **`reflect` capability** — durable, scope-tagged cross-session memory
  (`note`/`batch_note`/`recall`/`recall_semantic`/`search` over `Reflection`
  nodes the capability owns; Spec 045 added the semantic-recall verb with a
  pluggable TF-IDF/BGE embedder boundary).

The whole capability landscape of every installed plugin was surveyed, clustered,
and spec-paneled — see `CAPABILITY-CLUSTERS.md`. Verdict: the four concepts + the
engine absorb it all; the only net-new primitives were **`delegate`** (agent
fan-out + quota + join) and **`reflect`** (durable cross-session memory) — both
now built.

The capability set grows by dropping files into `capabilities/` (no wiring); the
live spec + test status is the binding index [`TODO.md`](../../TODO.md) — never a
count frozen here.
