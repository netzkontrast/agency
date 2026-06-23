<!-- agency-node: architecture-digest -->
# agency — architecture digest

Every recorded WH(Y) decision as a one-liner (16 across 5 layers), grouped by architecture layer — each links to the spec that established it with one central sentence from that spec. Linked specs are **approved**: a spec reaches `/inprogress` (and later `/done`) only once its decisions clear the ADR hinge, so an `/inprogress` spec is an approved one still shipping its last slices. The decision IS what ships — **code is the final decision**; the full rationale, neglected alternatives and trade-offs live in [`docs/adr/`](docs/adr/). Refreshed on spec-done via `adr.architecture(apply=True)`; emitted by the SessionStart hook.

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

## Workflow
_the ADR-centred repo-development lifecycle (Spec 353 reconciliations)_

- specs flow through physical Plan/<state>/ folders mirrored by a SpecLifecycle node (keep-both) — [`Plan/inprogress/357-spec-state-lifecycle/spec.md`](Plan/inprogress/357-spec-state-lifecycle/spec.md)
  > "Owner directive: *"Es gibt mehrere Verzeichnisse in Plan, dann neu: `/draft /open /inprogress /superseded /done`"
- the ADR hinge — open to inprogress is blocked until the spec's decisions are approved — [`Plan/done/358-workflow-capability/spec.md`](Plan/done/358-workflow-capability/spec.md)
  > "Owner directive: *"Ziel ist … einen Lifecycle für die Arbeit am Repo zu erstellen … beginnend mit Intent-Erfassung und Interview-Triage — Brainstorm und ggf"
- thematic, living ADRs — a Document per architecture layer, extended inline — [`Plan/done/354-adr-ontology-capability/spec.md`](Plan/done/354-adr-ontology-capability/spec.md)
  > "The `adr` repo (`/adr/specs/SPEC-001-A..E`) defines the *enhanced WH(Y) ADR* on paper"

## Capabilities

- D1 fix generator+substrate, not 36 skills by hand
- D2 get_schema renders nested object/array shapes
- D3 examples use real prefixed wire names + threaded intent_id
- D4 using-agency stays curated constant, gains naming rule
- Documentation generation mixes a deterministic template scaffold with MCP-sampled custom sections via document.compose
- Fix the generator + substrate, never hand-edit the 36 skills

## Lifecycle

- Lifecycle transitions are enforced by a data-driven A2A table with a typed IllegalTransition and a terminal floor; Lifecycle.move is the sole state writer, guarded statically by check-drift (B3)
