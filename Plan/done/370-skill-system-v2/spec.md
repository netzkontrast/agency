---
spec_id: "370"
slug: skill-system-v2
status: done
state: done
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [1, 3, 8]
depends_on: ["016", "023", "031", "032", "047", "080", "081", "148", "286"]
domain: skills
wave: program-master
---

# Spec 370 — Skill & Command system v2 (the generation overhaul) — MASTER

> Owner directive (2026-06-20): *"Rethink how we generate skill files AND commands.
> First a Set of Rules describing what skills ideally contain so every part of the
> system works together; then design schemas, per-capability templates and
> lifecycle so skills are OPTIMIZED content, not shallow docstring extracts. The
> schema must be much more powerful and flexible than anything so far. A capability
> must be able to register and design its own skills — but first, capabilities (+
> their code specs) should auto-generate GOOD skills. This needs MCP-server
> sampling with proper skill-creator prompts. This is several specs — it touches
> every part of the plugin."*

This is the **master** for a program (children 371–378). It is the single source
for *how the skill/command generation overhaul composes*; promoted children win
within their slice once shipped (047/307/338 precedent).

## Why — the verified defect

Agency treats a skill as a **rendered view of a docstring** and a phase as a
**structural shell**. Neither carries teaching content, so generated skills are
thin by construction. Evidence (verified via codegraph, 2026-06-20):

- **Phase** (`skill.py:phase`) = `{index,name,produces,gate?,verbs?,sample?,…}` —
  no content fields. `SkillRun.current()` surfaces only `{index,name,produces,gate}`,
  so a walking agent never receives instructions.
- **Source** (`disclosure.parse_slices`) — `brief` = the first *sentence* of the
  docstring → truncation (frugal's `description` is cut mid-sentence).
- **Template** — one generic `render/capability-skill.md` (+ a second path
  `templates.SKILL_MD`); every skill renders to the same shape.
- **Schema** (`plugin/schemas/skill-md.json`) = `{name,description,body}` — enforces
  nothing about usefulness, so thin bodies + literal `_(Tier B…)_` stubs ship.
- **Commands** (`install._generate_per_skill_commands`) — top-12 identical
  "walk the skill" stubs.

A skill should (a) be *found* at the right moment and (b) *teach the agent to do
the thing*. Today's output fails both. **No schema tweak alone fixes it — the data
model is the problem.** The assembled best-practices (R1–A7) are in
[`reference/SKILL-BEST-PRACTICES.md`](reference/SKILL-BEST-PRACTICES.md).

## Design — the v2 model

### 1. Data model: a powerful, layered, committed schema (the single source)
A typed `Skill`/`Phase` schema (small required core per **type**, optional rich
extensions — YAGNI on the rest) expresses everything R1–A7 demand (type · per-phase
degrees-of-freedom · one-deep reference tree · phases with
`goal`/`instructions`/`example`/`done_when` · workflow checklists · feedback loops ·
i/o example pairs · per-verb provenance trace · per-field `source` · `owner` · eval
scenarios · a source-hash stamp). It lives as a **committed per-capability data
file** (`agency/capabilities/<cap>/skill.yaml`) + the 3 pillar skills +
capability-authored skills (A6). The folder carries its skill data ⇒ the drop-in
bar holds.

### 2. Skill set (owner-decided)
- **3 pillar skills** — `intent`, `lifecycle`, `memory` (the three non-capability
  concepts of CORE.md's four).
- **1 skill per capability** (the Capability pillar), references-heavy.
- **Capability-authored skills** (A6) — a cap may ship/override richer skill data.

### 3. Generation model (the critical-thinking correction — A7)
**Sampling is an authoring-time generator, NOT an install-time renderer.**
- **Authoring-time** (`skill.author`/`regenerate`, dev-invoked): MCP-sampling +
  per-type skill-creator prompts, **grounded in code + governing spec(s) + ontology
  + the R1–A7 rules as system prompt** → fills the schema → validated against the
  live registry + type schema → reviewed → **committed**.
- **Install-time** (`install.generate`): **deterministic** render of the committed
  schema via per-type templates → self-contained `SKILL.md` (workflow/phases inline,
  A1) + one-deep references (heavy detail) + the SAME phases power the walk (A2).
  No LLM ⇒ `install regen` stays diff-free (A7); CI/Jules/offline safe.
- **Staleness gate** (`check-drift`): `hash(cap code + spec + prompt-version)` vs the
  committed skill's stamp → flags *"re-author"* — never an auto-rewrite.

### 4. Commands v2 (owner-decided)
Curated few — `/agency`, `/agency-onboard`, `/help` + one per **discipline/pillar**
— each command body **launches its skill** (inline instructions or the walk). Drop
the top-N `/agency-<every-skill>` explosion.

### 5. Enforcement (owner-decided: graduated)
Per-type JSON schemas + the `Phase` schema validated at `install.generate` AND
`check-drift`; lint extends `lint_skill_doc` (per-type completeness, phase
`instructions` non-empty = self-containment, R1/R3/R4). **Graduated:** warn
repo-wide; block for new/changed skills + the pillars + frugal as first exemplars;
flip to repo-wide block once the 33 are migrated.

## Children (the program — build-ordered)

| # | Spec | Scope | Key files |
|---|---|---|---|
| 371 | **phase-skill-schema** | the powerful layered `Phase`+`Skill` JSON schema; typed parse; committed per-cap `skill.yaml`; back-compat | `skill.py`, `_skill_parse.py`, `capability.py`, schemas/ |
| 372 | **phase-single-source** | `SkillRun.current/submit` + `develop.skill_walk` surface `goal/instructions/example`; walk↔file parity | `skill.py`, `develop/_main.py` |
| 373 | **per-type-templates-renderer** | pillar/capability/discipline templates w/ variables; deterministic self-contained render; kill truncation | `skill_emit.py`, `render/`, `templates.py`, `disclosure.py` |
| 374 | **skill-creator-sampling** | authoring-time `skill.author`/`regenerate`: MCP-sampling, per-type prompts, code+spec grounding, registry-validation, staleness stamp | new cluster, `_host_llm.py`, `skill_generator` cap |
| 375 | **pillar-skills** | author `intent`·`lifecycle`·`memory` concept skills + their generation path | new pillar source, `install.py`, ontology |
| 376 | **command-v2** | curated command set; launch-not-stub; drop top-N | `install.py`, `author_command`, `command-md.tpl` |
| 377 | **skill-lint-enforcement** | per-type + phase-instruction + self-containment lint; validate at generate + check-drift; graduated warn→block | `lint.py`, `check-drift`, `SKILL-CONTRACT`→v2 |
| 378 | **capability-skill-migration** | author phase/judgment content per cap (A6 path); flip to block; docs/doctrine v2 | every capability + docs |

**Build order:** 371 → 372 → 373 → 374 → (375 ‖ 376) → 377 → 378. 371–374 are the
substrate; 378 is the long tail. Each child is independently shippable.

## Cross-cluster coherence (Spec 047)
Skills/commands span clusters C01–C13; this program touches the **generation
substrate** they all share, so it lands as a cross-cutting program, not in one
cluster. Coherence risks: (1) the walk (`develop`, C03) vs the rendered file must
not diverge → A2 single-source; (2) the plugin authoring cap (C12) `author_skill`
path must converge onto the same schema/renderer (no third path); (3) the lint
(C04) must gate without blocking the existing 33 until migrated → graduated (377).

## Acceptance (program-level)
- **C1** A `Skill`/`Phase` schema exists, is strictly validated, and is powerful
  enough to express R1–A7 (371).
- **C2** A walked phase AND the rendered SKILL.md deliver the SAME instructions from
  ONE source (372); a read-only agent can follow a skill without skill-walk (A1).
- **C3** `install.generate` is deterministic (no LLM; `install regen` diff-free);
  the skill-creator's LLM output is authoring-time + committed (A7).
- **C4** Skill text is optimized (no docstring truncation, no `_(Tier B…)_` stubs);
  every referenced verb exists in the live registry.
- **C5** 3 pillar skills + per-cap skills + the capability-authored path (A6) ship.
- **C6** Commands are curated (entry + per discipline/pillar); no top-N explosion.
- **C7** Per-type schema + self-containment lint gate generation, graduated.

## Decisions (resolved with the owner, 2026-06-20)
1. Type-classified strict schema (pillar/capability + reference/technique/discipline).
2. Hybrid sourcing: derive mechanical + author judgment + LLM-sample.
3. Graduated rollout (warn → block).
4. Skill set = 3 pillars + 1/capability + capability-authored (A6).
5. Commands = curated few (entry + per discipline/pillar).
6. Self-contained skills (A1) + phase = single source (A2).
7. **Sampling = authoring-time, committed; deterministic install; staleness gate (A7).**

## Followup — Implementation Status (2026-06-20)
**Drafted (master).** Born from the owner's "rethink skill+command generation"
directive after the ponytail port exposed that auto-generated skills are shallow
docstring extracts. Grounded via codegraph (current-state map) + assembled
best-practices (R1–A7) + a critical-thinking/brainstorm pass that corrected the
sampling model from install-time to authoring-time (the reproducibility landmine).
No code yet — this master + children 371–378 are the design record.
