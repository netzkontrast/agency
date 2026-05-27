---
spec_id: music-001
slug: music-cluster
status: draft
owner: "@claude"
depends_on: []
affects:
  - "agency/capabilities/music.py"
source-repos:
  - "https://github.com/bitwize-music-studio/claude-ai-music-skills @ b4b70dbfa2e24e3b86ec3d6cbec4e9bf1baddfaf"
estimated_jules_sessions: 5
domain: "music"
wave: 2
---

# Music Capability Cluster

## Why
The Agency vision aims to fully encapsulate domain handlers (music, novel, agentic). `bitwize-music` demonstrates complex audio state management, metadata linting, and over 90 distinct MCP tools spanning album CRUD, audio mastering, lyric analysis, and promotion. We need a dedicated capability in Agency to manage these primitives cleanly so that standard skills can manipulate audio artifacts without hardcoding domain logic into the general codebase.

## Done When
- [ ] Create `agency/capabilities/music.py`.
- [ ] Implement capability verbs mapping all discovered MCP tools natively:
  - `reset_mastering(album_slug: str,     subfolders: list[str] = ["mastered"],  # noqa: B006 — MCP tool default, not mutated     dry_run: bool = True,)`: Remove mastered/, polished/, and/or mastering_samples/ subfolders.
  - `cleanup_legacy_venvs(dry_run: bool = True,)`: Detect and remove stale per-tool virtual environments from ~/.bitwize-music/.
  - `migrate_audio_layout(album_slug: str = "",     dry_run: bool = True,)`: Migrate album audio from legacy root layout to originals/ subdirectory.
  - `get_streaming_urls(album_slug: str)`: Get streaming platform URLs for an album.
  - `update_streaming_url(album_slug: str, platform: str, url: str)`: Set a streaming platform URL for an album.
  - `verify_streaming_urls(album_slug: str)`: Check if streaming URLs are live and reachable.
  - `list_skills(model_filter: str = "", category: str = "")`: List all skills with optional filtering.
  - `get_skill(name: str)`: Get full detail for a specific skill.
  - `check_homographs(text: str)`: Scan text for homograph words that Suno cannot disambiguate.
  - `scan_artist_names(text: str)`: Scan text for real artist/band names from the blocklist.
  - `check_pronunciation_enforcement(album_slug: str,     track_slug: str,)`: Verify that all Pronunciation Notes entries are applied in the Suno lyrics.
  - `check_explicit_content(text: str)`: Scan lyrics for explicit/profane words.
  - `extract_links(album_slug: str,     file_name: str = "SOURCES.md",)`: Extract markdown links from an album file.
  - `get_lyrics_stats(album_slug: str,     track_slug: str = "",)`: Get word count, character count, and genre target comparison for lyrics.
  - `check_cross_track_repetition(album_slug: str,     min_tracks: int = 3,     summary_only: bool = False,     max_results: int = 0,)`: Scan all tracks in an album for words/phrases repeated across multiple tracks.
  - `get_promo_status(album_slug: str)`: Get the status of promo/ directory files for an album.
  - `get_promo_content(album_slug: str, platform: str)`: Read the content of a specific promo file for an album.
  - `run_pre_generation_gates(album_slug: str,     track_slug: str = "",)`: Run all 8 pre-generation validation gates on a track or album.
  - `check_streaming_lyrics(album_slug: str, track_slug: str = "")`: Check streaming lyrics readiness for an album's tracks.
  - `db_init(run_migrations: str = "true")`: Initialize the database and run migrations.
  - `db_list_tweets(album_slug: str = "",     posted: str = "",     enabled: str = "",     platform: str = "",     limit: int = 50,     offset: int = 0,)`: List tweets with optional filtering by album, posted/enabled status, or platform.
  - `db_create_tweet(album_slug: str,     tweet_text: str,     track_number: int = 0,     platform: str = "twitter",     content_type: str = "promo",     media_path: str = "",)`: Insert a new post linked to an album and optionally a track.
  - `db_update_tweet(tweet_id: int,     tweet_text: str = "",     posted: str = "",     enabled: str = "",     platform: str = "",     content_type: str = "",     media_path: str = "",     times_posted: int = -1,)`: Update fields on an existing post. Only provided fields are changed.
  - `db_delete_tweet(tweet_id: int)`: Delete a tweet by ID.
  - `db_search_tweets(query: str,     album_slug: str = "",     platform: str = "",     limit: int = 50,     offset: int = 0,)`: Search post text with optional album and platform filters.
  - `db_sync_album(album_slug: str)`: Sync an album and its tracks from plugin markdown state to the database.
  - `db_get_tweet_stats(album_slug: str = "")`: Get tweet counts by status for an album or globally.
  - `find_album(name: str)`: Find an album by name with fuzzy matching.
  - `list_albums(status_filter: str = "")`: List all albums with summary info.
  - `get_track(album_slug: str, track_slug: str)`: Get details for a specific track.
  - `list_tracks(album_slug: str)`: List all tracks for an album in one call (avoids N+1 queries).
  - `get_session()`: Get current session context.
  - `update_session(album: str = "",     track: str = "",     phase: str = "",     action: str = "",     clear: bool = False,)`: Update session context.
  - `rebuild_state()`: Force full rebuild of state cache from markdown files.
  - `get_config()`: Get resolved configuration (paths, artist name, settings).
  - `get_python_command()`: Get the correct Python command for running plugin scripts via bash.
  - `get_ideas(status_filter: str = "")`: Get album ideas with status counts.
  - `search(query: str, scope: str = "all")`: Full-text search across albums, tracks, ideas, and skills.
  - `get_pending_verifications(album_slug: str = "",     summary_only: bool = False,)`: Get albums and tracks with pending source verification.
  - `resolve_path(path_type: str, album_slug: str, genre: str = "")`: Resolve the full filesystem path for an album's content, audio, or documents directory.
  - `resolve_track_file(album_slug: str, track_slug: str)`: Find a track's file path and return its full metadata from state cache.
  - `list_track_files(album_slug: str, status_filter: str = "")`: List all tracks for an album with file paths and optional status filtering.
  - `extract_section(album_slug: str, track_slug: str, section: str)`: Extract a specific section from a track's markdown file.
  - `update_track_field(album_slug: str,     track_slug: str,     field: str,     value: str,     force: bool = False,)`: Update a metadata field in a track's markdown file.
  - `get_album_progress(album_slug: str)`: Get album progress breakdown with completion stats and phase detection.
  - `extract_distinctive_phrases(text: str,     max_phrases: int = 0,     include_raw_lines: bool = True,)`: Extract distinctive phrases from lyrics for plagiarism checking.
  - `count_syllables(text: str)`: Get syllable counts per line with section tracking and consistency analysis.
  - `analyze_readability(text: str)`: Analyze readability of lyrics text using Flesch Reading Ease.
  - `analyze_rhyme_scheme(text: str)`: Analyze rhyme scheme of lyrics with section awareness.
  - `validate_section_structure(text: str)`: Validate section structure of lyrics.
  - `update_album_status(album_slug: str, status: str, force: bool = False)`: Update an album's status in its README.md file.
  - `create_track(album_slug: str,     track_number: str,     title: str,     documentary: bool = False,)`: Create a new track file in an album from the track template.
  - `create_idea(title: str,     genre: str = "",     idea_type: str = "",     concept: str = "",)`: Add a new album idea to IDEAS.md.
  - `update_idea(title: str, field: str, value: str)`: Update a field in an existing idea in IDEAS.md.
  - `promote_idea(idea_title: str,     album_slug: str = "",     documentary: bool = False,)`: Promote an album idea into an actual album project.
  - `rename_album(old_slug: str, new_slug: str, new_title: str = "")`: Rename album slug, title, and directories.
  - `rename_track(album_slug: str,     old_track_slug: str,     new_track_slug: str,     new_title: str = "",)`: Rename track slug, title, and file.
  - `load_override(override_name: str)`: Load a user override file by name from the overrides directory.
  - `get_reference(name: str, section: str = "")`: Read a plugin reference file with optional section extraction.
  - `format_for_clipboard(album_slug: str,     track_slug: str,     content_type: str,)`: Extract and format track content ready for clipboard copy.
  - `get_plugin_version()`: Get the current and stored plugin version.
  - `check_venv_health()`: Check if venv packages match requirements.txt pinned versions.
  - `health_check()`: Run startup health checks: venv packages and skill registration.
  - `diagnose()`: Run comprehensive health checks on the plugin environment.
  - `get_album_full(album_slug: str,     include_sections: str = "",     track_slugs: str = "",     summary_only: bool = False,)`: Get full album data including track content sections in one call.
  - `validate_album_structure(album_slug: str,     checks: str = "all",)`: Run structural validation on an album's files and directories.
  - `create_album_structure(album_slug: str,     genre: str,     documentary: bool = False,)`: Create a new album directory with templates.
  - `polish_audio(album_slug: str,     genre: str = "",     use_stems: bool = True,     dry_run: bool = False,     track_filename: str = "",     analyzer_results: dict[str, Any] | None = None,)`: Polish audio tracks by processing stems or full mixes.
  - `analyze_mix_issues(album_slug: str,     genre: str = "",)`: Analyze audio files for common mix issues and recommend settings.
  - `polish_album(album_slug: str,     genre: str = "",)`: End-to-end mix polish pipeline: analyze, polish stems, verify.
  - `polish_and_master_album(album_slug: str,     genre: str = "",     target_lufs: float = -14.0,     ceiling_db: float = -1.0,     cut_highmid: float = 0.0,     cut_highs: float = 0.0,)`: Combined polish + master pipeline in a single call.
  - `generate_promo_videos(album_slug: str,     style: str = "pulse",     duration: int = 15,     track_filename: str = "",     color_hex: str = "",     glow: float = 0.6,     text_color: str = "",)`: Generate promo videos with waveform visualization for social media.
  - `generate_album_sampler(album_slug: str,     clip_duration: int = 12,     crossfade: float = 0.5,     style: str = "pulse",     color_hex: str = "",     glow: float = 0.6,     text_color: str = "",)`: Generate an album sampler video cycling through all tracks.
  - `analyze_audio(album_slug: str, subfolder: str = "")`: Analyze audio tracks for mastering decisions.
  - `qc_audio(album_slug: str,     subfolder: str = "",     checks: str = "",     genre: str = "",)`: Run technical QC checks on audio tracks.
  - `master_audio(album_slug: str,     genre: str = "",     target_lufs: float = -14.0,     ceiling_db: float = -1.0,     cut_highmid: float = 0.0,     cut_highs: float = 0.0,     dry_run: bool = False,     source_subfolder: str = "",)`: Master audio tracks for streaming platforms.
  - `fix_dynamic_track(album_slug: str, track_filename: str)`: Fix a track with excessive dynamic range that won't reach target LUFS.
  - `master_with_reference(album_slug: str,     reference_filename: str,     target_filename: str = "",)`: Master tracks using a professionally mastered reference track.
  - `master_album(album_slug: str,     genre: str = "",     target_lufs: float = -14.0,     ceiling_db: float = -1.0,     cut_highmid: float = 0.0,     cut_highs: float = 0.0,     source_subfolder: str = "",     freeze_signature: bool = False,     new_anchor: bool = False,)`: End-to-end mastering pipeline: analyze, QC, master, verify, update status.
  - `render_codec_preview(album_slug: str,     subfolder: str = "mastered",     bitrate_kbps: int = 128,)`: Render a 128 kbps AAC preview of each mastered track.
  - `mono_fold_check(album_slug: str,     subfolder: str = "mastered",     write_audio: bool = True,)`: Run the mono fold-down QC gate on every mastered track.
  - `prune_archival(album_slug: str, keep: int = 3)`: Prune the album's archival/ directory, keeping the N newest files.
  - `measure_album_signature(album_slug: str,     subfolder: str = "mastered",     genre: str = "",     anchor_track: int | None = None,)`: Measure an album's multi-metric signature from its WAV files.
  - `album_coherence_check(album_slug: str,     subfolder: str = "mastered",     genre: str = "",     anchor_track: int | None = None,)`: Check an album's mastered tracks for coherence outliers vs. the anchor.
  - `album_coherence_correct(album_slug: str,     genre: str,     source_subfolder: str = "polished",     check_subfolder: str = "mastered",     target_lufs: float = -14.0,     ceiling_db: float = -1.0,     cut_highmid: float = 0.0,     cut_highs: float = 0.0,     anchor_track: int | None = None,     dry_run: bool = False,)`: Re-master LUFS-outlier tracks from polished/ into mastered/.
  - `transcribe_audio(album_slug: str,     track_filename: str = "",     formats: str = "pdf,xml,midi",     dry_run: bool = False,)`: Convert WAV files to sheet music using AnthemScore.
  - `prepare_singles(album_slug: str,     dry_run: bool = False,     xml_only: bool = False,)`: Prepare consumer-ready sheet music singles with clean titles.
  - `create_songbook(album_slug: str,     title: str,     page_size: str = "letter",)`: Combine sheet music PDFs into a distribution-ready songbook.
  - `publish_sheet_music(album_slug: str,     include_source: bool = False,     dry_run: bool = False,)`: Upload sheet music files (PDFs, MusicXML, MIDI) to Cloudflare R2.
- [ ] Map the underlying handler structure (`streaming`, `skills`, `text_analysis`, `promo`, `database`, `lyrics_analysis`, `rename`, `processing/mixing`, `processing/video`, `processing/audio`, `album_ops`) into native Agency lifecycle plugins.

## Source clones
```bash
git clone --depth=1 --branch=v0.91.0 https://github.com/bitwize-music-studio/claude-ai-music-skills.git ~/work/vendor/bitwize-music
# SHA: b4b70dbfa2e24e3b86ec3d6cbec4e9bf1baddfaf
```

## Files
- Create: `agency/capabilities/music.py`

## Evidence
- `bitwize-music-studio/servers/bitwize-music-server/handlers/` containing exactly 90 tool definitions.

## Self-Review
Scopes the exhaustive tool inventory requested into a native Agency module, ensuring full 90-tool coverage without abstraction.
