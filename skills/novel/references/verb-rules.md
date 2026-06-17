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

## novel verb audit — 0 of 95 verbs need work

| Verb | Role | tool-desc flags |
|------|------|-----------------|
| `novel.analyze_readability` | transform | ✓ clean |
| `novel.archive_codex_entry` | effect | ✓ clean |
| `novel.audit_novel_provenance` | transform | ✓ clean |
| `novel.beta_ready_gate` | effect | ✓ clean |
| `novel.capture_claim` | effect | ✓ clean |
| `novel.capture_idea` | effect | ✓ clean |
| `novel.chapter_report` | transform | ✓ clean |
| `novel.chapter_report_full` | act | ✓ clean |
| `novel.check_approach_concern` | transform | ✓ clean |
| `novel.check_content_warnings` | transform | ✓ clean |
| `novel.check_continuity` | transform | ✓ clean |
| `novel.check_crucial_element_placement` | transform | ✓ clean |
| `novel.check_dialogue_attribution` | transform | ✓ clean |
| `novel.check_dynamic_pair_reciprocity` | transform | ✓ clean |
| `novel.check_filter_words` | transform | ✓ clean |
| `novel.check_ktad_coverage` | transform | ✓ clean |
| `novel.check_mental_sex_problem_solving` | transform | ✓ clean |
| `novel.check_pov_consistency` | transform | ✓ clean |
| `novel.check_quad_completeness` | transform | ✓ clean |
| `novel.check_resolve_outcome_judgment` | transform | ✓ clean |
| `novel.check_sensitivity` | transform | ✓ clean |
| `novel.check_show_dont_tell` | transform | ✓ clean |
| `novel.check_signpost_permutation` | transform | ✓ clean |
| `novel.check_slot_fill` | transform | ✓ clean |
| `novel.check_storybeat_moment_refs` | transform | ✓ clean |
| `novel.check_throughline_partition` | transform | ✓ clean |
| `novel.check_voice_consistency` | transform | ✓ clean |
| `novel.conceptualize` | act | ✓ clean |
| `novel.copy_gate` | effect | ✓ clean |
| `novel.count_words` | transform | ✓ clean |
| `novel.create_chapter` | effect | ✓ clean |
| `novel.create_codex_entry` | effect | ✓ clean |
| `novel.create_culture` | effect | ✓ clean |
| `novel.create_language` | effect | ✓ clean |
| `novel.create_magic_system` | effect | ✓ clean |
| `novel.create_novel` | effect | ✓ clean |
| `novel.create_religion` | effect | ✓ clean |
| `novel.create_scene` | effect | ✓ clean |
| `novel.create_storyform` | effect | ✓ clean |
| `novel.create_world` | effect | ✓ clean |
| `novel.create_world_axiom` | effect | ✓ clean |
| `novel.developmental_gate` | effect | ✓ clean |
| `novel.dispatch_novel_research` | effect | ✓ clean |
| `novel.export_docx` | effect | ✓ clean |
| `novel.export_epub` | effect | ✓ clean |
| `novel.export_pdf` | effect | ✓ clean |
| `novel.fetch_scene_body` | transform | ✓ clean |
| `novel.find_axiom_contradictions` | effect | ✓ clean |
| `novel.find_novel` | transform | ✓ clean |
| `novel.flag_anachronistic_reference` | transform | ✓ clean |
| `novel.generate_scene_body` | act | ✓ clean |
| `novel.get_storyform` | transform | ✓ clean |
| `novel.integrate_scene_body` | effect | ✓ clean |
| `novel.line_gate` | effect | ✓ clean |
| `novel.link_character_to_world` | effect | ✓ clean |
| `novel.list_chapters` | transform | ✓ clean |
| `novel.list_claims` | transform | ✓ clean |
| `novel.list_codex_entries` | transform | ✓ clean |
| `novel.list_ideas` | transform | ✓ clean |
| `novel.list_reveals_in` | transform | ✓ clean |
| `novel.list_story_events_up_to` | transform | ✓ clean |
| `novel.list_world` | transform | ✓ clean |
| `novel.manuscript_coherence_check` | transform | ✓ clean |
| `novel.mark_narrative_beat` | effect | ✓ clean |
| `novel.match_codex_entries` | transform | ✓ clean |
| `novel.narrative_order` | transform | ✓ clean |
| `novel.novel_coherence_check` | effect | ✓ clean |
| `novel.novel_progress` | transform | ✓ clean |
| `novel.pending_verifications` | transform | ✓ clean |
| `novel.pov_options` | transform | ✓ clean |
| `novel.pre_draft_gate` | effect | ✓ clean |
| `novel.promote_idea` | effect | ✓ clean |
| `novel.publication_gate` | effect | ✓ clean |
| `novel.publish_ready_gate` | effect | ✓ clean |
| `novel.query_ready_gate` | effect | ✓ clean |
| `novel.record_character_learns` | effect | ✓ clean |
| `novel.record_story_event` | effect | ✓ clean |
| `novel.record_storyform_decision` | effect | ✓ clean |
| `novel.rename_novel` | effect | ✓ clean |
| `novel.render_all` | effect | ✓ clean |
| `novel.render_blurb` | act | ✓ clean |
| `novel.render_chapter_brief` | act | ✓ clean |
| `novel.render_manuscript` | act | ✓ clean |
| `novel.render_query_letter` | act | ✓ clean |
| `novel.render_synopsis` | act | ✓ clean |
| `novel.resume_session` | transform | ✓ clean |
| `novel.reveal_in_scene` | effect | ✓ clean |
| `novel.scan_proper_nouns` | transform | ✓ clean |
| `novel.set_chapter_status` | effect | ✓ clean |
| `novel.set_novel_status` | effect | ✓ clean |
| `novel.storyform_critical_pass` | act | ✓ clean |
| `novel.update_codex_entry` | effect | ✓ clean |
| `novel.validate_appreciations` | transform | ✓ clean |
| `novel.validate_narrative_functions` | transform | ✓ clean |
| `novel.what_does_X_know_as_of` | transform | ✓ clean |

> Generated from each verb's live docstring (`prompt.evaluate(target="tool-desc")`).
> A clean row meets the grammar; a flagged row names the rule it breaks. The
> repo-wide sweep `scripts/optimize-verb-docs` emits an optimized candidate for
> every flagged verb (advisory — writes no source).
