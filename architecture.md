<!-- agency-node: architecture-digest -->
# agency — architecture digest

Every recorded WH(Y) decision as a one-liner (13 across 5 layers), grouped by architecture layer. The decision IS what ships — **code is the final decision**; the full rationale, neglected alternatives and trade-offs live in [`docs/adr/`](docs/adr/). Rebuilt on spec-done via `adr.architecture(apply=True)`; emitted by the SessionStart hook.

## Datalayer
_how agency stores, versions and reconciles all state_

- project the hot typed entities (Intent, Agent, Invocation) onto SQLModel tables beside the graph
- keep-both reconciliation — never overwrite, the latest recorded_at wins on read
- a single bi-temporal GraphQLite graph as the one store for every concept

## Substrate
_the FastMCP engine and the wire contract every capability rides_

- run multi-step work in code-mode execute so chains stay inside the sandbox
- exactly three wire verbs — search, get_schema, execute
- every verb returns a typed ToolResult envelope with a severity taxonomy

## Capabilities
_how capabilities are authored, discovered and bounded_

- keep manage as capability-agnostic generic CRUD; domain verbs live in their own capability
- a capability is a self-registering folder under agency/capabilities/ (the drop-in bar)

## Lifecycle
_how stateful entities transition, with provenance_

- lifecycle machines are data (machines.json), not code
- ctx.lifecycle.move is the sole state writer; domain code never writes state directly

## Workflow
_the ADR-centred repo-development lifecycle (Spec 353 reconciliations)_

- thematic, living ADRs — a Document per architecture layer, extended inline
- specs flow through physical Plan/<state>/ folders mirrored by a SpecLifecycle node (keep-both)
- the ADR hinge — open to inprogress is blocked until the spec's decisions are approved
