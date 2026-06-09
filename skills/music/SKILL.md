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
| `capture_idea` | effect | Capture a creative idea (effect) — record an Idea node, persist via StateDriver. | [details](references/capture_idea.md) |
| `catalogue_status` | transform | Read track statuses from the catalogue DB via the DBDriver (transform). | [details](references/catalogue_status.md) |
| `conceptualize` | act | Render an album-concept document (act); ``type`` must be a known album type. | [details](references/conceptualize.md) |
| `count_syllables` | transform | Count syllables in a word — deterministic, driver-free text math. | [details](#count_syllables) |
| `create_album` | effect | Create an album root + render the canonical templates (effect). | [details](references/create_album.md) |
| `create_track` | effect | Create a track in an album, rendered from the bitwize ``track`` template (effect). | [details](references/create_track.md) |
| `find_album` | transform | Find albums by slug / fuzzy match via the StateDriver (transform). | [details](references/find_album.md) |
| `format_clipboard` | transform | Format text for clipboard paste into Suno / other generation services (transform). | [details](references/format_clipboard.md) |
| `get_config` | transform | Read the music capability's loaded config (transform). | [details](references/get_config.md) |
| `get_reference` | transform | Read a bundled reference / data file by slug (transform). | [details](references/get_reference.md) |
| `list_ideas` | transform | List captured ideas via the StateDriver (transform) — filter by status. | [details](references/list_ideas.md) |
| `list_tracks` | transform | List tracks for an album via the StateDriver (transform). | [details](references/list_tracks.md) |
| `load_override` | transform | Load a user-authored override file from the configured overrides dir (transform). | [details](references/load_override.md) |
| `lyric_report` | act | Analyze a lyric sheet's syllable load per line via the TextDriver (act). | [details](references/lyric_report.md) |
| `master_album` | effect | Master an audio file to a target loudness via the AudioDriver (effect). | [details](references/master_album.md) |
| `music_health` | transform | Self-check the music capability (transform, driver-free) — report which Driver seams are wired. | [details](references/music_health.md) |
| `pregen_check` | effect | Computed `pre-generation` gate — machine-checkable predicate (Spec 094). | [details](references/pregen_check.md) |
| `promo_copy` | act | Draft promotional copy for an album (act, produces a ``promo-copy`` artefact). | [details](references/promo_copy.md) |
| `promote_idea` | effect | Promote an Idea → Album (effect); record Album + PROMOTED_TO edge. | [details](references/promote_idea.md) |
| `publish_asset` | effect | Publish an album asset to object storage via the CloudDriver (effect). | [details](references/publish_asset.md) |
| `release_check` | effect | Computed `release-qa` gate: every track mastered (read via the DBDriver). | [details](references/release_check.md) |
| `rename_album` | effect | Rename an album, mirroring paths via the StateDriver (effect). | [details](references/rename_album.md) |
| `rename_track` | effect | Rename a track within an album, mirroring paths via the StateDriver (effect). | [details](references/rename_track.md) |
| `resume_session` | transform | Restore the last-album context via the StateDriver (transform). | [details](references/resume_session.md) |
| `set_album_status` | effect | Persist an album's production status via the StateDriver (effect). | [details](references/set_album_status.md) |
| `set_track_status` | effect | Persist a track's production status via the StateDriver (effect). | [details](references/set_track_status.md) |
| `transcribe_sheet` | act | Transcribe audio → sheet music via AudioDriver (act); produces sheet-music artefact. | [details](references/transcribe_sheet.md) |
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
- **`new-album`** (workflow): parse-args → validate-genre → check-existing → create-structure → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'new-album', 'inputs': {}, 'intent_id': '…'})`
- **`pre-generation`** (gate): concept-ready → rights-clear → approve
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'pre-generation', 'inputs': {}, 'intent_id': '…'})`
- **`release-qa`** (gate): mastered → metadata → ship
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'release-qa', 'inputs': {}, 'intent_id': '…'})`

## count_syllables

Count syllables in a word — deterministic, driver-free text math.

Parameters: `(word: 'str')`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/count_syllables.md.)_
