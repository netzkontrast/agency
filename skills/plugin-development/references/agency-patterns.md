# Agency Engine Patterns

> Generic Claude Code plugin patterns live in [`common-patterns.md`](common-patterns.md).
> This file covers patterns specific to the agency engine — capabilities,
> the skill walker, boundary drivers, and substrate tools.

The agency plugin is itself an MCP-server-plus-skill plugin, but its inner
architecture has four reusable patterns that don't exist in the generic
Claude Code contract.

## Pattern 1: Add a capability (the "add a file" rule)

The whole point: drop one file in `agency/capabilities/<name>.py` (or a folder
for heavy capabilities) and the engine discovers, registers, and auto-wires
one MCP tool per verb. No engine edits, no wiring code.

### When to use

You have a coherent cluster of verbs (one or more `act`/`transform`/`effect`
operations) that share a domain and (optionally) ontology fragment.

### Three kinds

| Kind | Use for | Shape |
|---|---|---|
| `light` | ≤3 verbs, no ontology fragment | single file, no `OntologyExtension` |
| `medium` | own ontology fragment (nodes/enums/edges) | single file with `OntologyExtension` |
| `heavy` | vendored data, multiple sub-modules, JSON schema, skill walker | **folder-form**: `__init__.py` re-exports + `_main.py` + `_<concern>.py` + `data/` |

### Workflow (gated)

```python
# 1. mint an intent
r = await call_tool('intent_bootstrap', {
    'purpose': '...',
    'deliverable': 'agency/capabilities/<name>/ implemented + tests pass',
    'acceptance': 'plugin.lint_capability("<name>") ok=True in block mode',
})
iid = r['intent_id']

# 2. scaffold — emits a CAPABILITY-AUTHORING.md-compliant skeleton
await call_tool('capability_develop_scaffold_capability', {
    'name': '<name>', 'kind': 'light|medium|heavy', 'intent_id': iid,
})

# 3. hand-edit the scaffolded files (verbs, ontology fragment, tests)

# 4. lint must pass before commit
r = await call_tool('capability_plugin_lint_capability', {
    'name': '<name>', 'intent_id': iid,
})
assert r['ok'] is True   # block mode — five rule families
```

The scaffold writes `# agency-scaffold: v1` on line 1 of `_main.py`. The linter
reads that marker and switches from `warn` to `block` mode — every violation
is a real error.

### Deep ref

This is the surface of [`authoring-capabilities`](../../authoring-capabilities/SKILL.md)
— the deep skill. Read its SKILL.md before authoring anything non-trivial,
and `docs/vision/CAPABILITY-AUTHORING.md` for the doctrine.

## Pattern 2: Add a skill-walker (Lifecycle template)

A skill walker is an ordered phase graph the engine walks one phase at a time
(progressive disclosure), ending at a hard confirm gate. It lives **in the
capability's `OntologyExtension`** as a `skills={...}` entry, not as a separate
SKILL.md file.

### When to use

You need a multi-step authoring discipline (album concept, novel work concept,
spec authoring, …) where every phase emits a strict artefact and the final
phase is a hard human-confirmation gate.

### Shape

```python
# inside the capability's OntologyExtension
skills = {
    "work-concept": {
        "kind": "conceptualizer",
        "phases": [
            {"name": "foundation",    "schema": "premise"},
            {"name": "premise",       "schema": "premise"},
            {"name": "storyform",     "schema": "ncp"},
            {"name": "cast",          "schema": "work"},
            {"name": "confirmation",  "gate": "hard"},   # terminal
        ],
    },
}
```

The walker exposes the **current** phase only (token-frugal). On each phase
completion, the engine validates the emitted artefact against the named schema
and advances. The terminal `gate: "hard"` phase requires explicit human approval.

### Real example

- `examples/music.py` — `album-concept` (single-domain reference).
- `Plan/superseded/010-novel-domain/spec.md` — `work-concept` (multi-phase, gates).

## Pattern 3: Add a boundary driver

A driver is an injectable boundary that the engine plumbs to one `ctx.client`
or named slot. The default is real (production); tests inject a stub. **This
is how `act`/`effect` verbs reach the outside world WITHOUT importing it
themselves.**

### When to use

You need an external integration that:
- has a stable interface (good for stubbing),
- carries side effects you want auditable,
- belongs to a family with multiple implementations (Jules vs. local subagent vs. another remote-agent backend).

### Shape

```python
# in agency/capabilities/_<driver>.py (private to the engine, not a capability)
class MyDriverClient:
    def call(self, ...): ...
    # async if needed

# Engine knows to inject it on ctx.client when a verb says inject=("client",)
```

In `agency/engine.py:105` the registry is given an injector map:
```python
self.registry.injectors = {
    "client": lambda: self.jules_client,
    "vcs":    lambda: self.vcs_backend,
}
```

### Real example

- `agency/capabilities/_vcs.py::GitClient` — real `git`/`gh` subprocess.
- `agency/capabilities/_jules_api.py::JulesClient` — httpx against Jules.

Both default to the production form; both can be overridden via the `Engine`
constructor for tests:
```python
Engine(":memory:", jules_client=FakeJules(), vcs_backend=FakeGit())
```

### Open driver slot today

The engine has **no MCP-client driver** for talking to *other* MCP servers
over stdio/HTTP. That's a recognised gap (see the Spec-031 / Spec-032 line in
this branch). When that lands, it will be a new `client_mcp` injector.

## Pattern 4: Add a substrate tool (engine-side, not a capability)

A substrate tool is wired directly on the FastMCP server inside
`engine.py::Engine.build_mcp`, NOT on a capability. It does NOT carry the
`capability_*_*` name prefix. It does NOT require `intent_id` (substrate tools
are the **bootstrap** layer — there's no intent yet to SERVES against).

### When to use

Rare. Only when the tool is part of the bootstrap or introspection contract:

- `agency_welcome` — onboarding payload (no graph write)
- `agency_install` — scaffold `.agency/` + CLAUDE.md snippet
- `agency_doctor` — health check (no graph touch)
- `intent_bootstrap` — mint the first Intent (the one tool without a SERVES guard)
- `lifecycle_gate` — human-in-the-loop elicit gate (uses `ctx.elicit`)
- `memory_graph_provenance` — read-only graph traversal

### Shape

```python
# inside Engine.build_mcp, after capability auto-wire:
@mcp.tool
def my_substrate_tool(...) -> dict:
    """Use sparingly — substrate, not capability."""
    ...
```

### Discipline

If you find yourself adding a substrate tool, the question is: **could this be
a capability instead?** Almost always yes. Substrate is for tools that
**fundamentally can't** be capabilities (no intent, host-elicit, raw graph access).

## Composition: how the four patterns combine

A real authoring loop in the agency plugin typically uses all four:

1. **Substrate** — `agency_welcome` → `agency_install` → `intent_bootstrap` (mint).
2. **Capability** — `capability_develop_scaffold_capability` (scaffold the new cap).
3. **Skill-walker** — the new capability's `OntologyExtension.skills` carries a walker that the engine walks one phase at a time.
4. **Driver** — when one of the new capability's `effect` verbs needs to talk outside, it reaches `ctx.client` (real or stubbed).

This is **harness-in-harness** — the engine drives the authoring of more engine.
