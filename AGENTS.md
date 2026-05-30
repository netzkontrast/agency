# AGENTS.md — agent guide (run · develop)

Two parts: **running** the engine from a bash-only shell (below), and
**developing** the plugin (at the end). Read [`docs/vision/CORE.md`](docs/vision/CORE.md)
for the model first.

> **Dispatching a remote async agent (Jules, etc.)?** Read
> [`AGENCY_PROTOCOL.md`](AGENCY_PROTOCOL.md) first. The doctrine: `COMPLETED ≠
> done`; verify via `git ls-remote`, never local HEAD; name the publish tool
> in the prompt; questions go through the blocking-ask tool only.

## Running the engine from bash only

This section is for **bash-only agents** (Jules, Codex, any LLM with a shell and no
MCP client / no Skill loader). You drive the engine with the **same contract** an
MCP client uses — **code-mode** — over a small CLI. No MCP, no skills, no special
integration. The isomorphism is proven in `tests/test_agency.py::test_isomorphism_mcp_equals_bash_cli`.

## Setup (once)

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"   # pyproject.toml is canonical; requirements.txt is legacy
```

## The contract: code-mode

State lives in one graph file you pass as `--db <path>` (it persists across calls).

```bash
# 0. bootstrap an Intent (everything you do SERVES one) — prints {"intent_id": "..."}
python -m agency.cli --db graph.db intent \
  --purpose "ship green CI" --deliverable "auth test passes" --acceptance "tests green"

# 1. discover what tools exist
python -m agency.cli --db graph.db search "lint skill"

# 2. get a tool's schema (params + returns)
python -m agency.cli --db graph.db get-schema capability_plugin_lint_skill

# 3. execute: write Python that chains tools and RETURNS ONLY A DELTA
python -m agency.cli --db graph.db execute --code '
r = await call_tool("capability_plugin_lint_skill", {"name": "Bad Name", "description": "does stuff", "intent_id": "intent:abc"})
return r["violations"] if isinstance(r, dict) and "violations" in r else r
'
# ...or pipe the code in on stdin:
echo 'return await call_tool("memory_graph_provenance", {"intent_id": "intent:abc"})' \
  | python -m agency.cli --db graph.db execute
```

Inside `execute`, `await call_tool(name, params)` is in scope and `return` yields
the result. Every command prints **one JSON document** to stdout.

## The rules (why it's token-efficient)

- **Chain tools inside one `execute` block.** Intermediate results stay in the
  sandbox; only what you `return` crosses back to you. Filter/aggregate before
  returning — return a small delta, never a dump.
- **Discover, don't guess:** `search` to find tools, `get-schema` before you call
  one. The full tool list is never loaded into your context.
- **State is the graph.** Everything you do is recorded as nodes + edges in
  `--db`; ask `memory_graph_provenance` to see what served an intent.

## Why this exists

`agency` exposes one engine three isomorphic ways — MCP tools, Skills, and this
bash CLI. A bash-only agent is therefore a first-class participant: you run the
*same* code-mode contract, against the *same* graph, with the *same* results as
any MCP client. That is what lets Jules (which has only a shell) drive the engine.

---

## Developing the plugin (dev hints)

**Add a capability = add a file.** Drop `agency/capabilities/<name>.py` with a
`CapabilityBase` subclass; the engine `discover()`s it and auto-wires one MCP tool
per `@verb` method. No registration code, no per-tool boilerplate.

```python
from ..capability import CapabilityBase, verb
from ..ontology import OntologyExtension

class GreetCapability(CapabilityBase):
    name = "greet"
    home = "capability"
    ontology = OntologyExtension(nodes={"Greeting": ["text"]})   # this cap OWNS its types

    @verb(role="act")
    def hello(self, who: str) -> dict:
        gid = self.ctx.record("Greeting", {"text": f"hi {who}"})  # services via self.ctx
        self.ctx.link(gid, self.ctx.intent_id, "SERVES")
        return {"result": gid}
```

**The one handle — `self.ctx` (`CapabilityContext`):** `ctx.memory`, `ctx.ontology`,
`ctx.render(template,…)` / `ctx.schema(name)` / `ctx.validate(label, props)`,
`ctx.call(cap, verb, …)` and `ctx.spawn(cap, verb, …)` to delegate to sibling
capabilities (recorded as provenance, depth-guarded), `ctx.intent_id`, `ctx.client`.
See [`docs/vision/specs/capability-base.md`](docs/vision/specs/capability-base.md).

**Stay CORE-faithful** ([`docs/vision/CORE.md`](docs/vision/CORE.md)):
- verbs are role-tagged `act` (writes an artefact) / `transform` (pure) / `effect`
  (touches the world);
- **code-mode is the only public contract** — never add a flat/four-verb surface;
- every call records an Invocation that `SERVES` the intent (don't bypass it);
- a capability **owns its ontology fragment** (nodes/edges/enums/skills/template-schemas),
  merged strictly onto the domain-agnostic core;
- never reintroduce a dropped idea (four-verb contract, fixed domains, `manifest.toml`).

**Skills** are Lifecycle templates (ordered phases + a hard gate) contributed via
a capability's `ontology.skills` and walked by `agency/skill.py` one phase at a time.

**Workflow & conventions:**
- Tests: `pytest -q`. **A complete, runnable implementation is the proof** — no
  mock-only "realish" tests; assert real provenance / a real skill walk.
- After adding/changing a capability, regenerate the self-hosted install:
  `python -m agency.install` (rewrites `.claude-plugin/plugin.json` + `skills/help` + `commands/`).
- Develop on the feature branch; **PRs target `main`**; additive commits, never
  force-push or rewrite history.
- Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`); one concern per commit.
- The growth plan is [`docs/EXTENSION-PLAN.md`](docs/EXTENSION-PLAN.md); the capability
  roadmap is [`docs/vision/CAPABILITY-CLUSTERS.md`](docs/vision/CAPABILITY-CLUSTERS.md).

## Remote-agent dispatch — tools to name explicitly

When dispatching a remote async agent (e.g. Jules) the prompt MUST name the
agent's tools by their canonical symbols — prose alone leaves work in the
agent's VM (the silent-fail mode that [`AGENCY_PROTOCOL.md`](AGENCY_PROTOCOL.md)
exists to close). The Jules canon (see `agency/capabilities/_jules_reference.md` §3):

- `pre_commit_instructions()` — mandatory pre-flight.
- **`submit(branch_name, commit_message, title, description)`** — the *one*
  tool that publishes work to remote. Always name it literally.
- `request_user_input(message)` — the **blocking** ask. NEVER use
  `message_user` for questions; it does not block.
- `replace_with_git_merge_diff` — preferred multi-line edit primitive
  (avoids JSON-escape failures on multiline code).
- `request_code_review()` — triggers the Jules Critic before `submit`.
- `reply_to_pr_comments(...)` — **required after `submit(...)`** when
  Jules is responding to a `@jules`-style review comment. Wakes the
  watching session via PR-comment webhook (see
  [`AGENCY_PROTOCOL.md`](AGENCY_PROTOCOL.md) §9).

Use **`jules.review_comment(body)`** to compose any agency-posted `@jules`
review comment — it appends the mandatory handshake tail so Jules always
receives the explicit `reply_to_pr_comments` instruction.

## Mode A (dogfood) vs Mode B (delegate)

- **Mode A** — Jules works directly in this repo. R+W here. AGENTS.md and
  `AGENCY_PROTOCOL.md` are inherited via Jules's lexical scoping (cloned into
  the VM with the repo).
- **Mode B** — the `agency` plugin is installed in *another project's*
  Claude Code; Jules works on that target repo. The dispatch preamble
  instructs Jules to `git clone --depth=1
  https://github.com/netzkontrast/agency.git ~/work/vendor/agency`
  **READ-ONLY**, then `read_file` both root docs before drafting any plan.
  Writes happen in the target repo only, never in the agency clone.

See `Plan/013-…/DESIGN.md` for the full split-ownership table.
