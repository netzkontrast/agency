# Implementation Roadmap — Novel Capability (102–108)

> Iteration 4 (2026-06-07). The 8-spec set decomposes into ~6-8 PRs over
> 3 waves. This roadmap sequences the work so each PR can ship Green
> independently while preserving the drop-in bar.

## Wave 1 — Foundation (1 PR)

### PR-A: Spec 102 base — `agency/capabilities/novel/` exists

**Scope** (per 102's "First-PR scope"):
- Module skeleton (`__init__.py` + `ontology.py` + `drivers.py` + `clusters/__init__.py`)
- Full `OntologyExtension` declaration (base + ALL iteration-2 nodes —
  even unused ones, so children can attach)
- 11 templates ported VERBATIM
- 4 data assets ported VERBATIM (`ontology.json`, `scenarios.json`,
  `ncp-schema-v1.3.0.json`, `research-domains.yaml`)
- Base lifecycle verbs (`conceptualize`, `capture_idea`, `promote_idea`,
  `list_ideas`, `create_novel`, `find_novel`, `set_novel_status`)
- `novel-concept` walkable skill (10 phases)
- `tests/test_novel_lifecycle.py` (~12 tests, simple-novel happy path)
- pytest marker addition
- 102 ships; 101 master moves to "Partial".

**LoC estimate**: ~600 impl + ~200 tests + ~150KB data assets

## Wave 2 — Parallel domain clusters (4 PRs, parallel-safe)

After PR-A lands, four child PRs can ship in parallel — each touches its
own driver surface.

### PR-B: Spec 103 — storyform (the Dramatica engine)

- 13 decidability-check verbs (11 decidable + 2 hybrid)
- 1 composite `novel_coherence_check` gate verb
- TextDriver method delta (`load_ontology`, `get_quad`, `get_dynamic_pair`, etc.)
- 34 NCP fixtures ported VERBATIM under `tests/fixtures/novel/`
- `storyform-build` walkable skill (6 phases)
- Token-budget assertion (clean PASS ≤ 40 tokens, 3-violation ≤ 400)

### PR-C: Spec 104 base — prose (base)

- 12 user verbs + 3 editorial-stage gate verbs
- TextDriver method delta (prose analysis: voice/POV/dialogue/filter words)
- 4 walkable editorial skills
- LLM-driver opt-in (Path A rule-based default)

### PR-D: Spec 105 — research (verbatim 099 pattern)

- 8 verbs delegating to `agency.research`
- 10-domain registry (`research-domains.yaml` already in PR-A)
- `verify_gate` composite
- `research-workflow` walkable skill

### PR-E: Spec 106 base — catalogue

- 10 verbs (beta-reader + edit-note + version-log)
- DBDriver method delta (psycopg2-shaped fake)
- `db_init.py` migration
- `beta-feedback` walkable skill

## Wave 3 — Composition (3 PRs, sequential)

### PR-F: Spec 107 — manuscript (introduces FormatDriver)

After PRs B+C+D+E land:
- FormatDriver protocol + fake
- 10 user verbs + 1 gate
- `manuscript-pass` + `publish-prep` walkable skills
- 4 publication templates (query-letter, synopsis, blurb, back-cover)
- Failure-mode table for pandoc/wkhtmltopdf/calibre
- Deferred-import discipline

### PR-G: Spec 108 base — gates (base 4)

After PR-F:
- 6 user verbs + 4 base composite-gate verbs (pre-draft, beta-ready,
  query-ready, publish-ready)
- 4 walkable gate skills
- Simple-novel E2E test (test_novel_e2e.py path 1)

### PR-H: 101 → Shipped

After PR-G:
- E2E test green
- 101 row flips to Shipped
- `scripts/check-drop-in-bar` CI gate confirms zero engine edits
- TODO.md row reconciliation

## Wave 4 — Iteration 2+3 extensions (3 PRs, opt-in)

These ship AFTER 101 is "Shipped"; they're additive feature PRs, not
spec changes.

### PR-I: Complex-novel extensions

- 102: `Volume`/`Part`/`Book` lifecycle verbs
- 102: World sub-schema verbs (8 nodes: Culture/Religion/Language/MagicSystem/
  Politics/Economy/Geography/Bestiary + WorldAxiom + Canon)
- 102: Faction/House/Family/Arc/ArcPhase lifecycle verbs
- 103: `list_storyforms` for nested-storyform discovery
- 104: per-POV voice signatures + multilingual canon preservation
- 106: arc/cast/worldbuilding coverage reports
- 107: series-boxset rendering
- 108: 4 new gates (G5-G8) + `series-publish-ready` skill
- Complex-novel E2E test (test_novel_e2e.py path 2)

### PR-J: Writer's workflow + genre extensions

- 104: `extract_inline_todos`, `Chapter.status=stub`,
  `Chapter.write_order`
- 104: genre-specific verbs (mystery/thriller/romance/fantasy/sci-fi/literary)
- 105: `suggest_domains_for_genre`

### PR-K: Draft-variant experimentation

- 102: `DraftVariant` node
- 106: `branch_draft_variant`, `promote_draft_variant`
- 106: `experiment-pass` walkable skill

## Migration sequence summary

```
                    ┌─→ PR-B (103 storyform)    ─┐
PR-A (102 base) ─→  ├─→ PR-C (104 prose base)   ─┤  Wave 2
                    ├─→ PR-D (105 research)     ─┤
                    └─→ PR-E (106 catalogue)    ─┘
                                                  │
                                                  └─→ PR-F (107 manuscript)
                                                         │
                                                         └─→ PR-G (108 gates base)
                                                                 │
                                                                 └─→ PR-H (101 → Shipped)
                                                                         │
                                                                         └─→ PR-I (complex extensions)
                                                                               ├─→ PR-J (writer's workflow)
                                                                               └─→ PR-K (draft variants)
```

## Per-PR risk register

| PR | Risk | Mitigation |
|---|---|---|
| A | Template + data asset port introduces too much in one PR | Split: PR-A1 = templates + ontology; PR-A2 = data assets + base verbs. Recombine if PR-A1 is small. |
| B | Decidability checks fan-out costs > 400 tokens for large NCPs | Per-check token budget; aggregator caps violation arrays at 3 |
| C | 12 verbs in one PR is wide | Split: 104-base (6 verbs) + 104-editorial (6 verbs + gates) |
| F | FormatDriver brings external deps | Deferred-import discipline already specified; CI runs fake only |
| G | E2E test orchestrates 5 clusters | Each cluster's verbs are mocked via fake_drivers — E2E exercises the registry, not the binaries |
| I | Complex-novel features land all together | Split into per-axis PRs (PR-I1 World, PR-I2 Volume/Part/Book, etc.) |

## Timeline estimate

Per-PR estimate at 1 day per PR + 1 day review:
- Wave 1: 2 days
- Wave 2: 4 PRs × 2 days = 8 days (parallel: ~3 days wall-clock with 2 engineers)
- Wave 3: 3 PRs × 2 days = 6 days
- Wave 4: 3 PRs × 2 days = 6 days

Total: ~22 days serial OR ~17 days with parallel Wave 2.
