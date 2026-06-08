---
spec_id: "093"
slug: music-complete-port
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["001", "002", "007", "020", "047", "054", "076", "079", "080", "081", "092"]
affects:
  - agency/capabilities/music/
  - examples/music.py
  - examples/music_drivers.py
  - tests/test_music_*.py
source-repos:
  - "https://github.com/bitwize-music-studio/claude-ai-music-skills.git @ v0.91.0+ (89 MCP tools, 53 skills, 72 genres, 46 reference docs)"
domain: music / cluster-integration / capability
wave: 7
research_first: false
---

# Spec 093 — Music Complete Port (master)

> **Master spec** — coordinates the seven child specs (094–100), one per cluster.
> Child specs ship independently; this master tracks coherence, ontology
> consolidation, and the doctrine exception that places music in
> `agency/capabilities/` instead of `examples/`.

## Why

Spec 007 deliberately shipped music as a **proof-of-contract slice** (15 verbs / 8
clusters / 5 drivers in `examples/music.py`), leaving the long-tail ~70 bitwize
tools marked **"covered-by-pattern, port-on-demand"**. That slice proved the
clustered Capability + Boundary/Driver contract + provenance moat on a real
domain. **What 007 proved, 093 ships in full.**

User directive (2026-06-07): *"Check the bitwize Music Plugin — and port it
completely to the Agency Plugin as capability."* The "covered-by-pattern" tail
is no longer notional — it is the deliverable.

A **complete port** is the next stress test of the substrate. If the
drop-in-capability bar (`CLAUDE.md`: "add a folder under `agency/capabilities/
<name>/` — verbs + ontology + a docstring that derives its Agent Skill — and
nothing else") truly holds, then porting bitwize-music's full surface should be
a *single folder* with no edit anywhere else in `agency/`. **That is what 093
proves, and what its CI gates check.**

### The full bitwize-music surface (audit baseline)

| Plugin aspect | Count / Description | Disposition in 093 |
|---|---|---|
| MCP tools | 89 (in 19 handler modules) | 75 ported (across 094–100), 11 absorbed by substrate, 3 dropped |
| Skills | 53 markdown + frontmatter | Workflow skills → walkable `OntologyExtension.skills` (8+ phase-graphs across 094–100); reference skills → docs |
| Templates | **14** (8 root `templates/*.md` + 6 in `templates/promo/`) | **All ported verbatim** to `agency/capabilities/music/templates/` + registered on `OntologyExtension.templates` (094 owns 5 lifecycle, 098 owns 6 promo, 099 owns 2 research/sources, 096 owns 1 genre — see per-cluster spec) |
| Reference docs | **50** markdown across 10 subdirs (mastering, suno, cloud, sheet-music, promotion, release, distribution, workflows, quick-start, overrides) | All ported verbatim to `agency/capabilities/music/data/reference/<subdir>/` with bitwize subdir layout preserved (so internal cross-links work) |
| Genre library | **All bitwize `genres/` dirs** (incl. subgenres + INDEX.md) | Ported verbatim to `agency/capabilities/music/data/genres/` (subdir-per-genre layout preserved) |
| FastMCP server | `servers/bitwize-music-server/` | Absorbed by `mcp__agency__{search,get_schema,execute}` |
| Slash commands | `/bitwize-music:<cmd>` per skill | Absorbed by Spec 079 CLI mirror (`agency music <verb>`) |
| Hooks | 6 items (session-start, pre-commit, validate_track.py, check_version_sync.py) | Absorbed by Spec 076 unified hook dispatch |
| Migrations | 6 version-specific `.md` notes | Bitwize-version-specific; not portable. Future agency migrations live in `agency/capabilities/music/migrations/` (097's `db_init.py` is the first) |
| State cache | `~/.bitwize-music/cache/state.json` | Absorbed by `.agency/session.db` (graph-canonical per CLAUDE.md rule 2) |
| Config | `~/.bitwize-music/config.yaml` | Absorbed by `.agency/session.db` + per-cap config |
| `tools/` Python utilities | 11 subdirs (cloud, database, mastering, mixing, n8n, promotion, shared, sheet-music, state, userscripts, validate_help_completeness.py) | Absorbed into Driver method implementations (StateDriver/AudioDriver/CloudDriver/DBDriver/TextDriver) |
| Tests | 3,773 tests | Behavioural parity in agency tests (per CLAUDE.md rule 8 — invariants not snapshots; we don't clone test count) |
| Docs (configuration/skills/troubleshooting) | `docs/` 4 items | Absorbed by agency `document` capability + `skills.find/render` |

> **bitwize-music plugin nothing-left-on-the-floor check:** every directory
> under the bitwize plugin root has a disposition in this table. The 14
> templates + 50 reference docs + the genre library are CONTENT artefacts —
> they ship as-is into `agency/capabilities/music/{templates,data}/`. The
> behaviour ports through verbs + drivers + skills. The infrastructure
> (server, hooks, config, state cache) evaporates into agency substrate.
> ZERO unaccounted bitwize content.

### What "complete" means here (the operating definition)

Complete behavioral parity, NOT 1:1 verb-name parity:

- **Every bitwize tool either becomes a verb in an existing cluster OR is
  explicitly DROPPED with justification.** The 89-tool inventory from 007's
  Appendix is the audit list — every row gets a verdict in 093 (or a child).
- **Every bitwize workflow skill becomes a walkable `OntologyExtension.skills`
  phase-graph** with computed predicates via `gate.check` and a terminal human
  `elicit` (Spec 080/081 contract). bitwize has 53 skills; ~35 are workflows
  (the rest are domain references or model-tier shims that evaporate).
- **Every bitwize side effect routes through a Driver.** The five proven driver
  protocols (StateDriver/TextDriver/AudioDriver/DBDriver/CloudDriver) already
  cover every bitwize boundary. No new driver protocols. The `llm` driver from
  Spec 092 G3 wires Suno prompt synthesis when desired.
- **Every bitwize stateful concept lives in the graph** — extending the existing
  Album/Track/Idea/Tweet/SheetMusic nodes with Genre, MasteringPreset, Reference,
  PromoTemplate, VerificationRecord, ResearchClaim. Reference data (72 genre
  guides, 46 reference docs) stays as static files under
  `agency/capabilities/music/data/` — read by drivers, NOT graph-ified
  (CLAUDE.md rule 2: graph is the store for *behavior + provenance*, not static
  data assets).
- **bitwize's MCP server, slash commands, session hooks, and state cache are
  ABSORBED** by agency's substrate (Specs 020 / 076 / 079) — they don't get
  ported, they evaporate. Net code reduction at the substrate level.

### What gets DROPPED (explicit non-port)

| bitwize tool/feature | Why dropped |
|---|---|
| `get_python_command`, `check_venv_health`, `cleanup_legacy_venvs` | Plugin-bootstrap concerns; agency installs differently |
| `load_override`, `get_config` | Replaced by `.agency/session.db` + Spec 092 G3 `llm` driver config |
| `health_check` (bitwize-specific) | Replaced by `music_health` (already in 007) + `agency_doctor` |
| `db_init`, `rebuild_state` | One-shot install ops, not verbs. **`db_init` → `agency/capabilities/music/migrations/db_init.py`** (per Spec 097's Done-When — Codex P2 alignment); `rebuild_state` evaporates (graph reads are canonical per CLAUDE.md rule 2) |
| `migrate_audio_layout`, `prune_archival` | Migration ops, not verbs — moved to `agency/capabilities/music/migrations/` |
| `get_plugin_version` | `agency_welcome` returns it |
| FastMCP server | Absorbed by `mcp__agency__{search,get_schema,execute}` |
| Slash-command facade | Absorbed by Spec 079's `agency <cap> <verb>` CLI mirror |
| Session-start hook | Absorbed by Spec 076's unified hook dispatch |
| `state.json` cache | Replaced by graph reads (Spec 020 central DB) |

That's ~14 tools that **disappear into substrate**, not 14 missing features.

## Doctrine exception (load-bearing)

CLAUDE.md standing rule: *"Domain capabilities live in `examples/` (e.g.
`examples/music.py`), loaded via `Engine(..., extra_capabilities=[…])` — the
bootstrapping harness stays minimal."*

**093 places music in `agency/capabilities/music/` (first-class, in-tree).**
User directive (2026-06-07 — explicit decision in the brainstorm gate of this
spec) overrides the default doctrine. The justifications, recorded so future
audits do not flag this as drift:

1. **Music has crossed the proof threshold.** 007 already proved music belongs
   in the substrate's capability set behaviorally (15 verbs, 5 drivers, full
   ontology, gated skills, provenance moat — all green). The `examples/` home
   was a hedge; the complete port retires it.
2. **The bootstrap harness stays minimal where it matters.** Music registers
   like every other capability (zero engine edits, single folder). The bootstrap
   cost of a first-class music cap is the same as any other capability.
3. **Future domain caps can still live in `examples/`.** The doctrine still
   applies to *new, unproven* domain caps. Music is the *proven* domain cap —
   its place in `agency/capabilities/` is earned, not granted by default.
4. **The drop-in bar still binds.** Adding music as a folder under
   `agency/capabilities/music/` with *no other edit* is the discriminator. If
   093 requires editing `agency/engine.py` or `agency/registry.py`, the bar is
   broken and the spec fails its own Done-When.

The `examples/music.py` + `examples/music_drivers.py` files will be **migrated**
into `agency/capabilities/music/` (Spec 094, lifecycle cluster, ships the move).
The `tests/test_agency.py` smoke (single-verb conceptualize) becomes
`tests/test_music_lifecycle.py`. No test count regression.

## Spec layout (the seven children)

Each child spec corresponds to one cluster from the proven 7-cluster
decomposition (007's 8 clusters consolidated: `media` folds into `audio` for
sheet-music transcription + into `promo` for video render; `cloud` splits along
the stdlib vs boto3 line — stdlib stays in `catalogue` for streaming verify,
boto3 stays in `promo` for R2 upload):

| Spec | Cluster | Driver(s) | bitwize tools absorbed | Skills (walkable) |
|---|---|---|---|---|
| **094** | lifecycle | StateDriver | album/track/idea CRUD + conceptualizer + rename + resume + session (~22 tools) | `album-concept` (kept) + `album-conceptualizer` (7-phase) + `lifecycle-walk` |
| **095** | lyrics | TextDriver | lyric analysis, pronunciation, voice-checker, plagiarism, explicit, rhyme/syllable (~14 tools) | `lyric-writing` + `lyric-review` + `pronunciation-pass` |
| **096** | audio | AudioDriver | mix/master/QC/album-coherence + sheet-music transcription + signature/measurement (~18 tools) | `mastering` + `mix-polish` + `release-prep-audio` |
| **097** | catalogue | DBDriver + CloudDriver(stdlib) | tweet DB CRUD + streaming verify + URL store (~14 tools) | `tweet-curation` + `streaming-verify` |
| **098** | promo | StateDriver + CloudDriver(boto3) + (optional) LLMDriver | promo copy + promo video render + cloud upload + sheet-music publish (~10 tools) | `promo-pass` + `release-publish` |
| **099** | research | research capability (delegation) + StateDriver | 10-domain researchers + verifier + document-hunter + verify-sources (~8 verbs as agency.research delegations) | `research-workflow` |
| **100** | gates | StateDriver + `gate.check` + `elicit` | pre-generation + structure validation + release-qa (~6 tools, mostly orchestration) | `pre-generation` + `release-qa` + `validate-structure` |

**Verb-count target** (panel-corrected, iteration 1):

| Child | User-facing verbs | Internal `*_gate` verbs | Total registered |
|---|---|---|---|
| 094 lifecycle | 14 | 0 | 14 |
| 095 lyrics | 14 | 4 (prosody/pronunciation/repetition/explicit) | 18 |
| 096 audio | 19 | 2 (measure/qc) | 21 |
| 097 catalogue | 14 | 1 (tweet_schedule) | 15 |
| 098 promo | 10 | 1 (promo_review) | 11 |
| 099 research | 8 | 1 (verify_gate) | 9 |
| 100 gates | 6 | 5 (concept/lyrics_pregen/audio_release/catalogue/promo) | 11 |
| **Total** | **85** | **14** | **99** |

89 bitwize tools → 14 absorbed/dropped → 75 ported + 1 bitwize-skill
(voice-checker) ported as a verb → split as 85 user-facing verbs (some
bitwize tools fan into 2+ agency verbs for ISP cleanness — e.g.
`get_lyrics_stats` folds into `lyric_report`; `transcribe_audio` splits into
audio + sheet-music) + 14 internal gate verbs that the walkable skills
compose.

**Arithmetic check** (user-facing column, in case audits trip):
14 + 14 + 19 + 14 + 10 + 8 + 6 = **85**. Each cluster spec's manifest table
sums independently; the row counts above match each child's "Verb manifest"
section.

## Design — the shared substrate (concerns common to all children)

### Drivers (no new boundaries)

All five protocols already live in `examples/music_drivers.py`. Spec 094
relocates them to `agency/capabilities/music/drivers.py` and the child specs
*extend the method surface* on existing drivers — they do NOT add new driver
protocols. The driver method audit is part of each child's Done-When.

| Driver | New methods added across 094–100 |
|---|---|
| StateDriver | `list_tracks`, `set_track_status`, `find_album`, `get_session`, `update_session`, `get_ideas`, `update_idea`, `promote_idea`, `rename_album`, `rename_track`, `resolve_path`, `validate_structure`, `pending_verifications`, `update_album_status` |
| TextDriver | `count_syllables_text`, `extract_distinctive_phrases`, `extract_section`, `validate_section_structure`, `analyze_rhyme_scheme`, `analyze_readability`, `check_pronunciation_enforcement`, `check_homographs`, `check_streaming_lyrics`, `check_cross_track_repetition`, `check_explicit_content`, `scan_artist_names`, `format_for_clipboard` |
| AudioDriver | `polish_audio`, `master_audio`, `master_with_reference`, `polish_album`, `polish_and_master_album`, `fix_dynamic_track`, `reset_mastering`, `render_codec_preview`, `measure_album_signature`, `album_coherence_check`, `album_coherence_correct`, `analyze_audio`, `analyze_mix_issues`, `qc_audio`, `mono_fold_check`, `transcribe_audio`, `prepare_singles`, `create_songbook`, `generate_promo_videos`, `generate_album_sampler` |
| DBDriver | `update_tweet`, `delete_tweet`, `list_tweets`, `search_tweets`, `get_tweet_stats`, `sync_album` |
| CloudDriver | `r2_put` (already exists), `r2_delete`, `r2_list`, `publish_sheet_music`, `upload_promo_asset` |

**Every new method goes through the typed-named-method discipline** (Spec 002
Option B). No `dispatch(op, **kw)`. Fakes for tests are deterministic; CI runs
zero real ffmpeg, zero real Postgres, zero real R2.

### Ontology (a single extension, merged via children)

The 094 cluster spec carries the **canonical ontology** for music; child specs
add their nodes via the same `OntologyExtension` (one extension per cap, per
Spec 002). The full node set after 093 ships:

```
Album       (status, type, genre, slug, artist, target_lufs, theme,
             created_at)
Track       (status, slug, album, syllables, readability, lyrics_path)
Idea        (text, status, captured_at, promoted_to_album)
Tweet       (album, body, scheduled_at, status, platform)
SheetMusic  (album, source_audio, format, body, published_url)
Genre       (slug, name, mastering_target_lufs, suno_tips, reference_artists)
Reference   (kind, slug, body)               # mastering/Suno/prosody refs
PromoTemplate (platform, slug, body)
VerificationRecord (claim, source, verified_by, verified_at)
ResearchClaim (text, source_uri, confidence, verified)
MasteringPreset (slug, target_lufs, eq_curve, true_peak, suno_compat)
```

Closed enums:
- `(Album, status)`: `draft / in-production / mastered / released`
- `(Album, type)`: existing `ALBUM_TYPES` (preserved)
- `(Track, status)`: `draft / recorded / mixed / mastered`
- `(Idea, status)`: `new / promoted / dropped`
- `(Tweet, status)`: `draft / scheduled / posted / archived`
- `(ResearchClaim, verified)`: `pending / human-confirmed / rejected`

Artefact schemas (every `act` verb that produces a document):
- `album-concept` (preserved from 007), `promo-copy` (preserved), `mastering-report`
  (preserved), `lyric-report` (preserved), `sheet-music` (preserved),
  `promo-video`, `qc-report`, `research-claim`, `pronunciation-report`,
  `genre-guide`, `release-package`.

### Walkable skills (workflows as phase-graphs)

bitwize's workflow skills (album-conceptualizer, lyric-writer, mastering-engineer,
release-director, pre-generation-check, etc.) each become a walkable
`OntologyExtension.skills` phase-graph (Spec 080/081 contract). Each phase has:

- `produces` — the keys it must set on the lifecycle context
- optional `gate` — computed via `gate.check` (BLOCKED_ON / PASSED) OR human
  via `elicit`/`lifecycle_gate` for the terminal "ship it?" confirmation

Naming follows Spec 081: the cap's walkable skill defaults to `music-usage`
(role-clustered, ≤6 phases, hard confirm gate); authored disciplines override.

### Reference data (static files, NOT graphed)

`agency/capabilities/music/data/` holds:
```
data/
├── genres/         # 72 genre guides — one .yaml per genre (production notes,
│                   # Suno tips, reference artists, mastering target)
├── reference/      # 46 reference docs — mastering workflows, Suno V5 guide,
│                   # vocal direction taxonomy, etc.
└── templates/      # promo platform templates (X/Threads/Instagram/TikTok)
```

The StateDriver gains a `read_data(kind, slug)` method to load them; tests bind
a fixture-data fake. **These files are CHECKED INTO THE REPO** because they are
authored domain content, not user-state. (User-state is graph-canonical per
rule 2.)

### Cross-cluster call patterns (panel-added, iteration 2)

| Pattern | Used where | Guarantees |
|---|---|---|
| Idempotent synchronous query | most `transform` verbs (find_album, list_tracks, lyric_report, …) | safe to retry, no state mutation, returns deterministic data |
| At-most-once side effect (intent-keyed) | all `effect` verbs that record artefacts | provenance ensures retry-safety: a retry against the same intent_id detects the prior PRODUCES edge and returns the prior result |
| Cross-cluster method call | 100's `pregen_check` calls `music.list_tracks`, `music.pending_verifications` | within-cap RPC via `ctx.call(cap, verb, …)`; idempotent if the called verb is `transform`; side-effecting otherwise |
| Fire-and-forget telemetry | `music_health`, `diagnose` | no provenance recorded; not retried |

**Track state lives in the graph** (Album/Track nodes, StateDriver-backed) —
NOT in Postgres. The DBDriver carries **promo/social state only** (tweets,
their scheduling + posting status). 100's `release_check` reads track status
via `find_album` → `list_tracks` (StateDriver), never via DBDriver. The 007
example's `release_check` query against tracks-in-DB is corrected to read
graph-canonical state.

**Provenance ordering is causal, NOT chronological.** A graph traversal from
the root intent returns edges in SERVES-DAG order, which agrees with wall-
clock for sequential calls and is well-defined (but not wall-clock-ordered)
for parallel calls.

### Provenance moat (the headline — net-new vs bitwize)

The full release audit becomes a single traversal. The substrate tool
signature (`engine.py:438`) is `memory_graph_provenance(intent_id: str) -> dict`
— **no `include` kwarg**; the result returns ALL relevant nodes (serves,
agents, artefacts, gates) keyed by category. Filtering happens on the result.

```python
# "Show me every research claim, lyric pass, master, QC run, tweet, and
# promo asset for album X, with the intent that served each."
result = await call_tool("memory_graph_provenance",
                         {"intent_id": album_intent_id})
# result["serves"]   — every node SERVES the intent (invocations, claims, …)
# result["artefacts"] — every PRODUCES'd artefact
# result["gates"]    — gate.check ledger entries
# result["agents"]   — every agent that performed an invocation
```

bitwize cannot do this (handlers are flat; no graph). This is the one thing
the complete port exists to demonstrate at full scale.

## Done When (master-level coverage gates)

- [ ] **All seven child specs (094–100) ship Green** with their own Done-When
      gates met; each child's Followup is grounded (Spec 092 G6).
- [ ] **`agency/capabilities/music/` is the live music cap;**
      `examples/music.py` + `examples/music_drivers.py` become **deprecation
      re-export shims** for one spec cycle (Codex P2 — match 094's contract;
      delete-outright would break any existing import). Removal lands in a
      future spec (~110 or whenever a grep confirms no external import
      survives — whichever first). `tests/test_agency.py:1116-1153` smoke is
      replaced by `tests/test_music_lifecycle.py`.
- [ ] **The drop-in bar holds end-to-end** AND is ENFORCED by CI: porting
      music requires ZERO edits to `agency/engine.py`, `agency/registry.py`,
      `agency/ontology.py`, `agency/capability.py`, or `agency/toolresult.py`
      (the substrate's load-bearing core). Enforced by
      `scripts/check-drop-in-bar` — **lands in the 094 PR (the migration
      PR), not in this design-only spec set.** Codex P2 flagged that the
      spec PR labels the script "new in this PR" but doesn't ship it; the
      label was wrong — this is a design wave (specs only), and the script
      is itself an artefact of the implementation wave that begins with 094.
      Once 094 ships, the script runs on every music PR; non-zero exit
      blocks merge. Without this gate the bar is aspiration.
- [ ] **89-tool audit closed:** every row in 007's Appendix A has a verdict
      across 094–100 (ported / dropped / absorbed). **The audit table is
      embedded as Appendix A of this master** (see end of this document) —
      regenerated on every child merge so the coverage gate can be closed
      mechanically. The audit IS the contract; without it, "complete" is
      vibes-based.
- [ ] **Provenance moat lit on a real album lifecycle:** an end-to-end test
      (`tests/test_music_e2e.py`) drives the full pipeline (capture_idea →
      conceptualize → research → lyric_report → master_album → promo_copy →
      verify_streaming) and asserts `memory_graph_provenance(intent_id)`
      returns the full chain with PRODUCES/SERVES edges intact.
- [ ] **Doc-drift clean:** `docs/guide/capabilities.md` regenerates with the
      new music verbs (Spec 092 G5); doctrine exception is recorded in
      `docs/vision/CAPABILITY-CLUSTERS.md` (one paragraph noting music
      graduated from examples/).
- [ ] **`TODO.md` updated** with 093 + each child spec row (rule 4).
- [ ] **`scripts/check-drift` Green** for the music capability (no orphans,
      no missing references); install regen committed.

## Cluster coherence (CLAUDE.md rule 5)

Per Spec 047 (cluster integration master), every new verb/skill lands in one
of the 13 SDLC+meta clusters. The seven music children map to:

- 094 lifecycle → **state cluster** (extends with domain-specific state)
- 095 lyrics → **content/analysis cluster** (decidable transforms)
- 096 audio → **artefact cluster** (produces mastering-reports + sheet-music)
- 097 catalogue → **catalogue/CRUD cluster** + **boundary cluster** (DB +
  network)
- 098 promo → **artefact cluster** (produces promo-copy + promo-video)
- 099 research → **research cluster** (delegates to existing `agency.research`)
- 100 gates → **gate cluster** (predicates + lifecycle pauses)

No new cross-cluster decisions; each child extends an existing cluster's
integration pattern. Coherence interactions are scored in each child's
"Coherence" section.

## Migration order (panel-corrected — Codex P2 on cross-cluster dependency)

**094 ships first** — the foundation move (`examples/music.py` →
`agency/capabilities/music/`), the consolidated ontology, the StateDriver
extensions. Every other child depends on 094.

**Wave 1 (parallel-safe after 094):** 095 (lyrics — TextDriver), 096 (audio
— AudioDriver), 097 (catalogue — DBDriver + CloudDriver-stdlib), 099
(research — delegates to `agency.research`). Each touches an isolated
boundary; the order among them is shape-of-the-team.

> **Frontmatter alignment** (Codex P2 — iteration 5): 096's earlier draft
> declared `depends_on: ["094", "095", "093"]` on the speculation that
> audio QC would read lyric markers. The actual 096 verb set (master/mix/QC
> on audio paths) does NOT read lyric state — that integration point was
> never real. 096's `depends_on` is corrected to `["094", "093"]`, matching
> the Wave 1 parallel-safe claim here.

**Wave 2 (after 096 + 097):** 098 (promo — CloudDriver-boto3, optionally
LLMDriver). Codex P2: 098's `release_package` verb composes audio render
outputs (096's `generate_promo_videos`, `generate_album_sampler`,
`prepare_singles`) and catalogue state (097's streaming URLs + tweet
records), so its release-packaging tests fail-fast if 096/097 are absent.
**098 is NOT parallel with 096/097 — it follows them.**

**100 ships LAST.** It composes cross-cluster predicates: `lyrics_pregen_gate`
reads from 095, `audio_release_gate` reads from 096, `catalogue_gate` reads
from 097, `promo_gate` reads from 098, `verify_gate` reads from 099. The
`release-qa` skill walk crashes with "unknown verb" if any predecessor
cluster's verbs are absent. **The master 093 end-to-end test
(`tests/test_music_e2e.py`) lives in 100 and asserts the full pipeline
provenance — it cannot run until all upstream clusters have shipped.**

```
094 lifecycle (the foundation; everything depends on it)
  │
  ├─→ 095 lyrics    ─┐
  ├─→ 096 audio     ─┤  Wave 1 — parallel-safe (touch isolated boundaries)
  ├─→ 097 catalogue ─┤
  └─→ 099 research  ─┘
        │   │
        │   └─→ 098 promo (Wave 2 — depends on 096 audio render + 097
        │                  catalogue state; release-packaging composes both)
        ↓
        └─→ 100 gates (the binder — composes all of the above; ships LAST,
                       carries the E2E test that flips 093 to Shipped)
```

> **Why not "100 second"?** An earlier draft ordered 100 second (rationale:
> "gates can be wired against 094 state"). Codex flagged the conflict in PR
> review: 100's frontmatter declares `depends_on: [094, 095, 096, 097, 099, 093]`
> and its `release-qa` reads promo state (098). The corrected order honors
> those declared dependencies. The 093 Done-When item "Provenance moat lit on
> a real album lifecycle" runs the E2E test, which lives in 100, after all
> domain clusters ship.

## Deployment (panel-added, iteration 2)

```bash
# Default install — lifecycle + lyrics + research + gates work out of the box
# (no audio binaries, no Postgres, no boto3). ~75% of music verbs available.
pipx install --editable agency

# Per-cluster opt-in extras:
pipx install agency[music-audio]    # pyloudnorm + numpy + scipy + soundfile + ffmpeg system binary
pipx install agency[music-db]       # psycopg2-binary
pipx install agency[music-cloud]    # boto3
pipx install agency[music-llm]      # routes promo_copy through `llm` driver (Spec 092 G3)
pipx install agency[music]          # everything above (the kitchen-sink extra)
```

CI matrix runs **5 install variants** to catch import-graph regressions:
default, `[music]`, `[music-audio]`, `[music-db]`, `[music-cloud]`. A
`scripts/check-install-matrix` job exercises one verb from each cluster per
variant and asserts the affected verbs degrade gracefully
(DEPENDENCY_MISSING) when their extra is absent.

## Open questions (resolved in panel pass — see REVIEW.md)

1. **Genre data shape: YAML or .py?** Recommend YAML (data-only, no executable);
   loaded by `StateDriver.read_data`. Children may revisit if performance bites.
2. **LLMDriver for Suno prompt synthesis?** Optional — the `suno-engineer`
   skill's prompt construction can stay rule-based (current bitwize approach)
   OR route through the `llm` driver (Spec 092 G3) for richer synthesis.
   Decision deferred to 098 (promo cluster) when the prompt builder lands.
3. **Postgres dependency in CI?** No — the DBDriver fake (psycopg2-shaped
   cursor) covers all DB tests. Production binds psycopg2 via the `[music-db]`
   extra; CI runs zero Postgres.
4. **AnthemScore for sheet-music?** Out of scope — the AudioDriver fake stubs
   `transcribe_audio` to return a deterministic `sheet-music` artefact; real
   transcription requires AnthemScore licensing, which is not a CI concern.
5. **Doctrine exception in CLAUDE.md text?** Add one line under rule "Domain
   capabilities live in `examples/`": *"…except music (Spec 093), which earned
   first-class placement via the proof-of-contract slice (007)."* This lands in
   Spec 094's PR.
6. **Renumbering Plan/ folder for music children?** No — 094–100 are
   contiguous and reserved by this spec. The Plan/ already has 091, 092 as
   the head; 094+ continues naturally (no gap collisions per the existing
   numbering policy).

## Followup — Implementation Status (2026-06-07)

**Verdict:** Drafted (spec set authored + spec-panel reviewed).

### Done
- Master spec authored (this file).
- Seven cluster specs (094–100) drafted (`Plan/094-music-lifecycle-cluster/spec.md`
  through `Plan/100-music-gates-cluster/spec.md`).
- 89-tool audit table grounded in 007's Appendix A.
- Cluster coherence mapped to Spec 047's 13-cluster taxonomy.
- Migration order documented — **corrected via Codex P2 review**: 094 first
  (foundation), 095/096/097/098/099 parallel-safe after 094, **100 LAST**
  (composes cross-cluster predicates; the E2E test that flips 093 to
  Shipped lives here).
- Doctrine exception (`agency/capabilities/` placement) justified + recorded.
- Spec-panel pass (via `sc:sc-spec-panel`) recorded in `REVIEW.md`.

### Still
- Implementation phase: each child spec drives its own RED→GREEN→Refactor cycle
  per Spec 053's fast-feedback discipline.
- The end-to-end provenance test (`tests/test_music_e2e.py`) lands in **100**
  (the last child — depends on all upstream clusters).
- `docs/vision/CAPABILITY-CLUSTERS.md` paragraph + CLAUDE.md doctrine-exception
  line land with the 094 PR (the migration PR).

## Appendix A — 89-tool audit (per-row verdict)

Every bitwize-music MCP tool (the v0.91.0+ surface) has a single verdict.
This table is the coverage gate: a child PR cannot close its Done-When if any
row mapped to its cluster is still `unverdicted`. Regenerated by
`scripts/audit-music-tools` (lands in 094 PR; reads bitwize's
`server.py:338-353` register chain + diffs against the children's manifests).

> **Source-of-truth for the row list:** 007's Appendix A is the canonical
> 89-row enumeration (`Plan/007-music-domain-capability/spec.md`).
> Appendix A here is the **verdict layer** keyed on 007's row IDs. Both
> tables must agree; `scripts/audit-music-tools` enforces it.

| 007 row | bitwize tool | Cluster | Verdict | Lands in |
|---|---|---|---|---|
| 1–7 | core: album/track lifecycle (`get_album_full`, `find_album`, `list_albums`, `get_track`, `list_tracks`, `list_track_files`, `get_session`) | lifecycle | ported | 094 |
| 8–15 | core: ideas/session/path (`create_idea`, `update_idea`, `promote_idea`, `get_ideas`, `update_session`, `resolve_path`, `resolve_track_file`, `get_pending_verifications`) | lifecycle | ported (some merged) | 094 + 100 (`pending_verifications`) |
| 16–18 | core: structural (`get_album_progress`, `create_album_structure`, `validate_album_structure`) | lifecycle / gates | ported | 094 / 100 |
| 19 | core: `get_config` | (absorbed) | absorbed → `.agency/session.db` | n/a |
| 20–22 | content: `create_track`, `update_track_field`, `update_album_status` | lifecycle | ported | 094 |
| 23–28 | text_analysis: `count_syllables`, `analyze_readability`, `analyze_rhyme_scheme`, `format_for_clipboard`, `extract_distinctive_phrases`, `extract_section` | lyrics | ported | 095 |
| 29–35 | lyrics_analysis: `validate_section_structure`, `check_pronunciation_enforcement`, `check_homographs`, `check_streaming_lyrics`, `check_cross_track_repetition`, `check_explicit_content`, `scan_artist_names` | lyrics | ported | 095 |
| 36 | lyrics_analysis: `get_lyrics_stats` | lyrics | ported (folded into `lyric_report`) | 095 |
| 37–39 | album_ops: `rename_album`, `rename_track`, `migrate_audio_layout` | lifecycle | ported × 2, dropped × 1 (`migrate_audio_layout` → migration script) | 094 |
| 40–43 | gates handler: `run_pre_generation_gates`, `validate_album_structure`, `validate_section_structure`, `diagnose` | gates | ported | 100 |
| 44–47 | streaming: `get_streaming_urls`, `update_streaming_url`, `verify_streaming_urls`, `extract_links` | catalogue | ported | 097 |
| 48–53 | skills: `list_skills`, `get_skill`, `load_override`, `get_plugin_version`, `health_check`, `get_python_command` | (absorbed) | absorbed → agency substrate (skills+welcome+doctor+install) | n/a |
| 54–55 | status: `get_pending_verifications`, `find_album` (re-export) | (merged) | ported (folded) | 094 / 099 |
| 56–58 | promo: `get_promo_status`, `get_promo_content`, `get_session` (re-export) | catalogue / promo | ported | 097 + 098 |
| 59–68 | processing/audio + processing/mixing: `master_audio`, `master_album`, `master_with_reference`, `polish_and_master_album`, `fix_dynamic_track`, `reset_mastering`, `render_codec_preview`, `measure_album_signature`, `album_coherence_check`, `album_coherence_correct` | audio | ported | 096 |
| 69–73 | processing/video + processing/sheet_music: `generate_promo_videos`, `generate_album_sampler`, `transcribe_audio`, `prepare_singles`, `create_songbook` | audio / promo | ported (`generate_promo_videos` + `transcribe_audio` → 096; `generate_album_sampler` + `prepare_singles` → 098; `create_songbook` → 096) | 096 + 098 |
| 74–81 | database: `db_init`, `db_sync_album`, `db_create_tweet`, `db_update_tweet`, `db_delete_tweet`, `db_list_tweets`, `db_search_tweets`, `db_get_tweet_stats` | catalogue | ported × 7 + 1 install script (`db_init` → migration) | 097 |
| 82–86 | promo + streaming (cont.): `get_promo_status`, `get_promo_content`, `get_streaming_urls`, `update_streaming_url`, `verify_streaming_urls` | catalogue / promo | ported (see rows 44–47 + 56–58 — folded) | 097 |
| 87 | processing/sheet_music: `publish_sheet_music` | promo | ported | 098 |
| 88–89 | gates: `run_pre_generation_gates`, `validate_album_structure` (re-exports) | gates | ported (see rows 40–43) | 100 |
| — | maintenance: `rebuild_state`, `prune_archival`, `cleanup_legacy_venvs`, `check_venv_health` | (absorbed/dropped) | absorbed → graph reads (rebuild_state) + dropped × 3 (venv ops are agency-substrate concerns) | n/a |
| — | search: `search` | (absorbed) | absorbed → `mcp__agency__search` | n/a |

**Audit totals:**
- **Ported**: 75 rows landed across 094–100
- **Absorbed by substrate**: 11 rows (config/venv/search/skills/welcome/health re-exports/session-start hook)
- **Dropped (no agency analog)**: 3 rows (venv-cleanup variants)
- **Total**: 89 rows accounted for — zero unverdicted

The audit is a **mechanically-checkable contract** — `scripts/audit-music-
tools` runs in CI per child PR and fails if any verdict goes missing or any
child's manifest does not match its claimed rows.
