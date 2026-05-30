# Spec 007 — Music Domain Capability — Spec-Panel Review

Reviewer: spec-panel (critique mode). Panel lens: Fowler (architecture/boundaries),
Newman (service decomposition), Nygard (production/failure-mode + real deps),
Wiegers (testable acceptance), Adzic (concrete examples), + domain-expert (audio/DSP).
Ground truth: `bitwize-music` v0.91.0 server at
`/root/.claude/plugins/cache/bitwize-music/bitwize-music/0.91.0/servers/bitwize-music-server/`.

---

## Verdict

**APPROVE WITH MUST-FIX CHANGES (do not start coding until §Must-fix resolved).**

The spec's *core architecture is sound and faithful*: 89-tool count is exact, the
migration-map tool inventory is identical to ground truth (verified by diff — zero
missing, zero invented), the role-tagging is mostly right, and the gate/skill
mapping is structurally correct against `gate.py` and the real
`run_pre_generation_gates`. The collapse-to-one-capability + driver-injection shape
matches `examples/music.py`, `capability.py`, and `jules.py` as cited.

But it is grounded in a **stale / partly-fabricated picture of the handler layout
and the real backends**: the "Why" section's module list is wrong (claims 11
modules; there are 19), and three concrete backend dependencies are mis-stated
(Postgres↛SQLite, urllib↛httpx, librosa not used). These are not cosmetic — the
DBDriver backend error changes the fake/real split, the CI "no external accounts"
claim, and Open-Q triage. Two tools are placed in the wrong cluster/driver relative
to the handler they actually live in. Fix the dependency facts and the two
mis-categorizations and this is ready.

---

## Verified tool count + mapping

**Count: 89 — VERIFIED EXACT.** There are exactly 89 `mcp.tool()(fn)` registrations
across the handlers (90 grep hits minus the `__init__.py:4` docstring mention).
Registration is `register(mcp)` per module calling `mcp.tool()(fn)` — NOT inline
`@mcp.tool` (the spec's "every handler is its own `@mcp.tool`" in §Why, line 35, is
imprecise: the decorator is applied programmatically in `register()`, e.g.
`skills.py:117-118`).

**Migration-map inventory: IDENTICAL to ground truth.** A `diff` of the spec's
89-row map (col 2) against the extracted real tool names is empty — every real tool
is mapped and no phantom tool is invented. Excellent.

### Real module → tool layout (authoritative; cite for the spec's §Why fix)

The spec §Why (lines 30-33) says "**eleven** handler modules: `streaming`, `skills`,
`text_analysis`, `promo`, `database`, `lyrics_analysis`, `rename`,
`processing/mixing`, `processing/video`, `processing/audio`, `album_ops`."
**This is wrong on three counts:** it is 19 modules (15 top-level + 4 under
`processing/`), it omits 8 of them, and it omits `processing/sheet_music`.
Registered in `server.py:338-353`:

| module (path:line of `register`) | # | tools |
|---|---|---|
| `core.py:1133` | 18 | find_album, list_albums, get_track, list_tracks, get_session, update_session, rebuild_state, get_config, get_python_command, get_ideas, search, get_pending_verifications, resolve_path, resolve_track_file, list_track_files, extract_section, update_track_field, get_album_progress |
| `content.py:262` | 3 | load_override, get_reference, format_for_clipboard |
| `text_analysis.py:980` | 7 | check_homographs, scan_artist_names, check_pronunciation_enforcement, check_explicit_content, **extract_links**, get_lyrics_stats, check_cross_track_repetition |
| `lyrics_analysis.py:929` | 5 | extract_distinctive_phrases, count_syllables, analyze_readability, analyze_rhyme_scheme, validate_section_structure |
| `album_ops.py:443` | 3 | get_album_full, validate_album_structure, create_album_structure |
| `gates.py:559` | 2 | run_pre_generation_gates, check_streaming_lyrics |
| `streaming.py:357` | 3 | get_streaming_urls, update_streaming_url, verify_streaming_urls |
| `skills.py:117` | 2 | list_skills, get_skill |
| `status.py:538` | 2 | update_album_status, create_track |
| `promo.py:160` | 2 | get_promo_status, get_promo_content |
| `health.py:578` | 4 | get_plugin_version, check_venv_health, health_check, diagnose |
| `ideas.py:474` | 3 | create_idea, update_idea, promote_idea |
| `rename.py:326` | 2 | rename_album, rename_track |
| `database.py:866` | 8 | db_init, db_list_tweets, db_create_tweet, db_update_tweet, db_delete_tweet, db_search_tweets, db_sync_album, db_get_tweet_stats |
| `maintenance.py:287` | 3 | reset_mastering, cleanup_legacy_venvs, migrate_audio_layout |
| `processing/audio.py:2120` | 12 | analyze_audio, qc_audio, master_audio, fix_dynamic_track, master_with_reference, master_album, render_codec_preview, mono_fold_check, **prune_archival**, measure_album_signature, album_coherence_check, album_coherence_correct |
| `processing/mixing.py:826` | 4 | polish_audio, analyze_mix_issues, polish_album, polish_and_master_album |
| `processing/sheet_music.py:698` | 4 | transcribe_audio, prepare_singles, create_songbook, publish_sheet_music |
| `processing/video.py:324` | 2 | generate_promo_videos, generate_album_sampler |

Sum = 89. (NB the spec maps `transcribe_audio`/`prepare_singles`/`create_songbook`/
`publish_sheet_music` to `AudioDriver`/`CloudDriver` from "`processing/audio`" — they
actually live in the *separate* `processing/sheet_music.py`, a module the spec never
names. The verb mapping itself is fine; the §Why narrative just under-counts.)

### Mapping corrections (cluster/driver fidelity — Fowler/Newman lens)

1. **`extract_links` is mis-clustered.** Spec map row #38 (line 228) and cluster 3
   ("state", line 148) assign it `StateDriver` and call it a path/link helper. It
   actually lives in `text_analysis.py:530` (registered `text_analysis.py:984`) — it
   is a **TextDriver / cluster-4** pure-text extractor, not a state read. Mis-routes
   the driver. *(Fowler: "you've put a text-analysis function behind the filesystem
   boundary — the boundary no longer maps to what the code touches.")*

2. **`prune_archival` lives in the audio handler, not state/maintenance.** Spec map
   row #35 (line 225) and cluster 3 assign it `StateDriver`. It is registered in
   `processing/audio.py:2129` (`async def prune_archival`, audio.py:1379) and uses
   audio-layout helpers. It is a filesystem *delete-of-archival-WAVs* operation —
   defensible as state, but the spec's claim that it sits with "session/config" and
   its sibling `migrate_audio_layout`/`reset_mastering` (which are in
   `maintenance.py` and `processing/audio.py`/`maintenance.py` respectively, NOT a
   single module) over-tidies the real layout. Either move it to the audio cluster
   or footnote that bitwize co-locates it with the audio pipeline.

3. **Role nit — `update_streaming_url` (#85, line 275)** is tagged `act` but the
   sibling reads/writes in cluster 7 are tagged `effect`/`transform`; it writes a
   streaming URL into the markdown state via StateDriver, so `effect` (a state
   side-effect) is the consistent tag. Minor.

Everything else in the 89-row map (drivers, roles, pipeline designations for
`master_album`/`polish_album`/`polish_and_master_album`) checks out. `master_album`
*is* genuinely a multi-stage pipeline — `processing/audio.py` docstring: "End-to-end
mastering pipeline: analyze, QC, master, verify, update status … Runs in three
phases, stopping on failure. See `_album_stages.py`." The single-pipeline-verb
decision is faithful.

### Backend / dependency corrections (Nygard lens — "what's the real failure surface?")

The Driver table (lines 124-130) and the internal-methods list (lines 166-169) name
backends that **do not match the source**:

1. **DBDriver is PostgreSQL (psycopg2), NOT SQLite — MUST FIX.** Spec says
   "the tweet/promo SQLite database … SQLite (`sqlite3`)" (line 129) and
   `DBDriver.connect()` (line 167). Ground truth: `database.py:19 _check_db_deps`
   imports **`psycopg2`**; `tools/database/connection.py:1` "PostgreSQL database
   connection helper", `get_connection()` calls `psycopg2.connect(host=…,
   connect_timeout=5)` reading credentials from a YAML config; `db_init` runs
   `tools/database/schema.sql` + a migrations dir. This invalidates the spec's
   implied "local sqlite file, no external account" testability story for the promo
   cluster: the real DBDriver needs a Postgres host + creds. The DEPENDENCY_MISSING
   stub recommendation (Open-Q #3) should explicitly extend to DBDriver, and the
   fake must model a Postgres-shaped connection, not a sqlite file.

2. **CloudDriver streaming check uses `urllib.request`, NOT `httpx`.** Spec says
   "streaming-URL checks … `httpx` + boto3/R2" (line 130) and `CloudDriver.head()`
   (line 168). Ground truth: `streaming.py:247-301` uses stdlib
   `urllib.request.urlopen(req, timeout=10)` for HEAD/GET. `httpx` is imported
   nowhere in the handlers. R2 publishing (`publish_sheet_music`,
   `processing/sheet_music.py:435`) does use **boto3** (`core.py`/`sheet_music.py`
   import boto3) — so split CloudDriver's two duties: URL-verify = stdlib urllib (no
   dep, testable today); R2 publish = boto3 + creds (DEPENDENCY_MISSING stub).

3. **`librosa` is not used; the real audio stack is `pyloudnorm` + ffmpeg(subprocess)
   + AnthemScore.** Spec AudioDriver backend (line 128) lists
   "`ffmpeg`/`librosa`/`pyloudnorm`/AnthemScore". Ground truth: `pyloudnorm` is
   imported (`processing/audio.py`, `processing/_helpers.py`, `core.py`); ffmpeg is
   invoked via `subprocess` in `processing/_album_stages.py` (and ffmpeg path checks
   in `health.py`/`_helpers.py`/`video.py`); AnthemScore is shelled out
   (`processing/_helpers.py::_check_anthemscore`, `sheet_music.py:54`). **`librosa`
   appears in zero handler imports.** Drop it (or verify it's a transitive dep) so
   the AudioDriver fake/real contract names the right libraries.

4. **TextDriver backend over-promises libraries.** Spec (line 127) says "stdlib +
   `pronouncing`/`textstat`". Neither `pronouncing` nor `textstat` is imported in
   `text_analysis.py` or `lyrics_analysis.py` — they use stdlib `re`, `threading`,
   `statistics` and module-level pattern tables (`_HOMOGRAPH_PATTERNS`,
   `_artist_blocklist_patterns`). The spec's own hedge "(or none — most are
   stdlib-pure)" (line 149) is the correct read; align the Driver table to it. This
   *strengthens* the spec's "driver-free transform" test (Done-When (c)).

---

## Gated-skill mapping (faithful, with one count caveat)

- **`run_pre_generation_gates` = exactly 8 gates — VERIFIED.**
  `gates.py:_check_pre_gen_gates_for_track` (lines 42-189) implements, in order:
  (1) Sources Verified, (2) Lyrics Reviewed, (3) Pronunciation Resolved,
  (4) Explicit Flag Set, (5) Style Prompt Complete, (6) Artist Names Cleared,
  (7) **Homograph Check**, (8) **Lyric Length**. The spec's gate-mapping table
  (line 291) enumerates "sources, lyrics, pronunciation, explicit, style box, artist
  names, …" and drops the last two by name — list all 8 so the `pre-generation`
  skill's `invoke:` phases are complete (the skill must call the homograph + length
  checks too, and only `check_explicit_content`/`scan_artist_names`/
  `check_pronunciation_enforcement` exist as standalone verbs; Sources/Lyrics/Style/
  Length are computed *inline inside* `run_pre_generation_gates`, not separate tools —
  so the "phases invoke the transform verbs" claim is only partially backed: 3 of 8
  checks have standalone verbs, the other 5 are internal to the gate function).

- **`gate.check` mapping is structurally correct.** `gate.py:20-32` —
  `check(lifecycle_id, name, passed, evidence)` records a `PASSED` edge or
  `BLOCKED_ON` + sets lifecycle `input-required`. This matches the spec's
  "PASSED / BLOCKED_ON + an input-required pause" and the GATE_FAILED ToolResult
  intent. Note the real `gate.check` signature requires a `lifecycle_id` that
  `SERVES` the current intent (cross-intent gates are rejected, `gate.py:23-27`) —
  the `pre-generation`/`release-qa` skills must thread a lifecycle id, which the spec
  should state in Done-When (e).

- **`release-qa` skill — confirm the real chain.** The spec maps it to
  "release-director 9-domain QA". The `release-director` SKILL.md (verified) is prose
  orchestration ("Run pre-release QA checklist, prepare distribution, uploads") and
  lists `bitwize-music-mcp` in allowed-tools, but there is **no single
  `run_release_gates` tool** — the QA is `validate_album_structure` +
  `check_streaming_lyrics` + manual checks. The spec's "9-domain QA" number is not
  grounded in a tool; soften to "the release-director prose chain" or cite where the
  9 domains come from.

---

## Missing surface

- **§Why module list (lines 30-33):** add the 8 omitted modules (`core`, `content`,
  `gates`, `status`, `health`, `ideas`, `maintenance`, `processing/sheet_music`) and
  correct "eleven" → "nineteen". As written it reads as if `core.py` (the single
  largest module, 18 tools / `core.py:39778` bytes) does not exist.
- **`processing/sheet_music.py`** is never named anywhere in the spec though it owns
  4 mapped tools (transcribe/prepare_singles/create_songbook/publish_sheet_music).
  Add it to the Driver table's "bitwize handler modules" column for AudioDriver/
  CloudDriver.
- **Internal-method realism:** the spec invents `DBDriver.connect()` /
  `CloudDriver.head()` against the wrong backends. Re-name to the real shapes
  (`DBDriver.cursor()` over psycopg2; `CloudDriver.url_head()` over urllib +
  `CloudDriver.r2_put()` over boto3).
- **Provenance "bonus" (lines 281-285)** is genuinely net-new vs bitwize and worth
  keeping — no correction, just confirming it is not in the source (bitwize records
  no shared trace; verified — no graph/provenance layer in handlers).

---

## Open-Questions triage

- **#1 Core vs examples — KEEP `examples/`.** Matches CLAUDE.md's standing rule
  ("Domain capabilities live OUT of the core as example extensions in `examples/`")
  and the existing `examples/music.py`. The catalogue's `agency/capabilities/`
  row is the stale one. Resolve by demoting the catalogue row, not the spec.
  *Resolved — no blocker.*
- **#2 Driver injection point — REAL BLOCKER until 001 is read.** Today
  `engine.py` injects only `client`/`vcs`. The spec needs 4 more injectors. This is
  the one core edit and the spec correctly flags it. **Confirm whether Spec-001's
  `DriverRegistry` shipped before coding** (the spec lists it conditionally in
  `affects:`). Cannot start cluster 5/7 verbs without this decided.
- **#3 Binary deps — ADOPT recommendation (b) stubs, AND extend it to DBDriver
  (Postgres) and the boto3 half of CloudDriver** (per the backend corrections
  above). The stdlib-urllib half of CloudDriver (`verify_streaming_urls`) needs NO
  stub — it works in CI today. Tighten the Open-Q to reflect the real per-driver dep
  matrix rather than lumping all of "audio/cloud" together.
- **#4 Gate granularity — RECOMMEND one aggregate `gate.check` after the 8 internal
  checks**, because only 3 of the 8 checks are standalone verbs (the other 5 are
  internal to `run_pre_generation_gates`); fine-grained per-gate edges would force
  exposing 5 currently-internal checks as verbs. Aggregate matches the real tool's
  single pass/fail-per-track return. (If per-gate provenance is wanted later, that is
  a refactor of the gate function, out of scope here.)
- **#5 Overlap with core (`list_skills`/`get_skill`/`search`/`health_check`/…)** —
  RECOMMEND: drop the venv-specific ones (`check_venv_health`, `cleanup_legacy_venvs`)
  as obsolete-once-one-engine (the whole per-tool-venv model disappears under
  Agency), keep `search`/`list_skills`/`get_skill` as thin domain verbs that
  `ctx.call` the core capability. The spec already raises this correctly; just record
  the decision so the migration map's "disposition" column stops saying "verb (see
  Open Q)" for 5 rows.
- **#6 StateDriver storage model — defer to the named `019-state-migration` spec**, as
  the spec says. For *this* spec, recommend option (b) (filesystem markdown 1:1) so
  007 is shippable without committing to the graph-native rewrite; flag (a) as the
  desirable end-state. *No blocker for 007 if (b) is adopted as the interim.*

---

## Must-fix list (block coding until done)

1. **DBDriver backend: PostgreSQL/psycopg2, not SQLite.** Fix Driver table (line 129),
   internal methods (line 167), and Open-Q #3. Source: `database.py:19`,
   `tools/database/connection.py:56-78`. Adjust the fake and the "no external
   account in CI" claim for cluster 7.
2. **CloudDriver: split urllib (URL-verify, stdlib, no stub) from boto3/R2 (publish,
   stub).** Replace the "`httpx`" claim (line 130, 168). Source: `streaming.py:247-301`
   (urllib), `processing/sheet_music.py:435` + boto3 import (R2).
3. **Fix §Why module inventory: "eleven" → 19, add the 8 omitted modules + name
   `processing/sheet_music`.** Source: `server.py:338-353`. Drop `librosa` from the
   AudioDriver backend and `pronouncing`/`textstat` from TextDriver (none imported);
   real audio stack = `pyloudnorm` + ffmpeg(subprocess) + AnthemScore.

### Should-fix (not blocking)

4. Re-cluster `extract_links` to TextDriver/cluster-4 (`text_analysis.py:530`); decide
   `prune_archival` placement (it is in `processing/audio.py:1379`, not state).
5. List all 8 pre-generation gates by name (add Homograph Check, Lyric Length) and
   note that only 3 of 8 have standalone verbs (the other 5 are internal to
   `run_pre_generation_gates`) — this directly affects the `pre-generation` skill's
   `invoke:` phase design and Open-Q #4.
6. Ground or soften the "9-domain QA" claim for `release-qa` (no single tool backs it;
   it is the release-director prose chain).
7. Resolve Open-Q #2 (driver injection / 001 `DriverRegistry`) before starting any
   driver-backed cluster — this is the single core-touching dependency.
