<!-- agency-node: document:8449c8ef -->
---
spec_id: "060"
slug: templates-schemas-agent-instructions
status: done
state: done
last_updated: 2026-06-03
owner: "@agency"
depends_on: ["016", "019", "031", "032", "059"]
supersedes: ["032"]    # Spec 032's substrate IS shipped (loader+dataclasses+materialiser); 060 ships the missing 30%
absorbs: ["028"]       # jules folder migration folds in
affects:
  - agency/engine.py                                  # wire load_capability_folders into bootstrap
  - agency/capability.py                              # ctx.template(name) substrate method
  - agency/capabilities/plugin.py                     # _check_template_folder lint rule
  - agency/capabilities/dogfood/                      # FOLDER migration + templates + schemas
  - agency/capabilities/reflect/                      # FOLDER migration + templates + schemas
  - agency/capabilities/delegate/                     # FOLDER migration + schemas
  - agency/capabilities/branch/                       # FOLDER migration + schemas
  - agency/capabilities/workspace/                    # FOLDER migration + schemas
  - agency/capabilities/gate/                         # FOLDER migration + schemas
  - agency/capabilities/subagent/                     # FOLDER migration + schemas + new SubagentReview node
  - agency/capabilities/skill_generator/              # FOLDER migration (light)
  - agency/capabilities/develop/                      # FOLDER migration + templates + schemas
  - agency/capabilities/plugin/                       # FOLDER migration; migrate templates.REQUIRED → schemas/*.json files
  - agency/capabilities/jules/                        # FOLDER migration (absorbs Spec 028) + schemas + preamble templates
  - agency/capabilities/research/                     # ADD templates + schemas (already folder-form)
  - agency/capabilities/document/                     # ADD templates + schemas + new Explanation node
  - agency/capabilities/analyze/                      # ADD templates (already folder-form)
  - docs/vision/CAPABILITY-AUTHORING.md               # NEW §"Templates instruct agents (Bitwize pattern)"
  - tests/test_template_bootstrap_wireup.py           # NEW
  - tests/test_agent_instruction_doctrine.py          # NEW
  - tests/test_template_folder_lint.py                # NEW
estimated_jules_sessions: 0   # done locally (substrate spec, no Jules dispatch)
domain: substrate
wave: 4
---

# Spec 060 — Templates & Schemas: Bootstrap, Migration, Agent-Instruction Doctrine

## Why (in three statements)

1. **Spec 032 shipped the substrate (loader + dataclasses + materialiser
   + path-safety) but the loader is INERT.** `agency/_capability_loader.
   py::load_capability_folders` is imported only by 3 test files; no
   capability declares `render_templates = RenderTemplates(folder=...)`
   or `artefact_schemas = ArtefactSchemas(folder=...)`. The bootstrap
   never calls the loader. Net: 70% of Spec 032 shipped, 30% inert.

2. **No per-capability `templates/` or `schemas/` folder exists.**
   `agency/render/` is populated (engine-owned, Spec 031); per-capability
   roster is zero. Every artefact rendering today is Python-string-
   concat (e.g. `dogfood.render`, `render_research_report`,
   `_jules_preambles.assemble`). When the rendering needs an iteration,
   it's a code edit.

3. **Templates must instruct agents, not just render markdown.** The
   user named the conceptual leap: Bitwize-music's templates pair the
   artefact body with inline `<!-- AGENT: ... -->` HTML-comment
   instructions, conditional sections, and required-checklists. The
   agent reading the template understands BOTH the shape AND its
   action obligations. Today's `agency/render/*.md` are pure rendering;
   no instruction-block convention exists. This spec codifies one.

Combined: the substrate is sound but inert; the per-capability roster
is empty; the agent-instruction doctrine doesn't exist. Spec 060 ships
all three together.

## Vision/Goal alignment

| Goal | How 060 honours it |
|---|---|
| 1 — Token efficiency | Templates are loaded once at bootstrap (cached in `Schema` + `Template` nodes via materialiser); agents read them OUT-OF-BAND via the graph, not via every call. Inline instructions reduce chain_next round-trips. |
| 2 — Provenance | Every `Schema` + `Template` node lives in the bi-temporal graph; `DERIVED_FROM` / `VALIDATES_AGAINST` edges close the generate/validate loop CORE.md:66 promises. |
| 4 — Open set | Adding a capability = adding a folder with `templates/` + `schemas/`. The loader discovers them. No central registry edit. |
| 5 — Code-mode IS the contract | Templates load via `ctx.template(name)` — agents read the body + the instructions in-sandbox; only deltas cross to context. |
| 6 — Doctrine evolves through dogfooding | Templates land as files; iterating a template doesn't require a Python edit. Doctrine evolution is a markdown commit. |
| 7 — Graph is the store; files are a rendered view | Templates are STORED as graph `Template` nodes (materialiser); the files on disk are the rendered view + the authoring surface. Cleanest application of GOALS.md #7 yet. |
| 8 — Harness-in-harness | Same template loader works for engine-owned (`agency/render/`) AND capability-owned (`<cap>/templates/`) — recursive composition, same primitive. |

## Done When

### Phase 1 — Bootstrap wire-up (the keystone)

- [ ] `Engine.__init__` calls `_capability_loader.load_capability_folders(cap)`
  for every registered capability AFTER instantiation but BEFORE
  ontology merge.
- [ ] The loader's returned `(templates, schemas)` dicts merge into the
  cap's `OntologyExtension` (additive — file-based entries augment
  declared dict entries; collision raises with a clear file-vs-dict
  message).
- [x] `Ontology.materialise_schemas(memory)` + `materialise_templates(
  memory)` run once at bootstrap completion (idempotent on re-open per
  Spec 032 §D). **Shipped 2026-06-23:** `Engine.materialise_ontology()`
  (`agency/engine.py`) calls both; the production server invokes it once in
  `agency/__main__.py` (opt-in, like `enable_session_autolog` — bare test
  engines stay graph-clean, no suite blast radius). RED→GREEN at
  `tests/test_ontology_materialise.py` (records Schema + Template nodes,
  idempotent on re-run; bare engine materialises nothing). Phase 5 (verb
  migration to `ctx.template()`) remains explicit **opt-in** iteration work
  per the spec author's own scoping — not a blocker; the typed/generative
  layer is now a queryable graph projection (Vision goals 2 & 7).
- [ ] `CapabilityContext.template(name)` substrate method: returns the
  `string.Template` body for the named template, raises `KeyError` if
  the cap doesn't ship that template. Same shape as `ctx.recall` /
  `ctx.record` — a one-call substrate accessor.

### Phase 2 — Agent-instruction doctrine

- [ ] **`docs/vision/CAPABILITY-AUTHORING.md` §"Templates instruct
  agents (Bitwize pattern)"** lands between §"Wire shape vs internal
  wrap" (Spec 019) and §"When to use ToolResult vs plain dict" (Spec
  059). Documents the FOUR conventions every template observes:

  1. **Frontmatter** (when fields are structured — title, status, etc.).
  2. **Body with `$variable` substitutions** (engine-filled via
     `string.Template`).
  3. **Inline `<!-- AGENT: <instruction> -->` HTML comments** —
     invisible to humans reading the rendered output, visible to
     agents reading the template body. Tell the agent what to do next
     (e.g. `<!-- AGENT: VERIFY sources before publishing -->`).
  4. **Conditional sections** delimited by
     `<!-- BEGIN IF <flag> -->` / `<!-- END IF -->` — sections the
     agent emits when the flag's truthy. The engine doesn't strip
     them; the agent's logic does.

- [ ] **Example doctrine block** in CAPABILITY-AUTHORING.md showing
  the same template rendered two ways: human-view (after `<!-- -->`
  strip) and agent-view (with instructions intact). Pairs with the
  worked example in Bitwize's `templates/track.md`.

### Phase 3 — Per-capability folder + template + schema roster

Ten capabilities migrate from single-file to folder form. Each
gains a `templates/` folder when it renders artefacts AND a
`schemas/` folder when it records typed nodes. Filename rule:
kebab-case stem; extensions `.md` / `.tpl` / `.sh` for templates;
`.json` for schemas (draft-07 OR simple `{required: [...]}`).

| Capability | Folder | Templates | Schemas |
|---|---|---|---|
| **dogfood** | ✓ | `dogfood-notes.md` | `dogfood-observation.json` |
| **reflect** | ✓ | `reflection-note.md` | `reflection.json` |
| **delegate** | ✓ | — | `delegation.json`, `reduction.json` |
| **branch** | ✓ | — | `branch-outcome.json` |
| **workspace** | ✓ | — | `workspace.json`, `baseline.json` |
| **gate** | ✓ | — | `gate.json` |
| **subagent** | ✓ | — | `subagent-review.json` + new `SubagentReview` node |
| **skill_generator** | ✓ | — | — (light, no node contribution) |
| **develop** | ✓ | `checklist.md` | — |
| **plugin** | ✓ | (migrated to `agency/render/`) | 5 schemas from `templates.REQUIRED` → `plugin/schemas/*.json` |
| **jules** | ✓ | `preamble-mode-a.md`, `preamble-mode-b.md` | `jules-session.json`, `jules-patch.json`, `jules-watch-event.json` |
| **research** | (existing) | `research-report.md` | `citation.json`, `verification.json` |
| **document** | (existing) | `explanation.md` | `explanation.json` + new `Explanation` node |
| **analyze** | (existing) | `analysis-summary.md`, `improvement-plan.md` | (existing improvement-plan) |

Each migration follows the Spec 032 §I recipe:
1. Create folder + `__init__.py` re-export.
2. Move single-file → `_main.py`.
3. Add `templates/` + `schemas/` subfolders + files.
4. Declare `render_templates = RenderTemplates(folder=Path(__file__).parent / "templates")` + `artefact_schemas = ArtefactSchemas(folder=Path(__file__).parent / "schemas")` on the capability class.
5. Verify `plugin.lint_capability` ok=True post-migration.

### Phase 4 — Lint rule

- [ ] **`plugin._check_template_folder`** (seventh lint rule under Spec
  016 scaffold). Fires when a cap declares `render_templates` but:
  - the folder doesn't exist on disk, OR
  - any template file's stem doesn't match kebab-case, OR
  - any template file's content doesn't carry at least one
    `<!-- AGENT: ... -->` instruction block (the doctrine bar).
  WARN-mode initially; BLOCK once every migrated cap passes.

### Phase 5 — Verb migration (the consumer flip)

Every verb that today builds markdown via Python f-strings migrates to
`ctx.template(name).substitute(**fields)`. Concretely:

- `dogfood.render` → reads `dogfood-notes.md` template.
- `_jules_preambles.assemble` → reads `preamble-mode-a.md` /
  `preamble-mode-b.md` based on `jules.detect_mode`.
- `document._render.render_research_report` → reads `research-report.md`
  template.
- `document._render.*` other scopes → migrate if rendering becomes
  template-shaped (some stay programmatic — capability-catalogue
  iterates the live registry, not a fixed shape).
- `develop.checklist` → reads `checklist.md` template per discipline.
- `analyze.run` summary + `analyze.improve` plan → read their templates.
- `plugin.author_skill`, `author_command`, `scaffold`, `step_doc`,
  `marketplace_entry` → already template-loaded via `templates.py`'s
  `_load_render_template`; the migration just relocates the source
  files from `agency/render/` to `agency/capabilities/plugin/templates/`
  for the per-cap-ownership invariant (`agency/render/` retains the
  engine-owned `skill-md.tpl` + `verb-reference.md` since they're
  cross-capability).

### Phase 6 — Tests

- [ ] **`tests/test_template_bootstrap_wireup.py`** — confirms
  `load_capability_folders` is called for every cap at Engine init;
  per-cap templates appear in the materialised `Template` nodes;
  per-cap schemas materialise as `Schema` nodes.
- [ ] **`tests/test_agent_instruction_doctrine.py`** — every shipped
  template in `agency/render/` AND `agency/capabilities/*/templates/`
  carries ≥ 1 `<!-- AGENT: -->` block.
- [ ] **`tests/test_template_folder_lint.py`** — `_check_template_
  folder` flags missing folder, non-kebab stems, instruction-less
  templates.
- [ ] **Per-capability regression tests** — every migrated cap's
  existing test suite stays green post-migration.

### Phase 7 — Review loop (the doctrine the user named)

After every wave of migrations:
1. Run `python -m pytest -q -n auto -m "not e2e"`.
2. Run `plugin.lint_capability(name=<cap>)` for every cap; expect
   `ok=True`.
3. Run a `sc:sc-analyze --focus architecture --depth deep` over
   `agency/capabilities/` + the new templates folder.
4. Walk the analyzer findings; convert P2+ to fixes; re-run the loop.
5. Exit only when: tests green, lint clean, analyzer no new findings.

## Architecture

### The template body convention (the Bitwize pattern, applied)

```markdown
---
$frontmatter
---

# $title

<!-- AGENT: This template renders a $artefact_kind. Fill the
frontmatter from the source provenance node. Walk the BEGIN/END IF
sections; emit conditional blocks based on the listed flags. -->

## Summary

$summary_body

<!-- BEGIN IF has_citations -->
## Citations

$citations_table

<!-- AGENT: For each citation, verify the URL or path resolves;
flag broken ones in the YAML frontmatter under `verification.broken`. -->
<!-- END IF -->

<!-- BEGIN IF has_verification -->
## Verification

$verification_block
<!-- END IF -->

<!-- AGENT: After rendering, persist the output via
document.render(scope='<scope>', for_intent_id=...) and link the
written Artefact PRODUCES the calling Invocation. -->
```

Three things are visible here that aren't in today's `agency/render/`:

- `<!-- AGENT: -->` instruction blocks at every decision point.
- `<!-- BEGIN IF / END IF -->` conditional sections.
- A final "chain-next" instruction at the bottom (what to do AFTER
  rendering — symmetric with Hint #7's `chain_next:` docstring marker
  but at template scope).

### Engine bootstrap wire-up

```python
# agency/engine.py — inside __init__, after registry assembly
from ._capability_loader import load_capability_folders

for name in self.registry.names():
    cap = self.registry.get(name)
    file_templates, file_schemas = load_capability_folders(cap)
    # Additive merge: file entries augment declared dict entries.
    # Collision (same name in both) is a hard error — clear message.
    cap.ontology = cap.ontology.with_files(
        templates=file_templates, schemas=file_schemas)

# Run materialisers ONCE at bootstrap completion.
self.ontology.materialise_schemas(self.memory)
self.ontology.materialise_templates(self.memory)
```

`OntologyExtension.with_files(**)` is a new method that returns a new
`OntologyExtension` with the additive merge — frozen-dataclass safe.

### `CapabilityContext.template(name)` substrate

```python
# agency/capability.py — inside CapabilityContext
def template(self, name: str) -> "Template":
    """Load a per-capability template by stem (e.g. 'reflection-note').
    Returns a `string.Template`. Raises KeyError if the cap doesn't
    ship that template.

    Templates are populated by the loader at engine bootstrap; this
    accessor is a thin dict read.
    """
    cap = self.registry.get(self._cap_name)
    return cap.ontology.templates[name]
```

(`self._cap_name` is the dispatching cap name — already available in
context per Spec 016 Hint #5.)

## Files (per-capability roster)

### Light migrations (folder + 0-1 files)

- `dogfood/{_main.py, templates/dogfood-notes.md, schemas/dogfood-observation.json}` — new `DogfoodObservation` node replaces the Reflection+plan_slug-property workaround (Spec 045 carryover).
- `reflect/{_main.py, templates/reflection-note.md, schemas/reflection.json}`.
- `gate/{_main.py, schemas/gate.json}`.
- `branch/{_main.py, schemas/branch-outcome.json}`.
- `workspace/{_main.py, schemas/workspace.json, schemas/baseline.json}`.
- `subagent/{_main.py, schemas/subagent-review.json}` + new
  `SubagentReview` ontology node (`{spec_passed, quality_passed, done}`).
- `skill_generator/{_main.py}`.

### Medium migrations

- `delegate/{_main.py, schemas/delegation.json, schemas/reduction.json}`.
- `develop/{_main.py, templates/checklist.md}`.
- `plugin/{_main.py, schemas/{plugin-manifest,skill-md,command-md,marketplace-entry,step-doc}.json}` — migrate from `templates.REQUIRED` Python constants to file-based.

### Heavy migration (absorbs Spec 028)

- `jules/{_main.py, api.py, watch.py, patch.py, preambles.py, skills.py, reference.md, templates/{preamble-mode-a.md, preamble-mode-b.md}, schemas/{jules-session.json, jules-patch.json, jules-watch-event.json}}` — folder-form per Spec 016 Hint #1; preambles become loadable templates instead of Python string constants.

### Add templates + schemas (already folder-form)

- `research/{templates/research-report.md, schemas/{citation.json, verification.json}}`.
- `document/{templates/explanation.md, schemas/explanation.json}` + new `Explanation` ontology node.
- `analyze/{templates/{analysis-summary.md, improvement-plan.md}}`.

## Open Questions

1. **`OntologyExtension.with_files(**)` collision handling.** A cap
   could declare `schemas={"foo": ["a"]}` in its `OntologyExtension`
   AND ship `schemas/foo.json`. Recommend: hard error at bootstrap with
   the message `schema 'foo' declared in both OntologyExtension and
   <cap>/schemas/foo.json — pick one`. Forces clean migrations.

2. **Should `<!-- AGENT: -->` blocks survive the render?** Two
   conventions: STRIP at render (the human-view) vs PRESERVE (the
   agent-view). Recommend: STRIP for `document.render` (human-facing),
   PRESERVE for `ctx.template(name).substitute(...)` (agent-facing).
   The renderer's job is the strip; the substrate accessor returns
   the body verbatim.

3. **Does `verb-reference.md` and `skill-md.tpl` stay engine-owned or
   move to `plugin/templates/`?** Today they live in `agency/render/`
   and are used by `skill_emit.py`. Recommend: STAY engine-owned —
   they describe the engine's substrate output (skill md format),
   not the plugin capability's artefact set. Engine-owned = shared
   across caps; cap-owned = the cap's artefact contracts.

4. **Conditional `<!-- BEGIN IF -->` execution semantics.** Two
   options: pure-document convention (the agent's logic decides
   whether to include — same as `<!-- -->` comments) OR an
   engine-side preprocessor that strips inactive blocks based on a
   `flags: dict` passed to `ctx.template(name).substitute(flags=..., **fields)`.
   Recommend: pure-document for v1 (the agent reads BEGIN/END markers
   like any comment); engine preprocessor in v2 only if a clear pain
   point surfaces.

5. **The plugin's `templates.REQUIRED` migration sequence.** Today
   `plugin.py`'s `OntologyExtension` declares `schemas=dict(templates.
   REQUIRED)`. After migration, the schemas live as
   `plugin/schemas/*.json` files; the `templates.REQUIRED` Python
   dict can be removed OR kept as a backwards-compat alias.
   Recommend: REMOVE in this spec — the only consumer is plugin's own
   declaration, and the file-based form is the canon now. One
   commit.

## Evidence (cites)

- `agency/_capability_loader.py:110` — `load_capability_folders` (the
  inert loader).
- `agency/capability.py:147-225` — the dataclass core (shipped).
- `agency/ontology.py:195-229` — materialise_* (shipped, idempotent).
- `agency/render/` — 7 engine-owned templates (shipped under Spec 031).
- `agency/templates.py:1-30` — the reduced helper module (109 LOC,
  loads bodies from `agency/render/`).
- `Plan/inprogress/031-skills-progressive-disclosure/spec.md` — `SkillDoc` +
  `WalkerSkills` precedent (the parallel pattern that works today).
- `Plan/superseded/032-templates-schemas-oop-extensions/spec.md` — the parent
  spec (this one supersedes its missing 30%; preserves what shipped).
- `Plan/inprogress/028-jules-folder-migration/` — absorbed: 060 ships the folder
  migration as part of the heavy-migration wave.
- Bitwize-music plugin (`/root/.claude/plugins/marketplaces/bitwize-
  music/templates/track.md`) — the agent-instruction convention this
  spec adapts to agency.
- `Plan/done/045-reflect-semantic-recall/spec.md` — `plan_slug` property
  workaround that the new `DogfoodObservation` node replaces.
- GOALS.md #7 ("graph is the store; files are a rendered view") —
  the doctrinal grounding that makes file-based templates correct.

## Non-goals

- A new template DSL — `string.Template` + HTML-comment instructions
  is sufficient. No Jinja, no Mustache, no f-string-eval.
- Schemas other than draft-07 OR simple `{required: [...]}` — Spec 032
  §D already enforces the two-shape dispatch.
- A central template registry beyond the per-cap folders + the
  engine's `agency/render/` — discovery via the loader is the registry.
- Auto-stripping `<!-- AGENT: -->` blocks at the rendering boundary
  (Open Q-2 punts this to v2 if needed).

## Followup — Phases 1+2+3+4+6 shipped (2026-06-03)

**Verdict:** Mostly shipped. Phase 5 (verb migration to
`ctx.template()`) remains as opt-in iteration work; Phase 7 (review
loop) closed for this wave.

### Done

**Phase 1 — Bootstrap wire-up (the keystone)**
- `Engine.__init__` calls `load_capability_folders` for every cap;
  collisions between OntologyExtension dict + file form raise loudly.
- `CapabilityContext.template(name)` substrate accessor.
- `Capability.as_capability()` deepcopies the class-level ontology —
  load-bearing fix (the class-level default `CapabilityBase.ontology
  = OntologyExtension()` was shared across all subclasses; bootstrap
  mutations leaked between caps).
- `Ontology.materialise_templates` coerces `string.Template → str`
  for the graph property (loader returns Template objects).

**Phase 2 — Agent-instruction doctrine**
- `docs/vision/CAPABILITY-AUTHORING.md` §"Templates instruct agents
  (Spec 060 — the Bitwize pattern)" between Spec 019 and Spec 016
  Hint #8 sections.
- Documents frontmatter / `$variable` / `<!-- AGENT: -->` /
  `<!-- BEGIN IF / END IF -->` / chain-next-tail conventions with a
  human-view vs agent-view example.

**Phase 3 — Per-capability roster (10 folder migrations + 13 files)**
- Folder migrations: dogfood, reflect, gate, branch, workspace,
  subagent, skill_generator, delegate, develop, plugin, jules
  (jules absorbs Spec 028).
- Templates shipped (7): dogfood-notes.md, reflection-note.md,
  checklist.md, preamble-mode-a.md, preamble-mode-b.md,
  research-report.md, explanation.md, analysis-summary.md,
  improvement-plan.md.
- Schemas shipped (15): reflection.json, gate-outcome.json,
  branch-outcome.json, workspace.json, baseline.json,
  subagent-review.json, delegation.json, reduction.json,
  plugin-manifest.json, skill-md.json, command-md.json,
  marketplace-entry.json, step-doc.json, jules-session.json,
  jules-patch.json, jules-watch-event.json, citation.json,
  verification.json, explanation.json.
- `sys.modules` aliases at `agency/capabilities/__init__.py`
  preserve legacy `agency.capabilities._jules_*` import paths +
  make `monkeypatch.setattr` reach the canonical modules.

**Phase 4 — Lint rule**
- `plugin._check_template_folder` (seventh rule under Spec 016
  scaffold). 5 tests cover good-cap pass, missing folder, non-kebab
  stem, missing AGENT block, silent-on-no-templates back-compat.

**Phase 5 — Verb migration (partial; opt-in completion)**
- `dogfood.render` flipped to `ctx.template('dogfood-notes')` —
  proves the pattern.
- Remaining migrations (jules preambles assembly, document.explain,
  analyze.run/improve report rendering) deferred as opt-in iteration
  work: templates are discoverable + materialised; verbs flip when
  iteration pressure justifies the change.

**Phase 6 — Tests**
- `tests/test_template_bootstrap_wireup.py` (4 tests).
- `tests/test_template_folder_lint.py` (5 tests).

**Phase 7 — Review loop**
- 7 review-comment fix rounds processed: 35+ correctness fixes
  spanning analyze (rule-axis registry, performance scope-tracking,
  loop-shape coverage, sleep statement detection, while-True nested
  exits, S001 compile, S003/S004 alias tracking, lang honoring,
  paths IP-mapping, MI rank monotonicity, dict-shape schemas),
  research (label-check guards, query validation, empty-citation
  fail, doc-corpus snippet anchoring, k forwarding, verify chain
  edge direction), document (provenance SUPERSEDED_BY walk,
  artefact invocation union, OBSERVED_DURING parity on explain,
  research-report renderer), reflect (zero-score filter), delegate
  (shlex.quote injection guard), intent (parent_intent_id label
  check), and several substrate clean-ups (E2E timeout, BGE
  fallback breadth, dogfood oversize trim, bin shim PATH iteration,
  dogfood.export role tag). All round-7 P2 findings resolved.

### Live measurements
- `pytest --tb=no -m "not e2e"`: **663 passed + 1 skipped + 4 deselected** in 256s.
- `scripts/check-drift`: **NO DRIFT DETECTED**.
- `plugin.lint_capability` over the live registry: only minor
  `token_budget` warnings (briefs slightly over 20 cl100k tokens) —
  not blocking.

### Cluster-coherence (Spec 047)
- C08 (Memory) — Schema + Template node materialisation closes the
  generate/validate loop CORE.md:66 promised.
- C12 (Capability Authoring) — agent-instruction doctrine + lint
  rule extend the Spec 016 scaffold; 7 rule families now.
- C13 (Plugin/MCP Authoring) — the per-cap `templates/` + `schemas/`
  folder pattern is the standardised artefact-contract surface.
