---
spec_id: "095"
slug: music-lyrics-cluster
status: draft
state: inprogress
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["094", "093"]
affects:
  - agency/capabilities/music/clusters/lyrics.py
  - agency/capabilities/music/drivers.py        # TextDriver extensions
  - agency/capabilities/music/ontology.py       # lyric artefact schemas
  - agency/capabilities/music/data/reference/   # pronunciation guide, prosody refs
  - tests/test_music_lyrics.py
domain: music / lyrics / text-analysis
wave: 7
parent_spec: "093"
---

# Spec 095 — Music Lyrics Cluster

## Why

The lyrics cluster is the **TextDriver showcase**: 14 bitwize tools doing pure,
decidable text analysis (syllable count, rhyme detection, readability scoring,
pronunciation enforcement, section parsing, plagiarism scanning) — driver-free
in principle, but routed through TextDriver so the analysis backend can be
swapped (current bitwize uses stdlib + bundled pattern tables; agency could
later bind `pronouncing`/`textstat` if `[lyrics]` extra ships).

This cluster is the **token-economy win**: every analysis tool here is
deterministic and cheap to test. CI runs full coverage in milliseconds.

bitwize lifts a substantial body of prosody knowledge — rhyme scheme analysis,
pronunciation enforcement (homographs, foreign words, distinctive phrases),
explicit content detection, cross-track repetition — into one cluster. 095
preserves that body of work, exposing each transform as a typed verb whose
output an LLM can reason about.

## Done When

- [ ] **Verbs ship:** **14 user-facing + 4 composite gate verbs = 18
  registered** (see "Verb manifest"), covering bitwize's 14 text/lyric tools
  + the `voice-checker` skill ported as verb #14 + the 4 gate verbs the
  `lyric-writing` skill calls (Codex P2 iteration 6 — without them the
  walk crashes).
- [ ] **TextDriver extended** with 14 new methods (one per user-facing verb
  that needs external pattern tables; the gate verbs reuse the underlying
  methods); pure-stdlib fake covers all of them.
- [ ] **Artefact schemas added** to ontology: `lyric-report` (kept from 007),
  `pronunciation-report`, `prosody-report`, `cross-track-report`,
  `explicit-scan`, `voice-check`.
- [ ] **Walkable skill: `lyric-writing`** — a 6-phase workflow (draft → prosody
  → pronunciation → cross-track → explicit → finalize) with computed gates
  on prosody/pronunciation/explicit, terminal `elicit` on finalize.
- [ ] **`scripts/test-cap music_lyrics`** Green; runs in < 5 seconds.
- [ ] **No regression on `lyric_report`** (preserved from 007).
- [ ] **`TODO.md` updated;** parent (093) row notes second child shipped.

## Verb manifest

| # | Verb | Role | Driver | bitwize tool absorbed | Notes |
|---|---|---|---|---|---|
| 1 | `lyric_report` | act | TextDriver | `get_lyrics_stats` + composite | kept from 007 |
| 2 | `count_syllables` | transform | (driver-free) | `count_syllables` | kept from 007 |
| 3 | `analyze_rhyme_scheme` | transform | TextDriver | `analyze_rhyme_scheme` | returns rhyme map + diagnostics |
| 4 | `analyze_readability` | transform | TextDriver | `analyze_readability` | Flesch-Kincaid + line-length stats |
| 5 | `check_pronunciation` | transform | TextDriver | `check_pronunciation_enforcement` | flags forced phonetic spellings |
| 6 | `check_homographs` | transform | TextDriver | `check_homographs` | detects ambiguous pronunciations |
| 7 | `check_streaming_lyrics` | transform | TextDriver | `check_streaming_lyrics` | platform-safe lyric formatting |
| 8 | `check_cross_track_repetition` | transform | TextDriver | `check_cross_track_repetition` | flags album-wide line repeats |
| 9 | `check_explicit_content` | transform | TextDriver | `check_explicit_content` | rates explicit / clean / suggestive |
| 10 | `extract_distinctive_phrases` | transform | TextDriver | `extract_distinctive_phrases` | corpus uniqueness signal |
| 11 | `extract_section` | transform | TextDriver | `extract_section` | verse/chorus/bridge structural parse |
| 12 | `validate_section_structure` | transform | TextDriver | `validate_section_structure` | section-tag well-formedness |
| 13 | `scan_artist_names` | transform | TextDriver | `scan_artist_names` | guards against accidental name-drops |
| 14 | `check_voice_tells` | transform | TextDriver | (the bitwize `voice-checker` skill) | rule-based AI-tell detection (abstract-noun stacking, cliché escalation, over-explained metaphors, missing idiosyncrasy); returns `findings` list with severity per row (Warning/Info — advisory only, doesn't block any gate) |

**Total: 14 verbs covering 14 bitwize tools + 1 bitwize-skill (voice-checker) ported as a verb.**

**Internal composite gate verbs** (Codex P2 iteration 6 — registered, but
called only by walkable skill phases; counted in 093's gate-verb column for
095):

| # | Verb | Role | Composes | Called by skill |
|---|---|---|---|---|
| G1 | `prosody_gate` | effect | `analyze_rhyme_scheme` + `count_syllables` + gate.check | `lyric-writing` phase 2 |
| G2 | `pronunciation_gate` | effect | `check_pronunciation` + `check_homographs` + gate.check | `lyric-writing` phase 3 |
| G3 | `repetition_gate` | effect | `check_cross_track_repetition` + gate.check | `lyric-writing` phase 4 |
| G4 | `explicit_gate` | effect | `check_explicit_content` + gate.check | `lyric-writing` phase 5 |

**Done-When implication:** the cluster ships **14 user + 4 gate = 18
registered verbs** total. Without the gate verbs, the `lyric-writing` skill
walk crashes at "unknown verb" on the prosody / pronunciation / repetition /
explicit phases.

## Design

### TextDriver method delta

```python
class TextDriver(Boundary):
    # existing 007 methods preserved
    def syllables(self, text: str) -> int: ...           # the kept primitive
    def stats(self, text: str) -> dict: ...              # composite for lyric_report

    # new methods (095) — all stdlib + pattern tables; no external deps
    def rhyme_scheme(self, lines: list[str]) -> dict: ...
    def readability(self, text: str) -> dict: ...        # FK + extras
    def pronunciation(self, text: str, guide: dict) -> list[dict]: ...
    def homographs(self, text: str) -> list[dict]: ...
    def streaming_safe(self, text: str, platform: str) -> dict: ...
    def cross_track(self, tracks: list[str]) -> dict: ...  # tracks = list of lyric bodies
    def explicit(self, text: str) -> dict: ...
    def distinctive_phrases(self, text: str, corpus: list[str]) -> list[str]: ...
    def extract_section(self, text: str, label: str) -> str: ...
    def validate_sections(self, text: str) -> dict: ...
    def scan_artist_names(self, text: str, allow: list[str]) -> list[dict]: ...
```

The pattern tables (homograph list, pronunciation guide) live as YAML under
`agency/capabilities/music/data/reference/` and are loaded by the fake driver
on first use (memoized).

### Primary actors (panel-added, iteration 1 / Cockburn)

- `lyric-writing` — **Primary actor: agent** (drafts + revises lyrics);
  human-curator signs off at phase 6 (finalize).
- `lyric-review` (followup) — Primary actor: human-curator; agent
  presents findings.
- `pronunciation-pass` (followup) — Primary actor: agent (mechanical scan);
  human acknowledges no flags.

### Walkable skill: `lyric-writing`

```python
LYRIC_WRITING_SKILL = {
    "name": "lyric-writing",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "draft", "produces": ["lyrics_draft"]},
        {"index": 2, "name": "prosody",
         "produces": ["syllable_target_met", "rhyme_scheme_valid"],
         "gate": "computed",   # → music.analyze_rhyme_scheme + music.count_syllables
         "gate_verb": "music.prosody_gate"},
        {"index": 3, "name": "pronunciation",
         "produces": ["pronunciation_clean"],
         "gate": "computed",   # → music.check_pronunciation + music.check_homographs
         "gate_verb": "music.pronunciation_gate"},
        {"index": 4, "name": "cross-track",
         "produces": ["no_album_wide_repeats"],
         "gate": "computed",   # → music.check_cross_track_repetition
         "gate_verb": "music.repetition_gate"},
        {"index": 5, "name": "explicit",
         "produces": ["explicit_rating_assigned"],
         "gate": "computed",
         "gate_verb": "music.explicit_gate"},
        {"index": 6, "name": "finalize",
         "produces": ["lyrics_locked"],
         "gate": "hard"},      # → elicit/lifecycle_gate
    ],
}
```

The computed gates each delegate to a tiny `*_gate` verb (lifecycle cluster
pattern from 007: `pregen_check`, `release_check`). Each `*_gate` verb returns
`ToolResult.success`/`ToolResult.failure("GATE_FAILED", …)` and calls
`gate.check` to record PASSED/BLOCKED_ON.

### Artefact schemas added

```python
# In ontology.py, appended to the existing list:
LYRIC_ARTEFACTS = [
    "lyric-report",            # kept from 007
    "pronunciation-report",    # new
    "prosody-report",          # new (rhyme + syllable composite)
    "cross-track-report",      # new (album-wide repetition findings)
    "explicit-scan",           # new (per-track rating + flagged lines)
    "voice-check",             # new (placeholder for future voice-checker port)
]
```

### Pronunciation reference data

bitwize ships a `pronunciation-guide.md` that the user can override via
`{overrides}/pronunciation-guide.md`. agency's StateDriver `read_data` loads the
guide from `data/reference/pronunciation-guide.yaml`; the agent can override by
authoring a project-local `pronunciation-guide.yaml` and adding its path to the
cap's config (deferred — for now, the data file is canonical).

## Test plan

```python
# tests/test_music_lyrics.py — ~14 tests
def test_lyrics_cluster_discovers_all_verbs(): ...
def test_count_syllables_remains_driver_free_and_deterministic(): ...
def test_lyric_report_produces_artefact_with_serves_edge(): ...
def test_analyze_rhyme_scheme_returns_rhyme_map(): ...
def test_check_pronunciation_flags_known_homograph(): ...
def test_check_explicit_classifies_known_phrase(): ...
def test_check_cross_track_repetition_flags_duplicate_line(): ...
def test_extract_section_returns_named_block(): ...
def test_validate_section_structure_rejects_malformed_tags(): ...
def test_lyric_writing_skill_walks_through_computed_gates(): ...
def test_prosody_gate_blocks_lifecycle_on_syllable_mismatch(): ...
def test_pronunciation_gate_records_blocked_on_via_gate_check(): ...
def test_explicit_gate_records_passed_when_clean(): ...
def test_finalize_phase_pauses_on_hard_elicit(): ...
```

## Open questions

1. **`pronouncing`/`textstat` as optional `[lyrics]` extra?** Defer to a
   followup PR. The pattern-table approach matches bitwize's behaviour and
   keeps CI lean.
2. **Override discovery (project-local pronunciation guide)?** Per-cap config
   path (e.g. `.agency/music/pronunciation-guide.yaml`) read by StateDriver.
   Deferred — single-source-of-truth (data/) is the default; overrides land in
   a followup.
3. **`voice-checker` (AI-tell detection) — verb or skill?** **Resolved
   (Codex P2):** ported as verb #14 `check_voice_tells` (transform,
   TextDriver, rule-based) — see manifest. The bitwize skill's prose
   guidance lives in the cluster as a checker; severity stays advisory
   (returns `findings` list with severity per row, doesn't block any gate).
   `llm` driver routing remains a followup enhancement; the rule-based
   path is the v1 contract.

## Followup — Implementation Status (2026-06-09)

**Verdict:** Partial (Slice 1 shipped — all v1 verbs + skill landed; per-cluster file split deferred).

### Done (Slice 1 — branch `claude/music-095-lyrics`, stacked on PR #65)
- **TextDriver Protocol extended** (drivers.py) with 13 new methods covering the bitwize text/lyric handler shape: `stats`, `rhyme_scheme`, `readability`, `pronunciation`, `homographs`, `streaming_safe`, `cross_track`, `explicit`, `distinctive_phrases`, `extract_section`, `validate_sections`, `scan_artist_names`, `voice_tells`. All implemented on `FakeTextDriver` with deterministic pattern tables (4 homographs, 3 pronunciation entries, 5 explicit + 3 suggestive words, voice-tell heuristic set with abstract-noun-stack / cliché-escalation / missing-idiosyncrasy detectors, artist blocklist with 6 entries). Stdlib-only — no `pronouncing`/`textstat` dep.
- **12 transform verbs + 4 composite gate verbs = 16 new verbs** on `MusicCapability`:
  - Transforms: `analyze_rhyme_scheme`, `analyze_readability`, `check_pronunciation`, `check_homographs`, `check_streaming_lyrics`, `check_cross_track_repetition`, `check_explicit_content`, `extract_distinctive_phrases`, `extract_section`, `validate_section_structure`, `scan_artist_names`, `check_voice_tells`.
  - Gate verbs (effect, compose `gate.check`): `prosody_gate`, `pronunciation_gate`, `repetition_gate`, `explicit_gate`. Each returns typed `ToolResult.failure("GATE_FAILED", …)` on block + records `PASSED`/`BLOCKED_ON` on the Lifecycle.
- **`lyric-writing` walkable skill** added to OntologyExtension.skills: 6-phase workflow (`draft → prosody → pronunciation → cross-track → explicit → finalize`) ending in a hard elicit. Computed gates at phases 2-5 delegate to the matching `*_gate` verb via `gate_verb` field (engine skill walker dispatches).
- **5 NEW artefact schemas** in OntologyExtension.schemas: `pronunciation-report`, `prosody-report`, `cross-track-report`, `explicit-scan`, `voice-check` (with `[album, track, …]` required fields).
- **`tests/test_music_lyrics.py` — 20 tests** covering each transform's happy + edge cases, all 4 gates' PASSED + BLOCKED paths (the explicit gate's `allow_explicit=True` override path included), the 6-phase walker through to the hard elicit, verb auto-discovery, voice-tells flagging cliché escalation, and the section-tag title-case validator rejecting lowercase.
- **Block-mode lint clean**: `plugin.lint_capability('music')` returns `ok=True, violations=0, warnings=1` (the accepted `surface_size>12` warn — now 42 verbs total: 26 from 094 + 16 from 095).
- **Note on `count_syllables` + `lyric_report`**: kept verbatim from 007 / Slice 1 (no duplication; the spec's manifest lists them as "kept from 007").

### Still to implement (deferred)
- **Per-cluster file split**: the 16 new verbs live on `_main.py` per the atomic-migration strategy used in 094 Slice 1+2. The eventual move into `agency/capabilities/music/clusters/lyrics.py` lands as part of a future cluster-batch migration (once 095-100 all ship, do a single split PR per cluster). This is the same deferral pattern Spec 094's Followup documented.
- **Pronunciation YAML override path**: Spec §"Pronunciation reference data" notes a `data/reference/pronunciation-guide.yaml` override; for now the bundled `_PRONUNCIATION_GUIDE` dict on `FakeTextDriver` is the canonical source (3 entries — sufficient for v1 coverage). Slice 2 widens this to read from `data/reference/`.
- **`pronouncing` / `textstat` as `[lyrics]` extra**: open question §1 — defer to a follow-up PR. The pattern-table approach matches bitwize's behaviour and keeps CI lean. Mark `extras` in pyproject for the future opt-in.

### Refinement needed (given later specs)
- The 16 new verbs follow the same `try: state = self.ctx.get_driver(...) except DriverMissing: return ToolResult.failure("DEPENDENCY_MISSING", …)` pattern as 094 Slice 2's 11 verbs. The `_require_driver(name)` helper the 094 review suggested would now save ~96 lines (16 verbs × ~6 lines of boilerplate each) across the 16 verbs here plus 094's 11. Defer to a cleanup slice; not blocking.
- `surface_size>12` warn is now firing for a substantially larger surface (42 verbs). Per CLAUDE.md "field-tested heuristics" §"Dormant-surface audit", once 100 (gates) ships and the per-cluster split lands, this warn naturally drops since each cluster will carry ~5-15 verbs. Tracking it here as a non-blocking refinement.

### Evidence
- code: `agency/capabilities/music/_main.py` (16 new methods on `MusicCapability`), `drivers.py` (Protocol + FakeTextDriver), `ontology.py` (LYRIC_WRITING_SKILL + 5 schemas).
- tests: `tests/test_music_lyrics.py` (20 tests, all green); full suite Green (1004 passed).
- lint: `plugin.lint_capability('music')` → ok=True block mode, 0 violations.
- branch: `claude/music-095-lyrics` (stacked on `claude/busy-bohr-wb18pg`).
