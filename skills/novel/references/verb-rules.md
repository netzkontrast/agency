<!-- agency-generated: v1 -->
# Writing novel verb descriptions

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

## novel verb audit — 2 of 163 verbs need work

| Verb | Role | tool-desc flags |
|------|------|-----------------|
| `novel.add_alter` | effect | ✓ clean |
| `novel.add_storyform_to_set` | effect | ✓ clean |
| `novel.analyze_readability` | transform | ✓ clean |
| `novel.anchor_beat` | effect | ✓ clean |
| `novel.anchor_status_report` | transform | ✓ clean |
| `novel.apply_structure` | effect | ✓ clean |
| `novel.archive_codex_entry` | effect | ✓ clean |
| `novel.assign_chapter_to_block` | effect | ✓ clean |
| `novel.assign_voice_to_alter` | effect | ✓ clean |
| `novel.audit_novel_provenance` | transform | ✓ clean |
| `novel.beta_ready_gate` | effect | ✓ clean |
| `novel.bridge_frequency_report` | transform | ✓ clean |
| `novel.briefing_checklist` | transform | ✓ clean |
| `novel.canon_audit` | transform | ✓ clean |
| `novel.canon_gate` | transform | ✓ clean |
| `novel.capture_claim` | effect | ✓ clean |
| `novel.capture_idea` | effect | ✓ clean |
| `novel.catalogue_query` | transform | ✓ clean |
| `novel.chapter_report` | transform | ✓ clean |
| `novel.chapter_report_full` | act | ✓ clean |
| `novel.check_alter_recognition` | transform | ✓ clean |
| `novel.check_approach_concern` | transform | ✓ clean |
| `novel.check_content_warnings` | transform | ✓ clean |
| `novel.check_continuity` | transform | ✓ clean |
| `novel.check_crucial_element_placement` | transform | ✓ clean |
| `novel.check_dialogue_attribution` | transform | ✓ clean |
| `novel.check_driver_transition_legality` | transform | ✓ clean |
| `novel.check_dynamic_pair_reciprocity` | transform | ✓ clean |
| `novel.check_filter_words` | transform | ✓ clean |
| `novel.check_genre_bleed` | transform | ✓ clean |
| `novel.check_klein_c_inversion` | transform | ✓ clean |
| `novel.check_ktad_coverage` | transform | ✓ clean |
| `novel.check_mental_sex_problem_solving` | transform | ✓ clean |
| `novel.check_mode_vs_storyform_boundary` | transform | ✓ clean |
| `novel.check_pov_consistency` | transform | ✓ clean |
| `novel.check_pov_voice` | transform | ✓ clean |
| `novel.check_quad_completeness` | transform | ✓ clean |
| `novel.check_resolve_outcome_judgment` | transform | ✓ clean |
| `novel.check_reveal_timing` | transform | ✓ clean |
| `novel.check_sensitivity` | transform | ✓ clean |
| `novel.check_show_dont_tell` | transform | ✓ clean |
| `novel.check_signpost_permutation` | transform | ✓ clean |
| `novel.check_slot_fill` | transform | ✓ clean |
| `novel.check_storybeat_moment_refs` | transform | ✓ clean |
| `novel.check_structure_coverage` | transform | ✓ clean |
| `novel.check_throughline_partition` | transform | ✓ clean |
| `novel.check_veil` | transform | ✓ clean |
| `novel.check_voice_consistency` | transform | ✓ clean |
| `novel.conceptualize` | act | ✓ clean |
| `novel.conflict_matrix_report` | transform | ✓ clean |
| `novel.copy_gate` | effect | ✓ clean |
| `novel.count_words` | transform | ✓ clean |
| `novel.create_chapter` | effect | ✓ clean |
| `novel.create_character_system` | effect | ✓ clean |
| `novel.create_codex_entry` | effect | ✓ clean |
| `novel.create_culture` | effect | ✓ clean |
| `novel.create_language` | effect | ✓ clean |
| `novel.create_magic_system` | effect | ✓ clean |
| `novel.create_novel` | effect | ✓ clean |
| `novel.create_religion` | effect | ✓ clean |
| `novel.create_scene` | effect | ✓ clean |
| `novel.create_storyform` | effect | ✓ clean |
| `novel.create_storyform_set` | effect | ✓ clean |
| `novel.create_voice_profile` | effect | ✓ clean |
| `novel.create_world` | effect | ✓ clean |
| `novel.create_world_axiom` | effect | ✓ clean |
| `novel.define_mode_block` | effect | ✓ clean |
| `novel.developmental_gate` | effect | ✓ clean |
| `novel.dispatch_novel_research` | effect | ✓ clean |
| `novel.dual_storyform_coherence_check` | act | ✓ clean |
| `novel.events_pov_witnessed` | transform | ✓ clean |
| `novel.export_docx` | effect | ✓ clean |
| `novel.export_epub` | effect | ✓ clean |
| `novel.export_pdf` | effect | ✓ clean |
| `novel.fetch_scene_body` | transform | ✓ clean |
| `novel.find_axiom_contradictions` | effect | ✓ clean |
| `novel.find_novel` | transform | ✓ clean |
| `novel.flag_anachronistic_reference` | transform | ✓ clean |
| `novel.generate_scene_body` | act | ✓ clean |
| `novel.get_storyform` | transform | ✓ clean |
| `novel.get_structure_template` | transform | ✓ clean |
| `novel.get_voice_profile` | transform | ✓ clean |
| `novel.integrate_scene_body` | effect | ✓ clean |
| `novel.leerstellen_report` | transform | ✓ clean |
| `novel.line_gate` | effect | ✓ clean |
| `novel.link_character_to_world` | effect | ✓ clean |
| `novel.list_chapters` | transform | ✓ clean |
| `novel.list_claims` | transform | ✓ clean |
| `novel.list_codex_entries` | transform | ✓ clean |
| `novel.list_ideas` | transform | ✓ clean |
| `novel.list_project_rules` | transform | ✓ clean |
| `novel.list_reveals_in` | transform | ✓ clean |
| `novel.list_story_events_up_to` | transform | ✓ clean |
| `novel.list_structure_templates` | transform | ✓ clean |
| `novel.list_world` | transform | ✓ clean |
| `novel.lock_index` | transform | ✓ clean |
| `novel.manuscript_coherence_check` | transform | ✓ clean |
| `novel.mark_narrative_beat` | effect | ✓ clean |
| `novel.match_codex_entries` | transform | ✓ clean |
| `novel.mode_block_report` | transform | ✓ clean |
| `novel.motif_echo_report` | transform | `long_brief` |
| `novel.narrative_order` | transform | ✓ clean |
| `novel.novel_coherence_check` | effect | ✓ clean |
| `novel.novel_progress` | transform | ✓ clean |
| `novel.pay_off_anchor` | effect | ✓ clean |
| `novel.pending_verifications` | transform | ✓ clean |
| `novel.plant_anchor` | effect | ✓ clean |
| `novel.pov_options` | transform | ✓ clean |
| `novel.pre_draft_gate` | effect | ✓ clean |
| `novel.preflight_readiness` | transform | ✓ clean |
| `novel.preflight_report` | act | ✓ clean |
| `novel.project_rule_gate` | transform | ✓ clean |
| `novel.promote_from_quarry` | effect | ✓ clean |
| `novel.promote_idea` | effect | ✓ clean |
| `novel.publication_gate` | effect | ✓ clean |
| `novel.publish_ready_gate` | effect | ✓ clean |
| `novel.quarry_filter` | transform | ✓ clean |
| `novel.query_co_front` | transform | ✓ clean |
| `novel.query_phobia_cycles` | transform | ✓ clean |
| `novel.query_ready_gate` | effect | ✓ clean |
| `novel.reader_function_audit` | transform | ✓ clean |
| `novel.record_alter_conflict` | effect | ✓ clean |
| `novel.record_character_learns` | effect | ✓ clean |
| `novel.record_leerstelle` | effect | ✓ clean |
| `novel.record_lock` | effect | ✓ clean |
| `novel.record_motif_echo` | effect | `long_brief` |
| `novel.record_story_event` | effect | ✓ clean |
| `novel.record_storyform_decision` | effect | ✓ clean |
| `novel.record_storyform_transition` | effect | ✓ clean |
| `novel.register_project_rule` | effect | ✓ clean |
| `novel.rename_novel` | effect | ✓ clean |
| `novel.render_all` | effect | ✓ clean |
| `novel.render_blurb` | act | ✓ clean |
| `novel.render_chapter_brief` | act | ✓ clean |
| `novel.render_chapter_briefing` | act | ✓ clean |
| `novel.render_manuscript` | act | ✓ clean |
| `novel.render_query_letter` | act | ✓ clean |
| `novel.render_synopsis` | act | ✓ clean |
| `novel.resolve_canon_conflict` | transform | ✓ clean |
| `novel.resume_session` | transform | ✓ clean |
| `novel.reveal_gate` | transform | ✓ clean |
| `novel.reveal_in_scene` | effect | ✓ clean |
| `novel.reveal_timeline_report` | transform | ✓ clean |
| `novel.route_scene_storyform` | effect | ✓ clean |
| `novel.run_project_rules` | transform | ✓ clean |
| `novel.scan_proper_nouns` | transform | ✓ clean |
| `novel.score_voice_match` | transform | ✓ clean |
| `novel.set_canon_status` | effect | ✓ clean |
| `novel.set_chapter_status` | effect | ✓ clean |
| `novel.set_novel_status` | effect | ✓ clean |
| `novel.set_reveal_rule` | effect | ✓ clean |
| `novel.story_time_query` | transform | ✓ clean |
| `novel.storyform_critical_pass` | act | ✓ clean |
| `novel.structure_position_report` | transform | ✓ clean |
| `novel.switching_log` | transform | ✓ clean |
| `novel.update_codex_entry` | effect | ✓ clean |
| `novel.update_voice_profile` | effect | ✓ clean |
| `novel.validate_appreciations` | transform | ✓ clean |
| `novel.validate_narrative_functions` | transform | ✓ clean |
| `novel.validate_no_fusion` | transform | ✓ clean |
| `novel.voice_drift_gate` | transform | ✓ clean |
| `novel.voice_drift_report` | transform | ✓ clean |
| `novel.what_does_X_know_as_of` | transform | ✓ clean |

> Generated from each verb's live docstring (`prompt.evaluate(target="tool-desc")`).
> A clean row meets the grammar; a flagged row names the rule it breaks. The
> repo-wide sweep `scripts/optimize-verb-docs` emits an optimized candidate for
> every flagged verb (advisory — writes no source).
