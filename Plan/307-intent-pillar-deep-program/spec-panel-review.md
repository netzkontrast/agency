<!-- doc-source: Plan/307-intent-pillar-deep-program/spec.md -->
# Spec Panel Review — Intent-pillar Deep Program (Spec 307 + children 308–325)

> Multi-expert specification critique run via the `sc:sc-spec-panel` discipline,
> critique mode, focus: requirements · architecture · testing · consistency.
> Reviewed: the master (307) in full; children 308, 309, 310, 312, 322, 323, 324,
> 325 in full; 311, 313, 314, 315, 316, 317, 318, 319, 320, 321 skimmed.
> **This panel does NOT rubber-stamp.** The corpus is unusually disciplined — but
> it has real blockers, several unfalsifiable acceptances, and one structural
> ambiguity (the AskUser harness contract) that is load-bearing for nine specs and
> specified nowhere.

---

## 0. Headline verdict (full synthesis at §7)

**Buildable after fixing 4 blockers.** The architecture is coherent, the verb
surface is genuinely locked, and the rule-8 discipline is the best this reviewer
has seen in this repo. But: (a) the **AskUser harness contract** — the single seam
on which 309/310/311/318/323 depend — is named in a *reference doc that does not
yet exist* (`references/askuser-contract.md`) and never specified as a testable
interface; (b) the **dependency graph has a declared cycle** (310↔309, 312↔313);
(c) several **clarity-gate and replay invariants are circular or unfalsifiable**;
(d) **`examine` vs `clarify` vs `frame`** have overlapping write-targets that the
coherence rules don't disambiguate.

---

## 1. Per-expert findings

### Karl Wiegers — Requirements clarity / testability lens

**W-1 (BLOCKER). The AskUser harness contract is the program's keystone and it is
unspecified.** Master §"thesis" engine 2 and 310 both lean entirely on "the
*harness* renders the `AskUserQuestion` payload; the caller folds the verbatim
answer back." But *who is the caller*? *What is the fold-back protocol*? 309 step 4
says "the caller folds the verbatim answer back into the next loop turn" — yet
`interview` is itself a single verb invocation. A verb cannot block mid-execution
to await a user answer and then resume its own loop unless the harness re-enters
it. **The control-flow model (single blocking call vs. continuation/resume vs.
N round-trips) is never pinned.** This is a requirement, not an implementation
detail: it changes the signature of `interview`, `clarify`, and `scope`, and it is
the contract `references/askuser-contract.md` is supposed to hold — but that file
is listed as scaffolding (308), not authored, and no child's Tests section
validates it. *How would you validate compliance in production?* Today you can't.

**W-2 (MAJOR). "draft Intent grounded in a recorded, adaptive interview" (309
Acceptance) is partly aspirational.** `interview` produces a draft Intent BEFORE
`ground` (312) runs (per the flow: `interview → [draft] → ground`). So the
interview's own acceptance saying "grounded" overstates — grounding is a later
phase. Tighten 309's Acceptance to claim *adaptive + recorded*, not *grounded*.

**W-3 (MINOR). `max_beats: int = 6` (309) is a magic number wearing a budget
costume.** CLAUDE.md #8 permits tunable budgets *with a rationale*. 309 gives
none for "6". Either cite the rationale (262's 4-beat + 2 follow-ups?) or make it
config like 310's `MIN/MAX_OPTIONS`.

### Gojko Adzic — Specification-by-example / BDD lens

**A-1 (MAJOR). Almost no Given/When/Then examples across 19 specs.** The repo's
own doctrine (CLAUDE.md rule 7) is that *Gherkin acceptance scenarios are the
contract*. Ironically, 317 (`acceptance`) is the spec that *derives* Gherkin —
yet not one spec in the corpus states its own acceptance as a concrete worked
example (seed → questions asked → answers → resulting Intent node). The Tests
sections describe invariants abstractly ("the beat-2 question is a function of the
beat-1 answer") but give **no concrete fixture pair**. *Can you provide a concrete
example demonstrating this in a real scenario?* Add one worked golden trace per
guided-exploration child (309/310/311) — a seed, the literal beats, the literal
draft Intent — so the deterministic fallback has an executable target.

**A-2 (MAJOR). The "derive-not-invent" runtime check (310) is asserted but its
oracle is undefined.** 310 Tests: "every option's `description` is traceable to a
token/signal present in `context`." *Traceable how?* Substring? Token overlap
above a threshold? Embedding similarity? This is the program's hardest contract
(rule 2) and its falsifiability hinges entirely on the unstated overlap predicate.
A stop-word-laden description will pass a naive substring test trivially (every
description contains "the"). Specify the predicate as an example: given context
`"uses FastMCP"`, option `"Wrap as MCP tool"` passes, option `"Use gRPC"` is
rejected — and name the function.

### Alistair Cockburn — Use-case / actor / altitude lens

**C-1 (MAJOR). Who is the primary actor, and is it ever a human?** The master
says "the user stays creative; the engine captures everything" — but every verb is
invoked by an *agent*, and the *human* only appears at the AskUser render. The use
case "user discovers their own intent" is never written at sea level. Critically:
**what happens when the human declines to answer, gives a free-text non-answer, or
abandons mid-interview?** No child handles the abandoned-session / partial-answer
case. `interview` terminates on "complete" or "max_beats" — there is no
`terminated_by="abandoned"`. This is the most common real-world path and it's a gap.

**C-2 (MINOR). Altitude split is mostly right but `discover.discover` (323) +
`discover.interview` (309) both claim the `interview` cluster and both "open a
DiscoverySession."** Two verbs minting the same root node from the same cluster
invites a double-session bug. Specify: `discover.discover` recalls-or-opens;
`interview` only opens when called standalone. State the precedence.

### Martin Fowler — Architecture / interface-design lens

**F-1 (BLOCKER). Declared dependency cycles.** 309 `depends_on: [...310]` and 310
"build immediately after 308 and **before 309**" — fine, 309→310 is acyclic. BUT
312 `depends_on: [...313]` while 313 `depends_on: [...312]` (313 extends research
selection that 312 invokes; 312 needs 313's scout profile). The specs paper over
this ("312 degrades gracefully if 313 lands later") but the `depends_on` arrays
encode a literal cycle a topological build-order tool will choke on. Break it:
make 312 depend on 044 only, and 313 depend on 312 — the scout profile is an
*enrichment* 312 reads via a registry lookup, not a build-time dependency.

**F-2 (MAJOR). `clarify` (311), `frame` (315), and `examine` (316) all mutate the
draft Intent's `{purpose, deliverable, acceptance}` with no last-writer-wins or
ordering contract.** Coherence rule 3 lists `clarify` as a writer and `frame` as
*transform* (read-only) — but 315's Why says `frame` "returns a structured,
sharper `{purpose, deliverable, acceptance}` draft **for the caller to amend**."
So `frame` is read-only but emits a mutation the caller applies; `clarify` mutates
directly. Two different mutation models for the same three fields. Under the
bi-temporal substrate this is *probably* keep-both-safe, but the spec never says
so. Define one mutation protocol for the Intent triple and make every sharpening
verb use it.

**F-3 (MINOR). The `OntologyExtension` "set equals the Spec 307 table" test (308)
parses the table out of this markdown spec as a fixture.** That couples a code
test to prose formatting in a `.md` file — fragile, and it inverts the
source-of-truth (code should own the ontology; the table should be generated FROM
it, like `gen-capability-docs`). Recommend the test assert the live ontology is a
superset of a small *hand-listed* canonical set in the test, and a doc-drift check
keep the table honest — don't parse the spec.

### Lisa Crispin / Janet Gregory — Testing / quality-attribute lens

**Q-1 (BLOCKER). 325's "completeness — the moat invariant" is circular and
therefore unfalsifiable as written.** It asserts `replay`'s collected edge set
EQUALS the union of edges siblings recorded — *computed by walking those same
edges*. If a sibling silently fails to record an edge, replay walks nothing for
it, the graph has nothing, and `set == set` (∅ == ∅) **passes green**. The test as
specified cannot detect the exact failure it claims to guard ("a sibling recorded
but replay didn't traverse" is caught; "a sibling *didn't* record" is NOT). The
real moat test must drive a known `discover.discover` walk that performs N known
step-kinds and assert replay surfaces exactly those N — which 325's *fourth* test
("round-trips a real discovery") does correctly. **Delete or rewrite the first
test; promote the fourth to the headline invariant.**

**Q-2 (MAJOR). 322's clarity-gate "monotonicity" is the right invariant but the
score's *upper anchor* is undefined.** "Resolving a signal never lowers the score"
is testable. But `ready = score >= threshold` with five equally-weighted signals
and an unstated normalization: is full-score 1.0 or 5? Is threshold expressed in
the same units? 323's gate reads it as `clarity >= threshold`. Pin the score range
(`0.0–1.0`, sum/5) so the threshold budget is interpretable.

**Q-3 (MAJOR). "Adaptivity (not a fixed 4)" test (309) is weaker than it reads.**
It asserts beat-2 differs when beat-1's answer differs — but the *deterministic
fallback* "walks the beat library in enum order and fills the template from prior
answers." If the template is `"You said {answer}; what about X?"`, beat-2 text
trivially differs because the answer is interpolated, **even though the question
SELECTION is identical (fixed order)**. The test passes while the system is still
a fixed script with mail-merge. Strengthen: assert the *selected `kind`* (not just
rendered text) diverges for divergent answer paths.

### Sam Newman / Michael Nygard — Distributed-systems / failure-mode lens

**N-1 (MAJOR). The research dispatch (312) has no failure/timeout/cost contract.**
`ground` dispatches lead → fan-out → verify — a multi-agent, potentially
long-running, potentially failing pipeline — inside a single `discover.ground`
call. *What happens when a specialist times out? when the verifier errors? when
`depth=deep` blows the budget?* 312 handles only `UNKNOWN_INTENT`. No partial-
grounding semantics, no timeout, no "research returned zero citations" path
(which collapses the whole "narrows the option space" premise for 311). Add a
degraded-grounding return and a budget ceiling.

**N-2 (MINOR). `watch_intent` (321) rides the session-start/event hook (Spec 076)
— a documented seam — but drift-detection has no debounce/false-positive
contract.** Every utterance "drifting from active intent" triggering a capture
recommendation will be noisy. Specify the threshold and the suppression window.

---

## 2. Completeness & testability of Done-When / invariants

| Spec | Invariant claimed | Verdict |
|---|---|---|
| 308 | ontology set-equality vs. spec table | **Testable but fragile** (F-3: parses prose) |
| 309 | turn-count == beats; adaptivity | turn-count ✓; adaptivity **weak** (Q-3) |
| 310 | 2≤options≤4; recommended-first; derive-not-invent | first two ✓; derive-not-invent **oracle undefined** (A-2) |
| 312 | grounds == verified citations; depth==planner | ✓ genuinely invariant + computed |
| 322 | monotonicity; computed-not-frozen | monotonicity ✓; **score range undefined** (Q-2) |
| 323 | one-phase-per-step; gate blocks decide | ✓ strong; gate test is real teeth |
| 325 | completeness (edge-set equality) | **circular/unfalsifiable** (Q-1) — but test #4 is sound |

**Genuinely-invariant honour roll:** 312 (depth maps to the *live* planner, not a
frozen list), 322 (monotonicity), 323 (phase verbs resolve against the live
registry so a rename reds the test). These are exemplary rule-8 work.

**Hidden-snapshot watch-list:** 310's `MAX_HEADER_LEN`/`MIN_OPTIONS`/`MAX_OPTIONS`
and 309's `max_beats=6` are budgets — acceptable per rule 8 *if* documented with
rationale (309 isn't; fix W-3). None are disguised snapshots — good.

**Unfalsifiable acceptances:** 325 test #1 (Q-1, circular); 310 derive-not-invent
(A-2, no oracle); 309 "grounded" (W-2, premature). The AskUser-contract acceptance
(W-1) is *absent*, which is worse than unfalsifiable.

---

## 3. Consistency across the 19

**Locked-surface integrity: strong.** No child redefines a node name or verb
signature; every child cites the master's table. `Citation`-reuse (no
redefinition) is asserted in 308 AND 312 — good redundancy.

**Contradictions / frictions found:**

1. **Role mismatch — `frame` (315).** Master verb table marks `frame` as
   `transform` (read-only) and coherence rule 3 lists it read-only. But 315 emits a
   sharper `{purpose, deliverable, acceptance}` "for the caller to amend" — i.e. it
   drives a mutation. Either it's read-only (then who writes, and is that edge
   recorded?) or it's a writer. Pick one. (See F-2.)
2. **Dependency cycle 312↔313** (F-1) — `depends_on` arrays literally encode it.
3. **Double-session risk 309 vs 323** (C-2) — both open a `DiscoverySession` in the
   `interview` cluster.
4. **`acceptance` ordering disagreement.** Master flow shows `scope → acceptance`
   AND `examine → ... → acceptance`; 317 Why says "right after `scope` (318) and
   `examine` (316)"; but 323's phase 6 runs `scope` and `acceptance` *in the same
   phase* (`verbs: ["scope", "acceptance"]`). Same-phase vs. sequential is a real
   semantic difference (can acceptance read the scope boundaries written in the same
   phase?). Reconcile the flow diagram with the phase graph.
5. **Overlap clarify vs examine vs frame** — three "sharpen the WHY" verbs whose
   write-targets overlap on the Intent triple with no disambiguation rule (F-2).

**Dependency-ordering:** otherwise clean. 322 `depends_on` 311/312/317/318 (reads
their signals) is correct. 325 landing last is correct. 323 depending on nearly all
phase verbs is correct and honestly flagged.

---

## 4. Ambiguity & gaps (the underspecified seams)

| Seam | Where | Gap |
|---|---|---|
| **AskUser harness contract** | 310/309/311/318/323 | Control-flow model (blocking vs resume vs N round-trips), fold-back protocol, the `askuser-contract.md` doc unwritten. **The keystone gap.** (W-1) |
| **Driver fallback** | 309/310/311 | "Deterministic fallback walks the beat library / extracts options from structured signals" — but the *structure* the fallback parses (what shape is `context`?) is never typed. The fallback is the *only* tested path; its input contract must be concrete. |
| **Research dispatch failure** | 312 | No timeout/partial/zero-citation/budget path (N-1). |
| **Abandoned / non-answer user** | 309/311/318 | No `abandoned` termination, no free-text-answer handling (C-1). |
| **Clarity-gate threshold semantics** | 322/323 | Score range + threshold units undefined (Q-2); weighting "open question" deferred to build — acceptable, but the *range* must be pinned now. |
| **`already_exists` confidence floor** | 312 | Honestly flagged as a build-time open question — acceptable. |
| **Override-token shape** | 322 | "explicit override token" recorded as a Gate result — the token's provenance/auth (who may override?) unspecified. Minor but security-adjacent. |

---

## 5. Scope / altitude / over-engineering

**Is 19 specs right-sized?** Mostly yes — but two consolidations and one split
are warranted:

- **MERGE candidate: 312 + 313 + 314 → one "research-grounding" spec, or at least
  fold 313 into 312.** 313 "adds NO new top-level verb"; it's a specialist-set
  extension that only 312 consumes. Three specs for one dispatch + its scouts + its
  verdict is fine-grained to the point of the cycle in F-1. At minimum, 313 should
  be a *section* of 312, not a sibling — it has no independent verb surface and no
  independent acceptance an agent can run.
- **MERGE candidate: 310 into 309?** No — keep separate. 310 is correctly a
  primitive composed by three callers; centralizing the well-formed-question rules
  once is exactly right (DRY). This is the corpus's best factoring.
- **SPLIT candidate: none.** No spec is too big.

**Over-engineering / gold-plating flags:**

- **`decompose_intent` (319) MECE discipline** may be gold-plating for v1. "Split
  into an exhaustive-and-disjoint sub-intent tree with provenance of *why* the split
  is MECE" is a lot of machinery before there's evidence agents need it during
  *discovery* (vs. during planning). Consider deferring 319 to a fast-follow; it's
  the least load-bearing for the "shallow intent" gap the program exists to close.
- **`replay` render-to-Document (325) + `state` render-to-Document (324)** — two
  projections of one Document is elegant but doubles the Document surface before
  either is dogfooded. Ship the graph-return first (both specs say Slice 1 does
  this — good), defer both renders to Slice 2 as written.
- **Seven-phase discipline (323)** is at the upper bound of what an agent will walk
  before fatigue. `frame`+`examine` (phases 4-5) are the two most skippable; the
  "open question: swap frame/examine" already hints they're soft. Consider making
  phases 4-5 *optional* (gated on clarity already being high after grounding),
  rather than mandatory beats — otherwise a sharp 3-beat intent still pays 7 phases.

**Altitude of the master:** excellent. The coverage matrix and locked verb/ontology
tables are exactly the right altitude for a program master and genuinely let a
reviewer answer the §Acceptance questions without opening a child.

---

## 6. Prioritized, actionable recommendations

| # | Severity | Spec · Section | Concrete edit | Fix-before-build? |
|---|---|---|---|---|
| R1 | **BLOCKER** | 310 §Design + 308 `references/askuser-contract.md` | Author the AskUser harness contract as a *testable interface*: define the control-flow model (recommend: `ask`/`interview` return a payload + the harness re-invokes with the answer — a resume model), the fold-back signature, and one worked round-trip example. Add a Tests bullet that exercises it with a stub harness. | **YES** |
| R2 | **BLOCKER** | 325 §Tests (test #1) | Delete the circular "edge-set equality" test; promote test #4 ("round-trips a real `discover.discover` walk, kind-set equals walked step-kinds") to the headline moat invariant. Add a *negative* case: a walk that skips grounding ⇒ replay's kind-set excludes `ground`. | **YES** |
| R3 | **BLOCKER** | 312 + 313 `depends_on` | Break the cycle: 312 `depends_on` 044 only; 313 `depends_on` 312. Make the scout profile a runtime registry lookup, not a build dep. | **YES** |
| R4 | **BLOCKER** | 310 §Tests (derive-not-invent) | Name the traceability oracle (token-overlap predicate + threshold, stop-words excluded) and give a pass/reject example pair. | **YES** |
| R5 | **MAJOR** | 315 §verb role vs master rule 3 | Resolve `frame`'s read-only-vs-writer contradiction; define ONE mutation protocol for the Intent `{purpose,deliverable,acceptance}` triple shared by `clarify`/`frame`/`examine` (last-writer-wins under keep-both, edge recorded). | YES |
| R6 | **MAJOR** | 322 §Design | Pin the clarity score range (`0.0–1.0`, mean of 5 signals) and threshold units so 323's gate comparison is interpretable. | YES |
| R7 | **MAJOR** | 309 §Tests (adaptivity) | Strengthen: assert the selected `turn_kind` (not just rendered text) diverges across divergent answer paths — otherwise mail-merge passes. | YES |
| R8 | **MAJOR** | 312 §Design | Add research-dispatch failure semantics: timeout, partial-grounding return, zero-citation path, `depth=deep` budget ceiling. | YES |
| R9 | **MAJOR** | 309/311/318 termination | Add `terminated_by="abandoned"` + free-text/non-answer handling for the human-declines path. | YES |
| R10 | **MAJOR** | 323 phase 6 vs master flow | Reconcile scope+acceptance same-phase (323) vs. sequential (flow diagram); state whether `acceptance` reads same-phase scope boundaries. | YES |
| R11 | MINOR | 313 (whole) | Fold 313 into 312 as a §section (no independent verb/acceptance); reduces 19→18 and removes the cycle's root cause. | Nice-to-have |
| R12 | MINOR | 308 §Tests (ontology set) | Don't parse the spec markdown; assert live-ontology ⊇ a small canonical set in-test + lean on doc-drift for the table. | Nice-to-have |
| R13 | MINOR | 309 §Design | Give `max_beats=6` a documented rationale or make it config (rule 8). | Nice-to-have |
| R14 | MINOR | 319 (whole) | Consider deferring to a fast-follow; least load-bearing for the shallow-intent gap. | Nice-to-have |
| R15 | MINOR | 323 phases 4-5 | Make `frame`/`examine` clarity-gated optional beats so a sharp intent isn't forced through 7 phases. | Nice-to-have |
| R16 | MINOR | every child §Acceptance | Add one concrete worked trace (seed → literal questions → literal Intent node) per guided-exploration child — the repo's own Gherkin doctrine (A-1). | Nice-to-have |
| R17 | MINOR | 322 override token | Specify the override token's shape + who may issue it (auth/provenance). | Nice-to-have |

---

## 7. Synthesized verdict

**Is the corpus ready to build? Not yet — but it is close, and the gaps are
sharply localized.** This is a strong, internally-coherent program. The master
genuinely locks its surface; the children genuinely cite it; the rule-8 discipline
is real (312, 322, 323 are model invariant-design). The "drop-in capability" bar is
respected — only 321 and 324 touch documented seams, exactly as the master claims.

But a panel that found nothing would be a failed panel, and this one found **four
blockers that must close before the first build slice**:

1. **Specify the AskUser harness contract (R1).** It is the keystone of nine specs
   and currently exists only as an unwritten reference doc. Until the control-flow
   and fold-back protocol are a *testable interface*, 309/310/311/318/323 are
   building against a hole.
2. **Fix the replay moat test (R2).** The program's self-declared whole-provenance
   acceptance gate is, as written, circular and passes on the empty graph — it
   cannot catch the failure it exists to catch.
3. **Break the 312↔313 dependency cycle (R3)** — a literal cycle in `depends_on`.
4. **Define the derive-not-invent oracle (R4)** — the corpus's hardest contract
   has no testable predicate.

The next three highest-leverage changes (majors): **R5** (unify the Intent-triple
mutation protocol across clarify/frame/examine), **R8** (research-dispatch failure
semantics), and **R9** (the abandoned/non-answer human path — the most common
real-world flow, currently unhandled).

Close R1–R4 and the corpus is build-ready for the stated slice order
(308 → 310 → 309 → 312). Close R5–R10 within the first two slices. Treat R11/R14
(fold 313, defer 319) as scope-tightening that would take the program from 19 to a
leaner, equally-complete 17 — a net win.

*Panel: Wiegers (requirements), Adzic (BDD), Cockburn (use-case/altitude), Fowler
(architecture), Crispin/Gregory (testing), Newman/Nygard (failure-modes).*
