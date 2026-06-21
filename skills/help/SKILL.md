---
name: help
description: Use when you need to discover the agency engine's capabilities (macroskills) and their verbs (the micro-skills).
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# help

## Quick start — MCP (Claude Code)

The plugin installs an MCP server exposing the code-mode contract
(`search` · `get_schema` · `execute`) AND three engine-substrate
onboarding tools (Spec 029):

- `agency_welcome` — one-shot onboarding payload; returns the
  bootstrap example + the live capability list. **Start here.**
- `agency_install` — scaffold `.agency/` + a CLAUDE.md snippet in
  the current target repo. Idempotent.
- `intent_bootstrap` — mint AND confirm an Intent. The only verb
  that does not require an existing `intent_id`.
- `agency_doctor` — health check (Spec 030): python version, deps,
  DB reachability, JULES_API_KEY presence (never the value).
  Call when something silently fails.

These onboarding tools and the code-mode trio share one MCP server
(`mcp__plugin_agency_agency__execute` for the sandbox, `mcp__plugin_agency_agency__search` for discovery, `mcp__plugin_agency_agency__get_schema` before a call).

```python
# 1. Onboard (one call; no intent_id needed)
await call_tool('agency_welcome', {})

# 2. Scaffold .agency/ + CLAUDE.md in the target repo if missing
await call_tool('agency_install', {})

# 3. Mint the intent every capability verb SERVES against
r = await call_tool('intent_bootstrap', {
    'purpose': 'ship X',
    'deliverable': 'Y working',
    'acceptance': 'tests green',
})
# 4. Use it
await call_tool('capability_plugin_help', {'intent_id': r['intent_id']})
```

## Quick start — bash (Jules / no-MCP)

The CLI resolves the graph DB itself (Spec 020: `AGENCY_DB` env, else
`./.agency/session.db`) — do NOT pass `--db`, or the bash surface writes
to a different store than MCP. The canonical entrypoint is
`python -m agency.cli` (works in Jules / no-MCP / any context where the
venv is activated). Spec 065: `agency` (the pipx-installed
console-script) is the canonical CLI form — no bin/ shim.

```bash
iid=$(agency intent --purpose help --deliverable map --acceptance ok \
      | python3 -c 'import sys,json; print(json.load(sys.stdin)["intent_id"])')
agency execute --code \
  "return await call_tool('capability_plugin_help', {'intent_id': '$iid'})"
```


# agency — capabilities (macroskills) and their verbs (micro-skills)

- **adr** — approve, catalogue, dod_check, draft, extract_decisions, hints, impact, link, read, render, spec_decisions_ready, supersede, theme, theme_status, update, validate
- **analyze** — architecture, cleanup, graph, improve, paths, performance, quality, review, run, score, security
- **branch** — assess, commit_smart, finish
- **config** — get, list, set
- **delegate** — dispatch_bash_hints, dispatch_decision, fan_out, join
- **develop** — checklist, draft_plan, estimate, index, maintain, mode_select, optimize_skilldoc, plan_status, record_authoring_outcome, record_step_outcome, reference, reload, remediate, review, scaffold_capability, session_check, session_init, session_resume, skill_walk, validate_skill
- **discover** — acceptance, ask, clarify, clarity, clarity_gate, interview, scope, status
- **doctrine** — cite, principles, resolve, rules
- **document** — convergence, explain, index_repo, ingest, mirror, render, reopen, restore_session, revisions, session, session_analytics, sync
- **dogfood** — apply_amendment, boundary_use_audit, collect, export, import, note, parse_amendment, recall_overflow_slice, record_decision, render, replay_events
- **frugal** — debt, gain, help, instructions, level, review, set_level
- **gate** — adjudicate, check
- **intent** — assumptions, decompose, first_principles, inversion, premortem, second_order, steelman, suggests, tradeoffs
- **jules** — activities, alias, apply_patch, approve_awaiting, approve_plan, detect_mode, dispatch, lint_prompt, list, message, patch, patch_body, plan, quota, recover, resolve_source, review_comment, status, status_all, stop, verify, watch
- **manage** — amend, artefacts, create, lifecycle, lifecycle_trail, list, open_intents, project, provenance, read, render, research_state, retract, state, subtree, timeline, update, whats_next
- **mode** — activate, detect, list
- **music** — album_coherence_check, album_coherence_correct, album_progress, analyze_audio, analyze_mix, analyze_readability, analyze_rhyme_scheme, audio_release_gate, capture_claim, capture_idea, catalogue_gate, catalogue_status, check_cross_track_repetition, check_explicit_content, check_homographs, check_name_exposure, check_pronunciation, check_streaming_lyrics, check_voice_tells, concept_gate, conceptualize, count_syllables, create_album, create_songbook, create_track, db_create_tweet, db_delete_tweet, db_get_tweet_stats, db_list_tweets, db_search_tweets, db_sync_album, db_update_tweet, diagnose, dispatch_research, document_hunt, explicit_gate, extract_distinctive_phrases, extract_links, extract_section, find_album, fix_dynamic_track, format_clipboard, generate_promo_videos, get_config, get_promo_content, get_promo_status, get_reference, get_streaming_urls, human_signoff, list_claims, list_ideas, list_tracks, load_override, lyric_report, lyrics_pregen_gate, master_album, master_audio, master_with_reference, measure_album_signature, measure_gate, mono_fold_check, music_health, name_exposure_gate, pending_verifications, polish_album, polish_and_master_album, polish_audio, pregen_check, promo_copy, promo_gate, promo_review, promo_review_gate, promote_idea, pronunciation_gate, prosody_gate, publish_asset, publish_sheet_music, qc_audio, qc_gate, r2_delete, r2_list, release_check, release_package, rename_album, rename_track, render_codec_preview, repetition_gate, research_scope, reset_mastering, resume_session, scan_artist_names, set_album_status, set_track_status, transcribe_sheet, tweet_schedule_gate, update_streaming_url, upload_promo_video, validate_album, validate_section_structure, validate_sections, verify_gate, verify_sources, verify_streaming
- **novel** — analyze_readability, archive_codex_entry, audit_novel_provenance, beta_ready_gate, capture_claim, capture_idea, chapter_report, chapter_report_full, check_approach_concern, check_content_warnings, check_continuity, check_crucial_element_placement, check_dialogue_attribution, check_dynamic_pair_reciprocity, check_filter_words, check_ktad_coverage, check_mental_sex_problem_solving, check_pov_consistency, check_quad_completeness, check_resolve_outcome_judgment, check_sensitivity, check_show_dont_tell, check_signpost_permutation, check_slot_fill, check_storybeat_moment_refs, check_throughline_partition, check_voice_consistency, conceptualize, copy_gate, count_words, create_chapter, create_codex_entry, create_culture, create_language, create_magic_system, create_novel, create_religion, create_scene, create_storyform, create_world, create_world_axiom, developmental_gate, dispatch_novel_research, export_docx, export_epub, export_pdf, fetch_scene_body, find_axiom_contradictions, find_novel, flag_anachronistic_reference, generate_scene_body, get_storyform, integrate_scene_body, line_gate, link_character_to_world, list_chapters, list_claims, list_codex_entries, list_ideas, list_reveals_in, list_story_events_up_to, list_world, manuscript_coherence_check, mark_narrative_beat, match_codex_entries, narrative_order, novel_coherence_check, novel_progress, pending_verifications, pov_options, pre_draft_gate, promote_idea, publication_gate, publish_ready_gate, query_ready_gate, record_character_learns, record_story_event, record_storyform_decision, rename_novel, render_all, render_blurb, render_chapter_brief, render_manuscript, render_query_letter, render_synopsis, resume_session, reveal_in_scene, scan_proper_nouns, set_chapter_status, set_novel_status, storyform_critical_pass, update_codex_entry, validate_appreciations, validate_narrative_functions, what_does_X_know_as_of
- **panel** — convene, experts
- **persona** — list, recommend, summon
- **plugin** — author_command, author_skill, help, lint_capability, lint_explain, lint_skill, marketplace_entry, publish_skill, scaffold, step_doc
- **prompt** — assemble_scene_brief, audit, audit_gate, brief_audit, brief_finalize, brief_render, catalog_list, engineer, evaluate, fragment, fragments_for, framework, frameworks_for, intent_capture, register_fragment, register_framework, render, route_framework, token_budget_gate
- **recommend** — route
- **reflect** — batch_note, note, recall, recall_semantic, search, synthesize_session
- **research** — ingest_gdoc, lead, record_ingested_source, specialist, verify
- **select** — archetypes, route
- **shell** — define, define_profile, filter, run, templates
- **skill_generator** — generate
- **skills** — find, index, lint, rank, render
- **subagent** — develop
- **symbols** — compress, expand, legend
- **thinking** — apply_full_review, assumptions, decompose, first_principles, inversion, premortem, red_team, second_order, socratic, steelman, tradeoffs
- **toolcalls** — export, prune, recent, stats, top
- **workflow** — board, index, move_spec, open_spec
- **workspace** — baseline, isolate

## Discovery

There is no separate 'remember to use the skill' layer — discovery IS the contract:

- `search` finds a capability/verb or a discipline by symptom;
- `get_schema` discloses just what you need (a verb's signature, a discipline's current phase);
- `execute` runs it — and the run is recorded provenance (an Invocation, or a skill walk, that SERVES the intent).

Walk a discipline one phase at a time (`develop.checklist` lists its steps); a hard gate halts until
confirmed, and a phase bound to a verb EXECUTES rather than merely documents. Fetch a discipline's
heavy how-to on demand with `develop.reference` (T3 progressive disclosure) — invoking a discipline IS
the recorded walk, so there is nothing extra to remember.

