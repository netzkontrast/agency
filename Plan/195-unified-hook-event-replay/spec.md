---
spec_id: "195"
slug: unified-hook-event-replay
status: partial
last_updated: 2026-06-12
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

## Followup — Implementation Status (Slice 1, 2026-06-12)

### Done — Slice 1 (BoundaryUse capture in the unified hook handler)

- **`agency/engine.py` `_default_hook_handler`** extended (Spec 076
  surface) to record a typed `BoundaryUse` node when:
  - `hook_event_name == "PreToolUse"` (Open Q1: bypass moment, not
    post),
  - `tool_name` ∈ {`Write`, `Edit`, `Bash`} (Open Q1: mutating
    tools only — reads aren't a moat gap),
  - AND `AGENCY_INTENT` resolves to a confirmed Intent (no-intent
    sessions don't poison the moat — there's no intent to serve).

- **`_verb_shadow_for(tool, payload)`** returns the
  `(verb_shadow, argument_summary)` pair the BoundaryUse carries:
  - Bash `git commit*` → `branch.commit_smart`
  - Bash `git push*` → `branch.finish_branch`
  - Bash `pytest` / `python -m pytest` → `develop.test`
  - Bash other → `shell.run(<head>)`
  - Edit/Write of `Plan/NNN-*/spec.md` → `dogfood.observe`
  - Edit/Write other → `capability_verb_for(<path>)` placeholder
  - Slice 2 derives this from the live registry via Spec 188
    `suggest_drill` so registry renames don't drift the shadows.

- **`BoundaryUse` ontology** now carries
  `{tool, argument_summary, target, verb_shadow, intent_id, session}`
  (was `{tool, argument_summary}` before). The schema (`["tool",
  "argument_summary"]` shape on `DogfoodCapability.ontology`) stays
  the published surface; the additional fields are optional graph
  props that downstream readers consume.

- **`RECORDED_BY` edge** added to the dogfood capability's edge
  registry so the BoundaryUse can chain back to the Event node
  (provenance reconstruction surface for Slice 2 replay).

- **`dogfood.boundary_use_audit(for_intent_id, session_lifecycle_id)`**
  rewired (Codex-style Spec 195 typed report):
  - `{intent_id, bypass_count, by_tool: dict[str,int],
    samples: list[{tool, target, verb_shadow, argument_summary,
    session}], count}`.
  - `for_intent_id` filters via the BoundaryUse `intent_id`
    property — cross-intent contamination invariant (Spec 195
    failure-mode "Cross-intent contamination").
  - Samples are bounded (5 per tool) so the audit stays
    token-cheap even when the bypass rate spikes; paged readers
    can drill via `dogfood.recall_overflow_slice`.

- **11 tests green** (`tests/test_hook_event_replay.py`):
  - Raw Bash git commit / push / pytest under intent records BU
    with the right `verb_shadow`.
  - Raw Edit of `Plan/*/spec.md` routes to `dogfood.observe`.
  - Raw Write of a random path uses the placeholder shadow.
  - No BU without an active intent.
  - No BU for `PostToolUse` (PreToolUse only).
  - No BU for read-only tools (Read/Grep/Glob/WebFetch).
  - BU SERVES the intent + RECORDED_BY the Event (the moat
    invariant).
  - Audit aggregates `bypass_count` + `by_tool` + samples carrying
    the live `verb_shadow`.
  - Audit filters by `for_intent_id` (no cross-intent leak).
  - Empty audit returns zero counts cleanly.

### Done — Slice 2 (event replay + monotonic chain, 2026-06-12)

- **`dogfood.replay_events(for_intent_id, tool="", limit=100)`** —
  walks every Event OBSERVED_DURING the named intent (Spec 076 hook
  surface), joins each row to its BoundaryUse via the Slice 1
  RECORDED_BY edge so the replay carries `verb_shadow` + `target`
  when capture fired.
- **Monotonic chain**: each row's `prior_event_id` points at the
  previous event's id (first event gets `""`). Slice 3 promotes this
  to a verified monotone invariant (clock-skew check + integrity
  assertion).
- **Typed return shape** — `{intent_id, events: [{event_id,
  prior_event_id, name, tool, session, target, verb_shadow,
  summary}], count}`. Cross-intent contamination prevented by the
  `OBSERVED_DURING` traversal anchor.
- **Filters**: `tool=` narrows to a single tool family (e.g. all
  `Bash` events); `limit=` bounds the row count for token-budget
  awareness (default 100).
- **5 new tests** in `tests/test_hook_event_replay.py` (16 total green):
  empty replay for unknown intent; record-order chain with verb_shadow
  joined from BoundaryUse; tool filter; limit; cross-intent isolation.

### Still — Slice 3+

- **Live `verb_shadow` derivation** via Spec 188 `suggest_drill`
  (registry-aware so renames don't drift the shadow strings).
- **Loop-detection event records** (Spec 156) appear in replay.
- **PII discipline** — Write/Edit content summarized by default;
  raw payload gated by Spec 192.
- **Monotonic invariant** + clock-skew detection.
- **Cross-session replay** (Open Q3: intent_id is stable across
  sessions; the chain integrity check holds).
- **Spec 280 Slice 2 integration** — the bypass-rate baseline
  drives the WARN→error flip on the dispatcher's clearest routes
  (`git commit` / `git push` → exit 2 + the routing advice).

## Followup — PreToolUse → agency MCP suggestion (Spec 195 Slice 2, 2026-06-17)

**Shipped (user directive — "when a hook fires and the plugin detects this
should be an MCP call, return the MCP functions + schema").** Spec 195 Slice 1's
`_verb_shadow_for` flagged "Slice 2 derives this from the live registry"; this
delivers it as a returning suggestion:

- **One shared `_RAW_ROUTES` table** (`agency/engine.py`) maps a raw tool +
  payload to the agency call — read by BOTH `_verb_shadow_for` (the Slice-1
  BoundaryUse shadow) and `_suggest_mcp_calls` (the Slice-2 suggestion) so they
  cannot drift (the /simplify review caught the prior two-table duplication).
  Live, registry-resolved targets (advisory; read tools included): Bash
  `git commit` → `branch.commit_smart`, `git push` → `branch.finish`; Grep/Glob
  → `mcp__agency__search`; Task/Agent → `subagent.develop`; Write/Edit on a
  spec.md → `dogfood.note`. (A test-runner and a URL-fetch route are
  deliberately omitted — no `develop.test` / `research.fetch` verb exists yet;
  pointing at a fiction would be dormant surface. Follow-up
  `# AGENCY-DRIFT: raw-tool-routes`: derive via `recommend.route` once a
  command-prefix matcher exists.)
- **`_verb_input_schema(engine, cap, verb)`** derives the call's JSON schema
  from the LIVE registry verb signature (intent_id/agent_id omitted — auto-
  injected); substrate tools (`mcp__agency__search`) carry an explicit schema.
- **`_pre_tool_use_handler`** (registered for `PreToolUse`) records the
  Event + BoundaryUse via the default handler, then attaches
  `hookSpecificOutput.additionalContext` naming the MCP call(s) + schema +
  `agency_suggestion` (the structured list).
- **CLI wire (`agency hook`)** now emits the `hookSpecificOutput` JSON on stdout
  so Claude Code folds it into the pending tool call's context — the piece that
  makes the suggestion actually reach the agent. Dogfooded live via
  `echo '{...PreToolUse git commit...}' | agency hook`.

**Tests:** 3 acceptance scenarios in `tests/acceptance/features/hooks.feature`
(git-commit → branch.commit_smart + schema + additionalContext; Grep →
mcp__agency__search; Read → no suggestion). 28 hooks + 67 install/cli/substrate
scenarios green; drift clean.

**Still:** broaden the raw→verb map as the surface grows; optional
`permissionDecision:"ask"` mode to make the nudge blocking (today advisory).
