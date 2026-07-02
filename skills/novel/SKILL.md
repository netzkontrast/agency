---
name: novel
description: "Use when authoring a novel — turning a premise into a structured manuscript through gated concept → chapters → report → render."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# novel capability

Five-verb path from premise to manuscript: conceptualize → create_novel → create_chapter → chapter_report → render_manuscript, plus the novel-concept gated planning skill.

## When to use

- A novel premise needs structured planning before drafting
- A chapter needs a per-chapter report (word count, beat progress)
- A finished draft needs rendering to manuscript format

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `add_alter` | effect | Add an alter to the system (effect). | [details](references/add_alter.md) |
| `add_storyform_to_set` | effect | Mint ``MEMBER_OF`` + stamp ``Storyform.role`` (effect). | [details](references/add_storyform_to_set.md) |
| `analyze_readability` | transform | Flesch Reading Ease for prose (transform, driver-free). | [details](#analyze_readability) |
| `anchor_beat` | effect | Map a manuscript scene to a beat: ``FULFILS`` edge + the expectation's ``scene_id`` (effect). | [details](references/anchor_beat.md) |
| `anchor_status_report` | transform | The Chekhov's-gun audit for NAMED anchors (transform): planted- but-unpaid anchors are the open foreshadowing debt. | [details](references/anchor_status_report.md) |
| `apply_structure` | effect | Apply a structure template: mint one ``BeatExpectation`` per beat (effect). | [details](references/apply_structure.md) |
| `archive_codex_entry` | effect | Flag a CodexEntry as archived (effect, soft-delete). | [details](references/archive_codex_entry.md) |
| `assign_chapter_to_block` | effect | Bind a chapter to its block via ``IN_MODE_BLOCK`` (effect). | [details](references/assign_chapter_to_block.md) |
| `assign_voice_to_alter` | effect | Bind a Spec 134 ``VoiceProfile`` to an alter (effect). | [details](references/assign_voice_to_alter.md) |
| `audit_novel_provenance` | transform | Aggregate the provenance graph census for the serving intent (transform, xcap to analyze). | [details](references/audit_novel_provenance.md) |
| `beta_ready_gate` | effect | Composite gate: all chapters drafted+ (effect). | [details](references/beta_ready_gate.md) |
| `bridge_frequency_report` | transform | Per mode-block share of soft-routed (bridge) scenes (transform). | [details](references/bridge_frequency_report.md) |
| `briefing_checklist` | transform | The §9 section-M pre-draft checklist (transform): what must be in place before this chapter drafts. | [details](references/briefing_checklist.md) |
| `canon_audit` | transform | Census + open-work surface (transform): counts per status, the ``[L]`` gaps still to set, the unmarked nodes (decide!), and the 5 newest locks. | [details](references/canon_audit.md) |
| `canon_gate` | transform | The drafting hard-stop (transform): refuse to treat a proposal/quarry/gap node as fact without an explicit author override — the KP "check the Master-Index first" rule, chainable from any drafting skill. | [details](references/canon_gate.md) |
| `capture_claim` | effect | Record a NovelClaim node SERVING the intent (effect). | [details](references/capture_claim.md) |
| `capture_idea` | effect | Record an Idea node SERVING the intent (effect). | [details](references/capture_idea.md) |
| `catalogue_query` | transform | Cross-work catalogue query (transform) — every scene across the author's novels reached by TRAVERSING the declared edges (Novel → CHAPTER_OF → SCENE_OF; Motif → ECHOES_IN), never a label scan with a Python foreign-key filter (the Spec 125 dormant-edge anti-pattern). | [details](references/catalogue_query.md) |
| `chapter_report` | transform | Read-only aggregate over the novel's chapters (transform). | [details](references/chapter_report.md) |
| `chapter_report_full` | act | Full editorial dashboard for one chapter (act). | [details](references/chapter_report_full.md) |
| `check_alter_recognition` | transform | The "recognized, never labeled" discipline (transform): alters are identified by syntax + somatik + lexicon, never by headers or labels; clinical veil terms are forbidden before the reveal chapter. | [details](references/check_alter_recognition.md) |
| `check_approach_concern` | transform | Mostly-decidable check (row 8): approach ↔ class compatibility (WARN-severity). | [details](references/check_approach_concern.md) |
| `check_content_warnings` | transform | Content-warning category scanner (transform, driver-free). | [details](references/check_content_warnings.md) |
| `check_continuity` | transform | Cross-chapter proper-noun continuity check (transform). | [details](references/check_continuity.md) |
| `check_crucial_element_placement` | transform | Decidable check (row 6): storyform.crucial_element_id == mc.problem_id. | [details](references/check_crucial_element_placement.md) |
| `check_dialogue_attribution` | transform | Dialogue-tag check — plain ('said') vs flowery (transform). | [details](references/check_dialogue_attribution.md) |
| `check_driver_transition_legality` | transform | The KP driver rule (transform): a driver-flip WITHIN one storyform is illegal (Dramatica forbids it); only a storyform *transition* (e.g. | [details](references/check_driver_transition_legality.md) |
| `check_dynamic_pair_reciprocity` | transform | Decidable check (row 1): mc.dynamic and os.dynamic must differ. | [details](references/check_dynamic_pair_reciprocity.md) |
| `check_filter_words` | transform | Filter-word density check (transform, show-don't-tell). | [details](references/check_filter_words.md) |
| `check_genre_bleed` | transform | The §11 genre-bleed rule (transform, soft): a chapter whose drafted ``genre_accent`` contradicts its block's accent is flagged — the author decides. | [details](references/check_genre_bleed.md) |
| `check_klein_c_inversion` | transform | Verify the involutive Klein-c symmetry between the set's primary and secondary storyforms (transform). | [details](references/check_klein_c_inversion.md) |
| `check_ktad_coverage` | transform | Decidable check (row 2): concern_id == signposts[0] (K-position). | [details](references/check_ktad_coverage.md) |
| `check_mental_sex_problem_solving` | transform | Decidable check (row 9): mental_sex ↔ class compatibility. | [details](references/check_mental_sex_problem_solving.md) |
| `check_mode_vs_storyform_boundary` | transform | The KP's load-bearing distinction (transform): mode-changes are NOT storyform boundaries. | [details](references/check_mode_vs_storyform_boundary.md) |
| `check_pov_consistency` | transform | Per-chapter POV uniformity check across scenes (transform). | [details](references/check_pov_consistency.md) |
| `check_pov_voice` | transform | Gate a scene's body against its POV character's profile (transform). | [details](references/check_pov_voice.md) |
| `check_quad_completeness` | transform | Decidable check (row 3): mc problem and solution are paired. | [details](references/check_quad_completeness.md) |
| `check_resolve_outcome_judgment` | transform | Decidable check (row 7): resolve/outcome/judgment triple is legal. | [details](references/check_resolve_outcome_judgment.md) |
| `check_reveal_timing` | transform | Check one scene against every tier's rule for a fact (transform). | [details](references/check_reveal_timing.md) |
| `check_sensitivity` | transform | Sensitivity-topic advisory scan (transform, WARN-severity). | [details](references/check_sensitivity.md) |
| `check_show_dont_tell` | transform | Telling-verb scan — interior-monologue tells (transform). | [details](references/check_show_dont_tell.md) |
| `check_signpost_permutation` | transform | Decidable check (row 10): signposts in canonical order per class. | [details](references/check_signpost_permutation.md) |
| `check_slot_fill` | transform | Decidable check (row 4): no null required slots (transform). | [details](references/check_slot_fill.md) |
| `check_storybeat_moment_refs` | transform | Decidable check (row 11): every moment.storybeat_ref resolves (transform). | [details](references/check_storybeat_moment_refs.md) |
| `check_structure_coverage` | transform | The author's checklist: which beats are anchored to scenes, which still await one (transform). | [details](references/check_structure_coverage.md) |
| `check_throughline_partition` | transform | Decidable check (row 5): 4 throughlines / 4 distinct Classes (transform). | [details](references/check_throughline_partition.md) |
| `check_veil` | transform | The multiplicity-veil scan (transform): any scene/chapter body before ``hold_until_chapter`` containing a veil term is a breach. | [details](references/check_veil.md) |
| `check_voice_consistency` | transform | Per-chapter voice-signature outlier check (transform). | [details](references/check_voice_consistency.md) |
| `conceptualize` | act | Render a novel-concept document, the first verb of the MVN flow (act). | [details](references/conceptualize.md) |
| `conflict_matrix_report` | transform | Render the full conflict matrix (transform): all typed phobia cells, counts per vector, and the max-intensity pairs that must never co-front a scene without a voice-collision warning. | [details](references/conflict_matrix_report.md) |
| `copy_gate` | effect | Composite gate: surface-level editorial readiness (effect). | [details](references/copy_gate.md) |
| `count_words` | transform | Word + char counter (transform, driver-free). | [details](#count_words) |
| `create_chapter` | effect | Record a Chapter graph node + CHAPTER_OF the parent Novel (effect). | [details](references/create_chapter.md) |
| `create_character_system` | effect | Mint the host ``CharacterSystem`` (effect). | [details](references/create_character_system.md) |
| `create_codex_entry` | effect | Mint a CodexEntry + CODEX_OF edge to the Novel (effect). | [details](references/create_codex_entry.md) |
| `create_culture` | effect | Mint a Culture under a World + PART_OF_WORLD edge (effect). | [details](references/create_culture.md) |
| `create_language` | effect | Mint a Language under a World + PART_OF_WORLD edge (effect). | [details](references/create_language.md) |
| `create_magic_system` | effect | Mint a MagicSystem under a World + PART_OF_WORLD edge (effect). | [details](references/create_magic_system.md) |
| `create_novel` | effect | Record a Novel node SERVING the intent, materialising disk on production. | [details](references/create_novel.md) |
| `create_religion` | effect | Mint a Religion under a World + PART_OF_WORLD edge (effect). | [details](references/create_religion.md) |
| `create_scene` | effect | Record a Scene node + SCENE_OF the parent Chapter (effect). | [details](references/create_scene.md) |
| `create_storyform` | effect | Mint the Storyform node for a novel + STORYFORM_OF edge (effect). | [details](references/create_storyform.md) |
| `create_storyform_set` | effect | Mint a ``StoryformSet`` grouping N simultaneous storyforms (effect). | [details](references/create_storyform_set.md) |
| `create_voice_profile` | effect | Mint (or overwrite) the character's ``VoiceProfile`` + ``VOICE_OF`` edge (effect). | [details](references/create_voice_profile.md) |
| `create_world` | effect | Mint a World node + SERVES intent (effect). | [details](references/create_world.md) |
| `create_world_axiom` | effect | Encode a WorldAxiom (rule) under a World (effect). | [details](references/create_world_axiom.md) |
| `define_mode_block` | effect | Mint a ``ModeBlock`` — a chapter span sharing a narrative stance (effect). | [details](references/define_mode_block.md) |
| `developmental_gate` | effect | Composite gate: structure-level editorial readiness (effect). | [details](references/developmental_gate.md) |
| `dispatch_novel_research` | effect | Mint a research lead + record NovelClaim (delegates to research cap). | [details](references/dispatch_novel_research.md) |
| `dual_storyform_coherence_check` | act | Composite (act): ``novel_coherence_check`` on EACH member + Klein-c inversion + legality of every recorded transition; records a ``dual-storyform-report`` Artefact. | [details](references/dual_storyform_coherence_check.md) |
| `events_pov_witnessed` | transform | The POV knowledge intersection (transform): events REVEALED_IN a scene the character fronts (``pov_character_id``), optionally cut to those with ``when_story`` < ``before_when``. |witnessed| ≤ |all|. | [details](references/events_pov_witnessed.md) |
| `export_docx` | effect | Render manuscript + write docx via FormatDriver (effect). | [details](references/export_docx.md) |
| `export_epub` | effect | Render manuscript + write epub via FormatDriver (effect). | [details](references/export_epub.md) |
| `export_pdf` | effect | Render manuscript + write PDF via FormatDriver (effect). | [details](references/export_pdf.md) |
| `fetch_scene_body` | transform | Spec 220 Slice 1.5 — public retrieval for a scene-body Artefact. | [details](references/fetch_scene_body.md) |
| `find_axiom_contradictions` | effect | Decidable axiom-contradiction scan + emit CONTRADICTS edges (effect). | [details](references/find_axiom_contradictions.md) |
| `find_novel` | transform | Substring-match novel titles (transform, driver-free). | [details](references/find_novel.md) |
| `flag_anachronistic_reference` | transform | Check if the character knows the fact yet (transform). | [details](references/flag_anachronistic_reference.md) |
| `generate_scene_body` | act | Spec 220 Slice 1 — wet scene-body generation via Spec 147 + Spec 279. | [details](references/generate_scene_body.md) |
| `get_storyform` | transform | Return a novel's Storyform node + parsed NCP body (transform). | [details](references/get_storyform.md) |
| `get_structure_template` | transform | Read one template's full body — every beat with its position + author-facing prompt (transform). | [details](references/get_structure_template.md) |
| `get_voice_profile` | transform | Read the character's voice profile (transform). | [details](references/get_voice_profile.md) |
| `integrate_scene_body` | effect | Spec 130 phase 5 — write the generated body back to the Scene (effect). | [details](references/integrate_scene_body.md) |
| `leerstellen_report` | transform | List the registered deliberate gaps (transform). | [details](references/leerstellen_report.md) |
| `line_gate` | effect | Composite gate: prose-level editorial readiness (effect). | [details](references/line_gate.md) |
| `link_character_to_world` | effect | Add a typed edge from Character → World child (effect). | [details](references/link_character_to_world.md) |
| `list_chapters` | transform | List a novel's chapters ordered by number (transform). | [details](references/list_chapters.md) |
| `list_claims` | transform | List captured claims with an optional verified-status filter (transform). | [details](references/list_claims.md) |
| `list_codex_entries` | transform | List CodexEntries for a novel, optionally filtered by kind (transform). | [details](references/list_codex_entries.md) |
| `list_ideas` | transform | List captured ideas with an optional status filter (transform). | [details](references/list_ideas.md) |
| `list_project_rules` | transform | The rule registry (transform), optionally filtered by severity. | [details](references/list_project_rules.md) |
| `list_reveals_in` | transform | List events this scene discloses (transform). | [details](references/list_reveals_in.md) |
| `list_story_events_up_to` | transform | Story-time slice: events with ``when_story`` ≤ this scene's anchor (transform). | [details](references/list_story_events_up_to.md) |
| `list_structure_templates` | transform | Discover the available story-structure templates (transform). | [details](references/list_structure_templates.md) |
| `list_world` | transform | Render a tree of a World's contents (transform). | [details](references/list_world.md) |
| `lock_index` | transform | The Master-Index of active locks (transform) — consulted before any contested drafting decision. | [details](references/lock_index.md) |
| `manuscript_coherence_check` | transform | Chapter-sequence contiguity check (transform, driver-free). | [details](references/manuscript_coherence_check.md) |
| `mark_narrative_beat` | effect | Mint a NarrativeBeat + optional PRECEDES edge from a predecessor (effect). | [details](references/mark_narrative_beat.md) |
| `match_codex_entries` | transform | Scan ``text`` for codex triggers — word-boundary decidable + optional fuzzy judged (transform). | [details](references/match_codex_entries.md) |
| `mode_block_report` | transform | The §1 block table (transform): every block with mode / bridge target / genre; chapters in NO block are the unstaged surface. | [details](references/mode_block_report.md) |
| `motif_echo_report` | transform | Per-scene echo counts + per-motif trail (transform); flags scenes over the cap (stacking = allegory). | [details](references/motif_echo_report.md) |
| `narrative_order` | transform | The narrative order DERIVED as a typed path over PRECEDES (transform) — a topological order of the beat DAG, never an ad-hoc property sort. | [details](references/narrative_order.md) |
| `novel_coherence_check` | effect | Composite gate (Spec 120): runs all 11 storyform checks with chaining. | [details](references/novel_coherence_check.md) |
| `novel_progress` | transform | Aggregate progress (word-count + per-status counts) for a novel (transform). | [details](references/novel_progress.md) |
| `pay_off_anchor` | effect | Record an anchor's payoff scene (effect). | [details](references/pay_off_anchor.md) |
| `pending_verifications` | transform | Aggregate pending claims by domain (transform). | [details](references/pending_verifications.md) |
| `plant_anchor` | effect | Plant a named foreshadowing anchor in a scene (effect) — earliest plant kept; re-planting adds a PLANTS edge without moving the origin. | [details](references/plant_anchor.md) |
| `pov_options` | transform | Structured POV choices for an assumption-gate (transform). | [details](references/pov_options.md) |
| `pre_draft_gate` | effect | Composite gate: storyform + research + chapters present (effect). | [details](references/pre_draft_gate.md) |
| `preflight_report` | act | The pre-scene readiness audit (act) — five read-only verdicts over the 137–144 stack, one composite ``{ready, blockers, warnings}``, and a recorded ``pre-flight`` Artefact. | [details](references/preflight_report.md) |
| `project_rule_gate` | transform | Composite manuscript gate (transform): fails iff any scene carries a finding AT or ABOVE ``block_at``; lower severities surface as warnings (§10.2 — critical strikes, medium/low reviewer-check). | [details](references/project_rule_gate.md) |
| `promote_from_quarry` | effect | Flip a quarry node → proposal + mint the Lock recording the promotion (effect). | [details](references/promote_from_quarry.md) |
| `promote_idea` | effect | Transition an Idea to a Novel, recording the PROMOTED_TO edge (effect). | [details](references/promote_idea.md) |
| `publication_gate` | effect | Terminal composite: publish_ready + ≥1 export + front-matter declared (effect). | [details](references/publication_gate.md) |
| `publish_ready_gate` | effect | Composite gate: contiguous chapters + status ≥ querying (effect). | [details](references/publish_ready_gate.md) |
| `quarry_filter` | transform | List the Steinbruch (transform): quarry-status nodes — deprecated material an author may still mine, never auto-canon. | [details](references/quarry_filter.md) |
| `query_co_front` | transform | Scenes where two system alters co-front (transform): every scene whose cast holds ≥ 2 alters of this system, filtered by pair kind — ``max`` (max-intensity conflict pairs; the canon violation), ``adjacent`` (any conflict edge), ``any`` (all pairs). | [details](references/query_co_front.md) |
| `query_phobia_cycles` | transform | Find PHOBIA_OF cycles in the conflict matrix (transform) — pure edge walk. | [details](references/query_phobia_cycles.md) |
| `query_ready_gate` | effect | Composite gate: status ≥ beta + content-clean (effect). | [details](references/query_ready_gate.md) |
| `reader_function_audit` | transform | Tag which Iser reader-layers a scene serves (transform): does it give the reader something to ASSEMBLE, not just consume? | [details](references/reader_function_audit.md) |
| `record_alter_conflict` | effect | Mint the ``PHOBIA_OF`` conflict-matrix edge a→b (effect). | [details](references/record_alter_conflict.md) |
| `record_character_learns` | effect | Mint a KnownFact + KNOWS + LEARNED_IN edges (effect). | [details](references/record_character_learns.md) |
| `record_leerstelle` | effect | Register a DELIBERATE Iser gap (effect) — so a reviewer sees the indeterminacy is intentional, not a defect. | [details](references/record_leerstelle.md) |
| `record_lock` | effect | Mint a ``Lock`` — a canonized decision (effect). | [details](references/record_lock.md) |
| `record_motif_echo` | effect | Log a motif echo in a scene (effect); mints the Motif on first sight (its ``first_event_chapter`` = this scene's chapter). | [details](references/record_motif_echo.md) |
| `record_story_event` | effect | Mint a StoryTimeEvent + optional HAPPENS_AT edge from a scene (effect). | [details](references/record_story_event.md) |
| `record_storyform_decision` | effect | Record a contested storyform decision (effect, xcap to dogfood). | [details](references/record_storyform_decision.md) |
| `record_storyform_transition` | effect | Record a Vortex — where one storyform overtakes another (effect). | [details](references/record_storyform_transition.md) |
| `register_project_rule` | effect | Author an R-rule (effect) — upsert keyed by (novel, rule_id). | [details](references/register_project_rule.md) |
| `rename_novel` | effect | Update a Novel's title (effect, graph-only). | [details](references/rename_novel.md) |
| `render_all` | effect | Re-materialise a novel's full markdown tree from graph ground truth (effect). | [details](references/render_all.md) |
| `render_blurb` | act | Render a back-cover blurb (act, driver-free). | [details](references/render_blurb.md) |
| `render_chapter_brief` | act | Produce a research-dossier brief tied to a chapter (act, xcap to prompt). | [details](references/render_chapter_brief.md) |
| `render_chapter_briefing` | act | Compose the 13-section chapter briefing (act) — AGGREGATES the whole KP stack (mode-block 141, storyform routing 136, alters/voice 138, reveals 139, motifs/anchors/R-rules 140) into the vendored template; records a ``chapter-briefing`` Artefact. | [details](references/render_chapter_briefing.md) |
| `render_manuscript` | act | Concatenate chapters into a manuscript artefact (act). | [details](references/render_manuscript.md) |
| `render_query_letter` | act | Render an agent query letter (act, driver-free). | [details](references/render_query_letter.md) |
| `render_synopsis` | act | Render a synopsis from chapter outline (act, driver-free). | [details](references/render_synopsis.md) |
| `resolve_canon_conflict` | transform | Apply the ONE conflict rule (transform): any canonical/proposal beats every quarry; among non-quarry the later ``source_date`` wins; exact ties return ``tied=True``. | [details](references/resolve_canon_conflict.md) |
| `resume_session` | transform | Return the most-recently-created Novel's id + title (transform). | [details](references/resume_session.md) |
| `reveal_gate` | transform | Composite pre-publication discipline (transform): passes IFF no scene breaches a tier floor for any ruled fact AND the veil holds. | [details](references/reveal_gate.md) |
| `reveal_in_scene` | effect | Add the REVEALED_IN edge (event disclosed by this scene) (effect). | [details](references/reveal_in_scene.md) |
| `reveal_timeline_report` | transform | The per-tier "who knows what when" map (transform) — every rule sorted by ``may_know_from_chapter`` (the KP §6.2 Reveal-Timeline). | [details](references/reveal_timeline_report.md) |
| `route_scene_storyform` | effect | Route a scene between the live storyforms (effect). | [details](references/route_scene_storyform.md) |
| `run_project_rules` | transform | Run EVERY registered R-rule over one scene (transform) — the §10.3 per-scene self-review checklist made executable. | [details](references/run_project_rules.md) |
| `scan_proper_nouns` | transform | Extract proper nouns (Title-Case words, sentence-starter words filtered) (transform). | [details](references/scan_proper_nouns.md) |
| `score_voice_match` | transform | Score prose against the character's profile — 0–100, equal-weighted across the SET fields (transform; OQ2 v1). | [details](references/score_voice_match.md) |
| `set_canon_status` | effect | Stamp any node with a ``CANON_STATUS`` marker (effect). | [details](references/set_canon_status.md) |
| `set_chapter_status` | effect | Flip a Chapter's enum-checked lifecycle status (effect). | [details](references/set_chapter_status.md) |
| `set_novel_status` | effect | Flip a Novel's enum-checked lifecycle status (effect). | [details](references/set_novel_status.md) |
| `set_reveal_rule` | effect | Mint/update a ``RevealRule`` — upsert keyed by (novel, fact, tier) (effect). | [details](references/set_reveal_rule.md) |
| `story_time_query` | transform | The continuity scan (transform): every StoryTimeEvent + beat, and SURFACED temporal contradictions — an event whose scene-order (HAPPENS_AT) contradicts its ``when_story`` ordering is returned in ``contradictions``, never silently sorted around. | [details](references/story_time_query.md) |
| `storyform_critical_pass` | act | Critical-thinking pass over the storyform (act, xcap to thinking). | [details](references/storyform_critical_pass.md) |
| `structure_position_report` | transform | Target vs actual manuscript position per anchored beat (transform). | [details](references/structure_position_report.md) |
| `switching_log` | transform | Infer per scene which alter fronts (transform) — matched from the bound voice signatures against the scene body — plus the R-4 micro-cue count (max 3 per bridge). | [details](references/switching_log.md) |
| `update_codex_entry` | effect | Edit a CodexEntry's body / triggers / name (effect). | [details](references/update_codex_entry.md) |
| `update_voice_profile` | effect | Partial update of any profile field (effect). | [details](references/update_voice_profile.md) |
| `validate_appreciations` | transform | Row 12 hybrid: NCP appreciations ∈ canonical 463 (transform). | [details](references/validate_appreciations.md) |
| `validate_narrative_functions` | transform | Row 13 hybrid: NCP narrative_functions ∈ canonical 144 (transform). | [details](references/validate_narrative_functions.md) |
| `validate_no_fusion` | transform | The resolution invariant (transform): no alter may be marked fused/eliminated — the canonical end-state is functional multiplicity, a plural "Wir", never a merged single self. | [details](references/validate_no_fusion.md) |
| `voice_drift_gate` | transform | Composite gate: passes IFF every POV scene with a profiled character scores ≥ ``min_score`` (transform). | [details](references/voice_drift_gate.md) |
| `voice_drift_report` | transform | Full-manuscript voice audit (transform): every POV scene scored against its character's profile, worst-first per character; the bottom 10% manuscript-wide flagged as outliers. | [details](references/voice_drift_report.md) |
| `what_does_X_know_as_of` | transform | List facts the character has learned ≤ the scene's narrative position (transform). | [details](references/what_does_X_know_as_of.md) |

## Example

```bash
await call_tool('capability_novel_add_alter', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-rolling chapter files outside the capability → call `novel.create_chapter`
- Skipping the conceptualizer's hard gate → walk `novel-concept`

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`alter-roster-builder`** (builder): system-create → roster-add → voice-bind → matrix-record → mirror-bind → discipline-verify
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'alter-roster-builder', 'inputs': {}, 'intent_id': '…'})`
- **`canon-lock-author`** (builder): stamp-status → record-lock → audit-review → index-publish
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'canon-lock-author', 'inputs': {}, 'intent_id': '…'})`
- **`chapter-briefing-author`** (builder): block-assign → render-briefing → gap-resolve → checklist-run → archive-as-artefact
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'chapter-briefing-author', 'inputs': {}, 'intent_id': '…'})`
- **`character-architect`** (conceptualizer): psychology → archetype → voice → confirmation
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'character-architect', 'inputs': {}, 'intent_id': '…'})`
- **`developmental-editor`** (editor): structure-pass → storyform-pass → developmental-gate → voice-pass → sign-off
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'developmental-editor', 'inputs': {}, 'intent_id': '…'})`
- **`dual-storyform-author`** (builder): define-set → add-A → add-B → verify-inversion → route-first-scenes
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'dual-storyform-author', 'inputs': {}, 'intent_id': '…'})`
- **`line-editor`** (editor): prose-pass → pov-pass → line-gate → sign-off
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'line-editor', 'inputs': {}, 'intent_id': '…'})`
- **`novel-concept`** (conceptualizer): premise → genre → audience → pov → setting → characters-core → dramatica-seed → outline-shape → series-hypothesis → confirmation
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'novel-concept', 'inputs': {}, 'intent_id': '…'})`
- **`novel-preflight`** (auditor): briefing-ready → canon-clean → reveal-clear → r-rules-dry-run → voice-ready
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'novel-preflight', 'inputs': {}, 'intent_id': '…'})`
- **`publish-prep`** (publisher): manuscript-pass → export-pass → publication-gate → sign-off
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'publish-prep', 'inputs': {}, 'intent_id': '…'})`
- **`r-rule-author`** (builder): pick-predicate → params-author → register → dry-run → gate-attach
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'r-rule-author', 'inputs': {}, 'intent_id': '…'})`
- **`reveal-rule-author`** (builder): enumerate-facts → set-rules → veil-configure → gate-verify
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'reveal-rule-author', 'inputs': {}, 'intent_id': '…'})`
- **`scene-bridge-auditor`** (auditor): Q1-purpose → Q2-POV → Q3-stakes → Q4-conflict → Q5-payoff-and-signoff
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'scene-bridge-auditor', 'inputs': {}, 'intent_id': '…'})`
- **`scene-writer`** (writer): assemble → validate-constraints → generate → check → integrate
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'scene-writer', 'inputs': {}, 'intent_id': '…'})`
- **`storyform-build`** (builder): throughline-partition → concern-and-signposts → elements-and-pair → dynamics-and-style → ncp-shape → composite-gate → structure-template-pick
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'storyform-build', 'inputs': {}, 'intent_id': '…'})`
- **`world-bible-architect`** (conceptualizer): geography → cultures → religions-languages → magic-systems → canon-lock
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'world-bible-architect', 'inputs': {}, 'intent_id': '…'})`

## Calling these verbs (code-mode)

Every verb here is the prefixed wire tool ``capability_novel_<verb>`` (underscores, not the hyphenated skill name). Call it inside an ``execute`` block, threading the serving ``intent_id``. ``get_schema`` an unfamiliar verb first (``detail="full"`` reveals nested object-param shapes):

```python
iid = (await call_tool("intent_bootstrap", {"purpose": "…", "deliverable": "…", "acceptance": "…"}))["intent_id"]
await call_tool("capability_novel_add_alter", {"intent_id": iid})
await call_tool("capability_novel_add_storyform_to_set", {"intent_id": iid})
await call_tool("capability_novel_analyze_readability", {"intent_id": iid})
await call_tool("capability_novel_anchor_beat", {"intent_id": iid})
await call_tool("capability_novel_anchor_status_report", {"intent_id": iid})
await call_tool("capability_novel_apply_structure", {"intent_id": iid})
```

More verbs: `capability_novel_archive_codex_entry`, `capability_novel_assign_chapter_to_block`, `capability_novel_assign_voice_to_alter`, `capability_novel_audit_novel_provenance`, `capability_novel_beta_ready_gate`, `capability_novel_bridge_frequency_report`, `capability_novel_briefing_checklist`, `capability_novel_canon_audit` …

## analyze_readability

Flesch Reading Ease for prose (transform, driver-free).

Parameters: `(body: 'str')`.

## count_words

Word + char counter (transform, driver-free).

Parameters: `(body: 'str')`.
