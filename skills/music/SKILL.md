---
name: music
description: "Use when conceptualizing or producing an album — turning an idea into a gated concept, mastering to a target loudness, drafting promo copy, or auditing a release — as the reference for how a first-class clustered domain capability extends agency."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# music capability

Music graduates from ``examples/music.py`` into a first-class folder-form capability under ``agency/capabilities/music/`` (Spec 094). The CLAUDE.md + docs/vision/CAPABILITY-CLUSTERS.md doctrine exception is documented in those files; music remains the **reference clustered domain capability** but is no longer "third-party example" — it's the substrate's first creative-production domain.

## When to use

- An album idea that needs a structured, gated concept before production
- A music production step (master, promo, lyric analysis) that should be recorded as provenance
- A reference for how a clustered domain capability reaches external tools via Drivers

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `album_coherence_check` | transform | Cross-track tonal coherence report via AudioDriver (transform). | [details](references/album_coherence_check.md) |
| `album_coherence_correct` | effect | Apply coherence corrections to bring outliers in line (effect). | [details](references/album_coherence_correct.md) |
| `album_progress` | transform | Album progress aggregate via the StateDriver (transform). | [details](references/album_progress.md) |
| `analyze_audio` | transform | General spectral + loudness probe via AudioDriver (transform). | [details](references/analyze_audio.md) |
| `analyze_mix` | transform | Analyse a mix for loudness issues via the AudioDriver (transform). | [details](references/analyze_mix.md) |
| `analyze_readability` | transform | Flesch-Kincaid-shaped readability over the lyric text (transform). | [details](references/analyze_readability.md) |
| `analyze_rhyme_scheme` | transform | Build a rhyme scheme (A/B/C labels) over the lyric lines (transform). | [details](references/analyze_rhyme_scheme.md) |
| `audio_release_gate` | effect | Composite audio-release gate — every track QC-passed (effect). | [details](references/audio_release_gate.md) |
| `capture_claim` | effect | Record a ResearchClaim node SERVES the intent (effect). | [details](references/capture_claim.md) |
| `capture_idea` | effect | Capture a creative idea (effect) — record an Idea node, persist via StateDriver. | [details](references/capture_idea.md) |
| `catalogue_gate` | effect | Catalogue-synced gate — streaming URLs + tweets ready (effect). | [details](references/catalogue_gate.md) |
| `catalogue_status` | transform | Read track statuses from the catalogue DB via the DBDriver (transform). | [details](references/catalogue_status.md) |
| `check_cross_track_repetition` | transform | Flag lyric lines repeated across multiple album tracks (transform). | [details](references/check_cross_track_repetition.md) |
| `check_explicit_content` | transform | Classify lyrics as clean / suggestive / explicit (transform). | [details](references/check_explicit_content.md) |
| `check_homographs` | transform | Flag words with multiple legitimate pronunciations (transform). | [details](references/check_homographs.md) |
| `check_name_exposure` | transform | Scan text for forbidden roster names (driver-free, deterministic) (transform). | [details](references/check_name_exposure.md) |
| `check_pronunciation` | transform | Flag words requiring forced pronunciation per the bundled guide (transform). | [details](references/check_pronunciation.md) |
| `check_streaming_lyrics` | transform | Check the lyric body for platform-incompatible markup (transform). | [details](references/check_streaming_lyrics.md) |
| `check_voice_tells` | transform | AI-tell rule-based detector (advisory only — no gate impact) (transform). | [details](references/check_voice_tells.md) |
| `concept_gate` | effect | Pre-generation gate: concept exists for the album (effect). | [details](references/concept_gate.md) |
| `conceptualize` | act | Render an album-concept document for a known album ``type`` (act). | [details](references/conceptualize.md) |
| `count_syllables` | transform | Count syllables in a word — deterministic, driver-free text math. | [details](#count_syllables) |
| `create_album` | effect | Create an album root + render the canonical templates (effect). | [details](references/create_album.md) |
| `create_songbook` | effect | LilyPond → PDF songbook render via AudioDriver (effect). | [details](references/create_songbook.md) |
| `create_track` | effect | Create a track in an album, rendered from the bitwize ``track`` template (effect). | [details](references/create_track.md) |
| `db_create_tweet` | effect | Insert a tweet row via the DBDriver, producing a tweet-record artefact (effect). | [details](references/db_create_tweet.md) |
| `db_delete_tweet` | effect | Delete a tweet row via the DBDriver (effect). | [details](references/db_delete_tweet.md) |
| `db_get_tweet_stats` | transform | Aggregate counts of tweets by status via DBDriver (transform). | [details](references/db_get_tweet_stats.md) |
| `db_list_tweets` | transform | List tweets via the DBDriver, filtered by album + status (transform). | [details](references/db_list_tweets.md) |
| `db_search_tweets` | transform | Substring search across tweet bodies via DBDriver (transform). | [details](references/db_search_tweets.md) |
| `db_sync_album` | effect | Idempotent sync of an album's tweets — replaces existing (effect). | [details](references/db_sync_album.md) |
| `db_update_tweet` | effect | Update tweet row fields via the DBDriver (effect). | [details](references/db_update_tweet.md) |
| `diagnose` | transform | Composite driver-free health probe (transform). | [details](references/diagnose.md) |
| `dispatch_research` | effect | Fan out to N specialists via agency.research (effect). | [details](references/dispatch_research.md) |
| `document_hunt` | effect | Dispatch a document-hunter specialist via agency.research (effect). | [details](references/document_hunt.md) |
| `explicit_gate` | effect | Computed explicit-content gate (effect). | [details](references/explicit_gate.md) |
| `extract_distinctive_phrases` | transform | Return novel tri-grams (not in corpus) from the lyrics (transform). | [details](references/extract_distinctive_phrases.md) |
| `extract_links` | transform | Extract URLs from text via simple regex (transform). | [details](references/extract_links.md) |
| `extract_section` | transform | Extract the body under a ``[<label>]`` section tag (transform). | [details](references/extract_section.md) |
| `find_album` | transform | Find albums by slug / fuzzy match via the StateDriver (transform). | [details](references/find_album.md) |
| `fix_dynamic_track` | effect | Dynamic range fixer — applies compression/expansion (effect). | [details](references/fix_dynamic_track.md) |
| `format_clipboard` | transform | Format text for clipboard paste into Suno / other generation services (transform). | [details](references/format_clipboard.md) |
| `generate_promo_videos` | effect | Render a vertical promo video via AudioDriver (effect). | [details](references/generate_promo_videos.md) |
| `get_config` | transform | Read the music capability's loaded config (transform). | [details](references/get_config.md) |
| `get_promo_content` | transform | Read promo content (drafts + scheduled tweets) via DBDriver (transform). | [details](references/get_promo_content.md) |
| `get_promo_status` | transform | Per-album promo state via StateDriver + DBDriver (transform). | [details](references/get_promo_status.md) |
| `get_reference` | transform | Read a bundled reference / data file by slug (transform). | [details](references/get_reference.md) |
| `get_streaming_urls` | transform | Read recorded streaming URLs for an album via StateDriver (transform). | [details](references/get_streaming_urls.md) |
| `human_signoff` | effect | Record terminal human approval for the album's research (effect). | [details](references/human_signoff.md) |
| `list_claims` | transform | List ResearchClaim nodes (transform). | [details](references/list_claims.md) |
| `list_ideas` | transform | List captured ideas via the StateDriver (transform) — filter by status. | [details](references/list_ideas.md) |
| `list_tracks` | transform | List tracks for an album via the StateDriver (transform). | [details](references/list_tracks.md) |
| `load_override` | transform | Load a user-authored override file from the configured overrides dir (transform). | [details](references/load_override.md) |
| `lyric_report` | act | Analyze a lyric sheet's syllable load per line via the TextDriver (act). | [details](references/lyric_report.md) |
| `lyrics_pregen_gate` | effect | Composite lyrics pre-generation gate — chains the lyric gates (effect). | [details](references/lyrics_pregen_gate.md) |
| `master_album` | effect | Master an audio file to a target loudness via the AudioDriver (effect). | [details](references/master_album.md) |
| `master_audio` | effect | Master a single track via AudioDriver, producing a mastering-report (effect). | [details](references/master_audio.md) |
| `master_with_reference` | effect | Master `path` to match `reference` album loudness (effect). | [details](references/master_with_reference.md) |
| `measure_album_signature` | transform | Spectral signatures for an album's tracks via AudioDriver (transform). | [details](references/measure_album_signature.md) |
| `measure_gate` | effect | Computed measure gate — composes loudness probe + range check (effect). | [details](references/measure_gate.md) |
| `mono_fold_check` | transform | Phase-cancellation check via AudioDriver (transform). | [details](references/mono_fold_check.md) |
| `music_health` | transform | Self-check the music capability (transform, driver-free) — report which Driver seams are wired. | [details](references/music_health.md) |
| `name_exposure_gate` | effect | Computed name-exposure gate — no forbidden roster names in lyrics (effect). | [details](references/name_exposure_gate.md) |
| `pending_verifications` | transform | Aggregate count of pending claims (transform). | [details](references/pending_verifications.md) |
| `polish_album` | effect | Album-wide polish pass — applies polish to every track (effect). | [details](references/polish_album.md) |
| `polish_and_master_album` | effect | Run the combined polish + master pipeline, producing a mastering-report (effect). | [details](references/polish_and_master_album.md) |
| `polish_audio` | effect | Per-track polish pass via AudioDriver (effect). | [details](references/polish_audio.md) |
| `pregen_check` | effect | Computed `pre-generation` gate — machine-checkable predicate (Spec 094). | [details](references/pregen_check.md) |
| `promo_copy` | act | Draft promotional copy for an album (act, produces a ``promo-copy`` artefact). | [details](references/promo_copy.md) |
| `promo_gate` | effect | Promo-drafted gate — at least 1 promo asset exists (effect). | [details](references/promo_gate.md) |
| `promo_review` | transform | Rule-based scoring of promo copy quality (transform). | [details](references/promo_review.md) |
| `promo_review_gate` | effect | Computed promo-review gate (effect) — composes ``promo_review`` scoring. | [details](references/promo_review_gate.md) |
| `promote_idea` | effect | Promote an Idea to an Album, recording the Album + PROMOTED_TO edge (effect). | [details](references/promote_idea.md) |
| `pronunciation_gate` | effect | Computed pronunciation gate — composes pronunciation + homograph (effect). | [details](references/pronunciation_gate.md) |
| `prosody_gate` | effect | Computed prosody gate — composes rhyme + syllable checks (effect). | [details](references/prosody_gate.md) |
| `publish_asset` | effect | Publish an album asset to object storage via the CloudDriver (effect). | [details](references/publish_asset.md) |
| `publish_sheet_music` | effect | Publish a sheet-music PDF to object storage (effect). | [details](references/publish_sheet_music.md) |
| `qc_audio` | transform | 7-point QC checklist via AudioDriver (transform). | [details](references/qc_audio.md) |
| `qc_gate` | effect | Computed QC gate — composes 7-point QC checklist (effect). | [details](references/qc_gate.md) |
| `r2_delete` | effect | Retract a published asset from object storage (effect). | [details](references/r2_delete.md) |
| `r2_list` | transform | List published assets by key prefix (transform). | [details](references/r2_list.md) |
| `release_check` | effect | Computed `release-qa` gate: every track mastered (read via the DBDriver). | [details](references/release_check.md) |
| `release_package` | act | Record a release package — gathers all release artefact paths (act). | [details](references/release_package.md) |
| `rename_album` | effect | Rename an album, mirroring paths via the StateDriver (effect). | [details](references/rename_album.md) |
| `rename_track` | effect | Rename a track within an album, mirroring paths via the StateDriver (effect). | [details](references/rename_track.md) |
| `render_codec_preview` | effect | Render a streaming-codec preview via AudioDriver (effect). | [details](references/render_codec_preview.md) |
| `repetition_gate` | effect | Computed cross-track repetition gate (effect). | [details](references/repetition_gate.md) |
| `research_scope` | act | Define a research question + plan specialist domains (act). | [details](references/research_scope.md) |
| `reset_mastering` | effect | Revert all master/polish state for an album (effect). | [details](references/reset_mastering.md) |
| `resume_session` | transform | Restore the last-album context via the StateDriver (transform). | [details](references/resume_session.md) |
| `scan_artist_names` | transform | Scan for accidental artist-name drops against the blocklist (transform). | [details](references/scan_artist_names.md) |
| `set_album_status` | effect | Persist an album's production status via the StateDriver (effect). | [details](references/set_album_status.md) |
| `set_track_status` | effect | Persist a track's production status via the StateDriver (effect). | [details](references/set_track_status.md) |
| `transcribe_sheet` | act | Transcribe audio to sheet music via AudioDriver, producing a sheet-music artefact (act). | [details](references/transcribe_sheet.md) |
| `tweet_schedule_gate` | effect | Computed tweet-schedule gate (effect) — composes 3 checks. | [details](references/tweet_schedule_gate.md) |
| `update_streaming_url` | effect | Persist a verified streaming URL via StateDriver (effect). | [details](references/update_streaming_url.md) |
| `upload_promo_video` | effect | Upload a promo video to object storage (effect). | [details](references/upload_promo_video.md) |
| `validate_album` | transform | Validate album file presence + mirror-path consistency via StateDriver (transform). | [details](references/validate_album.md) |
| `validate_section_structure` | transform | Validate section tag well-formedness (Title Case in brackets) (transform). | [details](references/validate_section_structure.md) |
| `validate_sections` | transform | Validate lyric section structure across an album (transform). | [details](references/validate_sections.md) |
| `verify_gate` | effect | Computed verification gate — composes pending_verifications (effect). | [details](references/verify_gate.md) |
| `verify_sources` | effect | Cross-check pending claims (effect). | [details](references/verify_sources.md) |
| `verify_streaming` | transform | Verify an album's streaming links are live via the CloudDriver (transform). | [details](references/verify_streaming.md) |

## Example

```bash
await call_tool('capability_music_album_coherence_check', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Shelling out to ffmpeg/Postgres/R2 directly → route through a Spec-002 Driver via ctx.get_driver
- Producing a document without an artefact → set data['artefact'] so the Registry records PRODUCES

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`album-concept`** (conceptualizer): foundation → concept → sonic → structure → art → practical → confirmation
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'album-concept', 'inputs': {}, 'intent_id': '…'})`
- **`lyric-writing`** (workflow): draft → prosody → pronunciation → cross-track → explicit → finalize
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'lyric-writing', 'inputs': {}, 'intent_id': '…'})`
- **`mastering`** (workflow): measure → polish → master → qc → coherence
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'mastering', 'inputs': {}, 'intent_id': '…'})`
- **`mix-polish`** (workflow): transcribe-stems → polish-per-stem → remix → loudness-check
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'mix-polish', 'inputs': {}, 'intent_id': '…'})`
- **`new-album`** (workflow): parse-args → validate-genre → check-existing → create-structure → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'new-album', 'inputs': {}, 'intent_id': '…'})`
- **`pre-generation`** (gate): concept-ready → rights-clear → approve
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'pre-generation', 'inputs': {}, 'intent_id': '…'})`
- **`pre-generation-full`** (workflow): concept-ready → research-verified → lyrics-clean → ready-to-generate
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'pre-generation-full', 'inputs': {}, 'intent_id': '…'})`
- **`promo-pass`** (workflow): draft → review → asset-attach → schedule → publish
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'promo-pass', 'inputs': {}, 'intent_id': '…'})`
- **`release-publish`** (workflow): gather-assets → upload → catalogue-update → announce
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'release-publish', 'inputs': {}, 'intent_id': '…'})`
- **`release-qa`** (gate): mastered → metadata → ship
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'release-qa', 'inputs': {}, 'intent_id': '…'})`
- **`release-qa-full`** (workflow): audio-mastered → catalogue-synced → promo-drafted → ship
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'release-qa-full', 'inputs': {}, 'intent_id': '…'})`
- **`research-workflow`** (workflow): scope → dispatch-specialists → collect → verify → human-sign-off
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'research-workflow', 'inputs': {}, 'intent_id': '…'})`
- **`streaming-verify`** (workflow): collect → head-check → record
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'streaming-verify', 'inputs': {}, 'intent_id': '…'})`
- **`tweet-curation`** (workflow): draft → schedule → publish → archive
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'tweet-curation', 'inputs': {}, 'intent_id': '…'})`
- **`validate-structure`** (workflow): album-files → track-files → mirror-paths
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'validate-structure', 'inputs': {}, 'intent_id': '…'})`

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_music_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_music_album_coherence_check", {"intent_id": iid})
await call_tool("capability_music_album_coherence_correct", {"intent_id": iid})
await call_tool("capability_music_album_progress", {"intent_id": iid})
await call_tool("capability_music_analyze_audio", {"intent_id": iid})
await call_tool("capability_music_analyze_mix", {"intent_id": iid})
await call_tool("capability_music_analyze_readability", {"intent_id": iid})
```

More verbs: `capability_music_analyze_rhyme_scheme`, `capability_music_audio_release_gate`, `capability_music_capture_claim`, `capability_music_capture_idea`, `capability_music_catalogue_gate`, `capability_music_catalogue_status`, `capability_music_check_cross_track_repetition`, `capability_music_check_explicit_content` …

## count_syllables

Count syllables in a word — deterministic, driver-free text math.

Parameters: `(word: 'str')`.
