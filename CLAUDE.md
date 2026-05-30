# agency — Claude Code plugin

This repo IS the plugin: a **FastMCP engine + bi-temporal GraphQLite graph**,
exposing exactly **`search` · `get_schema` · `execute`** as the wire contract.
Four concepts (Intent · Capability · Lifecycle · Memory) on one substrate.

> **Read first:** [`docs/vision/GOALS.md`](docs/vision/GOALS.md) (why),
> [`docs/vision/CORE.md`](docs/vision/CORE.md) (canon),
> [`AGENTS.md`](AGENTS.md) (operational), [`AGENCY_PROTOCOL.md`](AGENCY_PROTOCOL.md)
> (remote-agent doctrine).

## Three rules for working in this repo

1. **Dogfood the engine.** First instinct: `python -m agency.cli execute`
   chains tools inside the Monty sandbox; only the return crosses back. Direct
   `ctx.call` is fine inside a capability; orchestrator workflows chain via
   code-mode. Don't write code that bypasses the substrate.

2. **The graph is the store; files are a rendered view.** If you find yourself
   writing markdown that downstream code will parse, you have it backwards:
   `reflect.note(scope, text)` writes to the graph; render markdown on demand.
   Exceptions: canon/doctrine docs (CORE / AGENTS / AGENCY_PROTOCOL) serve
   external readers and stay as files.

3. **Decide before dispatching.** Walk `delegate.dispatch-decision` (skill)
   before dispatching to Jules. Dispatch only when context-heavy (≥ 4
   unfamiliar files / repeated exploration / ≥ 3 parallel siblings / ≥ 15 min
   wall-clock). Otherwise inline.

## Surface (discoverable; don't memorize)

Capabilities self-register from `agency/capabilities/`. Skills live on
`<capability>.ontology.skills` (Lifecycle templates, CORE.md:47-62).
`python -m agency.cli search <kw>` lists both. Jules needs `JULES_API_KEY`
at call time; see `AGENCY_PROTOCOL.md`.

Domain capabilities live in `examples/` (e.g. `examples/music.py`), loaded
via `Engine(..., extra_capabilities=[…])` — the bootstrapping harness stays
minimal.

## Dev

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q                    # 200+ passing
python -m agency.install     # regen the plugin install when capabilities change
```

- Feature branches; PRs target `main`; additive history; never rewrite or
  force-push.
- Add a capability = add a file (folder-per-capability when Spec 016 lands).
- Spec lifecycle: research → design → spec-panel → refine → IMPLEMENTATION-PLAN → TDD.
  Per-phase: RED → GREEN → green `pytest -q` → commit → push.
- Doctrine evolves through dogfooding: surface lessons via
  `reflect.note(scope="observation", …)` — NOT new markdown files.
