<!-- agency-generated: v1 -->
# Writing music verb descriptions

A verb description is a **functional** prompt — its job is invocation + cheap
discovery, not persuasion, and **not routing** (that is the capability's job:
`search` / `recommend` / the SkillDoc's "When to use"). Full rules + canon
(Spec 023): `agency/capabilities/prompt/references/tool-desc-authoring.md`. Score
any verb docstring with `prompt.evaluate(target="tool-desc")`.

**The grammar (each maps to a `tool-desc` flag):**
- **first sentence** — ≤120 chars, single clause, verb-first, role-tagged; **no Role** (`role_padding` · `long_brief`)
- **`Inputs:`** — `name (type) — meaning`, per user-facing arg (`missing_inputs`)
- **`Returns:`** — the wire shape; error / null cases too (`missing_returns`)
- **`chain_next:`** — the verb to call next, or `(terminal)` (advisory `no_chain_next`)

## music verb audit — 6 of 103 verbs need work

| Verb | Role | tool-desc flags |
|------|------|-----------------|
| `music.album_coherence_check` | transform | ✓ clean |
| `music.album_coherence_correct` | effect | ✓ clean |
| `music.album_progress` | transform | ✓ clean |
| `music.analyze_audio` | transform | ✓ clean |
| `music.analyze_mix` | transform | ✓ clean |
| `music.analyze_readability` | transform | ✓ clean |
| `music.analyze_rhyme_scheme` | transform | ✓ clean |
| `music.audio_release_gate` | effect | ✓ clean |
| `music.capture_claim` | effect | ✓ clean |
| `music.capture_idea` | effect | ✓ clean |
| `music.catalogue_gate` | effect | ✓ clean |
| `music.catalogue_status` | transform | ✓ clean |
| `music.check_cross_track_repetition` | transform | ✓ clean |
| `music.check_explicit_content` | transform | ✓ clean |
| `music.check_homographs` | transform | ✓ clean |
| `music.check_name_exposure` | transform | ✓ clean |
| `music.check_pronunciation` | transform | ✓ clean |
| `music.check_streaming_lyrics` | transform | ✓ clean |
| `music.check_voice_tells` | transform | ✓ clean |
| `music.concept_gate` | effect | ✓ clean |
| `music.conceptualize` | act | `long_brief` |
| `music.count_syllables` | transform | ✓ clean |
| `music.create_album` | effect | ✓ clean |
| `music.create_songbook` | effect | ✓ clean |
| `music.create_track` | effect | ✓ clean |
| `music.db_create_tweet` | effect | `long_brief` |
| `music.db_delete_tweet` | effect | ✓ clean |
| `music.db_get_tweet_stats` | transform | ✓ clean |
| `music.db_list_tweets` | transform | ✓ clean |
| `music.db_search_tweets` | transform | ✓ clean |
| `music.db_sync_album` | effect | ✓ clean |
| `music.db_update_tweet` | effect | ✓ clean |
| `music.diagnose` | transform | ✓ clean |
| `music.dispatch_research` | effect | ✓ clean |
| `music.document_hunt` | effect | ✓ clean |
| `music.explicit_gate` | effect | ✓ clean |
| `music.extract_distinctive_phrases` | transform | ✓ clean |
| `music.extract_links` | transform | ✓ clean |
| `music.extract_section` | transform | ✓ clean |
| `music.find_album` | transform | ✓ clean |
| `music.fix_dynamic_track` | effect | ✓ clean |
| `music.format_clipboard` | transform | ✓ clean |
| `music.generate_promo_videos` | effect | ✓ clean |
| `music.get_config` | transform | ✓ clean |
| `music.get_promo_content` | transform | ✓ clean |
| `music.get_promo_status` | transform | ✓ clean |
| `music.get_reference` | transform | ✓ clean |
| `music.get_streaming_urls` | transform | ✓ clean |
| `music.human_signoff` | effect | ✓ clean |
| `music.list_claims` | transform | ✓ clean |
| `music.list_ideas` | transform | ✓ clean |
| `music.list_tracks` | transform | ✓ clean |
| `music.load_override` | transform | ✓ clean |
| `music.lyric_report` | act | ✓ clean |
| `music.lyrics_pregen_gate` | effect | ✓ clean |
| `music.master_album` | effect | ✓ clean |
| `music.master_audio` | effect | `long_brief` |
| `music.master_with_reference` | effect | ✓ clean |
| `music.measure_album_signature` | transform | ✓ clean |
| `music.measure_gate` | effect | ✓ clean |
| `music.mono_fold_check` | transform | ✓ clean |
| `music.music_health` | transform | ✓ clean |
| `music.name_exposure_gate` | effect | ✓ clean |
| `music.pending_verifications` | transform | ✓ clean |
| `music.polish_album` | effect | ✓ clean |
| `music.polish_and_master_album` | effect | `long_brief` |
| `music.polish_audio` | effect | ✓ clean |
| `music.pregen_check` | effect | ✓ clean |
| `music.promo_copy` | act | ✓ clean |
| `music.promo_gate` | effect | ✓ clean |
| `music.promo_review` | transform | ✓ clean |
| `music.promo_review_gate` | effect | ✓ clean |
| `music.promote_idea` | effect | `long_brief` |
| `music.pronunciation_gate` | effect | ✓ clean |
| `music.prosody_gate` | effect | ✓ clean |
| `music.publish_asset` | effect | ✓ clean |
| `music.publish_sheet_music` | effect | ✓ clean |
| `music.qc_audio` | transform | ✓ clean |
| `music.qc_gate` | effect | ✓ clean |
| `music.r2_delete` | effect | ✓ clean |
| `music.r2_list` | transform | ✓ clean |
| `music.release_check` | effect | ✓ clean |
| `music.release_package` | act | ✓ clean |
| `music.rename_album` | effect | ✓ clean |
| `music.rename_track` | effect | ✓ clean |
| `music.render_codec_preview` | effect | ✓ clean |
| `music.repetition_gate` | effect | ✓ clean |
| `music.research_scope` | act | ✓ clean |
| `music.reset_mastering` | effect | ✓ clean |
| `music.resume_session` | transform | ✓ clean |
| `music.scan_artist_names` | transform | ✓ clean |
| `music.set_album_status` | effect | ✓ clean |
| `music.set_track_status` | effect | ✓ clean |
| `music.transcribe_sheet` | act | `long_brief` |
| `music.tweet_schedule_gate` | effect | ✓ clean |
| `music.update_streaming_url` | effect | ✓ clean |
| `music.upload_promo_video` | effect | ✓ clean |
| `music.validate_album` | transform | ✓ clean |
| `music.validate_section_structure` | transform | ✓ clean |
| `music.validate_sections` | transform | ✓ clean |
| `music.verify_gate` | effect | ✓ clean |
| `music.verify_sources` | effect | ✓ clean |
| `music.verify_streaming` | transform | ✓ clean |

> Generated from each verb's live docstring (`prompt.evaluate(target="tool-desc")`).
> A clean row meets the grammar; a flagged row names the rule it breaks. The
> repo-wide sweep `scripts/optimize-verb-docs` emits an optimized candidate for
> every flagged verb (advisory — writes no source).
