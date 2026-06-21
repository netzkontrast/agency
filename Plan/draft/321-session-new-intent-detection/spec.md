---
spec_id: "321"
slug: session-new-intent-detection
status: draft
state: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [2, 3]
depends_on: ["045", "076", "307", "308", "309"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 321 — Per-session new-intent detection (`discover.watch_intent`)

> Child of the intent-pillar deep program (Spec 307), **lifecycle layer**. The
> owner's explicit ask: *"every new intent in the Session is clearly captured."*
> This slice rides the unified event-hook (Spec 076) so detection is automatic:
> when a user utterance has DRIFTED from the active intent, it recommends
> capturing the new one instead of silently serving the old.

## Why (evidence + doctrine)

Spec 307 §"coverage matrix" assigns the **session-start hook (Spec 076)** row to
this child: `watch_intent` detects a NEW intent emerging mid-session. Today a
session bootstraps ONE intent (`/agency-onboard`, Spec 148) and every subsequent
action's `SERVES` edge attaches to it — even when the user has moved on to a
genuinely different goal. The provenance moat (Goal 2) then mis-attributes work:
artefacts that serve goal B are recorded as serving goal A, because no one
noticed the intent changed. The agent-uniform lifecycle (Goal 3) wants every
intent to be a first-class, captured node — including the ones that appear *after*
session start.

The doctrine: CORE.md names Intent the human-owned root. If a second root quietly
appears in a session and is never captured, the graph has a *blind spot* exactly
where the moat is supposed to be densest. The fix is not to nag on every message
(false-positive churn destroys the AskUser budget — Goal 1) but to detect
**drift** — a genuinely new goal, not a sub-step of the active one — and only then
recommend capture.

## Design

**Cluster path.** `agency/capabilities/discover/clusters/session.py` (shared with
`state`/`replay`, per Spec 307 §"Architecture"), **plus a documented SEAM**: the
unified event-hook (Spec 076). This is one of the two children Spec 307
§coherence rule 1 permits to touch a seam outside the `discover/` folder.

**Verb signature.**

```python
@verb(role="transform")
def watch_intent(self, utterance: str = "") -> ToolResult:
    """Detect a NEW intent emerging mid-session vs the active one (transform).

    Inputs: utterance (the new user prompt text).
    Returns: {drifted, confidence, recommended_action, candidate_seed}.
    chain_next: on drift, discover.interview (309) to capture the new intent.
    """
```

**The Spec 076 seam (documented).** Spec 076 ships `hooks/dispatch` → `agency
hook` → `engine.dispatch_hook` (the `hook_event` substrate tool), recording an
`Event` node per hook. A **UserPromptSubmit**-style event (Spec 076 §findings
lists `UserPromptSubmit` among the wired events) carries the user's utterance on
stdin. We register a hook handler (`engine.register_hook_handler`, Spec 076 §
Design 2) that, on `UserPromptSubmit`, calls `watch_intent(utterance)`. So
detection is **automatic, not opt-in** — the agent does not have to remember to
check; the hook fires on every prompt and the handler does the drift test off the
critical path (`async: true`).

**Drift scoring (typed shape + seam).** `watch_intent` compares the utterance
against the active Intent's `{purpose, deliverable}` (recalled via the
`DiscoverCluster` `_recall_intent`). Scoring uses **semantic distance** behind a
typed shape — the `reflect`/embed seam (Spec 045 recall backend) when available —
with a **keyword-overlap fallback** so the verb works with zero heavy deps
(CLAUDE.md #8: the threshold is a documented tunable budget, the score is
computed). Drift above the threshold ⇒ `drifted=True`.

**Return + recommendation.** On drift, `recommended_action="discover.interview"`
(Spec 309) with a `candidate_seed` derived from the utterance — and the
recommendation MAY chain the new intent as a **sibling or child** of the active
one (substrate `intent.capture(parent_intent_id=…)`, Spec 048) so the session's
intent structure is explicit. `watch_intent` itself is `role="transform"`: it
*recommends*, it does not capture (capture is the user-confirmed `interview` step
— keeping the human in the loop, Spec 307 §thesis).

**Spec-307 ontology used (by name).** No new node — `watch_intent` reads the
active Intent and the Spec 076 `Event`; it RECOMMENDS the `DiscoverySession` /
`interview` path rather than writing one. (Read-only stays read-only, Spec 307
§coherence rule 3.)

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **No false-positive churn (the headline invariant):** a near-restatement of the
  active intent's purpose (paraphrase, same goal) returns `drifted=False` — assert
  the *relationship* (paraphrase distance < threshold), computed live, never a
  pinned confidence number.
- **Genuine drift detected:** a clearly new goal (unrelated purpose) returns
  `drifted=True` with `recommended_action == "discover.interview"` — asserted
  against the live active intent, not a frozen string match.
- **Monotone in distance:** a more-distant utterance has confidence ≥ a
  less-distant one (relationship, not a magic value).
- **Read-only:** invoking `watch_intent` adds zero domain nodes (delta == the
  Invocation only) — the recommendation does not itself capture.
- **Hook seam wired:** a `UserPromptSubmit` `Event` through the Spec 076
  dispatcher reaches the registered handler and yields a `watch_intent` result —
  assert the handler is in `engine._hook_handlers` for that event (drift-tag
  coverage), not that a specific event count fired.
- **Fallback parity:** with the embed backend absent, the keyword fallback still
  separates the paraphrase (no drift) from the new goal (drift) — assert both
  branches agree on direction.

## Acceptance

Every new user utterance in a session is checked against the active intent
automatically (via the Spec 076 hook). A paraphrase of the current goal does NOT
trigger; a genuinely new goal returns `drifted=True` and recommends
`discover.interview` to capture it (optionally chaining it as a sibling/child).
The session no longer has a blind spot where a second intent appears uncaptured.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** Lifecycle-layer child of Spec 307. Touches the one
  documented seam (Spec 076 hook) the program permits; all verb code stays in
  `discover/clusters/session.py`.
- **Slice plan:** Slice 1 — `watch_intent` with the keyword-overlap drift scorer
  behind the typed shape (no hook); Slice 2 — register the `UserPromptSubmit`
  handler through `engine.register_hook_handler` so detection is automatic;
  Slice 3 — wire the embed/`reflect` semantic backend (Spec 045) behind the same
  typed contract.
- **Open question (resolve at build):** default the drift threshold conservative
  (favour silence over churn) and make it an overridable documented budget, not a
  per-call knob, per CLAUDE.md #8.
