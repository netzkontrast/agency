---
spec_id: "100"
slug: music-gates-cluster
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["094", "095", "096", "097", "099", "093"]
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

- [ ] **Verbs ship:** 6 gate verbs (see "Verb manifest"), all computing
  predicates from cross-cluster state.
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
| 2 | `release_check` | effect | DBDriver+gate.check | (composite) | kept from 007 |
| 3 | `validate_album` | transform | StateDriver | `validate_album_structure` | mirror-path + file-presence check |
| 4 | `validate_sections` | transform | TextDriver | `validate_section_structure` | delegated to 095 |
| 5 | `diagnose` | transform | (composite, driver-free) | `diagnose` | composite health probe |
| 6 | `music_health` | transform | (driver-free) | `health_check` | kept from 007 |

**Total: 6 verbs covering 6 bitwize tools (1:1 in gates).**

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
    NOT from the tweet DB. Records PASSED/BLOCKED_ON via gate.check."""
    tracks = self.ctx.call("music", "list_tracks", album=album).data["tracks"]
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
    PASSED/BLOCKED_ON via gate.check."""
    state = self.ctx.get_driver("music_state")
    album_data = state.find_album(album)[0]

    # Read predicates from cluster state (all via existing verbs / drivers):
    concept_ok = album_data.get("status") in {"in-production", "mastered",
                                              "released"}
    research = self.ctx.call("music", "pending_verifications", album=album)
    research_ok = research["data"]["pending_count"] == 0
    lyrics = self.ctx.call("music", "list_tracks", album=album)
    lyrics_ok = all(t["status"] in {"recorded", "mixed", "mastered"}
                    for t in lyrics["data"]["tracks"])

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
    SERVES the album intent."""
    eng = Engine(":memory:", drivers=fake_drivers())
    intent = eng.intent_bootstrap("album X", "release", "verify provenance")

    # 1. lifecycle
    eng.call("music", "capture_idea", text="album X")
    eng.call("music", "promote_idea", idea_id=...)
    eng.call("music", "conceptualize", artist="Artist", title="X",
             type="documentary", theme="...", tracklist="t1\nt2")

    # 2. research
    eng.call("music", "dispatch_research", question="X facts",
             domains="legal,financial", album="X")
    eng.call("music", "verify_sources", album="X")

    # 3. lyrics
    eng.call("music", "lyric_report", track="t1", lyrics="...")

    # 4. audio
    eng.call("music", "master_album", album="X", target_lufs=-14)
    eng.call("music", "qc_audio", path=".../X/master.wav")

    # 5. catalogue + promo
    eng.call("music", "db_create_tweet", album="X", body="...",
             scheduled_at="...", platform="x")
    eng.call("music", "promo_copy", album="X", platform="x")
    eng.call("music", "publish_asset", key="X/master.wav", body=b"...")

    # 6. gates — release_check should now pass
    result = eng.call("music", "release_check", lifecycle_id=intent.lifecycle_id,
                      album="X")
    assert result.ok

    # 7. THE HEADLINE — provenance returns the full chain
    prov = eng.call("memory", "graph_provenance",
                    intent_id=intent.intent_id,
                    include=["Invocation", "Artefact", "Reflection",
                            "ResearchClaim", "VerificationRecord"])
    assert prov.data["invocation_count"] >= 10
    assert prov.data["artefact_count"] >= 5  # concept, master-report, qc,
                                              # tweet, promo, asset
    assert "ResearchClaim" in prov.data["node_types"]
    assert all(edge["type"] == "SERVES"
               for edge in prov.data["edges_from_root"])
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

## Followup

(Populated when the PR ships. The master 093 row moves to **Shipped** when 100
lands Green.)
