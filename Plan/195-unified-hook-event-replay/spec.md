---
spec_id: "195"
slug: unified-hook-event-replay
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "076"
depends_on: ["076", "021", "156", "176"]
vision_goals: [2, 3]
affects:
  - agency/engine.py
  - agency/capabilities/dogfood/_main.py
  - tests/test_hook_event_replay.py
---

# Spec 195 — unified-hook event replay + boundary-use capture

## Why

Spec 076 ships the unified event-hook (`hooks/dispatch` → `agency hook`
→ `engine.dispatch_hook`; `Event` node + `AGENCY_INTENT` linkage).
Events are recorded but not REPLAYABLE — and Spec 114 Slice 2 (the
deferred BoundaryUse auto-capture on raw Write/Edit/Bash) needs exactly
this hook to record when an agent bypasses a capability verb. This spec
makes the Event stream replayable (provenance reconstruction) and wires
the deferred boundary-use capture.

## Done When

- [ ] **Event replay** — `dogfood.replay_events(intent_id)` returns a
      typed `ReplayResult{intent_id:str, events:list[EventRecord],
      reconstructed_actions:list[Action], boundary_uses:list[BoundaryUse],
      monotonic:bool, gap_count:int}`. EventRecord carries
      `{event_id, ts, kind, payload, prior_event_id}` so the sequence
      is verifiable as a chain (Goal 2: the graph is the record).
- [ ] **Raw-tool boundary-use capture** (Spec 114 Slice 2) — the hook
      records a `BoundaryUse{tool:Literal["Write","Edit","Bash"],
      target:str, intent_id:str, would_have_used:list[str], ts:str}`
      node when an agent uses raw Write/Edit/Bash instead of a
      capability verb. `would_have_used` is the candidate-verb list
      from a registry lookup (Spec 188 suggested-drill, on-demand).
- [ ] **`boundary_use_audit` (Spec 114) reads the captured nodes** —
      returns a typed `BoundaryAuditReport{intent_id, bypass_count:int,
      by_tool:dict[str,int], suggested_alternatives:list[VerbBrief]}`.
      Feeds the dogfood loop (Spec 150).
- [ ] **Loop-detection events (Spec 156) appear in the replay** as
      typed `LoopEvent` records with the detected cycle's edges.
- [ ] **Replay invariants** (rule 8): `events sorted by ts (monotonic)`;
      `every Event has prior_event_id OR is the session's first`;
      `every Action in reconstructed_actions traces back to ≥ 1 Event`;
      `boundary_uses ⊆ events filtered by kind`. No pinned event counts.
- [ ] **PII discipline**: replay does not surface raw payloads
      verbatim — Write/Edit content is summarized (paths + byte counts)
      unless the consumer holds an explicit `replay_raw=True` scope
      authorized via Spec 192 gate.
- [ ] **Failure-mode coverage** for clock skew, lost events, and
      cross-intent contamination.
- [ ] Test: a raw-edit hook records a BoundaryUse; replay reconstructs
      the sequence in order; a clock-skew fixture trips the monotonic
      invariant; cross-intent events do not leak.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  an agent session under intent_id "intent:abc"
        runs: Write(/x.py), call_tool("agency_search", ...), Bash("ls"), Edit(/y.md)
        AND the unified hook is installed
When:   each tool fires
Then:   the hook writes Event{kind:"raw_write", ...} for Write,
        BoundaryUse{tool:"Write", target:"/x.py", intent_id:"intent:abc",
        would_have_used:["dogfood.observe","branch.commit_smart"]};
        a capability_search invocation creates Event{kind:"verb_invoke", ...}
        (no BoundaryUse); Bash("ls") creates Event{kind:"raw_bash"} +
        BoundaryUse; Edit creates Event{kind:"raw_edit"} + BoundaryUse

Given:  the same session, after completion
When:   dogfood.replay_events("intent:abc") is called
Then:   ReplayResult.events lists 4 events sorted by ts;
        monotonic == True; gap_count == 0;
        reconstructed_actions has 4 entries; boundary_uses has 3;
        every Action traces back to an Event;
        boundary_use_audit returns
        BoundaryAuditReport{bypass_count:3, by_tool:{Write:1,Edit:1,Bash:1},
        suggested_alternatives:[<verb briefs>]}

Given:  a malicious actor reorders Event timestamps in the graph
When:   replay runs
Then:   monotonic == False; the consumer must surface this as a
        provenance corruption signal; replay refuses to reconstruct
        reliable actions
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Clock skew | host clock drift across sandbox boundaries | `monotonic` invariant on event ts | use monotonic counter alongside ts; flag drift but keep replay |
| Lost events | hook crash mid-write | `prior_event_id` chain has a gap | `gap_count > 0` surfaces; replay returns partial result with `complete:False` |
| Cross-intent contamination | hook writes Event without intent_id | invariant: every Event has intent_id OR is a SessionStart Event | reject writes without intent on the hook side |
| PII leak via replay | replay returns raw Write contents | summarization by default; explicit scope required for raw | gate via Spec 192; default is summarized |
| Hook ordering race | concurrent tool calls write Events out of order | monotonic counter + per-intent serialization | serialize per intent_id at the hook |
| Replay tampering | someone hand-edits Event nodes | the chain hash chains prior_event_id; tampering breaks the chain | replay verifies chain integrity before returning |

## Interconnects

- Spec 021 (monitor) + Spec 156 (loop hooks) emit into the stream.
- Spec 176 (sessionstart capture) opens the Intent the events SERVE.
- **dogfood-loop chain** (150): boundary-use bypasses become proposals.
- Spec 192 (shell safety gate) gates raw-content replay scope.
- Spec 194 (shell.define suggest) consumes the Event stream to find
  recurring bash sequences.
- Spec 188 (suggested-drill) supplies the `would_have_used` candidate
  list for BoundaryUse records.
- Spec 191 (vision matrix) reads the bypass_count for the Goal-2 row.
- Spec 193 (capstone) records its agent loop into this stream for
  re-running the proof.

## Open questions

1. Capture every raw tool use or only mutating? **Recommend**: only
   mutating (Write/Edit/Bash) — reads aren't a substrate bypass worth
   flagging. Read bypasses are noise; mutation bypasses are the moat
   gap.
2. How are `would_have_used` candidates populated? **Recommend**:
   on-demand lookup against the registry at hook time (Spec 188
   suggest_drill) — cached per (intent_id, tool, target_kind) so
   the hook stays fast.
3. Replay across sessions? **Recommend**: yes — intent_id is stable
   across sessions; replay walks all Events SERVES the intent
   regardless of session boundary. The chain integrity check holds
   across sessions.
