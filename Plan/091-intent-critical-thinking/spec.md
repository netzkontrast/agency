---
spec_id: "091"
slug: intent-critical-thinking
status: shipped
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["026"]
domain: capability
wave: 6
---

# Spec 091 — `intent` capability: critical-thinking methods

## Why

User directive (2026-06-07): *"Intent should be a capability — containing critical
thinking methods."* Spec 026's panel wanted the intent→skill projection to live on an
`intent` capability, but none existed. This makes `intent` a first-class capability whose
verbs are **critical-thinking methods** — structured reasoning scaffolds an agent applies
to the serving goal *before* committing to an approach. It gives Intent (the human-owned
root of the four concepts) a reasoning surface, and a provenance trail of *how* a goal was
examined, not just what was done.

## Design

`agency/capabilities/intent.py` (single-file drop-in). Eight `transform` methods, each
returning a deterministic scaffold (the method's steps/prompts) that defaults its subject
to the **serving intent** (`ctx.intent_id`'s deliverable/purpose) and accepts an explicit
override:

- `decompose` (MECE sub-problems) · `assumptions` (load-bearing vs incidental) ·
  `premortem` (assume-failed → causes + mitigations) · `first_principles` (strip to
  fundamentals, rebuild) · `inversion` (what guarantees failure?) · `steelman` (strongest
  counter-case) · `second_order` (and-then-what consequence chain) · `tradeoffs`
  (options × criteria matrix).

An **authored** `critical-thinking` walkable discipline (frame → surface → stress-test →
weigh → decide) overrides the derived `<cap>-usage` (Spec 081) and carries an
`applies_when` pattern Matcher, so `skills.suggests` projects to it on risky/unclear/
trade-off intents (Spec 026 Part B).

**CLI collision (resolved by design):** a capability named `intent` collides with the
legacy `agency intent` capture side-pipe. Spec 079 OQ-3 already handles this — the
capability's unified CLI *group* is skipped (legacy capture wins), while the capability
stays fully reachable via MCP (`capability_intent_*`), code-mode, and the per-verb
`bin/agency-intent-*` wrappers. No core edit.

## Done When

- [x] `intent` registers as a capability with the eight critical-thinking methods;
  bootstrap validates the docstring-derived SkillDoc.
- [x] Methods default the subject to the serving intent; explicit subject overrides;
  `tradeoffs` parses options/criteria with sensible defaults.
- [x] Authored `critical-thinking` discipline lints clean, walks via `develop.skill_walk`,
  and is the target of `skills.suggests` on a matching context.
- [x] CLI collision resolves (legacy capture wins; capability via MCP + bin wrappers).
- [x] `tests/test_intent_capability.py` (7); full suite 920 passed, 3 skipped;
  `check-drift` clean; install regen committed.

## Followup

- **Done (2026-06-07):** relocated `skills.suggests` → `intent.suggests` — Intent now owns
  the projection (026 panel honored). `_all_skills` reused from the skills module (DRY).
  `tests/test_intent_suggests.py` (6). The skills capability is back to find/render/lint/index.
