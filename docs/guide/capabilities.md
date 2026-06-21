# Capability reference

<!-- doc-generated-by: scripts/gen-capability-docs (re-run; do not hand-edit) -->

> **Generated** from the live registry by `scripts/gen-capability-docs`. Every capability self-registers from `agency/capabilities/`; this page is rendered from the running engine, so it is always current. Per-capability deep docs (the L1/L2/L3 Agent Skill) live in `skills/<capability>/SKILL.md`.

**35 core capabilities.** Domain capabilities (e.g. `music`) load out-of-tree via `Engine(..., extra_capabilities=[…])` — see `examples/music.py` + [../vision/reference/drivers.md](../vision/reference/drivers.md).

The wire contract is always the same three substrate tools — **`search` · `get_schema` · `execute`** — plus a few bootstrap tools; every verb below is reached through `execute` (code-mode) or its `agency <cap> <verb>` CLI mirror.

---
## `adr`  (memory)

Use when an architectural decision must be RECORDED as a first-class,

**Walkable skills:** `adr-usage`

| verb | role | summary |
|---|---|---|
| `adr.approve` | act | APPROVE — the DoD hinge (SPEC-001-E pre-approval gate). Runs `dod_check`; |
| `adr.dod_check` | transform | DOD_CHECK — run the ported SPEC-001-E Definition-of-Done criteria over a |
| `adr.draft` | act | DRAFT — record a WH(Y) ``Decision`` (status ``proposed``) ``PART_OF`` |
| `adr.extract_decisions` | act | EXTRACT_DECISIONS — surface a spec's key decisions as WH(Y) candidates |
| `adr.hints` | transform | HINTS — the payoff: at implementation start, project the spec's |
| `adr.impact` | transform | IMPACT — what ``DEPENDS_ON`` / ``REFINES`` / ``PART_OF`` this decision, |
| `adr.link` | act | LINK — add a typed SPEC-001-C dependency edge between two Decisions. |
| `adr.read` | act | READ a ``Decision``'s current WH(Y) fields + status (the domain read — |
| `adr.render` | act | RENDER — project a theme's **live** decisions into a markdown body and |
| `adr.spec_decisions_ready` | transform | SPEC_DECISIONS_READY — the /open→/inprogress predicate (358). ``ready`` |
| `adr.supersede` | act | SUPERSEDE — the SPEC-001-C automatic actions: mint a replacement |
| `adr.theme` | act | THEME — get-or-create a thematic-living ADR for one architecture |
| `adr.theme_status` | transform | THEME_STATUS — the SPEC-001-D aggregate status DERIVED from the theme's |
| `adr.update` | act | UPDATE a ``Decision`` in place — advance its ``status`` and/or fill WH(Y) |
| `adr.validate` | transform | VALIDATE — run the decidable WH(Y) rules over a Decision; return |

## `analyze`  (capability)

Use when assessing a codebase or diff for quality, security, performance, or architecture problems before review or shipping — surfaces decidable findings as graph artefacts.

**Walkable skills:** `code-analysis`

| verb | role | summary |
|---|---|---|
| `analyze.architecture` | transform | Dependency-graph + structural checks: import cycles, file LOC thresholds. |
| `analyze.cleanup` | act | Focused mode: analyse for dead-code findings only, draft a patch plan. |
| `analyze.graph` | transform | Query the provenance graph — a census of node types + a typed listing (read the graph). |
| `analyze.improve` | act | Read prior Analysis findings, draft an improvement plan as a Reflection. |
| `analyze.paths` | transform | Spec 048 intent-path analysis: long chains + verb sequences. |
| `analyze.performance` | transform | AST-based hot-path lint: nested O(n²), += in loop, unbounded while True. |
| `analyze.quality` | transform | Decidable lint findings: unused imports, long lines, long functions, long files. |
| `analyze.run` | act | Run the requested analysis axes and record an Analysis + per-Finding nodes. |
| `analyze.security` | transform | Decidable security patterns: eval/exec, hardcoded credentials, pickle.load, shell=True. |

## `branch`  (lifecycle)

Use when a development branch is ready to wrap up and its state must be detected to merge, open a PR, or report what blocks completion.

**Walkable skills:** `branch-usage`

| verb | role | summary |
|---|---|---|
| `branch.assess` | transform | Read the branch state (ahead/behind/dirty) and recommend merge/pr/keep/discard. |
| `branch.commit_smart` | transform | Compose a conventional-commit message from a change summary + the changed paths |
| `branch.finish` | effect | Finish the branch by the chosen action (merge/pr/keep/discard) and record the outcome. |

## `config`  (capability)

Use when you need to read or change an agency config value (e.g. frugal.level, a

**Walkable skills:** `config-usage`

| verb | role | summary |
|---|---|---|
| `config.get` | act | Resolve a config key to its live value + source. |
| `config.list` | act | Every registered config key → value + source, plus validation issues. |
| `config.set` | act | Persist a config value to ``.agency/config.yaml``, then re-resolve it. |

## `delegate`  (lifecycle)

Use when a task might be better handled by a subagent (local, Jules, or another driver) and the choice to dispatch versus stay inline must be weighed, then work fanned out and the results joined.

**Walkable skills:** `dispatch-decision`, `dispatching-parallel-agents`

| verb | role | summary |
|---|---|---|
| `delegate.dispatch_bash_hints` | transform | Compose the bash-hint context block for a dispatch prompt. |
| `delegate.dispatch_decision` | transform | Apply the dispatch-vs-inline heuristic and return a recommendation. |
| `delegate.fan_out` | effect | Open one child Lifecycle per item (capped at `quota`), dispatch the driver |
| `delegate.join` | act | Reduce a delegation over its children's Lifecycle state. |

## `develop`  (lifecycle)

Use when building the system further — walking a development discipline (tdd, plan, review), scaffolding a new capability, running a skill to its first hard gate, reloading edited capability code mid-session, or looking up code (use codegraph).

**Walkable skills:** `authoring-capabilities`, `brainstorm`, `debug`, `execute`, `plan`, `plan-execute`, `review`, `session-driver-pass`, `spec-panel`, `tdd`, `verify`

| verb | role | summary |
|---|---|---|
| `develop.checklist` | transform | Project a discipline (skill walk) into a step-by-step checklist. |
| `develop.draft_plan` | act | Author a bite-sized plan as graph provenance (Spec 287; rule 2). |
| `develop.estimate` | transform | Decidable effort estimate from change-size inputs (Spec 046 F-D — sc-estimate, |
| `develop.index` | effect | Index a repo as a token-cheap briefing — the development-workflow |
| `develop.maintain` | act | Drive — and AUTOLEARN — the recurring "Agency Steward" maintenance loop. |
| `develop.mode_select` | effect | Switch session mode + record a ModeShift node (effect). |
| `develop.optimize_skilldoc` | act | Author an optimized functional doc — flags + candidate, NO rewrite (act). |
| `develop.plan_status` | transform | Roll up a Plan's steps + completion (Spec 287) — the render-on-demand |
| `develop.record_authoring_outcome` | act | Record a Reflection at the end of an authoring-capabilities walk. |
| `develop.record_step_outcome` | act | Mark a PlanStep's execution outcome (Spec 287). |
| `develop.reference` | transform | Fetch a discipline's heavy how-to on demand (T3 disclosure). |
| `develop.reload` | effect | Reload edited capability code into the live session (effect). |
| `develop.scaffold_capability` | act | Emit a CAPABILITY-AUTHORING.md-compliant capability skeleton. |
| `develop.session_check` | transform | Read the current SessionLifecycle state (transform). |
| `develop.session_init` | act | Mint a SessionLifecycle SERVING the intent, detect mode, and suggest the first verb. |
| `develop.session_resume` | transform | Spec 114 Slice 2 — cross-session handoff. |
| `develop.skill_walk` | act | Walk a registered skill to the first hard gate in ONE call (the atomic walker). |
| `develop.validate_skill` | transform | Validate a capability's Agent-Skill (its SkillDoc) — lint + dry-run emit. |

## `discover`  (capability)

Use when a fresh or vague intent needs guided discovery BEFORE work begins —

**Walkable skills:** `discover-usage`

| verb | role | summary |
|---|---|---|
| `discover.acceptance` | transform | Derive testable, Gherkin-shaped acceptance criteria from the Intent (transform). |
| `discover.ask` | transform | Build ONE well-formed AskUserQuestion payload from DERIVED options (transform). |
| `discover.clarify` | act | Resolve a draft Intent's ambiguities, folding each answer back (act). |
| `discover.clarity` | transform | Score a captured Intent's clarity / readiness (transform, read-only). |
| `discover.clarity_gate` | effect | Composite clarity gate — records outcome via gate.check (effect). |
| `discover.interview` | act | Run the adaptive elicitation interview → a DRAFT Intent (act). |
| `discover.scope` | act | Elicit in-/out-of-scope boundaries (act). |
| `discover.status` | transform | Smoke verb — report the registered ``discover`` ontology surface. |

## `doctrine`  (capability)

Use when a decision must be grounded in a stated principle/rule, or two

**Walkable skills:** `doctrine-usage`

| verb | role | summary |
|---|---|---|
| `doctrine.cite` | effect | Record that a principle or rule DROVE an action — a DoctrineCitation |
| `doctrine.principles` | act | The engineering-principles roster — name · statement (Spec 303). |
| `doctrine.resolve` | act | Adjudicate two conflicting concerns by the conflict hierarchy |
| `doctrine.rules` | act | The behavioral rules, optionally filtered by priority (Spec 303). |

## `document`  (memory)

Use when a repository's structure must be understood or rendered — an explanation of a subsystem, a project index, or a graph-native rendering — without loading the whole tree.

**Walkable skills:** `repo-briefing`

| verb | role | summary |
|---|---|---|
| `document.convergence` | act | Audit a Document's convergence facets (Spec 292 C3). |
| `document.explain` | act | Deterministically explain code as markdown, emitting a Reflection. |
| `document.index_repo` | effect | Deterministic repo briefing. A PREVIEW (``apply=False``) fits ≤ |
| `document.ingest` | effect | Round-trip a markdown file INTO the graph (file → graph; Spec 292). |
| `document.mirror` | effect | Project graph→file AND event-source it (Spec 292 — closes the loop). |
| `document.render` | transform | Deterministically project graph state to markdown. |
| `document.reopen` | effect | Reopen an archived session Document — reconstruct the four concepts |
| `document.restore_session` | act | Restore a complete session from the Session Graph (Spec 292). |
| `document.revisions` | act | Read a Document's keep-both revision history (Spec 292). |
| `document.session` | effect | Render a Session as a Document — the four concepts converge (Spec 292). |
| `document.session_analytics` | act | Cypher analytics over the Session Graph (Spec 292). |
| `document.sync` | effect | Ingest every CHANGED markdown file under ``path`` (Spec 292). |

## `dogfood`  (memory)

Use when recording or rendering observation ledgers in the graph — capturing a development note, exporting the graph for merge-recovery, or importing it back.

**Walkable skills:** `dogfood-usage`

| verb | role | summary |
|---|---|---|
| `dogfood.apply_amendment` | effect | Render a ProposalPayload as a unified diff, recorded as a provenance Artefact. |
| `dogfood.boundary_use_audit` | transform | Audit BoundaryUse nodes — flag raw-tool uses where a verb exists (transform). |
| `dogfood.collect` | transform | Walk ``plan_dir`` for ``DOGFOOD-NOTES.md`` files and extract observations. |
| `dogfood.export` | effect | Dump the provenance store to a portable JSON file. |
| `dogfood.import` | effect | Replay a JSON export into this graph, preserving ids + windows. |
| `dogfood.note` | act | Record an observation Reflection tagged with plan_slug. |
| `dogfood.parse_amendment` | transform | Classify recent Reflections into amendment proposals. |
| `dogfood.recall_overflow_slice` | transform | Spec 154 Slice 3 — recall a paged view of a captured overflow body. |
| `dogfood.record_decision` | effect | Bind a decision to the current session (effect). |
| `dogfood.render` | transform | Project plan_slug observations into DOGFOOD-NOTES.md. |
| `dogfood.replay_events` | transform | Replay every Event recorded OBSERVED_DURING the given intent |

## `frugal`  (lifecycle)

Use when you want to read or switch the active frugal level, pull the ruleset

**Walkable skills:** `frugal`

| verb | role | summary |
|---|---|---|
| `frugal.debt` | effect | Harvest deliberate ``frugal:``/``ponytail:`` shortcut markers into a |
| `frugal.gain` | transform | The frugal impact scoreboard — the published benchmark medians (a |
| `frugal.help` | transform | The frugal reference card (the ponytail-help info): the discipline + |
| `frugal.instructions` | transform | Return the frugal ruleset text at a level — the ponytail-MCP port |
| `frugal.level` | transform | Report the active frugal level (env AGENCY_FRUGAL_LEVEL -> .agency/config.yaml -> full). |
| `frugal.review` | effect | Review for over-engineering ONLY (delete/stdlib/native/yagni/shrink) — |
| `frugal.set_level` | effect | Persist the frugal level (durable across processes via the Spec 334 config). |

## `gate`  (lifecycle)

Use when a programmatic, reusable predicate must pass before work proceeds — an acceptance check recorded as a Gate in the provenance graph.

**Walkable skills:** `gate-usage`

| verb | role | summary |
|---|---|---|
| `gate.adjudicate` | act | Adjudicate two CONFLICTING concerns at a decision point by consulting |
| `gate.check` | act | Record a gate outcome on a Lifecycle: PASSED, or BLOCKED_ON + |

## `intent`  (capability)

Use when examining a goal before committing to an approach — decomposing it, surfacing its assumptions, stress-testing it with a premortem, or weighing trade-offs.

**Walkable skills:** `critical-thinking`

| verb | role | summary |
|---|---|---|
| `intent.assumptions` | transform | Surface + classify the implicit assumptions a goal rests on (load-bearing vs not). |
| `intent.decompose` | transform | Decompose a goal into MECE sub-problems — the structured break-down method. |
| `intent.first_principles` | transform | Strip a goal to fundamental truths and rebuild — bypassing inherited assumptions. |
| `intent.inversion` | transform | Invert the goal — ask what would GUARANTEE failure, then avoid exactly that. |
| `intent.premortem` | transform | Premortem — assume the goal FAILED, reason backward to causes + mitigations. |
| `intent.second_order` | transform | Trace second- and third-order consequences — 'and then what?' past the first effect. |
| `intent.steelman` | transform | Build the STRONGEST version of the opposing or alternative position. |
| `intent.suggests` | transform | Project the serving intent + the last verb's state to the next applicable |
| `intent.tradeoffs` | transform | Build an explicit trade-off matrix — options × criteria — for a decision. |

## `jules`  (lifecycle)

Use when fanning a coding task out to a remote Jules agent session and driving it to a verified PR — dispatching, sending follow-ups, approving plans, and recovering completed-but-unpushed work.

**Walkable skills:** `jules-fanout`, `jules-pr-review-cycle`, `jules-protocol-preamble`, `jules-recovery-when-stuck`, `jules-self-improvement`, `jules-tool-discipline`

| verb | role | summary |
|---|---|---|
| `jules.activities` | transform | A session's activity stream. Trimmed to summaries by default (the |
| `jules.alias` | act | Read or upsert a stable alias for a Jules sid. |
| `jules.apply_patch` | transform | Compute a recovery plan for a session's patch (verb mirror of `recover_apply_plan`). |
| `jules.approve_awaiting` | effect | Bulk-approve every session in AWAITING_PLAN_APPROVAL (up to `limit`). |
| `jules.approve_plan` | effect | Approve a plan in AWAITING_PLAN_APPROVAL — the one state that times out. |
| `jules.detect_mode` | transform | Mode A (dogfood) vs Mode B (delegate) — pure decision on dispatch source. |
| `jules.dispatch` | effect | Spawn a remote Jules session (external effect). Returns id/url/state. |
| `jules.lint_prompt` | transform | Lint a dispatch prompt against the canonical must-name tool list. |
| `jules.list` | transform | Enumerate sessions (trimmed to id/state/title/url; one page — walk via token). |
| `jules.message` | effect | Send a message into a session (feedback / plan-revision / nudge to push). |
| `jules.patch` | transform | Per-output stats (``files``, ``lines``, ``bytes``) from the session's outputs — NO body. |
| `jules.patch_body` | transform | Explicit, capped unidiff retrieval for one of the session's outputs. |
| `jules.plan` | transform | The latest generated plan — show it before approve_plan (no PR exists yet). |
| `jules.quota` | transform | Count sessions created today (UTC). |
| `jules.recover` | effect | Promote a session to the watcher's recovery-in-flight tracker. |
| `jules.resolve_source` | transform | Resolve `owner/repo` to the opaque `sources/<id>` the API expects. |
| `jules.review_comment` | transform | Compose an @jules PR review-comment with the mandatory handshake tail. |
| `jules.status` | transform | Read a session's full state from the backend. |
| `jules.status_all` | transform | Paginated, grouped-by-state listing of every session on the account. |
| `jules.stop` | transform | UNSUPPORTED by design: the Jules v1alpha API exposes no cancel/delete/stop. |
| `jules.verify` | transform | COMPLETED != done — verifies the branch landed on origin. |
| `jules.watch` | transform | Await the next `WatchEvent` for a session or intent. |

## `manage`  (memory)

Use when an agent must directly create / read / update / amend / soft-delete a

**Walkable skills:** `lifecycle-management`

| verb | role | summary |
|---|---|---|
| `manage.amend` | effect | AMEND append-only — close the old version, create a new one linked |
| `manage.artefacts` | act | ARTEFACTS produced under an intent + their source invocations |
| `manage.create` | effect | CREATE a node of any ontology ``label`` that SERVES the intent (Spec 293). |
| `manage.lifecycle` | act | LIFECYCLE READ — the Spec 341 `read` frame: one Lifecycle's full state |
| `manage.lifecycle_trail` | act | LIFECYCLE WATCH — the Spec 341 `watch` frame: the ordered Spec 344 |
| `manage.list` | act | LIST nodes of a ``label``, optionally filtered by exact-match |
| `manage.open_intents` | act | OPEN-INTENTS — live intents + acceptance + SERVES subtree size, |
| `manage.project` | act | PROJECT — a query-ranked, token-budgeted slice of a label's live nodes |
| `manage.provenance` | act | PROVENANCE — the typed cross-concern join (Spec 330/290, Memory · |
| `manage.read` | act | READ a node by id — its current properties + a ``live`` flag |
| `manage.render` | act | RENDER the read-API as a compact markdown dashboard — the "where are |
| `manage.research_state` | act | RESEARCH-STATE — open research leads with their claims, citations and |
| `manage.retract` | effect | RETRACT — bi-temporal SOFT delete: close the node's valid window so |
| `manage.state` | act | STATE rollup — the "where are we" dashboard (Spec 290, on manage). |
| `manage.subtree` | act | SUBTREE — the ``PARENT_INTENT`` sub-intent tree rooted at an intent |
| `manage.timeline` | act | TIMELINE — the ordered Event + Invocation history for an intent |
| `manage.update` | effect | UPDATE a node in place — a bi-temporal revision, stable id (Spec 293). |
| `manage.whats_next` | act | WHATS-NEXT — blocked items + the next actions against an intent's |

## `mode`  (lifecycle)

Use when the way of working should shift for the task at hand — discovery,

**Walkable skills:** `mode-selection`

| verb | role | summary |
|---|---|---|
| `mode.activate` | effect | Activate a behavioral posture — return its rules + record provenance |
| `mode.detect` | act | Rank the behavioral modes by decidable trigger overlap with |
| `mode.list` | act | The behavioral-mode roster — name · purpose · behaviors · triggers. |

## `music`  (capability)

Use when conceptualizing or producing an album — turning an idea into a gated concept, mastering to a target loudness, drafting promo copy, or auditing a release — as the reference for how a first-class clustered domain capability extends agency.

**Walkable skills:** `album-concept`, `lyric-writing`, `mastering`, `mix-polish`, `new-album`, `pre-generation`, `pre-generation-full`, `promo-pass`, `release-publish`, `release-qa`, `release-qa-full`, `research-workflow`, `streaming-verify`, `tweet-curation`, `validate-structure`

| verb | role | summary |
|---|---|---|
| `music.album_coherence_check` | transform | Cross-track tonal coherence report via AudioDriver (transform). |
| `music.album_coherence_correct` | effect | Apply coherence corrections to bring outliers in line (effect). |
| `music.album_progress` | transform | Album progress aggregate via the StateDriver (transform). |
| `music.analyze_audio` | transform | General spectral + loudness probe via AudioDriver (transform). |
| `music.analyze_mix` | transform | Analyse a mix for loudness issues via the AudioDriver (transform). |
| `music.analyze_readability` | transform | Flesch-Kincaid-shaped readability over the lyric text (transform). |
| `music.analyze_rhyme_scheme` | transform | Build a rhyme scheme (A/B/C labels) over the lyric lines (transform). |
| `music.audio_release_gate` | effect | Composite audio-release gate — every track QC-passed (effect). |
| `music.capture_claim` | effect | Record a ResearchClaim node SERVES the intent (effect). |
| `music.capture_idea` | effect | Capture a creative idea (effect) — record an Idea node, persist via StateDriver. |
| `music.catalogue_gate` | effect | Catalogue-synced gate — streaming URLs + tweets ready (effect). |
| `music.catalogue_status` | transform | Read track statuses from the catalogue DB via the DBDriver (transform). |
| `music.check_cross_track_repetition` | transform | Flag lyric lines repeated across multiple album tracks (transform). |
| `music.check_explicit_content` | transform | Classify lyrics as clean / suggestive / explicit (transform). |
| `music.check_homographs` | transform | Flag words with multiple legitimate pronunciations (transform). |
| `music.check_name_exposure` | transform | Scan text for forbidden roster names (driver-free, deterministic) (transform). |
| `music.check_pronunciation` | transform | Flag words requiring forced pronunciation per the bundled guide (transform). |
| `music.check_streaming_lyrics` | transform | Check the lyric body for platform-incompatible markup (transform). |
| `music.check_voice_tells` | transform | AI-tell rule-based detector (advisory only — no gate impact) (transform). |
| `music.concept_gate` | effect | Pre-generation gate: concept exists for the album (effect). |
| `music.conceptualize` | act | Render an album-concept document for a known album ``type`` (act). |
| `music.count_syllables` | transform | Count syllables in a word — deterministic, driver-free text math. |
| `music.create_album` | effect | Create an album root + render the canonical templates (effect). |
| `music.create_songbook` | effect | LilyPond → PDF songbook render via AudioDriver (effect). |
| `music.create_track` | effect | Create a track in an album, rendered from the bitwize ``track`` template (effect). |
| `music.db_create_tweet` | effect | Insert a tweet row via the DBDriver, producing a tweet-record artefact (effect). |
| `music.db_delete_tweet` | effect | Delete a tweet row via the DBDriver (effect). |
| `music.db_get_tweet_stats` | transform | Aggregate counts of tweets by status via DBDriver (transform). |
| `music.db_list_tweets` | transform | List tweets via the DBDriver, filtered by album + status (transform). |
| `music.db_search_tweets` | transform | Substring search across tweet bodies via DBDriver (transform). |
| `music.db_sync_album` | effect | Idempotent sync of an album's tweets — replaces existing (effect). |
| `music.db_update_tweet` | effect | Update tweet row fields via the DBDriver (effect). |
| `music.diagnose` | transform | Composite driver-free health probe (transform). |
| `music.dispatch_research` | effect | Fan out to N specialists via agency.research (effect). |
| `music.document_hunt` | effect | Dispatch a document-hunter specialist via agency.research (effect). |
| `music.explicit_gate` | effect | Computed explicit-content gate (effect). |
| `music.extract_distinctive_phrases` | transform | Return novel tri-grams (not in corpus) from the lyrics (transform). |
| `music.extract_links` | transform | Extract URLs from text via simple regex (transform). |
| `music.extract_section` | transform | Extract the body under a ``[<label>]`` section tag (transform). |
| `music.find_album` | transform | Find albums by slug / fuzzy match via the StateDriver (transform). |
| `music.fix_dynamic_track` | effect | Dynamic range fixer — applies compression/expansion (effect). |
| `music.format_clipboard` | transform | Format text for clipboard paste into Suno / other generation services (transform). |
| `music.generate_promo_videos` | effect | Render a vertical promo video via AudioDriver (effect). |
| `music.get_config` | transform | Read the music capability's loaded config (transform). |
| `music.get_promo_content` | transform | Read promo content (drafts + scheduled tweets) via DBDriver (transform). |
| `music.get_promo_status` | transform | Per-album promo state via StateDriver + DBDriver (transform). |
| `music.get_reference` | transform | Read a bundled reference / data file by slug (transform). |
| `music.get_streaming_urls` | transform | Read recorded streaming URLs for an album via StateDriver (transform). |
| `music.human_signoff` | effect | Record terminal human approval for the album's research (effect). |
| `music.list_claims` | transform | List ResearchClaim nodes (transform). |
| `music.list_ideas` | transform | List captured ideas via the StateDriver (transform) — filter by status. |
| `music.list_tracks` | transform | List tracks for an album via the StateDriver (transform). |
| `music.load_override` | transform | Load a user-authored override file from the configured overrides dir (transform). |
| `music.lyric_report` | act | Analyze a lyric sheet's syllable load per line via the TextDriver (act). |
| `music.lyrics_pregen_gate` | effect | Composite lyrics pre-generation gate — chains the lyric gates (effect). |
| `music.master_album` | effect | Master an audio file to a target loudness via the AudioDriver (effect). |
| `music.master_audio` | effect | Master a single track via AudioDriver, producing a mastering-report (effect). |
| `music.master_with_reference` | effect | Master `path` to match `reference` album loudness (effect). |
| `music.measure_album_signature` | transform | Spectral signatures for an album's tracks via AudioDriver (transform). |
| `music.measure_gate` | effect | Computed measure gate — composes loudness probe + range check (effect). |
| `music.mono_fold_check` | transform | Phase-cancellation check via AudioDriver (transform). |
| `music.music_health` | transform | Self-check the music capability (transform, driver-free) — report which Driver seams are wired. |
| `music.name_exposure_gate` | effect | Computed name-exposure gate — no forbidden roster names in lyrics (effect). |
| `music.pending_verifications` | transform | Aggregate count of pending claims (transform). |
| `music.polish_album` | effect | Album-wide polish pass — applies polish to every track (effect). |
| `music.polish_and_master_album` | effect | Run the combined polish + master pipeline, producing a mastering-report (effect). |
| `music.polish_audio` | effect | Per-track polish pass via AudioDriver (effect). |
| `music.pregen_check` | effect | Computed `pre-generation` gate — machine-checkable predicate (Spec 094). |
| `music.promo_copy` | act | Draft promotional copy for an album (act, produces a ``promo-copy`` artefact). |
| `music.promo_gate` | effect | Promo-drafted gate — at least 1 promo asset exists (effect). |
| `music.promo_review` | transform | Rule-based scoring of promo copy quality (transform). |
| `music.promo_review_gate` | effect | Computed promo-review gate (effect) — composes ``promo_review`` scoring. |
| `music.promote_idea` | effect | Promote an Idea to an Album, recording the Album + PROMOTED_TO edge (effect). |
| `music.pronunciation_gate` | effect | Computed pronunciation gate — composes pronunciation + homograph (effect). |
| `music.prosody_gate` | effect | Computed prosody gate — composes rhyme + syllable checks (effect). |
| `music.publish_asset` | effect | Publish an album asset to object storage via the CloudDriver (effect). |
| `music.publish_sheet_music` | effect | Publish a sheet-music PDF to object storage (effect). |
| `music.qc_audio` | transform | 7-point QC checklist via AudioDriver (transform). |
| `music.qc_gate` | effect | Computed QC gate — composes 7-point QC checklist (effect). |
| `music.r2_delete` | effect | Retract a published asset from object storage (effect). |
| `music.r2_list` | transform | List published assets by key prefix (transform). |
| `music.release_check` | effect | Computed `release-qa` gate: every track mastered (read via the DBDriver). |
| `music.release_package` | act | Record a release package — gathers all release artefact paths (act). |
| `music.rename_album` | effect | Rename an album, mirroring paths via the StateDriver (effect). |
| `music.rename_track` | effect | Rename a track within an album, mirroring paths via the StateDriver (effect). |
| `music.render_codec_preview` | effect | Render a streaming-codec preview via AudioDriver (effect). |
| `music.repetition_gate` | effect | Computed cross-track repetition gate (effect). |
| `music.research_scope` | act | Define a research question + plan specialist domains (act). |
| `music.reset_mastering` | effect | Revert all master/polish state for an album (effect). |
| `music.resume_session` | transform | Restore the last-album context via the StateDriver (transform). |
| `music.scan_artist_names` | transform | Scan for accidental artist-name drops against the blocklist (transform). |
| `music.set_album_status` | effect | Persist an album's production status via the StateDriver (effect). |
| `music.set_track_status` | effect | Persist a track's production status via the StateDriver (effect). |
| `music.transcribe_sheet` | act | Transcribe audio to sheet music via AudioDriver, producing a sheet-music artefact (act). |
| `music.tweet_schedule_gate` | effect | Computed tweet-schedule gate (effect) — composes 3 checks. |
| `music.update_streaming_url` | effect | Persist a verified streaming URL via StateDriver (effect). |
| `music.upload_promo_video` | effect | Upload a promo video to object storage (effect). |
| `music.validate_album` | transform | Validate album file presence + mirror-path consistency via StateDriver (transform). |
| `music.validate_section_structure` | transform | Validate section tag well-formedness (Title Case in brackets) (transform). |
| `music.validate_sections` | transform | Validate lyric section structure across an album (transform). |
| `music.verify_gate` | effect | Computed verification gate — composes pending_verifications (effect). |
| `music.verify_sources` | effect | Cross-check pending claims (effect). |
| `music.verify_streaming` | transform | Verify an album's streaming links are live via the CloudDriver (transform). |

## `novel`  (capability)

Use when authoring a novel — turning a premise into a structured manuscript through gated concept → chapters → report → render.

**Walkable skills:** `character-architect`, `developmental-editor`, `line-editor`, `novel-concept`, `publish-prep`, `scene-bridge-auditor`, `scene-writer`, `storyform-build`, `world-bible-architect`

| verb | role | summary |
|---|---|---|
| `novel.analyze_readability` | transform | Flesch Reading Ease for prose (transform, driver-free). |
| `novel.archive_codex_entry` | effect | Flag a CodexEntry as archived (effect, soft-delete). |
| `novel.audit_novel_provenance` | transform | Aggregate the provenance graph census for the serving intent (transform, xcap to analyze). |
| `novel.beta_ready_gate` | effect | Composite gate: all chapters drafted+ (effect). |
| `novel.capture_claim` | effect | Record a NovelClaim node SERVING the intent (effect). |
| `novel.capture_idea` | effect | Record an Idea node SERVING the intent (effect). |
| `novel.chapter_report` | transform | Read-only aggregate over the novel's chapters (transform). |
| `novel.chapter_report_full` | act | Full editorial dashboard for one chapter (act). |
| `novel.check_approach_concern` | transform | Mostly-decidable check (row 8): approach ↔ class compatibility (WARN-severity). |
| `novel.check_content_warnings` | transform | Content-warning category scanner (transform, driver-free). |
| `novel.check_continuity` | transform | Cross-chapter proper-noun continuity check (transform). |
| `novel.check_crucial_element_placement` | transform | Decidable check (row 6): storyform.crucial_element_id == mc.problem_id. |
| `novel.check_dialogue_attribution` | transform | Dialogue-tag check — plain ('said') vs flowery (transform). |
| `novel.check_dynamic_pair_reciprocity` | transform | Decidable check (row 1): mc.dynamic and os.dynamic must differ. |
| `novel.check_filter_words` | transform | Filter-word density check (transform, show-don't-tell). |
| `novel.check_ktad_coverage` | transform | Decidable check (row 2): concern_id == signposts[0] (K-position). |
| `novel.check_mental_sex_problem_solving` | transform | Decidable check (row 9): mental_sex ↔ class compatibility. |
| `novel.check_pov_consistency` | transform | Per-chapter POV uniformity check across scenes (transform). |
| `novel.check_quad_completeness` | transform | Decidable check (row 3): mc problem and solution are paired. |
| `novel.check_resolve_outcome_judgment` | transform | Decidable check (row 7): resolve/outcome/judgment triple is legal. |
| `novel.check_sensitivity` | transform | Sensitivity-topic advisory scan (transform, WARN-severity). |
| `novel.check_show_dont_tell` | transform | Telling-verb scan — interior-monologue tells (transform). |
| `novel.check_signpost_permutation` | transform | Decidable check (row 10): signposts in canonical order per class. |
| `novel.check_slot_fill` | transform | Decidable check (row 4): no null required slots (transform). |
| `novel.check_storybeat_moment_refs` | transform | Decidable check (row 11): every moment.storybeat_ref resolves (transform). |
| `novel.check_throughline_partition` | transform | Decidable check (row 5): 4 throughlines / 4 distinct Classes (transform). |
| `novel.check_voice_consistency` | transform | Per-chapter voice-signature outlier check (transform). |
| `novel.conceptualize` | act | Render a novel-concept document, the first verb of the MVN flow (act). |
| `novel.copy_gate` | effect | Composite gate: surface-level editorial readiness (effect). |
| `novel.count_words` | transform | Word + char counter (transform, driver-free). |
| `novel.create_chapter` | effect | Record a Chapter graph node + CHAPTER_OF the parent Novel (effect). |
| `novel.create_codex_entry` | effect | Mint a CodexEntry + CODEX_OF edge to the Novel (effect). |
| `novel.create_culture` | effect | Mint a Culture under a World + PART_OF_WORLD edge (effect). |
| `novel.create_language` | effect | Mint a Language under a World + PART_OF_WORLD edge (effect). |
| `novel.create_magic_system` | effect | Mint a MagicSystem under a World + PART_OF_WORLD edge (effect). |
| `novel.create_novel` | effect | Record a Novel node SERVING the intent, materialising disk on production. |
| `novel.create_religion` | effect | Mint a Religion under a World + PART_OF_WORLD edge (effect). |
| `novel.create_scene` | effect | Record a Scene node + SCENE_OF the parent Chapter (effect). |
| `novel.create_storyform` | effect | Mint the Storyform node for a novel + STORYFORM_OF edge (effect). |
| `novel.create_world` | effect | Mint a World node + SERVES intent (effect). |
| `novel.create_world_axiom` | effect | Encode a WorldAxiom (rule) under a World (effect). |
| `novel.developmental_gate` | effect | Composite gate: structure-level editorial readiness (effect). |
| `novel.dispatch_novel_research` | effect | Mint a research lead + record NovelClaim (delegates to research cap). |
| `novel.export_docx` | effect | Render manuscript + write docx via FormatDriver (effect). |
| `novel.export_epub` | effect | Render manuscript + write epub via FormatDriver (effect). |
| `novel.export_pdf` | effect | Render manuscript + write PDF via FormatDriver (effect). |
| `novel.fetch_scene_body` | transform | Spec 220 Slice 1.5 — public retrieval for a scene-body Artefact. |
| `novel.find_axiom_contradictions` | effect | Decidable axiom-contradiction scan + emit CONTRADICTS edges (effect). |
| `novel.find_novel` | transform | Substring-match novel titles (transform, driver-free). |
| `novel.flag_anachronistic_reference` | transform | Check if the character knows the fact yet (transform). |
| `novel.generate_scene_body` | act | Spec 220 Slice 1 — wet scene-body generation via Spec 147 + Spec 279. |
| `novel.get_storyform` | transform | Return a novel's Storyform node + parsed NCP body (transform). |
| `novel.integrate_scene_body` | effect | Spec 130 phase 5 — write the generated body back to the Scene (effect). |
| `novel.line_gate` | effect | Composite gate: prose-level editorial readiness (effect). |
| `novel.link_character_to_world` | effect | Add a typed edge from Character → World child (effect). |
| `novel.list_chapters` | transform | List a novel's chapters ordered by number (transform). |
| `novel.list_claims` | transform | List captured claims with an optional verified-status filter (transform). |
| `novel.list_codex_entries` | transform | List CodexEntries for a novel, optionally filtered by kind (transform). |
| `novel.list_ideas` | transform | List captured ideas with an optional status filter (transform). |
| `novel.list_reveals_in` | transform | List events this scene discloses (transform). |
| `novel.list_story_events_up_to` | transform | Story-time slice: events with ``when_story`` ≤ this scene's anchor (transform). |
| `novel.list_world` | transform | Render a tree of a World's contents (transform). |
| `novel.manuscript_coherence_check` | transform | Chapter-sequence contiguity check (transform, driver-free). |
| `novel.mark_narrative_beat` | effect | Mint a NarrativeBeat + optional PRECEDES edge from a predecessor (effect). |
| `novel.match_codex_entries` | transform | Scan ``text`` for any registered codex trigger and return matches (transform). |
| `novel.narrative_order` | transform | Topo-sort over PRECEDES for the canonical narrative reading order (transform). |
| `novel.novel_coherence_check` | effect | Composite gate (Spec 120): runs all 11 storyform checks with chaining. |
| `novel.novel_progress` | transform | Aggregate progress (word-count + per-status counts) for a novel (transform). |
| `novel.pending_verifications` | transform | Aggregate pending claims by domain (transform). |
| `novel.pov_options` | transform | Structured POV choices for an assumption-gate (transform). |
| `novel.pre_draft_gate` | effect | Composite gate: storyform + research + chapters present (effect). |
| `novel.promote_idea` | effect | Transition an Idea to a Novel, recording the PROMOTED_TO edge (effect). |
| `novel.publication_gate` | effect | Terminal composite: publish_ready + ≥1 export + front-matter declared (effect). |
| `novel.publish_ready_gate` | effect | Composite gate: contiguous chapters + status ≥ querying (effect). |
| `novel.query_ready_gate` | effect | Composite gate: status ≥ beta + content-clean (effect). |
| `novel.record_character_learns` | effect | Mint a KnownFact + KNOWS + LEARNED_IN edges (effect). |
| `novel.record_story_event` | effect | Mint a StoryTimeEvent + optional HAPPENS_AT edge from a scene (effect). |
| `novel.record_storyform_decision` | effect | Record a contested storyform decision (effect, xcap to dogfood). |
| `novel.rename_novel` | effect | Update a Novel's title (effect, graph-only). |
| `novel.render_all` | effect | Re-materialise a novel's full markdown tree from graph ground truth (effect). |
| `novel.render_blurb` | act | Render a back-cover blurb (act, driver-free). |
| `novel.render_chapter_brief` | act | Produce a research-dossier brief tied to a chapter (act, xcap to prompt). |
| `novel.render_manuscript` | act | Concatenate chapters into a manuscript artefact (act). |
| `novel.render_query_letter` | act | Render an agent query letter (act, driver-free). |
| `novel.render_synopsis` | act | Render a synopsis from chapter outline (act, driver-free). |
| `novel.resume_session` | transform | Return the most-recently-created Novel's id + title (transform). |
| `novel.reveal_in_scene` | effect | Add the REVEALED_IN edge (event disclosed by this scene) (effect). |
| `novel.scan_proper_nouns` | transform | Extract proper nouns (Title-Case words, sentence-starter words filtered) (transform). |
| `novel.set_chapter_status` | effect | Flip a Chapter's enum-checked lifecycle status (effect). |
| `novel.set_novel_status` | effect | Flip a Novel's enum-checked lifecycle status (effect). |
| `novel.storyform_critical_pass` | act | Critical-thinking pass over the storyform (act, xcap to thinking). |
| `novel.update_codex_entry` | effect | Edit a CodexEntry's body / triggers / name (effect). |
| `novel.validate_appreciations` | transform | Row 12 hybrid: NCP appreciations ∈ canonical 463 (transform). |
| `novel.validate_narrative_functions` | transform | Row 13 hybrid: NCP narrative_functions ∈ canonical 144 (transform). |
| `novel.what_does_X_know_as_of` | transform | List facts the character has learned ≤ the scene's narrative position (transform). |

## `panel`  (memory)

Use when a strategy / plan / business decision needs stress-testing through

**Walkable skills:** `strategic-analysis`

| verb | role | summary |
|---|---|---|
| `panel.convene` | effect | Convene the panel on a ``subject`` — emit a mode-appropriate |
| `panel.experts` | act | The 9-expert roster — name · framework · lens · signature question. |

## `persona`  (lifecycle)

Use when a task needs a specific engineering specialist's lens — architecture,

**Walkable skills:** `specialist-dispatch`

| verb | role | summary |
|---|---|---|
| `persona.list` | act | The specialist-persona roster — name · focus · approach. |
| `persona.recommend` | act | Recommend the specialist persona(s) best matched to a ``task`` by |
| `persona.summon` | effect | Summon a specialist — compose a dispatch brief + record provenance |

## `plugin`  (capability)

Use when building or extending a Claude Code plugin — scaffolding a manifest, authoring a skill or command, or linting a capability against the authoring doctrine.

**Walkable skills:** `plugin-dev`, `skill-creation`

| verb | role | summary |
|---|---|---|
| `plugin.author_command` | act | Render a slash-command markdown stub. |
| `plugin.author_skill` | act | Render a CSO-compliant SKILL.md. |
| `plugin.help` | transform | Map the engine's capabilities (macroskills) to their verbs — via ctx.registry. |
| `plugin.lint_capability` | transform | Lint a capability against Hint #7 structural + role-tag + render-slice rules. |
| `plugin.lint_explain` | transform | Return the rework recipe for a lint rule kind (Spec 074) — so you learn HOW to fix it. |
| `plugin.lint_skill` | transform | Lint a skill description against the CSO + length rules. |
| `plugin.marketplace_entry` | act | Render a marketplace.json entry. |
| `plugin.publish_skill` | effect | Publish a capability's Agent Skill to the Anthropic Skills API (Spec 083). |
| `plugin.scaffold` | act | Render the plugin scaffold (plugin.json + .mcp.json). |
| `plugin.step_doc` | act | Render a step-doc markdown block (audit trail entry). |

## `prompt`  (capability)

Use when authoring a research dossier, engineering a token-budgeted prompt,

**Walkable skills:** `dossier-author`, `prompt-engineering-pass`

| verb | role | summary |
|---|---|---|
| `prompt.assemble_scene_brief` | act | Compose a Novelcrafter-style scene brief from graph state (act). |
| `prompt.audit` | effect | General-case reader-test simulation for any prompt (effect). |
| `prompt.audit_gate` | effect | Computed audit gate — passes iff clarity_score ≥ min_score (effect). |
| `prompt.brief_audit` | effect | Rule-based clarity audit of a ResearchBrief (effect). |
| `prompt.brief_finalize` | effect | Finalize a ResearchBrief — flips its status (effect). |
| `prompt.brief_render` | act | Render a ResearchBrief body from the dossier-skeleton template (act). |
| `prompt.catalog_list` | transform | List bundled CatalogModule entries optionally filtered by category (transform). |
| `prompt.engineer` | act | Render a PromptInstance inside a token budget (act). |
| `prompt.evaluate` | effect | Goal-aware multi-dimension evaluation of a prompt body (effect). |
| `prompt.fragment` | transform | Look up a single Dramatica prompt fragment (transform). |
| `prompt.fragments_for` | transform | Compose multiple fragments for a storyform scope (transform). |
| `prompt.framework` | transform | Look up a single prompt-engineering framework by slug (transform). |
| `prompt.frameworks_for` | transform | Budget-aware candidate list for a known intent category (transform). |
| `prompt.intent_capture` | act | Record a structured ResearchIntent SERVING the intent (act). |
| `prompt.register_fragment` | effect | Write a fragment to the project overlay (effect; runtime-extensible). |
| `prompt.register_framework` | effect | Write a custom framework to the project overlay (effect; extensible). |
| `prompt.render` | act | Fill a framework's template with ``fields`` → a PromptInstance (act). |
| `prompt.route_framework` | effect | Route a free-text ``draft`` to the ONE right framework (effect). |
| `prompt.token_budget_gate` | effect | Computed token-budget gate — passes iff approx_tokens ≤ max_tokens (effect). |

## `recommend`  (capability)

Use when you have a goal in words and want the right agency verb to reach for,

**Walkable skills:** `capability-routing`

| verb | role | summary |
|---|---|---|
| `recommend.route` | effect | Recommend the capability + verb best matched to a free-text |

## `reflect`  (memory)

Use when durable, scope-tagged memory must cross sessions — recording an insight, or recalling prior observations by scope or semantic similarity.

**Walkable skills:** `reflect-usage`

| verb | role | summary |
|---|---|---|
| `reflect.batch_note` | act | Bulk version of ``note``: one Reflection node per text. |
| `reflect.note` | act | Write a scope-tagged insight node, edged OBSERVED_DURING + SERVES the intent. |
| `reflect.recall` | transform | Retrieve reflections, newest first, optionally filtered by scope. |
| `reflect.recall_semantic` | transform | Semantic top-k recall over Reflection nodes (backend-injectable). |
| `reflect.search` | transform | Keyword search over reflection text (deterministic substring match). |
| `reflect.synthesize_session` | act | Produce a session-reflection artefact at session close (act). |

## `research`  (capability)

Use when an open question needs cited evidence from multiple sources — driving a research question through a lead, fan-out specialists, and an adversarial verifier.

**Walkable skills:** `deep-research`

| verb | role | summary |
|---|---|---|
| `research.ingest_gdoc` | transform | Compose a subagent dispatch contract that ingests a Google Doc to disk. |
| `research.lead` | act | Scope a research question and plan specialists, minting a Research node. |
| `research.record_ingested_source` | effect | Record an ``ingested-source`` Artefact (SERVES intent + PRODUCES edge). |
| `research.specialist` | act | Run one bounded sub-search, recording Citations under the research_id. |
| `research.verify` | act | Adversarially check citations, emitting a Verification node. |

## `select`  (lifecycle)

Use when an operation could be done several ways and the right approach depends

**Walkable skills:** `approach-routing`

| verb | role | summary |
|---|---|---|
| `select.archetypes` | act | The approach archetypes + their trade-offs. |
| `select.route` | effect | Route an ``operation`` to an approach archetype by decidable |

## `shell`  (capability)

Use when running a host CLI command whose output should be token-filtered and recorded — an allowlisted command, a reusable template, or a pure output filter.

**Walkable skills:** `shell-usage`

| verb | role | summary |
|---|---|---|
| `shell.define` | act | Define a named shell template (command + output filter + doc) in the graph. |
| `shell.filter` | transform | Filter text to a token-bounded slice — pure, no execution (hook-ready). |
| `shell.run` | effect | Run an ALLOWLISTED command (or a named template), FILTER its output, record it. |
| `shell.templates` | transform | Discover named query templates — built-in seeds ∪ graph-defined (Spec 075). |

## `skill_generator`  (capability)

Use when a deploy-ready skill should be produced in one call — a complete, CSO-clean SKILL.md generated from a description.

**Walkable skills:** `skill_generator-usage`

| verb | role | summary |
|---|---|---|
| `skill_generator.generate` | act | Author a SKILL.md and lint it against the CSO rules, flagging if not deploy-ready. |

## `skills`  (capability)

Use when discovering which walkable skills exist, reading one skill's phases at a chosen depth, or validating a skill's phase-graph shape — before walking, emitting, or authoring a skill.

**Walkable skills:** `skills-triage`

| verb | role | summary |
|---|---|---|
| `skills.find` | transform | Enumerate the walkable skills across all capabilities, with light filters. |
| `skills.index` | effect | Promote walkable skills into the graph as Skill + Phase nodes (Spec 026). |
| `skills.lint` | transform | Validate a skill's phase-graph shape — the structural contract a walk relies on. |
| `skills.rank` | transform | Rank walkable skills against a free-text query (Spec 161 Slice 1). |
| `skills.render` | transform | Render one skill to markdown at a chosen depth (progressive disclosure). |

## `subagent`  (lifecycle)

Use when a unit of work should be composed as subagent-driven development — isolating a task to a dispatched subagent that returns a verified result.

**Walkable skills:** `subagent-driven-development`

| verb | role | summary |
|---|---|---|
| `subagent.develop` | effect | Dispatch a worker child and gate it through spec-review then quality-review (effect). |

## `symbols`  (memory)

Use when output must be compact without losing meaning — large-scale results,

**Walkable skills:** `symbols-usage`

| verb | role | summary |
|---|---|---|
| `symbols.compress` | transform | Substitute known phrases with symbols — dense, decidable (Spec 300). |
| `symbols.expand` | transform | Expand symbols back into prose (the inverse of ``compress``). |
| `symbols.legend` | transform | The phrase↔symbol legend. |

## `thinking`  (capability)

Use when structured rigor needed before commit; binding decisions need tradeoff + premortem + red-team; an assumption stack needs surfacing.

**Walkable skills:** `critical-thinking-pass`

| verb | role | summary |
|---|---|---|
| `thinking.apply_full_review` | act | Run the 8 founding thinking methods in sequence, producing a thinking-analysis artefact (act). |
| `thinking.assumptions` | transform | Surface + classify implicit assumptions (load-bearing vs not) (transform). |
| `thinking.decompose` | transform | MECE sub-problem decomposition (transform). |
| `thinking.first_principles` | transform | Strip the goal to fundamentals + reconstruct (transform). |
| `thinking.inversion` | transform | Look for what guarantees failure rather than what guarantees success. |
| `thinking.premortem` | transform | Prospective failure analysis (transform). |
| `thinking.red_team` | transform | Adversarial review — adopt an attacker's stance + find failure paths (transform). |
| `thinking.second_order` | transform | Trace consequences N steps downstream (transform). |
| `thinking.socratic` | transform | Five-whys-deeper Socratic questioning (transform). |
| `thinking.steelman` | transform | Build the strongest possible argument against a position (transform). |
| `thinking.tradeoffs` | transform | Multi-criteria option scoring (transform). |

## `toolcalls`  (memory)

Use when reviewing what a session actually did — which tool calls ran, how often,

**Walkable skills:** `toolcalls-usage`

| verb | role | summary |
|---|---|---|
| `toolcalls.export` | effect | Distil the session's tool calls into a durable export — the top calls + |
| `toolcalls.prune` | effect | Clear the ephemeral capture store (after it has been distilled/exported). |
| `toolcalls.recent` | act | The most recent captured tool calls, in FULL (read-only). |
| `toolcalls.stats` | act | Capture counts broken down by phase and tool (read-only). |
| `toolcalls.top` | act | The top captured tool-call shapes by frequency × payload cost (read-only). |

## `workflow`  (lifecycle)

Use when a spec must move through its development stages (draft → open →

**Walkable skills:** `workflow-usage`

| verb | role | summary |
|---|---|---|
| `workflow.board` | transform | BOARD — the graph-native spec board: live SpecLifecycles grouped by |
| `workflow.move_spec` | effect | MOVE_SPEC — advance the spec's Lifecycle to ``to_state`` via |
| `workflow.open_spec` | act | OPEN_SPEC — mint a SpecLifecycle (machine ``spec``, state ``draft``) for |

## `workspace`  (lifecycle)

Use when work should be isolated in a git worktree with a recorded green baseline — a clean, provably-green starting point before risky changes.

**Walkable skills:** `workspace-usage`

| verb | role | summary |
|---|---|---|
| `workspace.baseline` | effect | Run the baseline test command in the workspace and record the green/red result. |
| `workspace.isolate` | effect | Create an isolated git worktree on a fresh branch off `base`, recording the Workspace. |
