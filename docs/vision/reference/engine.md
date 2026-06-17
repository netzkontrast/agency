# Engine — bootstrap, discovery, the substrate tools

<!-- doc-source: agency/engine.py -->
<!-- doc-hash: 5bea6367a1045f0b -->

`agency/engine.py` is the heart: it builds the graph, discovers capabilities, wires the
boundaries, and presents the three-tool wire contract.

## `Engine.__init__(path, …)`

Constructs an engine over a graph DB at `path` (`:memory:` for tests). Key parameters —
each is an injectable **boundary** with a real default, so tests substitute fakes:

| Param | Boundary | Default |
|---|---|---|
| `jules_client` | Jules REST | `JulesClient()` |
| `vcs_backend` | git/gh | `GitClient()` |
| `embedder` | semantic recall | resolved (`AGENCY_EMBEDDER` → BGE, else TF-IDF) |
| `web_search` | research | DuckDuckGo zero-config |
| `runner` | shell execution | the host runner |
| `token_counter` | token counting | `resolve_token_counter()` (count_tokens → tiktoken → proxy) |
| `skills_client` | Anthropic Skills API | `SkillsClient()` (lazy) |
| `drivers` | a `{name: driver}` override | merged onto the six above |
| `extra_capabilities` | out-of-tree caps | `[]` (e.g. `music`) |
| `_require_skill_doc` | bootstrap invariant bypass | `True` (probes pass `False`) |

Bootstrap order: resolve boundaries → build the `DriverRegistry` (Spec 002 — the six
boundaries unify into one named table; `Registry.injectors` is *derived* from it) →
`Ontology.core()` → discover + register capabilities, merging each `OntologyExtension`
strictly → validate each `SkillDoc`. **No graph writes happen here.**

## Capability discovery

`agency/capabilities/discover()` (`_capability_loader.py`) walks the `capabilities/`
package, finds every `CapabilityBase` subclass (folder-per-capability or single-file),
and compiles each to a `Capability` via `as_capability()`. The engine iterates
`discover() + extra_capabilities` and registers each. **Adding a folder is the only
step** to add a capability.

## The substrate tools (`build_mcp` / `call_tool`)

The engine exposes the wire contract:

- **`search`**, **`get_schema`**, **`execute`** — the three-tool contract.
- Bootstrap tools — `intent_bootstrap`, `agency_welcome`, `agency_doctor`,
  `lifecycle_gate`, `memory_graph_provenance`.
- In **code-mode** (`codemode=True`) the sandbox sees only `call_tool(name, args)` and
  chains verbs locally; in direct mode each verb is also a callable tool.

`agency_doctor` reports live backend health — the embedder, the `token_backend`
(count_tokens/tiktoken/proxy), the active `[analyze]` extras, drift indicators, and
whether `JULES_API_KEY` is set (never the key value).

## Where to look next

- The verb-invocation path + provenance recording: [capability-system.md](capability-system.md).
- The boundaries the engine builds: [drivers.md](drivers.md).
- What the engine emits for distribution: [install-cli.md](install-cli.md).
