---
spec_id: "229"
slug: session-driver-slice2-hooks
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "114"
depends_on: ["114", "195", "176", "150", "147", "146", "149", "148", "225", "226"]
vision_goals: [2, 3]
affects:
  - agency/capabilities/develop/_main.py
  - hooks/session-start.sh
  - tests/test_session_driver_slice2.py
---

# Spec 229 — session-driver Slice 2 (hooks + handoff)

## Why

Spec 114 (plugin-as-session-driver) is Partial — Slice 1 shipped 6
verbs + the session-driver skill; Slice 2 names "hooks/session-start.sh
integration (Spec 076 unified-hook layer) auto-records BoundaryUse on
raw Write/Edit/Bash; cross-session handoff; develop.brainstorm/
write_spec/implement skill implementations". Spec 195 (event replay)
already builds the BoundaryUse capture this needs; Spec 176 builds the
SessionStart Intent capture. This composes them to finish 114 Slice 2.
Without this, the session-driver is advisory, not load-bearing — every
raw-tool bypass is invisible, every cross-session handoff is lost.

## Done When

- [ ] **BoundaryUse auto-capture wired** (via Spec 195) with a typed
      return shape:
      ```python
      BoundaryUse = {
        "tool":         Literal["Write","Edit","Bash","WebFetch",...],
        "intent_id":    str,                 # SERVES which Intent
        "verb_shadow":  str | None,          # the verb that SHOULD have run
        "tokens_used":  int,
        "timestamp":    str,                 # bi-temporal
        "session_id":   str,
      }
      ```
      Invariant: every Write/Edit/Bash invocation under an active
      Intent emits exactly ONE `BoundaryUse` node; the count of
      BoundaryUse nodes per session equals the count of raw-tool
      invocations on the transcript (replay parity).
- [ ] **`verb_shadow` is derived, not authored** — the session driver
      consults the verb registry (Spec 149) to name which capability
      verb would have served the same intent (`Bash("pytest")` →
      `develop.test`; `Write("Plan/NNN/spec.md")` → `develop.write_spec`).
      Invariant: `verb_shadow` is non-null when a registered verb
      matches the tool+arg signature; null otherwise.
- [ ] **Cross-session handoff** — a `SessionReflection` (Spec 114) at
      close seeds the next session's Intent (Spec 176 capture reads it).
      Typed shape:
      ```python
      SessionHandoff = {
        "from_session_id": str,
        "to_session_id":   str | None,       # null until next session opens
        "carry_intent":    str | None,       # Intent id to resume
        "open_questions":  list[str],
        "tokens_consumed": int,
        "boundary_use_ct": int,              # how often raw-tool bypassed
      }
      ```
      Invariant: every closed session emits exactly ONE
      `SessionHandoff` node; the next `SessionStart` consumes at most
      one pending handoff (the most recent).
- [ ] **`develop.brainstorm`/`write_spec`/`implement` skills implemented**
      (114's deferred skills) as walkable phase-graphs — each emits ONE
      phase per call (Spec 114 phase-graph discipline); each phase
      records its own Intent + Artefact graph.
- [ ] **The session-driver loop feeds the dogfood loop** (Spec 150) —
      boundary-use patterns become amendment proposals. Invariant: when
      `boundary_use_ct / verb_invocation_ct > 0.3` for a session, a
      `Reflection(scope="driver-drift")` is emitted; Spec 150 classifies
      it as a candidate amendment.
- [ ] **Hook isolation honored** — `hooks/session-start.sh` mutates ONLY
      the agency graph (no global state, no env vars persisted); a hook
      failure degrades to advisory (the session opens without an
      auto-seeded Intent), never blocks.
- [ ] **Failure modes** (touches hooks + cross-session state):
      `Codes.HOOK_TIMEOUT` when session-start.sh exceeds 5s (hook
      degrades to advisory; SessionHandoff still readable next session);
      `Codes.HANDOFF_STALE` when a pending handoff is older than 24h
      (offered with a freshness warning, never auto-resumed);
      `Codes.BOUNDARY_REPLAY_MISMATCH` when BoundaryUse count diverges
      from transcript-replay count (Spec 195 invariant — hard error,
      points at the missing capture site);
      `Codes.PHASE_GRAPH_BROKEN` when a walkable skill emits >1 phase
      per call.
- [ ] **Output-budget honored** (Spec 146) — SessionHandoff bodies are
      bounded (≤ 1024 tokens of open_questions); overflow truncates with
      `truncated: true`, never silently drops.
- [ ] **114 row flips toward Shipped** with derived completion %
      (Spec 149 reads verb + walkable-skill counts off the live
      registry; the row is not hand-authored).
- [ ] Test: a raw edit records BoundaryUse with the right `verb_shadow`;
      a close emits SessionHandoff; the next session's SessionStart
      consumes it and seeds an Intent; the brainstorm skill emits
      exactly one phase per call; replay parity holds.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  an active Intent and the user invokes raw Bash("pytest -q")
When:   the session driver's hook fires
Then:   emits BoundaryUse{tool:"Bash", verb_shadow:"develop.test",
        intent_id:<active>, tokens_used:N};
        the substrate sees the bypass; the count matches the
        transcript-replay count exactly

Given:  a session closes with 2 open questions and 1 carry intent
When:   the close hook fires
Then:   emits SessionHandoff{carry_intent:<id>, open_questions:[..2..],
        boundary_use_ct:5}; the next SessionStart reads it, offers
        (not forces) the carry intent

Given:  a session where boundary_use_ct == 8 and verb_invocation_ct == 20
When:   the session closes
Then:   ratio 0.4 > 0.3 threshold; emits Reflection(scope:"driver-drift");
        Spec 150 classifier sees it as candidate amendment

Given:  hooks/session-start.sh hangs for 7s
When:   the session opens
Then:   raises Codes.HOOK_TIMEOUT at 5s, session opens in advisory
        mode (no auto-seeded Intent), the pending SessionHandoff
        remains readable for the next attempt — never lost
```

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| `HOOK_TIMEOUT` (>5s) | degrade to advisory; handoff persists for next session |
| `HANDOFF_STALE` (>24h) | offer with warning; never auto-resume |
| `BOUNDARY_REPLAY_MISMATCH` | hard error; points at missing capture site |
| `PHASE_GRAPH_BROKEN` (>1 phase emitted) | hard error; the skill is malformed |
| Hook env-var leakage | hard error per hook-isolation invariant |
| Handoff body overflow | truncate to 1024 tokens; `truncated: true` flag |

## Interconnects

- Spec 195 (event replay) provides the BoundaryUse capture substrate.
- Spec 176 (SessionStart capture) reads the SessionHandoff at open.
- Spec 150 (dogfood loop) classifies driver-drift Reflections as amendments.
- Spec 147 (LLM driver) is invoked by the walkable skills when their
  phases need inference.
- Spec 146 (output-budget) bounds SessionHandoff body size.
- Spec 149 (derived docs) reads the verb/skill counts for the 114 row.
- Spec 148 (slash family) provides the `/agency` SessionStart entry the
  hook complements.
- Spec 225 (prompt cap Slice 2) supplies the prompts the walkable
  skills compose.
- Spec 226 (thinking cap Slice 2) supplies the methods the
  `develop.brainstorm` skill walks.

## Open questions

1. Auto-seed the next Intent or offer? **Recommend**: offer (Spec 176
   never blocks); the handoff is a suggestion the user accepts —
   auto-seed would violate the "user is creative, AI captures" doctrine.
2. **BoundaryUse capture grain.** Every raw tool, or only Write/Edit/Bash?
   **Recommend**: every raw tool with a registered verb shadow; the
   verb registry (Spec 149) decides — keeps capture aligned with the
   substrate, not the harness.
3. **Driver-drift threshold.** 0.3 is a guess. **Recommend**: ship 0.3
   as default, document as tunable (rule 8 — named config); refine the
   threshold once Spec 150 reports drift Reflections for 4 weeks (the
   data sets the threshold, not the spec).
4. **Phase-graph implementation per skill.** Hand-authored YAML or
   derived from method registry? **Recommend**: hand-authored per skill
   (the phase content IS the discipline); only the skill's verb count
   in the 114 row is derived.
5. **Stale-handoff TTL.** 24h is a guess. **Recommend**: ship 24h as
   default tunable; revisit once cross-session handoff has 1 month of
   field data.
