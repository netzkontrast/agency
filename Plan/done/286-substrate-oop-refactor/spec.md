<!-- agency-node: document:df192abb -->
---
spec: 286
title: substrate-oop-refactor
status: done
state: done
depends_on: [040, 047, 053, 054]
clusters: [core, meta]
vision_goals: [4, 5, 6, 7]
---

<!-- doc-source: agency/engine.py agency/capability.py agency/memory.py agency/ontology.py -->

# Spec 286 — Substrate OOP Refactor (behavior-preserving)

> Umbrella spec. Renumbered from a working "284" to **286** to avoid the
> live `Plan/done/284-projected-enum-substrate` + `Plan/285-…` collision (PR #141).
> Companion to the approved plan in
> `~/.claude/plans/system-reminder-message-sent-at-sat-crystalline-ritchie.md`.

## Why (evidence + doctrine)

Five parallel analyses (3 Explore agents + SuperClaude `sc-refactoring-expert`
+ `sc-system-architect`) read the actual engine source and converged on the
same OOP debt. The substrate is sound at the open-set level (self-registering
`Capability` + `OntologyExtension` + `discover()`), but the spine + leaves have
accumulated smells that block clean extension:

- **Three engine god-methods.** `Engine.__init__` (`engine.py:191-340`, ~150
  LOC) holds **three representations of one boundary set** — the `self.<boundary>`
  attributes, a `DriverRegistry` rebuilt from them, and a parallel `injectors`
  table; `web_search` isn't even in the registry. `Engine.build_mcp`
  (`engine.py:464-960`, ~500 LOC) inlines 6-7 substrate tools as closures
  (`agency_doctor` alone ~200 LOC). `Registry.invoke` (`capability.py:582-686`,
  105 LOC) fuses inject-resolution, the SERVES guard, Invocation recording,
  call+exception capture, and ToolResult→side-effect processing.
- **Leaked graph abstraction.** ~18 sites reach raw `ctx.memory.g.query/.get_node`
  despite `ctx.neighbors` existing to retire exactly that.
- **God-class leaves.** `music/_main.py` (103 `@verb`), `novel/_main.py`
  (91 `@verb`, carries `# agency-accept-warn: surface_size`), plus
  `plugin`/`dogfood`/`prompt`.
- **Almost-abstracted duplication.** `_require_drv` unwrap idiom (73× in music),
  4 near-identical analyze subprocess wrappers, `_phase()` (3 copies), 30+
  hand-built skill dicts, the wire-unwrap rule duplicated across
  engine/registry/CLI, closed-set `frozenset` constants that want `StrEnum`
  (with `LifecycleState` duplicated between `ontology.py` and `lifecycle.py`).

Doctrine: this is a **rule-2 / rule-8** clean-up (derive over duplicate; assert
invariants, not frozen snapshots) delivered through the formal spec lifecycle.

## Decisions (user, 2026-06-13)

- **Full-system scope** (spine + ports + cross-cutting dedup + leaf god-class
  splits), behavior-preserving — **zero contract / wire / verb-name change**.
- **Formal spec lifecycle** — this umbrella + per-phase RED→GREEN→REFACTOR;
  full `pytest -n auto -m "not e2e"` on every migration; `scripts/check-drift`
  exit 0 + `TODO.md` row per spec-touching commit.
- **Coordinate with PR #141** — develop on its branch
  (`claude/agency-error-enum-fixes-13tpnf`) so there is one linear history;
  start with leaf refactors that do NOT touch the spine files #141's 284/285/103
  work actively owns (`capability.py`/`engine.py`/`memory.py`/`novel/`/
  `skill.py`/`develop`); move into the spine only after that work settles.

## Design — four phases (architectural sequencing)

Each phase stands on the ports the next depends on. Risk/leverage fuses the
architect's A1-A8 with the refactoring-expert's blast-radius scoring.

### Phase 0 — Foundational ports
- **A1 · `GraphStore` port** consumed by `Memory`; ban raw `.g` outside
  `memory.py` (one documented escape); migrate the ~18 raw-Cypher capability
  sites. **Preserves #141's `Memory.link` retry/backoff inside the port.**
- **A2 · Collapse boundary triplication** → `DriverRegistry` single source;
  delete the bespoke attrs + `injectors` dict; add `web_search`; `agency_doctor`
  reads uniform `readiness()`/`backend()`.
- **#10 · Test-fixture insulation** — migrate the ~141 tests that call
  `Engine(...)` directly onto the conftest fixtures (prereq for A2's signature).

### Phase 1 — Invocation spine
- **A3 · Decompose `Registry.invoke`** → `ParameterInjector` / `IntentGuard` /
  `InvocationRecorder` / `ResultProcessor`. **Carries #141's seams:** thread
  `param_enums` (Spec 284), preserve the `_host_ctx` ContextVar capture+`finally`
  reset (Spec 285-A), leave `_host_llm.complete_or_delegate`'s sample branch
  untouched, and **expose a clean post-mutation hook for Spec 283's renderer**
  (owner asked for option (a)). Post the hook signature on the #141 thread once
  it firms up.
- **A4 · Typed `Verb` value object** + consolidate the six metadata dataclasses
  toward one `CapabilitySkillProfile`; functional `Capability` = compiled output
  of `CapabilityBase`. Bridge with dict-compatible accessors.

### Phase 2 — Substrate + concept cleanup
- **A5 · Substrate tools as a registered set** (`requires_intent=False`);
  extract `agency_doctor`/`agency_welcome` out of `build_mcp` closures.
- **A7 · `WireEnvelope.unwrap()`** — one owner of the strip/re-wrap rule
  (engine `_wire`, registry, `cli._structured`); **incorporates #141's
  `{ok, error:{…severity…}}` failure shape**.
- **A7-concepts · shared `Gate` recorder** (unify `Lifecycle.move` / engine
  `lifecycle_gate` / `SkillRun.submit`); route concept services through the port.
- **A8 · close the `ctx.engine` escape hatch.**
- **#8 · closed-set → `StrEnum`** (`ROLES`/`LIFECYCLE_STATES`/`INTENT_OWNERS`
  + the duplicate `lifecycle.py` constants → one `LifecycleState`).

### Phase 3 — Leaf decomposition (highest churn, lowest architectural risk)
- **#1 · `SubprocessAnalyzer` Template Method** over ruff/bandit/radon. ✅ SHIPPED.
- **#2 · `Finding` → frozen dataclass + `FindingSeverity` enum.** (in progress)
- **#4 · `@requires_driver` decorator** replacing the 73× `_require_drv` unwrap.
- **#3+#6 · split music/novel/plugin/dogfood/prompt** into cluster mixins
  composed into ONE registered capability (lands the deferred 094-099 split).
- **#5 · `BoundaryConfig` parameter object** for `Engine.__init__` (after #10).
- **Capability-layer dedup** — shared `_phase()`, `SkillBuilder`,
  `record_and_serve()`, `budget_take()`; fold the verb return-shape
  inconsistency toward the typed A4/A7 envelope.

## Tests (RED → GREEN per slice)
Behavior-preservation is asserted via **invariants**, never frozen counts:
- "live verb count UNCHANGED across the music/novel cluster split"
- "no raw `.g` access outside `memory.py`"
- "`agency_doctor` field-set unchanged"; "MCP vs bash output identical"
  (`scripts/mcp_wire_smoke.py` + isomorphism tests)
- the 3-tool wire contract (`search`/`get_schema`/`execute`) byte-stable.
Each migration runs the FULL non-e2e suite (repo-wide invariant/inventory tests).

## Acceptance
- All four phases land behavior-preserving; full suite + `check-drift` + E2E
  (on tag) green; PR CI green before merge to `main`.
- Spec 283's renderer plugs into the Phase-1 `ResultProcessor` hook without
  re-touching `invoke`.
- No magic numbers / frozen snapshots introduced (rule 8).

## Followup — Implementation Status (2026-06-17)

- **Status: CODE-COMPLETE (acceptance + merge pending).** All four phases have
  landed behavior-preserving (the 2026-06-13 "spine NOT STARTED" note below is
  superseded — the spine work settled via #141 and merged to `main`). The
  binding cross-spec roll-up in `TODO.md` carries the per-phase commit ledger.
  Verified on this branch: full `pytest -n auto -m "not e2e"` → **1009 passed**
  (exit 0); `scripts/check-drift` exit 0; the 3-tool wire contract + capability
  surface byte-stable; A1 invariant holds (no raw `.g.query` in capabilities).
- **Phase 0** — A1 `GraphStore` port (no raw `.g` in capabilities), A2
  `DriverRegistry` single-source. **Phase 1** — A3 `Registry.invoke` → 4
  collaborators (`IntentGuard`/`ParameterInjector`/`InvocationRecorder`/
  `ResultProcessor`), A4 typed `Verb` value object. **Phase 2** — A5
  substrate-tools-as-set (`build_mcp` ~500→~96 LOC, `agency_doctor`/`welcome`
  extracted to `_substrate_tools.py`), A7 `WireEnvelope`, #8 closed-sets →
  `StrEnum`. **Phase 3** — all five god-classes split into cluster mixins
  (music/novel/plugin/dogfood/prompt), `@requires_driver`, `SubprocessAnalyzer`,
  `Finding`/`FindingSeverity` value object, cross-cap dedup.
- **A8 (soft per CORE v4) — escape-hatch closed in capabilities (2026-06-17,
  this branch).** The only ad-hoc `ctx.engine` reaches in capabilities were the
  two identical `getattr(self.ctx.engine, "_<domain>_production", False)` calls
  (novel + music cluster bases). Replaced with ONE typed
  `CapabilityContext.production_enabled(domain)` accessor; the remaining
  `ctx.engine` uses are the documented-legitimate ones (the long-lived
  `engine._jules_watcher` singleton, `develop.reload`). Behavior-preserving:
  241 music/novel/engine scenarios green post-change.
- **Deferred / optional (not gating Shipped):** A4 metadata-dataclass
  consolidation toward one `CapabilitySkillProfile`; #5 `BoundaryConfig`
  parameter object for `Engine.__init__`. **Done-When for Shipped:**
  Review-Partner Gherkin acceptance + clean-OOP review, then merge + CI green.
