<!-- agency-node: architecture-digest -->
# agency — architecture digest

Every recorded WH(Y) decision as a one-liner (13 across 5 layers), grouped by architecture layer — each links to the spec that established it with one central sentence from that spec. The decision IS what ships — **code is the final decision**; the full rationale, neglected alternatives and trade-offs live in [`docs/adr/`](docs/adr/). Rebuilt on spec-done via `adr.architecture(apply=True)`; emitted by the SessionStart hook.

## Datalayer
_how agency stores, versions and reconciles all state_

- a single bi-temporal GraphQLite graph as the one store for every concept — [`Plan/inprogress/020-central-graph-db/spec.md`](Plan/inprogress/020-central-graph-db/spec.md)
  > "The graph IS the moat (GOALS.md goal #2; CORE.md Memory)"
- keep-both reconciliation — never overwrite, the latest recorded_at wins on read — [`Plan/inprogress/292-graph-markdown-interconnect/spec.md`](Plan/inprogress/292-graph-markdown-interconnect/spec.md)
  > "Spec 292 — Graph↔Markdown Interconnect · the Document as convergence artefact"
- project the hot typed entities (Intent, Agent, Invocation) onto SQLModel tables beside the graph — [`Plan/inprogress/289-sqlmodel-entity-store/spec.md`](Plan/inprogress/289-sqlmodel-entity-store/spec.md)
  > "Spec 289 — SQLModel typed entities for every graph data object"

## Substrate
_the FastMCP engine and the wire contract every capability rides_

- every verb returns a typed ToolResult envelope with a severity taxonomy — [`Plan/done/282-error-severity-taxonomy/spec.md`](Plan/done/282-error-severity-taxonomy/spec.md)
  > "Spec 282 — Error Severity Taxonomy"
- exactly three wire verbs — search, get_schema, execute — [`Plan/inprogress/001-toolresult-and-typed-errors/spec.md`](Plan/inprogress/001-toolresult-and-typed-errors/spec.md)
  > "The PR1 engine exposes a clean external surface (`search` · `get_schema` · `execute`; `agency/engine.py:1-16`), but internally every capability verb returns an ad-hoc dict, and there are at least…"
- run multi-step work in code-mode execute so chains stay inside the sandbox — [`Plan/inprogress/005-context-mode-and-token-economics/spec.md`](Plan/inprogress/005-context-mode-and-token-economics/spec.md)
  > "The engine already pays the boot token cost well: `Engine.build_mcp` wraps the server in FastMCP's `CodeMode()` transform (`agency/engine.py:91-95`), so the only tools the model sees at start are…"

## Capabilities
_how capabilities are authored, discovered and bounded_

- a capability is a self-registering folder under agency/capabilities/ (the drop-in bar) — [`Plan/inprogress/016-capability-authoring-doctrine/spec.md`](Plan/inprogress/016-capability-authoring-doctrine/spec.md)
  > "The Core canon (`docs/vision/CORE.md`) defines WHAT a capability is — an invokable action with role-tagged verbs, owning an ontology fragment, exposed isomorphically over MCP / Skills / bash CLI"
- keep manage as capability-agnostic generic CRUD; domain verbs live in their own capability — [`Plan/done/290-management-capability/spec.md`](Plan/done/290-management-capability/spec.md)
  > "(evidence + doctrine) An agent today cannot ask *"what is the current state — open intents, lifecycle status, research, artefacts — across the whole graph?"* without either raw Cypher…"

## Lifecycle
_how stateful entities transition, with provenance_

- ctx.lifecycle.move is the sole state writer; domain code never writes state directly — [`Plan/inprogress/339-lifecycle-capability-write-frame/spec.md`](Plan/inprogress/339-lifecycle-capability-write-frame/spec.md)
  > "Spec 338 §Architecture calls for a `lifecycle` capability that owns the CORE.md §3 verb frame"
- lifecycle machines are data (machines.json), not code — [`Plan/inprogress/340-lifecycle-state-machine-transitions/spec.md`](Plan/inprogress/340-lifecycle-state-machine-transitions/spec.md)
  > "`ontology.py:58 LifecycleState` constrains the *value* of `state`, but Spec 338 §Why item 2 documents the real defect — no transition is enforced"

## Workflow
_the ADR-centred repo-development lifecycle (Spec 353 reconciliations)_

- specs flow through physical Plan/<state>/ folders mirrored by a SpecLifecycle node (keep-both) — [`Plan/inprogress/357-spec-state-lifecycle/spec.md`](Plan/inprogress/357-spec-state-lifecycle/spec.md)
  > "Owner directive: *"Es gibt mehrere Verzeichnisse in Plan, dann neu: `/draft /open /inprogress /superseded /done`"
- the ADR hinge — open to inprogress is blocked until the spec's decisions are approved — [`Plan/done/358-workflow-capability/spec.md`](Plan/done/358-workflow-capability/spec.md)
  > "Owner directive: *"Ziel ist … einen Lifecycle für die Arbeit am Repo zu erstellen … beginnend mit Intent-Erfassung und Interview-Triage — Brainstorm und ggf"
- thematic, living ADRs — a Document per architecture layer, extended inline — [`Plan/done/354-adr-ontology-capability/spec.md`](Plan/done/354-adr-ontology-capability/spec.md)
  > "The `adr` repo (`/adr/specs/SPEC-001-A..E`) defines the *enhanced WH(Y) ADR* on paper"
