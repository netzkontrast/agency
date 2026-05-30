# DOGFOOD-NOTES — building Jules with Jules

Running record of what orchestrating actual Jules sessions for Spec 012's own
implementation teaches us about the design we're shipping. Each entry lands
back into the spec when a pattern is clear.

---

## 2026-05-30 — initial dispatch (phases 4 + 6 → Jules)

**Sessions:**
- Phase 4 (recovery-plan planner): sid `17080122233254972311` ([url](https://jules.google.com/session/17080122233254972311))
- Phase 6 (watcher): sid `1696509658639614343` ([url](https://jules.google.com/session/1696509658639614343))
- Intent: `intent:3eca0a8d` (ephemeral DB `/tmp/jules-012.db`)

**Observation 1 — `dispatch` hardcodes `require_plan_approval=False`.** I had to
dispatch without the plan-approval gate that Spec 012 calls "the recommended
default." Phase 5 of the implementation plan flips this, but until it lands,
every dispatch we do *as part of building 012* runs against the older shape.
→ **Design fold-back:** add to the spec's Refinement notes that **Phase 5
should precede Phase 4 + Phase 6 dispatches in any future re-run**, so the
self-implementing pass uses the recommended gate. Track as `OQ8` if not
already covered.

**Observation 2 — provenance recorded as a one-graph traversal, even from a
throwaway dispatch script.** `jules.dispatch` via `e.registry.invoke(...)`
records `Intent → Invocation → Artefact{kind: "jules-session"}` in one walk;
the moat (CORE.md:38-45) is real even for tactical dispatches. → No design
change; this validates the "no parallel sessions.json" decision (Spec 012
"Done When" item: registry = `JulesSession` nodes in the bi-temporal graph).

**Observation 3 — dispatch prompt token cost.** Each of the two prompts is
~500 words (~700 tokens). That's the price of the JULES_PROTOCOL discipline
(verify remote / no scope creep / TDD-RED-then-GREEN / no source copying).
→ **Design fold-back:** Phase 5 should add a `protocol_preset` field to
`dispatch` (lesson-15 §7) so the discipline boilerplate isn't re-pasted every
call; the caller passes scope + acceptance + reference files, and the engine
composes the canonical preamble. Token win + drift-resistance.

**Observation 4 — `require_plan_approval=True` would have produced
`AWAITING_PLAN_APPROVAL` immediately.** That's the state the watcher is
*specifically designed to react to* via the `review_and_approve_plan`
`WatchEvent`. Two implications: (a) implementing 012 via 012 is a real test
case for the watcher itself; (b) the `auto-if-affects-only` policy in OQ4
becomes more interesting when *we* are the dispatch target — the policy needs
a clear scope-locked rejection path ("Jules touched a path outside `affects:`"
→ reject + emit a `BLOCKED:` PR per JULES_PROTOCOL §1).

## 2026-05-30 — Codex review on ccb8f03 (4 P2 comments, mid-Phase-2)

Triage:
- **#3 (jules.py:139, `activities` missing `page_token`)** — real, fixed
  inline. `JulesBackend` Protocol + `JulesClient` + `StubJulesClient` + verb
  all carry `page_token` now.
- **#4 (engine.py:94, unbounded CodeMode sandbox)** — real, fixed inline.
  `MontySandboxProvider(limits={max_duration_secs: 30, max_memory: 512MB})`
  with env overrides (`AGENCY_SANDBOX_MAX_{SECS,MEM_MB}`). Without limits a
  bad `/execute` ties up the MCP process.
- **#2 (jules.py:117, `dispatch` returns `id` vs `name`)** — **false positive**.
  Downstream methods all normalize via `_jules_api._short_id()` which strips
  the `sessions/` prefix and accepts the bare numeric id; the Jules API
  accepts both forms in path params.
- **#1 (jules.py:166, `DELETE /v1alpha/sessions/{id}` may now exist)** —
  **deferred**: needs API verification (container SSL clock skew is blocking
  direct calls; will check via `WebFetch` on the Jules docs once the network
  cooperates). If real, the fix is small (try `DELETE` first, gracefully
  degrade to the current "unsupported" string on 404/405).

**Observation 5 — container SSL clock skew blocks `jules_get` calls from
*this* environment**, while the earlier dispatch went through. `httpx`
reports `CERTIFICATE_VERIFY_FAILED: certificate is not yet valid`. → **Design
fold-back:** the watcher (Phase 6) must handle transient TLS errors as
retriable, not terminal, and the recovery flow needs an alternate "check via
GitHub MCP" path when the Jules API itself is unreachable (lesson-15 §15
flavour). Track as `OQ9`.

## What to watch for next

- Did either session reach `AWAITING_PLAN_APPROVAL`? If yes, we may need to
  approve manually until Phase 5 lands.
- Silent-fail watch: **the user's note — most of the time Jules just did
  not publish the PR.** Probe via `jules.message(sid, "your branch isn't on
  origin — push and reply with the PR URL")` if a session reports COMPLETED
  without us seeing a PR on `git ls-remote`.
- Token budget of the WatchEvent payload is the spec's central claim —
  measure it once the watcher lands and a real session triggers a
  `recover_silent_fail` event.
