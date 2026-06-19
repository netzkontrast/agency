---
capability: music
pillar: capability
vision_goals: [2, 4]
status: living
last_generated: 2026-06-19
sources: [7, 93, 115, 117]
---

# music — Music graduates from ``examples/music.py`` into a first-class folder-form capability under ``agency/capabilities/music/`` (Spec 094) (capability pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
Music is the reference clustered domain capability — demonstrating how a first-class creative-production domain (lyrics, audio, promo, catalogue) reaches external tools via Drivers and records every step as provenance in the graph.

## Verbs (generated · 103)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `music.album_coherence_check` | transform | **album** · **paths** | Cross-track tonal coherence report via AudioDriver (transform). |
| `music.album_coherence_correct` | effect | **album** · **paths** · target | Apply coherence corrections to bring outliers in line (effect). |
| `music.album_progress` | transform | **album** | Album progress aggregate via the StateDriver (transform). |
| `music.analyze_audio` | transform | **album** · **path** | General spectral + loudness probe via AudioDriver (transform). |
| `music.analyze_mix` | transform | **album** · **path** | Analyse a mix for loudness issues via the AudioDriver (transform). |
| `music.analyze_readability` | transform | **text_** | Flesch-Kincaid-shaped readability over the lyric text (transform). |
| `music.analyze_rhyme_scheme` | transform | **lyrics** | Build a rhyme scheme (A/B/C labels) over the lyric lines (transform). |
| `music.audio_release_gate` | effect | **lifecycle_id** · **album** | Composite audio-release gate — every track QC-passed (effect). |
| `music.capture_claim` | effect | **text** · **source_uri** · **domain** · album · confidence | Record a ResearchClaim node SERVES the intent (effect). |
| `music.capture_idea` | effect | **text** | Capture a creative idea (effect) — record an Idea node, persist via StateDriver. |
| `music.catalogue_gate` | effect | **lifecycle_id** · **album** | Catalogue-synced gate — streaming URLs + tweets ready (effect). |
| `music.catalogue_status` | transform | album | Read track statuses from the catalogue DB via the DBDriver (transform). |
| `music.check_cross_track_repetition` | transform | **tracks** | Flag lyric lines repeated across multiple album tracks (transform). |
| `music.check_explicit_content` | transform | **lyrics** | Classify lyrics as clean / suggestive / explicit (transform). |
| `music.check_homographs` | transform | **lyrics** | Flag words with multiple legitimate pronunciations (transform). |
| `music.check_name_exposure` | transform | **text** · roster | Scan text for forbidden roster names (driver-free, deterministic) (transform). |
| `music.check_pronunciation` | transform | **lyrics** | Flag words requiring forced pronunciation per the bundled guide (transform). |
| `music.check_streaming_lyrics` | transform | **lyrics** · platform | Check the lyric body for platform-incompatible markup (transform). |
| `music.check_voice_tells` | transform | **lyrics** | AI-tell rule-based detector (advisory only — no gate impact) (transform). |
| `music.concept_gate` | effect | **lifecycle_id** · **album** | Pre-generation gate: concept exists for the album (effect). |
| `music.conceptualize` | act | **artist** · **title** · **type** · theme · tracklist | Render an album-concept document (act); ``type`` must be a known album type. |
| `music.count_syllables` | transform | **word** | Count syllables in a word — deterministic, driver-free text math. |
| `music.create_album` | effect | **artist** · **title** · **genre** · type | Create an album root + render the canonical templates (effect). |
| `music.create_songbook` | effect | **album** · **tracks** | LilyPond → PDF songbook render via AudioDriver (effect). |
| `music.create_track` | effect | **album** · **title** · track_number | Create a track in an album, rendered from the bitwize ``track`` template (effect). |
| `music.db_create_tweet` | effect | **album** · **body** · **scheduled_at** · platform | Insert a tweet row via the DBDriver (effect); produces tweet-record artefact. |
| `music.db_delete_tweet` | effect | **tweet_id** | Delete a tweet row via the DBDriver (effect). |
| `music.db_get_tweet_stats` | transform | album | Aggregate counts of tweets by status via DBDriver (transform). |
| `music.db_list_tweets` | transform | album · status · limit | List tweets via the DBDriver, filtered by album + status (transform). |
| `music.db_search_tweets` | transform | **query** · limit | Substring search across tweet bodies via DBDriver (transform). |
| `music.db_sync_album` | effect | **album** · **tweets** | Idempotent sync of an album's tweets — replaces existing (effect). |
| `music.db_update_tweet` | effect | **tweet_id** · **fields** | Update tweet row fields via the DBDriver (effect). |
| `music.diagnose` | transform |  | Composite driver-free health probe (transform). |
| `music.dispatch_research` | effect | **research_id** · specialists · album | Fan out to N specialists via agency.research (effect). |
| `music.document_hunt` | effect | **query** · domain | Dispatch a document-hunter specialist via agency.research (effect). |
| `music.explicit_gate` | effect | **lifecycle_id** · **lyrics** · allow_explicit | Computed explicit-content gate (effect). |
| `music.extract_distinctive_phrases` | transform | **lyrics** · corpus | Return novel tri-grams (not in corpus) from the lyrics (transform). |
| `music.extract_links` | transform | **text** | Extract URLs from text via simple regex (transform). |
| `music.extract_section` | transform | **lyrics** · **label** | Extract the body under a ``[<label>]`` section tag (transform). |
| `music.find_album` | transform | query | Find albums by slug / fuzzy match via the StateDriver (transform). |
| `music.fix_dynamic_track` | effect | **album** · **path** · target_dr | Dynamic range fixer — applies compression/expansion (effect). |
| `music.format_clipboard` | transform | **text** · format | Format text for clipboard paste into Suno / other generation services (transform). |
| `music.generate_promo_videos` | effect | **album** · **audio** · **art** · template | Render a vertical promo video via AudioDriver (effect). |
| `music.get_config` | transform |  | Read the music capability's loaded config (transform). |
| `music.get_promo_content` | transform | **album** | Read promo content (drafts + scheduled tweets) via DBDriver (transform). |
| `music.get_promo_status` | transform | **album** | Per-album promo state via StateDriver + DBDriver (transform). |
| `music.get_reference` | transform | **slug** · kind | Read a bundled reference / data file by slug (transform). |
| `music.get_streaming_urls` | transform | **album** | Read recorded streaming URLs for an album via StateDriver (transform). |
| `music.human_signoff` | effect | **album** · reviewer | Record terminal human approval for the album's research (effect). |
| `music.list_claims` | transform | album · status | List ResearchClaim nodes (transform). |
| `music.list_ideas` | transform | status | List captured ideas via the StateDriver (transform) — filter by status. |
| `music.list_tracks` | transform | **album** | List tracks for an album via the StateDriver (transform). |
| `music.load_override` | transform | **name** | Load a user-authored override file from the configured overrides dir (transform). |
| `music.lyric_report` | act | **album** · **lyrics** | Analyze a lyric sheet's syllable load per line via the TextDriver (act). |
| `music.lyrics_pregen_gate` | effect | **lifecycle_id** · **album** · lyrics | Composite lyrics pre-generation gate — chains the lyric gates (effect). |
| `music.master_album` | effect | **album** · **path** · target_lufs | Master an audio file to a target loudness via the AudioDriver (effect). |
| `music.master_audio` | effect | **album** · **path** · target_lufs · preset | Single-track master via AudioDriver (effect); produces mastering-report. |
| `music.master_with_reference` | effect | **album** · **path** · **reference** | Master `path` to match `reference` album loudness (effect). |
| `music.measure_album_signature` | transform | **album** · **paths** | Spectral signatures for an album's tracks via AudioDriver (transform). |
| `music.measure_gate` | effect | **lifecycle_id** · **path** · min_lufs · max_lufs | Computed measure gate — composes loudness probe + range check (effect). |
| `music.mono_fold_check` | transform | **album** · **path** | Phase-cancellation check via AudioDriver (transform). |
| `music.music_health` | transform |  | Self-check the music capability (transform, driver-free) — report which Driver seams are wired. |
| `music.name_exposure_gate` | effect | **lifecycle_id** · **lyrics** · roster | Computed name-exposure gate — no forbidden roster names in lyrics (effect). |
| `music.pending_verifications` | transform | album | Aggregate count of pending claims (transform). |
| `music.polish_album` | effect | **album** · **paths** | Album-wide polish pass — applies polish to every track (effect). |
| `music.polish_and_master_album` | effect | **album** · **paths** · target_lufs | Combined polish + master pipeline (effect); produces mastering-report. |
| `music.polish_audio` | effect | **album** · **path** | Per-track polish pass via AudioDriver (effect). |
| `music.pregen_check` | effect | **lifecycle_id** · concept_ready · rights_clear | Computed `pre-generation` gate — machine-checkable predicate (Spec 094). |
| `music.promo_copy` | act | **album** · angle | Draft promotional copy for an album (act, produces a ``promo-copy`` artefact). |
| `music.promo_gate` | effect | **lifecycle_id** · **album** | Promo-drafted gate — at least 1 promo asset exists (effect). |
| `music.promo_review` | transform | **body** · platform | Rule-based scoring of promo copy quality (transform). |
| `music.promo_review_gate` | effect | **lifecycle_id** · **body** · platform · min_score | Computed promo-review gate (effect) — composes ``promo_review`` scoring. |
| `music.promote_idea` | effect | **idea_id** · **artist** · **title** · **genre** · type | Promote an Idea → Album (effect); record Album + PROMOTED_TO edge. |
| `music.pronunciation_gate` | effect | **lifecycle_id** · **lyrics** | Computed pronunciation gate — composes pronunciation + homograph (effect). |
| `music.prosody_gate` | effect | **lifecycle_id** · **lyrics** · syllable_target | Computed prosody gate — composes rhyme + syllable checks (effect). |
| `music.publish_asset` | effect | **album** · **key** · body | Publish an album asset to object storage via the CloudDriver (effect). |
| `music.publish_sheet_music` | effect | **album** · **key** · body | Publish a sheet-music PDF to object storage (effect). |
| `music.qc_audio` | transform | **album** · **path** | 7-point QC checklist via AudioDriver (transform). |
| `music.qc_gate` | effect | **lifecycle_id** · **path** | Computed QC gate — composes 7-point QC checklist (effect). |
| `music.r2_delete` | effect | **key** | Retract a published asset from object storage (effect). |
| `music.r2_list` | transform | prefix | List published assets by key prefix (transform). |
| `music.release_check` | effect | **lifecycle_id** · album | Computed `release-qa` gate: every track mastered (read via the DBDriver). |
| `music.release_package` | act | **album** · **assets** | Record a release package — gathers all release artefact paths (act). |
| `music.rename_album` | effect | **old_slug** · **new_slug** | Rename an album, mirroring paths via the StateDriver (effect). |
| `music.rename_track` | effect | **album** · **old_slug** · **new_slug** | Rename a track within an album, mirroring paths via the StateDriver (effect). |
| `music.render_codec_preview` | effect | **album** · **path** · codec | Render a streaming-codec preview via AudioDriver (effect). |
| `music.repetition_gate` | effect | **lifecycle_id** · **tracks** | Computed cross-track repetition gate (effect). |
| `music.research_scope` | act | **question** · album · depth | Define a research question + plan specialist domains (act). |
| `music.reset_mastering` | effect | **album** | Revert all master/polish state for an album (effect). |
| `music.resume_session` | transform |  | Restore the last-album context via the StateDriver (transform). |
| `music.scan_artist_names` | transform | **lyrics** · allow | Scan for accidental artist-name drops against the blocklist (transform). |
| `music.set_album_status` | effect | **album** · **status** | Persist an album's production status via the StateDriver (effect). |
| `music.set_track_status` | effect | **album** · **track** · **status** | Persist a track's production status via the StateDriver (effect). |
| `music.transcribe_sheet` | act | **album** · **path** | Transcribe audio → sheet music via AudioDriver (act); produces sheet-music artefact. |
| `music.tweet_schedule_gate` | effect | **lifecycle_id** · **body** · **scheduled_at** · platform · max_length | Computed tweet-schedule gate (effect) — composes 3 checks. |
| `music.update_streaming_url` | effect | **album** · **platform** · **url** | Persist a verified streaming URL via StateDriver (effect). |
| `music.upload_promo_video` | effect | **album** · **key** · body | Upload a promo video to object storage (effect). |
| `music.validate_album` | transform | **album** | Validate album file presence + mirror-path consistency via StateDriver (transform). |
| `music.validate_section_structure` | transform | **lyrics** | Validate section tag well-formedness (Title Case in brackets) (transform). |
| `music.validate_sections` | transform | **album** · lyrics | Validate lyric section structure across an album (transform). |
| `music.verify_gate` | effect | **lifecycle_id** · album | Computed verification gate — composes pending_verifications (effect). |
| `music.verify_sources` | effect | album | Cross-check pending claims (effect). |
| `music.verify_streaming` | transform | **album** · urls | Verify an album's streaming links are live via the CloudDriver (transform). |

## Ontology (generated)

**Nodes:** `Album`(artist, title, type, status, genre, slug, target_lufs) · `Track`(title, status, slug) · `Tweet`(text) · `Idea`(text) · `SheetMusic`(title) · `Genre`(slug, name) · `Reference`(kind, slug) · `AlbumClaim`(text, source_uri, domain, verified) · `AlbumVerification`(claim, verdict)
**Edges:** `PROMOTED_TO` · `RECORDED_FOR`
**Enums:** `('Album', 'type')` ∈ {character-study, collection, documentary, narrative, ost, thematic} · `('Album', 'status')` ∈ {draft, in-production, mastered, released} · `('Track', 'status')` ∈ {draft, mastered, mixed, recorded} · `('Idea', 'status')` ∈ {dropped, new, promoted} · `('Tweet', 'status')` ∈ {archived, draft, posted, scheduled} · `('AlbumClaim', 'verified')` ∈ {human-confirmed, pending, rejected} · `('AlbumClaim', 'domain')` ∈ {biographical, document_hunter, financial, government, historical, journalism, legal, primary_source, security, technical} · `('AlbumVerification', 'verdict')` ∈ {confirmed, needs-more-evidence, rejected}

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/music -->
