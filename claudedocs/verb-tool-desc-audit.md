<!-- agency-generated: scripts/optimize-verb-docs (Spec 306). Advisory candidates — apply by hand. -->
# Verb-description optimization sweep (tool-desc)

Audited **373 verbs** across **28 capabilities**; **50** need work (13%). Rules: `agency/capabilities/prompt/references/tool-desc-authoring.md`.

## Flag histogram

| Flag | Count | What it means |
|------|-------|---------------|
| `long_brief` | 38 |  |
| `missing_inputs` | 11 | no Inputs: section |
| `missing_returns` | 1 |  |
| `no_chain_next` | 1 | no chain_next: |

## Per-capability candidates

Each candidate is the tool-desc skeleton filled from the verb's own docstring; `[TODO]` marks the slot the flag says is missing (fill it, then the flag clears).

### `analyze` — 1/9 verbs need work

<details><summary><code>analyze.run</code> (act) — `long_brief`</summary>

```
BRIEF: Run the requested axes; record an Analysis + per-Finding nodes.

INPUTS: path (str), axes (list[str] — default: all four), lang (str — only 'py' in v1). Returns: ``{analysis_id, totals: {axis: {info, warn, fail}}}`` — compact summary; detail lives in the graph as Analysis → HAS_FINDING → Finding nodes. chain_next: ``analyze.improve(analysis_id)`` or ``analyze.cleanup(path)``.

RETURNS: ``{analysis_id, totals: {axis: {info, warn, fail}}}`` — compact summary; detail lives in the graph as Analysis → HAS_FINDING → Finding nodes. chain_next: ``analyze.improve(analysis_id)`` or ``analyze.cleanup(path)``.

CHAIN_NEXT: ``analyze.improve(analysis_id)`` or ``analyze.cleanup(path)``.
```
</details>

### `branch` — 1/3 verbs need work

<details><summary><code>branch.finish</code> (effect) — `long_brief`</summary>

```
BRIEF: Finish the branch by the chosen action (merge/pr/keep/discard); record the outcome.

INPUTS: branch (str), action (one of merge/pr/keep/discard), base (str). Returns: ``{outcome, branch, action, ok, detail}`` (wire shape); ``{error, actions}`` on unknown action. chain_next: terminal — outcome node carries the audit trail.

RETURNS: ``{outcome, branch, action, ok, detail}`` (wire shape); ``{error, actions}`` on unknown action. chain_next: terminal — outcome node carries the audit trail.

CHAIN_NEXT: terminal — outcome node carries the audit trail.
```
</details>

### `develop` — 3/16 verbs need work

<details><summary><code>develop.draft_plan</code> (act) — `long_brief`</summary>

```
BRIEF: Author a bite-sized plan as graph provenance (Spec 287; rule 2).

INPUTS: title, steps (JSON list or newlines). Returns: ``{plan_id, step_ids, count}``. chain_next: walk ``plan-execute``, or sign off then ``record_step_outcome`` per step + ``plan_status`` to roll up.

RETURNS: ``{plan_id, step_ids, count}``. chain_next: walk ``plan-execute``, or sign off then ``record_step_outcome`` per step + ``plan_status`` to roll up.

CHAIN_NEXT: walk ``plan-execute``, or sign off then ``record_step_outcome`` per step + ``plan_status`` to roll up.
```
</details>

<details><summary><code>develop.session_init</code> (act) — `long_brief`</summary>

```
BRIEF: Mint a SessionLifecycle SERVING the intent; detect mode; suggest first verb.

INPUTS: purpose, deliverable, acceptance (optional intent triple — if empty, uses the serving intent's existing fields), mode_hint (override the auto-detect). Returns: ``{session_lifecycle_id, intent_id, mode, suggested_first_verb}``. chain_next: ``develop.session_check`` to read state OR ``develop.mode_select`` to switch.

RETURNS: ``{session_lifecycle_id, intent_id, mode, suggested_first_verb}``. chain_next: ``develop.session_check`` to read state OR ``develop.mode_select`` to switch.

CHAIN_NEXT: ``develop.session_check`` to read state OR ``develop.mode_select`` to switch.
```
</details>

<details><summary><code>develop.skill_walk</code> (act) — `missing_returns`</summary>

```
BRIEF: Walk a registered skill to the first hard gate in ONE call (the atomic walker).

INPUTS: name (registered skill, e.g. 'tdd'), inputs (map of produce→value), resume_from (a prior skill_id to resume; "" starts fresh). Returns (the status contract): - ``{status: "completed", skill_id, outputs}`` - ``{status: "input-required", phase, blocked_on, resume_with, skill_id, partial_outputs}`` - ``{status: "failed", phase, error, skill_id, completed_phases}`` chain_next: on input-required, re-call with resume_from + resume_with keys.

RETURNS: [TODO]

CHAIN_NEXT: on input-required, re-call with resume_from + resume_with keys.
```
</details>

### `document` — 4/12 verbs need work

<details><summary><code>document.explain</code> (act) — `long_brief`</summary>

```
BRIEF: Deterministic code → markdown explanation; emits a Reflection.

INPUTS: target (str — file path | module | module.symbol), depth (str — brief | standard | deep). Returns: ``{reflection_id, content, tokens}``. chain_next: caller renders or stores the content.

RETURNS: ``{reflection_id, content, tokens}``. chain_next: caller renders or stores the content.

CHAIN_NEXT: caller renders or stores the content.
```
</details>

<details><summary><code>document.index_repo</code> (effect) — `long_brief`</summary>

```
BRIEF: 94%-reduction repo briefing — deterministic; ≤ max_tokens.

INPUTS: path (str), apply (bool — write PROJECT_INDEX.md), max_tokens (int — budget; default 3000). Returns: ``{index_id, content, tokens, files_scanned, writeup}``. chain_next: caller publishes via ``apply=True`` after review.

RETURNS: ``{index_id, content, tokens, files_scanned, writeup}``. chain_next: caller publishes via ``apply=True`` after review.

CHAIN_NEXT: caller publishes via ``apply=True`` after review.
```
</details>

<details><summary><code>document.ingest</code> (effect) — `long_brief`</summary>

```
BRIEF: Round-trip a markdown file INTO the graph (file → graph; Spec 292).

INPUTS: path (str — the .md file), audit (bool — prompt-audit the body), template (str — generator binding), schema (str — schema binding). Returns: ``{document_id, revision_id, action, content_sha, anchored, clarity_score, path}``. action ∈ created | revised | unchanged. chain_next: ``document.revisions`` to read the keep-both history.

RETURNS: ``{document_id, revision_id, action, content_sha, anchored, clarity_score, path}``. action ∈ created | revised | unchanged. chain_next: ``document.revisions`` to read the keep-both history.

CHAIN_NEXT: ``document.revisions`` to read the keep-both history.
```
</details>

<details><summary><code>document.render</code> (transform) — `long_brief`</summary>

```
BRIEF: Project graph state to markdown; deterministic.

INPUTS: scope (str — one of install-artefacts | reflections | provenance | capability-catalogue), for_intent_id (str — required for provenance, optional filter for reflections; named `for_intent_id` rather than `intent_id` because the substrate already injects intent_id for SERVES discipline), format (str — 'markdown' in v1). Returns: ``{content, tokens, node_count, scope}``. chain_next: caller writes to disk — and a disk edit round-trips back via ``document.ingest`` (graph↔file are peers now; Spec 292).

RETURNS: ``{content, tokens, node_count, scope}``. chain_next: caller writes to disk — and a disk edit round-trips back via ``document.ingest`` (graph↔file are peers now; Spec 292).

CHAIN_NEXT: caller writes to disk — and a disk edit round-trips back via ``document.ingest`` (graph↔file are peers now; Spec 292).
```
</details>

### `dogfood` — 2/11 verbs need work

<details><summary><code>dogfood.apply_amendment</code> (effect) — `long_brief`, `no_chain_next`</summary>

```
BRIEF: Render a ProposalPayload as a unified diff; provenance Artefact.

INPUTS: payload (dict — ProposalPayload schema; see Plan/150), dry_run (bool — default True; False requires ``confirm_token`` to match the payload id-hash), confirm_token (str — opt-in live-write gate). Returns: ``{diff, artefact_id, written_path?}``. Failure modes: ``AMENDMENT_BAD_SPEC`` (no such spec dir), ``AMENDMENT_NO_SOURCE`` (citations empty), ``AMENDMENT_VAGUE`` (rationale < 40 chars), ``AMENDMENT_UNCONFIRMED`` (live write requested, confirm_token does not match the payload id-hash).

RETURNS: ``{diff, artefact_id, written_path?}``. Failure modes: ``AMENDMENT_BAD_SPEC`` (no such spec dir), ``AMENDMENT_NO_SOURCE`` (citations empty), ``AMENDMENT_VAGUE`` (rationale < 40 chars), ``AMENDMENT_UNCONFIRMED`` (live write requested, confirm_token does not match the payload id-hash).

CHAIN_NEXT: [TODO]
```
</details>

<details><summary><code>dogfood.collect</code> (transform) — `long_brief`</summary>

```
BRIEF: Walk ``plan_dir`` for ``DOGFOOD-NOTES.md`` files; extract observations.

INPUTS: plan_dir (str — root dir of plans; default ``Plan``). Returns: ``{observations: [{plan, kind, index, title, text}], texts: [str], count, plans: [str], warnings: [str]}``. chain_next: ``reflect.batch_note(scope='observation', texts=)`` to seed the graph from one-shot migration of legacy files. Deprecated for ongoing use — prefer ``dogfood.note`` (graph- native authoring) + ``dogfood.render`` (markdown projection on demand). Errors (missing dir, unreadable file) degrade into the ``warnings`` list rather than raising.

RETURNS: ``{observations: [{plan, kind, index, title, text}], texts: [str], count, plans: [str], warnings: [str]}``. chain_next: ``reflect.batch_note(scope='observation', texts=)`` to seed the graph from one-shot migration of legacy files. Deprecated for ongoing use — prefer ``dogfood.note`` (graph- native authoring) + ``dogfood.render`` (markdown projection on demand). Errors (missing dir, unreadable file) degrade into the ``warnings`` list rather than raising.

CHAIN_NEXT: ``reflect.batch_note(scope='observation', texts=)`` to seed the graph from one-shot migration of legacy files. Deprecated for ongoing use — prefer ``dogfood.note`` (graph- native authoring) + ``dogfood.render`` (markdown projection on demand). Errors (missing dir, unreadable file) degrade into the ``warnings`` list rather than raising.
```
</details>

### `jules` — 1/22 verbs need work

<details><summary><code>jules.list</code> (transform) — `long_brief`</summary>

```
BRIEF: Enumerate sessions (trimmed to id/state/title/url; one page — walk via token).

INPUTS: page_size (int), page_token (str — empty = first page). Returns: ``{sessions: [{id, state, title, url}], next_page_token}``. chain_next: re-call with returned ``next_page_token`` to walk older pages.

RETURNS: ``{sessions: [{id, state, title, url}], next_page_token}``. chain_next: re-call with returned ``next_page_token`` to walk older pages.

CHAIN_NEXT: re-call with returned ``next_page_token`` to walk older pages.
```
</details>

### `manage` — 5/10 verbs need work

<details><summary><code>manage.artefacts</code> (act) — `missing_inputs`</summary>

```
BRIEF: ARTEFACTS produced under an intent + their source invocations

INPUTS: [TODO]

RETURNS: ``{intent_id, count, artefacts: [props]}``. chain_next: manage.read(id) for one artefact's full state.

CHAIN_NEXT: manage.read(id) for one artefact's full state.
```
</details>

<details><summary><code>manage.create</code> (effect) — `long_brief`</summary>

```
BRIEF: CREATE a node of any ontology ``label``; SERVES the intent (Spec 293).

INPUTS: label (str — an ontology node label), props (dict|json-str — the node's properties; validated against the ontology). Returns: ``{id, label}`` or ``{error}`` on an ontology violation. chain_next: manage.read(id) to confirm; manage.update to mutate.

RETURNS: ``{id, label}`` or ``{error}`` on an ontology violation. chain_next: manage.read(id) to confirm; manage.update to mutate.

CHAIN_NEXT: manage.read(id) to confirm; manage.update to mutate.
```
</details>

<details><summary><code>manage.open_intents</code> (act) — `missing_inputs`</summary>

```
BRIEF: OPEN-INTENTS — live intents + acceptance + SERVES subtree size,

INPUTS: [TODO]

RETURNS: ``{count, intents: [{id, purpose, acceptance, status, serves_count}]}``. chain_next: manage.timeline(intent_id) for an intent's event order.

CHAIN_NEXT: manage.timeline(intent_id) for an intent's event order.
```
</details>

<details><summary><code>manage.state</code> (act) — `missing_inputs`</summary>

```
BRIEF: STATE rollup — the "where are we" dashboard (Spec 290, on manage).

INPUTS: [TODO]

RETURNS: ``{intents, reflections, artefacts, lifecycles_by_state, …}``. chain_next: manage.open_intents / manage.timeline to drill in.

CHAIN_NEXT: manage.open_intents / manage.timeline to drill in.
```
</details>

<details><summary><code>manage.timeline</code> (act) — `missing_inputs`</summary>

```
BRIEF: TIMELINE — the ordered Event + Invocation history for an intent

INPUTS: [TODO]

RETURNS: ``{intent_id, count, timeline: [{kind, name, at}]}`` ordered by valid-time. chain_next: manage.artefacts(intent_id) for what it produced.

CHAIN_NEXT: manage.artefacts(intent_id) for what it produced.
```
</details>

### `mode` — 2/3 verbs need work

<details><summary><code>mode.detect</code> (act) — `missing_inputs`</summary>

```
BRIEF: Rank the behavioral modes by decidable trigger overlap with

INPUTS: [TODO]

RETURNS: ``{matches: [{mode, score}], top}`` (``top`` empty if none). chain_next: mode.activate(mode=top, context=...).

CHAIN_NEXT: mode.activate(mode=top, context=...).
```
</details>

<details><summary><code>mode.list</code> (act) — `missing_inputs`</summary>

```
BRIEF: The behavioral-mode roster — name · purpose · behaviors · triggers.

INPUTS: [TODO]

RETURNS: ``{count, modes: [...]}``. chain_next: mode.detect(context) or mode.activate(mode).

CHAIN_NEXT: mode.detect(context) or mode.activate(mode).
```
</details>

### `music` — 6/103 verbs need work

<details><summary><code>music.conceptualize</code> (act) — `long_brief`</summary>

```
BRIEF: Render an album-concept document (act); ``type`` must be a known album type.

INPUTS: artist, title, type (one of ``ALBUM_TYPES``), theme, tracklist. Returns: ``{result, artefact}`` where artefact.kind = ``album-concept``. chain_next: ``music.lyric_report`` for prosody analysis, then ``music.master_album``.

RETURNS: ``{result, artefact}`` where artefact.kind = ``album-concept``. chain_next: ``music.lyric_report`` for prosody analysis, then ``music.master_album``.

CHAIN_NEXT: ``music.lyric_report`` for prosody analysis, then ``music.master_album``.
```
</details>

<details><summary><code>music.db_create_tweet</code> (effect) — `long_brief`</summary>

```
BRIEF: Insert a tweet row via the DBDriver (effect); produces tweet-record artefact.

INPUTS: album, body, scheduled_at (ISO), platform (default ``x``). Returns: ``{result, artefact}`` tweet-record artefact with tweet_id. chain_next: ``music.db_update_tweet`` to flip status; ``music.tweet_schedule_gate``.

RETURNS: ``{result, artefact}`` tweet-record artefact with tweet_id. chain_next: ``music.db_update_tweet`` to flip status; ``music.tweet_schedule_gate``.

CHAIN_NEXT: ``music.db_update_tweet`` to flip status; ``music.tweet_schedule_gate``.
```
</details>

<details><summary><code>music.master_audio</code> (effect) — `long_brief`</summary>

```
BRIEF: Single-track master via AudioDriver (effect); produces mastering-report.

INPUTS: album, path, target_lufs, preset. Returns: ``{result, artefact}`` with input/output paths + gain. chain_next: ``music.qc_audio`` to verify.

RETURNS: ``{result, artefact}`` with input/output paths + gain. chain_next: ``music.qc_audio`` to verify.

CHAIN_NEXT: ``music.qc_audio`` to verify.
```
</details>

<details><summary><code>music.polish_and_master_album</code> (effect) — `long_brief`</summary>

```
BRIEF: Combined polish + master pipeline (effect); produces mastering-report.

INPUTS: album, paths, target_lufs. Returns: ``{result, artefact}`` with per-track gain summary. chain_next: ``music.qc_audio`` per output.

RETURNS: ``{result, artefact}`` with per-track gain summary. chain_next: ``music.qc_audio`` per output.

CHAIN_NEXT: ``music.qc_audio`` per output.
```
</details>

<details><summary><code>music.promote_idea</code> (effect) — `long_brief`</summary>

```
BRIEF: Promote an Idea → Album (effect); record Album + PROMOTED_TO edge.

INPUTS: idea_id, artist, title, genre, type. Returns: ``{idea_id, album_id, album_slug, status}``. chain_next: ``music.conceptualize`` to draft the album concept.

RETURNS: ``{idea_id, album_id, album_slug, status}``. chain_next: ``music.conceptualize`` to draft the album concept.

CHAIN_NEXT: ``music.conceptualize`` to draft the album concept.
```
</details>

<details><summary><code>music.transcribe_sheet</code> (act) — `long_brief`</summary>

```
BRIEF: Transcribe audio → sheet music via AudioDriver (act); produces sheet-music artefact.

INPUTS: album, path (the audio file). Returns: ``{result, artefact}`` where artefact.kind = ``sheet-music`` with source path. chain_next: ``music.publish_asset``.

RETURNS: ``{result, artefact}`` where artefact.kind = ``sheet-music`` with source path. chain_next: ``music.publish_asset``.

CHAIN_NEXT: ``music.publish_asset``.
```
</details>

### `novel` — 9/95 verbs need work

<details><summary><code>novel.conceptualize</code> (act) — `long_brief`</summary>

```
BRIEF: Render a novel-concept document (act); the first verb of the MVN flow.

INPUTS: title, author, premise, central_question. Returns: ``{result, artefact}`` novel-concept artefact. chain_next: ``novel.create_novel`` to mint the Novel node.

RETURNS: ``{result, artefact}`` novel-concept artefact. chain_next: ``novel.create_novel`` to mint the Novel node.

CHAIN_NEXT: ``novel.create_novel`` to mint the Novel node.
```
</details>

<details><summary><code>novel.create_novel</code> (effect) — `long_brief`</summary>

```
BRIEF: Record a Novel node SERVING the intent; materialise disk on production.

INPUTS: title, author, genre (default "novel"; routes the disk layout `works/{author}/works/{genre}/{slug}/`). Returns: ``{novel_id, title, status, work_path?}`` — ``work_path`` appears when the production driver is wired (Spec 121). chain_next: ``novel.create_chapter`` once outline is ready.

RETURNS: ``{novel_id, title, status, work_path?}`` — ``work_path`` appears when the production driver is wired (Spec 121). chain_next: ``novel.create_chapter`` once outline is ready.

CHAIN_NEXT: ``novel.create_chapter`` once outline is ready.
```
</details>

<details><summary><code>novel.list_claims</code> (transform) — `long_brief`</summary>

```
BRIEF: List captured claims; optional verified-status filter (transform).

INPUTS: verified (one of ``CLAIM_VERIFIED`` or ``""`` for all). Returns: ``{claims, count}``. chain_next: ``novel.verify_sources`` for pending claims.

RETURNS: ``{claims, count}``. chain_next: ``novel.verify_sources`` for pending claims.

CHAIN_NEXT: ``novel.verify_sources`` for pending claims.
```
</details>

<details><summary><code>novel.list_ideas</code> (transform) — `long_brief`</summary>

```
BRIEF: List captured ideas; optional status filter (transform).

INPUTS: status (one of ``IDEA_STATUS`` or ``""`` for all). Returns: ``{ideas: [...], count}``. chain_next: ``novel.promote_idea`` for any "new" idea ready to ship.

RETURNS: ``{ideas: [...], count}``. chain_next: ``novel.promote_idea`` for any "new" idea ready to ship.

CHAIN_NEXT: ``novel.promote_idea`` for any "new" idea ready to ship.
```
</details>

<details><summary><code>novel.match_codex_entries</code> (transform) — `long_brief`</summary>

```
BRIEF: Scan ``text`` for any registered codex trigger; return matches (transform).

INPUTS: novel_id, text (the body to scan — chapter outline, scene draft, etc.). Returns: ``{matches: [{entry_id, slug, name, kind, body, trigger_hit}]}``. chain_next: feed matches to ``prompt.assemble_scene_brief``'s world_rules section.

RETURNS: ``{matches: [{entry_id, slug, name, kind, body, trigger_hit}]}``. chain_next: feed matches to ``prompt.assemble_scene_brief``'s world_rules section.

CHAIN_NEXT: feed matches to ``prompt.assemble_scene_brief``'s world_rules section.
```
</details>

<details><summary><code>novel.narrative_order</code> (transform) — `long_brief`</summary>

```
BRIEF: Topo-sort over PRECEDES; canonical narrative reading order (transform).

INPUTS: novel_id. Returns: ``{beats: [{beat_id, label, scene_id}]}`` ordered so every predecessor appears before its successor. chain_next: author's checklist for the manuscript's narrative spine.

RETURNS: ``{beats: [{beat_id, label, scene_id}]}`` ordered so every predecessor appears before its successor. chain_next: author's checklist for the manuscript's narrative spine.

CHAIN_NEXT: author's checklist for the manuscript's narrative spine.
```
</details>

<details><summary><code>novel.promote_idea</code> (effect) — `long_brief`</summary>

```
BRIEF: Idea → Novel transition; records PROMOTED_TO edge (effect).

INPUTS: idea_id, title, author. Returns: ``{idea_id, novel_id, title, status}``. chain_next: ``novel.create_chapter`` to start outlining.

RETURNS: ``{idea_id, novel_id, title, status}``. chain_next: ``novel.create_chapter`` to start outlining.

CHAIN_NEXT: ``novel.create_chapter`` to start outlining.
```
</details>

<details><summary><code>novel.set_chapter_status</code> (effect) — `long_brief`</summary>

```
BRIEF: Flip a Chapter's lifecycle status; enum-checked (effect).

INPUTS: chapter_id, status (one of ``CHAPTER_STATUS``). Returns: ``{chapter_id, status}``. chain_next: ``novel.novel_progress`` to see the aggregate shift.

RETURNS: ``{chapter_id, status}``. chain_next: ``novel.novel_progress`` to see the aggregate shift.

CHAIN_NEXT: ``novel.novel_progress`` to see the aggregate shift.
```
</details>

<details><summary><code>novel.set_novel_status</code> (effect) — `long_brief`</summary>

```
BRIEF: Flip a Novel's lifecycle status; enum-checked (effect).

INPUTS: novel_id, status (one of ``NOVEL_STATUS``). Returns: ``{novel_id, status}``. chain_next: continue per the new lifecycle phase.

RETURNS: ``{novel_id, status}``. chain_next: continue per the new lifecycle phase.

CHAIN_NEXT: continue per the new lifecycle phase.
```
</details>

### `panel` — 1/2 verbs need work

<details><summary><code>panel.experts</code> (act) — `missing_inputs`</summary>

```
BRIEF: The 9-expert roster — name · framework · lens · signature question.

INPUTS: [TODO]

RETURNS: ``{count, experts: [...]}``. chain_next: panel.convene(subject) to apply the panel to a subject.

CHAIN_NEXT: panel.convene(subject) to apply the panel to a subject.
```
</details>

### `persona` — 2/3 verbs need work

<details><summary><code>persona.list</code> (act) — `missing_inputs`</summary>

```
BRIEF: The specialist-persona roster — name · focus · approach.

INPUTS: [TODO]

RETURNS: ``{count, personas: [...]}``. chain_next: persona.recommend(task) or persona.summon(name, task).

CHAIN_NEXT: persona.recommend(task) or persona.summon(name, task).
```
</details>

<details><summary><code>persona.recommend</code> (act) — `missing_inputs`</summary>

```
BRIEF: Recommend the specialist persona(s) best matched to a ``task`` by

INPUTS: [TODO]

RETURNS: ``{task, top, matches: [{persona, score, focus}]}``. chain_next: persona.summon(top, task) to compose the dispatch brief.

CHAIN_NEXT: persona.summon(top, task) to compose the dispatch brief.
```
</details>

### `prompt` — 2/19 verbs need work

<details><summary><code>prompt.register_fragment</code> (effect) — `long_brief`</summary>

```
BRIEF: Write a fragment to the project overlay (effect; runtime-extensible).

INPUTS: slug (str — canonical or alias id), text (str — guidance body, ≤300 tokens recommended), overlay_path (str — defaults to ``.agency/dramatica-fragments-overlay.yaml``). Returns: ``{slug, canonical_id, kind, tokens, overlay_path}`` OR ``{slug, error: 'UNKNOWN_SLUG'}``. chain_next: ``prompt.fragment(slug)`` to verify the round-trip.

RETURNS: ``{slug, canonical_id, kind, tokens, overlay_path}`` OR ``{slug, error: 'UNKNOWN_SLUG'}``. chain_next: ``prompt.fragment(slug)`` to verify the round-trip.

CHAIN_NEXT: ``prompt.fragment(slug)`` to verify the round-trip.
```
</details>

<details><summary><code>prompt.register_framework</code> (effect) — `long_brief`</summary>

```
BRIEF: Write a custom framework to the project overlay (effect; extensible).

INPUTS: slug (str), payload (dict — at minimum ``template``; any of name/intent_category/complexity_tier/audience/components/ when_to_use/discriminators override the vendored defaults). ``intent_category``/``complexity_tier``/``audience`` must be valid ontology enum values (validated HERE so a bad overlay fails fast, not later at ``render`` time when the ``PromptFramework`` node is recorded). overlay_path (str — defaults to the project overlay). Returns: ``{slug, name, intent_category, audience, overlay_path}`` OR ``{slug, error: 'INVALID_ARGUMENT', invalid: {...}}`` when the template is missing or an enum field is out of range. chain_next: ``prompt.framework(slug)`` to verify the round-trip.

RETURNS: ``{slug, name, intent_category, audience, overlay_path}`` OR ``{slug, error: 'INVALID_ARGUMENT', invalid: {...}}`` when the template is missing or an enum field is out of range. chain_next: ``prompt.framework(slug)`` to verify the round-trip.

CHAIN_NEXT: ``prompt.framework(slug)`` to verify the round-trip.
```
</details>

### `reflect` — 2/6 verbs need work

<details><summary><code>reflect.note</code> (act) — `long_brief`</summary>

```
BRIEF: Write a scope-tagged insight node; edged OBSERVED_DURING + SERVES the intent.

INPUTS: scope (one of observation/project/reflection/technical/user/world), text (str — the insight body). Returns: ``{result: <reflection_id>}``. chain_next: ``reflect.recall(scope=)`` or ``reflect.search(query=)`` to surface what was written.

RETURNS: ``{result: <reflection_id>}``. chain_next: ``reflect.recall(scope=)`` or ``reflect.search(query=)`` to surface what was written.

CHAIN_NEXT: ``reflect.recall(scope=)`` or ``reflect.search(query=)`` to surface what was written.
```
</details>

<details><summary><code>reflect.recall_semantic</code> (transform) — `long_brief`</summary>

```
BRIEF: Semantic top-k recall over Reflection nodes; backend-injectable.

INPUTS: query (str — free text; empty → empty results), k (int — max results), scope (str — optional post-rank filter). Returns: ``{results: [{id, score, scope, text, vfrom}], embedder}``. ``text`` truncated to 200 chars (Spec 023 budget); call ``recall``/``search`` for full text. ``embedder`` names the live backend so callers confirm which ran. chain_next: ``reflect.recall(scope=)`` for full text on a top match.

RETURNS: ``{results: [{id, score, scope, text, vfrom}], embedder}``. ``text`` truncated to 200 chars (Spec 023 budget); call ``recall``/``search`` for full text. ``embedder`` names the live backend so callers confirm which ran. chain_next: ``reflect.recall(scope=)`` for full text on a top match.

CHAIN_NEXT: ``reflect.recall(scope=)`` for full text on a top match.
```
</details>

### `research` — 3/5 verbs need work

<details><summary><code>research.lead</code> (act) — `long_brief`</summary>

```
BRIEF: Scope a research question + plan specialists; mints a Research node.

INPUTS: question (str), depth (str — brief|standard|deep). Returns: ``{research_id, specialists, plan}``. chain_next: ``research.specialist`` per planned role.

RETURNS: ``{research_id, specialists, plan}``. chain_next: ``research.specialist`` per planned role.

CHAIN_NEXT: ``research.specialist`` per planned role.
```
</details>

<details><summary><code>research.specialist</code> (act) — `long_brief`</summary>

```
BRIEF: One bounded sub-search; records Citations under the research_id.

INPUTS: research_id (str — from research.lead), role (str — codebase|prior-reflections|doc-corpus|web), query (str), search_root (str — codebase only), docs_root (str — doc-corpus only), k (int — max hits). Returns: ``{citations, summary}``. chain_next: more specialists OR research.verify.

RETURNS: ``{citations, summary}``. chain_next: more specialists OR research.verify.

CHAIN_NEXT: more specialists OR research.verify.
```
</details>

<details><summary><code>research.verify</code> (act) — `long_brief`</summary>

```
BRIEF: Adversarial citation check; emits a Verification node.

INPUTS: research_id (str — from prior research.lead). Returns: ``{ok, checks: {evidence-supports-claim, contradiction-cluster}}``. chain_next: walker's publish phase on ok=True; rerun specialists on ok=False.

RETURNS: ``{ok, checks: {evidence-supports-claim, contradiction-cluster}}``. chain_next: walker's publish phase on ok=True; rerun specialists on ok=False.

CHAIN_NEXT: walker's publish phase on ok=True; rerun specialists on ok=False.
```
</details>

### `select` — 1/2 verbs need work

<details><summary><code>select.archetypes</code> (act) — `missing_inputs`</summary>

```
BRIEF: The approach archetypes + their trade-offs.

INPUTS: [TODO]

RETURNS: ``{count, archetypes: {name: description}}``. chain_next: select.route(operation) to pick one for an operation.

CHAIN_NEXT: select.route(operation) to pick one for an operation.
```
</details>

### `skill_generator` — 1/1 verbs need work

<details><summary><code>skill_generator.generate</code> (act) — `long_brief`</summary>

```
BRIEF: Author a SKILL.md and lint it against the CSO rules; flag if not deploy-ready.

INPUTS: name (skill slug), description (str — the trigger phrase), body (str — the SKILL.md content). Returns: ``{name, skill_md, ok, violations}`` (wire shape). chain_next: caller writes ``skills/<name>/SKILL.md`` if ``ok=True``; otherwise iterates on ``violations``.

RETURNS: ``{name, skill_md, ok, violations}`` (wire shape). chain_next: caller writes ``skills/<name>/SKILL.md`` if ``ok=True``; otherwise iterates on ``violations``.

CHAIN_NEXT: caller writes ``skills/<name>/SKILL.md`` if ``ok=True``; otherwise iterates on ``violations``.
```
</details>

### `subagent` — 1/1 verbs need work

<details><summary><code>subagent.develop</code> (effect) — `long_brief`</summary>

```
BRIEF: Dispatch a worker child via delegate, then gate it spec-review→quality-review; done iff both pass.

INPUTS: driver (capability name), driver_verb (str), item (dict — task payload), spec_passed (bool), quality_passed (bool), spec_evidence/quality_evidence (str, optional). Returns: ``{child, done, spec, quality}`` (wire shape). chain_next: terminal — ``done=True`` flips the child Lifecycle to ``completed``; ``done=False`` leaves it ``input-required``.

RETURNS: ``{child, done, spec, quality}`` (wire shape). chain_next: terminal — ``done=True`` flips the child Lifecycle to ``completed``; ``done=False`` leaves it ``input-required``.

CHAIN_NEXT: terminal — ``done=True`` flips the child Lifecycle to ``completed``; ``done=False`` leaves it ``input-required``.
```
</details>

### `symbols` — 1/3 verbs need work

<details><summary><code>symbols.legend</code> (transform) — `missing_inputs`</summary>

```
BRIEF: The phrase↔symbol legend.

INPUTS: [TODO]

RETURNS: ``{count, legend: [{phrase, symbol}]}``. chain_next: symbols.compress(text) / symbols.expand(text).

CHAIN_NEXT: symbols.compress(text) / symbols.expand(text).
```
</details>

### `thinking` — 1/11 verbs need work

<details><summary><code>thinking.apply_full_review</code> (act) — `long_brief`</summary>

```
BRIEF: Run the 8 founding methods in sequence; produce thinking-analysis artefact (act).

INPUTS: subject (defaults to serving intent), depth (one of ANALYSIS_DEPTH; documents the rigor level). Returns: ``{result, artefact}`` thinking-analysis artefact. chain_next: ``thinking.tradeoffs`` if multiple recommendations compete, OR commit + ``dogfood.record_decision``.

RETURNS: ``{result, artefact}`` thinking-analysis artefact. chain_next: ``thinking.tradeoffs`` if multiple recommendations compete, OR commit + ``dogfood.record_decision``.

CHAIN_NEXT: ``thinking.tradeoffs`` if multiple recommendations compete, OR commit + ``dogfood.record_decision``.
```
</details>

### `workspace` — 1/2 verbs need work

<details><summary><code>workspace.isolate</code> (effect) — `long_brief`</summary>

```
BRIEF: Create an isolated git worktree on a fresh branch off `base`; record the Workspace.

INPUTS: branch (str — new branch name), base (str — default 'main'). Returns: ``{workspace, path, branch, base}`` on success; ``{error, branch, detail}`` on failure (wire shape). chain_next: ``workspace.baseline(workspace=, command=)`` to record the starting GREEN state.

RETURNS: ``{workspace, path, branch, base}`` on success; ``{error, branch, detail}`` on failure (wire shape). chain_next: ``workspace.baseline(workspace=, command=)`` to record the starting GREEN state.

CHAIN_NEXT: ``workspace.baseline(workspace=, command=)`` to record the starting GREEN state.
```
</details>

