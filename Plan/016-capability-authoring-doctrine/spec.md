---
spec_id: "016"
slug: capability-authoring-doctrine
status: complete                 # v2 shipped 2026-05-30: Phases 2/3/5 landed; 7 dropped; 6 → Spec 028
version: 2
shipped_commits:
  - "f5f7575 (Phase 1 — CAPABILITY-AUTHORING.md)"
  - "7e3de29 (Phase 2 — CORE.md CapabilityContext paragraph)"
  - "8a5a45d (Phase 3 — folder-form discover RED→GREEN)"
  - "d76135a (Phase 5 — tests/conftest.py + proof-of-concept migration)"
  - "e9a529d (Phase 5 hardening — 4 spec-panel findings folded)"
  - "Plan/024 PR-A (Phase 4 — plugin.lint_capability, in-flight)"
owner: "@agency"
depends_on: ["001", "012", "013"]
affects:
  - docs/vision/CORE.md                          # Phase 2 — CapabilityContext paragraph (this iteration)
  - docs/vision/CAPABILITY-AUTHORING.md          # Phase 1 — SHIPPED f5f7575
  - agency/capabilities/__init__.py              # Phase 3 — folder-form discover() RED→GREEN
  - agency/capabilities/plugin.py                # Phase 4 — lint_capability — DEFERRED to Plan/024 PR-A
  - tests/conftest.py                            # Phase 5 — shared fixtures (13 dup blocks VERIFIED by survey a7e6bd1)
defers_to:
  - "028 (jules-folder-migration)"  # Phase 6 — heavy mechanical move; warrants its own spec
drops:
  - phase: 7
    reason: |
      plugin → folder form. v1 cited "consolidating templates.py
      ownership" but (a) plugin.py has ZERO sibling helpers,
      violating Hint #2's own ≥3-sibling bar; (b) templates.py is a
      top-level shared module used by plugin AND install AND jules —
      folder consolidation would break the sharing. Phase 7's
      rationale collapses on two grounds rooted in Spec 016's own
      doctrine.
estimated_jules_sessions: 0
domain: meta
wave: 3
---

# Spec 016 v2 — Capability authoring doctrine (Foundation iteration)

> **What changed in v2 from v1:**
> - **Status**: `draft` → `in-progress`. Phases 1 + 4 are done (1 shipped
>   `f5f7575`; 4 absorbed by Plan/024 PR-A — implementation lives on
>   `plugin.lint_capability`, not `develop.lint_capability`, per spec-panel
>   F5a). This iteration ships Phases 2 + 3 + 5.
> - **Phase 7 DROPPED** with rationale in frontmatter `drops:` block.
>   v1 was self-contradictory; v2 honors Hint #2.
> - **Phase 6 DEFERRED** to a future Spec 028 (jules-folder-migration).
>   The mechanical refactor is genuinely heavy (6 file moves + 13 test-file
>   import rewires); it warrants its own spec rather than landing under
>   the doctrine umbrella.
> - **Phase 5 fixture design** now grounded in a real survey
>   (`reflection a7e6bd1`): the v1 "13 duplicate fixture blocks" claim
>   verified EXACTLY. Design upgraded from v1's two fixtures (`engine`,
>   `iid`) to four (adds `memory_engine` for the ~13 inline `:memory:`
>   call-sites and `make_engine(**overrides)` factory for the 5 special-purpose
>   tests). Also fixes a latent bug: v1's `tempfile.mktemp()` is deprecated
>   (race condition); v2 uses pytest's `tmp_path`.


## Why

**The Core canon** (`docs/vision/CORE.md`) defines WHAT a capability is — an
invokable action with role-tagged verbs, owning an ontology fragment, exposed
isomorphically over MCP / Skills / bash CLI. **It does NOT define HOW to author
one.** That gap has been filled implicitly by precedent (`reflect.py`, `plugin.py`,
`develop.py`, `jules.py`); the precedent is uneven, and the unevenness costs
tokens, tests, and review time.

This spec is the **first Core Expansion** — the canon stays minimal; this doctrine
layers ON TOP, governing the open set of capabilities authors will keep adding.
Per the canon's own discipline (CORE.md "the canon wins; code serves it"), the
doctrine page becomes part of what new capabilities must read before adding a file.

The hints below come from the session that produced it — actual experience
authoring `jules` (heavy), `delegate` (medium), `dogfood` (light), and the
six new Jules-specific skills. **Every hint is grounded in a file:line cite**
so the doctrine traces back to real code, not speculation.

## Done When

- [ ] `docs/vision/CAPABILITY-AUTHORING.md` lands as the canonical authoring doctrine.
  - Eleven sections (mirror the structure of "The Capability Contract" below).
  - File:line cites for every claim that has a counter-example in the code.
- [ ] `docs/vision/CORE.md` gains a short pointer paragraph + the
  `CapabilityContext` field list (currently undocumented in canon — see
  Hint #5 below). Cite: `agency/capability.py:47` (the `engine` field added
  mid-session was the trigger).
- [ ] `agency/capabilities/__init__.py` `discover()` accepts BOTH module-form
  and subpackage-form capabilities (Hint #1).
  - RED test: a fixture capability laid out as a folder + `__init__.py`
    re-exporting the Capability class registers identically to one declared
    as a single `.py` file.
- [ ] `plugin.lint_capability(name)` verb lands (extension of `plugin.lint_skill`).
  - Enforces the docstring contract from Hint #7: every `@verb` docstring
    names input keys, output keys, and a `chain_next:` line.
  - Enforces the `input-required` return convention (Hint #8) where it
    applies (effects + multi-step transforms).
  - Returns `{ok, violations: [{verb, kind, msg, fix}]}` — same shape as
    `lint_skill`.
- [ ] `tests/conftest.py` lands with shared `engine`/`iid` fixtures; 13
  duplicate fixture blocks across test files removed (subagent finding).
- [ ] `Plan/016-…/IMPLEMENTATION-PLAN.md` lands (Phase E of the design loop).
- [ ] Three existing capabilities migrate to the new shape as proof:
  - `jules` (heavy) → folder form (Hint #1). Sibling `_jules_*.py` files
    move under `agency/capabilities/jules/`.
  - `reflect` (light) → stays single-file (Hint #2: don't fix what works).
  - `plugin` (medium) → folder form, consolidating `templates.py`
    ownership under `agency/capabilities/plugin/templates.py`. The
    third migration is no longer hypothetical — `plugin` is the clean
    pick because `templates.py` is already a shared module + the
    folder form makes ownership explicit (panel W1).
- [ ] **Folder-form precedence rule** (panel W2): when both
  `jules/__init__.py` AND `jules/jules.py` declare a `CapabilityBase`
  subclass, `__init__.py`'s explicit re-export wins (this is the
  canonical pattern — `jules.py` is the class file; `__init__.py` is
  the discovery surface). The `discover()` patch enforces this
  ordering in a RED test (two competing classes; the re-exported one
  is what `registry.names()` carries).
- [ ] **`@verb(skip_lint=True)` escape hatch** (panel W3): intentional
  minimal docstrings (e.g. trivial wrappers, single-line predicates)
  can opt out of the docstring lint. `lint_capability` skips these +
  records the count in its output (so reviewers see "5 verbs linted, 1
  skip_lint=True"). Used SPARINGLY by doctrine; the default is
  enforcement.
- [ ] `pytest -q` stays green throughout (currently 216).

## The capability contract (refresh + corrections)

The canon (`CORE.md`) said: capabilities are an open set; verbs are
role-tagged `act`/`transform`/`effect`; each capability owns an ontology
fragment; everything self-registers via reflection. **All true.** This
section adds what the canon underspecifies + what the code has decided
through precedent.

### Hint #1 — Folder form is the right shape for heavy capabilities

**Trigger:** `jules.py` (571 lines) + 6 sibling files (`_jules_api.py` 412 LOC,
`_jules_watch.py` 384 LOC, `_jules_patch.py`, `_jules_preambles.py`,
`_jules_skills.py`, `_jules_reference.md`). Seven files for one capability is
the signal that the `capability-as-file` shape has run out.

**Doctrine:** a capability is a **module or a subpackage**, both forms accepted
by `discover()`. The folder layout is:

```
agency/capabilities/jules/
  __init__.py        # re-exports JulesCapability so discover() finds it
  jules.py           # the CapabilityBase class
  api.py             # was _jules_api.py (httpx client; the boundary)
  watch.py           # was _jules_watch.py (background watcher)
  patch.py           # was _jules_patch.py (unidiff planner)
  preambles.py       # was _jules_preambles.py (Mode A/B assembler)
  skills.py          # was _jules_skills.py (ontology.skills source)
  reference.md       # was _jules_reference.md (external doc)
  templates/         # NEW — Jinja/YAML templates the capability owns
  schemas/           # NEW — JSON schemas for payloads
  ontologies/        # NEW — split ontology fragments if large
```

**Discovery change (~10 LOC at `agency/capabilities/__init__.py:20-34`):**

```python
for info in sorted(pkgutil.iter_modules(__path__), key=lambda i: i.name):
    if info.name.startswith("_"):
        continue
    module = importlib.import_module(f"{__name__}.{info.name}")
    # Works for BOTH .py modules and folder/__init__.py subpackages —
    # importlib unifies them. Sibling files inside a subpackage that start
    # with `_` are still skipped because the inner __init__.py decides
    # what to re-export. (Underscore-prefix-skip stays the boundary marker.)
```

**Rule for choosing:** stay single-file until the capability would have ≥3
sibling files. Then promote to folder. The migration is mechanical (move +
re-export); zero behavioural change.

### Hint #2 — Light capabilities stay single-file (don't fix what works)

**Trigger:** subagent inventory — `gate.py` (44 LOC), `subagent.py` (39 LOC),
`skill_generator.py` (25 LOC), `reflect.py` (~80 LOC) are all healthy as
single files. Promoting them to folders adds ceremony without saving anything.

**Rule:** the folder form is for capabilities that already have ≥3 sibling
files or ship templates/schemas/ontologies as data. Otherwise the single-file
form wins on clarity.

### Hint #3 — Verb role tags are load-bearing

The canon says verbs are `act` / `transform` / `effect`. Concrete rules
(extracted from the precedent):

- **`act`**: writes an artefact / a node / a reflection. Records an Invocation
  + SERVES edge. Example: `reflect.note` (`agency/capabilities/reflect.py:26`).
- **`transform`**: pure compute over inputs (or read-only graph query). No
  side effects beyond the invocation record. Example: `plugin.lint_skill`
  (`agency/capabilities/plugin.py:212`).
- **`effect`**: touches the outside world (Jules REST, GitHub MCP, filesystem,
  subprocess). Example: `jules.dispatch` (`agency/capabilities/jules.py:160`).

**Why it matters for authors:** the engine's auto-wiring + ToolResult unwrap
+ provenance recording all key off the role tag. Mis-tagging a verb that
calls a remote API as `transform` silently breaks the provenance moat.

### Hint #4 — Capability owns ITS ontology fragment; never reaches into others

**Trigger:** `JulesCapability.ontology` (`agency/capabilities/jules.py:137-150`)
owns `JulesSession` / `JulesAlias` / `JulesWatchEvent` / `JulesPatch` nodes +
`OBSERVED_OF` / `RECOVERED_BY` / `ALIAS_OF` edges + `JulesState` / `WatchAction`
enums. None of these leak into other capabilities; the merge into the engine
ontology is strict.

**Rule:** when adding a node type, edge label, or enum, declare it on YOUR
capability's `OntologyExtension`. Don't reach across. If two capabilities
need the same node type, neither should own it — promote to the core ontology
via a CORE.md amendment (a high-cost path that should be rare).

### Hint #5 — `CapabilityContext` fields the canon doesn't document yet

**Trigger:** mid-session we added `engine` to `CapabilityContext`
(`agency/capability.py:47`) because `jules.watch` needs to reach
`engine._jules_watcher`. The canon doesn't list the context's fields.

**Rule:** treat `CapabilityContext` as part of the canon surface. Its
current fields:

| Field | Purpose | Example use |
|---|---|---|
| `memory` | The graph (Memory instance) | `ctx.memory.record(...)`, `ctx.memory.g.query(...)` |
| `ontology` | The merged ontology (read-only) | `ctx.ontology.skills["jules-fanout"]` |
| `registry` | The capability registry | `ctx.registry.invoke(...)` for cross-capability calls |
| `intent_id` | The SERVING intent (auto-injected) | every node `SERVES` this |
| `agent_id` | Optional performer | `agent:claude` / `agent:jules` |
| `client` | Boundary object the engine injects (e.g. `JulesClient`) | `self.ctx.client.create(...)` in `jules.py:152` |
| `depth` | Recursion-depth guard | `ctx.spawn` enforces `MAX_DEPTH=16` |
| `engine` | The owning Engine (for engine-attached singletons) | `self.ctx.engine._jules_watcher` |

**Action for the doctrine page:** this table copies into CAPABILITY-AUTHORING.md
and a one-line "context surface includes …" sentence lands in CORE.md.

### Hint #6 — Returns must be deltas, not dumps

**Trigger:** token-efficiency audit (subagent) flagged
`reflect.recall(scope="")` and `reflect.search(query)` as unbounded — they
return ALL Reflection nodes. On a project with 1000+ reflections that's a
megabyte of JSON crossing the sandbox boundary, defeating the code-mode
"sandbox keeps intermediate results" promise.

**Rule:** every `transform` verb that could return >20 items MUST take a
`limit: int` arg (sane default, e.g. 20) and return `{result, total, cursor}`
for pagination. Every verb returning a string body (e.g. `jules.patch_body`
returns multi-KB diffs) MUST take a `max_bytes: int` arg.

**Rule:** `act` verbs return only `{result: <id>}` or
`{result: <id>, metadata: <≤100 chars>}` — never the recorded node verbatim.

### Hint #7 — Docstring contract (named keys + chain hint)

**Trigger:** `get_schema(tools=[...])` returns the verb's docstring as the
primary documentation surface. Many existing docstrings prose-describe
behavior without naming the keys; an agent reading them must guess at
`returns["session"]` vs `returns["sid"]`.

**Rule:** every `@verb` docstring follows this shape (~3-6 lines):

```python
@verb(role="effect")
def dispatch(self, source: str, ..., automation_mode: str = "") -> dict:
    """Spawn a remote Jules session.

    Inputs: source (owner/repo), starting_branch, prompt, title?,
            require_plan_approval=True, alias?, automation_mode='|AUTO_CREATE_PR',
            protocol_preset='agency-default'.
    Returns: {status, session, url, alias, artefact: {kind, session, url}}.
    chain_next: jules.status(session=) once dispatched; jules.approve_plan
                if state in {AWAITING_PLAN_APPROVAL, COMPLETED+plan_unapproved}.
    """
```

The `Inputs:` / `Returns:` / `chain_next:` markers are what
`plugin.lint_capability` (Done When item) enforces.

### Hint #8 — Universal `input-required` return convention

**Trigger:** the Codex C3 fix (`agency/skill.py:71-95`) made hard-gate
pauses persist as `Gate{paused:True}` + `BLOCKED_ON` edges. The pause
returns `{status: "input-required", phase, gate: "hard", blocked_on}`.
This shape should be UNIVERSAL across any verb that can pause.

**Rule:** verbs that can block on human/agent input return:

```python
{
    "status": "input-required",
    "reason": "<one-liner why>",
    "blocked_on": "<Gate id>",        # the persisted blocker for audit
    "resume_with": ["<input keys>"],  # what the caller must supply on retry
}
```

The caller resumes by re-invoking with the resume-with keys + a `confirmed=True`
flag (where applicable). This is the chain-pattern at scale — applies to skills,
to long-running effects, to elicit-driven gates.

### Hint #9 — Skills compose by intersection at hard gates

**Trigger:** Spec 013's intersection model (DESIGN.md §3, recommended (a))
proved out: skills chain not by name-keyed registry but by *shared hard
gates* and *data-flow*. Example: `jules-protocol-preamble.dispatched.session_id`
feeds every subsequent Jules skill; `jules-recovery-when-stuck.recovered.pr_url`
feeds `jules-pr-review-cycle`.

**Rule:** when a capability owns ≥2 skills that chain, do NOT introduce a
"meta-skill" or a name-keyed shared-gate registry. Make the produces field
of one phase MATCH the inputs of the next phase's first invocation. The
walker handles the rest.

### Hint #10 — Graph is the store; files are a rendered view

**Trigger:** the user's mid-session insight — `DOGFOOD-NOTES.md` files were
markdown round-tripping data (`dogfood.collect` parsed back into Reflection
nodes via `reflect.batch_note`). Backwards. The canon's "the moat is the
graph" implies the graph is the source of truth; markdown is the rendered
view for external readers.

**Rule:** if your capability writes a markdown file that downstream code
parses, you have it backwards. Write to the graph (a `Reflection` /
`Artefact` / your-own-node-type); render markdown on demand via a separate
`<cap>.render(...)` verb when humans need it. Exceptions: canon/doctrine
docs (CORE.md, AGENTS.md, AGENCY_PROTOCOL.md) — those serve external
readers and stay as files.

### Hint #11 — Verbs go through the engine in tests

**Trigger:** subagent test-audit + session experience. 13 test files
re-declare `engine`/`iid` fixtures. Several test verbs by importing and
calling them directly instead of via `engine.registry.invoke` — which
skips the provenance record + the ToolResult unwrap + the C5 intent-id
validation.

**Rule:** tests exercise verbs through `engine.registry.invoke(...)`, NEVER
by direct method call. Shared `tests/conftest.py` provides `engine` and `iid`
fixtures so the boilerplate stops repeating. Direct verb tests (when truly
needed for a pure transform) live in their own file marked `# unit-level —
does not exercise engine wiring`.

## The capability shape (decision tree)

```
Adding a new capability?
├── Will it ship templates / schemas / ontologies as data files?
│       ├── YES → folder form from day 1
│       └── NO  → next question
├── Does it have any underscore-prefixed sibling that exists ONLY to support it?
│       ├── ≥2 siblings → folder form
│       └── 0-1 siblings → single-file
└── (Re-evaluate at every commit; promote to folder when the second sibling lands.)
```

## Files

- **Create:**
  - `docs/vision/CAPABILITY-AUTHORING.md` — the doctrine page (the eleven
    hints above, expanded with examples; ~250 lines).
  - `agency/capabilities/__init__.py` discovery patch (subpackage form).
  - `tests/conftest.py` — shared fixtures.
  - `tests/test_capability_authoring.py` — RED→GREEN coverage of the
    subpackage form, the docstring lint, the `input-required` convention.
  - `Plan/016-…/IMPLEMENTATION-PLAN.md` (Phase E).
- **Modify:**
  - `docs/vision/CORE.md` — add the `CapabilityContext` fields paragraph
    + pointer to CAPABILITY-AUTHORING.md.
  - `agency/capabilities/plugin.py` — add `lint_capability` verb.
  - `agency/capabilities/jules.py` → folder migration (`jules/` subpackage).
  - One other capability migration (to be picked per Jules's findings).
  - All test files using the engine/iid fixture pattern — strip duplicates
    once `conftest.py` is in.

## Open Questions

1. **Should `lint_capability` BLOCK on docstring violations, or just warn?**
   The doctrine answer is BLOCK (parity with `lint_skill`), but the
   migration cost is real — every existing verb's docstring needs the
   `Inputs:` / `Returns:` / `chain_next:` markers. Recommend: WARN for the
   migration window; flip to BLOCK after all shipped verbs comply.

2. **Where does the `chain_next:` hint live for verbs that can chain to
   MULTIPLE different verbs based on state?** Example: `jules.dispatch`'s
   natural next call branches on `automation_mode` + `require_plan_approval`.
   Recommend: structured list — `chain_next: jules.status (always);
   jules.approve_plan (state==AWAITING_PLAN_APPROVAL)`.

3. **Does the subpackage form change any auto-install behaviour?**
   `python -m agency.install` regenerates the help skill + plugin manifest
   by reflecting over `registry.names()`. Folder vs file should be
   transparent if discovery handles both; verify with the RED test before
   migrating jules.

4. **Jules's architecture review (Spec 015) may surface additional hints.**
   Reserve a `### Hint #12+ (post-Jules)` section to fold those in without
   restructuring. Specific topics likely to surface based on the dispatch
   brief: graph-vs-file generalization beyond DOGFOOD-NOTES.md; concrete
   token-leak examples from running execute blocks; specs for new
   capabilities the existing roadmap implies (e.g. `research`).

5. **Should the doctrine page live under `docs/vision/` or under
   `docs/getting-started.md`?** `vision/` is the canon (read-once);
   getting-started/ is the onboarding (read-while-doing). The doctrine is
   read by ANY agent considering adding a capability — both audiences. I
   recommend `docs/vision/CAPABILITY-AUTHORING.md` with a strong link from
   `docs/getting-started.md`.

## Evidence (cites)

- `docs/vision/CORE.md` — the four concepts + the open-set claim this doctrine
  expands. Lines :7-18 (lean code-mode contract), :47-62 (skills),
  :131-133 (capability-owned ontology, strict merge).
- `agency/capability.py:36-60` — `CapabilityContext` (Hint #5 target).
- `agency/capabilities/__init__.py:20-34` — discovery (Hint #1 target).
- `agency/capabilities/jules.py:127-150` — JulesCapability + ontology
  (Hint #4 reference; Hint #1 migration target).
- `agency/capabilities/reflect.py:17-65` — single-file precedent (Hint #2).
- `agency/capabilities/_jules_skills.py` (subpackage migration: → `jules/skills.py`).
- `agency/skill.py:48-99` — SkillRun + the `input-required` convention
  (Hint #8 reference; Codex C3 made the pause persist).
- `agency/capabilities/plugin.py:212` — `lint_skill` precedent for
  `lint_capability` (Done When item).
- `agency/capabilities/dogfood.py` + `Plan/013-…/DOGFOOD-NOTES.md` — the
  markdown-round-trip anti-pattern Hint #10 closes.
- `agency/capabilities/_jules_watch.py:73-145` — the `_classify` function +
  the `plan_unapproved` parameter (recent doctrine fix; Hint #5 + Hint #8
  apply here too).
- `Plan/015-architecture-review/` (forthcoming, Jules) — the deeper hint
  source. Reserved for Hint #12+.
- Reflection nodes recorded this session — `reflect.recall(scope="observation")`
  surfaces them; the doctrine-correction triplet
  (`reflection:32e3bce4` / `766d9f69` / `05dd76de`) and the Spec 014
  hint set (10 nodes from `dogfood.collect` walk).
