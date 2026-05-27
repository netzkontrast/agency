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
  - tests/test_develop_capability.py
  - tests/test_develop_references.py
source-repos:
  - "https://github.com/obra/superpowers-marketplace @ 6be22035d873c31ca246db4f4932a1098aea46fc"
estimated_jules_sessions: 2
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
capability-catalogue.md`). What ships today, role-tagged:

- `develop` skills (gated phase-graphs): `brainstorm`, `plan`, `tdd`, `debug`,
  `verify`, `spec-panel`, `review`, `execute`.
- companion capabilities the port spun off: `workspace` (using-git-worktrees),
  `branch` (finishing-a-development-branch), `delegate` (dispatching-parallel-
  agents), `subagent` (subagent-driven-development), `gate`, `plugin` +
  `skill_generator` (writing-skills).
- the discovery meta-skill (using-superpowers) IS the engine contract
  (`search`/`get_schema`/`execute`).

That leaves a precise, small **remainder** — the items the catalogue marks
`partial` or `planned`, plus anything in the marketplace tree (`lib/`, `bin/`,
`references/`) not yet absorbed:

1. **`receiving-code-review`** — marked **partial** (folded into `review`'s
   resolve phase but never given its own technical-rigor phases).
2. **The heavy `references/`** — the writing-skills how-to corpus
   (`testing-skills-with-subagents.md`, `persuasion-principles.md`,
   `anthropic-best-practices.md`, and any per-skill `references/`) — marked
   **planned**. In Agency these travel as T3 progressive-disclosure docs fetched
   on demand by `develop.reference`, NOT carried in any system prompt.
3. **`lib/` + `bin/` scripts** — the marketplace's helper modules and CLI scripts.
   Per FINDINGS, the marketplace root is mostly an *aggregator* (a
   `marketplace.json` manifest), so we must verify which scripts are genuine
   **runtime dependencies** (must become capability utilities or sandbox-exec
   wrappers) versus **prose/build tooling** (re-express as references or drop).

This spec closes that remainder so the superpowers port is COMPLETE and the
SuperClaude/superpowers plugins can be uninstalled for development-discipline use.

## Done When

- [ ] `develop`'s `review` skill (in `DEV_SKILLS`) gains explicit
      **receiving-side** phases so the discipline covers BOTH requesting and
      receiving review: a `triage` phase (classify each finding: agree / disagree-
      with-reason / needs-verification) preceding the existing `resolve` gate. The
      catalogue entry for `receiving-code-review` flips **partial → covered**.
- [ ] `skills/code-review/SKILL.md` reflects the requesting + receiving phases (the
      installable skill matches the schema). It passes `plugin.lint_skill`.
- [ ] `develop.reference` serves the remaining superpowers how-to corpus. The
      `REFERENCES` dict gains entries for every heavy reference identified in the
      marketplace sweep (at minimum: `testing-skills-with-subagents`,
      `persuasion-principles`, `anthropic-best-practices`, `receiving-review-rigor`).
      Each is ORIGINAL, principle-focused prose (the knowledge travels re-expressed,
      not copied). `develop.reference("persuasion-principles")` returns the doc.
- [ ] A marketplace `lib/`+`bin/` audit is recorded in
      `docs/vision/specs/superpowers-port.md` classifying each script as
      **runtime-dep** (→ ported as a capability utility / `effect` verb) or
      **build/prose** (→ dropped or referenced). If any runtime-dep is found, it is
      ported behind an existing capability (no new top-level capability) and tested;
      if NONE are found (the expected outcome — the tree is an aggregator), that
      finding is documented explicitly with the marketplace commit SHA as evidence.
- [ ] The superpowers coverage table in `docs/vision/specs/superpowers-port.md` has
      NO remaining `partial`/`planned` rows for in-scope items — every superpowers
      skill + its references resolves to **covered** or an explicit **dropped (with
      reason)**.
- [ ] `tests/test_develop_capability.py` covers the extended `review` phase-graph
      (asserts `triage` precedes the `resolve` hard gate; ordering enforced).
      `tests/test_develop_references.py` asserts every new reference topic resolves
      via `develop.reference` and that unknown topics return the available list.
- [ ] The existing suite still passes (`pytest -q`); no regression in the 8 shipped
      `develop` disciplines.
- [ ] No superpowers source is copied into the tree. References are re-expressed;
      vendor source stays read-only under `~/work/vendor/`.

## Source clones (run first)

```bash
git clone --depth=1 https://github.com/obra/superpowers-marketplace.git \
  ~/work/vendor/superpowers-marketplace   # SHA 6be22035d873c31ca246db4f4932a1098aea46fc
```

Sweep for the full skill + reference + script set:

```bash
find ~/work/vendor/superpowers-marketplace -name 'SKILL.md' -o -name '*.md' \
  -path '*references*' ; ls -R ~/work/vendor/superpowers-marketplace/{lib,bin} 2>/dev/null ; \
  cat ~/work/vendor/superpowers-marketplace/.claude-plugin/marketplace.json
```

If the marketplace only vendors a manifest (no inline `lib/`/`bin/`/`references/`),
the actual skill bodies live in the referenced sub-plugins — follow the
`marketplace.json` plugin sources and record where the real `references/`/`lib/`/
`bin/` live before classifying. If a source is unreachable, record
`[BLOCKED: source superpowers-<x>]` and continue with what you have.

## Design

The remainder is **EXTEND-not-add**: it mutates the existing `develop` capability
(`DEV_SKILLS` schema + `REFERENCES` dict) and the matching `skills/code-review/
SKILL.md`. No new top-level capability is created (the gap is references + one
half-ported discipline, not a new craft).

### The gap vs `develop.py`'s existing 8 disciplines

`develop.py` ships `{brainstorm, plan, tdd, debug, verify, spec-panel, review,
execute}` and a `REFERENCES` dict with `{testing-skills, skill-descriptions,
best-practices}`. The gap this spec fills:

| superpowers item | current state in `develop.py` | this spec's target | role |
|---|---|---|---|
| requesting-code-review | `review` skill (request→dispatch→resolve) | unchanged (already covered) | — |
| receiving-code-review | folded into `resolve` only (**partial**) | add a `triage` phase before `resolve` | discipline (transform) |
| writing-skills ref: testing-skills-with-subagents | `REFERENCES["testing-skills"]` (present) | confirm parity; keep | reference (transform) |
| writing-skills ref: persuasion-principles | absent (**planned**) | `REFERENCES["persuasion-principles"]` | reference (transform) |
| writing-skills ref: anthropic-best-practices | partial (`best-practices` is Agency-authored) | `REFERENCES["anthropic-best-practices"]` (distinct) | reference (transform) |
| receiving-review rigor notes | absent | `REFERENCES["receiving-review-rigor"]` | reference (transform) |
| any per-skill `references/` found in sweep | absent | add to `REFERENCES` as found | reference (transform) |
| marketplace `lib/` modules | not surveyed | classify → port runtime-deps behind existing caps, else drop | effect/transform (only if runtime) |
| marketplace `bin/` scripts | not surveyed | classify → sandbox-exec wrapper if runtime, else drop | effect (only if runtime) |

### Verbs / skills touched

- **`develop` skill `review`** (`DEV_SKILLS["review"]`, **transform-home**
  discipline): insert phase `triage` (produces `classified_findings`) between
  `dispatch` and the `resolve` hard gate. The Iron-Law ordering means a finding
  cannot be resolved before it is triaged (agree / disagree-with-reason / needs-
  verification) — receiving-review rigor becomes STRUCTURE, not a "be rigorous"
  plea.
- **`develop.reference`** (**transform**): no signature change; the `REFERENCES`
  dict grows. Heavy how-to stays T3 (fetched on demand via code-mode), never in a
  system prompt — exactly the existing pattern.
- **(conditional) a `lib`/`bin` runtime-dep**: if the sweep finds a genuine
  runtime helper, it is added as a verb on an EXISTING capability (e.g. a
  `workspace`/`develop` utility) or a sandbox-exec wrapper; it is NOT a new
  capability. Expected outcome per FINDINGS: none found (aggregator-only).

## Files

- **Modify**:
  - `agency/capabilities/develop.py` — extend `DEV_SKILLS["review"]` with the
    `triage` phase; grow `REFERENCES` with the remaining superpowers how-to corpus
    (original, principle-focused prose).
  - `skills/code-review/SKILL.md` — reflect requesting + receiving phases.
  - `docs/vision/specs/superpowers-port.md` — flip `receiving-code-review` and the
    reference rows to **covered**; record the `lib/`+`bin/` classification audit.
- **Create**:
  - `tests/test_develop_capability.py` (or extend the existing develop test) — the
    extended `review` phase-graph ordering.
  - `tests/test_develop_references.py` — every reference topic resolves.
- **Move / Delete**: none.

## Open Questions / Needs Research

1. **Are any superpowers `lib/`/`bin/` scripts runtime deps or just prose/build
   tooling?** FINDINGS says the marketplace root is an aggregator (manifest only),
   so the expectation is NONE are runtime deps — but the real skill bodies live in
   the referenced sub-plugins. The sweep MUST follow `marketplace.json` to the
   sub-plugins and confirm. If a script IS a runtime dep (e.g. a skill that shells
   out to a helper), decide: port as a capability `effect` verb vs a sandbox-exec
   wrapper vs drop-and-reimplement-in-Python. **Resolve before writing code.**
2. **`receiving-code-review`: new skill or extend `review`?** This spec extends the
   existing `review` skill with a `triage` phase (one discipline covering both
   sides). Confirm this is faithful to superpowers, where requesting and receiving
   are two SEPARATE skills — if the two must stay distinct disciplines, add a
   second `develop` skill `receive-review` instead of extending `review`.
3. **Reference fidelity vs originality.** The CORE rule is "the knowledge travels,
   re-expressed" — references are ORIGINAL principle-focused prose, not copies (the
   existing `REFERENCES` entries already follow this). Confirm the new entries
   (`persuasion-principles`, `anthropic-best-practices`) re-express rather than
   reproduce the upstream files, to stay license-clean (superpowers is read-only).
4. **Does `anthropic-best-practices` duplicate the existing `best-practices`
   entry?** `develop.py` already has an Agency-authored `best-practices`. Decide
   whether the upstream anthropic-best-practices is a distinct doc worth a separate
   key, or whether its principles fold into the existing entry (avoid a near-dup).

## Evidence

- `~/work/vendor/superpowers-marketplace/.claude-plugin/marketplace.json` — the
  aggregator manifest; the source of truth for which sub-plugins host the real
  skill bodies / `references/` / `lib/` / `bin/`.
- `~/work/vendor/superpowers-marketplace/**/SKILL.md` + `**/references/*.md` — the
  skill + reference corpus to diff against the ported set.
- `~/work/vendor/superpowers-marketplace/{lib,bin}/` — the scripts to classify
  runtime-dep vs prose/build.
- Agency prior art (DO NOT re-port): `agency/capabilities/develop.py` (the 8
  shipped disciplines + the `REFERENCES` T3 pattern + the `review` phase-graph with
  its `delegate.fan_out`-bound dispatch phase), `skills/code-review/SKILL.md`,
  `agency/capabilities/{workspace,branch,delegate,subagent,gate}.py` (the
  spun-off companion capabilities — already cover worktrees/branch/parallel/
  subagent), `docs/vision/specs/superpowers-port.md` (the authoritative coverage
  mapping + pressure→structure thesis; the doc this spec must finish),
  `research/capability-specs/capability-catalogue.md` (the per-skill `done/partial/
  planned` status), `research/capability-specs/FINDINGS.md` (the "marketplace root
  is an aggregator" finding driving Open Question 1).
