# TODO — `ncp-author` Skill

Last updated: 2026-05-03 (session 3)
Status: **MVP, version 0.3.0.** Single-skill scope (Path A) committed. Validator + templates shipped. `novel-architect` cross-link in place. Eval set ready (5 cases, 4 EN + 1 DE) but not yet executed against the live skill.

This file tracks every open decision and unfinished item. Items are ordered roughly by what unblocks the most downstream work. Each carries an ID (`T-N`) for cross-reference from `SPEC.md` and conversation logs.

---

## P0 — Blocking decisions (need Michael)

*(none currently open — T-1 settled in session 2, T-7 wired in session 3)*

---

## P1 — Build items (mechanical work, no decision needed)

### T-9 — SKILL.md description optimization
**Status:** Description rewritten in v0.2.0 (drops WIP framing, adds DE triggers, commits Path A); *automated* optimization still pending; eval set now exists (T-10 done) so the optimizer has something concrete to score against
**Spec:** Current description is hand-tuned. The `skill-creator`'s `scripts/run_loop.py` description optimizer requires `claude -p` (Claude Code CLI), which is not available in claude.ai. Defer until skill is run from a Claude Code session. The 5-case eval set at `evals/evals.json` is what the optimizer should score against.

---

## P2 — Open questions inherited from SPEC.md

### T-5 — Chapter-level scaffolding gap
**Status:** Open
**Inherited from:** SPEC.md §5.6 + Implementation Notes §3
**Issue:** NCP has no native "Chapter" entity. SPEC proposes custom-labeled `overviews` as the compensation; that works for top-of-book overviews but doesn't scale to chapter-level scaffolding for novel-length work.
**Options:**
- (a) Use `storytelling.moments[].act` + `order` as proxy chapters; document the convention
- (b) Define an external chapter container that references `moment.id` arrays
- (c) Lobby upstream NCP to add a `chapters[]` array

**Recommendation:** (a) for now (zero schema changes); (b) when a project actually needs persistent chapter metadata; (c) only if pattern (b) becomes broadly useful.

### T-6 — Multi-agent concurrent edit merging
**Status:** Open (from SPEC.md §12)
**Issue:** "How are multi-agent concurrent edits merged in a single JSON file?" SPEC says "Assume git-level merging for now" — this is fine until two agents touch the same field, at which point JSON-merge conflicts are nasty.
**Options to evaluate:**
- Path-based diffing (jq + jsonpatch)
- CRDT layer over the JSON (overkill?)
- Lock-per-section (one agent owns Storypoints, another owns Moments — write turns)

**Decision deferred until** there's actually a multi-agent workflow running against a shared NCP file. Premature for current state.

### T-8 — Quad (KTAD) integrity layer
**Status:** Open (from SPEC §4.6 pre-commitment + Implementation Notes §1)
**Issue:** NCP doesn't encode Quads. The proposed `dramatica-validator` cross-cutting skill from SPEC §8.10 cannot ground all KTAD checks in NCP alone — must consult `dramatica-vocabulary` or `dramatica-theory`.
**Action:** Document this clearly in any future `dramatica-validator` skill spec. Until then, `ncp-author` validation explicitly excludes KTAD coherence (see `references/validation-rules.md` §7) and points to the Dramatica skills.

---

## P3 — Iteration items (post-MVP polish)

### T-15 — Run the eval set against the live skill
**Status:** Not started (new — created when T-10 closed)
**Spec:** With `evals/evals.json` shipped, the next step is execution. Per `skill-creator`'s claude.ai-friendly path: load the skill, execute each test prompt one at a time, present output inline for Michael's review, iterate the skill on feedback. Five cases is the right size for inline review without overwhelm.
**Recommendation:** run in a fresh session so Claude is loading the skill cleanly rather than already in-context. Start with eval #2 (audit path) — it's the most discriminating because the skill must NOT silently fix.

### T-11 — Bidirectional Subtxt/Dramatica-software interoperability
**Status:** Out of scope until requested
**Note:** SPEC §3.2 explicitly excludes proprietary Dramatica software output. But Write Brothers + Narrative First merged in 2025 (per upstream README) and the Subtxt/Dramatica platform is the canonical NCP producer. Round-tripping NCP ↔ Subtxt could matter eventually. Not now.

### T-13 — Ralph integration
**Status:** Out of scope (Path A committed, not Path C)
**Note:** SPEC §7's "Autonomous hand-off via NCP-state" is a Ralph-style loop. Closed unless Path C is later opened.

### T-14 — Upstream re-pin policy
**Status:** Closed in session 3
**Resolution:** Documented in `upstream/_PINNED_AT.md`. Policy: re-pin on demand (real conflict, not schedule). Commit must include validator re-run against the two template assets and a one-line trigger note.

---

## Done

- ✅ **T-7 — `novel-architect` cross-link wired (session 3).** Bidirectional. `ncp-author/references/related-skills.md` now has a real `novel-architect` entry replacing the placeholder, with the orchestrator → backend wiring direction documented. `novel-architect/SKILL.md` gets `ncp-author` added to its Integration table (Backend relation) and to its Navigation block.
- ✅ **T-10 — Eval set shipped (session 3).** 5 prompts at `evals/evals.json`: 4 EN + 1 DE. Inputs reference upstream canonical examples (`anora.json`, three from `invalid/`) rather than fabricated fixtures. One bespoke input (`evals/files/outline.md`) for the conversion test. Execution is T-15 (next session).
- ✅ **T-14 — Upstream re-pin policy documented (session 3).** Re-pin on demand, not on schedule. Trigger = real conflict. Commit includes validator re-run against the two template assets and a one-line trigger note. Lives in `upstream/_PINNED_AT.md`.
- ✅ **T-1 — Granularity decided: Path A (single skill).** Splitting deferred indefinitely; merging back from a split is expensive, so single skill is the lowest-regret commit.
- ✅ **T-2 — `scripts/validate.js` shipped.** Thin Ajv wrapper around the pinned upstream schema. Matches `upstream/tests/validate-file.js` settings (`strict:false`, `allErrors:true`). `package.json` stub added; `npm install` once and the validator works.
- ✅ **T-3 — `assets/template-empty.json` shipped.** Minimal valid skeleton: schema_version + all required story fields + one empty narrative with all five subtext arrays empty + storytelling.overviews/moments empty. Validates clean.
- ✅ **T-4 — `assets/template-storyform.json` shipped.** Cleaned trim of `upstream/examples/complete-storyform-template.json`: 4 perspectives, 143 Storypoints (canonical slot list per throughline), 16 Storybeats. Legacy `signpost` field stripped (`scope` + `sequence` already encode it). Validates clean against the pinned schema — unlike upstream's own version.
- ✅ **T-12 — Language decided: EN-primary, DE supplementary.** Description carries DE triggers; SKILL.md has a DE-Notiz callout; schema fields stay English (canonical).
- ✅ Cloned `narrative-context-protocol` repo at SHA `0b9ab12`, embedded in `upstream/`
- ✅ Extracted canonical enums from `schema/ncp-schema.json` (463 appreciations + 144 narrative_functions + supporting enums)
- ✅ Wrote `references/schema-cheatsheet.md` (top-level shape, required fields, common pitfalls)
- ✅ Wrote `references/canonical-vocabulary.md` (all enum lists, structured for scanning)
- ✅ Wrote `references/validation-rules.md` (semantic rules beyond JSON-Schema)
- ✅ Wrote `references/authoring-order.md` (10-stage practical workflow)
- ✅ Wrote `references/related-skills.md` (delegation map to existing skills)
- ✅ Embedded Michael's SPEC.md (1:1, with Implementation Notes appendix)
- ✅ Wrote draft SKILL.md (WIP-marked, then promoted to v0.2.0 MVP)
- ✅ Wrote this TODO

---

## Working notes for next session

**Completed in session 3:**
- T-7 (novel-architect cross-link, both sides)
- T-10 (eval set with 5 cases, upstream-canonical inputs)
- T-14 (re-pin policy in `upstream/_PINNED_AT.md`)
- Workflow norm captured to memory: pre-flight sync of all relevant `/mnt/skills/user/*` skills into workspace before any skill-coordinating edit.

**Top of next session queue:**
1. **T-15 — execute the eval set.** Five prompts, inline review per skill-creator's claude.ai workflow. Start with eval #2 (audit path) — most discriminating.
2. **T-9 — automated description optimization.** Defer until next Claude Code session. Eval set now exists for the optimizer to score against.
3. Optional: bundle the updated `novel-architect/SKILL.md` patch into a separate `.skill` so Michael can install both together, or leave novel-architect for a dedicated session given its WIP status (OQ-01/02/03 still blocking).

**Files that may still need attention (carried over):**
- `references/related-skills.md` — novel-architect entry now real (✓); other entries still accurate against live frontmatter as of 2026-05-03.
- `upstream/_PINNED_AT.md` — re-pin policy in place (✓).
