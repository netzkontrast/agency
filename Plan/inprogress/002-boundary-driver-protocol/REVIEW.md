# REVIEW — Spec 002: Generic `Boundary`/`Driver` Protocol Family + `DriverRegistry`

Spec-panel critique. Panel personas: **Protocol/Type Designer** (Hejlsberg-style),
**Architecture/Boundaries** (Cockburn ports-and-adapters), **Test Seam Owner**
(Feathers), **Source Faithfulness** auditor. Verdict is the panel's consensus.

---

## Verdict: REQUEST CHANGES (sound motivation, wrong load-bearing default + a terminology collision)

The problem is real and well-evidenced: `FINDINGS.md:16` correctly names the two
boundaries as "excellent injections… not unified," and the engine genuinely does pay
the four-part tax the spec lists (new Protocol + new `Engine.__init__` kwarg + new
`Registry.injectors` key + bespoke accessor) for every external cluster
(`engine.py:40-42,55-56`). A named `DriverRegistry` reached via `ctx.get_driver(name)`
is the right shape to retire that tax, and the spec is correctly *additive* in intent.

But the spec leaves its **single load-bearing decision (Open Q-1: uniform
`dispatch(op, **kw)` vs. typed named methods) unresolved**, and the evidence it cites
actually argues *against* the uniform-dispatch framing it leans toward. It also reuses
the word "driver" in a way that **collides with an existing, different meaning** in
`delegate`/`subagent`, which the spec under-acknowledges. These two must be resolved
before any code lands, because they change the Protocol's public shape and the
`delegate` blast radius respectively.

---

## The load-bearing question: uniform `dispatch(op, **kw)` vs. typed named methods

**Recommendation: Option B — keep typed named methods; `Driver` is a marker
`Boundary`. Do NOT adopt a uniform `dispatch(op, **kw)`.** The spec frames this as
genuinely open; the evidence does not support that even-handedness.

1. **The cited prior art argues the opposite of what the spec implies.** The spec
   leans on `the-agency-system`'s 0004-five-handler-domains as "the precedent for one
   routing table over many domains" (spec `:62-64`, `:121`). Read at source, ADR-0004
   is a *fixed taxonomy of domains*, and each domain exposes **typed named handler
   functions**, not a single `dispatch(op)`. The real tool clusters the spec names as
   the motivating future drivers — `bitwize-music` mastering/audio/db — are, in the
   reference repo, directories of *named* functions
   (`servers/agency-mcp/src/agency_mcp/tools/mastering/{analyze_tracks,master_tracks,qc_tracks,…}.py`),
   registered via `register_<domain>_handlers(mcp)`
   (`the-agency-system/servers/agency-mcp/src/agency_mcp/server.py:55-85`). There is
   **no `dispatch(op, **kw)` anywhere** in `servers/` (grep returns nothing). So the
   precedent the spec cites for "one uniform entry point" is in fact a precedent for
   "named methods + a per-domain registration function." Option B is the faithful
   reading; Option A is a misreading of the cited ADR.

2. **The local boundaries are richly typed and that typing is load-bearing.**
   `JulesBackend` has seven differently-signed methods
   (`jules.py:25-34`: `create(prompt,source,starting_branch)`, `get(session)`,
   `list(page_size,page_token)`, `activities(session,page_size,only_kinds)`, …) and
   `VCSBackend` has four (`_vcs.py:18-23`). A uniform `dispatch(op: str, **kw)` erases
   every one of these signatures into a stringly-typed `op` + opaque `**kw` — which is
   *exactly the "stringly-typed" smell* Spec 001 exists to eliminate (`FINDINGS.md:18`,
   Spec 001 `:58-64`). Adopting Option A in Spec 002 would re-introduce, at the driver
   seam, the disease Spec 001 cures at the result seam. That is incoherent across the
   wave.

3. **Option A buys nothing the registry needs.** The registry's value is *named
   lookup + uniform result type* (`ToolResult`), not a uniform *method name*. A marker
   `Boundary`/`Driver` Protocol + `ctx.get_driver("jules").create(...)` gives the host
   a uniform plug-in seam while the *capability* keeps full typed knowledge of its own
   boundary. The only thing Option A adds is verb→op string-mapping boilerplate (which
   the spec's own Option-A sketch at `:264-270` demonstrates: `dispatch("create",
   prompt=…)` — strictly worse than `create(prompt=…)`).

4. **`PROPOSAL.md §2` is a 6-line sketch, not a constraint.** It does show
   `driver.dispatch({...})`, but it is explicitly a "Python Sketch" with `pass` bodies
   and an `async` signature that contradicts the sync reality (Open Q-6). It should not
   outweigh the two concrete, typed Protocols already in the tree and the actual
   structure of the reference repo it cites.

**Therefore the spec's framing is wrong:** it presents Q-1 as a balanced A/B choice and
hedges the `Driver` Protocol body (`:154` "shape per Open Q-1"). The evidence is
lopsided toward B. The spec should *resolve* Q-1 to B and demote it from "load-bearing
open question" to "decided: B, with rationale." `Driver` becomes a marker Protocol
(possibly with an optional `name`/`describe()` for registry introspection), and the
uniform contract that matters is the *return type* (`ToolResult`), inherited from
Spec 001 — not the method name.

---

## Source-grounded corrections (path:line)

- **`jules.py` line citations are off by ~6.** The spec repeatedly cites
  `jules.py:25-34` for the `JulesBackend` Protocol and `:37-69` for `JulesClient` and
  `:76-77`/`:76-82` for `_backend()`. Verified against source: `JulesBackend` is
  `jules.py:25-34` ✓; `JulesClient` is `:37-69` ✓; `_backend()` is `:76-77` ✓;
  `dispatch` is `:79-89`. These are **correct**. (No correction — confirmed accurate.)

- **`engine.py:67` cited for the `inject` convention (Open Q-2) is wrong.** The spec
  says "The `inject` convention (`engine.py:67`, `capability.py:103`)". `engine.py:67`
  is inside `_wire` computing `user_params` (`:66-67`); the `inject` *resolution* lives
  in `capability.py:149-163` (`Registry.invoke`) and the verb-side declaration in
  `capability.py:103` (`_wrap_method` returning `"inject": ["ctx"] + meta["inject"]`)
  and `capability.py:84-90` (the `verb()` decorator). Cite `capability.py:149-163`, not
  `engine.py:67`.

- **The `CapabilityContext` field-line citation drifts.** Spec cites
  `capability.py:35-47` for the context dataclass and `:152-163` / `:152-157` /
  `:144-163` for the inject branch. Source: the dataclass is `capability.py:35-47` ✓
  (fields end at `MAX_DEPTH` `:47`); the `ctx` injection branch is `capability.py:152-157`
  ✓ inside `invoke` `:144-180`. Correct. But the spec's "After" `CapabilityContext`
  sketch (`:181-195`) adds `drivers` *after* `client` and **defaults it to `None`**
  while typing it `"DriverRegistry"` (not `Optional`) — a type lie that will bite
  `get_driver` with `AttributeError: 'NoneType'`. Either type it
  `Optional["DriverRegistry"] = None` and guard, or (better) make `Registry.invoke`
  *always* pass a real (possibly empty) `DriverRegistry` so the field is never `None`.

- **`delegate.fan_out` "driver" already means something else — the spec's `:99-103`
  Done-When item is built on a terminology collision.** In the live tree, `fan_out`'s
  `driver`/`driver_verb` are a **capability name + verb** resolved via
  `ctx.spawn(driver, driver_verb, **item)` against the *capability* Registry
  (`delegate.py:29,40,52`), and `subagent.develop` calls it that way with
  `driver="jules", driver_verb="dispatch"` (`subagent.py:23-28`). The spec's new
  `DriverRegistry` introduces a *second, different* "driver" (a registered `Driver`
  object). Done-When `:99-103` says a registered `Driver` should become "a first-class
  delegation target," but `fan_out`'s whole contract (`delegate.py:48-54`) is to open a
  **child Lifecycle** that `SERVES` the intent, is `DISPATCHED_TO` an agent, and
  `DRIVES` a recorded Invocation. A bare `Driver.dispatch()` (or `.create()`) does
  **not** flow through `ctx.spawn`, so it records **no Invocation** and breaks the
  "connected provenance subgraph" guarantee the module docstring promises
  (`delegate.py:11-12`). Open Q-5/Q-7 gesture at this but the spec still lists the
  `delegate` change in Done-When and `affects:` as if it were straightforward. It is
  not. **This is the second must-fix.**

- **`engine.py:55-56` injectors citation is correct but the "After" shim is subtly
  self-defeating.** The proposed `injectors = {"client": lambda: self.drivers.get("jules"),
  "vcs": lambda: self.drivers.get("vcs")}` (`spec :236-237`) keeps `ctx.client` and
  `inject=["vcs"]` working — good. But note `DriverRegistry.get` is specified to *raise*
  on a miss (`spec :167-168`), so these lambdas now raise inside `Registry.invoke`'s
  inject loop (`capability.py:156,163`) if someone constructs an `Engine` and removes a
  default driver. Today `injectors["client"]()` can't fail (it returns the stored
  object). The shim must use `.has()`-guarded lookup or the registry's miss path must be
  non-raising for the back-compat keys.

- **`PROPOSAL.md` line cite.** Spec evidence cites `PROPOSAL.md:44-83` for the
  Boundary/Driver sketch; source confirms §2 begins ~`:46` ("## 2. Generalised
  `Boundary` / `Driver`…") and the sketch + before/after run to ~`:83`. Accurate.

---

## Missing depth

1. **No resolution of the `delegate` provenance path (the hardest part) — only Open
   Questions.** Q-5 and Q-7 together *are* the spec's biggest design risk, yet both are
   parked. The spec must state, concretely: does a `Driver` dispatch record an
   Invocation? Through what code path (a thin wrapper capability? a `ctx.spawn`-like
   `ctx.drive(name, op, **kw)` that records first?)? Until that is answered the
   `delegate.fan_out` Done-When item (`:99-103`) is not implementable without guessing —
   which violates the spec's own "open a `[BLOCKED]` PR, do not guess" rule (`:33-34`).

2. **`Boundary` as a `@runtime_checkable` marker Protocol with an empty body is a
   no-op.** A `runtime_checkable` Protocol with no members makes `isinstance(x, Boundary)`
   **true for literally every object** (PEP 544). If the registry ever `isinstance`-checks
   on register/get, it provides zero safety. Either drop `@runtime_checkable` from the
   empty marker, or give `Driver` at least one member so the check means something. The
   spec doesn't address what (if anything) validates a registered object.

3. **Async question (Q-6) interacts with the whole call chain and is left open.**
   `JulesClient`/`GitClient` are sync, `_wire.impl` is sync (`engine.py:69`),
   `Registry.invoke` is sync (`capability.py:144`). `PROPOSAL.md §2`'s `async def
   dispatch` would force a sync→async conversion across `invoke`/`_wire`. The spec
   should *close* this as "drivers are sync, matching today" (the only non-breaking
   answer) rather than list it as open — an async driver would be out of scope and a far
   larger spec.

4. **No statement on `_jules_api`'s exception model vs. `ToolResult`.** `JulesClient`
   methods can raise `JulesAPIError`/`RuntimeError` (`_jules_api.py:22-38,64-66`). Spec
   002 says drivers "return `ToolResult`" (`:68-69`) and Done-When `:96-98` claims "No
   behaviour change to `JulesClient`/`GitClient` internals beyond return-type alignment"
   — but converting raise-based boundaries to `ToolResult`-returning ones *is* a
   behaviour change, and it duplicates Spec 001's `Registry.invoke` exception→`INTERNAL`
   handling. The spec should clarify: drivers stay raise-on-error (boundaries are I/O),
   the *capability* wraps into `ToolResult` (as Spec 001 already migrates `jules.dispatch`
   to do). Otherwise Spec 001 and 002 fight over who owns boundary-error→`ToolResult`.

5. **`DriverRegistry` lifecycle/immutability unspecified.** Can a host re-`register`
   over `"jules"`? Is the registry frozen after `Engine.__init__`? The `extra_capabilities`
   precedent (`engine.py:48`) suggests host-supplied drivers should be allowed to
   *add* but the override semantics of the `drivers=` kwarg vs. the two defaults
   (`spec :228-232`: defaults registered first, then `drivers` dict overlaid) means a
   host CAN silently shadow `"jules"`. State whether that's intended.

---

## Open-Questions triage

| # | Topic | Disposition | Reasoning |
|---|---|---|---|
| **Q-1** | uniform `dispatch` vs. named methods | **BLOCKING — but should be resolved now, to B.** | This is the spec's own load-bearing decision and it gates the Protocol body, every `_backend`→`_driver` rewrite, and the `JulesBackend`/`VCSBackend` survival. Evidence (prior art = named handlers; Spec 001 anti-stringly-typed; richly-typed existing Protocols) points decisively to **B**. Leaving it open forces the implementer to guess the single most consequential decision. Resolve to B in-spec. |
| **Q-5** | `delegate.fan_out` driver resolution + provenance | **BLOCKING.** | The terminology collision (capability-"driver" vs. registry-`Driver`) plus the Invocation/provenance path is unresolved and the `delegate` Done-When + `affects:` entry depend on it. Cannot implement without an answer. See Missing-depth #1. |
| **Q-3** | missing-driver behaviour | **RESOLVABLE NOW (not blocking).** | Spec 001 already defines `ErrorCode.NOT_FOUND` (Spec 001 `:96-97,160`). The clean answer: `DriverRegistry.get` raises a typed `KeyError`-subclass/`LookupError`; the *capability* catches and returns `ToolResult.failure(NOT_FOUND, …)` — exactly the pattern Spec 001 establishes. State it; don't leave it a three-way open question. (Note the back-compat-shim interaction flagged above.) |
| **Q-6** | async vs. sync | **RESOLVABLE NOW → sync.** | The entire call chain is sync; async is a different, larger spec. Close it as "sync, matching today." |
| **Q-2** | keep `inject=["vcs"]` as sugar | **NON-BLOCKING (defer/decide either way).** | Both options work; the back-compat shim (`spec :236-237`) already makes `inject=["vcs"]` resolve through the registry, so this is a style choice, not a blocker. Recommend: keep `inject` working (registry-backed injector) and make `ctx.get_driver` the *documented* path — least churn, preserves the 7 `vcs_backend` test seams. |
| **Q-4** | back-compat for `jules_client=`/`vcs_backend=`/`ctx.client` | **NON-BLOCKING — keep the shims (decide: keep).** | Blast radius is small and verified: 7 `vcs_backend` + 3 `jules_client` references and **1** `ctx.client` read (`jules.py:77`) in the whole tree. Keeping the deprecated kwargs as forwarders into the registry (as the "After" sketch already does, `spec :226-237`) keeps Spec 002 additive and the 57 tests green. Recommend keep, mark deprecated, migrate in a later cleanup. |
| **Q-7** | does a `Driver` get `CapabilityContext`/memory | **BLOCKING (folds into Q-5).** | The answer must be "no — a `Driver` is a dumb I/O edge; the calling capability owns all graph writes," which is what `delegate`/`workspace`/`branch` already assume (boundaries never touch the graph; `_vcs.py:1-9`). If that's the answer, the provenance path in Q-5 *must* run through a capability, not the raw driver. So Q-7 is not independent — it constrains Q-5. |

---

## Must-fix list (ordered)

1. **Resolve Q-1 to Option B in the spec.** Make `Driver` a marker `Boundary`
   (drop the placeholder `dispatch(op, **kw)` body at `:154`); the uniform contract is
   the **return type** (`ToolResult`, from Spec 001), not a uniform method name. Keep
   `JulesBackend`/`VCSBackend` as the typed `Driver` shapes. Rewrite Open Q-1 from "the
   load-bearing decision" to "decided: B" with the prior-art + anti-stringly-typed
   rationale.

2. **Resolve the "driver" collision and the `delegate` provenance path (Q-5+Q-7)
   before listing `delegate.py` in `affects:`.** Rename the registry concept or the
   `fan_out` arg so the two "drivers" don't alias; specify that a registry-`Driver`
   delegation target still records an Invocation via a capability-mediated path
   (`ctx.spawn`-equivalent), preserving the connected provenance subgraph
   (`delegate.py:11-12,48-54`). If unresolved, **remove `delegate.py` from this spec's
   scope** and split it into a follow-up — do not ship a half-specified `fan_out` change.

3. **Fix the `CapabilityContext.drivers` type/`None` hazard.** Either
   `Optional["DriverRegistry"] = None` with a guard in `get_driver`, or have
   `Registry.invoke` always inject a real (empty-if-unset) `DriverRegistry` so the field
   is never `None` (`capability.py:152-157`; spec `:181-195,203-210`).

4. **Close Q-3 (typed `NOT_FOUND` via capability-side catch), Q-6 (sync), and harden
   the back-compat injector shim** so `injectors["client"/"vcs"]` cannot raise
   (`.has()`-guard or non-raising miss for those keys) — `capability.py:156,163`,
   spec `:236-237`.

5. **Fix the citation errors and the `runtime_checkable` empty-marker no-op:** correct
   the `engine.py:67` `inject` cite to `capability.py:149-163`; either drop
   `@runtime_checkable` from the memberless `Boundary` or give `Driver` a member so the
   check is meaningful.

6. **Reconcile boundary-error ownership with Spec 001.** State explicitly that drivers
   remain raise-on-error and the *capability* converts to `ToolResult` (matching Spec
   001's `jules.dispatch` migration), so Done-When `:96-98`'s "no behaviour change to
   internals" is actually true and the two specs don't both claim the conversion.

---

## Faithfulness / implementability / testability summary

- **Faithfulness to source: mostly good, one structural error.** Line cites are
  ~95% accurate (one wrong cite: `engine.py:67`). The fatal faithfulness gap is the
  **misuse of ADR-0004 as precedent for uniform dispatch** when the cited repo
  demonstrably uses named handlers — this inverts the load-bearing recommendation.

- **Implementability: blocked.** Two Done-When items (`delegate.fan_out`, the `Driver`
  body) cannot be built without first resolving Q-1 and Q-5/Q-7 — which the spec's own
  no-guessing rule (`:33-34`) forbids guessing. As written, a faithful Jules session
  would (correctly) open a `[BLOCKED: clarification]` PR.

- **Testability: strong.** The `FakeDriver` + `NOT_FOUND` test (`:104-106`) and the
  existing 57-test suite with its `StubVCS`/`StubJulesClient` seams
  (`tests/test_agency.py:62,101,255,1089-1282`) give a clean regression net. With Q-4
  kept (back-compat shims), the migration is provably non-breaking — keep that property.

**Bottom line:** Right problem, right registry shape, additive instinct — but flip
Q-1 to typed-named-methods, de-collide and properly scope the `delegate` change, and
resolve the parked questions that the spec's own discipline says block coding.
