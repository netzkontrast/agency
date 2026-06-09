---
type: theory-chunk
chunk_id: dt-00-storyform-validation
summary: Checklist for validating a completed storyform against Dramatica's hard structural rules and soft completeness checks before locking it in.
covers_ontology_ids:
  - concept.storyform
  - concept.crucial-element
serves_scenarios:
  - novel.storyform-slot-fill
  - novel.dual-storyform
size_kb: 8
depends_on_chunks:
  - dt-00-storyform-worksheet
  - dt-01-foundations
---

# Storyform Validation

> Run this against a filled `00-storyform-worksheet.md` before declaring the storyform locked. Hard rules are structural — if violated, the storyform is invalid as Dramatica defines it. Soft checks are completeness/quality flags — they don't break the storyform but tend to predict trouble in encoding.

---

## Hard rules

These come from the geometry of the Dramatica model. A storyform that fails any of these is broken and will produce incoherence in the draft.

### H1 — Exactly four throughlines

The storyform must name all four: Overall Story (OS), Main Character (MC), Impact Character (IC), Subjective Story (SS). If any is unnamed, the storyform is incomplete; encoding decisions made downstream will paper over the gap and produce inconsistency.

Most common violation: missing SS (no relationship-as-its-own-story between MC and IC).

### H2 — Each Class used exactly once

Universe, Physics, Mind, Psychology — each Class is assigned to exactly one throughline. Two throughlines in the same Class is a structural collapse: two perspectives competing for the same conflict-domain.

### H3 — OS-SS and MC-IC are complementary dynamic pairs

The four Classes split into two dynamic pairs:
- **State pair:** Universe ↔ Mind
- **Process pair:** Physics ↔ Psychology

OS and SS must be in one dynamic pair; MC and IC must be in the other. So:
- If OS=Universe → SS=Mind, MC and IC split Physics/Psychology
- If OS=Physics → SS=Psychology, MC and IC split Universe/Mind
- If OS=Mind → SS=Universe, MC and IC split Physics/Psychology
- If OS=Psychology → SS=Physics, MC and IC split Universe/Mind

If your assignments don't fit one of those four configurations, the storyform is invalid.

### H4 — Story Goal sits at Type level

The Story Goal is one of the 16 Types (e.g. *Obtaining*, *Becoming*, *Doing*, *Understanding*). Not a Variation, not an Element. If your Goal reads like an Issue ("the goal is morality") or an Element ("the goal is faith"), it's pitched at the wrong level — re-pitch it as a Type.

### H5 — Crucial Element sits at Element level

The Crucial Element is one of the 64 Motivation Elements (e.g. *Pursue*, *Avoid*, *Logic*, *Feeling*, *Faith*, *Disbelief*). Not a Variation, not a Type. If your Crucial Element reads like a theme word ("inequity" — wait, that one IS an Element; check `09-reference.md`), verify against the Element list. If it doesn't appear there, you've named something at the wrong granularity.

### H6 — Crucial Element lives in the OS

The Crucial Element is one of the OS Character Elements. The MC sits on it within the OS — that's what makes the MC's personal arc structurally connected to the objective story. If you find yourself saying the Crucial Element is "in the MC throughline only" or "in the SS only", you've separated the MC from the OS and the storyform is broken.

### H7 — MC Resolve and Crucial Element role agree

Two valid pairings:
- **MC Resolve = Change** ↔ Crucial Element is the **Problem** (MC must give it up)
- **MC Resolve = Steadfast** ↔ Crucial Element is the **Solution** (MC must hold to it)

If MC Resolve is Change but the Crucial Element is framed as the right thing to hold — or vice versa — Step 3 and Step 6 of the worksheet contradict. Pick which one is true and fix the other.

### H8 — IC sits on the dynamic-pair partner of the Crucial Element

If MC sits on *Pursue*, IC sits on *Avoid*. If MC on *Logic*, IC on *Feeling*. If MC on *Faith*, IC on *Disbelief*. The MC↔IC opposition runs through this pair. If your IC's defining Element is something unrelated to the Crucial Element's pair, the IC throughline isn't doing its structural job.

### H9 — No character carries both Elements of a dynamic pair

A character cannot hold both *Pursue* and *Avoid*; cannot hold both *Logic* and *Feeling*. You can be FOR or AGAINST something in a story, not both at once. If a character ends up assigned both halves of a pair, split them across two characters or pick one.

### H10 — Outcome × Judgment yields exactly one of four endings

| | Outcome: Success | Outcome: Failure |
|---|---|---|
| **Judgment: Good** | Triumph | Personal Triumph |
| **Judgment: Bad** | Personal Tragedy | Tragedy |

Outcome and Judgment are independent dynamics. *Failure* doesn't automatically mean Bad ending; *Success* doesn't automatically mean Good. (Personal Triumph: the OS goal isn't reached but the MC ends well — common in coming-of-age. Personal Tragedy: the OS goal *is* reached but the MC pays internally — common in noir.) If you find yourself collapsing these two dynamics into one, separate them.

### H11 — Story Driver consistent across act transitions

If Story Driver = Action, every act-to-act transition is forced by an action that prompts a decision. If = Decision, every transition is a decision that prompts an action. The chosen Driver must hold for *all* major transitions — not just the inciting incident.

If Act 1 → Act 2 is driven by an action but Act 2 → Act 3 is driven by a decision, the Story Driver is inconsistent and the plot will feel arrhythmic.

### H12 — All four Signposts of a throughline are the four Types of that throughline's Class

If MC's Class is Universe, MC's four Signposts must be the four Universe Types: Past, Progress, Present, Future. You can't smuggle in a Type from another Class. The Type ordering is constrained further by other dynamics — see `07-storyencoding.md`.

---

## Soft checks

These don't break the storyform but predict draft trouble. Worth running before encoding.

### S1 — Premise is articulable in one sentence

If you can't state the premise in a single sentence (Step 0 of the worksheet), the thematic argument is probably under-formed. The storyform will be technically valid but will have nothing to argue, and the encoding will feel mechanical.

### S2 — IC's challenge to MC is concrete

You should be able to finish: "The IC challenges the MC's worldview by being/doing/representing _______." If the answer is vague ("they're just different"), the IC throughline isn't earning its structural place yet.

### S3 — SS has its own arc, not just MC+IC scenes

The SS is the relationship treated as its own story — with its own concern, issue, problem, progression. If you can't describe what the relationship *as an entity* learns or fails to learn, the SS exists in name only.

### S4 — Each thematic story point is concrete enough to write

Concerns, Issues, Problems work as words. But for encoding, each needs at least one concrete instantiation. "Issue: Skill" → "specifically: who can fly a Y-wing under fire, who has the Force-sensitivity, who knows how to read a star chart." If you can't instantiate, encoding will struggle.

### S5 — Goal, Consequences, Forewarnings, Requirements form one coherent arc

Test: "If the Requirements aren't met, the Consequences arrive, and the Forewarnings tell us they're coming." If those four don't fit that sentence, the static plot story points aren't aligned.

### S6 — Costs and Dividends are visible, not just structural

If your Costs and Dividends exist in the storyform but never show up as scene material, they're decorative. Either drop them or schedule scenes for them.

### S7 — At least one full Signposts-and-Journeys progression has been picked

You don't need all four throughlines fully sequenced before drafting, but at least the OS and one of MC/IC/SS should be sequenced — otherwise act structure is arbitrary.

### S8 — Author's Intent isn't ironic relative to the storyform

If your Premise is "control destroys what it tries to preserve" but you've picked Outcome = Success / Judgment = Good and a control-the-situation Goal, the storyform is going to argue *against* your premise. That can be deliberate (unreliable-author stories), but it's almost always accidental and worth catching early.

---

## Tier check

When something fails:

- **Hard rule failure** → fix the storyform before drafting. The structure is broken.
- **Soft check failure** → flag it, decide whether to fix now or accept the risk. Some draft problems trace back here later; some don't.
- **Multiple hard rules failing** → most likely cause is a wrong throughline assignment in Step 1 or wrong Class assignment in Step 2. Re-derive from those, don't try to patch downstream.
