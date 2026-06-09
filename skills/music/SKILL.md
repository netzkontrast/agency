<!-- agency-generated: v1 -->
---
name: music
description: Use when conceptualizing or producing an album — turning an idea into a gated concept, mastering to a target loudness, drafting promo copy, or auditing a release — as the reference for how a first-class clustered domain capability extends agency.
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# music capability

Music graduates from ``examples/music.py`` into a first-class folder-form capability under ``agency/capabilities/music/`` (Spec 094). The CLAUDE.md + docs/vision/CAPABILITY-CLUSTERS.md doctrine exception is documented in those files; music remains the **reference clustered domain capability** but is no longer "third-party example" — it's the substrate's first creative-production domain.

## When to use

- An album idea that needs a structured, gated concept before production
- A music production step (master, promo, lyric analysis) that should be recorded as provenance
- A reference for how a clustered domain capability reaches external tools via Drivers

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `album_progress` | transform | Album progress aggregate via the StateDriver (transform). | [details](references/album_progress.md) |
| `analyze_mix` | transform | Analyse a mix for loudness issues via the AudioDriver (transform). | [details](references/analyze_mix.md) |
| `analyze_readability` | transform | Flesch-Kincaid-shaped readability over the lyric text (transform). | [details](references/analyze_readability.md) |
| `analyze_rhyme_scheme` | transform | Build a rhyme scheme (A/B/C labels) over the lyric lines (transform). | [details](references/analyze_rhyme_scheme.md) |
| `capture_idea` | effect | Capture a creative idea (effect) — record an Idea node, persist via StateDriver. | [details](references/capture_idea.md) |
| `catalogue_status` | transform | Read track statuses from the catalogue DB via the DBDriver (transform). | [details](references/catalogue_status.md) |
| `check_cross_track_repetition` | transform | Flag lyric lines repeated across multiple album tracks (transform). | [details](references/check_cross_track_repetition.md) |
| `check_explicit_content` | transform | Classify lyrics as clean / suggestive / explicit (transform). | [details](references/check_explicit_content.md) |
| `check_homographs` | transform | Flag words with multiple legitimate pronunciations (transform). | [details](references/check_homographs.md) |
| `check_pronunciation` | transform | Flag words requiring forced pronunciation per the bundled guide (transform). | [details](references/check_pronunciation.md) |
| `check_streaming_lyrics` | transform | Check the lyric body for platform-incompatible markup (transform). | [details](references/check_streaming_lyrics.md) |
| `check_voice_tells` | transform | AI-tell rule-based detector (advisory only — no gate impact) (transform). | [details](references/check_voice_tells.md) |
| `conceptualize` | act | Render an album-concept document (act); ``type`` must be a known album type. | [details](references/conceptualize.md) |
| `count_syllables` | transform | Count syllables in a word — deterministic, driver-free text math. | [details](#count_syllables) |
| `create_album` | effect | Create an album root + render the canonical templates (effect). | [details](references/create_album.md) |
| `create_track` | effect | Create a track in an album, rendered from the bitwize ``track`` template (effect). | [details](references/create_track.md) |
| `explicit_gate` | effect | Computed explicit-content gate (effect). | [details](references/explicit_gate.md) |
| `extract_distinctive_phrases` | transform | Return novel tri-grams (not in corpus) from the lyrics (transform). | [details](references/extract_distinctive_phrases.md) |
| `extract_section` | transform | Extract the body under a ``[<label>]`` section tag (transform). | [details](references/extract_section.md) |
| `find_album` | transform | Find albums by slug / fuzzy match via the StateDriver (transform). | [details](references/find_album.md) |
| `list_ideas` | transform | List captured ideas via the StateDriver (transform) — filter by status. | [details](references/list_ideas.md) |
| `list_tracks` | transform | List tracks for an album via the StateDriver (transform). | [details](references/list_tracks.md) |
| `lyric_report` | act | Analyze a lyric sheet's syllable load per line via the TextDriver (act). | [details](references/lyric_report.md) |
| `master_album` | effect | Master an audio file to a target loudness via the AudioDriver (effect). | [details](references/master_album.md) |
| `music_health` | transform | Self-check the music capability (transform, driver-free) — report which Driver seams are wired. | [details](references/music_health.md) |
| `pregen_check` | effect | Computed `pre-generation` gate — machine-checkable predicate (Spec 094). | [details](references/pregen_check.md) |
| `promo_copy` | act | Draft promotional copy for an album (act, produces a ``promo-copy`` artefact). | [details](references/promo_copy.md) |
| `promote_idea` | effect | Promote an Idea → Album (effect); record Album + PROMOTED_TO edge. | [details](references/promote_idea.md) |
| `pronunciation_gate` | effect | Computed pronunciation gate — composes pronunciation + homograph (effect). | [details](references/pronunciation_gate.md) |
| `prosody_gate` | effect | Computed prosody gate — composes rhyme + syllable checks (effect). | [details](references/prosody_gate.md) |
| `publish_asset` | effect | Publish an album asset to object storage via the CloudDriver (effect). | [details](references/publish_asset.md) |
| `release_check` | effect | Computed `release-qa` gate: every track mastered (read via the DBDriver). | [details](references/release_check.md) |
| `rename_album` | effect | Rename an album, mirroring paths via the StateDriver (effect). | [details](references/rename_album.md) |
| `rename_track` | effect | Rename a track within an album, mirroring paths via the StateDriver (effect). | [details](references/rename_track.md) |
| `repetition_gate` | effect | Computed cross-track repetition gate (effect). | [details](references/repetition_gate.md) |
| `resume_session` | transform | Restore the last-album context via the StateDriver (transform). | [details](references/resume_session.md) |
| `scan_artist_names` | transform | Scan for accidental artist-name drops against the blocklist (transform). | [details](references/scan_artist_names.md) |
| `set_album_status` | effect | Persist an album's production status via the StateDriver (effect). | [details](references/set_album_status.md) |
| `set_track_status` | effect | Persist a track's production status via the StateDriver (effect). | [details](references/set_track_status.md) |
| `transcribe_sheet` | act | Transcribe audio → sheet music via AudioDriver (act); produces sheet-music artefact. | [details](references/transcribe_sheet.md) |
| `validate_section_structure` | transform | Validate section tag well-formedness (Title Case in brackets) (transform). | [details](references/validate_section_structure.md) |
| `verify_streaming` | transform | Verify an album's streaming links are live via the CloudDriver (transform). | [details](references/verify_streaming.md) |

## Example

```bash
await call_tool('capability_music_album_progress', {'intent_id': 'intent:abc'})
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
- **`pre-generation`** (gate): concept-ready → rights-clear → approve
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'pre-generation', 'inputs': {}, 'intent_id': '…'})`
- **`release-qa`** (gate): mastered → metadata → ship
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'release-qa', 'inputs': {}, 'intent_id': '…'})`

## count_syllables

Count syllables in a word — deterministic, driver-free text math.

Parameters: `(word: 'str')`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/count_syllables.md.)_
