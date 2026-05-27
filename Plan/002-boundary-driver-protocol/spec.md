---
spec_id: 002
slug: boundary-driver-protocol
status: draft
owner: "@agency"
depends_on: [001]
affects:
  - agency/capability.py
  - agency/engine.py
  - agency/capabilities/jules.py
  - agency/capabilities/_vcs.py
  - agency/capabilities/workspace.py
  - agency/capabilities/branch.py
  - tests/test_agency.py
source-repos:
  - https://github.com/netzkontrast/the-agency-system.git @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22
  - https://github.com/bitwize-music-studio/claude-ai-music-skills.git @ b4b70dbfa2e24e3b86ec3d6cbec4e9bf1baddfaf
estimated_jules_sessions: 2
domain: cross
wave: A
---

> **Jules: read `Plan/JULES_PROTOCOL.md` before starting** (if present; otherwise
> follow the repo's contribution rules in `CLAUDE.md`). Run the gates in order:
> (1) Confidence ≥ 0.90, (2) TDD Red-Green-Refactor, (3) Evidence pasted under
> `## Evidence`, (4) Self-Review answered.
> Branch: `claude/extract-agency-plugin-o4JRc`. PRs target `main`. Only modify
> paths under `affects:` below. Additive commits; never rewrite history or
> force-push.
> **Depends on Spec 001** — `ToolResult`/`TypedError` must exist first; drivers
> return `ToolResult`. If anything is ambiguous, open a draft PR labelled
> `[BLOCKED: clarification]` and stop. Every guessable decision is parked under
> `## Open Questions / Needs Research`.

# Spec 002 — Generic `Boundary` / `Driver` Protocol Family + `DriverRegistry`

## Why

The engine already isolates external side-effects behind two **per-capability**
Protocols that are injected for deterministic testing:

- `JulesBackend` (`agency/capabilities/jules.py:25-34`) — the Jules REST surface;
  default impl `JulesClient` (`:37-69`); injected as `ctx.client` via
  `Registry.injectors["client"]` (`agency/engine.py:55`) and reached by
  `JulesCapability._backend()` (`jules.py:76-77`).
- `VCSBackend` (`agency/capabilities/_vcs.py:18-23`) — git/gh; default impl
  `GitClient` (`:26-67`); injected via `Registry.injectors["vcs"]`
  (`agency/engine.py:56`) and the `inject=["vcs"]` verb convention in
  `workspace`/`branch` (`workspace.py:25,36`, `branch.py:32,38`).

`FINDINGS.md` flags these as *"excellent injections… not unified under a single
driver or boundary protocol, leading to duplication in how tests mock them"*
(`research/oo-architecture/FINDINGS.md:16`). Each new external cluster today means:
(a) a new ad-hoc Protocol, (b) a new hard-coded `Engine.__init__` kwarg
(`engine.py:40-42` already has `jules_client=` and `vcs_backend=`), (c) a new
`Registry.injectors` entry (`engine.py:55-56`), and (d) a bespoke `_backend()` or
`inject=[...]` access pattern. That does not scale: `bitwize-music`'s pipeline is a
fleet of tool-clusters (audio analysis, mastering, transcription, DB) that each
want to plug in as a driver and return a uniform result —
`PROPOSAL.md §2` makes the generic `Boundary`/`Driver`/`DriverRegistry` the
remedy, and `the-agency-system`'s five-handler-domain routing
(`vendor/the-agency-system/Plan/decisions/0004-five-handler-domains.md`) is the
precedent for one routing table over many domains.

This spec generalises the two existing boundaries into a **`Driver` Protocol
family + a `DriverRegistry`** reached via `ctx.drivers` / `ctx.get_driver(name)`,
so a domain tool-cluster plugs in by registering a driver and needs **no** new
`Engine` kwarg or `injectors` key. `JulesBackend` and `VCSBackend` are kept
unchanged as the typed-Protocol *shape* of two concrete drivers — the
generalisation is additive, not a rip-out.

**The load-bearing decision is resolved (was Open Q-1): Option B — a `Driver` is a
marker `Boundary` that exposes its own typed, named methods. There is NO uniform
`dispatch(op, **kw)`.** The uniform contract every driver shares is the **RETURN
TYPE** (`ToolResult`, from Spec 001), reached through the *capability* that wraps the
boundary — not a uniform method *name*. Rationale: (a) the prior art the spec cites,
ADR-0004, is a *fixed taxonomy of domains exposing typed named handler functions*
registered via `register_<domain>_handlers(mcp)`
(`vendor/the-agency-system/servers/agency-mcp/src/agency_mcp/server.py:55-85`); there
is **no `dispatch(op)` anywhere in `servers/`** (grep returns nothing), and the
motivating clusters (`bitwize-music` mastering/audio/db) are *directories of named
functions* (`…/tools/mastering/{analyze_tracks,master_tracks,qc_tracks,…}.py`) — the
faithful reading is named methods, not one stringly-typed entry point; (b)
`JulesBackend` (seven differently-signed methods, `jules.py:25-34`) and `VCSBackend`
(four, `_vcs.py:18-23`) are richly typed, and collapsing them to `dispatch(op: str,
**kw)` would re-introduce the stringly-typed smell Spec 001 exists to eliminate —
incoherent across the wave; (c) the registry's value is *named lookup + uniform
result type*, which Option B already delivers (`ctx.get_driver("jules").create(...)`
returning into a `ToolResult`), while Option A only adds verb→op string-mapping
boilerplate; (d) `PROPOSAL.md §2`'s `driver.dispatch({...})` is a 6-line `async`/`pass`
sketch, not a constraint, and the two concrete typed Protocols already in the tree
outweigh it.

## Done When

- [ ] `Boundary` and `Driver` Protocols live in `agency/capability.py` (per
      `PROPOSAL.md §2` and Spec 001's file). `Boundary` is a marker Protocol for any
      injected external dependency; `Driver` is a marker `Boundary` (Option B —
      **no** uniform `dispatch(op, **kw)`). Each concrete driver keeps its own typed,
      named methods; the uniform contract is the RETURN TYPE (`ToolResult`, Spec 001),
      produced by the *capability* that wraps the boundary, not by a uniform method
      name. `Driver` carries one optional introspection member (`name`/`describe()`)
      so the `isinstance` check is meaningful (see Missing-depth note).
- [ ] `DriverRegistry` (in `agency/capability.py`) supports `register(name, driver)`,
      `get(name) -> Driver` (raising a typed `NOT_FOUND` `ToolResult`/error when
      absent — see Open Q-3), `names() -> list[str]`, and `has(name) -> bool`.
- [ ] `CapabilityContext` gains `drivers: DriverRegistry` and a
      `get_driver(name) -> Driver` convenience (`agency/capability.py:35-47`),
      injected by `Registry.invoke` the same way `client`/`memory`/`intent_id` are
      today (`agency/capability.py:152-163`).
- [ ] `Engine.__init__` builds the `DriverRegistry` and registers the two existing
      boundaries under stable names — `"jules"` (the `JulesClient`) and `"vcs"` (the
      `GitClient`) — replacing the bespoke `jules_client=`/`vcs_backend=` kwargs with
      a single `drivers: dict[str, Driver] | None = None` override (back-compat for
      the two old kwargs is Open Q-4).
- [ ] `JulesCapability._backend()` (`jules.py:76-77`) is rewritten to
      `self.ctx.get_driver("jules")`; `workspace`/`branch` verbs drop `inject=["vcs"]`
      and use `self.ctx.get_driver("vcs")` instead (or keep `inject` as sugar — Open Q-2).
- [ ] `JulesBackend`/`VCSBackend` are declared as `Driver` Protocols (they already
      are Protocols; this is a marker-base change + registration by name). **No
      behaviour change and no return-type change** to `JulesClient`/`GitClient`: they
      stay raise-on-error I/O boundaries (they keep returning `dict`); the *capability*
      owns the conversion into `ToolResult` (exactly as Spec 001 already migrates
      `jules.dispatch` to do). This avoids Spec 001 and 002 both claiming the
      boundary-error→`ToolResult` conversion.
- [ ] **`delegate.fan_out` is OUT OF SCOPE for this spec** (de-collided). In the live
      tree `fan_out(driver, driver_verb, …)` already means **capability name + verb**,
      resolved via `ctx.spawn` (`delegate.py:29,40,52`; `subagent.develop` calls it
      with `driver="jules", driver_verb="dispatch"`, `subagent.py:23-28`). The new
      `DriverRegistry` introduces a *second, different* "driver" (a registered object),
      and a raw `Driver.create(...)` does NOT flow through `ctx.spawn`, so it records
      **no Invocation** and breaks the connected-provenance guarantee
      (`delegate.py:11-12,48-54`). Making a registered `Driver` a delegation target
      therefore requires a capability-mediated, Invocation-recording path
      (`ctx.spawn`-equivalent) and a rename to remove the alias — that is a follow-up
      spec (see Open Questions). `delegate.py` is removed from `affects:` here.
- [ ] A test-only `FakeDriver` demonstrates the contract: register it under a name,
      resolve it via `ctx.get_driver`, call its typed method, and assert the *capability*
      that wraps it returns a `ToolResult`; assert an unregistered name raises
      `DriverMissing` and the capability maps it to `ToolResult.failure(NOT_FOUND, …)`.
- [ ] `tests/test_agency.py` still passes (56+), with existing Jules/VCS injection
      tests rewritten to inject via the `DriverRegistry` and proving the old
      `jules_client=`/`vcs_backend=` test seams still resolve (or their replacement).

## Source clones (run first)

```bash
git clone --depth=1 https://github.com/netzkontrast/the-agency-system.git \
  ~/work/vendor/the-agency-system        # SHA 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22
git clone --depth=1 --branch=v0.91.0 \
  https://github.com/bitwize-music-studio/claude-ai-music-skills.git \
  ~/work/vendor/bitwize-music             # SHA b4b70dbfa2e24e3b86ec3d6cbec4e9bf1baddfaf
```

Read `~/work/vendor/the-agency-system/Plan/decisions/0004-five-handler-domains.md`
**and** `servers/agency-mcp/src/agency_mcp/server.py:55-85` for the precedent: a fixed
taxonomy of domains, each registered via `register_<domain>_handlers(mcp)` exposing
**typed named handler functions** — not a single `dispatch(op)` (there is none in
`servers/`). This is the source grounding for D-1 (Option B). Skim the `bitwize-music`
MCP tool clusters (audio/master/transcribe/db families) — directories of named
functions — as the motivating set of future drivers; do **not** port them here; this
spec only builds the registry they will plug into.

## Design

### `agency/capability.py` — the Protocol family + registry

```python
from __future__ import annotations
from typing import Protocol
# ToolResult / TypedError / ErrorCode are defined earlier in this module (Spec 001).


class Boundary(Protocol):
    """Marker Protocol for any injected external dependency (a seam tests can
    stand in for). JulesClient and GitClient are Boundaries. NOT @runtime_checkable:
    a memberless runtime_checkable Protocol makes isinstance() true for every object
    (PEP 544), which is a no-op safety check."""
    ...


# Driver is a plain (NOT @runtime_checkable) marker base. RESOLVED (was Open Q-1):
# a Driver is a marker, NOT a uniform dispatch surface. Each concrete driver keeps
# its own typed, named methods (JulesBackend.create/get/list/…;
# VCSBackend.worktree/run/state/finish). The uniform contract is the RETURN TYPE
# (ToolResult, Spec 001), produced by the capability that wraps the boundary — not a
# uniform method name. It is NOT @runtime_checkable: a memberless runtime_checkable
# Protocol is a no-op isinstance (PEP 544), and requiring a member (e.g. describe())
# would force a behaviour change onto JulesClient/GitClient, which this spec forbids.
class Driver(Boundary, Protocol):
    """Marker base for any object registrable in the DriverRegistry."""
    ...


class DriverMissing(LookupError):
    """A typed miss raised by DriverRegistry.get(absent). The calling CAPABILITY
    catches it and returns ToolResult.failure(ErrorCode.NOT_FOUND, …) (Spec 001),
    so loop-recovery sees a typed code. The registry never builds a ToolResult
    itself — get() returning a Driver-or-raise keeps the type honest."""


class DriverRegistry:
    """One named table of Drivers, reached from a verb via ctx.get_driver(name).
    Replaces the bespoke Registry.injectors['client'/'vcs'] entries. Registration is
    not isinstance-gated (the marker has no members to check); any object the host
    supplies is accepted, and the capability that uses it owns the typed contract."""
    def __init__(self) -> None:
        self._drivers: dict[str, Driver] = {}

    def register(self, name: str, driver: Driver) -> None:
        self._drivers[name] = driver

    def get(self, name: str) -> Driver:
        if name not in self._drivers:                      # RESOLVED (was Open Q-3)
            raise DriverMissing(name)                      # capability -> ToolResult.failure(NOT_FOUND)
        return self._drivers[name]

    def has(self, name: str) -> bool:
        return name in self._drivers

    def names(self) -> list[str]:
        return sorted(self._drivers)
```

### `CapabilityContext` — expose the registry (`agency/capability.py:35-82`)

```python
@dataclass
class CapabilityContext:
    memory: Memory
    ontology: Any
    registry: "Registry"
    intent_id: str
    agent_id: Optional[str] = None
    client: Any = None              # DEPRECATED alias for drivers.get("jules") (kept, Q-4)
    # NEW: the named Driver table. Defaulted to a real empty registry, NOT None, so
    # get_driver() never hits 'NoneType'. `Registry.invoke` always passes the real one.
    drivers: "DriverRegistry" = field(default_factory=lambda: DriverRegistry())
    depth: int = 0
    MAX_DEPTH: int = 16

    def get_driver(self, name: str) -> "Driver":
        return self.drivers.get(name)
```

Defaulting `drivers` to an empty `DriverRegistry` (via `field(default_factory=…)`,
never `None`) removes the type-lie hazard — the field is typed non-Optional, so it
must never be `None`. `Registry.invoke` (below) always injects the engine's real
registry, so the default only ever applies to a hand-built `CapabilityContext` in a
test.

### `Registry.invoke` — inject `drivers` (`agency/capability.py:144-163`)

`Registry` keeps a `self.drivers: DriverRegistry` (set by the engine, like
`self.ontology` at `capability.py:133`). The `ctx` branch in `invoke` passes it:

```python
if name == "ctx":
    call["ctx"] = CapabilityContext(
        memory=memory, ontology=self.ontology, registry=self,
        intent_id=intent_id, agent_id=agent_id,
        client=(self.injectors["client"]() if "client" in self.injectors else None),
        drivers=self.drivers,                              # NEW
        depth=_depth)
```

### `Engine.__init__` — build + register (`agency/engine.py:40-59`)

**Before:**
```python
def __init__(self, path, jules_client=None, vcs_backend=None, extra_capabilities=None):
    self.jules_client = jules_client or JulesClient()
    self.vcs_backend = vcs_backend or GitClient()
    ...
    self.registry.injectors = {"client": lambda: self.jules_client,
                               "vcs": lambda: self.vcs_backend}
```

**After:**
```python
def __init__(self, path, extra_capabilities=None, drivers=None,
             jules_client=None, vcs_backend=None):   # old kwargs kept (Q-4), keyword-only in tests
    self.drivers = DriverRegistry()
    self.drivers.register("jules", jules_client or JulesClient())
    self.drivers.register("vcs", vcs_backend or GitClient())
    for name, drv in (drivers or {}).items():        # host-supplied / domain clusters
        self.drivers.register(name, drv)             # NOTE: a host CAN shadow "jules"/"vcs"
    ...
    self.registry.drivers = self.drivers
    # back-compat shims (kept, Q-4): ctx.client -> the jules driver, inject=["vcs"] ->
    # the vcs driver. `.has()`-guarded so these injectors CANNOT raise inside the
    # Registry.invoke inject loop even if a host removed a default driver — today
    # injectors["client"]() can't fail, and that property must be preserved.
    self.registry.injectors = {
        "client": lambda: self.drivers.get("jules") if self.drivers.has("jules") else None,
        "vcs": lambda: self.drivers.get("vcs") if self.drivers.has("vcs") else None,
    }
```

### Before / After — `JulesCapability._backend` (`jules.py:76-82`)

**Before:**
```python
def _backend(self) -> JulesBackend:
    return self.ctx.client or JulesClient()

@verb(role="effect")
def dispatch(self, source, starting_branch, prompt) -> ToolResult:   # ToolResult per Spec 001
    s = self._backend().create(prompt=prompt, source=source, starting_branch=starting_branch)
    ...
```

**After (RESOLVED — Option B, typed named methods via the registry):** `_backend`
becomes `_driver`, reaching the same `JulesClient` by name. The verb keeps calling the
typed `.create(...)` (no `dispatch(op)` indirection), catches `DriverMissing`, and
owns the `ToolResult` conversion (Spec 001):
```python
def _driver(self) -> JulesBackend:
    return self.ctx.get_driver("jules")     # raises DriverMissing if unregistered

@verb(role="effect")
def dispatch(self, source, starting_branch, prompt) -> ToolResult:
    try:
        s = self._driver().create(prompt=prompt, source=source, starting_branch=starting_branch)
    except DriverMissing as e:
        return ToolResult.failure(ErrorCode.NOT_FOUND, f"no driver: {e}")   # Spec 001
    ...
```
The deprecated `ctx.client` read (`jules.py:77`) is removed in favour of
`ctx.get_driver("jules")`, but the `injectors["client"]` shim above keeps `ctx.client`
resolving for any out-of-tree caller (Q-4).

### Before / After — `workspace.isolate` (`workspace.py:25-34`)

**Before:** `@verb(role="effect", inject=["vcs"])` + `def isolate(self, vcs, branch, base)` + `(vcs or GitClient()).worktree(...)`.

**After (RESOLVED — Q-2: `ctx.get_driver` is the documented path; `inject=["vcs"]`
keeps working as registry-backed sugar):** the `injectors["vcs"]` shim above is
registry-backed, so the existing `inject=["vcs"]` verbs in `workspace`/`branch`
continue to resolve unchanged (least churn, preserves the `vcs_backend` test seams).
New code uses `ctx.get_driver("vcs")`:
```python
@verb(role="effect")
def isolate(self, branch: str, base: str = "main") -> ToolResult:
    wt = self.ctx.get_driver("vcs").worktree(branch=branch, base=base)
    ...
```

### `delegate.fan_out` — explicitly OUT OF SCOPE (de-collided)

`fan_out`'s `driver`/`driver_verb` already mean **capability name + verb**, dispatched
via `ctx.spawn` so each child records an Invocation in the connected provenance
subgraph (`delegate.py:11-12,40,52`; `subagent.develop` uses `driver="jules",
driver_verb="dispatch"`, `subagent.py:23-28`). The `DriverRegistry`'s `Driver` is a
*different* "driver" (a registered object), and calling it directly records **no**
Invocation — it would break that provenance guarantee. Folding registry-`Driver`s into
`fan_out` therefore requires (a) renaming one of the two "driver" concepts to kill the
alias, and (b) a capability-mediated, Invocation-recording dispatch path
(`ctx.spawn`-equivalent). That is a follow-up spec; this spec touches no `delegate`
code and `Driver`s remain dumb I/O edges with no `CapabilityContext`/memory access
(former Q-7: the calling capability owns all graph writes — matching how
`workspace`/`branch` already treat the VCS boundary, `_vcs.py:1-9`).

## Files

- **Modify** `agency/capability.py`: add `Boundary`, `Driver`, `DriverRegistry`;
  add `drivers` + `get_driver` to `CapabilityContext`; inject `drivers` in
  `Registry.invoke`; add `Registry.drivers` slot.
- **Modify** `agency/engine.py`: build the `DriverRegistry`, register `jules`/`vcs`,
  accept a `drivers=` override, keep `injectors` as a back-compat shim.
- **Modify** `agency/capabilities/jules.py`: `_backend` → `_driver` via
  `ctx.get_driver("jules")`; declare `JulesBackend` as a `Driver` Protocol (marker
  base only; no method/return-type change — the capability owns `ToolResult`).
- **Modify** `agency/capabilities/_vcs.py`: declare `VCSBackend` as a `Driver`
  Protocol (marker base only); no `GitClient` behaviour or return-type change.
- **Modify** `agency/capabilities/{workspace,branch}.py`: use `ctx.get_driver("vcs")`
  in any new code; their existing `inject=["vcs"]` verbs keep working via the
  registry-backed injector shim (Q-2 — no rewrite required).
- **NOT modified** `agency/capabilities/delegate.py`: the `fan_out` Driver-target
  change is de-collided and deferred to a follow-up spec (see Done When + Design).
- **Modify** `tests/test_agency.py`: rewrite Jules/VCS injection to use the registry;
  prove the old `jules_client=`/`vcs_backend=`/`ctx.client` seams still resolve; add
  `FakeDriver` + `DriverMissing`/`NOT_FOUND` tests.
- **Create**: none (everything lands in `capability.py`, per `PROPOSAL.md §2`).

## Decided (was open — resolved in this revision per REVIEW)

- **D-1 (`Driver` shape) → Option B.** A `Driver` is a marker `Boundary` exposing its
  own typed, named methods; there is **no** uniform `dispatch(op, **kw)`. The uniform
  contract is the RETURN TYPE (`ToolResult`, Spec 001), owned by the wrapping
  capability. Rationale in **Why** (prior art = named handlers, not `dispatch`; anti-
  stringly-typed coherence with Spec 001; richly-typed existing Protocols; `PROPOSAL.md`
  is a non-binding sketch).
- **D-2 (`inject=["vcs"]`) → keep as registry-backed sugar.** `ctx.get_driver` is the
  documented path; the injector shim keeps existing `inject=["vcs"]` verbs working with
  no rewrite (preserves the `vcs_backend` test seams).
- **D-3 (missing driver) → typed raise + capability-side convert.**
  `DriverRegistry.get(absent)` raises `DriverMissing(LookupError)`; the *capability*
  catches and returns `ToolResult.failure(NOT_FOUND, …)` (Spec 001 pattern). The
  back-compat injector lambdas are `.has()`-guarded so they never raise in the inject
  loop.
- **D-4 (back-compat) → keep the shims.** Verified small blast radius (7 `vcs_backend`,
  3 `jules_client`, 1 `ctx.client`): `jules_client=`/`vcs_backend=` kwargs and
  `ctx.client` are kept as deprecated forwarders into the `DriverRegistry`, so 002 is
  additive and the suite stays green. Migrate the call sites in a later cleanup.
- **D-5 (async) → sync, matching today.** `JulesClient`/`GitClient`, `_wire.impl`, and
  `Registry.invoke` are all sync; async drivers would force a sync→async conversion
  across the call chain and are a separate, larger spec — out of scope.
- **D-6 (Driver + memory) → no.** A `Driver` is a dumb I/O edge with no
  `CapabilityContext`/memory access; the calling capability owns all graph writes
  (matching `workspace`/`branch`/`_vcs.py:1-9`). This constrains the deferred
  `delegate` work (Q-1 below).

## Open Questions / Needs Research

1. **`delegate.fan_out` as a registry-`Driver` target (DEFERRED to a follow-up spec;
   out of scope here).** Two unresolved sub-problems: (a) the terminology **collision**
   — `fan_out`'s `driver`/`driver_verb` already mean capability+verb via `ctx.spawn`
   (`delegate.py:29,40,52`; `subagent.py:23-28`), and the new registry-`Driver` is a
   different concept; one must be renamed. (b) the **provenance path** — a raw
   `Driver` call records no Invocation, breaking the connected subgraph
   (`delegate.py:11-12,48-54`); per D-6 a `Driver` is a dumb edge, so any
   delegation-target dispatch must run through a capability-mediated,
   Invocation-recording path (`ctx.spawn`-equivalent, e.g. a thin wrapper capability or
   a `ctx.drive(name, op, **kw)` that records first). Until both are designed, this
   stays out of `affects:` — do not implement `fan_out` against the `DriverRegistry`
   in this spec.
2. **`DriverRegistry` immutability after `Engine.__init__`?** The `drivers=` overlay
   lets a host silently shadow `"jules"`/`"vcs"` (Missing-depth note). Decide whether
   re-`register` is allowed or the registry is frozen post-construction; low risk,
   non-blocking for the core build.

## Evidence

- `agency/capabilities/jules.py:25-34,37-69,76-82` — `JulesBackend` Protocol,
  `JulesClient` default, `_backend()` access via `ctx.client`.
- `agency/capabilities/_vcs.py:18-23,26-67` — `VCSBackend` Protocol + `GitClient`.
- `agency/engine.py:40-59` — `Engine.__init__`: the `jules_client=`/`vcs_backend=`
  kwargs (`:40-42`) and `Registry.injectors` wiring (`:55-56`).
- `agency/capability.py:35-47,126-163` — `CapabilityContext` dataclass (`:35-47`),
  `Registry`, `injectors` (`:129-133`), and the `inject` *resolution* in
  `Registry.invoke` at `capability.py:149-163` (the `ctx` branch is `:152-157`). The
  `inject` convention is declared at `capability.py:84-90` (`verb()`) + `:103`
  (`_wrap_method`) — **NOT** `engine.py:67`, which only computes `user_params` in
  `_wire` (corrected citation).
- `agency/capabilities/workspace.py:25,36`, `branch.py:32,38` — the `inject=["vcs"]`
  verb convention, kept working via the registry-backed injector (D-2).
- `agency/capabilities/delegate.py:11-12,28-56`, `subagent.py:23-28` — `fan_out`
  resolving `driver`/`driver_verb` via `ctx.spawn` (capability+verb), and the
  connected-provenance docstring guarantee — the basis for de-colliding "driver" and
  deferring the `fan_out`-as-Driver change.
- `research/oo-architecture/FINDINGS.md:16,18` — scattered boundaries / mocking
  duplication, and the stringly-typed smell Spec 001/002 must not re-introduce.
- `research/oo-architecture/PROPOSAL.md:44-83` — `Boundary`/`Driver`/`DriverRegistry`
  sketch + before/after (§2); a non-binding `async`/`pass` sketch (D-1, D-5).
- `vendor/the-agency-system/servers/agency-mcp/src/agency_mcp/server.py:55-85` @
  `0a6a9e71f6c26bc120a8fc1db02f8990b7916f22` — `register_<domain>_handlers(mcp)`:
  named handler functions per domain. `tools/mastering/{analyze_tracks,master_tracks,
  qc_tracks,…}.py` are directories of named functions; **no `dispatch(op)` anywhere in
  `servers/`** (grep returns nothing) — the prior art for D-1 (Option B, named methods).
- `vendor/the-agency-system/Plan/decisions/0004-five-handler-domains.md` @
  `0a6a9e71f6c26bc120a8fc1db02f8990b7916f22` — a fixed taxonomy of domains, each a set
  of typed named handlers (one registration table over many domains, not one `dispatch`).
