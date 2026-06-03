# agency — Claude Code plugin

This repo IS the plugin: a **FastMCP engine + bi-temporal GraphQLite graph**,
exposing exactly **`search` · `get_schema` · `execute`** as the wire contract.
Four concepts (Intent · Capability · Lifecycle · Memory) on one substrate.

> **Read first:** [`docs/vision/GOALS.md`](docs/vision/GOALS.md) (why),
> [`docs/vision/CORE.md`](docs/vision/CORE.md) (canon),
> [`AGENTS.md`](AGENTS.md) (operational), [`AGENCY_PROTOCOL.md`](AGENCY_PROTOCOL.md)
> (remote-agent doctrine).

## Three rules for working in this repo

1. **Dogfood the engine — MCP-first when available.** When your harness has
   `mcp__plugin_agency_agency__{search,get_schema,execute}` (i.e. Claude
   Code with this plugin installed), use those tools directly — no
   subprocess hop, same per-project graph. The bash CLI (`python -m
   agency.cli execute` via `bin/agency`) is the fallback for Jules /
   no-MCP harnesses. Either surface chains tools inside the sandbox;
   only the return crosses back. Don't write code that bypasses the
   substrate.

2. **The graph is the store; files are a rendered view.** If you find yourself
   writing markdown that downstream code will parse, you have it backwards:
   `reflect.note(scope, text)` writes to the graph; render markdown on demand.
   Exceptions: canon/doctrine docs (CORE / AGENTS / AGENCY_PROTOCOL) serve
   external readers and stay as files.

3. **Decide before dispatching.** Walk the `dispatch-decision` skill
   (`skills/dispatch-decision/` + `delegate.ontology.skills`) before any
   subagent / Jules / future-MCP-client dispatch. The heuristic is the
   **eleven-signal** rule (Spec 040 §"eleven signals") with **two budget
   models** (local vs. Jules):
   - Work-shape signals: S1 (return tokens ≥ 5000), S2 (≥ 4 unfamiliar
     files), S3 (repeated exploration), S4 (≥ 3 parallel siblings),
     S5 (≥ 15 min wall-clock).
   - Role/safety: S6 (mutates — disqualifier without provenance),
     S7 (read-only amplifies), S8 (driver_hint as tie-breaker).
   - Cost-model: S9 (context_overlap ≥ 0.7 → re-load tax), S10
     (cache_warmth ≥ 0.6 → 10% cost), S11 (`local_budget_relevant=False`
     → Jules path; relaxes S1/S9/S10).
   Two disqualifiers run BEFORE positive scoring. Otherwise: any positive
   signal → dispatch (driver picked by the matrix); none → inline.

4. **Keep `TODO.md` current — MANDATORY in every spec-touching commit.**
   `TODO.md` in the repo root is the **binding spec status index** —
   verdict per spec (Shipped / Partial / Not started), one-line summary,
   blocker / next step. **No spec-touching commit ships without updating
   the corresponding row** — this is a HARD rule, not a soft preference.
   Failure to update IS a doctrine violation that future audits will
   flag. The same commit MUST update `TODO.md` when it:
   - ships a spec (status flip → Shipped — also flip Verdict-counts
     at top + add the new row entry to "Suggested next 5" if applicable),
   - makes meaningful progress on one (Not started → Partial; note WHAT
     is now done + WHAT remains in the "Blocker / Next step" column),
   - opens a new spec (add row),
   - closes / supersedes / cancels one (note in row),
   - renumbers (rare; only after a naming collision on merge).

   `TODO.md` ONLY carries the cross-spec roll-up — verdict + one-line +
   pointer. Per-spec deep state (test counts, file:line evidence, verbatim
   Done / Still / Refinement) lives in each `Plan/NNN-…/spec.md`'s
   `## Followup — Implementation Status (…)` section. No drift between
   the two; `TODO.md` rolls up, the Followup section grounds.

6. **Address drift before committing.** Spec 054 ships TWO guardrails
   for keeping the open-set substrate (capabilities, skills, ontology
   enums, extras) in sync across the ~9 places code/docs depend on
   the set:
   - **Inline tags.** `# AGENCY-DRIFT: <topic>` at every site where
     code reads a set/list that changes with the capability surface.
     `grep -rn AGENCY-DRIFT agency/ tests/ scripts/` lists them all.
   - **Drift detection script.** `scripts/check-drift` (called by CI on
     every PR) runs install dry-run, capability-test-gap check, and
     tag inventory. Exit 0 = clean; 1 = drift detected.
   When adding a new capability / extra / substrate tool, run
   `scripts/check-drift` BEFORE commit. Failure to do so is a doctrine
   violation; future audits flag it.

5. **Check cluster coherence before adding a verb / skill.** Spec 047
   (cluster-integration master) maps the 13 SDLC+meta clusters onto the
   agency surface. Every new verb / skill / substrate tool lands in one
   of those clusters. Before adding, find the cluster's section in
   `Plan/047-cluster-integration/spec.md` and check the integration
   pattern + coherence interactions — does your addition extend the
   pattern, or break it? When the cluster's integration plan grows past
   ~150 lines OR you trigger ≥ 3 named cross-cluster decisions, promote
   it to a standalone spec (Spec-015→017/018/019 precedent). The master
   is the source of truth UNTIL promotion; the promoted spec wins
   thereafter.

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
python -m pytest -q          # full default suite (slow — ~4 min sequential)
python -m pytest -q -n auto  # parallel via pytest-xdist (Spec 053; ~1 min on 4 cores)
python -m agency.install     # regen the plugin install when capabilities change
```

Spec 053 — fast local feedback:
```bash
scripts/test-cap analyze      # ~6s; tests/test_analyze_*.py only
scripts/test-cap research     # ~12s; tests/test_research_*.py only
scripts/test-cap "analyze or research"   # multi-marker via pytest expression
scripts/test-changed          # git-diff-driven: runs only the capabilities touched
```

CI (`.github/workflows/test.yml`):
- Push to main + every PR run `pytest -n auto -m "not e2e"`.
- Tagged builds (`v*`) ALSO run the E2E suite.
- Self-hosted install drift check still gates merge.

**Always activate the venv** (`. .venv/bin/activate`) before invoking
`python -m agency.cli` or `python -m pytest`. The bare `pytest` command
may resolve to a globally-installed pytest that does not see the venv's
deps (`graphqlite`, `fastmcp`) → silent collection errors. Use
`python -m pytest` to force venv-Python's site-packages.

- Feature branches; PRs target `main`; additive history; never rewrite or
  force-push.
- Add a capability = add a file (folder-per-capability when Spec 016 lands).
- Spec lifecycle: research → design → spec-panel → refine → IMPLEMENTATION-PLAN → TDD.
  Per-phase: RED → GREEN → green `python -m pytest -q` → commit → push.
- Doctrine evolves through dogfooding: surface lessons via
  `reflect.note(scope="observation", …)` — NOT new markdown files.
