# Vision-Alignment Review — Spec 009 (superpowers-remainder)

**Reviewer:** vision-alignment (spec-panel critique mode)
**Date:** 2026-05-27
**Spec:** `Plan/superseded/009-superpowers-remainder/spec.md`
**Canon:** `docs/vision/CORE.md`, `docs/vision/specs/superpowers-port.md`,
`docs/vision/specs/skills-and-gates.md`, `docs/vision/CAPABILITY-CLUSTERS.md`;
code `agency/capabilities/develop.py`, `skills/code-review/SKILL.md`.

---

## Alignment verdict

**ALIGNED (strong) — proceed with minor must-changes.** The spec is a faithful,
canon-true finishing of the superpowers port. It correctly treats the remainder
as *no new craft*: one half-ported discipline (`receiving-code-review`) plus a
body of reference prose, both delivered by **EXTENDING `develop`** (mutating
`DEV_SKILLS` + `REFERENCES` + the matching `SKILL.md`s), with no new top-level
capability. It honours the pressure→structure thesis, the
drop-a-file/no-wiring contract, and the T3 progressive-disclosure reference
model. Three minor must-changes (below) keep it from over-reaching the canon.

---

## Alignment question 1 — does the spec's gap match `superpowers-port.md`?

**YES — the gap matches the canon's mapping exactly, and the spec correctly
reconciles it.**

- The spec claims "13 of 14 disciplines already covered" with
  `receiving-code-review` as "the ONE uncovered discipline" (spec.md:36, 52).
- `superpowers-port.md` is the canonical mapping. Its table marks every other
  superpowers skill **done** (lines 55–68) and marks **`receiving-code-review`
  the single non-done discipline**: *"folded into the `review` skill
  (assess/resolve phases) … status **partial**"* (superpowers-port.md:63). This
  is the one discipline-row in the table that is not `done`.
- The only other non-`done` row is the **references** row, status **planned**
  (`testing-skills-with-subagents`, `persuasion-principles`,
  `anthropic-best-practices`) (superpowers-port.md:69), and porting principle 6
  *"References travel."* (superpowers-port.md:48–49). The spec scopes exactly
  these (plus the debug/tdd references found in the v5.1.0 tree) as the second
  half of the remainder (spec.md:57–63, Design table 193–200). So the spec's
  two-part remainder (1 discipline + reference corpus) is a one-to-one match to
  the two non-`done` rows of the canon table.
- `CAPABILITY-CLUSTERS.md:13` shows the `develop` row **built (v0.1)** — i.e.
  the discipline engine exists; the spec extends it, it does not re-found it.

**Code confirms the canon's "partial."** `develop.py`'s `review` skill is
`request → dispatch → resolve` with no `triage`/`verify`-against-codebase phase;
receiving rigor is, exactly as the canon says, *implicitly folded into*
`resolve`. The spec's plan to flip `partial → covered` by adding a distinct
`receive-review` skill is the correct closure of canon line 63.

**Verdict on Q1: the spec's gap statement is consistent with — and correctly
finishes — `superpowers-port.md`.** No misalignment.

## Alignment question 2 — Lifecycle-template skills + elicit gates, EXTEND-not-add?

**YES.**

- The new `receive-review` is specced as a `develop` skill schema in `DEV_SKILLS`
  — an ordered phase-graph `read → understand → verify → triage →
  resolve(hard)` ending in a hard gate (spec.md:93–99, 221–228). That is exactly
  the canon's "skill = a Lifecycle template: a graph of atomic Capability steps +
  Gates" (CORE.md:47–54; skills-and-gates.md:13–25) and the porting principle
  "Discipline → gated skill" (superpowers-port.md:31–35).
- The hard gate is **judgment-as-code**: the `resolve` predicate cannot pass
  while any finding is `needs-verification` (spec.md:102–106, 226–228). That is
  canon's "Rationalizations → checks" (superpowers-port.md:36–39) and gates as
  `elicit`/`Gate` nodes (CORE.md:56–62; skills-and-gates.md:33–45) — a hard gate
  that must pass to advance.
- It is **drop-in / no new concept**: the spec explicitly EXTENDS `develop`
  (`DEV_SKILLS` + `REFERENCES`), adds **no new capability file**, and the header
  states this (spec.md:19–26, 173–176, 221–233). This honours CORE.md:123–125
  ("grow the capability set by dropping files … no wiring") and CORE.md:126–128
  (the develop/skill-creation port is the proven precedent).
- The pushback path is modeled as a representable classification
  (`disagree-with-reason` carries reasoning — no silent compliance), encoded as
  a test fixture (spec.md:131–139). This is canon's "rationalization tables
  become test fixtures" (superpowers-port.md:103–104).
- The "drift fix first" (`assess → dispatch` in `code-review/SKILL.md`) keeps the
  installable skill isomorphic to the schema — the schema-renders-three-ways
  isomorphism (CORE.md:65–73). Confirmed real: `develop.py` `review` uses
  `dispatch` (bound to `delegate.fan_out`), but `skills/code-review/SKILL.md`
  still says `assess`. Reconciling to `dispatch` is correct.

**Verdict on Q2: fully aligned.** Nothing is modeled as a new primitive; the
remainder is structure + gates over the existing engine.

## Alignment question 3 — references re-expressed, kept T3 / on-demand?

**YES.**

- The spec mandates the references travel **re-expressed, not copied** — the
  ~46KB `anthropic-best-practices.md` and `persuasion-principles.md` are
  RE-EXPRESSED as original principle-focused prose, vendor source stays
  read-only (spec.md:60–63, 110–117, 142–145). That is the canon stance
  ("References travel … loaded on demand", superpowers-port.md:48–49, principle
  6; and "the knowledge travels, re-expressed" as already practised in
  `develop.py`'s `REFERENCES` docstring lines 83–85).
- They stay **T3 / on-demand**: served by `develop.reference(topic)`, "never
  carried in any system prompt" (spec.md:63, 110, 231–233). This matches the
  progressive-disclosure model — only the next step / fetched doc loads
  (CORE.md:50–54; skills-and-gates.md:53–61) — and the *existing* `reference`
  verb pattern in `develop.py:139–145` (unknown topic returns the available
  list, which the spec preserves at spec.md:117, 139).
- OQ3 (spec.md:264–269) is the canon-critical guard: `persuasion-principles`
  must be re-framed as "WHY structural gates work (parahuman compliance
  research)", NOT "how to write YOU-MUST prose" — directly enforcing
  "System-prompt pressure does NOT port" (superpowers-port.md:99–107). The spec
  correctly flags this as OPEN and requires canon-owner sign-off.

**Verdict on Q3: aligned**, contingent on the OQ3 framing being honoured at
write time.

---

## Misalignments / risks (none blocking; ordered by severity)

1. **MINOR — canon table will be edited by an implementing spec; record the
   provenance.** The spec writes back into `superpowers-port.md` (flips rows to
   covered/dropped, adds the SCRIPT audit; spec.md:124–129, 242–244). The canon
   is authoritative and `superpowers-port.md` is `status: draft`, so editing it
   is legitimate — but the spec should state that the canon table's
   *references* row currently reads **planned** (not "absent") and that the
   author must also flip THAT row, not only add new rows. As written the spec
   enumerates references the canon row never named (debug/tdd refs), which is
   *more* than the canon planned — fine, but the canon row must end with no
   `planned` residue. Make the alignment explicit so the canon and spec do not
   silently diverge on which references were "promised."

2. **MINOR — `receive-review` actor/role vs the canon's `transform` tag.**
   `superpowers-port.md:63` tags `receiving-code-review` as kind **transform**.
   The spec calls it a "transform-home discipline" (spec.md:192, 224) but models
   it as a multi-phase gated `develop` skill (a Lifecycle template), consistent
   with how `develop` already homes `review` (a discipline, not a `transform`
   verb). This is fine — `develop.home = "lifecycle"` and its skills are
   disciplines — but the spec mixes "transform" labels with "discipline" framing.
   Pick one vocabulary: it is a **`develop` discipline (gated phase-graph)**;
   "transform-home" is misleading. Align the label to CORE/CLUSTERS wording.

3. **INFO — `execute` is shipped but absent from the canon table and some
   tests.** `develop.py` ships an `execute` skill and `superpowers-port.md:66`
   marks `executing-plans` **done**, yet `tests/test_agency.py:672,706` assert
   only the 7-skill set (no `execute`, no `receive-review`). Not this spec's bug,
   but the spec's `Done When` (spec.md:130–141) should ensure the
   `test_every_dev_skill_walks_to_a_hard_gate` invariant is asserted over the
   FULL `DEV_SKILLS` set (including `execute` and the new `receive-review`), so
   the new skill cannot regress the canon's "every dev skill ends in a hard
   gate" promise.

---

## Recommended aligned framing (canon-true language to adopt)

- Describe `receive-review` strictly as **"a `develop` discipline — a Lifecycle
  template (gated phase-graph) ending in a hard gate"** (CORE.md:47–54), not a
  "transform-home" verb. The receiving *rigor* becomes **structure** (ordered
  phases) + a **judgment-as-code gate** (the `needs-verification` predicate).
- Frame the whole spec as **"finishing canon row 63 + the planned references
  row 69 of `superpowers-port.md`"** — i.e. it closes the only two non-`done`
  rows of the canonical mapping. This anchors the gap claim directly to the
  canon and removes any ambiguity about "13 of 14."
- For references: keep the exact `develop.py` framing already in the code —
  *"the knowledge travels, re-expressed … fetched by `reference`, never carried
  in any system prompt"* (develop.py:83–85). The spec already uses this; make it
  the literal contract for every new `REFERENCES` entry.

---

## Must-change list

1. **Make the canon-table reconciliation explicit and complete.** State that
   `superpowers-port.md`'s references row (line 69) is **planned** today and
   that the spec must flip BOTH the `receiving-code-review` row (63, partial→
   covered) AND the references row (69, planned→covered/dropped) — leaving the
   canonical mapping with zero `partial`/`planned` rows for in-scope items.
   (Already in `Done When` 124–129; tie it to the specific canon line numbers so
   author and reviewer cannot diverge.)

2. **Fix the role vocabulary.** Replace "transform-home discipline"
   (spec.md:192, 224) with "**`develop` discipline (gated Lifecycle-template
   phase-graph)**." `receive-review` is a discipline homed in `lifecycle`, not a
   `transform` verb; the only `transform` verb touched is `develop.reference`
   (its signature unchanged). This keeps the spec isomorphic with CORE.md:47–54
   and CAPABILITY-CLUSTERS.md:13.

3. **Pin the hard-gate invariant over the full skill set.** The `Done When`
   test line (spec.md:130–141) must assert `test_every_dev_skill_walks_to_a_hard
   _gate` across **all** of `DEV_SKILLS` including `execute` and the new
   `receive-review` (current tests only cover 7), and assert `triage` is a
   NON-terminal, non-gate phase so the canon's "every dev skill ends in a hard
   gate" (CORE.md:122; develop.py invariant) is preserved, not weakened.

(OQ3's "no re-introduced pressure" framing is already correctly OPEN and gated
on canon-owner approval — keep it open until that sign-off; it is the single
most canon-sensitive write in the spec.)
