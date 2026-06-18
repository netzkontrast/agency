---
spec_id: "323"
slug: guided-discovery-discipline
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [3, 9]
depends_on: ["081", "148", "307", "308", "309", "311", "312", "314", "315", "316", "317", "318", "322"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 323 — Guided-discovery walkable discipline (`guided-discovery` + `discover.discover`)

> Child of the intent-pillar deep program (Spec 307), **discipline layer**. This
> authors the `guided-discovery` walkable discipline (the session-mode spine) and
> the composite `discover.discover` verb that is its act, walking the Spec 307
> flow from seed → confirmed, grounded, clarity-gated Intent — one bounded phase
> at a time.

## Why (evidence + doctrine)

Spec 307 §"The thesis" says a shallow intent is a guess and a discovered intent
is grounded — and the difference is **guided exploration**. The 14 sibling verbs
(309–322) each capture one beat of that exploration, but a beat is not a session.
Without an authored discipline, an agent must *remember the order* — interview
before ground, clarify before frame, gate before confirm — and improvisation is
exactly the failure mode the four-beat `/agency-onboard` (Spec 148) leaves open:
it mints an Intent in four scripted prose beats with **no research grounding, no
ambiguity loop, no clarity gate** (Spec 307 §"Why"). The WHY is captured, not
discovered.

The substrate already solves "deliver a procedure one bounded phase at a time":
`develop.skill_walk(name, inputs, resume_from)` (Spec 081, Spec 018 Win 1) walks
a phase-graph to its first hard gate, recording each phase as `SkillRun`
provenance so context stays bounded (Goal 1) and the lifecycle is uniform across
agents (Goal 3). The `intent` capability's authored `critical-thinking`
discipline (`agency/capabilities/intent/_main.py:24-37`) is the exact shape: a
`kind="discipline"` skill dict with an `applies_when` Matcher, phases that name
their `verbs` + `produces`, and a hard `gate` on the terminal `decide` phase.
This spec is that shape, applied to discovery — and it **supersedes** the
prose-script onboard with a graph-walked, gated, provenance-recording session
mode (Goal 9: the discovery converges on the `discovery-session.md` Document).

## Design

**Cluster:** `agency/capabilities/discover/clusters/interview.py` (Spec 307 verb
table: `discover` lands in the `interview` cluster). **Skill home:**
`discover.ontology.skills["guided-discovery"]`, registered in
`agency/capabilities/discover/ontology.py` (the slot Spec 308 reserves).

### The authored discipline (overrides the derived `discover-usage`)

`guided-discovery` is `kind="discipline"`, so it **overrides** the Spec 081
derived `discover-usage` default (the per-role-cluster walk a drop-in cap gets
free) — same override mechanism the `intent` cap uses. The `applies_when` Matcher
is a `pattern` kind firing on a fresh-or-vague seed; the engine's
`intent.suggests` projection (`agency/capabilities/intent/_main.py:166`) routes
to it when the context matches:

```python
GUIDED_DISCOVERY_SKILL = {
    "name": "guided-discovery",
    "kind": "discipline",
    "applies_when": {"kind": "pattern",
                     "pattern": r"new|fresh|not sure|vague|what do i want|where do i start|start",
                     "confidence": 0.7},
    "phases": [
        {"index": 1, "name": "elicit",     "produces": ["draft_intent", "elicitation_turns"],
         "verbs": ["interview"]},                                    # Spec 309
        {"index": 2, "name": "ground",     "produces": ["citations", "feasibility_signal"],
         "verbs": ["ground", "feasibility"]},                        # Spec 312 + 314
        {"index": 3, "name": "clarify",    "produces": ["ambiguities_resolved"],
         "verbs": ["clarify"]},                                      # Spec 311
        {"index": 4, "name": "frame",      "produces": ["sharp_intent"],
         "verbs": ["frame"]},                                        # Spec 315
        {"index": 5, "name": "examine",    "produces": ["thinking_findings"],
         "verbs": ["examine"]},                                      # Spec 316
        {"index": 6, "name": "scope",      "produces": ["scope_boundaries", "acceptance_criteria"],
         "verbs": ["scope", "acceptance"]},                          # Spec 318 + 317
        {"index": 7, "name": "decide",     "produces": ["confirmed_intent"],
         "verbs": ["clarity"], "gate": "hard"},                      # Spec 322 gate → confirm
    ],
}
```

The phase order walks the Spec 307 §"The guided-discovery flow" diagram exactly:
seed → elicit → ground → clarify → frame → examine → scope+acceptance → decide.
The walker delivers **one phase per `skill_walk` step** (Spec 081), so the agent
never holds the whole flow in context — it receives the current phase's verbs,
runs them, and the engine advances. The `examine` phase's `verbs: ["examine"]`
honours the Spec 291 merge: discovery's thinking pass routes through
`discover.examine` (Spec 316), which composes the `thinking` methods — no second
critical-thinking surface.

### The composite verb — `discover.discover`

```python
@verb(role="act")
def discover(self, seed: str = "") -> ToolResult:
    """The full guided-discovery walk (the discipline's spine).

    Opens (or recalls) a DiscoverySession from `seed` (defaults to the serving
    intent's purpose), then hands control to `develop.skill_walk(name=
    "guided-discovery")`. Returns the FIRST phase's payload + the session_id —
    each subsequent step is a skill_walk resume. The hard gate on phase 7 reads
    the Spec 322 clarity score and refuses `decide` until clarity >= threshold.
    chain_next: walk to the gate, then `discover.state` / `discover.replay`.
    """
```

`role="act"` (Spec 307 verb table) — it writes: it opens the `DiscoverySession`
node (via `_base._session(seed)`, Spec 308) and its `DISCOVERED` edge, and each
walked phase records its sibling's nodes/edges. `discover.discover` does **not**
re-implement the per-phase verbs — it is the **spine** that sequences them via
the shared walker (Spec 081 §"one shared walker"; rule 5 cluster coherence — no
new walking verb per capability).

### The hard gate (the invariant's teeth)

Phase 7 (`decide`) carries `gate: "hard"`. Per Spec 322, the gate reads the live
clarity score for the session's Intent and **blocks** until `clarity >=
threshold`; only then does `decide` confirm the Intent (calls `intent.confirm`,
Spec 029). This makes "you cannot confirm an unclear intent" a structural
property of the walk, not a reviewer's hope. If clarity is below threshold the
gate returns the open ambiguities (from `discover.state`, Spec 324) and the walk
re-enters at `clarify` rather than advancing.

### Session-mode entry — supersedes `/agency-onboard`

A new `commands/agency-discover.md` routes `/agency-discover` to
`develop.skill_walk(name="guided-discovery", inputs={"seed": "<arg>"})` — the
graph-walked successor to the four prose beats of `/agency-onboard` (Spec 148).
The onboard's four beats (describe · configure · confirm · capture) become the
*first phase* (`elicit`, via `discover.interview`, Spec 309) of a seven-phase
discipline; the remaining six add the grounding, clarification, framing,
examination, scoping, and gating the prose script never had. `/agency-onboard`
stays as the no-discovery quick path (declined-onboarding fallback); `/agency-
discover` is the deep, session-mode default (Spec 307 §"session-start protocol"
successor).

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **One phase per step.** Walking `guided-discovery` via `develop.skill_walk`
  yields exactly ONE phase payload per step (assert the returned phase index
  advances by 1 each resume and the payload names a single phase) — computed from
  the walk's `SkillRun` events, not a pinned phase list.
- **Cannot reach `decide` before the gate clears.** With clarity below the Spec
  322 threshold, resuming the walk does NOT return the `decide` phase / does NOT
  confirm the Intent; once `discover.clarity` reports `>= threshold`, the next
  resume reaches `decide`. Assert the gate is monotonic in the clarity score
  (derived from the live score, never a frozen number).
- **Override holds.** `discover.ontology.skills["guided-discovery"].kind ==
  "discipline"` and it is the skill `intent.suggests` returns for a vague seed —
  proving it overrode the derived `discover-usage` (assert the derived default is
  NOT what walks).
- **Phase verbs are live siblings.** Every `verbs` entry in the phase graph
  resolves to a registered `discover` verb (set-membership against the live
  registry, so renaming a sibling breaks here, not silently) — `interview`,
  `ground`, `feasibility`, `clarify`, `frame`, `examine`, `scope`, `acceptance`,
  `clarity` all present.
- **Provenance recorded.** A completed `discover.discover` walk leaves a
  `DiscoverySession` with a `DISCOVERED` edge to the confirmed Intent and a
  `SkillRun` per phase — assert the SkillRun count equals the number of phases
  actually walked (computed, not pinned).

## Acceptance

A fresh agent typing `/agency-discover "I want to build something but I'm not
sure what"` is walked through seven bounded phases — eliciting, grounding in
research, clarifying ambiguity, framing, examining, scoping — and **cannot
confirm** the Intent until the clarity gate clears, with every phase recorded as
provenance. The discipline is the session-mode entry that supersedes the prose
`/agency-onboard`, and it adds no walking machinery beyond the shared
`develop.skill_walk` (rule 5).

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** Discipline-layer child of Spec 307. Depends on the scaffold
  (308) for the skill slot + `_base._session`, and on siblings 309/311/312/314/
  315/316/317/318/322 for the phase verbs — so it lands *after* its phase verbs
  exist (or alongside, with phases referencing not-yet-built verbs failing the
  "phase verbs are live siblings" test until each ships).
- **Build slice:** author the skill dict + `discover.discover` spine + the gate
  read of Spec 322; wire `/agency-discover`. The gate's clarity-threshold value
  is the one tunable budget (CLAUDE.md #8 — a named, overridable config, not a
  snapshot), owned by Spec 322 and read here.
- **Open question (resolve at build):** whether `examine` (phase 5) and `frame`
  (phase 4) should swap — framing after examination may sharpen better. Default:
  follow the Spec 307 flow diagram (frame → examine); revisit if dogfooding shows
  the inverse reads better (surface via `reflect.note`, not a new doc).
