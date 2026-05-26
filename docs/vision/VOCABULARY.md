---
slug: vision-vocabulary
type: vision
status: ready
summary: Canonical terms for the v4 four-concept model. One self-describing definition each. Defines Intent, Capability (act/transform/effect), Lifecycle (open·move·close + read·find·check·watch; agent as parameterization), Memory (record·link·supersede + recall·find·validate; project; provenance), the Engine substrate, engine guards, skills as atomic gated step-graphs, gates/elicit, 5W1H-as-lens, and the naming scheme.
---

# Vocabulary (v4)

> Authoritative model: [CORE.md](CORE.md).

| Term | Meaning |
|---|---|
| **Intent** | The human-owned root — a supersedable node carrying **purpose + acceptance**, with the **deliverable as an attribute** (why/what merged). `capture → confirm`, revised via `amend`. Every action edges back to it via `SERVES`. |
| **Capability** | The craft — the OPEN set. An invokable action whose verbs are capability-defined and **role-tagged**. Discover via `<capability>.help`. Invoking one records an Invocation in Memory. |
| **act / transform / effect** | The three capability roles. `act` = a craft write; `transform` = stateless compute, no side-effect; `effect` = an external side-effect. |
| **Lifecycle** | The task/agent state-machine. Write frame `open · move · close`; observe frame `read · find · check · watch`. States align with A2A tasks. |
| **Memory** | The moat — one bi-temporal, append-only graph holding every node and edge. Write frame `record · link · supersede`; read frame `recall · find · validate`; `project(query, budget)`. The only persistent state. |
| **Engine** | The substrate (NOT a concept) — one FastMCP server + one graph. **Code-mode IS the contract**: the public surface is exactly `search · get_schema · execute`. Capabilities self-register by reflection. The host. |
| **Verb frame** | The isomorphic frame the concepts share. Lifecycle: `open · move · close` (write) + `read · find · check · watch` (observe). Memory: `record · link · supersede` (write) + `recall · find · validate` (read). Intent: `capture · confirm · amend`. Capability verbs are open but role-tagged. |
| **Agent (as parameterization)** | An agent (the old "who") is a **Lifecycle parameterization** — an agent-session is a Lifecycle whose transitions/observers differ. A remote async agent inserts a `verify` step because `COMPLETED ≠ done`. Not a separate concept. |
| **Gate** | A Lifecycle step that pauses at `input-required` for a decision. A gate that needs a human is an `elicit` step; its outcome is recorded as a `Gate` node, `PASSED` (or blocked) by the Lifecycle. |
| **elicit / sample / report_progress** | Mid-flow interaction steps. `ctx.elicit(prompt)` asks the agent/human a one-line question and gets a typed answer (askuser-in-the-flow); `ctx.sample(...)` asks the caller's LLM; `ctx.report_progress(...)` streams. |
| **Skill (atomic step-graph)** | A **Lifecycle template: a graph of atomic Capability steps + Gates**, walked step-by-step via code-mode with progressive disclosure (only the next step's instruction loads). NOT a monolith loaded wholesale. |
| **SERVES** | The edge from every action node back to the Intent it serves. The spine of the provenance graph. |
| **provenance** | A single Memory traversal from an Intent returning every action that `SERVES` it, the agent that `PERFORMED_BY` it, the artefact it `PRODUCES`d, and the gate it `PASSED`. The moat — a flat SDK+memory-tool stack needs a multi-system join. |
| **project(query, budget)** | The read path into Memory: a ranked, token-budgeted, supersession-aware (`as_of`) projection that returns DELTAS, never raw history. How append-only memory coexists with compaction. |
| **bi-temporal / append-only / supersede** | Memory records valid-time and transaction-time and never overwrites; a corrected fact `supersede`s the prior one (`SUPERSEDED_BY` edge), which keeps its valid window for `as_of` reconstruction. |
| **Invocation** | A Memory node recording one capability call: its capability, verb, and role; edged `SERVES → intent` (+ `PERFORMED_BY → agent`, `PRODUCES → artefact`). |
| **Engine guards** | Cross-cutting engine **middleware** (NOT concepts): quality-score, loop-detection, compaction checkpoints, `Slot`/quota accounting. |
| **Code-mode** | The Engine hiding raw tools behind `search` / `get_schema` / `execute`; the agent chains tools in-sandbox and returns only deltas (the −98%-token pattern). The executable chain mirrors into the provenance graph. |
| **5W1H (a lens)** | The journalistic six-interrogative checklist. In v4 it is a **lens, not structure**. A Capability cross-section is an optional `(home, target)` **observation**, never a total function (total decomposition leaks). |
| **AOP escape hatch** | For genuinely cross-cutting capabilities (`verify`/QC, observability) with no natural home: model the capability across concepts rather than forcing a home. No generating function is required. |
| **Naming scheme** | Structure-first. Concepts: `intent`, `capability`, `lifecycle`, `memory`. Tool names `<concept>_<capability>_<verb>` — underscores, ≤64 chars, no dots; the client injects `mcp__`. |
| **A2A-aligned states** | Lifecycle states mirror A2A tasks: `submitted · working · input-required · completed · failed · canceled`. `COMPLETED ≠ done`. |
| **Frontmatter canon** | Required front-matter on canon docs and skills: `slug`, `type`, `status`, `summary`. Specs add a **Status** line ("specced; proven where noted"). |
