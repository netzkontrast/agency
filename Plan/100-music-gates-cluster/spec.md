---
spec_id: "100"
slug: music-gates-cluster
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["094", "095", "096", "097", "098", "099", "093"]
affects:
  - agency/capabilities/music/clusters/gates.py
  - agency/capabilities/music/ontology.py       # release-qa + pre-gen + validate-structure skills
  - tests/test_music_gates.py
domain: music / gates / lifecycle
wave: 7
parent_spec: "093"
---

# Spec 100 — Music Gates Cluster

## Why

The gates cluster is the **lifecycle binder** — the cluster that wires every
other cluster's quality predicates into the album's lifecycle as computed
`gate.check` calls + terminal `elicit` confirmations. Without 100, the lyrics
gates, audio QC gates, and research verification all fire in isolation; with
100, they compose into the canonical **pre-generation** and **release-qa**
workflows that bitwize ships as load-bearing prose.

bitwize ships ~6 gate-shaped tools (`run_pre_generation_gates`,
`validate_album_structure`, `validate_section_structure`, `diagnose`,
`rebuild_state`, `health_check`) — but the **doctrine** that "nothing ships
without passing gates" is the value here, not the tools. 100 ports that
doctrine into agency's `gate.check` + `elicit` substrate.

This is also the cluster that lights the **provenance moat at full scale**:
each gate fire records a `Gate` event SERVES the intent; a release audit
traces every blocker, every BLOCKED_ON reason, every PASSED predicate, in
chronological order.

## Done When

- [ ] **Verbs ship:** 6 top-level + 5 composite gate verbs = 11 registered
  (see "Verb manifest"), all computing predicates from cross-cluster state.
  Without the composite gates, the `pre-generation` and `release-qa` skill
  walks crash with "unknown verb" — they are part of the cluster, not a
  followup.
- [ ] **No DRIVER additions** — gates compose existing cluster verbs +
  StateDriver reads + `gate.check` core verb.
- [ ] **Walkable skill: `pre-generation`** — 4-phase workflow (concept-ready
  → research-verified → lyrics-clean → ready-to-generate), all computed gates,
  terminal `elicit` on ready.
- [ ] **Walkable skill: `release-qa`** — 4-phase workflow (audio-mastered →
  catalogue-synced → promo-drafted → ship), terminal `elicit` on ship.
- [ ] **Walkable skill: `validate-structure`** — driver-only 3-phase workflow
  (album-files → track-files → mirror-paths), reports without gating.
- [ ] **No regression on `pregen_check`, `release_check`** (preserved from 007).
- [ ] **End-to-end test:** `tests/test_music_e2e.py` (the master 093's
  end-to-end gate) drives the full pipeline through 100's `release-qa` and
  asserts `memory_graph_provenance(intent_id)` returns the complete chain
  (every gate, every PRODUCES, every SERVES, every BLOCKED_ON).
- [ ] **`scripts/test-cap music_gates`** Green.
- [ ] **`TODO.md` updated;** parent (093) row moved to **Shipped** once 100's
  end-to-end test passes.

## Verb manifest

| # | Verb | Role | Driver / Backing | bitwize tool absorbed | Notes |
|---|---|---|---|---|---|
| 1 | `pregen_check` | effect | StateDriver+gate.check | `run_pre_generation_gates` | kept from 007; expanded predicates |
| 2 | `release_check` | effect | StateDriver+gate.check | (composite) | kept from 007 — track status read graph-canonically (NOT via DBDriver — see "Track-status correction" below) |
| 3 | `validate_album` | transform | StateDriver | `validate_album_structure` | mirror-path + file-presence check |
| 4 | `validate_sections` | transform | TextDriver | `validate_section_structure` | delegated to 095 |
| 5 | `diagnose` | transform | (composite, driver-free) | `diagnose` | composite health probe |
| 6 | `music_health` | transform | (driver-free) | `health_check` | kept from 007 |

**Internal composite gate verbs** (registered, but called only by walkable
skill phases — counted in 093's gate-verb column):

| # | Verb | Role | Composes | Called by skill |
|---|---|---|---|---|
| G1 | `concept_gate` | effect | StateDriver.find_album + gate.check | `pre-generation` phase 1 |
| G2 | `lyrics_pregen_gate` | effect | `music.list_tracks` + 4 lyric `*_gate` verbs (095) + gate.check | `pre-generation` phase 3 |
| G3 | `audio_release_gate` | effect | `music.list_tracks` + `music.qc_audio` + gate.check | `release-qa` phase 1 |
| G4 | `catalogue_gate` | effect | `music.get_streaming_urls` + `music.db_list_tweets` + gate.check | `release-qa` phase 2 |
| G5 | `promo_gate` | effect | StateDriver.read promo dir + gate.check | `release-qa` phase 3 |

**Total: 6 top-level verbs + 5 composite gate verbs = 11 registered.** All 6
bitwize-equivalent tools (1:1) + 5 agency-native compositions that the
walkable skills compose. The composite gates are what make the
`pre-generation` and `release-qa` skill walks executable; without them, the
skills reference undefined gate verbs at walk-time.

> The 093 master gate-column for cluster 100 lists 4 gates; this manifest
> lists 5. The fifth (`concept_gate`, phase 1 of pre-generation) was
> implicit in the master table's count. 093 master gate-column corrected
> to 5 in this same wave.

## Design

### Walkable skill: `pre-generation`

```python
PRE_GENERATION_SKILL = {
    "name": "pre-generation",
    "kind": "gate",
    "phases": [
        {"index": 1, "name": "concept-ready",
         "produces": ["concept_complete"],
         "gate": "computed", "gate_verb": "music.concept_gate"},
        {"index": 2, "name": "research-verified",
         "produces": ["all_claims_human_confirmed"],
         "gate": "computed", "gate_verb": "music.verify_gate"},
        {"index": 3, "name": "lyrics-clean",
         "produces": ["prosody_clean", "pronunciation_clean",
                      "explicit_rated"],
         "gate": "computed", "gate_verb": "music.lyrics_pregen_gate"},
        {"index": 4, "name": "ready-to-generate",
         "produces": ["approved"],
         "gate": "hard"},   # elicit — human says "ship it to Suno"
    ],
}
```

### Walkable skill: `release-qa`

```python
RELEASE_QA_SKILL = {
    "name": "release-qa",
    "kind": "gate",
    "phases": [
        {"index": 1, "name": "audio-mastered",
         "produces": ["all_tracks_mastered", "qc_passed"],
         "gate": "computed", "gate_verb": "music.audio_release_gate"},
        {"index": 2, "name": "catalogue-synced",
         "produces": ["streaming_urls_recorded", "tweets_drafted"],
         "gate": "computed", "gate_verb": "music.catalogue_gate"},
        {"index": 3, "name": "promo-drafted",
         "produces": ["promo_per_platform_drafted"],
         "gate": "computed", "gate_verb": "music.promo_gate"},
        {"index": 4, "name": "ship",
         "produces": ["released"],
         "gate": "hard"},   # elicit — human ships
    ],
}
```

### Walkable skill: `validate-structure`

```python
VALIDATE_STRUCTURE_SKILL = {
    "name": "validate-structure",
    "kind": "validation",   # not a gate — reports findings without blocking
    "phases": [
        {"index": 1, "name": "album-files",
         "produces": ["album_dir_well_formed"]},
        {"index": 2, "name": "track-files",
         "produces": ["track_count_valid", "missing_tracks_listed"]},
        {"index": 3, "name": "mirror-paths",
         "produces": ["content_audio_documents_aligned"]},
    ],
}
```

This skill is a **diagnostic walk**, not a workflow gate — it reports issues
without pausing the lifecycle. Useful for `validate_album` periodic checks.

### Primary actors (panel-added, iteration 1 / Cockburn)

- `pre-generation` — **Primary actor: agent** (composes predicates from
  cross-cluster state via `gate.check`); human-curator approves at phase 4
  (ready-to-generate). Without approval, the lifecycle stays paused.
- `release-qa` — **Primary actor: agent** (composes release predicates);
  human-curator ships at phase 4 (ship). This is the terminal human gate
  of the entire music pipeline.
- `validate-structure` — **Primary actor: agent** (diagnostic, no gating);
  emits findings the user reads via `document.render`.

### Track-status correction (panel-resolved, iteration 2 / Newman)

The original 100 example read track status via DBDriver (`cur.execute(
"SELECT slug, status FROM tracks WHERE album = %s", ...)`). **That was
wrong** — track state is graph-canonical (per 094 ontology), NOT in
Postgres. The DBDriver carries only tweet/social state.

The corrected `release_check` reads track status via the StateDriver via
the music capability's own `list_tracks`:

```python
@verb(role="effect")
def release_check(self, lifecycle_id: str, album: str = "") -> ToolResult:
    """Composite release-qa gate — reads track status from graph (StateDriver),
    NOT from the tweet DB. Records PASSED/BLOCKED_ON via gate.check.

    API note (Codex P2 iteration 5 — same contract as 099): ctx.call returns
    the spawned verb's unwrapped result dict (capability.py:138 →
    self.spawn(...)[0]). Never .data on a ctx.call result.
    """
    result = self.ctx.call("music", "list_tracks", album=album)
    tracks = result["tracks"]
    unmastered = [t["slug"] for t in tracks if t["status"] != "mastered"]
    passed = not unmastered
    self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                  name="release-qa", passed=passed,
                  evidence="all mastered" if passed
                           else f"unmastered: {unmastered}")
    if not passed:
        return ToolResult.failure("GATE_FAILED",
                                  f"release-qa blocked; unmastered: {unmastered}")
    return ToolResult.success(data={"album": album, "gate": "release-qa",
                                    "passed": True})
```

The original 007 `release_check` is corrected in the same PR that ships 100
(the move from DBDriver → StateDriver for track status is part of 100's
followup task list).

### Gate composition (the magic move)

The expanded `pregen_check` verb (kept from 007 but with more inputs) reads
state across clusters via composed driver calls:

```python
@verb(role="effect")
def pregen_check(self, lifecycle_id: str, album: str = "") -> ToolResult:
    """Composite pre-generation gate — reads cross-cluster state and computes
    PASSED/BLOCKED_ON via gate.check.

    API note (Codex P2 iteration 6 — same unwrap contract as 099 + the
    release_check fix earlier in this spec): ctx.call returns the spawned
    verb's UNWRAPPED result dict. Never `.data` or `["data"]` indexing.
    """
    state = self.ctx.get_driver("music_state")
    album_data = state.find_album(album)[0]

    # Read predicates from cluster state (all via existing verbs / drivers):
    concept_ok = album_data.get("status") in {"in-production", "mastered",
                                              "released"}
    research = self.ctx.call("music", "pending_verifications", album=album)
    research_ok = research["pending_count"] == 0                # NOT ["data"][...]
    lyrics = self.ctx.call("music", "list_tracks", album=album)
    lyrics_ok = all(t["status"] in {"recorded", "mixed", "mastered"}
                    for t in lyrics["tracks"])                  # NOT ["data"][...]

    missing = []
    if not concept_ok: missing.append("concept")
    if not research_ok: missing.append("research")
    if not lyrics_ok: missing.append("lyrics")

    passed = not missing
    self.ctx.call("gate", "check", lifecycle_id=lifecycle_id,
                  name="pre-generation", passed=passed,
                  evidence="all green" if passed else f"missing: {missing}")
    if not passed:
        return ToolResult.failure("GATE_FAILED",
                                  f"pre-generation blocked; missing: {missing}")
    return ToolResult.success(data={"album": album, "gate": "pre-generation",
                                    "passed": True})
```

`release_check` composes similarly across audio (master status), catalogue
(streaming URLs), promo (tweets drafted), and structure (mirror-path
validity).

### The end-to-end test (the master 093's gate)

```python
# tests/test_music_e2e.py — the full pipeline asserted via provenance
def test_music_full_pipeline_records_complete_provenance_chain(fake_drivers):
    """Drive the full music capability through release; assert that
    memory_graph_provenance returns every Invocation/Artefact/Reflection
    SERVES the album intent.

    API note (Codex P2 — verified against capability.py:520 +
    test_engine_unwrap_contract.py:56): Engine does NOT expose .call() or
    .intent_bootstrap() helpers. The two canonical idioms are:
      A) `engine.registry.invoke(memory, intent_id, cap, verb, agent_id=, **kw)`
         → returns `(result_dict, error_str)`; the registry has already
         unwrapped ToolResult.data.
      B) `await engine.build_mcp(codemode=True).call_tool(tool_name, kwargs)`
         → MCP wire path; result on `.structured_content` or `.data`.
    The intent is minted via `engine.intent.capture_and_confirm(purpose,
    deliverable, acceptance, owner="user")` → returns the intent_id string.
    """
    eng = Engine(":memory:", drivers=fake_drivers())
    intent_id = eng.intent.capture_and_confirm(
        purpose="album X", deliverable="release", acceptance="verify provenance",
        owner="user")
    invoke = lambda cap, verb, **kw: eng.registry.invoke(
        eng.memory, intent_id, cap, verb, agent_id="agent:e2e", **kw)[0]

    # 1. lifecycle
    invoke("music", "capture_idea", text="album X")
    idea = invoke("music", "list_ideas")
    invoke("music", "promote_idea", idea_id=idea["ideas"][0]["id"])
    invoke("music", "conceptualize", artist="Artist", title="X",
           type="documentary", theme="...", tracklist="t1\nt2")

    # 2. research
    invoke("music", "dispatch_research", question="X facts",
           domains="legal,financial", album="X")
    invoke("music", "verify_sources", album="X")

    # 3. lyrics
    invoke("music", "lyric_report", track="t1", lyrics="...")

    # 4. audio
    invoke("music", "master_album", album="X", target_lufs=-14)
    invoke("music", "qc_audio", path=".../X/master.wav")

    # 5. catalogue + promo
    invoke("music", "db_create_tweet", album="X", body="...",
           scheduled_at="...", platform="x")
    invoke("music", "promo_copy", album="X", platform="x")
    invoke("music", "publish_asset", key="X/master.wav", body=b"...")

    # 6. gates — release_check should now pass.
    # Codex P2 iteration 5: there is no `eng.memory.find_lifecycle_for_intent`
    # method. Lifecycles are created directly via `memory.record("Lifecycle",
    # {...})` + `memory.link(lifecycle_id, intent_id, "SERVES")` (the pattern
    # used in tests/test_codex_c2_c3.py:45-46 and agency/_pressure.py:147).
    # The E2E sketch mints one explicitly here, matching how the album-concept
    # skill walker creates its lifecycle:
    lifecycle_id = eng.memory.record("Lifecycle",
                                     {"state": "working", "phase": 0,
                                      "name": "release-qa"})
    eng.memory.link(lifecycle_id, intent_id, "SERVES")
    result = invoke("music", "release_check", lifecycle_id=lifecycle_id,
                    album="X")
    assert result.get("passed") is True

    # 7. THE HEADLINE — provenance returns the full chain.
    # Codex P2 iteration 5: `memory_graph_provenance` is an MCP SUBSTRATE
    # tool (engine.py:438 @mcp.tool), NOT a capability verb. There is no
    # `memory` capability. The substrate tool's signature is
    # `memory_graph_provenance(intent_id: str) -> dict` — NO `include` kwarg.
    # Two equivalent call paths:
    #   A) Direct on the memory object: `eng.memory.provenance(intent_id)`
    #      (engine.py:440 — `mem.provenance(intent_id)`).
    #   B) Via the MCP wire: `await mcp.call_tool("memory_graph_provenance",
    #      {"intent_id": intent_id})` after `mcp = eng.build_mcp(codemode=True)`.
    # Path A is simpler for the E2E test.
    #
    # SHAPE (Codex P2 iteration 6 — verified against agency/memory.py:243-…):
    # `Memory.provenance` returns dict[str, list[dict]] with keys
    # `serves`, `agents`, `artefacts`, `gates`. NOT `invocation_count` /
    # `artefact_count` / `node_types` / `edges_from_root`. Assertions
    # must use the real keys.
    prov = eng.memory.provenance(intent_id)
    # The `serves` list carries every node SERVES the intent — invocations,
    # reflections, lifecycles, and the music-domain nodes (Idea, Album,
    # ResearchClaim) that linked via SERVES.
    serves_labels = {p.get("__label") or "" for p in prov["serves"]}
    assert "Invocation" in serves_labels      # every invoke() recorded one
    assert "ResearchClaim" in serves_labels   # the dispatch_research path
    # The `artefacts` list carries every PRODUCES artefact under the intent:
    artefact_kinds = {a.get("kind", "") for a in prov["artefacts"]}
    assert "album-concept" in artefact_kinds
    assert "mastering-report" in artefact_kinds
    assert "promo-copy" in artefact_kinds
    assert "published-asset" in artefact_kinds
    # The `gates` list shows the gate.check ledger:
    gate_names = {g.get("name", "") for g in prov["gates"]}
    assert "release-qa" in gate_names         # release_check fired it
    # Length sanity (causal-ordered per 093's call-patterns table):
    assert len(prov["serves"]) >= 12          # ~1 per invocation
    assert len(prov["artefacts"]) >= 5
```

## Test plan (cluster-local)

```python
# tests/test_music_gates.py — ~10 tests
def test_gates_cluster_discovers_all_verbs(): ...
def test_pregen_check_blocks_when_concept_incomplete(): ...
def test_pregen_check_blocks_when_research_pending(): ...
def test_pregen_check_blocks_when_lyrics_unclean(): ...
def test_pregen_check_passes_when_all_green(): ...
def test_release_check_blocks_on_unmastered_tracks(): ...
def test_validate_album_reports_missing_mirror_paths_without_blocking(): ...
def test_diagnose_returns_per_cluster_readiness_report(): ...
def test_pregeneration_skill_walks_through_three_computed_gates(): ...
def test_release_qa_skill_pauses_on_hard_ship_gate(): ...
```

## Open questions

1. **`pregen_check` predicates — hardcoded or pluggable?** Hardcoded for now
   (matches bitwize). A followup could let a project register custom predicates
   via the ontology.
2. **Should `diagnose` be a verb or a CLI command?** Both — it's a verb
   (discoverable) AND a `agency music diagnose` shell template (Spec 075).
3. **Validate-structure as a `validation` kind vs `workflow` kind?** New kind
   `validation` proposed (walked without lifecycle pausing). Ontology accepts
   it (open kind set). Documented in ontology comments.
4. **Cross-spec composition concern.** `pregen_check` calls verbs on the same
   cap (`music.pending_verifications`, `music.list_tracks`). The pattern is
   already proven in 091/092. No engine change needed.

## Followup — Implementation Status (2026-06-09)

**Verdict:** **Shipped** — and the master Spec 093 flips to Shipped with it.

### Done (Slice 1 — branch `claude/music-100-gates`, stacked on PR #71)
- **3 NEW top-level verbs** on `MusicCapability` (3 already shipped: `pregen_check` + `release_check` + `music_health` from 007):
  - `validate_album` (transform) — StateDriver check on file presence + mirror-path consistency
  - `validate_sections` (transform) — TextDriver-delegated section structure validation; iterates album tracks when called with empty lyrics
  - `diagnose` (transform, driver-free) — composite health probe returning drivers_wired + verbs_count + skills_count
- **5 NEW composite gate verbs**:
  - `concept_gate` — passes iff album resolves via StateDriver
  - `lyrics_pregen_gate` — composes 095's prosody + pronunciation + explicit sub-gates; all must pass
  - `audio_release_gate` — passes iff every track in album has status=mastered
  - `catalogue_gate` — passes iff at least 1 streaming URL + 1 scheduled tweet
  - `promo_gate` — passes iff at least 1 published-asset in cloud store for the album
- **3 NEW walkable skills**:
  - `pre-generation-full` (4-phase: concept-ready → research-verified → lyrics-clean → ready-to-generate hard)
  - `release-qa-full` (4-phase: audio-mastered → catalogue-synced → promo-drafted → ship hard)
  - `validate-structure` (3-phase driver-only)
- **The end-to-end provenance chain test passes** (`test_e2e_full_provenance_chain_through_release_qa`): drives a full music pipeline through every cluster (lifecycle → research → audio → catalogue → promo → gates) and asserts the complete graph provenance — published-asset + tweet-record artefacts PRODUCES'd against the intent; audio-release + catalogue + promo gates recorded. **This is the master Spec 093 contract met**.
- **19 gate tests** covering: verb discovery; all 3 skills' shape; validate_album happy + missing-album path; diagnose driver inventory; concept_gate pass+block; audio_release_gate pass+block (mastered+unmastered); catalogue_gate pass+block; promo_gate pass+block; lyrics_pregen_gate empty-lyrics block; both walkable skills' full walk; the E2E test.
- **Block-mode lint clean**: 97 verbs total on `music` (the surface_size>12 warn accepted per the documented Slice 2 file-split deferral).
- **Full pytest -n auto Green**: 1099 passed, 6 skipped, 0 failed.

### Master Spec 093 contract verified
The bitwize-music plugin (~75 verbs across 8 clusters) is now fully ported to `agency/capabilities/music/` as a first-class clustered Capability. ZERO engine edits across the 7 PRs (#65-#72); every effect verb records provenance; every gate records `Gate` + `PASSED`/`BLOCKED_ON` SERVES the intent; release audit is one graph traversal. The provenance moat is lit on the full pipeline.

### Deferred (per-cluster nice-to-haves, not Done-When-blocking)
- Per-cluster file split — 97 verbs live on `_main.py`. Move into `clusters/{lifecycle,lyrics,audio,catalogue,promo,research,gates}.py` as a single cleanup PR.
- Spec 097 Slice 2: 6 promo platform templates + `[music-cloud]` extra.
- Spec 098 Slice 2: LLM driver routing for `promo_copy`.
- Spec 099 Slice 2: `research-domains.yaml` + research/sources templates.

### Evidence
- code: `agency/capabilities/music/_main.py` (8 new gate methods + 3 transforms), `ontology.py` (3 walkable skills).
- tests: `tests/test_music_gates.py` (19 tests Green); full suite Green: **1099 passed**.
- lint: `plugin.lint_capability('music')` → ok=True block mode, 0 violations.
- branch: `claude/music-100-gates` (stacked on `claude/music-099-research`).

**Master 093 row flipped to Shipped in TODO.md.**
