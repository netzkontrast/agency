# REVIEW — Spec 006 Core Hardening (spec-panel + security-engineer)

> Reviewer pass over `Plan/inprogress/006-core-hardening/spec.md`. Every citation re-verified
> against the live code on this tree; the Monty exploitability question was settled
> by a **RED probe run against the actual `pydantic-monty 0.0.16` sandbox** (the
> version pinned in `requirements.txt`), not by inference.

## Verdict

**Approve with required revisions.** Three of the four fixes are sound and
correctly grounded (#1, #2, #3). Fix #4's *premise* is empirically false on the
shipped stack — the `os.environ` exfiltration vector is **not reachable** under
Monty — so #4 must be re-scoped from "High-sev hole" to documented
defense-in-depth, and its test reframed as a regression guard. The spec already
anticipated this in Open Question #1 and prescribed the right action (RED probe
first); this review executes that probe and records the result. All `path:line`
citations in `## Evidence` are accurate.

---

## Per-fix verification

### #1 — CLI-boot full graph scan → O(1) seed. CONFIRMED; design CHOICE corrected.

Citations all hold against the current file:

- `agency/memory.py:37` — `self._tick = self._max_persisted_tick()`. Confirmed.
- `agency/memory.py:39-62` — `_max_persisted_tick`. Confirmed.
- `agency/memory.py:42` — `rows = self.g.query("MATCH (n) RETURN n")`. Confirmed
  (full node materialization into Python, then a `for r in rows` max loop).
- `agency/memory.py:55` — `erows = self.g.query("MATCH ()-[r]->() RETURN r")`.
  Confirmed (a *second* full scan, of every edge). The Chesterton's-fence note in
  the spec is right: the edge scan was added deliberately because `link()`
  (`memory.py:82`) advances the same clock and persists `vfrom` on edges, so a
  node-only seed under-counts after an edge was the last write.

The diagnosis is correct: the bash CLI opens a fresh `Engine` → fresh `Memory`
per invocation (`engine.py:57` constructs `Memory(path, …)` inside
`Engine.__init__`), so this O(N+E) materialization runs on **every** command.

**Correction to the spec's recommendation (load-bearing).** The spec hedges
between two designs and leaves the choice to Open Question #3 ("does GraphQLite's
Cypher support server-side `max()`?"). **I resolved this empirically.**
GraphQLite **0.5.0** (the `requirements.txt` floor, and the installed version)
**does** support server-side aggregation. Probe result:

```
MATCH (n) RETURN max(n.vfrom) AS mx          -> [{'mx': 50}]
MATCH ()-[r]->() RETURN max(r.vfrom) AS mx   -> [{'mx': 77}]
MATCH (n) RETURN count(n) AS c               -> [{'c': 5}]
MATCH (n) RETURN n.vfrom AS v ORDER BY v DESC LIMIT 1 -> [{'v': 50}]
```

Therefore the **aggregation form is the correct fix, and the `_Metadata:Clock`
singleton node should NOT be built.** Two server-side `max()` queries (one over
nodes, one over edges), taking the larger and guarding `OPEN` (`10**12`), is:

- O(1) on the Python side (returns one row, not N+E rows);
- requires **no schema addition**, **no migration**, **no write-amplification**
  (the Clock-node design adds one `upsert_node` on every single `_now()` —
  i.e. on every `record`/`link`/`supersede`, a real hot-path cost);
- carries **no risk** of a singleton leaking into `find`/`project`/`provenance`
  (the spec itself flags this Clock-node hazard at spec.md:298-300 and admits it
  "needs a test").

One subtlety the aggregation must handle that the spec's sketch glosses: `vto`
is `OPEN` (`10**12`) for all live rows, so a naive `max(n.vto)` would always
return the sentinel. The current scan already excludes `OPEN` (`memory.py:49`).
The replacement must `max()` over `vfrom` only (every tick that has ever been
assigned appears as some row's `vfrom`; `vto` is only ever a *prior* tick or
`OPEN`, so `vfrom` alone is a sufficient high-water mark). **Must-fix:** the
implementation must `max(vfrom)` over BOTH nodes and edges and take the larger —
dropping the edge query reintroduces exactly the staleness bug the comment at
`memory.py:51-53` documents.

The `the-agency-system` prior art (`/home/user/the-agency-system/agency/agency/memory.py:39-51`)
is the *older, node-only* version of this scan — it does not have an O(1) clock
and is in fact buggier (no edge scan at all). There is no O(1)-tick prior art to
borrow; the aggregation approach is net-new and correct.

### #2 — Pagination cap truncates source resolution. CONFIRMED.

- `_jules_api.py:70` — `def _paginate(path, params, max_pages=10)`. Confirmed.
- `:75` — `while pages < max_pages:`. Confirmed (the ceiling).
- `:86-88` — `token = raw.get("nextPageToken", "")` then `if not token: break`.
  Confirmed (token exhaustion already breaks).
- `:100` — `_resolve_github_source` paginates `/v1alpha/sources` at `pageSize=100`.
  Confirmed.
- `:104` — the false "no Jules source connected" error. Confirmed.
- `:259` (`jules_plan`) passes an explicit `max_pages`. Confirmed — keeping that
  call bounded is correct (latest-plan scan is intentionally finite).

The fix is well-judged: make `max_pages=None` mean "walk to token exhaustion",
keep an explicit cap on `jules_plan`, and add a **repeated-token loop guard**
(`seen_tokens`) so a misbehaving API that never empties `nextPageToken` cannot
spin forever. That loop guard is a genuine robustness add over the current code,
which would infinite-loop on a non-empty constant token if the ceiling were
simply removed. Good.

One nit on the sketch: the proposed `_paginate` rewrite changes the
`array_key`-discovery semantics slightly (it now discovers the key only on the
first page and breaks if absent) — this matches current behavior at `:81-84`, so
no regression, but the test must cover a 12-page token chain where the match is
on page 11 (the `Done When` test already specifies this).

### #3 — `jules.verify` trusts a caller bool. CONFIRMED; honors the §8 doctrine.

- `jules.py:138-142` — `verify(self, state, branch_on_remote)`; `done` derived
  purely from `bool(branch_on_remote)` at `:141`. Confirmed verbatim.
- `:138` — the `@verb(role="transform")` has **no `inject=`**. Confirmed — `verify`
  cannot see `vcs` today.
- `_vcs.py:18-23` — `VCSBackend` Protocol exposes only
  `worktree`/`run`/`state`/`finish`. Confirmed.
- `_vcs.py:46-54` — `state()` uses `git rev-list --count base..branch` /
  `branch..base` (LOCAL ahead/behind) and `git status --porcelain`. **No remote
  call.** Confirmed.
- **No `remote_exists` / `ls-remote` anywhere in the package.** Verified by grep
  across `agency/` — zero hits. Confirmed.
- The `vcs` injector is wired at `engine.py:56` (`"vcs": lambda: self.vcs_backend`)
  and consumed via `inject=["vcs"]` at `branch.py:32,38` and `workspace.py:25,36`.
  Confirmed — the injection pattern the fix reuses is real and established.

This fix directly enforces the canon. `JULES_PROTOCOL.md` §8-Appendix (lines
153-156) states the silent-fail mode precisely: "the session transitions to
`COMPLETED` but no branch lands on the remote … `state=COMPLETED` is *not*
terminal." The orchestrator's authoritative check is the branch *on origin*
(the-agency-system CLAUDE.md: "Always verify the branch on remote before trusting
`COMPLETED`"). Trusting a caller-supplied `branch_on_remote` bool is exactly the
hallucination vector the whole capability exists to close (jules.py module
docstring, lines 1-6). Deriving the truth from `vcs.remote_exists(branch)` →
`git ls-remote --heads origin <branch>` is the right boundary.

Three correctness points the implementation MUST get right:

1. **`branch_on_remote` must NOT remain a trusted fallback that can flip `done`
   to `True`.** The spec sketch (spec.md:197-205) keeps `branch_on_remote` as an
   optional fallback "logged as untrusted" and still lets it drive `done` when no
   branch/vcs is supplied. That re-opens the hole for any caller who omits
   `branch`. **Must-fix:** when the remote cannot be independently verified,
   `done` must be `False` (or the verb must hard-require `branch`), never the
   caller's word. `verified_via:"caller"` returning `done=True` defeats the fix.
2. **Default base branch is capitalised `Master` in the-agency-system, not
   `main`.** `ls-remote --heads origin <branch>` only ever checks the *work*
   branch name, so base-branch casing does not bite `remote_exists` directly —
   but any test or doc that hard-codes `origin/main` will mislead. Note it; the
   work-branch check itself is base-agnostic, which is correct.
3. **`GitClient._git` does not pass `cwd` for `ls-remote`** in the sketch — that
   is fine (origin is repo-relative and the engine runs in the repo root), and it
   matches how `state()` calls `rev-list` without `cwd`. Keep it consistent.

### #4 — Code-mode sandbox reads `os.environ`. PREMISE REFUTED by RED probe; re-scope to defense-in-depth.

Citations are accurate:

- `engine.py:94` — `transforms = [CodeMode()] …`; `:95` —
  `FastMCP("agency", transforms=transforms)`. Confirmed (spec says `:94` for
  `CodeMode()`; on this tree the `CodeMode()` call is on line 94 inside the
  `transforms` list comprehension — accurate).
- `_jules_api.py:31-38` — `_api_key()`; `:32` —
  `os.environ.get("JULES_API_KEY", "")` read lazily; `:61` — consumed in the
  `_request` header. Confirmed.
- The engine/CLI do **not** touch `JULES_API_KEY` today (grep: zero hits in
  `engine.py`/`cli.py`). Confirmed — there is no existing capture/clear.

**Security-engineer finding (the load-bearing one).** I ran the env-leak as a
RED probe against the real sandbox the engine ships (`pydantic-monty 0.0.16`,
driven exactly as `code_mode.py:133-138` drives it:
`Monty(code).run_async(external_functions={"call_tool": …})`, with **no `os=`
argument**). Results, with `JULES_API_KEY=secret-xyz` set in the host:

```
import os; os.environ.get('JULES_API_KEY')   -> NotImplementedError: OS function 'os.environ' not implemented
import os; dict(os.environ)...               -> NotImplementedError: OS function 'os.environ' not implemented
import os; os.getenv('JULES_API_KEY')        -> NotImplementedError: OS function 'os.getenv' not implemented
from importlib import import_module          -> ModuleNotFoundError: No module named 'importlib'
__import__('os')                             -> NameError: name '__import__' is not defined
import subprocess                            -> ModuleNotFoundError: No module named 'subprocess'
globals() / __builtins__ / open() / eval()   -> NameError (all undefined)
```

Why: Monty is an **allow-list reimplementation of Python**, not a CPython
`exec`. `os.environ`/`os.getenv` are not attributes — they are *host callbacks*
routed through an `AbstractOS` instance passed as `Monty.run(os=…)`
(`pydantic_monty/os_access.py:194-197`, `OSAccess.get_environ`/`getenv` at
`:925-929`). FastMCP's `MontySandboxProvider.run` (`code_mode.py:112-138`)
**passes no `os=`**, so the callback surface is unwired and every `os.*` call
raises `NotImplementedError`. There is no `__import__`, no `importlib`, no
`open`, no `eval`, no `globals()` — so there is no path from sandbox code to
`os.environ`, to a module global like `_jules_api._CAPTURED_KEY`, or to the real
filesystem. The only host-reachable surface is the injected `external_functions`
(here exactly one: `call_tool`), and no agency verb returns raw environment.

**Conclusion:** the High-sev premise ("if the sandbox can reach `os.environ`")
is **false on the shipped stack**. FINDINGS.md §1's escape is, in its own words,
"architecturally present but theoretical" — and the probe shows it is not even
theoretically reachable through `os`, imports, or builtins under pinned Monty.

This does **not** make fix #4 worthless, but it changes what it is:

- **Re-scope #4 from "High × Medium closed hole" to "Low-residual,
  defense-in-depth + version-drift guard."** The genuine residual risk is *not*
  today's sandbox; it is (a) a future FastMCP/Monty version that wires an `os=`
  callback proxying the real environ, or (b) a custom `SandboxProvider` swapped
  in, or (c) a future `external_function` that incidentally surfaces env. Capture-
  and-withhold is cheap insurance against those, and it is the correct first
  layer regardless.
- **The env-leak test should be the RED probe, kept as a permanent regression
  guard.** Per the spec's own Open Question #1: write it first; it returns "no
  leak" *before* any code change (as proven above); document that Monty already
  blocks the vector; then land `capture_api_key()` as belt-and-suspenders and
  keep the test green as a tripwire for the version-drift case. The test must
  drive the **real** `MontySandboxProvider`/`Monty.run` path — a hand-rolled
  `exec()` stand-in would give a *false RED* (plain exec leaks) and mislead the
  whole assessment. Use the installed `pydantic-monty`, not a fake.
- **`capture_api_key()` home (Open Question #2): `build_mcp` is correct, not
  `Engine.__init__`.** Capturing in `__init__` mutates global `os.environ` for
  every `Engine(...)` including test fixtures and library callers who never build
  the MCP/CodeMode surface — a surprising, hard-to-debug side effect (a fixture
  that sets `JULES_API_KEY` then constructs an `Engine` would find the var gone).
  The threat only exists when `CodeMode()` is instantiated, so scope the pop to
  `build_mcp(codemode=True)`, immediately before `FastMCP(..., transforms=…)`. The
  module-global `_CAPTURED_KEY` is acceptable *because* the probe shows it is not
  sandbox-reachable (no `import`, no `globals`) — but say so explicitly in the
  code comment so a future reader does not assume the global is the weak point.
- **Watch the import-time read of `JULES_API_BASE_URL` (`_jules_api.py:19`).**
  Not a secret, so out of scope, but note that module-level env reads bake in
  whatever was set at import; `_api_key()` reads lazily, which is what makes
  capture-then-withhold viable. No change needed; just don't "fix" #4 by making
  the key import-time too.

---

## Missing depth / risk

- **#1 write-path interaction unexamined.** The spec's Clock-node sketch upserts
  on every `_now()`. Even the (recommended) aggregation form must be checked
  against concurrency: `_now()` holds `self._lock` (`memory.py:65`), but
  `_max_persisted_tick()` runs in `__init__` *before* any worker thread exists,
  so the seed read is single-threaded — safe. State this invariant in the test so
  a future refactor that moves the seed doesn't silently break it.
- **#1 reopen test must assert no full materialization.** "Done When" #1 says
  "without scanning all rows," but an assertion on behavior (not just result) is
  needed — e.g. monkeypatch `self.g.query` to fail on `"MATCH (n) RETURN n"`
  (bare, no aggregation) and assert the seed still resolves via the `max()` query.
  Otherwise the test passes even if the scan is left in.
- **#2 cost ceiling removed but no overall budget.** Uncapped walk to exhaustion
  is right for correctness, but a 10k-source account now pages 100 times per
  `_coerce_source` call. Acceptable (source resolution is rare and cached-by-call),
  but worth a one-line comment that the `seen_tokens` guard is the only stop other
  than real exhaustion.
- **#3 has no remote-call failure mode.** `git ls-remote` can fail for reasons
  other than "branch absent" (no network, auth, detached origin). The sketch's
  `r.returncode == 0 and bool(r.stdout.strip())` treats *any* non-zero as "not on
  remote" → `done=False`. That is the safe default (fail closed), but the verb
  should surface *why* (e.g. `verified_via:"remote-error"`) so a network blip is
  not silently read as "Jules silent-failed." Add it to the return dict.
- **#4 — no negative test for the `external_functions` surface.** Since the only
  host reach is `call_tool`, add an assertion (or at least a comment in the test)
  that no agency verb returns raw env, so a future verb that does is caught.

---

## Open-Questions triage

1. **Is `os.environ` exploitable under Monty? — RESOLVED: No (on pinned stack).**
   RED probe run; `os.environ`/`os.getenv`/`import os`-attribute/`__import__`/
   `importlib`/`subprocess`/`open`/`eval`/`globals` all denied or unimplemented.
   **Recommendation stands and is now evidence-backed:** keep #4 as the RED-probe
   regression test + defense-in-depth `capture_api_key()` in `build_mcp`; downgrade
   FINDINGS.md §1 severity from High to Low/Info with this probe transcript
   attached. The RED-probe-first approach is the correct discipline — adopt it.
2. **Where to clear the key? — RESOLVED: `build_mcp` (codemode branch), not
   `__init__`.** Scoped to the actual sandbox boundary; avoids mutating env for
   non-MCP `Engine` users and test fixtures. Out-of-process secret holder /
   Monty deny-list is over-engineering given the probe shows no in-process reach;
   revisit only if a future Monty version wires an `os=` callback.
3. **Does GraphQLite support server-side `max()`? — RESOLVED: Yes (0.5.0).**
   Probed live. Use the aggregation form; **do not** add the `_Metadata:Clock`
   node (avoids write-amplification + the find/project/provenance-leak hazard the
   spec itself worried about). This collapses #1 to a clean, migration-free change.

All three open questions are answerable now; none needs to block implementation.

---

## Must-fix list (blocking)

1. **#1 — use server-side `max(vfrom)` aggregation over BOTH nodes and edges;
   drop the `_Metadata:Clock` node entirely.** GraphQLite 0.5.0 supports it
   (probed). Take the larger of node-max and edge-max; the edge query is not
   optional (it guards the documented `link()` staleness bug at memory.py:51-53).
2. **#3 — when the remote cannot be independently verified, `done` must be
   `False`.** Do not let the `branch_on_remote` fallback flip `done=True` on the
   caller's word (spec sketch spec.md:197-205 does). Hard-require `branch`+`vcs`
   for a `True`, or fail closed. This is the entire point of the fix.
3. **#4 — reframe as RED-probe regression test + defense-in-depth, run against
   the REAL Monty sandbox (`MontySandboxProvider`), and put `capture_api_key()` in
   `build_mcp` not `Engine.__init__`.** The env-leak test must drive
   `pydantic-monty`, never a hand-rolled `exec()` (which would false-RED). Update
   the spec's "Why" / severity for #4 to record that the `os.environ` vector is
   not reachable on the pinned stack.

### Should-fix (non-blocking)

- #1 reopen test asserts the bare `MATCH (n) RETURN n` scan is gone (behavioral,
  not just result-based).
- #3 returns a `verified_via:"remote-error"` distinct from a clean "not on
  remote" so network failures aren't misread as silent-fail.
- #2 add a one-line comment that `seen_tokens` is the sole non-exhaustion stop.
