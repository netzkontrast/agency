---
review_of: Plan/superseded/009-superpowers-remainder/spec.md
reviewer: spec-panel (critique mode)
panel: [Wiegers, Adzic, Cockburn, Fowler, Crispin, Nygard]
date: 2026-05-27
status: CHANGES REQUESTED
grounded_in:
  - superpowers v5.1.0 @ f2cbfbefebbfef77321e4c9abc9e949826bea9d7 (CACHE, real files read)
  - agency/capabilities/develop.py
  - skills/code-review/SKILL.md
  - tests/test_agency.py
---

# REVIEW — Spec 009 Superpowers Remainder

## Verdict

**CHANGES REQUESTED.** The spec's *intent* is sound and the EXTEND-not-add
design is the right shape, but it is built on **two factually wrong premises**
about the source, **mis-states the current `review` phase-graph**, and
**ignores a real class of runtime/supporting scripts** by scoping the audit to
`lib/`+`bin/` (which do not exist). The remainder is genuinely small, but it is
*not* the remainder the spec describes. Fix the premises and the work is ~1
session, not 2.

The good news: the verified gap is even smaller than the spec claims. After
reading every real `SKILL.md`, the **only uncovered discipline is
`receiving-code-review`** (1). Everything else is references (prose) or
already-covered.

---

## The VERIFIED coverage gap (grounded in real superpowers v5.1.0)

The cached plugin is a **single, fully-inlined plugin** — NOT an aggregator that
forwards to sub-plugins. `marketplace.json` lists exactly one plugin with
`"source": "./"` (cache `.claude-plugin/marketplace.json`), and all 14 skill
bodies live inline under `skills/*/SKILL.md`. There are **no `lib/` and no
`bin/` directories** anywhere in the tree.

Full discipline set (14 skills, real paths):

| superpowers skill (cache path `skills/<x>/SKILL.md`) | Agency target | status |
|---|---|---|
| using-superpowers | engine `search`/`get_schema`/`execute` | covered |
| writing-skills | `plugin.author_skill`+`lint_skill`, `skill_generator`, `skill-creation` | covered |
| test-driven-development | `develop.tdd` | covered |
| systematic-debugging | `develop.debug` | covered |
| verification-before-completion | `develop.verify` | covered |
| brainstorming | `develop.brainstorm` | covered |
| writing-plans | `develop.plan` | covered |
| requesting-code-review | `develop.review` (+ `delegate.fan_out`) | covered |
| **receiving-code-review** | folded into `review` resolve only | **PARTIAL → the one true gap** |
| dispatching-parallel-agents | `delegate.fan_out` | covered |
| subagent-driven-development | `subagent.develop` (`delegate`+`gate`) | covered |
| executing-plans | `develop.execute` | covered |
| using-git-worktrees | `workspace` capability | covered |
| finishing-a-development-branch | `branch` capability | covered |

**Verified uncovered disciplines: 1** (`receiving-code-review`).
Everything else is reference prose (transform, not a discipline) — see below.

### References corpus — the REAL set (the spec's list is incomplete)

The spec names 4 references. The real per-skill supporting-doc corpus in the
cache is larger. Heavy reference `.md` (prose → T3 `REFERENCES`):

- `skills/writing-skills/testing-skills-with-subagents.md` — Agency has
  `REFERENCES["testing-skills"]`; **confirm parity, keep.**
- `skills/writing-skills/persuasion-principles.md` — **absent in Agency.** (Read
  it: Cialdini 7 principles + Meincke 2025. Note the CORE tension below.)
- `skills/writing-skills/anthropic-best-practices.md` — **absent.** This is a
  ~46KB verbatim copy of Anthropic's *official* public skill-authoring guide. It
  is DISTINCT from Agency's authored `REFERENCES["best-practices"]` (Open Q4:
  resolved — distinct, but see Must-Fix #5 on copy risk).
- `skills/test-driven-development/testing-anti-patterns.md` — **absent, not in
  spec.** A real reference; should map to `REFERENCES` or be explicitly dropped.
- `skills/systematic-debugging/{root-cause-tracing,defense-in-depth,condition-based-waiting}.md`
  — **absent, not in spec.** Three substantive technique docs behind `debug`.
- `skills/using-superpowers/references/{codex,copilot,gemini}-tools.md` — host
  adapter docs; **drop (Agency-irrelevant)** — record the drop.

The spec's claim that the heavy corpus is just 4 files is **wrong**. The
`Done When` "no remaining partial/planned rows for in-scope items" cannot be
satisfied without enumerating these. **Must-fix #2.**

### Supporting *scripts* (the real "runtime-dep" question — not lib/bin)

There is no `lib/`/`bin/`, but there ARE executable per-skill scripts. These are
what the runtime-dep audit must actually classify:

| script (cache path) | what it is | classification |
|---|---|---|
| `skills/writing-skills/render-graphs.js` | renders skill graphviz → SVG | **build/dev tooling** — drop |
| `skills/systematic-debugging/find-polluter.sh` | bisects a polluting test | **technique helper** — re-express as reference prose; NOT a capability verb |
| `skills/brainstorming/scripts/{server.cjs,helper.js,start-server.sh,stop-server.sh,frame-template.html}` | a hand-rolled WebSocket "visual companion" server for brainstorming | **interactive UX tooling** — out of scope; Agency's `brainstorm` is a gated phase-graph, drop |
| `skills/systematic-debugging/condition-based-waiting-example.ts` | example code | **prose/example** — fold into the debug reference if kept |
| `scripts/{bump-version,sync-to-codex-plugin}.sh` (repo root) | release/sync tooling | **build tooling** — drop |
| `hooks/session-start` + `hooks/hooks.json` | injects `using-superpowers` into the system prompt | **the pressure mechanism Agency deliberately drops** (code-mode replaces it) — record as dropped-with-reason |

**Conclusion on runtime-deps: NONE are genuine runtime dependencies.** Every
script is build tooling, interactive UX, or example code. This *confirms the
expected outcome* — but via the real evidence, not the false "aggregator-only"
reasoning. The audit must be rewritten to classify SCRIPTS (which exist), not
`lib/`+`bin/` (which don't).

---

## Runtime-dep findings (Open Question 1 — RESOLVED)

- **No `lib/`, no `bin/`.** The spec's entire OQ1 framing ("follow
  `marketplace.json` to the sub-plugins to find the real `lib/`/`bin/`") is
  moot: the manifest sources one inline plugin (`./`), and the skill bodies are
  already inline in the cache.
- **No script is a runtime dep.** All are build/UX/example/pressure tooling
  (table above). The `Done When` line "port runtime-deps behind an existing
  capability" will have an empty body — that's correct, but the spec should say
  so as the *primary* expected outcome and record the **actual SHA**
  (`f2cbfbef…`, v5.1.0), not the stale `6be2203…` it currently freezes.

---

## Per-expert critique

**Wiegers (requirements quality).** The central acceptance criterion — "no
remaining partial/planned rows for in-scope items" — is **not testable as
written** because "in-scope items" is undefined and the reference list is
incomplete (6+ real reference docs vs the spec's 4). Make the reference set an
explicit enumerated list (the table above) so "covered or dropped-with-reason"
is checkable. The `lib/bin` audit criterion asserts a thing that does not exist;
re-state it as "classify the per-skill scripts in the table."

**Adzic (specification by example).** No Given/When/Then for the new `triage`
phase. The genuinely load-bearing behavior of `receiving-code-review` is
*pushback* and *clarify-before-implement* — yet `Done When` only asserts
"`triage` precedes `resolve`". Add concrete examples the test must encode, e.g.
*Given a finding the agent believes is wrong, When triaged, Then it is
classified `disagree-with-reason` and `resolve` records the reasoning, not a
silent compliance.* The receiving-review skill's whole point (cache
`skills/receiving-code-review/SKILL.md:113-129`, "When To Push Back") is lost if
`triage` only tags findings without forcing the verify/pushback path.

**Cockburn (use cases / actors).** Two distinct actors are conflated. In
superpowers these are **two separate skills** with different triggers:
`requesting-code-review` (actor: author seeking review) and
`receiving-code-review` (actor: implementer processing feedback — incl. feedback
from a *human*, not just a dispatched subagent). Folding both into one
`develop.review` walk forces a single linear graph `request→dispatch→triage→
resolve`, which is wrong for the receiving-only case (you receive feedback you
did NOT request — there is no `request`/`dispatch` to walk). **Open Question 2
is under-resolved; see Must-Fix #3.**

**Fowler (interface/design).** The spec says the current `review` graph is
`request → dispatch → resolve` — and `develop.py:65-71` confirms that. BUT the
*installed* `skills/code-review/SKILL.md:18` describes `request → assess →
resolve` (an `assess`, not `dispatch`, phase). **The capability and its shipped
skill are already out of sync.** Any edit here must reconcile the two, or
`Done When`'s "the installable skill matches the schema" silently fails. The
spec doesn't notice this drift. **Must-fix #4.**

**Crispin (testing).** The two new test files do not yet exist — there is no
`tests/test_develop_capability.py` or `tests/test_develop_references.py`; the
develop suite lives in `tests/test_agency.py`
(`test_every_dev_skill_walks_to_a_hard_gate`, `test_checklist_returns_steps…`).
Critically, `test_every_dev_skill_walks_to_a_hard_gate` (test_agency.py:691)
asserts `phases[-1].gate == "hard"` AND walks each skill to completion. Inserting
`triage` between `dispatch` and the `resolve` gate is safe ONLY if `triage` is a
non-terminal, non-gate phase and `_walk_to_completion` still reaches `resolve`.
The spec must require the existing test to keep passing (it lists this) but
should explicitly call out the `phases[-1]` invariant so the implementer doesn't
accidentally make `triage` terminal. Also: assert `triage` *produces*
`classified_findings` AND that a `disagree`/`needs-verification` classification
is representable — ordering alone is a weak test (Adzic's point).

**Nygard (failure modes).** What happens when `develop.reference("unknown")` is
called — the spec says "return the available list" (good, matches existing
`develop.py:143-145`). But there is no failure-mode criterion for the
*receiving* path: what if a finding is classified `needs-verification` and the
verification can't run? Superpowers handles this explicitly (cache
`receiving-code-review/SKILL.md:79-80`: "IF can't easily verify: say so… ask for
direction"). The `resolve` gate should be unable to pass with an unresolved
`needs-verification` item — encode that as the gate predicate, not prose.

---

## Open-Questions triage

1. **lib/bin runtime-deps?** — **RESOLVED: none, and lib/bin don't exist.**
   Rewrite OQ1 to classify the per-skill *scripts* (table above). Record actual
   SHA `f2cbfbefebbfef77321e4c9abc9e949826bea9d7` (v5.1.0).
2. **receiving-code-review: extend `review` or separate skill?** — **NOT
   adequately resolved.** Upstream they are two skills with two triggers, and
   receiving applies to feedback you didn't request. Recommendation: add a
   **separate `develop` skill `receive-review`** (phases: `read` → `understand`
   → `verify` → `triage` (classify) → `resolve` hard-gate), and keep `review`
   (requesting) as-is. A `triage` phase bolted onto `review` cannot model
   "feedback arrives unsolicited from a human." (Cockburn + Adzic.) If the team
   still prefers extend-one-skill, the spec must justify why the unsolicited-
   feedback actor is acceptably dropped. **Must-fix #3.**
3. **Reference fidelity vs originality** — **VALID, sharpen.** `persuasion-
   principles.md` teaches authority/"YOU MUST" pressure — the *exact* mechanism
   CORE says Agency drops in favor of structure. Re-expressing it risks
   re-introducing a dropped idea. Re-frame it as "why structural gates work
   (parahuman compliance research)", not "how to write YOU-MUST prose."
4. **anthropic-best-practices duplicates `best-practices`?** — **RESOLVED:
   distinct.** Upstream file is Anthropic's official guide (verbatim, ~46KB);
   Agency's `best-practices` is authored Agency-porting guidance. Keep distinct
   key BUT do not copy the upstream file (Must-Fix #5).

---

## Must-fix list (blocking)

1. **Fix the false source premises.** There is no `lib/`/`bin/`; the marketplace
   is not an aggregator forwarding to sub-plugins (it sources one inline plugin,
   `source: "./"`). Rewrite OQ1 + the audit `Done When` to classify the real
   per-skill *scripts*. Record the **actual** SHA
   `f2cbfbefebbfef77321e4c9abc9e949826bea9d7` (v5.1.0) — the spec's frozen
   `6be22035…` is not the reviewed tree.
2. **Enumerate the COMPLETE reference corpus.** Add the missing real docs
   (`testing-anti-patterns`, `root-cause-tracing`, `defense-in-depth`,
   `condition-based-waiting`, and a drop-with-reason for the host-adapter
   `references/*-tools.md`). The "no partial/planned rows" gate is unverifiable
   without the full list.
3. **Resolve OQ2 with a decision, and prefer a separate `receive-review`
   skill.** A `triage` phase on `review` cannot model unsolicited (human)
   feedback; superpowers ships two skills for two actors. Either add
   `develop.receive-review` (recommended) or justify dropping the unsolicited
   actor in the spec body.
4. **Reconcile `develop.py` vs `skills/code-review/SKILL.md` drift FIRST.** The
   capability says `request→dispatch→resolve`; the shipped skill says
   `request→assess→resolve`. They already disagree; the spec must pick the
   canonical graph before adding `triage`, or "installable skill matches schema"
   fails silently.
5. **Reference originality / license.** Do NOT carry `anthropic-best-practices.md`
   or `persuasion-principles.md` as copies (superpowers is MIT, the anthropic
   file is Anthropic docs). Re-express as ORIGINAL principle-focused prose, and
   re-frame persuasion as "why structural enforcement works," not "how to write
   YOU-MUST pressure" (CORE: pressure → structure).

## Should-fix (non-blocking)

- Make the `resolve` gate predicate reject unresolved `needs-verification`
  findings (Nygard) — judgment-as-code, not prose.
- Add Given/When/Then test fixtures for the pushback / disagree-with-reason path
  (Adzic), not just phase ordering.
- `estimated_jules_sessions: 2` is high for "1 discipline + N references + a
  doc-audit"; once premises are fixed this is ~1 session.
