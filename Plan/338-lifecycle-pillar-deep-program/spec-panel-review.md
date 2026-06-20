<!-- doc-source: Plan/338-lifecycle-pillar-deep-program/spec.md -->
# Spec Panel Review — Lifecycle-pillar Deep Program (Spec 338 + children 339–344)

> Multi-expert specification critique run via the `sc:sc-spec-panel` discipline,
> **critique mode**, focus: requirements · architecture · testing · operations ·
> consistency. Reviewed: the master (338) in full; children 339, 340, 341, 342,
> 343, 344 in full. Panel: Wiegers · Adzic · Cockburn · Fowler · Nygard · Newman ·
> Hohpe · Crispin · Gregory · Hightower.
>
> **This panel does NOT rubber-stamp.** The corpus is unusually well-grounded —
> the codegraph deep-analysis pass gives it file:line evidence most specs lack,
> and the N1–N6 bottom-up justification is exemplary. But it has **5 blockers**,
> two of which mirror the exact failure that bit Spec 307 (a load-bearing
> control-flow seam named but never specified), several unfalsifiable
> "sole-writer" invariants, and one head-on contradiction with a *shipped* spec
> (336) that the program does not acknowledge.

---

## 0. Headline verdict (full synthesis at §7)

**Buildable after fixing 5 blockers.** The diagnosis is the best in the repo —
three divergent lifecycle paths, two contradictory "done"s, and the no-events gap
are all real and cited. The altitude is right (promote+unify, not a side-car).
But the program is written as if the hard part is the *state machine*, when the
codegraph evidence shows the hard part is the *migration*: turning a
SERVES-guard-exempt substrate class (`agency/lifecycle.py`) and two hand-rolled
paths into one intent-served capability, without breaking the engine's own
intent-less internal usage. That migration is asserted ("becomes a shim") and
never designed. Blockers: (B1) the substrate-class→capability migration crosses
the SERVES-guard boundary and is unspecified; (B2) the `verify` *observer*
control-flow — who runs the transform and performs `verify→completed` — is the
342 keystone and is named nowhere (the 307 AskUser repeat); (B3) "`move` is the
sole writer" / "no ad-hoc update" are unfalsifiable without an enforcement test;
(B4) 344 records a graph `Event` per transition, directly contradicting the
*shipped* Spec 336 decision to move high-volume capture OFF the graph; (B5) the
cross-capability contract that is the program's entire point (fan_out → verify →
join agree) has no end-to-end acceptance scenario.

---

## 1. Per-expert findings

### Karl Wiegers — Requirements clarity / testability

**W-1 (BLOCKER). "`move` is the SOLE writer of `Lifecycle.state`" is an
unfalsifiable invariant.** 338 §thesis-2 and 339 §Acceptance ("no other code path
writes Lifecycle.state directly") state the program's central guarantee — but no
spec says *how it is enforced or tested*. The codegraph pass itself found ≥4
writers; nothing stops a 5th from landing tomorrow. A claimed invariant with no
guard decays on the next PR. **Fix:** add an `# AGENCY-DRIFT: lifecycle-state-writer`
tag + a `scripts/check-drift` rule (or an acceptance test) that greps `agency/`
for `update(.*"state"` / `record("Lifecycle"` outside `lifecycle/` and fails on a
new occurrence. Make the invariant *executable*, like the Spec 327 `serves_intent_id`
non-null guard.

**W-2 (MAJOR). `close(..., outcome)` "+ done-gate" is undefined.** The 338 verb
table appends "(+ done-gate)" with no referent; 343 phase 5 mentions
`gate.check (done-gate)`. Against *what* is completion gated? Spec 328 already
ships `GateKind.completion` + `AcceptanceCriterion VALIDATES Intent`. The
relationship is a real coherence opportunity left unspecified: `close(
outcome="completed")` should record a Spec 328 **completion `Gate`** keyed to the
intent, reading its `AcceptanceCriterion`s. As written, "done-gate" is a TODO
wearing a parenthesis.

**W-3 (MINOR). `auth-required` is dormant surface.** It is in the enum and the 338
base table (`working → auth-required`, `auth-required → working|canceled`), but no
child shows a *producer* — `agency/lifecycle.py` never emits it, no parameterization
declares it. CLAUDE.md heuristic #1: declare a state ⇒ something must reach it.
Either name the producer (jules auth-pending? a Spec 285 elicitation pause?) or cut
it from the base table and leave it to a parameterization.

### Gojko Adzic — Specification-by-example / BDD

**A-1 (GOOD, with one gap).** Every child carries Given/When/Then — a real
improvement over the 307 corpus at first draft. **But** the scenarios are all
*single-slice*. The headline behavior (B5) — a remote-async child that reports
`completed` but isn't on origin must NOT count done — appears only as an isolated
342 scenario with no actor running `verify`. Make it an executable, cross-cap
example: `Given delegate.fan_out opens a remote-async child / When the driver
returns state=completed but the branch is absent / Then lifecycle.read shows
"verify" not "completed" AND delegate.join.done is False`.

**A-2 (MAJOR). 344's "emits a transition event" has no observable assertion of
volume or dedup.** A `move` that is called in a retry loop (failed→working→failed)
emits an Event each time. The LoopEvent precedent (156) explicitly dedups; 344
does not say whether repeated identical transitions collapse. Add a scenario.

### Alistair Cockburn — Use-case / primary-actor

**C-1 (MAJOR). Who is the primary actor of `lifecycle.move`?** Two very different
actors are conflated: (a) a *capability* advancing its own work (`gate.check`,
`delegate`), and (b) the *management discipline* (343) advancing someone else's
lifecycle. These have different guards — a cap should only move lifecycles it owns;
the discipline moves across owners. The SERVES guard (B1) handles (a) but the
spec never says whether (b) is allowed to move a lifecycle serving a *different*
sub-intent. Pin the ownership rule.

**C-2 (MINOR). The "session" actor is missing from the parameterization story.**
342 enumerates `remote-async` and `reviewed` but 339 also promises to absorb
`develop.SessionLifecycle` as a "session" parameterization — yet no
parameterization entry, transitions, or observers are given for it. Either spec
the `session` parameterization or stop claiming the absorption (see N-1).

### Martin Fowler — Architecture / interface design

**F-1 (BLOCKER, =B1). The substrate-class→capability migration crosses the
SERVES-guard boundary and is unspecified.** `agency/lifecycle.py::Lifecycle` is a
substrate class the *engine* holds (`engine.lifecycle`, used by
`music/drivers_production.py`); it writes nodes with **no intent guard**. A
capability verb CANNOT: every `capability_*_*` verb is subject to the SERVES
intent-guard (`capability.py`). So "promote the class to a capability + leave a
shim" (339) is not a rename — it changes the *trust boundary*. How does the engine
open a lifecycle internally, with no ambient intent? Either (i) keep a thin
substrate `open/move` the capability *wraps* (the `SubstrateTool` pattern, like
`lifecycle_gate`), or (ii) require every internal caller to supply a system intent.
This is THE architectural decision of the program and it is currently a one-line
"becomes a shim."

**F-2 (MAJOR). 340 and 342 contradict each other on monotonicity.** 340: a
parameterization "may **never** remove a base edge (monotone extension — the
safety floor)." 342: introduces `removes_from_base: ["working->completed"]` as
"the ONE narrow exception." A floor that has an exception is not a floor. **Fix:**
restate the invariant as what actually must hold — *no parameterization may make a
terminal state non-terminal, nor orphan a base state (render it unreachable)* —
and allow edge *replacement* (remove + insert-intermediate) under that invariant.
The monotonicity framing is wrong; the orphan-check is the real safety property.

**F-3 (MAJOR). Three node shapes are being unified but only one is modeled.** 339
absorbs `Lifecycle`, hand-rolled `Lifecycle`, and `SessionLifecycle` — but the
last has its own props (`mode`, `status`) and enums (`SESSION_MODE`,
`SESSION_STATUS`). The unified node's schema (which props, which become
parameterization-scoped) is never given. Without it, "one node, parameterized" is
a slogan, not a design.

### Michael Nygard — Production / failure modes

**N-1 (BLOCKER, =B4). 344 re-introduces the bloat Spec 336 just removed.** Spec 336
(SHIPPED 2026-06-19) moved high-volume pre/post tool-call capture OFF the graph
into an ephemeral `toolcalls.db` *because Events were ~95% of `session.db` bloat*.
344 proposes a durable graph `Event` **per `move`** — i.e. per state transition,
which on a fan-out of N children + retries is high-volume. The spec must resolve
the contradiction explicitly: are transitions **durable provenance** (graph —
then justify against 336) or **telemetry** (the `toolcalls`/monitor store — then
`watch` reads there)? My recommendation: terminal/blocked transitions are
provenance (graph, low-volume); intermediate churn rides the monitor channel.
Right now 344 cites 336's ecosystem approvingly while violating its core ruling.

**N-2 (MAJOR). `watch` overpromises.** 341 names the verb `watch` and the use-case
"notify me when it transitions," but the design delivers a **pull** (read the
recorded event trail). Pull ≠ watch. Either rename to `history`/`transitions`, or
specify the actual push path (the jules watcher / a hook fires on `move`). A verb
whose name implies notification but returns a log is an operational trap.

**N-3 (MINOR). Failure of the `verify` remote check is a fork, not a branch.**
342's remote-async `verify` depends on `vcs.remote_exists`, which can fail
(network/auth) distinctly from "branch absent." `jules.verify` already
fail-closes (done=False on lookup error). The parameterized `verify` state must
say what a *lookup failure* maps to — stay in `verify`? → `input-required`? It is
not `failed`. Specify the three-way outcome.

### Sam Newman — Distributed systems / evolution

**S-1 (MAJOR, =N-1 sibling). Backward compatibility of the node migration is
unaddressed.** Existing graphs hold `Lifecycle{state:"working"}` opened by the old
class at `working` (never `submitted`) and `SessionLifecycle` nodes. After 339
flips `open→submitted` and 342 adds `parameterization`, how do *already-recorded*
lifecycles read? The bi-temporal graph is append-only; old nodes won't have
`parameterization`. State the default-on-read (`parameterization=""→"default"`)
and confirm `manage`'s state-set classification still holds for legacy nodes.

**S-2 (MINOR). `delegate.fan_out` children "start working" today; 339 wants
`submitted`.** Changing the start state changes `delegate.join`'s reduction
(`done iff all completed`) and `manage.whats_next`'s `active_states={submitted,
working}`. Trace the blast radius — this is exactly the kind of cross-cap
invariant the CLAUDE.md "full suite on a migration" heuristic warns about.

### Gregor Hohpe — Integration / messaging

**H-1 (BLOCKER, =B2). The `verify` observer has no invocation model.** This is the
342 keystone and the direct repeat of 307's AskUser-contract blocker. The spec
says the `remote-async` parameterization's observer "is `jules.verify`." But
`jules.verify` is `role="transform"` — it computes `{done}` and writes nothing.
For `working → verify → completed` to actually gate, *something* must: (1) detect
the child reported completion, (2) call `verify`, (3) `move(→completed)` on done /
`move(→input-required)` on not-done. Is that trigger `delegate.join`? `lifecycle.watch`?
A `post_invocation` hook? An observer registered by the parameterization? The
message-exchange pattern (who calls whom, when, with what delivery guarantee) is
the integration contract and it is unspecified. Until it is, "join's done == verify's
done" (the headline Goal-3 win) is aspiration.

**H-2 (MINOR). Ordering of transition events.** 344 says events appear in
`manage.timeline` "in order" — ordered by what? `recorded_at`? A fan-out emits
concurrent child transitions; without a sequence key, "in order" is undefined
across children. Specify the ordering key.

### Lisa Crispin — Agile testing

**Cr-1 (BLOCKER, =B5). The cross-capability contract is untested.** Every child
tests its own slice; the *integration* that justifies the whole program — Goal 3's
"one done for every agent" — has no acceptance scenario spanning
`delegate`+`jules`+`lifecycle`. Add an e2e (injected vcs, deterministic) proving
the remote-async round-trip end to end. Without it, six green slices can still
sum to a broken pillar.

**Cr-2 (MAJOR). Several acceptances assert negatives that can't be observed.**
"no hand-written graph query" (338 #1), "no other code path writes state" (339)
— a test cannot observe the *absence* of a code path. Convert to the W-1 drift
guard (a static check), not a runtime scenario.

### Janet Gregory — Collaborative quality

**G-1 (MAJOR). The affected capability owners aren't in the room.** This program
rewrites behavior in `delegate`, `jules`, `develop`, `gate`, and `music`
(drivers_production uses the buggy class). Does `music` production *depend* on
`open→working`? Does `develop.session_state`/`reflect.synthesize_session` break
when `SessionLifecycle` folds? The specs assert the migrations; no "three amigos"
check with those surfaces is recorded. Run `codegraph impact` on
`agency/lifecycle.py::Lifecycle` and `SessionLifecycle` and fold the blast radius
into 339.

### Kelsey Hightower — Operability

**Hi-1 (MAJOR). The `lifecycle-board.md` Document and `watch` need an operational
story for the common case: a stuck lifecycle.** The pillar's best operational payoff
is detecting a lifecycle stuck in `input-required`/`verify`. 344 emits the
transition; but what *surfaces* the stall — a `manage` query, the dogfood
loop-detector (which detects repetition, not silence), a timeout? "Stall detection"
is implied by the events but owned by no verb. Name it or scope it out explicitly.

**Hi-2 (MINOR). No metric/SLO on transition latency.** If `watch`/`verify` is the
recovery path for async agents, a transition that never fires (jules silent-fail)
is the failure mode that matters most. `jules.verify` already emits
`silent_fail_detected`; wire 344/341 to surface it as a first-class stall, not a
log line.

---

## 2. Consensus points (≥3 experts agree)

1. **The diagnosis is excellent; the migration is the unspecified hard part.**
   (Fowler, Newman, Gregory, Nygard) — the program over-invests in the state-machine
   design and under-invests in how three live paths converge without breakage.
2. **The `verify` observer control-flow (B2) is the keystone and is missing.**
   (Hohpe, Fowler, Crispin) — exactly the 307 AskUser-contract failure, repeated.
3. **"Sole-writer / no ad-hoc update" must be an executable static guard, not a
   runtime acceptance.** (Wiegers, Crispin) — unfalsifiable as written.
4. **344 must reconcile with shipped Spec 336 before it ships.** (Nygard, Newman)
   — graph-Event-per-transition is the bloat 336 removed.

## 3. Disagreements

- **Nygard vs. the spec on event storage:** the spec wants durable graph events
  for *all* transitions; Nygard wants only terminal/blocked in the graph and churn
  on the monitor channel. (Resolvable by the B4 decision.)
- **Fowler vs. Cockburn on `check`:** Fowler would drop `lifecycle.check` entirely
  (it is `gate.check` + a `move`; two verbs for one act); Cockburn keeps it as the
  frame's named affordance. (Minor; reuse-vs-discoverability tension.)

## 4. Blockers (must fix before build)

| # | Owner | Blocker | Smallest fix |
|---|---|---|---|
| **B1** | Fowler/Newman | substrate-class→capability migration crosses the SERVES guard; engine's intent-less internal use unhandled | keep a thin substrate `open/move` (`SubstrateTool`, `requires_intent=False`) that the capability wraps; spec the system-intent path |
| **B2** | Hohpe | `verify` observer invocation model unspecified (who calls verify + performs `verify→completed`) | pin the trigger (recommend: `delegate.join` runs verify for remote-async children; document the post-completion-report→verify→move contract) |
| **B3** | Wiegers/Crispin | "sole writer" invariant unfalsifiable | add `# AGENCY-DRIFT: lifecycle-state-writer` + a `check-drift`/grep test |
| **B4** | Nygard | 344 contradicts shipped Spec 336 (events off the graph) | decide durable-vs-telemetry per transition class; terminal/blocked→graph, churn→monitor |
| **B5** | Crispin | the cross-cap Goal-3 contract has no e2e | add a `delegate`+`jules`+`lifecycle` round-trip acceptance (injected vcs) |

## 5. Majors (fix during build)

W-2 (`close`→completion Gate, wire Spec 328) · F-2 (340/342 monotonicity
contradiction → orphan-check) · F-3 (unified node schema incl. SessionLifecycle
props) · N-2 (`watch` is pull, not push — rename or specify push) · S-1
(legacy-node read compat after `open→submitted` + new `parameterization`) · A-2
(transition-event dedup) · C-1 (ownership rule for discipline-driven moves) ·
G-1 (codegraph-impact the affected caps) · Hi-1 (stall detection owner).

## 6. What the program gets RIGHT (not a rubber stamp — earned)

- **Bottom-up justification (N1–N6).** Grounding the program in what real callers
  re-implement, with file:line, is the strongest "why" in the repo's spec corpus.
- **Goal 3 as north star + the `jules.verify`/`delegate.join` disconnect as the
  motivating bug.** This is a true, specific, falsifiable defect — not a vibe.
- **Altitude discipline inherited from 307** (promote+unify, reuse `manage`/`jules`,
  one walkable skill) — the program will not become a side-car.
- **Scoped-OUT is honest** (329 typed table, 290/330 read-API, FastAPI deferred).

## 7. Synthesis & recommendation

**Verdict: strong design, not yet buildable — fix 5 blockers, all small.** None of
the blockers is a redesign; each is a *missing decision* the codegraph evidence
already points at. The two that matter most are B1 (the migration trust-boundary)
and B2 (the verify observer) — and both are the same lesson 307 learned the hard
way: **the load-bearing seam is the control-flow contract between capabilities,
not the data model.** Pin those two contracts (substrate-wrap for B1; `delegate.join`
runs `verify` for B2), make the sole-writer invariant a static guard (B3), resolve
the 336 tension (B4), and add the one cross-cap e2e (B5), and this is the cleanest
pillar build in the repo.

**Quality scores (0–10):**

| Axis | Score | Note |
|---|---|---|
| Requirements clarity | 7.5 | excellent diagnosis; `close`/`auth-required`/observer under-specified |
| Architecture | 6.5 | migration trust-boundary (B1) + monotonicity contradiction (F-2) unresolved |
| Testability | 6.0 | per-slice Gherkin good; unfalsifiable invariants + no cross-cap e2e |
| Consistency | 6.5 | 344↔336 contradiction; 340↔342 contradiction; otherwise tight |
| Operability | 7.0 | strong intent (events, stall detection) but `watch` overpromises |
| **Overall** | **6.7** | buildable after the 5 blockers; design instinct is sound |

**Suggested next step:** fold B1–B5 into 338/339/342/344 in place (the 307
precedent: blockers fixed in-spec, panel doc retained as the record), then proceed
to `develop.implement` on the 339 scaffold.

---

## 8. Resolution — folded 2026-06-20 (this review retained as the record)

All 5 blockers + the majors are resolved in-spec. The decisive move was an owner
directive that landed alongside the fold: **"lifecycle isn't a capability — it's
its own pillar."** That reframed the architecture and dissolved B1 outright.

| Item | Resolution | Where |
|---|---|---|
| **B1** trust boundary | **Lifecycle is a pillar, not a capability** — substrate `agency/lifecycle.py` + `ctx.lifecycle` + `lifecycle_*` substrate-tools (peer to Intent/Memory). Substrate is not under the SERVES guard, so the boundary is never crossed. | 338 §Architecture; 339 retitled "harden the substrate" |
| **B2** verify observer | `delegate.join` is the trigger: a `verify`-state child → `join` runs `jules.verify` → `move(verify→completed|input-required)`; lookup failure stays in `verify`. join.done == verify.done. | 342 §"The verify observer" + 2 scenarios |
| **B3** sole-writer | static `# AGENCY-DRIFT: lifecycle-state-writer` + `check-drift` grep (incl. the newly-found `subagent.develop:66` writer). | 338 §Architecture; 340 note |
| **B4** 344 vs 336 | split by class: terminal/blocked → durable graph `Event`; intermediate churn → the Spec 021 monitor channel (never the graph). | 344 §Emission + scenarios |
| **B5** no e2e | a delegate+jules+lifecycle round-trip acceptance (injected vcs). | 342 §Acceptance |

**Majors folded:** W-2 (`close`→Spec 328 completion Gate), F-1 (observe arm is
REUSE of `manage`/`gate`/`jules`, no new verbs), F-2 (orphan/terminal floor, not
"never remove"), F-3 (unified node schema incl. `SessionLifecycle`→`session`
parameterization), N-2 (`watch` is an honest pull), N-3 (verify lookup-failure
stays in `verify`), S-1 (legacy `parameterization=""→"default"`; `open→submitted`
new-only), A-2 (event dedup/class split), H-2 (ordering by `recorded_at`), C-1 +
Hi-1 (ownership rule + stall detection → 343). The unified-node schema (F-3) and
the `session` parameterization remain the largest implementation risk and are
flagged for the 339/342 build.

---

## 9. Second-pass panel — after the pillar reframe (2026-06-20)

> Re-review of the **revised** corpus (substrate pillar, not a capability; B1–B5
> folded). The reframe is a net improvement and the right call — but a pillar
> made of substrate-tools is not free, and the fold introduced **3 new findings**
> (one a blocker) plus left one major under-addressed.

**Headline (2nd pass): closer, one new blocker.** The pillar model removed the
worst structural problem (B1) and made the design canon-symmetric with Intent and
Memory. But moving the frame from capability verbs to **substrate-tools** trades
away the auto-surface every capability gets for free, and B2's fix introduced a
cross-member coupling that wants one more turn of the crank.

### P1 (BLOCKER) — Newman/Hightower: the substrate frame loses discoverability

A capability verb is auto-discovered (`mcp__agency__search`), CLI-mirrored (Spec
079), and carries a derived SkillDoc (Spec 080) **for free**. A `SubstrateTool`
(`lifecycle_open/move/close`) is **hand-registered** in `SUBSTRATE_TOOLS`, is NOT
in the capability registry `search` walks, and has no `<cap>.help`. So the pillar's
own write frame becomes *less* discoverable than the member caps that drive it —
the opposite of "a complete, first-class suite" (CORE.md "four complete pillars").
`intent_bootstrap` gets away with this because it is ONE well-known entry point;
`open/move/close/+verify` is a frame an agent must find. **Fix options (→ brainstorm):**
(a) register the substrate-tools' briefs into `search`'s index explicitly; (b)
keep a *thin* `home="lifecycle"` member cap whose verbs are pure pass-throughs to
`ctx.lifecycle` purely for discovery/CLI/SkillDoc (the frame lives in substrate,
the *surface* is a member) — note this re-opens the "is it a capability" question
the owner just closed, so it needs care; (c) accept reduced discoverability and
document the frame in the pillar's reference doc + `manage`. **This must be decided
before 339 builds** — it changes what `lifecycle_*` *is*.

### P2 (BLOCKER) — Hohpe/Fowler: who invokes the parameterization's observer?

B2 placed verify-invocation in `delegate.join` (`join` calls `jules.verify`). That
works for the dispatch path, but it **hardcodes a member→member dependency**
(`delegate` must know `jules`) and does not generalize: the `reviewed`
parameterization's observer is `gate.check`, run by `subagent.develop`, not
`join`. So "who runs the observer" is answered *per caller*, re-creating the
per-agent special-casing Goal 3 exists to remove — just one layer up. **The
cleaner model:** the parameterization *declares* its observer; whoever drives the
`→verify`/`→in-review` transition asks the substrate to **dispatch the declared
observer by name** (`ctx.lifecycle.advance(lc)` runs the parameterization's
observer and performs the resulting move). Then `delegate.join` and
`subagent.develop` call the SAME `advance`, and neither hardcodes jules/gate.
**But** substrate dispatching INTO a capability verb (`jules.verify` needs `vcs`
+ network) is a layering inversion (substrate is below caps). Resolving *where
`advance` lives* (substrate? a member? the registry?) is the real open question →
brainstorm.

### P3 (MAJOR) — Fowler: `ctx.lifecycle` is a CORE.md change, unstated

CORE.md §CapabilityContext enumerates the delegator's fields ("Eight fields…").
Adding `ctx.lifecycle` makes it nine and is a canon edit — the program must say so
(and update CORE.md), or the next reader treats `ctx.lifecycle` as undocumented
surface. Small, but it is exactly the kind of canon-drift CLAUDE.md rule 2 warns
about. (Same applies to documenting the new `lifecycle_*` substrate-tools in
CORE.md's substrate-tool list.)

### P4 (MAJOR, carried) — Gregory/Crispin: the member migration is still the risk

The reframe did not shrink the migration — `delegate`, `subagent`, `jules`,
`develop` (SessionLifecycle), `music`, `gate` all rewire to `ctx.lifecycle`, and
`SessionLifecycle`→`session`-parameterization (F-3) is unproven. **Recommendation:
add an explicit slice ordering — migrate ONE member (`delegate`) end-to-end as the
proof-of-pillar BEFORE the others**, so the substrate API is validated by a real
consumer before five more depend on it. Today 339 absorbs all paths at once.

### What the 2nd pass CONFIRMS is right

- The pillar reframe is canon-faithful (substrate symmetry with `intent.py`/
  `memory.py`) and genuinely dissolves B1 — net large positive.
- B4's event-class split is the correct reconciliation with shipped 336.
- F-2's orphan/terminal floor is the right invariant.

### 2nd-pass verdict

**Still buildable; resolve P1 + P2 first (both are "where does X live" decisions,
not redesigns), state P3, and re-order 339 per P4.** Overall **7.1/10** (up from
6.7 — the reframe fixed more than it cost). P1 and P2 are exactly the kind of
open design questions a brainstorm should settle before implementation.

> **RESOLVED 2026-06-20 (owner forks, see `brainstorm.md`):** P1 → index the
> `lifecycle_*` substrate-tools into `search` (no shell cap); P2 → one
> `ctx.lifecycle.advance` reducer at the cap layer (parameterization declares the
> observer; `advance` dispatches via `ctx.registry`); P3 → 339 updates CORE.md
> §CapabilityContext; P4 → 339 re-ordered proof-first (`delegate` migrated first,
> `SessionLifecycle` fold last). Folded into 338/339/342. **No open blockers
> remain;** the corpus is buildable.
