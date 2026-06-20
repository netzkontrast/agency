---
capability: novel
pillar: capability
vision_goals: []        # TODO(why-author): which GOALS.md goals this serves
status: living
last_generated: 2026-06-13
sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this
---

# novel — Five-verb path from premise to manuscript: conceptualize → create_novel → create_chapter → chapter_report → render_manuscript, plus the novel-concept gated planning skill (capability pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
_TODO: authored intent._

## Verbs (generated · 95)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `novel.analyze_readability` | transform | **body** | Flesch Reading Ease for prose (transform, driver-free). |
| `novel.archive_codex_entry` | effect | **entry_id** · reason | Flag a CodexEntry as archived (effect, soft-delete). |
| `novel.audit_novel_provenance` | transform | **novel_id** | Aggregate the provenance graph census for the serving intent (transform, xcap to analyze). |
| `novel.beta_ready_gate` | effect | **novel_id** | Composite gate: all chapters drafted+ (effect). |
| `novel.capture_claim` | effect | **text** · **source_uri** · **domain** | Record a NovelClaim node SERVING the intent (effect). |
| `novel.capture_idea` | effect | **text** | Record an Idea node SERVING the intent (effect). |
| `novel.chapter_report` | transform | **novel_id** | Read-only aggregate over the novel's chapters (transform). |
| `novel.chapter_report_full` | act | **chapter_id** | Full editorial dashboard for one chapter (act). |
| `novel.check_approach_concern` | transform | **ncp** | Mostly-decidable check (row 8): approach ↔ class compatibility (WARN-severity). |
| `novel.check_content_warnings` | transform | **body** | Content-warning category scanner (transform, driver-free). |
| `novel.check_continuity` | transform | **novel_id** | Cross-chapter proper-noun continuity check (transform). |
| `novel.check_crucial_element_placement` | transform | **ncp** | Decidable check (row 6): storyform.crucial_element_id == mc.problem_id. |
| `novel.check_dialogue_attribution` | transform | **body** | Dialogue-tag check — plain ('said') vs flowery (transform). |
| `novel.check_dynamic_pair_reciprocity` | transform | **ncp** | Decidable check (row 1): mc.dynamic and os.dynamic must differ. |
| `novel.check_filter_words` | transform | **body** · threshold | Filter-word density check (transform, show-don't-tell). |
| `novel.check_ktad_coverage` | transform | **ncp** | Decidable check (row 2): concern_id == signposts[0] (K-position). |
| `novel.check_mental_sex_problem_solving` | transform | **ncp** | Decidable check (row 9): mental_sex ↔ class compatibility. |
| `novel.check_pov_consistency` | transform | **novel_id** | Per-chapter POV uniformity check across scenes (transform). |
| `novel.check_quad_completeness` | transform | **ncp** | Decidable check (row 3): mc problem and solution are paired. |
| `novel.check_resolve_outcome_judgment` | transform | **ncp** | Decidable check (row 7): resolve/outcome/judgment triple is legal. |
| `novel.check_sensitivity` | transform | **body** | Sensitivity-topic advisory scan (transform, WARN-severity). |
| `novel.check_show_dont_tell` | transform | **body** | Telling-verb scan — interior-monologue tells (transform). |
| `novel.check_signpost_permutation` | transform | **ncp** | Decidable check (row 10): signposts in canonical order per class. |
| `novel.check_slot_fill` | transform | **ncp** | Decidable check (row 4): no null required slots (transform). |
| `novel.check_storybeat_moment_refs` | transform | **ncp** | Decidable check (row 11): every moment.storybeat_ref resolves (transform). |
| `novel.check_throughline_partition` | transform | **ncp** | Decidable check (row 5): 4 throughlines / 4 distinct Classes (transform). |
| `novel.check_voice_consistency` | transform | **bodies** · z_threshold | Per-chapter voice-signature outlier check (transform). |
| `novel.conceptualize` | act | **title** · **author** · premise · central_question | Render a novel-concept document (act); the first verb of the MVN flow. |
| `novel.copy_gate` | effect | **novel_id** | Composite gate: surface-level editorial readiness (effect). |
| `novel.count_words` | transform | **body** | Word + char counter (transform, driver-free). |
| `novel.create_chapter` | effect | **novel_id** · **number** · **title** · body | Record a Chapter graph node + CHAPTER_OF the parent Novel (effect). |
| `novel.create_codex_entry` | effect | **novel_id** · **slug** · **name** · **kind** · **body** · triggers | Mint a CodexEntry + CODEX_OF edge to the Novel (effect). |
| `novel.create_culture` | effect | **world_id** · **slug** · **name** | Mint a Culture under a World + PART_OF_WORLD edge (effect). |
| `novel.create_language` | effect | **world_id** · **slug** · **name** | Mint a Language under a World + PART_OF_WORLD edge (effect). |
| `novel.create_magic_system` | effect | **world_id** · **slug** · **name** | Mint a MagicSystem under a World + PART_OF_WORLD edge (effect). |
| `novel.create_novel` | effect | **title** · **author** · genre | Record a Novel node SERVING the intent; materialise disk on production. |
| `novel.create_religion` | effect | **world_id** · **slug** · **name** | Mint a Religion under a World + PART_OF_WORLD edge (effect). |
| `novel.create_scene` | effect | **chapter_id** · **slug** · **pov** | Record a Scene node + SCENE_OF the parent Chapter (effect). |
| `novel.create_storyform` | effect | **novel_id** · body | Mint the Storyform node for a novel + STORYFORM_OF edge (effect). |
| `novel.create_world` | effect | **slug** · **name** | Mint a World node + SERVES intent (effect). |
| `novel.create_world_axiom` | effect | **world_id** · **text** · severity | Encode a WorldAxiom (rule) under a World (effect). |
| `novel.developmental_gate` | effect | **novel_id** | Composite gate: structure-level editorial readiness (effect). |
| `novel.dispatch_novel_research` | effect | **question** · **domain** | Mint a research lead + record NovelClaim (delegates to research cap). |
| `novel.export_docx` | effect | **novel_id** | Render manuscript + write docx via FormatDriver (effect). |
| `novel.export_epub` | effect | **novel_id** | Render manuscript + write epub via FormatDriver (effect). |
| `novel.export_pdf` | effect | **novel_id** | Render manuscript + write PDF via FormatDriver (effect). |
| `novel.fetch_scene_body` | transform | body_handle · max_chars | Spec 220 Slice 1.5 — public retrieval for a scene-body Artefact. |
| `novel.find_axiom_contradictions` | effect | **world_id** | Decidable axiom-contradiction scan + emit CONTRADICTS edges (effect). |
| `novel.find_novel` | transform | query | Substring-match novel titles (transform, driver-free). |
| `novel.flag_anachronistic_reference` | transform | **scene_id** · **character_id** · **fact_text** | Check if the character knows the fact yet (transform). |
| `novel.generate_scene_body` | act | scene_id · scene_brief · alter_id · system · host_completion · prefer_delegate · max_tokens | Spec 220 Slice 1 — wet scene-body generation via Spec 147 + Spec 279. |
| `novel.get_storyform` | transform | **novel_id** | Return a novel's Storyform node + parsed NCP body (transform). |
| `novel.integrate_scene_body` | effect | **scene_id** · **body** | Spec 130 phase 5 — write the generated body back to the Scene (effect). |
| `novel.line_gate` | effect | **novel_id** | Composite gate: prose-level editorial readiness (effect). |
| `novel.link_character_to_world` | effect | **character_id** · **target_id** · edge_kind | Add a typed edge from Character → World child (effect). |
| `novel.list_chapters` | transform | **novel_id** | List a novel's chapters ordered by number (transform). |
| `novel.list_claims` | transform | verified | List captured claims; optional verified-status filter (transform). |
| `novel.list_codex_entries` | transform | **novel_id** · kind | List CodexEntries for a novel, optionally filtered by kind (transform). |
| `novel.list_ideas` | transform | status | List captured ideas; optional status filter (transform). |
| `novel.list_reveals_in` | transform | **scene_id** | List events this scene discloses (transform). |
| `novel.list_story_events_up_to` | transform | **scene_id** | Story-time slice: events with ``when_story`` ≤ this scene's anchor (transform). |
| `novel.list_world` | transform | **world_id** | Render a tree of a World's contents (transform). |
| `novel.manuscript_coherence_check` | transform | **novel_id** | Chapter-sequence contiguity check (transform, driver-free). |
| `novel.mark_narrative_beat` | effect | **scene_id** · **beat_label** · predecessor_id | Mint a NarrativeBeat + optional PRECEDES edge from a predecessor (effect). |
| `novel.match_codex_entries` | transform | **novel_id** · **text** | Scan ``text`` for any registered codex trigger; return matches (transform). |
| `novel.narrative_order` | transform | **novel_id** | Topo-sort over PRECEDES; canonical narrative reading order (transform). |
| `novel.novel_coherence_check` | effect | **ncp** | Composite gate (Spec 120): runs all 11 storyform checks with chaining. |
| `novel.novel_progress` | transform | **novel_id** | Aggregate progress (word-count + per-status counts) for a novel (transform). |
| `novel.pending_verifications` | transform |  | Aggregate pending claims by domain (transform). |
| `novel.pov_options` | transform | keys | Structured POV choices for an assumption-gate (transform). |
| `novel.pre_draft_gate` | effect | **novel_id** | Composite gate: storyform + research + chapters present (effect). |
| `novel.promote_idea` | effect | **idea_id** · **title** · **author** | Idea → Novel transition; records PROMOTED_TO edge (effect). |
| `novel.publication_gate` | effect | **novel_id** | Terminal composite: publish_ready + ≥1 export + front-matter declared (effect). |
| `novel.publish_ready_gate` | effect | **novel_id** | Composite gate: contiguous chapters + status ≥ querying (effect). |
| `novel.query_ready_gate` | effect | **novel_id** | Composite gate: status ≥ beta + content-clean (effect). |
| `novel.record_character_learns` | effect | **character_id** · **fact** · **scene_id** | Mint a KnownFact + KNOWS + LEARNED_IN edges (effect). |
| `novel.record_story_event` | effect | **novel_id** · **label** · **when_story** · scene_id | Mint a StoryTimeEvent + optional HAPPENS_AT edge from a scene (effect). |
| `novel.record_storyform_decision` | effect | **novel_id** · **decision** · rationale | Record a contested storyform decision (effect, xcap to dogfood). |
| `novel.rename_novel` | effect | **novel_id** · **new_title** | Update a Novel's title (effect, graph-only). |
| `novel.render_all` | effect | **novel_id** | Re-materialise a novel's full markdown tree from graph ground truth (effect). |
| `novel.render_blurb` | act | **novel_id** · **hook** · **stakes** | Render a back-cover blurb (act, driver-free). |
| `novel.render_chapter_brief` | act | **chapter_id** · research_intent_id | Produce a research-dossier brief tied to a chapter (act, xcap to prompt). |
| `novel.render_manuscript` | act | **novel_id** | Concatenate chapters into a manuscript artefact (act). |
| `novel.render_query_letter` | act | **novel_id** · **agent_name** · comp_titles | Render an agent query letter (act, driver-free). |
| `novel.render_synopsis` | act | **novel_id** | Render a synopsis from chapter outline (act, driver-free). |
| `novel.resume_session` | transform |  | Return the most-recently-created Novel's id + title (transform). |
| `novel.reveal_in_scene` | effect | **event_id** · **scene_id** | Add the REVEALED_IN edge (event disclosed by this scene) (effect). |
| `novel.scan_proper_nouns` | transform | **body** | Extract proper nouns (Title-Case words, sentence-starter words filtered) (transform). |
| `novel.set_chapter_status` | effect | **chapter_id** · **status** | Flip a Chapter's lifecycle status; enum-checked (effect). |
| `novel.set_novel_status` | effect | **novel_id** · **status** | Flip a Novel's lifecycle status; enum-checked (effect). |
| `novel.storyform_critical_pass` | act | **novel_id** | Critical-thinking pass over the storyform (act, xcap to thinking). |
| `novel.update_codex_entry` | effect | **entry_id** · body · triggers · name | Edit a CodexEntry's body / triggers / name (effect). |
| `novel.validate_appreciations` | transform | **ncp** | Row 12 hybrid: NCP appreciations ∈ canonical 463 (transform). |
| `novel.validate_narrative_functions` | transform | **ncp** | Row 13 hybrid: NCP narrative_functions ∈ canonical 144 (transform). |
| `novel.what_does_X_know_as_of` | transform | **character_id** · **scene_id** | List facts the character has learned ≤ the scene's narrative position (transform). |

## Ontology (generated)

**Nodes:** `Novel`(title, author, status) · `Chapter`(novel, number, title, status) · `Idea`(text) · `Storyform`(novel) · `NovelClaim`(text, source_uri, domain) · `Scene`(chapter, slug, pov) · `World`(slug, name) · `Culture`(slug, name) · `Religion`(slug, name) · `Language`(slug, name) · `MagicSystem`(slug, name) · `WorldAxiom`(text, severity) · `StoryTimeEvent`(novel, label, when_story) · `NarrativeBeat`(novel, label, scene) · `CodexEntry`(novel, slug, name, kind) · `KnownFact`(character, fact)
**Edges:** `BELONGS_TO` · `CHAPTER_OF` · `CODEX_OF` · `CONTRADICTS` · `HAPPENS_AT` · `INHABITS` · `KNOWS` · `LEARNED_IN` · `PART_OF_WORLD` · `PRECEDES` · `PROMOTED_TO` · `REVEALED_IN` · `SCENE_OF` · `SPEAKS` · `STORYFORM_OF` · `WIELDS` · `WORSHIPS`
**Enums:** `('Novel', 'status')` ∈ {beta, concept, drafting, outlining, published, querying, revising} · `('Chapter', 'status')` ∈ {drafted, final, outlined, revised} · `('Idea', 'status')` ∈ {dropped, new, promoted} · `('NovelClaim', 'verified')` ∈ {confirmed, needs-source, pending, refuted} · `('NovelClaim', 'domain')` ∈ {biographical, cultural, geographical, historical, linguistic, philosophical, political, religious, scientific, technological} · `('Scene', 'pov')` ∈ {first, second, third-limited, third-omniscient} · `('WorldAxiom', 'severity')` ∈ {hard, soft} · `('CodexEntry', 'kind')` ∈ {artefact, concept, faction, location, minor-character}

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/novel -->
