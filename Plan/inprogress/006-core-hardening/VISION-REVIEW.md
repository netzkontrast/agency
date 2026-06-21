# VISION-REVIEW — Spec 006 Core Hardening

> Vision-alignment pass over `Plan/inprogress/006-core-hardening/spec.md` against the canon
> (`docs/vision/CORE.md` authoritative; `specs/{engine,memory,lifecycle}.md`).
> Question asked: do these four **substrate** fixes reinforce the canon's
> invariants, or do they smuggle in new concepts / break a canon property?
> Method: spec-panel-style critique (Wiegers · Fowler · Nygard · Newman lenses),
> every claim cross-checked against the shipped code.

## Alignment verdict

**ALIGNED — approve.** All four fixes are pure substrate hardening (Engine +
Memory + the capability boundaries the Engine injects). Not one introduces a new
concept, a fifth verb axis, or a new top-level vocabulary item. Each fix
*reinforces* an existing canon invariant rather than reinterpreting it. The
spec's own Chesterton's-fence notes (#1 monotonicity, #4 lazy-read export) show
the author already reasoned from the invariant the canon protects. Misalignments
are cosmetic, not structural.

---

## Canon citations (the invariants each fix touches)

- **CORE.md:9** — "One FastMCP server + one bi-temporal graph" (the Substrate).
- **CORE.md:9-18** — Code-mode IS the contract; the sandbox runs caller code;
  "Cross-cutting guards … are engine middleware, **not** concepts."
- **CORE.md:33-35** — "a remote async agent inserts `verify`; `COMPLETED ≠ done`."
- **CORE.md:38-45** — Memory: "bi-temporal, append-only graph holding **every**
  node … and their edges"; `record · link · supersede`; `project(...) as_of`.
- **CORE.md:30-31** — Lifecycle frame `open · move · close` + `read · find ·
  check · watch`.
- **CORE.md:27-28** — Capability verbs role-tagged `act · transform · effect`.
- **CORE.md:96 / specs/lifecycle.md:51-53** — the `COMPLETED ≠ done` lesson is
  "kept (panel-endorsed)" and proven via the Jules `verify` step (branch on
  origin).
- **specs/memory.md:15-19, 33** — "Facts are **never overwritten**"; `as_of`
  reconstruction is the read contract.
- **specs/engine.md:67-75** — engine guards are middleware, not concepts.

---

## Per-fix alignment (the four substrate fixes)

### #1 — O(1) clock seed (Memory substrate). UPHOLDS CORE.md:38-45.

The logical clock IS the mechanism that makes the graph **monotonically
versioned and bi-temporal** (CORE.md:38-45; specs/memory.md:25 `vfrom/vto`). The
canon never specifies *how* the seed is computed — only that ticks stay
monotonic across reopens so `vfrom` is a true high-water mark and `as_of`
reconstructs correctly. The fix swaps an O(N+E) Python materialization for two
server-side `max(vfrom)` aggregations (nodes + edges, take the larger). This:

- **preserves monotonicity** — the seed is still ≥ every persisted `vfrom`, so
  no new write can reuse a stale tick (the documented `link()` bug at
  `memory.py:51-53` stays closed because the edge query is kept, non-optional);
- **preserves `as_of` correctness** — `_now()` is UNCHANGED (a pure locked
  increment); `recall`/`find`/`project` still test `vfrom <= as_of < vto`. The
  fix touches only the *seed*, never the window arithmetic or the read path. The
  spec is explicit: aggregate over `vfrom` only, never `vto` (which is the `OPEN`
  sentinel for live rows) — this is exactly what keeps the high-water mark
  honest.
- **adds nothing to the graph** — `_Metadata:Clock` is explicitly rejected,
  which is the *canon-correct* call: a singleton metadata node would pollute
  `find`/`project`/`provenance` (CORE.md:38-41 says the graph holds Intent /
  Invocation / Lifecycle / Artefact nodes — a clock node is none of those and
  would leak into the moat traversal). Rejecting it keeps Memory's node set pure.

Spec-panel (Fowler/Nygard): a performance fix that leaves the invariant's
*observable* contract (`as_of`, monotonic `vfrom`) byte-identical. Textbook
substrate hardening. The behavioral test (monkeypatch the bare `MATCH (n)` to
fail) correctly proves the scan is *gone*, not merely that results match.

### #2 — pagination to token-exhaustion (capability-internal). NEUTRAL-to-POSITIVE; no canon surface.

This is below the concept line entirely — it lives inside `_jules_api._paginate`,
an `_`-prefixed vendored client helper, not a verb, not a node, not an edge. It
touches no canon invariant directly. Its *indirect* alignment: a truncated
source walk produces a false "no Jules source connected", which would make the
`jules` **effect** verb (`dispatch`) fail to serve its Intent. Letting
`nextPageToken` exhaustion (plus a `seen_tokens` loop guard) be the sole stop
makes the boundary honest. Bounded `jules_plan` stays bounded. Correct scoping;
no concept impact.

### #3 — fail-closed `verify` (Lifecycle invariant). UPHOLDS CORE.md:33-35 directly — the strongest alignment in the spec.

This is the canon-most-load-bearing fix. CORE.md:33-35 names the exact mechanism:
"a remote async agent inserts `verify`; **`COMPLETED ≠ done`**", proven in
specs/lifecycle.md:51-53 as "the silent-fail lesson as a first-class
observe-step." The current code (`jules.py:139-142`) derives `done` from a
**caller-supplied bool** — which means the orchestrator can be lied to, and the
one canon lesson the capability exists to enforce is defeated. The fix:

- **injects `vcs` and derives the remote truth independently** via
  `remote_exists` → `git ls-remote --heads origin <branch>`. This is precisely
  CORE.md's "branch on origin" semantics (CORE.md:113-114 — "real Jules `verify`:
  state completed AND a branch on origin"). The fix makes the code match the
  canon's own worked example.
- **fails closed** — `done=False` whenever the remote cannot be independently
  verified; the caller bool is *removed*, not demoted to a trusted fallback. This
  is the correct reading of `COMPLETED ≠ done`: completion is a *claim*, done is a
  *verified fact*. (The REVIEW's must-fix #2 caught an earlier sketch that let the
  fallback flip `done=True`; the spec now removes the bool entirely — resolved.)

Spec-panel (Wiegers/Nygard): this is the canon invariant moving from
"documented + half-enforced" to "enforced at the boundary." Strong reinforcement.

### #4 — env-capture at the sandbox boundary (Engine substrate). CONSISTENT with CORE.md:9-18; correctly framed as substrate, not a concept.

The canon frames the sandbox as where "the agent writes code … chains tools …
intermediate results stay in-sandbox" (CORE.md:11-14) and frames all
cross-cutting protections as **engine middleware, not concepts** (CORE.md:17-18;
specs/engine.md:67-75). "Harden the sandbox boundary" is therefore squarely a
substrate concern, not a new concept — it is the same category as
quality-score / loop-detection / Slot-quota. Alignment specifics:

- The fix is placed at the actual boundary (`build_mcp`, the codemode branch),
  not `Engine.__init__` — i.e. it scopes to where `CodeMode()` is wired, which is
  exactly the canon's sandbox surface. Capturing in `__init__` would have leaked
  the behavior into every `Engine(...)` (library/test callers who never build the
  CodeMode surface) — a non-boundary side effect. `build_mcp` is canon-correct.
- The spec is honest that the premise is REFUTED on the pinned stack (Monty
  denies `os.environ`/`import`/`globals`), so #4 is re-scoped to
  defense-in-depth + a permanent RED-regression tripwire against version drift.
  This is the right posture: it does not *invent* a threat-model concept; it adds
  a middleware-grade guard and a regression test. No new vocabulary.
- It does NOT add a fifth concept (no "Secret" node, no "Vault" capability) —
  a process-local `_CAPTURED_KEY` module global, justified precisely because the
  probe shows it is not sandbox-reachable. Minimal substrate change.

---

## Naming / verb-frame check

- **`vcs.remote_exists(branch) -> bool`** — fits. It is a method on the injected
  `VCSBackend` boundary (`_vcs.py`), a sibling of `worktree`/`run`/`state`/
  `finish`. Those are imperative boundary methods, not concept verbs, so they are
  *not* governed by the `act/transform/effect` role-tag frame (CORE.md:27-28) nor
  the Lifecycle `open/move/close` frame (CORE.md:30-31) — the role-tag frame
  applies to **Capability verbs** decorated with `@verb`, and `remote_exists` is a
  backend method, not a verb. A `*_exists` predicate name reads as a pure query
  (no side effect), matching `state()`'s read-only character. Consistent and
  correct.
- **`jules.verify`** — already a canon-named step (CORE.md:34 "inserts `verify`").
  It keeps its `@verb(role="transform")` tag, which is correct: `verify` derives a
  truth from an injected boundary read; it performs no craft write (`act`) and no
  external mutation (`effect`). It *reads* the remote, but the role frame tags the
  verb's effect on **Memory/the world**, not whether it does I/O — `verify`
  produces a computed verdict, so `transform` is the right tag. (One could argue
  the `ls-remote` subprocess is an external read; but the canon's `effect` is
  reserved for external *side-effects* (CORE.md:28), and a read is not a
  side-effect. `transform` holds.)
- **`verified_via` field** (`"remote"`/`"remote-error"`/`"unverified"`) — a
  return-payload field, not a concept name; it surfaces *why* a verdict is
  fail-closed so a network blip isn't misread as a Jules silent-fail. No frame
  governs payload keys; this is good observability hygiene.

---

## Misalignments

Structurally: **none.** The following are cosmetic / wording nits only:

1. **(Nit) Spec "Why" #3 still narrates the old `branch_on_remote` parameter as
   the vector but the Design correctly removes it.** Fine as written (the Why
   describes the *bug*, the Design the *fix*), but a one-line "the bool is
   removed, not retained as a fallback" in the Why would prevent a skim-reader
   from thinking the bool survives. Non-blocking.
2. **(Nit) `verify`'s `role="transform"` does an external `ls-remote` read via the
   injected `vcs`.** This is canon-consistent (a read is not an `effect`), but
   because the verb now performs network I/O, a one-line docstring note that the
   role tag describes the *verdict* (compute), not the *I/O*, would pre-empt a
   future reviewer's "should this be `effect`?" question. Purely documentary.
3. **(Nit) #4's `_CAPTURED_KEY` module global.** Canon-acceptable (probe shows
   not sandbox-reachable), and the spec already mandates a code comment saying so.
   Ensure that comment lands — it is the single line that keeps a future reader
   from mistaking the global for the weak point. The REVIEW already flagged this;
   keep it.

No fix asserts a new concept, breaks append-only/bi-temporal semantics, alters
the `as_of` read contract, weakens `COMPLETED ≠ done`, or changes the
`search/get_schema/execute` public surface. The substrate stays the substrate.

---

## Recommended aligned framing

State the canon-tie explicitly in the spec's "Why" for each fix (the spec mostly
does this via Chesterton's-fence notes — make it a one-liner per fix):

- **#1**: "Preserves the bi-temporal monotonic-clock invariant (CORE.md:38-45);
  changes only the seed computation, never `_now()` or the `as_of` window — so
  `recall`/`project` reconstruction is byte-identical."
- **#3**: "Makes the code enforce the canon's own worked example — `verify` =
  `COMPLETED AND branch-on-origin` (CORE.md:33-35, 113-114) — by deriving the
  remote truth independently and failing closed; the caller bool that defeated
  it is removed."
- **#4**: "A sandbox-boundary middleware guard (CORE.md:17-18 — guards are
  middleware, NOT concepts); adds no node type and no capability; scoped to
  `build_mcp` because that is the canon's sandbox surface."

---

## Must-change list

**None blocking on vision grounds — the spec is canon-aligned as written.** The
following are SHOULD-do polish (all documentary, none structural):

1. **Add the one-line canon tie-in per fix** (above) to the "Why" so future
   readers see the invariant each fix protects without re-deriving it.
2. **#3 docstring:** note that `verify`'s `transform` role tags the *verdict*,
   not the `ls-remote` I/O — pre-empts a spurious "should be `effect`?" review.
3. **#4:** ensure the mandated `_CAPTURED_KEY`-not-sandbox-reachable comment
   actually lands in code (already specified; confirm at GREEN).

All correctness must-fixes (server-side `max(vfrom)` over nodes+edges; fail-closed
`done`; real-Monty RED probe in `build_mcp`) are already folded in from
`REVIEW.md` and carry no *additional* vision constraint.
