<!-- doc-source: Plan/draft/307-intent-pillar-deep-program/spec.md -->
# Business Panel Review — Spec 307 Intent-Pillar Deep Program

> **Mode:** Socratic + Debate. Nine experts convened to evaluate the **strategic
> value** of the 19-spec `discover` corpus (307–325): guided intent discovery
> turning a one-sentence seed into a grounded, clarity-gated, confirmed Intent
> via research agents + AskUser chains.
>
> **The motivating directive under review:** *"The capability pillar is nearly
> complete — but the intent is shallow."*
>
> A panel that only praises is useless. This one is instructed to challenge.

---

## 1. Per-Expert Assessment

### Christensen — Jobs-to-be-Done / Disruption

**Verdict: CONDITIONAL GO — the job is real, but you have two candidate jobs and have not separated them.**

> *"What job does a user — or an agent — hire 'guided discovery' for?"*

There are two jobs here, and the corpus conflates them:

- **Job A (the human's job):** *"Help me figure out what I actually want before I commit work to it."* This is a genuine, under-served job — the JTBD literature's classic "I don't know what I don't know." Non-consumption is real: today the user types a sentence and the system runs. Nobody is currently doing the WHY-sharpening.
- **Job B (the graph's job):** *"Give the provenance moat a richer root node to hang SERVES edges from."* This is an **internal** job, hired by the architecture, not the customer.

The danger: Spec 307's "Why" is written almost entirely in Job B language — *"the provenance moat records what was done against an intent that was never sharpened."* That is the architect's pain, not the user's. **Is the innovation sustaining or disruptive?** It is *sustaining* — it makes an existing product (the agency engine) better along a dimension the existing owner already values (provenance depth). Sustaining innovation is fine, but it must be justified by customer value, not internal elegance.

**My probe:** *Strip every word about the moat. Is there still a user who would pay for guided discovery? If yes — name them, and the spec's Why should lead with them. If no — this is gold-plating Job B and calling it Job A.*

---

### Porter — Competitive Strategy / The Moat

**Verdict: GO — this is the rare durable differentiator, IF the provenance is the product and not a side-effect.**

> *"Is the provenance moat durable differentiation versus an SDK-native rival?"*

Five Forces lens. The threat is **substitutes**: any team can wire `AskUserQuestion` + a research loop in an afternoon with the raw Agent SDK. So clarification-as-a-feature is *not* defensible — it's table stakes within a quarter.

What IS defensible is the **bi-temporal, replayable provenance graph** (Spec 325). A rival can replicate the *interaction* (ask sharp questions); they cannot cheaply replicate the *accumulated, queryable history of how every intent in a project was discovered* without having built the same substrate from day one. That is a **switching cost** and a **value-chain integration** advantage: discovery feeds the same graph that capability, lifecycle, and memory feed. The moat is the *integration*, not the interview.

**The strategic error to avoid:** if `discover` ships as a bolt-on interview wizard whose provenance is an afterthought, you have built the commoditizable part and skipped the defensible part. Spec 325 must not be the *last* child — it is the **thesis**, and it should gate the others.

**My probe:** *What is the sustainable competitive advantage — the interview, or the replay? If you halved the budget tomorrow, which half do you cut? The answer reveals whether you actually believe your own moat.*

---

### Drucker — Management / Right Problem

**Verdict: REFINE — you may be solving the right problem for the wrong customer, efficiently.**

> *"Who is the customer? What does the customer value?"*

The most uncomfortable question on the panel, so I will ask it plainly: **What is your business? An agentic substrate, or a provenance research project?** The directive — *"the intent is shallow"* — is an **inside-out** statement. It describes an asymmetry the owner noticed between two pillars (Capability is rich, Intent is thin) and seeks to **balance the architecture**. Symmetry is an aesthetic value, not a customer value.

> *"There is nothing so useless as doing efficiently that which should not be done at all."*

Nineteen specs is a great deal of efficiency aimed at a problem whose customer demand is **asserted, not evidenced**. The spec says an Intent is "born shallow" — but no user reflection, no dogfooding `Reflection` node, no support ticket is cited showing that shallow intents *caused a failure the user felt*. The CLAUDE.md doctrine demands "evidence + doctrine." This spec has doctrine in abundance and **evidence almost entirely absent** — the one citation is the owner's own directive.

**My probe:** *Show me one concrete instance where a shallow intent produced a bad outcome a real user noticed. One. If you cannot, you are gold-plating the pillar to match its sibling, and the right scope is 3 specs, not 19.*

---

### Godin — Remarkable / Tribe

**Verdict: REFINE — grounded intent is valuable but invisible; nobody talks about plumbing.**

> *"Is a discovered, grounded intent remarkable — worth talking about?"*

Be honest: **no user has ever told a friend about a clarification dialog.** Guided discovery is *felt* as friction in the moment and *appreciated* only in retrospect, if ever. That is the opposite of remarkable — it is invisible infrastructure.

BUT — there is a Purple Cow hiding here, and the corpus buries it. **`replay` (325) is the remarkable thing.** "Show me exactly *how* this project's goal was discovered — every question, every piece of evidence, every time we changed our minds" — *that* is a demo that makes people lean in. It is a story. The interview is the cost; the replay is the campaign.

**The adoption risk Godin sees that the engineers miss:** forcing guided discovery in front of every intent is **interruption marketing** — you are interrupting the user's flow to ask questions they didn't request. Permission must be earned. Make discovery **opt-in and remarkable** (`/discover` when I'm stuck), not **mandatory and resented** (a gate before every `intent_bootstrap`).

**My probe:** *Who would miss `discover` if it vanished? If the answer is "the graph," it's not remarkable. If the answer is "the user who was stuck on a vague goal," then build for THAT moment and make it spreadable.*

---

### Kim & Mauborgne — Blue Ocean

**Verdict: GO with a CANVAS WARNING — value innovation is real, but watch which axis you compete on.**

> *"Does this create uncontested space, or compete on a crowded axis?"*

Apply the Four Actions (ERRC) to the agentic-tooling strategy canvas:

- **Eliminate:** the parallel tracking system (there is none — the graph is the moat). Good.
- **Reduce:** the cost of a wrong WHY discovered late.
- **Raise:** intent *clarity at birth* — a factor no competing agent framework optimizes.
- **Create:** **replayable discovery provenance** — genuinely uncontested space. No SDK ships "reconstruct how the goal was discovered."

So the value-innovation thesis (differentiation + the substrate already exists, so low marginal cost) holds. **The red-ocean trap:** "better questions / smarter clarification" is a **red ocean** — every assistant competes there and it's a feature arms race. If `discover` is sold as "we ask better questions," you have swum into the bloodiest water in the category. If it's sold as "your intents are grounded *and the grounding is permanent and queryable*," that's blue.

**My probe:** *Plot your strategy canvas. If your highest curve is "quality of clarification questions," you are in the red ocean. The blue-ocean curve is "discovery is a durable, replayable graph asset." Lead with the latter.*

---

### Collins — Hedgehog / Flywheel

**Verdict: GO — this is a true flywheel push, the strongest strategic argument in the room.**

> *"Does discovery feed the provenance flywheel?"*

This is where the investment is most defensible. The hedgehog intersection:
- **Passion / purpose:** the human-owned root that everything edges back to (CORE.md).
- **Best at:** provenance — one bi-temporal graph, no parallel system (Goal 2).
- **Economic engine:** every recorded edge compounds the moat's value.

Discovery doesn't just *use* the flywheel — it **feeds the highest-value part of it**. A richer root means every downstream SERVES edge inherits clarity instead of vagueness. Sharper intent → better grounding → richer provenance → more reuse → more reason to capture intent well. That flywheel turns.

**The discipline warning (brutal facts):** Good-to-Great companies confront the brutal facts. The brutal fact here is **scope**. Great flywheels are built by *consistent, small pushes*, not a single 19-spec heave. Nineteen specs authored in one commit is a **Big Hairy Plan**, not a flywheel turn. The risk is that you build the flywheel's housing perfectly and never get it spinning because momentum died in the build.

**My probe:** *What is the smallest push that makes the flywheel measurably turn — one discovery, replayed, that demonstrably improved one downstream outcome? Build THAT, ship it, feel the momentum, then add spokes.*

---

### Taleb — Antifragility / Risk

**Verdict: DESCOPE HARD — 19 specs of upfront design is the textbook fragility you claim to avoid.**

> *"Over-engineering fragility? What's the downside of 19 specs of upfront scope?"*

I am the dissent. This corpus is **fragile pretending to be robust.**

**Via negativa:** the strongest move is almost always *removal*. You are *adding* — a capability, 16 verbs, 7 node types, 7 edges, 4 enums, 6 schemas — all designed **before a single line runs** and before one real user has hit the problem. The spec even admits it: *"No code yet — this is the design layer."* Nineteen interlocking specs, each depending on the others (309 needs 310; 312 needs 313; 325 needs all 14), is a **tightly-coupled chain**. Tight coupling is the signature of fragility: a wrong assumption in 307's ontology propagates into 18 children that all cite it. You have maximized the blast radius of being wrong about the WHY of WHY-discovery.

**Where is the optionality?** Antifragile design buys cheap options and lets the winners run. The antifragile version of this program is: ship `discover.interview` + `discover.replay` as **two** specs, expose them, and let *usage* (volatility, real users) tell you which of the other 17 verbs deserve to exist. Instead you've front-loaded the conviction. **The hidden tail risk:** you spend the whole budget building `decompose_intent`, `frame`, `examine`, `watch_intent`, `feasibility` — and discover users only ever wanted `interview`. The downside if you're completely wrong is **18 specs of sunk design**.

**The asymmetry to exploit:** the cost of shipping 2 verbs and being wrong is small (you learn). The cost of shipping 19 and being wrong is large (you've poured concrete). **Bet small, where the upside is convex.**

**My probe:** *If this entire design is wrong about what users want, how much have you lost — and how would you even find out, given nothing ships until the whole chain is built? Design for being wrong cheaply.*

---

### Meadows — Systems Leverage

**Verdict: GO — "sharpen the WHY at the root" is a genuine high-leverage intervention point. This is Taleb's direct counter.**

> *"Is sharpening the WHY at the root a high-leverage place to intervene?"*

Yes — and this is the most important systems insight on the panel, the one that *answers* Taleb. In her leverage-point hierarchy, the **goal of the system** and the **paradigm/mindset out of which the system arises** are the two *highest* leverage points — far above parameters, buffers, or feedback delays.

The Intent IS the system's goal node. Every SERVES edge is the structure that flows from it. **Intervening at the goal is the single highest-leverage move available** — a vague root mis-aligns the entire downstream structure, and no amount of optimizing the downstream (better lifecycle, better memory) can compensate for a wrong goal. So the *target* of this investment is correct: you are intervening at the right place.

**But leverage cuts both ways** — Meadows' famous warning is that people intuit the right leverage point and then **push in the wrong direction.** Adding *friction* (mandatory gates, 16 verbs of process) at the goal-setting point could *lower* the system's responsiveness — users route around a heavy intake. The high-leverage intervention is not "more discovery machinery," it's "a sharper goal." Those are not the same. The leverage is in the *clarity*, not the *apparatus*.

**Where Meadows meets Taleb:** he is right that the *mechanism* should be lean; I am right that the *target* is the best in the system. **The synthesis: a high-leverage target deserves a low-mass intervention.** Build the lightest thing that sharpens the goal — not the heaviest.

**My probe:** *You found the highest leverage point in the system. Now: what is the lightest possible touch there? Because at high-leverage points, heavy touches produce policy resistance, not improvement.*

---

### Doumont — Communication Clarity

**Verdict: REFINE — the corpus's own message is buried under its own machinery; physician, heal thyself.**

> *"Is the corpus's own message clear? What is the core message?"*

Exquisite irony: a program whose entire purpose is **clarifying the user's WHY** has a **muddy WHY of its own.** The master spec's core message — *"a discovered intent is grounded; a shallow one is a guess"* — is sound and one sentence long. But it is surrounded by a coverage matrix, a verb table, an ontology table, an enum table, a flow diagram, and 18 cross-references. The **cognitive load is enormous**, and a reader must hold all of it to evaluate the whole.

By my own structure rule: lead with the **one message**, structure for the **audience's decision** (ship / refine / cut), and push the machinery to an appendix. The spec inverts this — machinery first, message diffused throughout.

**The deeper tell:** a clear program can be stated as *"build the smallest thing that proves a discovered intent beats a guessed one."* That it instead requires 19 documents to state suggests the *thinking* is not yet as sharp as the *goal* it serves. The medium is the message — and the message here is "comprehensive," which is precisely the value (gold-plating) the panel is worried about.

**My probe:** *State the entire program in one sentence a busy owner can act on. If it takes 19 specs to say it, the WHY of the WHY-discoverer is itself not yet discovered.*

---

## 2. Tensions & Debate (staged)

### Debate 1 — Taleb vs. Meadows: the central fight

**Taleb:** *"You've designed 19 interlocking specs before one runs. That's fragile. Via negativa — ship two, remove the rest until usage demands them."*

**Meadows:** *"You're confusing the target with the mass. The Intent is the goal node — the highest leverage point in the entire system. Intervening there is exactly right. You don't 'descope' the most important place to act."*

**Taleb:** *"I'm not arguing the target. I'm arguing the* mass *at the target. You agree heavy touches at leverage points cause policy resistance — users route around a 16-verb intake. So we agree: lean intervention, high-leverage target."*

**Meadows:** *"Then we converge. The disagreement was never target-vs-no-target. It was apparatus-vs-clarity. A high-leverage point demands the* lightest *effective touch — and 19 specs is not light."*

**Resolution (synthesis):** Both right at different levels. **Intervene at the WHY (Meadows), with minimal mass (Taleb).** The program's *target* is correct; its *scope* is not. Ship the two highest-leverage verbs, let volatility select the rest.

### Debate 2 — Drucker vs. Porter: right problem vs. real moat

**Drucker:** *"Show me the customer who feels the pain. The Why is inside-out — pillar symmetry, not user value. Without evidence, this is efficient gold-plating."*

**Porter:** *"The customer pain is downstream and invisible to them — that's exactly why it's defensible. A moat the customer doesn't consciously value but can't leave is the* best *kind. Switching costs don't require the customer to articulate them."*

**Drucker:** *"A moat around a castle no one wants to live in is a cost, not an asset. You must first prove someone wants the castle."*

**Porter:** *"Agreed that adoption must be proven. But if it IS adopted, the provenance integration is what makes it un-copyable. The sequence matters: prove the job (Drucker), then the moat compounds (Porter)."*

**Resolution:** Sequence, not conflict. **Drucker gates Porter.** Validate the job with one real user before pouring the moat's concrete; once validated, Porter's integration advantage is the reason to go deep.

### Debate 3 — Godin vs. the architecture: mandatory vs. opt-in

**Godin:** *"Forcing discovery before every intent is interruption marketing. It will be resented."*

**Collins (siding partially):** *"But the flywheel needs the data to compound — opt-in discovery means sparse provenance, a weaker moat."*

**Godin:** *"Sparse-but-loved beats comprehensive-but-resented. Earn permission; the tribe that opts in gives you richer signal than the masses you coerce."*

**Resolution:** **Opt-in, remarkable, with replay as the hook.** Let the `replay` demo pull users into wanting discovery, rather than gating them into it.

---

## 3. The Top 3 Strategic Risks

1. **Gold-plating a pillar to match its sibling (Drucker + Doumont).** The strongest evidence in the Why is the owner's aesthetic observation that Capability is rich and Intent is thin. Symmetry is not demand. **Risk: 19 specs of effort aimed at architectural balance, not a felt user failure.** Mitigation: cite one concrete failure of a shallow intent before building past the scaffold.

2. **Friction at the highest-leverage point reduces, not improves, the system (Meadows + Godin).** Mandatory guided discovery before every `intent_bootstrap` adds process exactly where the system most needs responsiveness. Users route around heavy intake. **Risk: the intervention lowers adoption of the very pillar it strengthens.** Mitigation: opt-in, lightweight, with the heavy machinery reachable but never forced.

3. **Fragile upfront scope — 18 children chained to one untested ontology (Taleb + Collins).** Nothing ships until the chain is built; a wrong assumption in 307's ontology propagates to all 18 children. **Risk: 18 specs of sunk design if the WHY-of-WHY-discovery is wrong, with no cheap way to find out.** Mitigation: vertical slice (interview → confirm → replay) ships and earns usage *before* the other 14 verbs are committed.

---

## 4. Synthesis & Recommendation

### Recommendation: **REFINE — descope to a vertical slice, then go.**

Not GO (Taleb/Drucker/Doumont's caution is decisive — 19 unproven specs is real risk). Not KILL (Meadows/Collins/Porter are right that the *target* and the *moat* are genuinely valuable). **Refine: build the smallest end-to-end proof, ship it, let usage select the rest.**

### The single highest-leverage strategic insight

> **The Intent is the goal node — the highest-leverage point in the entire system (Meadows) — and therefore deserves the lightest effective touch, not the heaviest (Taleb). The corpus has correctly identified WHERE to intervene and incorrectly concluded that the right intervention is MORE machinery. The leverage is in the clarity of the WHY, not the mass of the apparatus that produces it.**

Everything follows from this. The program's *aim* is excellent; its *scope* is the inverse of what high-leverage intervention demands.

### If budget were halved — what to build first, what to cut

**Build first (the irreducible vertical slice — ~4 specs):**
1. **308** — `discover` scaffold (the drop-in folder; the cost of admission).
2. **309** — `interview` (the one verb that does the job: adaptive AskUser → draft Intent). *This is the job-to-be-done.*
3. **322** — `clarity` gate + **confirm** (the gate that makes a discovered intent *mean* something).
4. **325** — `replay` (the moat; the remarkable thing; Porter's durable differentiator and Godin's demo, in one).

This slice proves the entire thesis: *seed → interviewed → clarity-gated → confirmed → replayable*. It is the smallest thing that demonstrates a discovered intent beats a guessed one, and it ships Porter's moat and Godin's hook on day one.

**Cut / defer until usage demands them (the other 13):**
- `ground` (312), `feasibility` (314), the research scouts (313) — *valuable but defer;* grounding is the second engine, prove the first engine first.
- `frame` (315), `examine` (316) — sharpening passes; nice-to-have once the spine works.
- `acceptance` (317), `scope` (318), `decompose_intent` (319) — structure verbs; let real intents reveal which are needed.
- `refine` (320), `watch_intent` (321) — lifecycle refinements; premature before there is discovery volume.
- `state` (324) — composes `manage`; a read-API over a feature that has barely shipped is itself gold-plating; defer.

**The sequencing principle (the whole panel's consensus):** the corpus's own dependency order (308 → 309/310 → 312) is *implementation-correct* but *strategy-wrong* — it builds the guided-exploration engines before proving anyone wants guided exploration. **Re-sequence around proof, not around architecture:** ship the thinnest replayable discovery, put it in front of one real user, and let the resulting `Reflection` nodes — the dogfood loop this very repo is built on (Goal 6) — tell you which of the remaining 13 verbs earned the right to exist.

> **Final word (Doumont's, fittingly):** the program that teaches users to sharpen their WHY should first sharpen its own. State it in one sentence — *"prove a discovered intent beats a guessed one, in four specs, then let usage write the other fifteen"* — and build that.
