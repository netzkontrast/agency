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

7. **Regression testing lives in CI, not locally.** Per Spec 053 + user
   directive (2026-06-03):
   - Locally, run **only** focused slices (`scripts/test-cap <marker>`,
     `scripts/test-changed`) — typically < 30 seconds. Full-suite
     wall-clock is too expensive in a tight TDD loop.
   - The **full regression** (`pytest -n auto -m "not e2e"` + E2E on
     tag) runs in GitHub Actions on every PR + push to `main`. The
     workflow is `.github/workflows/test.yml`.
   - When pushing a feature branch, **always subscribe to PR activity**
     via `subscribe_pr_activity` so CI failures and review comments
     arrive as session notifications (no polling, no manual recheck).
     The subscription is the default, not opt-in.
   - If CI is red, the watching session investigates + fixes
     autonomously (per the GitHub Integration §"PR Activity Events"
     handling rules above). Push fixes; let CI re-run; reply only
     when the loop converges or a question genuinely needs the user.

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

8. **No hardcoded values — code (and tests) solve the problem, they don't
   gate a fixed solution.** Prefer COMPUTED / derived / discovered values
   over magic numbers and frozen snapshots. A test that pins a live-derived
   number (e.g. "the registry has exactly 73 verbs", "the payload is 1503
   tokens") breaks on every legitimate change and forces a hand-edit — it
   gates a fixed surface instead of guarding behaviour. Assert
   **invariants + relationships** (`wire_tok > bare_tok * 2.5`; "the known
   collisions are a SUBSET of live collisions"; "the substrate set equals
   the documented six") and compute expectations from the live source, not
   a constant. Genuine **tunable budgets** (a name-token limit, a payload
   byte cap) are fine — they are documented config with a rationale, not a
   snapshot of the current state; keep them few, named, and overridable.
   When you catch yourself updating a magic number to make a test pass, stop
   and make the test flexible instead.

## Field-tested heuristics (dogfooded — grounded in graph reflections)

Cheap checks that caught real failures during the 076→080 build-out. Pointers,
not prose — `analyze.graph` to read the originating reflections.

- **Dormant-surface audit.** Before trusting a pipeline, count its live triggers:
  `grep` the gate predicate, count satisfiers; **zero = dead code**. (031/032 emit
  shipped + tested but produced nothing — 0/15 caps declared `skill_doc`.)
- **Derivability audit.** Authored metadata that duplicates an existing source is
  drift waiting to happen — **derive it** (rule 2 applied to docstrings). SkillDocs
  derive from the module docstring (`Use when:`/`Triggers:`/`Red flags:`); the
  overview/briefs/example are free. No literal.
- **Enforcement blast-radius.** Before flipping a bootstrap invariant, `grep
  'Engine('` for synthetic-object call sites and ship a documented bypass
  (`_require_skill_doc=False` for probes/fixtures).
- **Sourcing-model first.** Decide the source-of-truth BEFORE any N>5 file
  migration — re-sourcing 15 caps twice is the tax for skipping it.
- **Full suite on a migration.** A migration touches repo-wide invariant/inventory
  tests (`test_naming_audit` substrate set), not just the changed slice. Run all of
  it before declaring green; CI is the net, not the first check.
- **Read the graph:** `analyze.graph` (census + typed listing) is the query
  surface — code-mode exposes only `call_tool`; `memory_graph_provenance` drills
  one intent. Don't claim to "read the graph" by reading intents you already know.

**The drop-in-capability bar.** Add a folder under `agency/capabilities/<name>/` —
verbs + ontology + a docstring that *derives* its Agent Skill — and **nothing
else**, and agency gains a complete, discoverable, walkable, CLI-exposed,
MCP-wired, emittable capability. If adding a capability needs an edit anywhere
else, that coupling is the bug to fix.

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
