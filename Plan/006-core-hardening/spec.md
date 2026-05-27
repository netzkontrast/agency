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
> Only touch paths under `affects:`.

## Why

Four architectural risks in the PR1 core, each verified against the code at the
cited line on branch `claude/extract-agency-plugin-o4JRc`:

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

4. **Code-mode sandbox can read `os.environ` (High sev × Medium likelihood).**
   The engine builds FastMCP with `CodeMode()` (`agency/engine.py:94`), which
   runs caller-supplied Python in the Monty sandbox. `_jules_api._api_key()`
   (`agency/capabilities/_jules_api.py:31-38`) reads `os.environ["JULES_API_KEY"]`
   **lazily, per request** (line 32; consumed at line 61). If the sandbox can
   reach `os.environ`, a prompt-injected `import os; os.environ['JULES_API_KEY']`
   exfiltrates the key. *Chesterton's fence:* the per-request read lets the key
   be exported in the launching shell — so we cannot just delete the env var;
   we must **capture it into process-local state at engine boot, then withhold
   it from `os.environ`** so the sandbox sees nothing, while `_api_key()` still
   resolves it.

## Done When

- [ ] **(#1)** `Memory._max_persisted_tick` no longer issues an unconstrained
      `MATCH (n)` / `MATCH ()-[r]->()` scan; it resolves the seed tick in O(1)
      (single aggregation query, or read of a `_Metadata:Clock` node), and the
      logical clock remains monotonic across reopens. A test seeds a graph, reopens
      `Memory`, and asserts the next `_now()` exceeds the previously-persisted max
      without scanning all rows.
- [ ] **(#2)** `_resolve_github_source` paginates `/v1alpha/sources` until
      `nextPageToken` is exhausted (no `max_pages` ceiling on the source walk).
      A test with a stub `_request` returning 12 token-chained pages finds a source
      on the 11th page.
- [ ] **(#3)** `GitClient` gains `remote_exists(branch: str) -> bool` backed by
      `git ls-remote`; `VCSBackend` Protocol declares it; `jules.verify` injects
      `vcs` and derives the remote check from it rather than trusting a caller bool.
      A test injects a fake `vcs` whose `remote_exists` returns `False` and asserts
      `verify` reports `done=False` even when the caller would have claimed the
      branch landed.
- [ ] **(#4 — env-leak unit test)** The `JULES_API_KEY` is captured at engine
      construction and removed from `os.environ`; `_jules_api._api_key()` reads it
      from the captured store. A unit test runs the engine's `execute` path (or its
      in-process equivalent) with `import os; return os.environ.get('JULES_API_KEY')`
      and asserts the result is `None`, while a normal `jules.dispatch` still
      authenticates against the captured key.

## Design

Fix sketches (illustrative Python; final shape decided in RED→GREEN).

### #1 — O(1) clock seed via a `_Metadata:Clock` node

Keep the bi-temporal guarantee but stop scanning. On every `_now()` increment,
upsert the running tick onto a single well-known node; seed from it on boot.

```python
# agency/memory.py
_CLOCK_ID = "_meta:clock"   # the one mutable singleton outside the bi-temporal axes

def _max_persisted_tick(self) -> int:
    node = self.g.get_node(self._CLOCK_ID)
    if node is not None:
        return int(node["properties"].get("tick", 0))
    # one-time migration for pre-existing graphs: bounded aggregation, not a
    # Python-side full scan. Prefer a single MAX() query if GraphQLite supports it:
    #   MATCH (n) RETURN max(n.vfrom) AS a   /  MATCH ()-[r]->() RETURN max(r.vfrom) AS b
    # Fall back to the legacy scan ONLY when the Clock node is absent.
    return self._legacy_scan_max_tick()

def _now(self) -> int:
    with self._lock:
        self._tick += 1
        # O(1) write of the singleton; not on the bi-temporal axes (no vfrom/vto)
        self.g.upsert_node(self._CLOCK_ID, {"tick": self._tick}, label="_Metadata")
        return self._tick
```

Notes: the Clock node is a plain singleton (no `vfrom`/`vto`), so `find`/
`project`/`provenance` (which filter on those axes) never surface it. The
aggregation form (`max(n.vfrom)`) is preferred if GraphQLite's Cypher supports
`max()` server-side; otherwise the Clock node is the portable fallback.

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
        # ls-remote queries ORIGIN (state() only checks LOCAL ahead/behind)
        r = self._git("ls-remote", "--heads", "origin", branch)
        return r.returncode == 0 and bool(r.stdout.strip())
```

```python
# agency/capabilities/jules.py — verify derives the remote truth itself
@verb(role="transform", inject=["vcs"])
def verify(self, vcs, state: str, branch: str = "", branch_on_remote: bool | None = None) -> dict:
    "COMPLETED != done: done only if state==completed AND the branch is on origin."
    if branch and vcs is not None:                       # authoritative path
        on_remote = (vcs or GitClient()).remote_exists(branch)
    else:                                                # fallback: caller assertion (logged as untrusted)
        on_remote = bool(branch_on_remote)
    done = str(state).lower() == "completed" and on_remote
    return {"done": done, "state": state, "branch_on_remote": on_remote,
            "verified_via": "remote" if (branch and vcs is not None) else "caller"}
```

`vcs` is already wired as an engine injector (`agency/engine.py:56`) and consumed
elsewhere via `inject=["vcs"]` (`branch.py:32,38`; `workspace.py:25,36`), so this
is the established pattern. Keeping `branch_on_remote` as an optional fallback
avoids breaking callers that cannot supply a branch name, but `verified_via`
flags when the result is merely the caller's word.

### #4 — capture-and-withhold `JULES_API_KEY` from the sandbox

The key is read per-request, so we cannot simply delete it. Capture it into a
process-local store at engine boot and `pop()` it from `os.environ`, then have
`_api_key()` read the store:

```python
# agency/capabilities/_jules_api.py
_CAPTURED_KEY: str | None = None

def capture_api_key() -> None:
    """Move JULES_API_KEY out of os.environ into process-local state so the
    code-mode sandbox (which can read os.environ) cannot exfiltrate it."""
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
# agency/engine.py — call once at construction (or in build_mcp before CodeMode)
from .capabilities import _jules_api
_jules_api.capture_api_key()
```

A module-global captured in the engine process is still reachable by sufficiently
determined sandbox code (`_jules_api._CAPTURED_KEY`) — see Open Questions for
where the real boundary is. This fix closes the *obvious* `os.environ` vector,
which is the one the repro in FINDINGS.md exploits.

**Env-leak unit test idea:**

```python
def test_codemode_sandbox_cannot_read_jules_key(monkeypatch):
    monkeypatch.setenv("JULES_API_KEY", "secret-xyz")
    eng = Engine(":memory:")                  # construction triggers capture_api_key()
    leaked = run_in_sandbox("import os\nreturn os.environ.get('JULES_API_KEY')")
    assert leaked is None
    # and the key still works for the capability:
    assert _jules_api._api_key() == "secret-xyz"
```

## Files

- **Modify**:
  - `agency/memory.py` — `_max_persisted_tick` O(1) seed + `_now` Clock upsert (#1).
  - `agency/capabilities/_jules_api.py` — `_paginate` token-exhaustion walk (#2);
    `capture_api_key()` + `_api_key()` reads captured store (#4).
  - `agency/capabilities/_vcs.py` — `remote_exists` on `VCSBackend` + `GitClient` (#3).
  - `agency/capabilities/jules.py` — `verify` injects `vcs`, derives remote check (#3).
  - `agency/engine.py` — call `capture_api_key()` at boot/`build_mcp` (#4).
- **Create**:
  - `tests/test_hardening.py` — one test per fix (clock seed, uncapped pagination,
    remote-derived verify, sandbox env-leak).
- **Move / Delete**: none.

## Open Questions / Needs Research

1. **Is the `os.environ` read actually exploitable under Monty's restrictions?**
   FINDINGS.md §1 and both research self-reviews flag that the FastMCP `CodeMode`
   /Monty sandbox was *not* tested directly — the escape is "architecturally
   present but theoretical." If Monty already blocks `import os` (or strips
   `os.environ`), fix #4 is defense-in-depth, not a closed hole. **Action:** write
   the env-leak test first as a RED probe — if it already returns `None` before any
   change, document Monty's restriction and downgrade #4 to belt-and-suspenders.

2. **What is the right home to clear/withhold the key?** Options: (a) `Engine.__init__`
   (every engine, including tests — may surprise fixtures that set the env); (b)
   `build_mcp` right before `CodeMode()` is instantiated (scoped to the actual
   sandbox boundary); (c) the CLI entry / `agency/cli.py` (covers the bash path but
   not direct `build_mcp` callers). Capturing into a `_jules_api` module global is
   itself reachable from sandbox code (`_jules_api._CAPTURED_KEY`) — does the real
   fix need an out-of-process secret holder or a Monty deny-list, making the
   env-pop merely the first layer?

3. **Does GraphQLite's Cypher support server-side `max()` aggregation?** If yes,
   #1 can be a one-line `MATCH (n) RETURN max(n.vfrom)` with no schema addition and
   no migration concern. If not, the `_Metadata:Clock` singleton is required — which
   adds a node that every `find`/`project`/`provenance` path must be confirmed to
   ignore (it carries no `vfrom`/`vto`, so it should fall out of those filters, but
   this needs a test). Also: should the Clock node persist `tick` on every `_now()`
   (write amplification — one extra upsert per logical event) or be flushed lazily
   on `close()` (risk of losing the last tick on a hard crash, reintroducing reuse)?

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
  `:61` (consumed in `_request` headers). *(Research cited `engine.py:94` and
  `_jules_api.py:32` — both verified accurate.)*
