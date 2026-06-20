<!-- doc-source: Plan/338-lifecycle-pillar-deep-program/spec.md -->
# Brainstorm — Lifecycle pillar, open design questions (2026-06-20)

> Second-round brainstorm after the pillar reframe + the 2nd-pass spec-panel.
> Scope: the questions the panel left genuinely open (P1 discoverability, P2
> observer dispatch), plus two it implied (the frame's home, migration order).
> Each question: the tension, the options, a recommendation. The two starred (★)
> are forks for the owner — they re-touch "is it a capability."

## The frame so far (settled)

Lifecycle is a **pillar**: substrate `agency/lifecycle.py` (state machine) +
`ctx.lifecycle` + `lifecycle_*` substrate-tools + the `home="lifecycle"` member
caps. `move` is the sole, guarded, event-emitting state writer. Observation is
REUSE (`manage`/`gate`/`jules`). That much is decided. What follows is the
residue.

## Q1 ★ — How does the pillar's write frame stay discoverable? (panel P1)

**Tension.** Capability verbs are auto-discovered (`search`), CLI-mirrored (079),
SkillDoc'd (080) for free. Substrate-tools are hand-registered and invisible to
`search`/`<cap>.help`. So `open/move/close` risk being *less* findable than the
member caps that call them — anti-"complete first-class pillar."

| Option | What | Cost | Verdict |
|---|---|---|---|
| **A. Index the substrate-tools into `search`** | add `lifecycle_*` briefs to the discovery index the way `intent_bootstrap`/`agency_welcome` are surfaced | small engine change; keeps pure-substrate | **recommend** — smallest, canon-true (Intent already does this for `intent_bootstrap`) |
| **B. Thin discovery member cap** | a `home="lifecycle"` cap whose verbs are pure pass-throughs to `ctx.lifecycle`, existing only for surface | re-opens "is it a capability"; a shell cap is the anti-pattern CLAUDE.md warns of | only if A can't surface richly enough |
| **C. Document-only** | frame lives in the pillar reference doc + `manage`; no `search` hit | cheapest; weakest discoverability | reject — fails the "complete pillar" bar |

**Recommendation: A.** It matches the Intent precedent exactly (substrate entry
points are indexed, not wrapped in a fake cap) and keeps the owner's "not a
capability" ruling intact.

## Q2 ★ — Who invokes a parameterization's observer (`verify`/`in-review`)? (panel P2)

**Tension.** B2 put verify in `delegate.join` (hardcodes `delegate`→`jules`). The
`reviewed` parameterization's observer (`gate.check`) is run by `subagent.develop`,
not `join`. So "who runs the observer" is answered per-caller — per-agent
special-casing one layer up, the very thing Goal 3 kills.

| Option | What | Trade-off |
|---|---|---|
| **A. Per-caller (status quo / B2)** | each driver caller runs its own observer | simple now; re-creates special-casing; each new parameterization touches its caller |
| **B. `ctx.lifecycle.advance(lc)` dispatches the declared observer** | the parameterization *declares* its observer by name; `advance` looks it up and runs it, then performs the resulting move; `delegate.join` + `subagent.develop` both just call `advance` | one path for all agents (true Goal 3); BUT substrate calling *into* a capability verb (`jules.verify` needs `vcs`/network) is a layering inversion |
| **C. `advance` lives at the registry/member layer, not substrate** | a small reducer (in `delegate` or a shared helper) that reads the parameterization's declared observer and invokes it via `ctx.registry` | avoids the layering inversion (capability-layer calls capability); still one path | the "where does advance live" sub-question |

**Recommendation: B's *contract* via C's *placement*.** The parameterization
declares its observer (substrate data); a single `advance` reducer at the
**capability layer** (reachable as `ctx.lifecycle.advance` but implemented to call
out through `ctx.registry`, not from deep substrate) runs the declared observer and
moves. Both `join` and `subagent.develop` call `advance`; neither hardcodes
jules/gate. This keeps Goal 3 (one path) without the substrate→capability
inversion. **Needs owner nod because it sets the layering rule** for how the
Lifecycle pillar reaches its members.

## Q3 — Migration order: big-bang vs proof-first? (panel P4)

339 currently absorbs all three minting paths at once. Safer: **migrate `delegate`
end-to-end first** (it is the richest consumer — fan_out/join + the remote-async
parameterization + verify), proving the substrate API against one real member
before `subagent`/`jules`/`develop`/`music` follow. **Recommendation: proof-first.**
Re-order 339 → 339a (substrate + `ctx.lifecycle` + migrate `delegate` only) →
339b (migrate the rest). Low-risk, no scope change. (I can apply this without a
fork — it is a sequencing call, not an architecture one.)

## Q4 — Does `SessionLifecycle` really fold into a `session` parameterization?

F-3's biggest risk. `SessionLifecycle{mode,status}` + `SESSION_MODE`/`SESSION_STATUS`
+ `ModeShift` history + readers (`develop.session_check/resume`, `reflect.
synthesize_session`). Two reads:
- **Fold (current spec):** `Lifecycle{parameterization="session", mode, status}`;
  the session enums become parameterization-scoped props. Unifies the node (N6);
  bigger migration.
- **Leave it:** `SessionLifecycle` stays a distinct node; the pillar governs only
  *task* lifecycles. Smaller; but then "one lifecycle node" (N6) is unmet and a
  session's state machine stays un-guarded.

**Lean: fold, but as the LAST migration slice** (after the substrate is proven by
`delegate`), and behind its own acceptance that the develop/reflect readers still
pass. Not a fork unless the owner wants to keep `SessionLifecycle` separate.

## What needs the owner (the two ★ forks)

Q1 (discoverability approach) and Q2 (observer-dispatch home) both re-touch the
capability/substrate boundary the owner just set, so they go to the owner before
339 builds. Q3/Q4 are sequencing/risk calls I can apply with the panel's
recommendations unless the owner objects.
