---
type: theory-chunk
chunk_id: dt-11-anti-patterns
summary: Catalog of common Dramatica misapplications—everyday vs. technical word sense confusions and collapsed distinctions—with failure modes and fixes.
covers_ontology_ids:
  - concept.storyform
  - throughline.*
  - element.*
serves_scenarios:
  - novel.diagnose-flat-draft
  - novel.character-arc
size_kb: 12
depends_on_chunks:
  - dt-01-foundations
  - dt-02-characters
  - dt-04-theme
---

# Anti-Patterns

> Common mistakes when applying Dramatica. Most of these come from misreading the model — using a familiar word in its everyday sense rather than its Dramatica-specific sense, or collapsing two distinctions the model treats as separate. Each pattern: the failure mode, why it happens, the fix.

---

## AP-1: Confusing MC with Protagonist

**Failure mode.** Treating "Main Character" and "Protagonist" as synonyms, then writing as if the storyform constrains them together.

**Why.** In ordinary critical vocabulary the two terms collapse. Most stories Western audiences default to *do* have MC=Protagonist (Luke is both, Rocky is both, Frodo is both).

**Why it matters.** Dramatica separates them deliberately, because some of the most interesting stories don't collapse them. *To Kill A Mockingbird*: Atticus is the Protagonist (he pursues the goal, he's the OS-throughline driver), but Scout is the MC (we live inside her experience). *The Great Gatsby*: Gatsby is the Protagonist, Nick Carraway is the MC.

**Fix.** Ask two questions separately:
1. Whose personal struggle do we live inside? (= MC)
2. Who pursues the OS Story Goal? (= Protagonist)

If they're the same person, fine. If not, you have a non-collapsed story and the storyform must reflect that.

---

## AP-2: Forgetting the Subjective Story throughline

**Failure mode.** Storyform names OS, MC, IC. SS is left blank or filled with vague "their relationship".

**Why.** SS is the easiest throughline to overlook because it's a *relationship* treated as its own entity, not a person.

**Why it matters.** A draft without SS feels like the MC and IC never get a real story together — they collide as opponents, or they stand near each other, but their *relationship* doesn't develop on its own arc. The audience never gets the "we" perspective.

**Fix.** Treat the relationship as a character. Give it a Concern, an Issue, a Problem, a progression. Ask: what does the *relationship* want? What does it learn? Where does it end up?

Mockingbird example: SS is Scout↔Boo Radley. The relationship's arc is: invisible-Boo → mythical-Boo → understood-Boo. That's an SS arc, not just "they meet at the end".

---

## AP-3: Story Goal pitched at the wrong level

**Failure mode.** Goal stated as a Variation ("the goal is *fairness*") or an Element ("the goal is *faith*") instead of a Type.

**Why.** Authors naturally state goals in thematic-feeling words, which tend to be at Variation or Element level.

**Why it matters.** The Goal *is* the OS's Type. If it's at the wrong level, the storyform can't connect Type-level Concerns to Variation-level Issues to Element-level Problems coherently — the rest of the thematic story points won't have a Goal to anchor to.

**Fix.** Re-pitch at Type level. "Fairness" is a Variation — the Goal is probably "Becoming" (changing the Justice system) or "Doing" (executing fair acts) or "Future" (establishing fairness as future condition). Find the Type that captures the OS Class's slice of the goal-question.

---

## AP-4: Crucial Element too abstract

**Failure mode.** Crucial Element stated as a theme word that isn't actually one of the 64 Motivation Elements.

**Why.** Authors think in themes; the 64 Elements are a constrained vocabulary that doesn't always match the author's thematic intuition word-for-word.

**Why it matters.** The Crucial Element has a structural job (anchor the MC↔IC opposition; pivot of MC Resolve). If it's not a real Element, the structural mechanics don't engage — you can't identify its dynamic-pair partner for the IC, you can't check Resolve coherence.

**Fix.** Look up the 64 Elements list in `references/09-reference.md`. Find the one closest to your thematic intent. If the closest match is too far from what you mean, your thematic intent might be at Variation or Issue level — bump up one level and re-derive.

---

## AP-5: Class double-assignment

**Failure mode.** Two throughlines end up wanting the same Class — both OS and MC feel like Universe, or both MC and IC feel like Mind.

**Why.** Same draft material can read multiple ways depending on which character's POV you take. If two characters have similar problem-domains, both throughlines will gravitate to the same Class.

**Why it matters.** Hard rule violation. Each Class is one throughline only.

**Fix.** Either:
- Differentiate the two throughlines more sharply (one is really about the situation; the other is really about the activity within that situation), or
- Reassign one to a different Class and re-derive the dynamics from there. Often the IC's Class is the one that needs to shift, since IC tends to be the throughline authors think about least concretely.

---

## AP-6: MC Resolve and Crucial Element disagree

**Failure mode.** Author picks Change for MC Resolve and frames the Crucial Element as the *right thing to hold onto*. Or picks Steadfast and frames the Crucial Element as *the problem*.

**Why.** Resolve gets picked from feeling about the MC's arc; Crucial Element gets picked from feeling about the theme. Both get picked separately, and they don't always agree.

**Why it matters.** Hard rule violation. The Resolve and the Crucial Element role are tied: Change pairs with Crucial-Element-as-Problem, Steadfast pairs with Crucial-Element-as-Solution.

**Fix.** Pick which one you trust more — Resolve or Crucial Element — and revise the other. If the MC clearly transforms in the climax (Change), then whatever you've named as Crucial Element must be the *problem* the MC gives up. If the MC clearly endures (Steadfast), it must be the *solution* the MC holds.

---

## AP-7: Conflating Outcome and Judgment

**Failure mode.** Storyform records a single ending-feel ("happy ending" or "sad ending") rather than two independent dynamics.

**Why.** In ordinary criticism, ending = good or bad. Dramatica splits this into Outcome (was the OS goal achieved?) and Judgment (is the MC at peace?).

**Why it matters.** The four-cell matrix Triumph / Personal Triumph / Personal Tragedy / Tragedy disappears if you only track one dimension. You miss the *Casablanca* shape (Failure outcome — they don't get away together — but Good judgment because Rick has resolved his personal arc).

**Fix.** Always pick Outcome and Judgment separately. Practice on existing films — Casablanca: Failure/Good. Star Wars: Success/Good. Chinatown: Failure/Bad. Hamlet: Failure/Bad with everyone dying.

---

## AP-8: Mental Sex read as gender identity

**Failure mode.** Author thinks "Mental Sex = Female" means the MC must be a woman, or rejects the dynamic because the labels feel essentialist.

**Why.** The original 1990s labels — "Male / Female problem-solving" — read in modern context as either tied to gender or as a relic to be discarded.

**Why it matters.** The cognitive distinction (cause-and-effect chains vs relating multiple things) is real and gender-independent. Discarding the dynamic loses a useful structural distinction.

**Fix.** Use Linear / Holistic as working terms. Note the original labels once for collaborators who may know them. The MC's gender has nothing to do with the dynamic.

---

## AP-9: Inconsistent Story Driver across acts

**Failure mode.** Inciting incident is an action that forces decisions (looks like Action Driver), but the second-act break is a decision that triggers actions (looks like Decision Driver).

**Why.** Drafts develop organically; the act transitions emerge separately and aren't always pulled by the same dynamic.

**Why it matters.** Story Driver is one of the dynamics that holds the plot's *rhythm*. If it's inconsistent, the plot feels arrhythmic — readers can't predict the type of beat coming, which reads as "off" without them being able to name why.

**Fix.** Pick which Driver the story actually wants (usually the inciting incident sets the answer). Revise the other transitions to match. If you genuinely can't, the storyform may not be a Grand Argument Story — it may be a vignette or a Tale.

---

## AP-10: Genre as marketing label

**Failure mode.** Storyform's Genre field reads "thriller" or "literary fiction" or "romance" — the bookshop label.

**Why.** "Genre" in everyday usage means category-of-thing-on-the-shelf.

**Why it matters.** Dramatica's Genre is a Mode of Expression — a structural choice about how the storyform is filtered into delivery. The bookshop label doesn't carry that information.

**Fix.** If you don't know Dramatica's Genre Modes, leave the field blank. It's optional. Better empty than misfilled. See `references/05-plot-genre.md`.

---

## AP-11: Storyform locked too early

**Failure mode.** Author writes out the entire storyform before drafting a single scene, treating it as a complete plan.

**Why.** Dramatica looks like a plotting framework; authors who like outlining are tempted to lock the structure first.

**Why it matters.** The storyform's job is to enforce *internal consistency*; it doesn't tell you whether the story is *interesting*. A storyform-first draft can be technically valid and emotionally inert.

**Fix.** Do enough storyforming to know the throughlines, the Class assignments, and the major dynamics. Draft scenes from there. Let encoding inform the storyform — if Variations and Elements don't feel right under the pen, change them. Lock the storyform fully only when you've drafted enough to know what the story actually wants to be.

---

## AP-12: Storyform applied retroactively to an existing draft, then ignored

**Failure mode.** Author has a finished draft, runs it through the storyform exercise, finds contradictions, then "the draft is what it is" and the storyform analysis goes in a drawer.

**Why.** The retroactive analysis feels academic once the prose exists.

**Why it matters.** The point of running the exercise on a finished draft is to *find the structural problems* — the contradictions are the diagnostic output. Ignoring them means accepting that those contradictions are in the draft.

**Fix.** When the storyform exercise surfaces a contradiction, decide: (a) is this draft a Grand Argument Story or actually a Tale/vignette? If Tale, Dramatica doesn't fully apply, fine. (b) If Grand Argument, the contradictions are revision targets — *which* hard-rule violation does the revision address, and *what scenes* change?

---

## AP-13: Treating Dramatica vocabulary as universal

**Failure mode.** Translating Dramatica terms ("Throughline", "Crucial Element", "Storyform") onto other story frameworks (Save the Cat, Hero's Journey, Story Grid) as if they're equivalent.

**Why.** They're all story-structure frameworks; surface-level mapping looks plausible.

**Why it matters.** The mappings aren't clean. Dramatica's "MC" is not Save the Cat's "Hero". Dramatica's "Story Goal" is not Truby's "Want". Forcing equivalence corrupts both frameworks.

**Fix.** Use one framework at a time within a project. If you're doing Dramatica, do Dramatica. If you want another framework's perspective, do it as a separate pass with that framework's vocabulary intact. Don't run a hybrid.

---

## AP-14: IC defined only as "MC's foil"

**Failure mode.** IC has no independent throughline — they exist only in MC scenes, only as a counterweight, with no own concern/issue/problem.

**Why.** IC's structural job *is* to challenge MC's worldview, so authors stop there.

**Why it matters.** The IC throughline gets one of the four Classes and four Signposts — they have a story arc of their own that runs parallel to the others. If the IC has no independent presence, the IC throughline isn't earning its slot.

**Fix.** Sketch the IC's own arc independently of MC. Where do they start, what do they pursue (in their throughline's Class terms), how do they progress through their four Signposts? Then check: do those scenes actually exist in the draft, or do you only see the IC when MC is there?
