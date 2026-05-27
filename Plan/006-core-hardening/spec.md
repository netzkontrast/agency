---
spec_id: 006
slug: core-hardening
status: draft
owner: "@agency"
depends_on: []
affects:
  - agency/memory.py
  - agency/capabilities/_jules_api.py
  - agency/capabilities/jules.py
  - agency/capabilities/_vcs.py
  - agency/engine.py
  - tests/test_hardening.py
source-repos:
  - url: https://github.com/netzkontrast/the-agency-system
    ref: master
estimated_jules_sessions: 2
domain: core
wave: 1
---

# Spec 006 — Core Hardening

> Consolidates the verified red-team risks (`research/red-team/FINDINGS.md`,
> `research/red-team/hardening-spec.md`) into one implementable hardening pass.
> Each fix is grounded against the current code with a re-pinned `path:line`
> citation (the research had drifted line numbers — corrected under `## Evidence`).
> Refined per the spec-panel REVIEW (`Plan/006-core-hardening/REVIEW.md`), which
> ran **live probes** against the pinned stack (GraphQLite 0.5.0, pydantic-monty
> 0.0.16) to settle the open design choices — those findings are folded in below.
> Only touch paths under `affects:`.

## Why

Four architectural risks in the PR1 core, each verified against the code at the
cited line on branch `claude/extract-agency-plugin-o4JRc`. The REVIEW re-verified
every citation as accurate and resolved the open design questions with live
probes; #4's severity is **downgraded** by that probe (see below):

1. **CLI-boot full graph scan (Medium sev × High likelihood).**
   `Memory._max_persisted_tick` (`agency/memory.py:39-62`) seeds the logical
   clock by pulling **every node** (`MATCH (n) RETURN n`, line 42) **and every
   edge** (`MATCH ()-[r]->() RETURN r`, line 55) into Python and looping to find
   the max `vfrom`/`vto`. The bash CLI opens a fresh `Engine` (→ fresh `Memory`,
   `agency/memory.py:37`) on **every command**, so boot cost is O(N+E) on each
   invocation. At 100k+ nodes this is a linear startup cliff. *Chesterton's
   fence:* the scan exists because the clock must stay monotonic across reopens
   (stateless CLI) — the fix must preserve that guarantee, not drop it.

2. **Pagination cap silently truncates source resolution (Low sev × Medium
   likelihood).** `_jules_api._paginate` (`agency/capabilities/_jules_api.py:70`)
   loops `while pages < max_pages` with `max_pages=10`. It *already* breaks on
   `nextPageToken` exhaustion (lines 86-88) — but the `max_pages` ceiling can cut
   the walk short first. `_resolve_github_source` (line 100) paginates
   `/v1alpha/sources` at `pageSize=100`; a user with >1000 connected sources
   whose target is on page 11 gets a false "no Jules source connected" error
   (line 104). *The fix is to let `nextPageToken` exhaustion be the sole stop
   condition for source resolution — NOT a crude bump to `max_pages=1000`.*

3. **`jules.verify` trusts a caller-supplied bool (Medium sev × High
   likelihood).** `verify(self, state: str, branch_on_remote: bool)`
   (`agency/capabilities/jules.py:139-142`) computes `done` purely from the
   caller's `branch_on_remote` argument (line 141). Nothing independently checks
   the remote. An agent that hallucinates the branch landed can pass `True` and
   mark a silent-fail session as done — defeating the `COMPLETED != done` guard
   the whole capability exists for (module docstring, lines 1-6). The injected
   `vcs` boundary (`VCSBackend`, `agency/capabilities/_vcs.py:18-23`) exposes only
   `worktree`/`run`/`state`/`finish` — and `state()` (line 46) checks **LOCAL**
   ahead/behind via `git rev-list`, never the remote. There is **no
   `remote_exists` and no `git ls-remote` anywhere in the file.** `jules.verify`
   does not even inject `vcs` today (its `@verb` has no `inject=`, line 138).

4. **Code-mode sandbox `os.environ` exfiltration — premise REFUTED on the pinned
   stack; re-scoped to defense-in-depth (Low/Info residual).** The engine builds
   FastMCP with `CodeMode()` (`agency/engine.py:94`), which runs caller-supplied
   Python in the Monty sandbox. `_jules_api._api_key()`
   (`agency/capabilities/_jules_api.py:31-38`) reads `os.environ["JULES_API_KEY"]`
   **lazily, per request** (line 32; consumed at line 61). The original theory:
   if the sandbox can reach `os.environ`, a prompt-injected
   `import os; os.environ['JULES_API_KEY']` exfiltrates the key. **The REVIEW ran
   this as a RED probe against the real shipped sandbox (`pydantic-monty 0.0.16`,
   driven exactly as `code_mode.py:133-138`) and the vector is NOT reachable:**
   Monty is an allow-list reimplementation of Python, not a CPython `exec` —
   `os.environ`/`os.getenv` raise `NotImplementedError` (they are unwired host
   callbacks, no `os=` is passed), and `__import__`, `importlib`, `subprocess`,
   `open`, `eval`, and `globals()` are all undefined or denied. There is therefore
   **no in-process path** from sandbox code to `os.environ` or to a module global
   like `_jules_api._CAPTURED_KEY`. The genuine residual risk is *future drift* —
   a FastMCP/Monty version that wires an `os=` callback, a swapped-in
   `SandboxProvider`, or a future `external_function` that incidentally surfaces
   env. So #4 stays as cheap **defense-in-depth + a permanent RED-regression
   guard**: capture `JULES_API_KEY` into process-local state and `pop()` it from
   `os.environ` at the *sandbox boundary* (`build_mcp`, not `Engine.__init__`),
   while `_api_key()` still resolves it from the captured store. *Chesterton's
   fence:* the per-request read lets the key be exported in the launching shell,
   so the env var cannot simply be deleted — it must be captured first.

## Done When

- [ ] **(#1)** `Memory._max_persisted_tick` no longer issues an unconstrained
      `MATCH (n)` / `MATCH ()-[r]->()` materialization into Python; it resolves the
      seed tick in O(1) via **two server-side `max(vfrom)` aggregation queries —
      one over nodes, one over edges — taking the larger** (GraphQLite 0.5.0
      supports server-side `max()`, REVIEW-probed). **No `_Metadata:Clock` node is
      added.** Aggregate over `vfrom` only (never `vto`, which is `OPEN` for all live
      rows). The edge query is **not** optional — dropping it reintroduces the
      `link()` staleness bug documented at `memory.py:51-53`. The logical clock
      remains monotonic across reopens. A test seeds a graph (last write an edge),
      reopens `Memory`, and asserts the next `_now()` exceeds the previously-persisted
      max; the test **monkeypatches `self.g.query` to fail on the bare
      `"MATCH (n) RETURN n"`** so it proves the full scan is gone (behavioral, not
      just result-based). The seed read runs single-threaded in `__init__` before any
      worker thread exists — state this invariant in the test.
- [ ] **(#2)** `_resolve_github_source` paginates `/v1alpha/sources` until
      `nextPageToken` is exhausted (no `max_pages` ceiling on the source walk),
      with a `seen_tokens` repeated-token loop guard as the only stop other than real
      exhaustion. `jules_plan` keeps its explicit `max_pages`. A test with a stub
      `_request` returning 12 token-chained pages finds a source on the 11th page.
- [ ] **(#3)** `GitClient` gains `remote_exists(branch: str) -> bool` backed by
      `git ls-remote --heads origin <branch>`; `VCSBackend` Protocol declares it;
      `jules.verify` injects `vcs` and derives the remote check from it.
      **FAIL-CLOSED:** `done=False` whenever the remote cannot be independently
      verified — the `branch_on_remote` caller bool must NEVER flip `done` to `True`.
      A test injects a fake `vcs` whose `remote_exists` returns `False` and asserts
      `verify` reports `done=False` even when the caller would have claimed the
      branch landed; a second test omits `branch`/`vcs` and asserts `done=False`
      regardless of `state`.
- [ ] **(#4 — RED-regression test + defense-in-depth)** A regression test drives the
      **real** `MontySandboxProvider`/`Monty.run` path (the installed
      `pydantic-monty`, never a hand-rolled `exec()` which would false-RED) with
      `import os; return os.environ.get('JULES_API_KEY')` and asserts the result is a
      denial/`None` — documenting that Monty already blocks the vector and tripping
      if a future version wires an `os=` callback. Separately, `capture_api_key()` is
      called in **`build_mcp`** (the sandbox boundary, codemode branch) — NOT
      `Engine.__init__` — popping `JULES_API_KEY` from `os.environ` into a process-
      local store; `_jules_api._api_key()` reads that store, and a normal
      `jules.dispatch` still authenticates against the captured key.

## Design

Fix sketches (illustrative Python; final shape decided in RED→GREEN).

### #1 — O(1) clock seed via server-side `max(vfrom)` aggregation

Keep the bi-temporal guarantee but stop scanning. GraphQLite **0.5.0** (the
`requirements.txt` floor and installed version) supports server-side aggregation
— the REVIEW probed it live:

```
MATCH (n) RETURN max(n.vfrom) AS mx          -> [{'mx': 50}]
MATCH ()-[r]->() RETURN max(r.vfrom) AS mx   -> [{'mx': 77}]
```

So seed the clock with **two server-side `max(vfrom)` queries — one over nodes,
one over edges — and take the larger**. This is O(1) on the Python side (one row
each, not N+E rows), needs **no schema addition, no migration, and no
write-amplification**. The `_Metadata:Clock` singleton node is explicitly
**rejected**: it would add an `upsert_node` on every `_now()` (a real hot-path
cost on every `record`/`link`/`supersede`) and risk leaking into
`find`/`project`/`provenance`.

```python
# agency/memory.py
def _max_persisted_tick(self) -> int:
    # aggregate over vfrom ONLY: every tick ever assigned appears as some row's
    # vfrom; vto is only ever a prior tick or OPEN (10**12), so vfrom alone is a
    # sufficient high-water mark and we never read the OPEN sentinel.
    def _agg(cypher: str) -> int:
        try:
            rows = self.g.query(cypher)
        except Exception:
            return 0
        v = (rows[0].get("mx") if rows else 0) or 0
        return int(v) if isinstance(v, int) else 0
    node_mx = _agg("MATCH (n) RETURN max(n.vfrom) AS mx")
    # the edge query is NOT optional: link() (memory.py:82) advances the same clock
    # and persists vfrom on edges; if the last write before a reopen was an edge,
    # a node-only seed under-counts and new writes reuse stale ticks (memory.py:51-53).
    edge_mx = _agg("MATCH ()-[r]->() RETURN max(r.vfrom) AS mx")
    return max(node_mx, edge_mx)

# _now() is UNCHANGED — it stays a pure in-memory increment under self._lock:
def _now(self) -> int:
    with self._lock:
        self._tick += 1
        return self._tick
```

Concurrency invariant: `_max_persisted_tick()` runs in `__init__` before any
worker thread exists, so the seed read is single-threaded and needs no lock. State
this in the test so a future refactor that moves the seed doesn't silently break
it.

### #2 — pagination stops on token exhaustion

`_paginate` already breaks on `not token` (lines 87-88). Give the **source
resolution** path an uncapped walk while keeping a guard against a misbehaving
API (token that never empties) — e.g. a sentinel "no progress / repeated token"
break rather than a fixed page count:

```python
# agency/capabilities/_jules_api.py
def _paginate(path, params, max_pages=None):   # None => walk until token exhausts
    items, token, seen_tokens = [], "", set()
    array_key = None
    while True:
        q = dict(params)
        if token:
            q["pageToken"] = token
        raw = _request("GET", path, params=q)
        if array_key is None:
            array_key = next((k for k, v in raw.items() if isinstance(v, list)), None)
            if array_key is None:
                break
        items.extend(raw.get(array_key, []) or [])
        token = raw.get("nextPageToken", "")
        if not token or token in seen_tokens:   # exhausted, or API loop guard
            break
        seen_tokens.add(token)
        if max_pages is not None and len(seen_tokens) >= max_pages:
            break
    return items

# _resolve_github_source passes no cap -> walks to exhaustion
for s in _paginate("/v1alpha/sources", {"pageSize": 100}):
    ...
```

`jules_plan` (line 259) keeps its explicit `max_pages` (latest-plan scan is
intentionally bounded). Only the source walk goes uncapped.

### #3 — `remote_exists` on the VCS boundary, injected into `verify`

```python
# agency/capabilities/_vcs.py — Protocol + GitClient
class VCSBackend(Protocol):
    ...
    def remote_exists(self, branch: str) -> bool: ...

class GitClient:
    def remote_exists(self, branch: str) -> bool:
        # ls-remote queries ORIGIN (state() only checks LOCAL ahead/behind). No cwd,
        # matching state()'s rev-list calls (origin is repo-relative). The branch
        # arg is the *work* branch name, so base-branch casing (the-agency-system
        # uses `Master`, not `main`) does not bite this check.
        r = self._git("ls-remote", "--heads", "origin", branch)
        return r.returncode == 0 and bool(r.stdout.strip())
```

```python
# agency/capabilities/jules.py — verify derives the remote truth itself, FAIL-CLOSED
@verb(role="transform", inject=["vcs"])
def verify(self, vcs, state: str, branch: str = "") -> dict:
    "COMPLETED != done: done only if state==completed AND the branch is on origin."
    completed = str(state).lower() == "completed"
    if not branch or vcs is None:
        # cannot independently verify the remote -> FAIL CLOSED (never trust a caller bool)
        return {"done": False, "state": state, "branch_on_remote": False,
                "verified_via": "unverified"}
    try:
        on_remote = vcs.remote_exists(branch)
        via = "remote"
    except Exception:
        # ls-remote can fail for network/auth/detached-origin, not just "branch absent".
        # Treat any error as not-verified (fail closed) but surface WHY so a network
        # blip is not misread as a Jules silent-fail.
        on_remote, via = False, "remote-error"
    return {"done": completed and on_remote, "state": state,
            "branch_on_remote": on_remote, "verified_via": via}
```

`vcs` is already wired as an engine injector (`agency/engine.py:56`) and consumed
elsewhere via `inject=["vcs"]` (`branch.py:32,38`; `workspace.py:25,36`), so this
is the established pattern. The caller-supplied `branch_on_remote` bool is
**removed** — it was the entire hallucination vector. When the remote cannot be
independently confirmed, `done` is `False`; `verified_via` distinguishes a clean
`"remote"` (not on origin) from a `"remote-error"` (the check itself failed) and
`"unverified"` (no branch/vcs supplied).

### #4 — defense-in-depth capture-and-withhold + RED-regression probe

The REVIEW's RED probe proved the `os.environ` vector is **not reachable** under
the pinned `pydantic-monty 0.0.16` (see `## Why` #4). So this is no longer a
closed hole — it is cheap insurance against version drift plus a permanent
tripwire. The key is read per-request, so we cannot simply delete it: capture it
into a process-local store **at the sandbox boundary (`build_mcp`)** and `pop()`
it from `os.environ`, then have `_api_key()` read the store.

```python
# agency/capabilities/_jules_api.py
_CAPTURED_KEY: str | None = None

def capture_api_key() -> None:
    """Move JULES_API_KEY out of os.environ into process-local state. Defense in
    depth: the pinned Monty sandbox already denies os.environ/import/globals (so
    _CAPTURED_KEY is NOT sandbox-reachable today, per the REVIEW probe) — this
    guards against a future Monty that wires an os= callback or a swapped provider."""
    global _CAPTURED_KEY
    v = os.environ.pop("JULES_API_KEY", None)
    if v:
        _CAPTURED_KEY = v

def _api_key() -> str:
    key = _CAPTURED_KEY or os.environ.get("JULES_API_KEY", "")
    if not key:
        raise RuntimeError("JULES_API_KEY is not set. Export it ... then retry.")
    return key
```

```python
# agency/engine.py — capture in build_mcp at the sandbox boundary, NOT __init__
# (capturing in __init__ would mutate os.environ for every Engine(...) including
# test fixtures and library callers that never build the CodeMode surface).
def build_mcp(self, codemode: bool = True) -> FastMCP:
    if codemode and HAVE_CODEMODE:
        from .capabilities import _jules_api
        _jules_api.capture_api_key()          # withhold the key before CodeMode() is wired
    transforms = [CodeMode()] if (codemode and HAVE_CODEMODE) else []
    mcp = FastMCP("agency", transforms=transforms)
    ...
```

Do **not** make the key import-time (cf. `_jules_api.py:19`'s import-time
`JULES_API_BASE_URL` read) — the lazy `_api_key()` read is precisely what makes
capture-then-withhold viable.

**RED-regression test (drive the REAL sandbox, never a hand-rolled `exec()`):**

```python
def test_codemode_sandbox_cannot_read_jules_key(monkeypatch):
    monkeypatch.setenv("JULES_API_KEY", "secret-xyz")
    # Drive the actual MontySandboxProvider / Monty.run path (the installed
    # pydantic-monty) — a plain exec() stand-in would FALSE-RED (it leaks).
    result = run_in_real_monty("import os\nreturn os.environ.get('JULES_API_KEY')")
    assert result is None or "not implemented" in str(result).lower()   # Monty denies it today
    # After build_mcp() the key is captured but still resolves for the capability:
    eng = Engine(":memory:"); eng.build_mcp()
    assert _jules_api._api_key() == "secret-xyz"
    # Negative note: the only host-reachable surface is `call_tool`; no agency verb
    # returns raw env — a future verb that does must be caught here.
```

## Files

- **Modify**:
  - `agency/memory.py` — `_max_persisted_tick` O(1) seed via two server-side
    `max(vfrom)` aggregations (nodes + edges); `_now()` UNCHANGED (#1).
  - `agency/capabilities/_jules_api.py` — `_paginate` token-exhaustion walk +
    `seen_tokens` loop guard (#2); `capture_api_key()` + `_api_key()` reads captured
    store (#4).
  - `agency/capabilities/_vcs.py` — `remote_exists` on `VCSBackend` + `GitClient` (#3).
  - `agency/capabilities/jules.py` — `verify` injects `vcs`, derives remote check,
    drops the `branch_on_remote` bool, fails closed (#3).
  - `agency/engine.py` — call `capture_api_key()` in `build_mcp` (codemode branch),
    NOT `Engine.__init__` (#4).
- **Create**:
  - `tests/test_hardening.py` — one test per fix (clock seed with bare-scan
    monkeypatch guard, uncapped 12-page pagination, fail-closed remote-derived
    verify, real-Monty RED-regression env-leak probe).
- **Move / Delete**: none. The `_Metadata:Clock` node is explicitly NOT added (#1).

## Open Questions / Needs Research

The three original open questions were all **RESOLVED** by the REVIEW's live
probes; none blocks implementation. Recorded here for provenance:

1. **Is the `os.environ` read exploitable under Monty? — RESOLVED: No (pinned
   stack).** A RED probe against the real `pydantic-monty 0.0.16` sandbox denied
   `os.environ`/`os.getenv`/attribute-`import os`/`__import__`/`importlib`/
   `subprocess`/`open`/`eval`/`globals` — every vector unimplemented or undefined.
   The escape is not even theoretically reachable in-process today. #4 is therefore
   defense-in-depth + a RED-regression tripwire, not a closed hole; FINDINGS.md §1
   should be downgraded from High to Low/Info with the probe transcript attached.

2. **Where to clear the key? — RESOLVED: `build_mcp` (codemode branch), not
   `Engine.__init__`.** Scoped to the actual sandbox boundary; avoids mutating
   `os.environ` for non-MCP `Engine` users and test fixtures. The module-global
   `_CAPTURED_KEY` is acceptable *because* the probe shows it is not sandbox-
   reachable (no `import`, no `globals`); an out-of-process secret holder or Monty
   deny-list is over-engineering given that finding — revisit only if a future
   Monty version wires an `os=` callback.

3. **Does GraphQLite support server-side `max()`? — RESOLVED: Yes (0.5.0).**
   Probed live (`MATCH (n) RETURN max(n.vfrom)` returns one row). Use the
   aggregation form over BOTH nodes and edges; the `_Metadata:Clock` node is NOT
   added (avoids write-amplification and the find/project/provenance-leak hazard).
   This collapses #1 to a clean, migration-free change with no schema addition.

Remaining watch-items (non-blocking, noted for the implementer):

- **#2 has no overall page budget.** An uncapped walk is correct, but a 10k-source
  account now pages ~100 times per `_coerce_source` call. Acceptable (source
  resolution is rare); add a one-line comment that `seen_tokens` is the sole stop
  other than real exhaustion.
- **#1 reopen test must be behavioral, not result-only** (monkeypatch the bare
  `MATCH (n) RETURN n` to fail) so the scan can't silently survive.

## Evidence

All citations re-pinned against branch `claude/extract-agency-plugin-o4JRc`
(research line numbers had drifted; corrections noted):

- **#1** `agency/memory.py:37` (`self._tick = self._max_persisted_tick()`),
  `:39-62` (`_max_persisted_tick`), `:42` (`MATCH (n) RETURN n`),
  `:55` (`MATCH ()-[r]->() RETURN r`). *(Research said `35-51`; corrected.)*
- **#2** `agency/capabilities/_jules_api.py:70` (`def _paginate(... max_pages=10)`),
  `:75` (`while pages < max_pages`), `:86-88` (existing token break),
  `:100` (`_resolve_github_source` paginates `/v1alpha/sources`),
  `:104` ("no Jules source connected"). *(Research said `:53`; corrected to `:70`.)*
- **#3** `agency/capabilities/jules.py:138-142` (`verify`, `branch_on_remote` at
  `:139`, `done` derivation at `:141`). `agency/capabilities/_vcs.py:18-23`
  (`VCSBackend` exposes only `worktree`/`run`/`state`/`finish`), `:46-54`
  (`state()` uses LOCAL `git rev-list` ahead/behind, **no remote**). No
  `remote_exists`/`git ls-remote` present anywhere in `_vcs.py` (verified by grep).
  `vcs` injector wired at `agency/engine.py:56`; consumed via `inject=["vcs"]` at
  `branch.py:32,38` and `workspace.py:25,36`. *(Research said `jules.py:46-50`;
  corrected to `:138-142`.)*
- **#4** `agency/engine.py:94` (`CodeMode()` in `transforms`), `:95`
  (`FastMCP("agency", transforms=...)`). `agency/capabilities/_jules_api.py:31-38`
  (`_api_key`), `:32` (`os.environ.get("JULES_API_KEY", "")`, read lazily),
  `:61` (consumed in `_request` headers). Engine/CLI do not touch `JULES_API_KEY`
  today (grep: zero hits). *(All citations verified accurate.)* **REVIEW probe
  against `pydantic-monty 0.0.16`** (driven as `code_mode.py:133-138`, no `os=`):
  `os.environ`/`os.getenv` → `NotImplementedError`; `__import__`/`importlib`/
  `subprocess`/`open`/`eval`/`globals` → undefined/`ModuleNotFoundError`. Monty is
  an allow-list reimplementation (`pydantic_monty/os_access.py:194-197`,
  `:925-929`); FastMCP's `MontySandboxProvider.run` passes no `os=`, so the vector
  is unreachable — premise refuted, severity downgraded to Low/Info.
