---
spec_id: "229"
slug: session-driver-slice2-hooks
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "114"
depends_on: ["114", "195", "176", "150"]
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

## Done When

- [ ] **BoundaryUse auto-capture wired** (via Spec 195) — the session
      driver sees raw-tool bypasses.
- [ ] **Cross-session handoff** — a `SessionReflection` (Spec 114) at
      close seeds the next session's Intent (Spec 176 capture reads it).
- [ ] **`develop.brainstorm`/`write_spec`/`implement` skills implemented**
      (114's deferred skills) as walkable phase-graphs.
- [ ] **The session-driver loop feeds the dogfood loop** (Spec 150) —
      boundary-use patterns become amendment proposals.
- [ ] **114 row flips toward Shipped.**
- [ ] Test: a raw edit records BoundaryUse; a close seeds the next
      session's Intent.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 195 (event replay) + Spec 176 (sessionstart capture) compose here.
- **dogfood-loop chain** (150): boundary-use → proposals.

## Open questions

1. Auto-seed the next Intent or offer? **Recommend**: offer (Spec 176
   never blocks); the handoff is a suggestion the user accepts.
