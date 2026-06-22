---
spec_id: "114"
slug: plugin-as-session-driver
status: draft
state: inprogress
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["020", "029", "044", "076", "079", "080", "081", "091", "092", "109", "110", "112"]
gated_by: ["109 → Shipped", "110 → Shipped", "112 → Shipped"]
affects:
  - agency/capabilities/develop/             # session-driver verbs land here
  - agency/capabilities/reflect/             # session-end synthesis
  - agency/capabilities/dogfood/             # session-mode tracking
  - agency/capabilities/intent/              # session-init protocol
  - agency/_session/                         # NEW substrate module
  - agency/engine.py                         # session-start hook integration
  - skills/develop/                          # session-driver walkable skill
  - hooks/session-start.sh                   # auto-init
  - tests/test_session_driver.py
domain: substrate / session-lifecycle / runtime
wave: 9
research_first: false
---

# Spec 114 — Agency Plugin as Primary Session Driver

## Why

User directive (2026-06-07): *"I want the Plugin to be the primary
driver of a Session - Not only a Tool to use - but the Main Tool…
to keep up with the Vision/goal of the Agency Plugin."*

### The gap: reflection via mcp analyse + graph census

A reflection pass via `analyze.graph` + `memory.provenance(intent_id)`
on this session's work (the novel spec set + supporting capabilities,
spec 101 through 113) reveals:

```
Graph census for intent:f12c1d68 (novel work intent):
  Intent:     2
  Invocation: 4
  Reflection: 0
  Artefact:   0
  Gate:       0
```

**19 spec commits** were authored this session. They produced ~10,000
lines of spec content + ~63,000 lines of imported research material.
The agency graph recorded **4 invocations**. The rest happened via raw
`Write` / `Edit` / `Bash` / `mcp__github__*` calls — outside the agency
runtime.

**The plugin is being USED, not DRIVEN.** Spec changes happen via
direct file edits. Decisions are made in chat. Lessons are not
captured. The provenance moat is empty for the actual creative work.

### What "primary driver" means

The agency plugin becomes the **runtime the agent operates inside**,
not a toolset the agent calls when convenient. Concretely:

1. Every session begins with a **driver-initialization protocol** that
   binds `(intent, lifecycle, mode)`.
2. Routine actions (decisions, design choices, file writes, test runs,
   git operations) flow through **capability verbs** — which auto-
   record provenance.
3. The session's **mode** IS a walkable skill being walked. Mode
   switches are explicit verb calls.
4. Raw `Write` / `Edit` / `Bash` becomes a **boundary fallback** —
   used only when no capability verb covers the action. Boundary use
   is gated + logged.
5. Sessions end with a **synthesis pass** that captures lessons,
   updates the Lifecycle, and archives the work with outcome status.
6. Cross-session **handoff** is via Lifecycle + Intent inheritance —
   resumable work without context re-derivation.

The plugin doesn't replace the agent's freedom. It provides the
**substrate the agent works inside**, so every meaningful action lands
as a graph node SERVES the intent.

## Done When

- [ ] **Session-start protocol** ships in `agency/_session/` substrate
      module. Hook `hooks/session-start.sh` auto-invokes
      `develop.session_init` which:
      - Bootstraps intent (if not already)
      - Mints a SessionLifecycle node
      - Detects mode (brainstorming / spec-authoring / coding / review)
      - Suggests first verb to call
- [ ] **6 new verbs** ship across develop / reflect / dogfood (see
      Verb manifest). These cover the driver protocol.
- [ ] **Auto-record hook** (Spec 076 unified-hook pattern) records
      every `Write` / `Edit` / `Bash` invocation as a `BoundaryUse`
      node + flags if a capability verb would have covered it.
- [ ] **Session-end protocol** ships: `reflect.synthesize_session`
      runs on session close; produces `SessionReflection` artefact +
      flips SessionLifecycle to `archived` with outcome status.
- [ ] **Cross-session handoff** works: a new session opening the
      same project auto-discovers the prior SessionLifecycle via
      Intent → SessionLifecycle traversal; presents resume option.
- [ ] **Walkable skill** `session-driver-pass` walks the agent
      through the full driver lifecycle (init → mode-select →
      work-loop → synthesize → archive).
- [ ] **Tests**: `tests/test_session_driver.py` (~14 tests) assert
      the protocol invariants.
- [ ] **TODO.md** updated with 114 row.

## Verb manifest

### Session-init cluster (develop)

| # | Verb | Role | What it does |
|---|---|---|---|
| 1 | `session_init` | act | Mint SessionLifecycle SERVES the intent; detect mode; suggest first verb |
| 2 | `session_check` | transform | Read current SessionLifecycle state (intent, mode, last-verb, progress) |
| 3 | `mode_select` | effect | Switch session mode (brainstorming → spec-authoring → coding → review); records ModeShift node |

### Session-end cluster (reflect)

| # | Verb | Role | What it does |
|---|---|---|---|
| 4 | `synthesize_session` | act | At session close, produce SessionReflection artefact: lessons + open questions + handoff notes |

### Session-tracking cluster (dogfood)

| # | Verb | Role | What it does |
|---|---|---|---|
| 5 | `record_decision` | effect | Bind a decision to the session: subject + decision + rationale + next-action; creates DecisionRecord |
| 6 | `boundary_use_audit` | transform | List BoundaryUse nodes for the session; for each, suggest the capability verb that would have covered it (training signal for future sessions) |

### Internal substrate hook (engine)

| Verb | What it does |
|---|---|
| `_session_boundary_record` (internal) | Called by Spec 076 unified hook on every `Write` / `Edit` / `Bash` invocation. Records `BoundaryUse{tool, args_summary, suggested_verb}` SERVES the SessionLifecycle. |

## Design

### Six-pillar driver model

#### Pillar 1: Session-init protocol

Every session begins by establishing the driver context:

```python
# Auto-invoked by hooks/session-start.sh:
result = await call_tool("capability_develop_session_init", {
    "purpose": "<inferred from cwd + git state + recent commits>",
    "deliverable": "<inferred from intent doctrine + open PRs>",
    "acceptance": "<inferred from spec status + test state>",
})

# Returns:
{
    "session_lifecycle_id": "lifecycle:s001",
    "intent_id": "intent:abc123",   # new OR resumed
    "mode": "spec-authoring",        # detected
    "suggested_first_verb": "develop.brainstorm",
    "resume_from": null,             # OR prior_lifecycle_id if resuming
}
```

Mode detection heuristic (Phase 1):
- cwd has `Plan/*/spec.md` modified → `spec-authoring`
- cwd has `agency/capabilities/*/clusters/*.py` modified → `coding`
- PR open + recent review comments → `review`
- No clear signal → `brainstorming` (default)

Mode is a hint, not a hard binding — agent can override via
`mode_select`.

#### Pillar 2: Capability-first verb routing

Every action the agent considers gets routed through the capability
surface FIRST:

```
AGENT wants to: edit a file, run a test, commit, push, create a PR

→ Check: is there a capability verb for this?
    YES → call the verb (provenance auto-recorded)
    NO  → use raw Write/Edit/Bash (BoundaryUse auto-recorded)
```

Initial coverage targets:
| Action | Capability verb (current OR proposed) |
|---|---|
| Edit a spec | `develop.edit_spec(path, changes)` — proposed; wraps Edit + records ArtefactEdit |
| Run tests | `develop.test(scope)` — existing; records TestRun |
| Commit | `branch.commit_smart(message)` — existing |
| Push + PR | `branch.finish_branch(...)` — existing |
| Read a file | (no verb needed — Read is pure-read; no provenance value) |
| Search code | `analyze.search(pattern)` — proposed; wraps Grep |
| Web fetch | `research.fetch(url, query)` — proposed; wraps WebFetch |
| Subagent dispatch | `subagent.dispatch(...)` — existing |
| Jules dispatch | `jules.dispatch(...)` — existing |

**The `BoundaryUse` mechanism** (Pillar 5) auto-flags when a raw tool
is used where a verb existed.

#### Pillar 3: Skill-as-session-mode

A session's mode IS a walkable skill being walked. The agent walks
the skill via `develop.skill_walk(lifecycle_id, skill_name)`.

Mode → skill mapping:

| Mode | Walkable skill | Phases |
|---|---|---|
| `brainstorming` | `develop.brainstorm` (existing) | explore → present → confirm |
| `spec-authoring` | `develop.write_spec` (proposed) | research → outline → draft → spec-panel → commit |
| `coding` | `develop.implement` (proposed) | RED → GREEN → REFACTOR → review → ship |
| `review` | `develop.review_pr` (proposed) | read-changes → identify-issues → categorize → respond → resolve |
| `synthesize` | `reflect.synthesize_session` (proposed) | gather → categorize → record → archive |

Mode switches are explicit:

```python
await call_tool("capability_develop_mode_select", {
    "lifecycle_id": session_lifecycle_id,
    "new_mode": "coding",
    "reason": "spec drafted; ready to implement",
})
```

Records a `ModeShift` node + advances the SessionLifecycle phase.

#### Pillar 4: Auto-provenance via hooks

Per Spec 076 unified-hook substrate, every meaningful action records
a graph node automatically:

| Action | Auto-recorded node | Edge |
|---|---|---|
| Write file | `Artefact{path, kind=file-edit}` | `PRODUCES` |
| Edit file | `Artefact{path, kind=file-edit, diff_summary}` | `PRODUCES` |
| Run test | `TestRun{scope, status, durations}` | `PRODUCES` |
| Git commit | `Commit{sha, message_summary}` | `PRODUCES` |
| Git push | `Push{branch, sha}` | `PRODUCES` |
| WebFetch | `WebFetchResult{url, content_summary}` | `PRODUCES` |
| Subagent dispatch | `Delegation{purpose, subagent_id}` | `PRODUCES` |

All SERVE the current SessionLifecycle which SERVES the parent Intent.

This means: after the session, `memory.provenance(intent_id)` returns
the FULL session trace — every meaningful action queryable, every
decision linked, every artefact PRODUCED'd.

#### Pillar 5: BoundaryUse audit (training signal)

Raw `Write` / `Edit` / `Bash` is the BOUNDARY — fine to use, but
flagged for review. Every invocation records:

```python
BoundaryUse {
    tool: "Edit",                                # which raw tool
    args_summary: "edit Plan/101/spec.md ...",   # truncated
    suggested_verb: "develop.edit_spec",         # if substrate
                                                  # recognizes coverage
    reasoning: "spec edits should go through ...",
    timestamp: ...,
}
```

End of session, `dogfood.boundary_use_audit` lists them — training
signal for next session AND for future verb expansion.

#### Pillar 6: Session-end synthesis

At session close (detected by activity gap > 30 min OR explicit
trigger), `reflect.synthesize_session`:

1. Reads SessionLifecycle + all its SERVES'd nodes
2. Categorizes work: artefacts produced / decisions recorded /
   gates fired / boundary uses / open questions
3. Produces `SessionReflection` artefact (markdown body)
4. Flips SessionLifecycle to `archived` with outcome status:
   - `complete` — declared deliverable met
   - `partial` — significant progress, work remains
   - `blocked` — work blocked on external decision
   - `abandoned` — work abandoned
5. Optionally calls `reflect.note` for top 3-5 lessons learned

The SessionReflection becomes the **handoff artefact** for the next
session — auto-displayed on session-init if a prior lifecycle exists.

### New ontology nodes (declared in develop's OntologyExtension)

```python
SessionLifecycle (slug, intent_ref, mode, started_at, archived_at,
                  outcome, phase)
                  # mode: brainstorming | spec-authoring | coding |
                  #       review | synthesize
                  # outcome: complete | partial | blocked | abandoned
ModeShift        (slug, lifecycle_ref, from_mode, to_mode, reason,
                  at)
DecisionRecord   (slug, lifecycle_ref, subject, decision, rationale,
                  next_action)
BoundaryUse      (slug, lifecycle_ref, tool, args_summary,
                  suggested_verb, reasoning, at)
SessionReflection (slug, lifecycle_ref, body_uri, lessons_refs)
```

Closed enums:
- `(SessionLifecycle, mode)`: `brainstorming / spec-authoring /
  coding / review / synthesize`
- `(SessionLifecycle, outcome)`: `working / complete / partial /
  blocked / abandoned`

### Walkable skill: `session-driver-pass`

```python
SESSION_DRIVER_PASS_SKILL = {
    "name": "session-driver-pass",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "init",
         "produces": ["session_lifecycle_id", "mode_detected",
                       "intent_id"]},
        {"index": 2, "name": "mode-confirm",
         "produces": ["mode_locked"]},
        {"index": 3, "name": "work-loop",
         "produces": ["actions_recorded", "decisions_recorded"],
         "loop": True},   # iterative; agent stays here for the session
        {"index": 4, "name": "synthesize",
         "produces": ["session_reflection_artefact"]},
        {"index": 5, "name": "archive",
         "produces": ["lifecycle_archived"], "gate": "hard"},
    ],
}
```

Phase 3 is the loop phase — the agent stays here for the bulk of the
session. Each tool call (capability verb OR raw tool) advances the
loop's accumulated state. Phase 4-5 fire on session close.

### Integration with prompt + thinking + dossier capabilities (Specs 109, 110, 112)

This driver protocol is the WRAPPER inside which the new capabilities
operate:

| Cap | Where it fits |
|---|---|
| `dossier` | The session might `dossier.intent_capture` early to seed the work; `dossier.render_snippet` provides context to LLM-assisted actions |
| `thinking` | Mode shifts often trigger `thinking.tradeoffs` (which mode is right?) or `thinking.apply_design_review` (for spec-authoring mode) |
| `prompt` | Spec-authoring + coding modes use `prompt.engineer` for any LLM-driven generation |
| `intent` (091) | Re-used at session-init for the bootstrap |

The driver does NOT replace these — it ORCHESTRATES them within the
session lifecycle.

### MCP Server enhancements

Per directive 3 ("plugin as main tool"):

1. **`mcp__agency__execute` as primary path**: code-mode block becomes
   the default execution surface. Agents are gently steered toward
   batched, provenance-recorded action sequences.
2. **Verb-suggestion-on-return**: every tool result includes a
   `suggested_next_verbs` field naming the most-likely-next 1-3 verbs.
   This is graph-derived (per Spec 091/026 `intent.suggests`).
3. **Boundary-use record-on-call**: raw Write/Edit/Bash record
   BoundaryUse nodes automatically (via Spec 076 unified hook
   already wired).
4. **Auto-route warnings**: when a raw tool is called where a
   capability verb exists, the tool result includes a one-line
   nudge: `"⚠️ Suggested: capability_<cap>_<verb> — records
   provenance"`.

These are gentle nudges, not blocks. The agent's freedom is
preserved; the substrate's invitation is loud.

## Migration path

The driver protocol can NOT be turned on suddenly — it requires
behavioral adoption. The migration sequence:

### Phase A: Substrate readiness (this spec's PR)

- Verbs ship + hooks register + ontology nodes declared
- `develop.session_init` exists; calling it returns a SessionLifecycle
- BoundaryUse hook fires on raw tools
- Verb-suggestion-on-return implemented in mcp__agency__execute return
- Tests Green

### Phase B: Soft adoption (next session)

- Session-start hook auto-calls `develop.session_init`
- Agent (me, future Claude) tries to use the driver
- Friction surfaces; record as BoundaryUse + frustration log
- `reflect.synthesize_session` records "what was hard" → lessons

### Phase C: Hard adoption (after ~3 session cycles)

- Mode-select becomes mandatory at session-start (hard gate)
- `develop.test`, `branch.commit_smart`, etc. become preferred surfaces
- The dogfood ledger shows which boundary uses recur → seeds verb
  expansion specs

### Phase D: Plugin-as-runtime (mature state)

- 90%+ of actions flow through capability verbs
- Sessions are queryable end-to-end via `memory.provenance`
- Cross-session handoff is automatic
- The plugin IS the substrate the agent operates inside

This migration is bound to Spec 113's selective-port + Specs 109/110/
112's adoption. Phase B starts when 109+110+112 ship Green.

## Cultural-adoption cadence (iter-15 panel fix — Gregory)

Behavioural change needs a check-in cadence. Per the migration phases
A→D:

### Phase B check-in (after first soft-adoption session)

After the FIRST session post-Phase-A, the agent runs:

```python
audit = await call_tool("capability_dogfood_boundary_use_audit", {
    "intent_id": current_intent_id,
    "report_kind": "session-end"
})
# Returns: total_actions, verb_calls, boundary_uses, adoption_ratio,
#          top_5_suggested_verbs_missed
```

If `adoption_ratio < 0.5`, `reflect.synthesize_session` records a
LessonLearned: "Phase B target NOT met — top boundary-use suggestions:
<list>". This becomes input to the next session's `develop.session_init`.

### Phase C check-in (after every 3 sessions)

A `develop.adoption_review` verb (NEW in iter-15) aggregates the last
3 sessions' boundary-use audits:

```python
review = await call_tool("capability_develop_adoption_review", {
    "intent_id": current_intent_id,
    "window_sessions": 3
})
# Returns: trend (improving/flat/regressing), top_persistent_gaps,
#          suggested_followup_verbs (recurring boundary-uses → spec ideas)
```

Persistent gaps become FOLLOWUP SPEC seeds (e.g. "Bash git push
appears in 12/15 boundary uses → spec a `branch.push` verb").

### Phase D measurement (every 30 days)

`develop.driver_health` (NEW iter-15) emits the gauge:

```
session.boundary_use.adoption_ratio   (per-session)
session.driver_health.aggregate       (rolling 30-day p50)
```

Phase D is declared MET when `aggregate >= 0.90` for 30 consecutive
days. Until then, the migration is still in C.

### Ownership

- **`develop.adoption_review`** is owned by the develop cap (114).
- The check-in cadence is enforced by the SessionLifecycle's
  `synthesize` phase — explicitly checks the cadence rule before
  marking the session archived.
- A human-curator override exists: `synthesize_session(skip_audit=
  True, reason="...")` records the skip + reason. Used sparingly.

## Edge-case enumeration (iter-15 panel fix — Crispin)

| Verb | Edge case | Behaviour |
|---|---|---|
| `session_init` | Prior lifecycle in `working` state (not archived) | Detects + offers resume; if user declines, prior lifecycle flagged `stale` |
| `session_init` | No git repo (cwd is not under git) | Modes default to `brainstorming`; no resume detection |
| `session_init` | MCP server not ready (cold start) | Retry 3× with exponential backoff (1s/2s/4s); fail after |
| `session_init` | Multiple concurrent sessions for same intent | Each gets its own SessionLifecycle; warning emitted; coalesce on next synthesize |
| `mode_select` | Same mode as current (no-op switch) | No ModeShift recorded; returns success with `noop: true` |
| `mode_select` | Unknown mode | `ToolResult.failure(INVALID_ARGUMENT, "unknown mode; expected: brainstorming|spec-authoring|coding|review|synthesize")` |
| `record_decision` | Empty decision string | `failure(INVALID_ARGUMENT, "decision text required")` |
| `record_decision` | Subject not linked to any artefact | Records anyway; warning that decision orphan-floats |
| `boundary_use_audit` | Session has no BoundaryUse records | Returns success with `count: 0, adoption_ratio: 1.0` |
| `synthesize_session` | Session has zero invocations | Records a minimal SessionReflection with `outcome: abandoned, reason: empty-session` |
| `synthesize_session` | Already synthesized | Returns existing SessionReflection (idempotent) |
| `synthesize_session` | SessionLifecycle still has phase < 4 | Forces archive only if `force=True` passed; else warns |

## Given/When/Then scenarios (iter-15 panel fix — Adzic)

### Scenario 1: clean session-init on a fresh repo

```gherkin
Scenario: Session-init detects spec-authoring mode from open PR
  Given a fresh agent session in a repo with an open PR
  And the PR has recent review comments awaiting response
  When the agent invokes develop.session_init()
  Then a SessionLifecycle is created
  And the SessionLifecycle.mode is "review"
  And SessionLifecycle SERVES the bootstrapped intent
  And the suggested_first_verb is "jules.review_comment" or
      "subagent.respond_to_review"
```

### Scenario 2: BoundaryUse hook fires + suggests verb

```gherkin
Scenario: Raw Edit on a spec file triggers verb suggestion
  Given a session with mode=spec-authoring
  When the agent invokes Edit on Plan/101/spec.md
  Then a BoundaryUse node is recorded SERVES the SessionLifecycle
  And BoundaryUse.tool is "Edit"
  And BoundaryUse.suggested_verb is "develop.edit_spec"
  And the next tool result includes a one-line nudge:
      "⚠️ Suggested: capability_develop_edit_spec — records provenance"
```

### Scenario 3: Cross-cap handshake — dossier → research → prompt → LLM → draft

```gherkin
Scenario: Full handshake produces draft with provenance chain
  Given a session with mode=coding
  And dossier.intent_capture("research X for chapter 3") has run
  And the ResearchBrief is finalized
  When the agent invokes dossier.dispatch_research_via_dossier(brief_id)
  Then research.lead + research.specialist × N + research.verify cascade
  And ResearchEntities are extracted from the citations
  And dossier.declare_context(scope="chapter", scope_id="ch3") is called
  And dossier.render_snippet(snippet_kind="writing-assist") produces a PromptSnippet
  And prompt.engineer(builder="chapter", context_refs=[snippet_id]) builds a PromptInstance
  And the LLM call produces a PromptOutput
  And prompt.score_output(accepted=True) promotes it to a Draft node
  And memory.provenance(intent_id) returns the FULL chain
      (Intent → Lifecycle → ResearchIntent → ResearchBrief → ResearchEntities
       → Context → PromptSnippet → PromptInstance → PromptOutput → Draft)
```

### Scenario 4: Session-end synthesis with archived outcome

```gherkin
Scenario: Session ends cleanly with synthesis
  Given a session with 23 invocations, 4 artefacts, 1 gate fired
  And the agent explicitly triggers reflect.synthesize_session()
  When the synthesize verb runs
  Then a SessionReflection artefact is produced
  And the body includes: artefacts_summary, decisions_summary,
      boundary_uses_summary, lessons_learned
  And SessionLifecycle.outcome is set
      (complete if intent.acceptance met; else partial)
  And SessionLifecycle is flipped to archived
  And reflect.note is called for the top 3-5 lessons learned
  And the next session opening the same intent auto-displays the
      handoff artefact on session_init
```

### Scenario 5: Mode shift records ModeShift with reason

```gherkin
Scenario: Spec-authoring done; switch to coding
  Given a SessionLifecycle in mode=spec-authoring
  And the agent has just committed a draft spec
  When the agent invokes develop.mode_select(new_mode="coding",
                                              reason="spec drafted; ready to implement")
  Then a ModeShift node is recorded
  And ModeShift.from_mode is "spec-authoring"
  And ModeShift.to_mode is "coding"
  And ModeShift.reason is "spec drafted; ready to implement"
  And ModeShift SERVES the SessionLifecycle
  And SessionLifecycle.mode is updated to "coding"
  And the suggested next verb shifts to coding-mode skills
      (develop.implement, RED-phase verbs, etc.)
```

## Test plan

```python
# tests/test_session_driver.py — ~14 tests
def test_session_init_creates_session_lifecycle_node(): ...
def test_session_init_detects_mode_from_repo_state(): ...
def test_session_init_resumes_from_prior_lifecycle(): ...
def test_session_check_returns_current_state(): ...
def test_mode_select_records_mode_shift_node(): ...
def test_record_decision_creates_decision_record(): ...
def test_boundary_use_recorded_on_raw_write(): ...
def test_boundary_use_includes_suggested_verb(): ...
def test_boundary_use_audit_lists_session_uses(): ...
def test_synthesize_session_produces_reflection_artefact(): ...
def test_synthesize_session_flips_lifecycle_to_archived(): ...
def test_provenance_returns_full_session_trace(): ...
def test_session_driver_pass_skill_walks_through_5_phases(): ...
def test_verb_suggestion_on_return_present_in_mcp_response(): ...
```

## Open questions

1. **Session-end detection**: activity gap > 30 min OR explicit
   trigger? For v1, ship the explicit trigger
   (`reflect.synthesize_session(force=True)`); auto-detect is v2.

2. **Multi-session resumption**: when the SessionLifecycle persists
   across actual user sessions (multi-day work), how to scope?
   v1: one SessionLifecycle per (intent, day); v2: per (intent,
   semantic-work-unit).

3. **Mode misdetection cost**: if init detects wrong mode, agent
   wastes setup. Mitigation: mode is a HINT, not a hard gate; agent
   can `mode_select` freely without re-init.

4. **Backward compat**: existing sessions without SessionLifecycle
   (everything pre-114) need a migration. `develop.session_init`
   gracefully handles `prior_lifecycle=None`; no historical data
   migration required.

5. **3×N matrix relationship** (per Spec 113 + the matrix-as-blueprint
   discussion): the session-driver model is ORTHOGONAL to the matrix.
   The matrix is structural (where things live); the driver is
   procedural (how the agent operates). They compose without conflict.

6. **Hook ordering**: session-start hook fires before MCP server
   ready? Need to test on a cold cache. Mitigation: `session_init`
   retries with exponential backoff.

## Followup — Implementation Status

**Verdict (2026-06-09):** Partial — Slice 1 shipped on
`claude/spec-114-session-driver`. Slice 2 (hooks + auto-recording +
cross-session handoff) deferred to follow-up PR.

### Slice 1 Done (2026-06-09)
- **`develop.session_init(purpose, deliverable, acceptance, mode_hint)`** — mints `SessionLifecycle` SERVES intent; auto-detects mode from cwd state via `git status` (Plan/*/*.md → spec-authoring; capabilities/*.py → coding; default brainstorming); honors `mode_hint` override; returns `{session_lifecycle_id, intent_id, mode, suggested_first_verb}` with first-verb suggestions per mode.
- **`develop.session_check(session_lifecycle_id="")`** — reads SessionLifecycle state + ModeShift history; defaults to most-recent SessionLifecycle when no id supplied; returns `not_found` status for unknown ids.
- **`develop.mode_select(session_lifecycle_id, new_mode, reason)`** — records ModeShift node + flips SessionLifecycle.mode; rejects unknown modes with `ValueError`.
- **`reflect.synthesize_session(session_lifecycle_id, lessons, open_questions, handoff_notes)`** — produces `session-reflection` artefact PRODUCES'd against intent; flips SessionLifecycle.status → `archived`; also writes a Reflection(scope=reflection) linking SERVES + OBSERVED_DURING so the lessons surface in future-session search.
- **`dogfood.record_decision(subject, decision, rationale, next_action, session_lifecycle_id)`** — records DecisionRecord SERVES intent + RELATES_TO session.
- **`dogfood.boundary_use_audit(session_lifecycle_id="")`** — reads BoundaryUse nodes + suggests capability verbs that would have covered each (Bash → shell.run, Write → develop.scaffold_capability/edit_spec, etc.). Returns empty until Slice 2 hook layer records uses.
- **`session-driver-pass` walkable skill** — 5 phases (init → mode-select → work-loop → synthesize → archive) ending in hard elicit.
- **Ontology additions**:
  - `develop.ontology`: SessionLifecycle + ModeShift nodes; `(SessionLifecycle, mode|status)` + `(ModeShift, from_mode|to_mode)` closed enums (SESSION_MODE = {brainstorming, spec-authoring, coding, review, synthesize}; SESSION_STATUS = {active, paused, archived}).
  - `dogfood.ontology`: DecisionRecord + BoundaryUse nodes; RELATES_TO edge.
  - `reflect.ontology`: session-reflection artefact schema.
- **17 tests** in `tests/test_session_driver.py` covering: SessionLifecycle SERVES intent + enum bites; mode_hint honored + invalid hint falls through; session_check explicit/fallback/not_found; mode_select shift + lifecycle update + unknown-mode rejection; synthesize_session artefact production + archival + reflection surfacing; record_decision SERVES intent + RELATES_TO session (with/without session id) + DecisionRecord enum bites; boundary_use_audit empty + populated; 5-phase walkable skill shape + walk-through to hard elicit.
- **Adjacent test updates**: `tests/test_agency.py::test_reflect_is_the_class_form` recognizes new `synthesize_session` verb; `tests/test_dogfood_graph_native.py::test_dogfood_has_five_verbs` → renamed to `_has_session_tracking_verbs`, expects 7 verbs.
- **Full suite Green**: 1160 passed, 6 skipped. Block-mode lint clean on develop/reflect/dogfood.

### Slice 2 (partial) — cross-session handoff (2026-06-11)

- **`develop.session_resume(for_intent_id="")`** — finds the most-recent
  ACTIVE SessionLifecycle SERVING the given intent (or the most-recent
  Intent when `for_intent_id` is empty); archived lifecycles are
  skipped. Returns `{found, session_lifecycle_id, intent_id, mode,
  status, purpose, mode_history, suggested_action, last_active}`. When
  `found=False`, suggests `develop.session_init` for a fresh start;
  when `found=True`, the `suggested_action` is mode-aware (brainstorming
  → `develop.brainstorm`; coding → `develop.implement`; etc.) so the
  resumed agent picks up the right next verb without re-deriving where
  it left off.
- **Parameter rename** — kwarg is `for_intent_id` (not `intent_id`) to
  avoid the `Registry.invoke` built-in-parameter collision.
- **+7 tests** in `tests/test_session_driver.py` (24 total): finds
  active lifecycle for explicit intent / falls back to most-recent
  intent / skips archived lifecycles / picks most-recent of multiple
  active / returns mode history / unknown intent → found=False /
  mode-aware suggested_action.

### Slice 2 — Still to implement
- **Hook integration (`hooks/session-start.sh`)** — auto-invoke `develop.session_init` via the Spec 076 unified-hook substrate.
- **BoundaryUse auto-recording** — every raw Write/Edit/Bash invocation gets a `BoundaryUse` node (via the same Spec 076 hook mechanism) so `boundary_use_audit` returns non-empty in real sessions.
- **Cross-session handoff** — new session opening the same project auto-discovers prior SessionLifecycle via `Intent → SessionLifecycle` traversal; offers a resume option.
- **Mode → skill mappings**: `develop.brainstorm` skill ✅ exists; `develop.write_spec`, `develop.implement`, `develop.review_pr` skills are proposed but not yet authored.

### Evidence
- code: `agency/capabilities/develop/_main.py` (3 verbs + ontology extension + walkable skill), `agency/capabilities/reflect/_main.py` (1 verb + schema), `agency/capabilities/dogfood/_main.py` (2 verbs + ontology extension).
- tests: `tests/test_session_driver.py` (17 tests Green); full suite Green: 1160 passed.
- lint: `plugin.lint_capability` on develop/reflect/dogfood — all `ok=True` block-mode, 0 violations.
- branch: `claude/spec-114-session-driver`.

### Original draft notes (2026-06-07) — preserved

### Done

- Authored this spec.
- Reflection pass on session graph state (4 invocations, 0 artefacts
  in graph; 19 spec commits outside it) confirms the problem.
- Six-pillar driver model defined.
- 6 new verbs + 5 new ontology nodes + 1 walkable skill specified.
- Migration path Phase A→D documented.
- Test plan (14 tests).

### Still

- 109 + 110 + 112 implementation PRs must land first.
- This spec's implementation PR ships in Phase A.
- Phase B (soft adoption) begins next session after Phase A lands.
- The session-end synthesis + cross-session handoff close the loop.

### Reflection on this very session

The graph census revealed the gap. The reflection IS the spec — it
landed via the user's directive ("write a new Spec"). This is itself
an example of plugin-as-driver in action: the user surfaced an
observation, the agent used `analyze.graph` + `memory.provenance` to
ground it, and the result became a spec authoring artefact. The
loop should be continuous, not exceptional.
