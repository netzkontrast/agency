<!-- agency-node: architecture-digest -->
# agency — architecture digest

Every recorded WH(Y) decision as a one-liner (21 across 5 layers), grouped by architecture layer — each links to the spec that established it with one central sentence from that spec. Linked specs are **approved**: a spec reaches `/inprogress` (and later `/done`) only once its decisions clear the ADR hinge, so an `/inprogress` spec is an approved one still shipping its last slices. The decision IS what ships — **code is the final decision**; the full rationale, neglected alternatives and trade-offs live in [`docs/adr/`](docs/adr/). Refreshed on spec-done via `adr.architecture(apply=True)`; emitted by the SessionStart hook.

## Datalayer
_how agency stores, versions and reconciles all state_

- a single bi-temporal GraphQLite graph as the one store for every concept — [`Plan/inprogress/020-central-graph-db/spec.md`](Plan/inprogress/020-central-graph-db/spec.md)
  > "The graph IS the moat (GOALS.md goal #2; CORE.md Memory)"
- keep-both reconciliation — never overwrite, the latest recorded_at wins on read — [`Plan/inprogress/292-graph-markdown-interconnect/spec.md`](Plan/inprogress/292-graph-markdown-interconnect/spec.md)
- project the hot typed entities (Intent, Agent, Invocation) onto SQLModel tables beside the graph — [`Plan/inprogress/289-sqlmodel-entity-store/spec.md`](Plan/inprogress/289-sqlmodel-entity-store/spec.md)

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
- a capability's skill data derives from its docstring; an authored skill.yaml is the A6 override, not a committed file per capability — [`Plan/done/378-capability-skill-migration/spec.md`](Plan/done/378-capability-skill-migration/spec.md)
  > "The substrate (371–374) + enforcement (377) are inert until the existing 33 capabilities carry v2 `skill.yaml`"
- one per-type renderer renders every skill from its type template — no second render path — [`Plan/done/373-per-type-templates-renderer/spec.md`](Plan/done/373-per-type-templates-renderer/spec.md)
  > "One `render/capability-skill.md` shape for everything + a second `templates.SKILL_MD` path = generic output + a divergent path"
- the skill surface is bounded by a schema lint and a repo-wide self-containment discipline gate — [`Plan/done/377-skill-lint-enforcement/spec.md`](Plan/done/377-skill-lint-enforcement/spec.md)
  > "`lint_skill_doc` checks the description/triggers/example shape but passes thin bodies, stub sections, and missing phase instructions"
- render capability templates through a Jinja2 engine so their gates are programmatic — [`Plan/done/388-jinja-template-engine/spec.md`](Plan/done/388-jinja-template-engine/spec.md)
  > "The render surface today is two mechanisms welded together: 1"

## Lifecycle
_how stateful entities transition, with provenance_

- ctx.lifecycle.move is the sole state writer; domain code never writes state directly — [`Plan/inprogress/339-lifecycle-capability-write-frame/spec.md`](Plan/inprogress/339-lifecycle-capability-write-frame/spec.md)
- lifecycle machines are data (machines.json), not code — [`Plan/done/340-lifecycle-state-machine-transitions/spec.md`](Plan/done/340-lifecycle-state-machine-transitions/spec.md)
  > "`ontology.py:58 LifecycleState` constrains the *value* of `state`, but Spec 338 §Why item 2 documents the real defect — no transition is enforced"
- a skill is a typed phase-graph — six types with a per-type required core, and a phase is a first-class object with inline content — [`Plan/done/371-phase-skill-schema/spec.md`](Plan/done/371-phase-skill-schema/spec.md)
  > "Today a phase is `{index,name,produces,gate?,verbs?,sample?,…}` (no content) and a skill is `{name,description,body}` (enforces nothing)"
- the phase graph is the single source — the walk and the rendered file read one phase — [`Plan/done/372-phase-single-source/spec.md`](Plan/done/372-phase-single-source/spec.md)
  > "`SkillRun.current()` returns only `{index,name,produces,gate}` — the walking agent never receives `goal`/`instructions`/`example`"
- the four concepts each ship a committed pillar skill — [`Plan/done/375-pillar-skills/spec.md`](Plan/done/375-pillar-skills/spec.md)
  > "Agency emits a skill per capability but NONE for the concepts themselves"

## Workflow
_the ADR-centred repo-development lifecycle (Spec 353 reconciliations)_

- specs flow through physical Plan/<state>/ folders mirrored by a SpecLifecycle node (keep-both) — [`Plan/inprogress/357-spec-state-lifecycle/spec.md`](Plan/inprogress/357-spec-state-lifecycle/spec.md)
  > "Owner directive: *"Es gibt mehrere Verzeichnisse in Plan, dann neu: `/draft /open /inprogress /superseded /done`"
- the ADR hinge — open to inprogress is blocked until the spec's decisions are approved — [`Plan/done/358-workflow-capability/spec.md`](Plan/done/358-workflow-capability/spec.md)
  > "Owner directive: *"Ziel ist … einen Lifecycle für die Arbeit am Repo zu erstellen … beginnend mit Intent-Erfassung und Interview-Triage — Brainstorm und ggf"
- thematic, living ADRs — a Document per architecture layer, extended inline — [`Plan/done/354-adr-ontology-capability/spec.md`](Plan/done/354-adr-ontology-capability/spec.md)
  > "The `adr` repo (`/adr/specs/SPEC-001-A..E`) defines the *enhanced WH(Y) ADR* on paper"
- derive reference-doc fragments from live code via `<!-- derived -->` fences — [`Plan/done/389-derived-fence-reference-docs/spec.md`](Plan/done/389-derived-fence-reference-docs/spec.md)
  > "Spec 389 — Derived fences for hand-authored reference docs"
