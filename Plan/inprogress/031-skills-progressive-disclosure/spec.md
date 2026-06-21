---
spec_id: "031"
slug: skills-progressive-disclosure
status: draft
state: inprogress
last_updated: 2026-05-31
owner: "@agency"
depends_on: [016, 023, 029, 030]
affects:
  - agency/capability.py                      # +SkillDoc + WalkerSkills dataclasses; CapabilityBase attrs
  - agency/engine.py                          # +skill_list substrate tool; +SkillDoc bootstrap validation
  - agency/install.py                         # generate() delegates per-cap; +--dry-run; +emit fns
  - agency/skill_emit.py                      # NEW — emit_skill / emit_references / emit_bash_wrappers
  - agency/cache.py                           # NEW — atomic skill-cache.json read/write
  - agency/templates.py                       # +CAPABILITY_SKILL_MD, VERB_REFERENCE_MD, BASH_WRAPPER_SH, HELP_INDEX_MD, RULE_VERSION
  - agency/capabilities/plugin.py             # +author_reference, +lint_skill_doc rules
  - agency/capabilities/skill/__init__.py     # NEW (folder-form) — re-exports SkillCapability
  - agency/capabilities/skill/_main.py        # NEW — current/submit/done verbs
  - agency/capabilities/skill/_walker.py      # NEW — graph-state recovery for SkillRun
  - agency/capabilities/reflect.py            # +skill_doc (worked example, panel F-12)
  - agency/capabilities/branch.py             # +skill_doc
  - agency/capabilities/workspace.py          # +skill_doc
  - agency/capabilities/dogfood.py            # +skill_doc
  - agency/capabilities/gate.py               # +skill_doc
  - agency/capabilities/skill_generator.py    # +skill_doc
  - agency/capabilities/subagent.py           # +skill_doc
  - agency/capabilities/develop.py            # +skill_doc; DEV_SKILLS → walker_skills.schemas
  - agency/capabilities/delegate.py           # +skill_doc; _DISPATCH_DECISION_SKILL → walker_skills.schemas
  - agency/capabilities/jules.py              # +skill_doc; JULES_SKILLS → walker_skills.schemas
  - docs/vision/SKILL-CONTRACT.md             # NEW — the §16 doctrine doc
  - skills/                                   # rm hand-authored; generator owns the namespace
  - bin/                                      # +agency-<cap>-<verb> wrappers (chmod +x)
  - tests/test_skill_doc_validation.py        # NEW — bootstrap validation; lint_skill_doc rules
  - tests/test_skill_emit.py                  # NEW — emit_skill/emit_references/emit_bash_wrappers
  - tests/test_skill_cache_atomic.py          # NEW — TEST-3 atomic-kill survival
  # tests/test_skill_contract_e2e.py          # deferred to Spec 163 (progressive-disclosure-closure); subagent E2E discipline
  # tests/test_skill_mcp_surface.py           # deferred to Spec 163; skill_list / capability_skill_*
estimated_jules_sessions: 0
domain: substrate
wave: 4
---

# Spec 031 — Skills as Progressive Disclosure

## Why

A fresh agent (Jules, a teammate, a future Claude session) walks into a repo with the agency plugin installed and today has to read `agency/capabilities/*.py` to learn what each capability does and which verbs exist. The plugin's only auto-generated skill is `skills/help/SKILL.md` — a single ~1000-word file that dumps the capability map without per-capability triggers, examples, or references. Heavy reference reading per first contact ≈ 5–20 KB of source.

**Goal:** the MCP server generates skill files that follow the superpowers writing-skills discipline (CSO + progressive disclosure + Iron Law) AND the agency's own patterns (templates / schemas / lint), so committing the generated files is enough — pointing Jules (or any fresh agent) at `skills/<capability>/SKILL.md` replaces the source dive. Net effect: ≤500 words upfront per capability + ≤2 KB reference per verb fetched on demand.

The work breaks into three structural changes plus a doctrine doc:

1. **Capability core becomes self-describing for its skill** — every `CapabilityBase` subclass declares a `SkillDoc` (rendering metadata) and an optional `WalkerSkills` (the existing phase-graph schemas, lifted out of scattered dict literals into the owning capability folder).
2. **Generation pipeline** — `install.generate(engine)` delegates per-capability to `skill_emit.emit_skill / emit_references / emit_bash_wrappers`, gated by `lint_skill_doc` in block mode + an idempotency cache that regenerates only when a capability's hash changes.
3. **MCP wire surface for the walker** — `skill_list` (engine substrate, no `intent_id`) for discovery; `capability_skill_current / submit / done` on a new `skill` capability for walking (state recovered from the graph between calls).

Plus the §16 doctrine doc (`SKILL-CONTRACT.md`) that defines what every skill MUST expose to its caller (when to call, which verb, what it mutates, how to recover, where to fetch heavy reference).

## Done When

### A. Capability core extension

- [ ] `agency/capability.py` ships `SkillDoc` dataclass: `{description, overview, triggers, canonical_example, red_flags, required_subskills, verb_briefs}` — rendering metadata only.
- [ ] `agency/capability.py` ships `WalkerSkills` dataclass: `{schemas}` — the existing phase-graph dict shape, lifted out of `OntologyExtension.skills`. `OntologyExtension.skills` becomes the merge target both feed into.
- [ ] `CapabilityBase` gains class-level `skill_doc: ClassVar[SkillDoc | None] = None` and `walker_skills: ClassVar[WalkerSkills | None] = None`.
- [ ] `Engine.__init__` validates at bootstrap (after the extend loop): any capability with `≥1` verb but `skill_doc is None` raises `ValueError` naming the offending capability and pointing at the reflect reference shape.

### B. Lint extension (`plugin.lint_skill_doc`)

- [ ] `plugin.lint_skill_doc(cap_name, doc, verbs) → {ok, violations: [{rule, message}]}` enforces 9 rules (§17 in design): `description-trigger-first`, `description-no-workflow-summary`, `overview-no-workflow-summary`, `triggers-named-symptoms`, `triggers-count` (2–5), `example-uses-real-verb`, `red-flags-required` (≥1 if ≥3 verbs), `red-flags-format` (each item contains `→` or ` - `), `verb-briefs-resolve` (all keys are real verbs).
- [ ] `lint_skill_doc` runs PRE-EMIT in `skill_emit.emit_skill`; failure aborts install with structured error.

### C. Templates (new in `templates.py`)

- [ ] `CAPABILITY_SKILL_MD` template — frontmatter + body shape per §6 (revised); leads with `<!-- agency-generated: vN -->` marker.
- [ ] `VERB_REFERENCE_MD` template — Tier-A reference body shape per §6.
- [ ] `BASH_WRAPPER_SH` template — wrapper per §21 worked example (JSON-via-Python build, `--` terminator, error trap).
- [ ] `HELP_INDEX_MD` template — thin help SKILL.md per §6 (revised).
- [ ] `RULE_VERSION: int = 1` constant — bumped when template shape changes; participates in `_capability_hash` so a bump invalidates the cache.

### D. Emit pipeline (`agency/skill_emit.py`)

- [ ] `emit_skill(cap_name, doc, verbs) → dict[str, str]` returns `{skills/<cap>/SKILL.md: <rendered>}` after running `lint_skill_doc`. Renders auto-region (verb table + Tier B anchors) within the ≤200-word auto budget (NFR-1 split).
- [ ] `emit_references(cap_name, verbs) → dict[str, str]` returns `{skills/<cap>/references/<verb>.md: <rendered>}` for every Tier-A verb. Skips Tier-B (those render as anchors inside SKILL.md, handled by `emit_skill`).
- [ ] `emit_bash_wrappers(cap_name, verbs) → dict[str, str]` returns `{bin/agency-<cap>-<verb>: <rendered>}` for every verb. Mode `0o755` set by `install.write`.
- [ ] `_capability_hash(cap, rule_version) → str` returns sha256 of `cap.name + sorted([(verb, role, fn.__doc__, str(inspect.signature(fn))) for verb, spec in cap.verbs.items()]) + rule_version`. Stable across runs.
- [ ] `_classify_tier(verb_fn) → "A" | "B"` per §5 Gherkin (all three markers non-empty → A; `(terminal)`/`(none)` in `chain_next` counts as A; anything missing/empty → B).

### E. Cache (`agency/cache.py`)

- [ ] `cache.peek(cache_dir, cap_name, hash_) → dict | None` returns cached `{hash, files: [paths]}` if hash matches, else None.
- [ ] `cache.commit(cache_dir, cap_name, hash_, files) → None` writes `<dir>/skill-cache.json.tmp` then `os.replace` to `skill-cache.json` (atomic).
- [ ] **TEST-3:** `test_skill_cache_atomic.py` simulates `commit` interrupted between `tmp` write and `os.replace`; subsequent `peek` returns None (no corrupt JSON crashes); next emit regenerates cleanly.

### F. Install integration

- [ ] `install.generate(engine)` iterates `engine.registry.names()`; per-cap calls `cache.peek` → emit pipeline → `cache.commit`.
- [ ] `install.main(...)` accepts `--dry-run` flag; prints would-write paths + per-file lint result; exit 0 iff all lints pass.
- [ ] `install.write(root)` `chmod +x` every emitted `bin/agency-*` file; on `chmod` failure (RO mount) logs warning + continues (per §8a failure-modes table).
- [ ] Help skill becomes the thin index per §6 (revised): `skills/help/SKILL.md` ≤200 words with inline capability list; `skills/help/quickstart.md` carries the MCP + bash quickstart bodies.

### G. Engine substrate — `skill_list`

- [ ] `engine.py::build_mcp` registers `skill_list(query: str = "") → {skills: [{name, kind, capability, brief, phase_count, gate_at}], total}` as a substrate tool (no `intent_id`, like `agency_welcome`).
- [ ] Brief ≤60 chars per skill. Total payload ≤1 KB for ≤20 skills.

### H. `skill` capability folder

- [ ] `agency/capabilities/skill/__init__.py` re-exports `SkillCapability(CapabilityBase)`; folder-form auto-discovered per Spec 016 Phase 3.
- [ ] `agency/capabilities/skill/_main.py` defines three verbs:
  - `current(name) → {phase, phase_name, produces, inputs, gate, status, references}` (role=transform, requires intent_id)
  - `submit(name, outputs, confirmed=False) → {status, phase, blocked_on?, next_phase?}` (role=act, requires intent_id)
  - `done(name) → {done, last_phase?, phase_count?}` (role=transform, requires intent_id)
- [ ] `agency/capabilities/skill/_walker.py::resume(memory, intent_id, skill_schema) → SkillRun` reconstructs walker state from the graph: queries max-index Phase node serving the intent with skill=name; if none → `i=0`; checks for paused Gate node → `input-required`.
- [ ] `SkillCapability.skill_doc` declared (the worked example for the new capability eats its own dogfood).

### I. Migration

- [ ] `agency/capabilities/reflect.py` gets `skill_doc = SkillDoc(...)` per §21 worked example. This is the first migration + serves as the reference template for the others.
- [ ] Remaining capabilities get `skill_doc`: branch, workspace, dogfood, gate, skill_generator, subagent (6 trivial). The 4 heavy capabilities (develop, plugin, delegate, jules) also get `walker_skills = WalkerSkills(schemas={...})` with their existing dict literals migrated.
- [ ] `JULES_SKILLS` moves from `_jules_skills.py` into `jules.JulesCapability.walker_skills.schemas` (or stays as a `_skills.py` sibling that the class imports and assigns — author's preference, but the source of truth is the attribute on the class).

### J. Cleanup

- [ ] Remove hand-authored files under `skills/` (the 11+ pre-existing SKILL.md files). Generator now owns the namespace.
- [ ] `python -m agency.install` runs cleanly on a fresh tree; emits `skills/<cap>/SKILL.md` + `skills/<cap>/references/<verb>.md` (Tier A) + `bin/agency-<cap>-<verb>` for every capability.

### K. Discipline test (TEST-2 — the Iron Law proof)

- [ ] `tests/test_skill_contract_e2e.py` dispatches a subagent with `tools=[Read]` against a sandboxed copy of `skills/reflect/`. Task: "call `capability_reflect_note` with scope='observation' and text='X' against intent_id 'intent:abc'." Subagent is FORBIDDEN to read any file outside `skills/reflect/`. Test passes iff the constructed call has all required parameters with correct values.
- [ ] Repeat for at least 2 more capabilities (jules, develop) — the discipline test must generalize.

### L. Doctrine doc

- [ ] `docs/vision/SKILL-CONTRACT.md` ships the §16 five-obligation contract. CORE.md references it from the §Skills/Lifecycle section.

## Files

See `affects:` list above.

## Open Questions

- **OQ-1 (RESOLVED 2026-05-31).** Surface placement → Hybrid (skill_list substrate + skill capability for walk verbs).
- **OQ-2 (RESOLVED 2026-05-31).** Reference attachment → Tier A files in `references/<verb>.md`, Tier B anchors in SKILL.md.
- **OQ-3 (RESOLVED 2026-05-31).** Wrapper safety → JSON built in Python, piped to `execute --code`. Per §21 example.
- **OQ-4 (RESOLVED 2026-05-31).** Help skill → inline capability list + sibling `quickstart.md`.
- **OQ-5 (RESOLVED 2026-05-31).** Hand-authored coexistence → generator owns `skills/` namespace; hand-authored removed in this PR.
- **OQ-6 (RESOLVED 2026-05-31).** Marker syntax → `<!-- agency-generated: vN -->` (markdown comment, matches `# agency-scaffold: vN` convention namespace).
- **OQ-7 (DEFERRED — F-5 from panel).** `SkillDoc.version` field — YAGNI for v1; add additively when needed.

## Evidence

- Spec 016 (capability-authoring-doctrine, `status: complete`) — Phase 3 `8a5a45d` ships folder-form `discover()` that auto-finds `agency/capabilities/<name>/`.
- Spec 023 (adaptive-disclosure) — `parse_slices` already returns `{brief, inputs, returns, chain_next, body}`; this spec consumes those slices for the Tier-A reference rendering.
- Spec 029 (MCP bootstrap + self-explain) — `agency_welcome` / `agency_install` / `intent_bootstrap` / `agency_doctor` substrate tools shipped in PR #14; `skill_list` joins them as a substrate-style fifth.
- Spec 030 (key clarity + doctor + stateful welcome) — `agency_welcome` carries `state: fresh|in_progress`; this spec adds `skills_index_path` to its payload (relative path string, not the full list).
- Superpowers writing-skills discipline (`~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/skills/writing-skills/SKILL.md`) — the CSO rules + Iron Law this spec ports.
- Subagent reports captured in this design session — skill implementation audit + install pipeline audit + gap analysis vs writing-skills (see `.agency/session.db` reflections under `intent:<this-spec's-id>`).

## Non-goals

- **Hand-authored skill content for `superpowers:writing-skills`-style external skills.** Those live in their own plugin marketplace; this spec only owns the agency-plugin's auto-generated content.
- **A full skill graph (skills as first-class nodes with edges to verbs).** Out of scope. Skills stay dict-in-`OntologyExtension`-merged-from-`WalkerSkills`. A future spec could promote.
- **Cross-skill composition** (e.g. one skill embedding another's phases). Composition is via `**REQUIRED SUB-SKILL:**` markers in the body — Fed-by-Markdown, not by mechanism.

## Followup — Implementation Status (2026-06-12)

**Verdict:** Shipped (largely superseded → Spec 080 + Spec 081).

The progressive-disclosure surface is delivered by Spec 080 (every cap
drops in a complete Agent Skill; SkillDoc DERIVED from the module
docstring) + Spec 081 (walkable usage-skill per cap; phase-graph
clusters verbs by role). The remaining closure of the original 031
scope is tracked by Spec 163 (progressive-disclosure-closure, wave-2).

### Done

- **A. Capability core extension** — `SkillDoc` + `WalkerSkills` exist on
  every shipped capability (Spec 080).
- **B–H. Lint + Templates + Emit + Cache + Install + Engine substrate +
  skill capability folder** — surface delivered via Spec 080/081
  pipeline (the discipline-via-derived-content path won over the
  hand-authored skill-as-folder path).

### Still (absent; superseded by Spec 163)

- `tests/test_skill_contract_e2e.py` — absent; subagent end-to-end discipline test not yet written; superseded by Spec 163.
- `tests/test_skill_mcp_surface.py` — absent; `skill_list` / `capability_skill_*` surface coverage not yet written; superseded by Spec 163.

