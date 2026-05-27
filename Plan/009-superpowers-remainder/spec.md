---
spec_id: 009
slug: superpowers-remainder
status: draft
owner: "@agency"
depends_on: [003]
affects:
  - agency/capabilities/develop.py
  - skills/code-review/SKILL.md
  - docs/vision/specs/superpowers-port.md
  - tests/test_agency.py
source-repos:
  - "https://github.com/obra/superpowers-marketplace @ f2cbfbefebbfef77321e4c9abc9e949826bea9d7"
estimated_jules_sessions: 1
domain: capability
wave: 1
---

> **Read `Plan/JULES_PROTOCOL.md` (or `AGENTS.md`) before starting.** This is an
> ADDITIVE spec that EXTENDS the existing `develop` capability — it does NOT add a
> new capability file. Only modify the paths under `affects:`. Source repos are
> clone-and-read-only into `~/work/vendor/` — never commit them. **The canon wins;
> code serves it** (`docs/vision/CORE.md`). Re-express superpowers' system-prompt
> pressure as STRUCTURE (ordered phases + hard gates + judgment-as-code); never
> port the "you MUST" prose. If anything is ambiguous, stop and open
> `[BLOCKED: clarification]` — do not guess.

# Spec 009 — Superpowers Remainder

## Why

Agency's `develop` capability already ports the **bulk** of superpowers (see
`docs/vision/specs/superpowers-port.md` and `research/capability-specs/
capability-catalogue.md`). Reading every real `SKILL.md` in superpowers v5.1.0
(@ `f2cbfbef…`) against the shipped engine shows **13 of 14 disciplines are
already covered**:

- `develop` skills (gated phase-graphs): `brainstorm` (brainstorming), `plan`
  (writing-plans), `tdd` (test-driven-development), `debug` (systematic-
  debugging), `verify` (verification-before-completion), `spec-panel`, `review`
  (requesting-code-review), `execute` (executing-plans).
- companion capabilities the port spun off: `workspace` (using-git-worktrees),
  `branch` (finishing-a-development-branch), `delegate` (dispatching-parallel-
  agents), `subagent` (subagent-driven-development), `gate`, `plugin` +
  `skill_generator` (writing-skills).
- the discovery meta-skill (using-superpowers) IS the engine contract
  (`search`/`get_schema`/`execute`).

That leaves a precise, **single** uncovered discipline plus a body of
reference prose to port:

1. **`receiving-code-review`** — the ONE uncovered discipline. Superpowers ships
   it as a SEPARATE skill from `requesting-code-review` (two actors: an author
   requesting review vs. an implementer processing feedback — including
   UNSOLICITED feedback from a human). Today its rigor is implicitly folded into
   `review`'s `resolve` step and given no phases of its own.
2. **The reference corpus** — the per-skill supporting `.md` docs
   (writing-skills' `persuasion-principles`, `anthropic-best-practices`,
   `testing-skills-with-subagents`; tdd's `testing-anti-patterns`; debug's
   `root-cause-tracing` / `defense-in-depth` / `condition-based-waiting`). These
   are NOT new disciplines — they are knowledge that travels **re-expressed** as
   T3 progressive-disclosure docs fetched on demand by `develop.reference`, never
   carried in any system prompt.

There is **no new craft** here. The remainder is one half-ported discipline plus
re-expression of reference prose. Closing it lets the superpowers plugin be
uninstalled for development-discipline use.

### What is explicitly NOT a runtime dependency

The cached plugin is a **single, fully-inlined plugin** — NOT an aggregator.
`marketplace.json` lists exactly ONE plugin with `"source": "./"`; all 14 skill
bodies live inline under `skills/*/SKILL.md`. **There are no `lib/` and no `bin/`
directories anywhere in the tree.** The only executable scripts are per-skill
build/UX/example tooling with **zero runtime dependency** on Agency (see audit
table below): `writing-skills/render-graphs.js` (graphviz→SVG build),
`systematic-debugging/find-polluter.sh` (a bisect technique → re-express as
reference prose), the `brainstorming/scripts/*` WebSocket "visual companion"
server (interactive UX), `condition-based-waiting-example.ts` (example),
`scripts/{bump-version,sync-to-codex-plugin}.sh` (release tooling), and
`hooks/session-start` (the system-prompt pressure mechanism Agency deliberately
drops in favor of code-mode). None become capability verbs.

## Done When

- [ ] **Drift reconciled FIRST.** `agency/capabilities/develop.py` defines
      `review` as `request → dispatch → resolve`, but the shipped
      `skills/code-review/SKILL.md` says `request → assess → resolve`. Pick the
      canonical graph (the bound `dispatch` phase that invokes `delegate.fan_out`
      is the real one — `assess` is stale) and make the SKILL.md match BEFORE any
      new work. After this step the capability schema and the installable skill
      agree.
- [ ] A NEW `develop` skill **`receive-review`** is added to `DEV_SKILLS`
      covering the receiving actor (feedback you did NOT necessarily request,
      possibly from a human): phases `read` (raw feedback) → `understand`
      (restate / clarify; produces `clarified`) → `verify` (check each item
      against codebase reality; produces `checked`) → `triage` (classify each:
      `agree` / `disagree-with-reason` / `needs-verification`; produces
      `classified_findings`) → `resolve` (hard gate: `addressed`). `review`
      (requesting) is left as-is. The catalogue entry for `receiving-code-review`
      flips **partial → covered**.
- [ ] The `resolve` hard gate of `receive-review` CANNOT pass while any finding
      is classified `needs-verification` and unresolved — encode this as the gate
      predicate (judgment-as-code), not prose. A `disagree-with-reason`
      classification is representable and carries its reasoning (no silent
      compliance).
- [ ] `skills/code-review/SKILL.md` (requesting) and a new
      `skills/receiving-code-review/SKILL.md` (receiving) each reflect their
      phase-graph and pass `plugin.lint_skill`.
- [ ] `develop.reference` serves the FULL re-expressed corpus. `REFERENCES`
      gains an entry (or an explicit drop-with-reason) for EVERY heavy reference
      enumerated in the Design table below — at minimum:
      `persuasion-principles`, `anthropic-best-practices`, `testing-anti-patterns`,
      `root-cause-tracing`, `defense-in-depth`, `condition-based-waiting`,
      `receiving-review-rigor`; `testing-skills` confirmed at parity and kept.
      Each is ORIGINAL, principle-focused prose. `develop.reference("persuasion-
      principles")` returns the doc; an unknown topic returns the available list.
- [ ] The per-skill **script** audit is recorded in
      `docs/vision/specs/superpowers-port.md` (NOT a `lib/`/`bin/` audit — those
      do not exist). It classifies each script in the table below as
      build/UX/example/pressure tooling and records the **primary expected
      outcome: ZERO runtime dependencies**, with the marketplace SHA
      `f2cbfbefebbfef77321e4c9abc9e949826bea9d7` (v5.1.0) as evidence.
- [ ] The superpowers coverage table in `docs/vision/specs/superpowers-port.md`
      has NO remaining `partial`/`planned` rows for the enumerated in-scope items
      — every skill + every enumerated reference resolves to **covered** or an
      explicit **dropped (with reason)** (e.g. the host-adapter
      `using-superpowers/references/{codex,copilot,gemini}-tools.md` →
      dropped, Agency-irrelevant).
- [ ] `tests/test_agency.py` (the develop suite) covers the new `receive-review`
      phase-graph: `triage` produces `classified_findings` and precedes the
      `resolve` hard gate; the existing `test_every_dev_skill_walks_to_a_hard_gate`
      invariant (`phases[-1].gate == "hard"`, `_walk_to_completion` reaches the
      final gate) still holds — `triage` must be a NON-terminal, non-gate phase.
      A Given/When/Then fixture encodes the pushback path: GIVEN a finding the
      agent believes is wrong, WHEN triaged, THEN it is `disagree-with-reason`
      and `resolve` records the reasoning, not silent agreement. Reference tests
      assert every new topic resolves via `develop.reference` and unknown topics
      return the available list.
- [ ] The existing suite still passes (`pytest -q`); no regression in the 8
      shipped `develop` disciplines.
- [ ] No superpowers source is copied into the tree (the ~46KB
      `anthropic-best-practices.md` and `persuasion-principles.md` especially are
      RE-EXPRESSED, not carried). Vendor source stays read-only under
      `~/work/vendor/`.

## Source clones (run first)

```bash
git clone https://github.com/obra/superpowers-marketplace.git \
  ~/work/vendor/superpowers-marketplace
git -C ~/work/vendor/superpowers-marketplace checkout \
  f2cbfbefebbfef77321e4c9abc9e949826bea9d7   # v5.1.0 — the reviewed tree
```

Sweep the inline plugin (it is NOT an aggregator — `marketplace.json` sources one
inline plugin, `"source": "./"`; all skill bodies are inline):

```bash
V=~/work/vendor/superpowers-marketplace
find "$V/skills" -name 'SKILL.md' | sort
find "$V/skills" -name '*.md' ! -name 'SKILL.md' | sort   # the reference corpus
find "$V/skills" -type f ! -name '*.md' | sort            # the per-skill scripts
ls "$V"/{lib,bin} 2>/dev/null   # expected: NOTHING — they do not exist
cat "$V/.claude-plugin/marketplace.json"
```

If a source is unreachable, record `[BLOCKED: source superpowers-<x>]` and
continue with what you have.

## Design

The remainder is **EXTEND-not-add**: it mutates the existing `develop` capability
(`DEV_SKILLS` schema + `REFERENCES` dict) and the matching SKILL.md files. No new
top-level capability is created — the gap is one half-ported discipline plus
reference prose, not a new craft.

### Reconcile the existing drift FIRST

`develop.py` (`review`) and `skills/code-review/SKILL.md` already disagree on the
middle phase (`dispatch` vs `assess`). This MUST be fixed before adding anything,
or "the installable skill matches the schema" fails silently. The `dispatch`
phase is canonical (it is BOUND to `delegate.fan_out` — walking `review` with a
registry dispatches a real reviewer); `assess` is stale prose. Update the SKILL.md
to `request → dispatch → resolve`.

### The verified gap vs `develop.py`'s 8 disciplines

| superpowers item | current state | this spec's target | role |
|---|---|---|---|
| requesting-code-review | `review` (`request→dispatch→resolve`) — but SKILL.md drifted to `assess` | reconcile SKILL.md to `dispatch`; otherwise unchanged | — |
| **receiving-code-review** | rigor implicitly folded into `resolve` (**partial**) | NEW skill `receive-review` (`read→understand→verify→triage→resolve`) | discipline (transform) |
| writing-skills: testing-skills-with-subagents | `REFERENCES["testing-skills"]` present | confirm parity; keep | reference (transform) |
| writing-skills: persuasion-principles | absent (**planned**) | `REFERENCES["persuasion-principles"]`, RE-FRAMED (see OQ3) | reference (transform) |
| writing-skills: anthropic-best-practices | absent (distinct from Agency's `best-practices`) | `REFERENCES["anthropic-best-practices"]` (re-expressed, NOT the 46KB copy) | reference (transform) |
| tdd: testing-anti-patterns | absent | `REFERENCES["testing-anti-patterns"]` | reference (transform) |
| debug: root-cause-tracing | absent | `REFERENCES["root-cause-tracing"]` | reference (transform) |
| debug: defense-in-depth | absent | `REFERENCES["defense-in-depth"]` | reference (transform) |
| debug: condition-based-waiting | absent | `REFERENCES["condition-based-waiting"]` (fold the `.ts` example in if kept) | reference (transform) |
| receiving-review rigor notes | absent | `REFERENCES["receiving-review-rigor"]` | reference (transform) |
| using-superpowers/references/*-tools.md | n/a | **dropped** (host-adapter docs, Agency-irrelevant) | — |

### The per-skill SCRIPT audit (NOT lib/bin — those don't exist)

| script (cache path) | what it is | classification |
|---|---|---|
| `skills/writing-skills/render-graphs.js` | renders skill graphviz → SVG | **build/dev tooling** — drop |
| `skills/systematic-debugging/find-polluter.sh` | bisects a polluting test | **technique helper** — re-express as reference prose; NOT a verb |
| `skills/brainstorming/scripts/{server.cjs,helper.js,start-server.sh,stop-server.sh,frame-template.html}` | hand-rolled WebSocket "visual companion" | **interactive UX** — out of scope; `brainstorm` is a gated phase-graph — drop |
| `skills/systematic-debugging/condition-based-waiting-example.ts` | example code | **prose/example** — fold into the debug reference if kept |
| `skills/writing-skills/graphviz-conventions.dot` | graph styling | **build/dev tooling** — drop |
| `scripts/{bump-version,sync-to-codex-plugin}.sh` (repo root) | release/sync tooling | **build tooling** — drop |
| `hooks/session-start` + `hooks/hooks.json` | injects `using-superpowers` into the system prompt | **the pressure mechanism Agency drops** (code-mode replaces it) — dropped-with-reason |

**Conclusion: NONE are runtime dependencies.** The `Done When` audit line records
this as the primary expected outcome, evidenced by the SHA — not via the false
"aggregator-only" reasoning.

### Verbs / skills touched

- **NEW `develop` skill `receive-review`** (`DEV_SKILLS["receive-review"]`,
  **transform-home** discipline): `read → understand → verify → triage →
  resolve(hard)`. Receiving-review rigor becomes STRUCTURE: a finding cannot be
  resolved before it is verified-against-the-codebase and triaged
  (`agree` / `disagree-with-reason` / `needs-verification`). The `resolve` gate
  predicate REJECTS unresolved `needs-verification` items ("can't verify → say so,
  ask for direction"). This is a distinct skill (distinct actor/trigger) from
  `review`; the unsolicited-human-feedback case has no `request`/`dispatch` to walk.
- **`develop` skill `review`** (requesting): only its drifted SKILL.md is
  reconciled to `dispatch`; the phase-graph is unchanged.
- **`develop.reference`** (**transform**): no signature change; `REFERENCES`
  grows per the table. Heavy how-to stays T3, fetched on demand, never in a
  system prompt — the existing pattern.

## Files

- **Modify**:
  - `agency/capabilities/develop.py` — add `DEV_SKILLS["receive-review"]`
    (`read→understand→verify→triage→resolve`) with the `needs-verification`-aware
    `resolve` gate; grow `REFERENCES` per the Design table (original prose).
  - `skills/code-review/SKILL.md` — reconcile `assess → dispatch` (drift fix).
  - `docs/vision/specs/superpowers-port.md` — flip `receiving-code-review` and
    the enumerated reference rows to **covered**/**dropped**; record the per-skill
    SCRIPT audit (no runtime deps; SHA `f2cbfbef…`).
- **Create**:
  - `skills/receiving-code-review/SKILL.md` — the receiving phase-graph.
  - Tests in `tests/test_agency.py` (the develop suite) — `receive-review`
    ordering + the `needs-verification` gate + the disagree-with-reason Given/
    When/Then; reference resolution.
- **Move / Delete**: none.

## Open Questions / Needs Research

1. **(RESOLVED) Are any superpowers scripts runtime deps?** No. There is no
   `lib/`/`bin/`; the manifest sources one inline plugin (`"source": "./"`). All
   per-skill scripts are build/UX/example/pressure tooling (audit table) — ZERO
   runtime dependencies. The audit records this with SHA `f2cbfbef…` as evidence.
   No script becomes a capability verb. *(Was OQ1.)*
2. **(RESOLVED) `receiving-code-review`: extend `review` or separate skill?**
   SEPARATE skill `receive-review`. Upstream ships two skills for two actors, and
   receiving applies to UNSOLICITED feedback (incl. from a human) — a `triage`
   phase bolted onto `review` cannot model "feedback you did not request" (there
   is no `request`/`dispatch` to walk). *(Was OQ2.)*
3. **(OPEN) Re-framing `persuasion-principles` without re-introducing dropped
   pressure.** The upstream file teaches authority / "YOU MUST" compliance
   pressure — the EXACT mechanism CORE says Agency drops in favor of structure.
   Re-express it as "why structural gates work (parahuman compliance research:
   Cialdini, Meincke 2025)", NOT "how to write YOU-MUST prose". Confirm the framing
   with the canon owner before writing the entry.
4. **(OPEN) Does folding `condition-based-waiting-example.ts` into the
   `condition-based-waiting` reference add value, or should the example be
   dropped?** Decide during the reference sweep; either keep a short re-expressed
   illustration or drop-with-reason.
5. **(RESOLVED) `anthropic-best-practices` vs Agency's `best-practices`.**
   Distinct keys: the upstream file is Anthropic's official skill-authoring guide
   (~46KB verbatim); Agency's `best-practices` is authored porting guidance. Keep
   a distinct key BUT do NOT copy the upstream file — re-express its principles.

## Evidence

- `~/work/vendor/superpowers-marketplace/.claude-plugin/marketplace.json` — ONE
  inline plugin (`"source": "./"`); proves it is NOT an aggregator.
- `~/work/vendor/superpowers-marketplace/skills/*/SKILL.md` — the 14 skill bodies
  (inline); diffed against the ported set yields 1 uncovered discipline.
- `~/work/vendor/superpowers-marketplace/skills/receiving-code-review/SKILL.md`
  (lines 16-25 the response pattern, 79-80 "can't verify → ask", 113-129 "When To
  Push Back") — the source for the `receive-review` phases + gate predicate.
- `~/work/vendor/superpowers-marketplace/skills/*/*.md` (non-SKILL) — the full
  reference corpus enumerated in the Design table.
- `~/work/vendor/superpowers-marketplace/skills/**/*.{js,sh,ts,cjs,html,dot}`,
  `scripts/`, `hooks/` — the per-skill scripts (no `lib/`/`bin/`); all
  build/UX/example/pressure tooling.
- Agency prior art (DO NOT re-port): `agency/capabilities/develop.py` (the 8
  shipped disciplines + the `REFERENCES` T3 pattern + the `review` phase-graph
  with its `delegate.fan_out`-bound `dispatch` phase; note the SKILL.md drift),
  `skills/code-review/SKILL.md`,
  `agency/capabilities/{workspace,branch,delegate,subagent,gate}.py` (the
  spun-off companion capabilities), `docs/vision/specs/superpowers-port.md` (the
  authoritative coverage mapping + pressure→structure thesis; the doc this spec
  finishes), `tests/test_agency.py` (`test_every_dev_skill_walks_to_a_hard_gate`,
  `test_checklist_returns_steps…` — the invariants to preserve),
  `research/capability-specs/capability-catalogue.md` (per-skill status).
