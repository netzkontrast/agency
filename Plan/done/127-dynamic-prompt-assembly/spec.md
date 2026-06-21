---
spec_id: "127"
slug: dynamic-prompt-assembly
status: shipped
state: done
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["109", "120", "129"]
affects:
  - agency/capabilities/prompt/_main.py
  - agency/capabilities/novel/_main.py
  - tests/test_dynamic_prompt_assembly.py
domain: novel / prompt / context-economics
parent_spec: "101"
mvp-source:
  - "Novelcrafter / Scrivener UX (smart context injection — small windows, the right facts)"
  - "agency/capabilities/novel/data/dramatica/ontology.json (304 entries)"
  - "Plan/done/129-dramatica-prompt-fragments/spec.md (the fragment library this verb composes)"
---

# Spec 127 — Dynamic prompt assembly (`prompt.assemble_scene_brief`)

## Why

Writing a scene with an LLM-agent is a context-assembly problem. The agent
needs: which throughline does THIS scene serve, who's the POV, what does the
POV know AT THIS POINT in story-time, which world rules apply, what
foreshadowing obligations are open, what continuity facts have been
established. The wrong slice (too narrow → contradictions; too wide → drift +
tokens) makes the output worse.

Agency has the substrate (storyform graph, Dramatica fragments per Spec 129,
character + chapter + scene nodes). Spec 127 is the verb that **assembles**
the right slice into a bounded prompt — the Novelcrafter pattern, but with
a real graph behind it instead of authored "codex entries". One verb, one
artefact, full provenance moat.

## Done When

- [ ] **`prompt.assemble_scene_brief(scene_id) -> SceneBrief`** — pure
      transform; reads from graph, composes prompt, returns it. No LLM
      call.
- [ ] **`SceneBrief` shape**: `{prompt, sections, token_count, sources}`
      where:
      - `prompt` — the full ready-to-send prompt body
      - `sections` — `{storyform, pov_card, scene_cast, world_rules,
        continuity, foreshadowing, voice_constraints}` — each a string
        block, each ≤ a per-section budget (320 tok default).
      - `sources` — `[{node_id, kind, contributed: section_name}]` —
        which graph nodes contributed to which section. Closes the
        provenance moat: every fact in the brief traces to a node.
- [ ] **Total brief ≤ 4000 cl100k tokens** (configurable; default cap).
      Over-budget sections truncate-then-flag with `truncated: ["world_rules"]`.
- [ ] **Section composers** (each a private helper):
      - `_storyform_section` — picks throughline + concern + crucial
        element fragments via `prompt.fragments_for` (Spec 129).
      - `_pov_card` — POV character's voice + traits + arc-status.
      - `_scene_cast` — non-POV characters present in this scene
        (per `SCENE_CAST` edge).
      - `_world_rules` — world facts whose triggers fire in this scene
        (Spec 132 codex parity; placeholder until 132).
      - `_continuity` — story-time facts established BEFORE this scene
        in narrative order (Spec 128 dependency; placeholder until 128).
      - `_foreshadowing` — planted Chekhov's-gun obligations open at
        this scene (Spec 123 dependency).
      - `_voice_constraints` — POV tense + voice rules from chapter +
        story-level outline.
- [ ] **`prompt.assemble_chapter_brief(chapter_id)`** — sister verb;
      same shape, scoped to a chapter (across N scenes).
- [ ] **`novel.render_chapter_brief` chains** to
      `prompt.assemble_chapter_brief` (the existing verb is a stub;
      this is the wire-up).
- [ ] **Provenance**: records `Artefact(kind="scene-brief")` with
      `SERVES` to intent + per-source `BRIEF_USED` edges (new edge type).
      `analyze.graph` shows which fact came from where.
- [ ] **Fake-driver friendly**: no driver dep; pure graph walk + Spec
      129 fragment lookup. Runs in CI without filesystem.
- [ ] **scene-writer walkable skill** (5 phases, advance from Spec 130
      brainstorm): assemble → validate → generate (driver) → check →
      integrate. Phase 1 binds to `prompt.assemble_scene_brief`; phase 4
      to `novel.novel_coherence_check`.
- [ ] TODO.md row + drift clean.

## Design notes

- **Bounded by construction**: section budgets first, total budget second.
  Section composers truncate from least-load-bearing tail first
  (voice_constraints sits at the END; storyform sits at the TOP).
- **Read-only**: `assemble_scene_brief` writes the Artefact node but
  doesn't mutate scene/chapter/character state. Spec 130's skill phase 5
  (integrate) handles the write-back.
- **Sourcing-model**: graph IS the source of truth (CLAUDE.md rule 2);
  the brief is a rendered view. Re-running `assemble_scene_brief` on
  the same scene + same graph state IS idempotent — same brief, same
  Artefact (sha-keyed).
- **Hooks Spec 128 (time)**: when 128 lands, `_continuity` queries
  `StoryTimeEvent` nodes ≤ this scene's beat. Until then, returns
  empty + flags "continuity: time-graph not yet shipped" in sources.
- **Hooks Spec 131 (character knowledge)**: when 131 lands, `_pov_card`
  includes "POV knows X but not Y" facts. Until then, pulls from
  static character profile.

## Open questions

1. **Brief format**: structured markdown sections vs prose vs JSON?
   Recommend structured markdown — agent-friendly, human-readable, easy
   for the assembler to compose by string concat.
2. **Default budgets**: 4000 tok total / 320 per section is conservative
   (Claude-3 context > 200k). Recommend keep small; smaller briefs are
   *better* prompts. Configurable per-call.
3. **Multi-scene chapter brief**: include FULL scene briefs concatenated
   (heavy), or a chapter-level summary + per-scene index? Recommend the
   latter — chapter brief is for outlining, not generating.

## Followup — Implementation Status (2026-06-10)

**Done (Slice 1):**
- `prompt.assemble_scene_brief(scene_id, max_tokens=4000, section_budget=320)`
  ships as an `act` verb in `agency/capabilities/prompt/_main.py`. Walks
  Scene → Chapter → Novel → Storyform via `ctx.recall` + `ctx.find`; parses
  the Storyform `body` field as NCP JSON and flattens it into a
  fragments_for scope.
- **All 7 sections compose**: storyform / pov_card / scene_cast /
  world_rules / continuity / foreshadowing / voice_constraints. The
  three with future-spec dependencies (world_rules → 132, foreshadowing
  → 123, continuity time-graph → 128) ship as **explicit placeholders
  that name the gating spec** — a reader sees "Spec 132 codex parity
  pending" instead of a silent gap. Continuity does what it can today:
  anchors to the chapter number.
- **Storyform section composes via Spec 129**: when a Storyform body
  is present, `_compose_storyform` calls `cap.fragments_for(scope)` and
  renders each matched fragment as a bullet with canonical_id + kind +
  text. The good-fixture-shaped NCP routes to throughline.main +
  class.universe + type.past + var.self-interest + var.morality — all
  with bootstrap fragments per 129.
- **Section + total budgets enforced**: each section truncated to
  ``section_budget`` (default 320 tok) with `truncated` flagging;
  ``max_tokens`` (default 4000) caps the cumulative count and drops
  lowest-priority sections when bound. Truncation appends `...` so the
  cut is honest.
- **Provenance moat**: each call records `Artefact(kind="scene-brief",
  scene_id, token_count, section_count, truncated_count)` with SERVES
  edge to the intent. The `sources` array tags each contributing
  ontology fragment + Scene/Chapter node with `contributed: <section>`
  so a future query can answer "which graph node informed THIS line of
  the brief".
- **Rendered output**: structured markdown — `# Scene brief` followed
  by `## <section title>` per section, per Open Q1 (markdown for
  agent-readability + human-readability).

**Still (deferred):**
- `prompt.assemble_chapter_brief(chapter_id)` sister verb — same shape,
  chapter-summary-plus-per-scene-index. Slice 2 work.
- `BRIEF_USED` edge type — current Slice 1 uses SERVES for the brief
  Artefact + sources-array for the per-fragment trail. A typed
  `BRIEF_USED` edge between Artefact and contributing nodes would let
  graph queries enumerate "which briefs used THIS fragment". Slice 2.
- `novel.render_chapter_brief` wire-up to `assemble_chapter_brief`.
- `scene-writer` 5-phase walkable skill (Spec 130 territory).
- Hooks: when Spec 128 (story-time graph) and Spec 131 (character
  knowledge) ship, the `_continuity` and `_pov_card` composers gain
  their real data sources. The placeholders already name the dependency,
  so the upgrade is mechanical.

**Test:** 16 new tests (`tests/test_dynamic_prompt_assembly.py`) — verb
registration, brief-shape return contract, NOT_FOUND path, all-7-sections
present, POV/voice/continuity anchoring, placeholder dependency-flagging,
storyform fragment composition, source attribution, section budget
truncation, total budget priority drops, Artefact + SERVES provenance,
rendered markdown shape. 250+ across prompt/novel/naming green; drift
clean (prompt cap surface_size warn ACCEPTED per accept-warn marker,
documented rationale).

**Open Q resolutions:** Q1 — structured markdown (agent-friendly +
human-readable). Q2 — 4000 tok / 320 per section kept as defaults
(configurable per-call). Q3 — chapter brief deferred to Slice 2 (the
spec hints latter approach is better but it's a separate composer that
warrants its own design pass).
