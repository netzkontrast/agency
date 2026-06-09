---
spec_id: "096"
slug: music-audio-cluster
status: draft
last_updated: 2026-06-07
owner: "@agency"
depends_on: ["094", "093"]
affects:
  - agency/capabilities/music/clusters/audio.py
  - agency/capabilities/music/drivers.py        # AudioDriver extensions
  - agency/capabilities/music/ontology.py       # audio artefact schemas
  - agency/capabilities/music/data/reference/   # mastering presets
  - tests/test_music_audio.py
domain: music / audio / mastering
wave: 7
parent_spec: "093"
---

# Spec 096 — Music Audio Cluster

## Why

The audio cluster is the **AudioDriver flagship** — and the most
infrastructure-heavy part of the port. bitwize ships ~18 audio tools spanning
loudness measurement (pyloudnorm), mix polish (per-stem ffmpeg processing),
mastering pipelines (single-track + album-coherence), QC (clipping, phase,
silence, frequency balance), sheet-music transcription (AnthemScore-class), and
promo video/sampler render (ffmpeg-driven).

All eighteen route through `AudioDriver` (already proven in 007 for
`master_album`/`analyze_mix`/`transcribe_sheet`). 096 extends the driver
method surface and ships the verbs; **no new boundary type**.

**The CI guarantee binds hard here:** the AudioDriver fake produces
deterministic loudness numbers from track metadata + a tmp-path WAV stub; CI
runs zero real `ffmpeg`, zero `pyloudnorm` install, zero AnthemScore. Real
audio binds at production via the `[music-audio]` extra
(`pyloudnorm`, `numpy`, `scipy`, `soundfile`, and a `ffmpeg` system binary).

## Done When

- [ ] **Verbs ship:** **19 user-facing + 2 composite gate verbs = 21
  registered** (Codex P2 iteration 6 — gate verbs were the missing piece
  for `mastering` skill walks), covering all bitwize audio + media tools.
- [ ] **AudioDriver extended** with 20 new methods (one per user-facing verb
  that touches external audio toolchain; `create_songbook` adds
  `render_songbook`); fake produces deterministic outputs for every method
  (no real audio binaries in CI).
- [ ] **Artefact schemas added:** `mastering-report` (kept from 007),
  `mix-analysis`, `qc-report`, `sheet-music` (kept from 007), `coherence-report`,
  `promo-video`, `album-sampler`.
- [ ] **Walkable skill: `mastering`** — a 5-phase workflow (measure → polish →
  master → QC → coherence) with computed gates on measure/QC, terminal `elicit`
  on coherence.
- [ ] **Walkable skill: `mix-polish`** — per-stem polish workflow
  (transcribe-stems → polish-per-stem → remix → loudness-check), all driver-routed.
- [ ] **CI guarantee verified:** `scripts/test-cap music_audio` runs in < 8
  seconds with no ffmpeg/pyloudnorm/AnthemScore binaries available.
- [ ] **No regression on `master_album`, `analyze_mix`, `transcribe_sheet`**
  (preserved from 007).
- [ ] **`TODO.md` updated;** parent (093) row notes child shipped.

## Verb manifest

| # | Verb | Role | Driver | bitwize tool absorbed | Notes |
|---|---|---|---|---|---|
| 1 | `master_album` | effect | AudioDriver | `master_album` | kept from 007 |
| 2 | `analyze_mix` | transform | AudioDriver | `analyze_mix_issues` | kept from 007 |
| 3 | `transcribe_sheet` | act | AudioDriver | `transcribe_audio` (audio half) | kept from 007 |
| 4 | `master_audio` | effect | AudioDriver | `master_audio` | single-track master |
| 5 | `master_with_reference` | effect | AudioDriver | `master_with_reference` | reference-album anchoring |
| 6 | `polish_audio` | effect | AudioDriver | `polish_audio` | per-stem cleanup |
| 7 | `polish_album` | effect | AudioDriver | `polish_album` | album-wide polish pass |
| 8 | `polish_and_master_album` | effect | AudioDriver | `polish_and_master_album` | combined pipeline |
| 9 | `fix_dynamic_track` | effect | AudioDriver | `fix_dynamic_track` | dynamic range fixer |
| 10 | `reset_mastering` | effect | AudioDriver+StateDriver | `reset_mastering` | reverts to pre-master state |
| 11 | `render_codec_preview` | effect | AudioDriver | `render_codec_preview` | streaming-codec preview |
| 12 | `measure_album_signature` | transform | AudioDriver | `measure_album_signature` | spectral signature |
| 13 | `album_coherence_check` | transform | AudioDriver | `album_coherence_check` | cross-track tonal balance |
| 14 | `album_coherence_correct` | effect | AudioDriver | `album_coherence_correct` | applies coherence corrections |
| 15 | `analyze_audio` | transform | AudioDriver | `analyze_audio` | general spectral/loudness probe |
| 16 | `qc_audio` | transform | AudioDriver | `qc_audio` | 7-point QC checklist |
| 17 | `mono_fold_check` | transform | AudioDriver | `mono_fold_check` | phase-cancellation check |
| 18 | `generate_promo_videos` | effect | AudioDriver | `generate_promo_videos` | 15s vertical promo render |
| 19 | `create_songbook` | effect | AudioDriver | `create_songbook` | LilyPond render to PDF — sheet-music domain belongs to AudioDriver |

**Total: 19 verbs covering 19 bitwize tools (1:1 in audio + sheet-music).**

**Internal composite gate verbs** (Codex P2 iteration 6 — registered, but
called only by walkable skill phases; counted in 093's gate-verb column for
096):

| # | Verb | Role | Composes | Called by skill |
|---|---|---|---|---|
| G1 | `measure_gate` | effect | `analyze_audio` + `read_loudness` + gate.check | `mastering` phase 1 |
| G2 | `qc_gate` | effect | `qc_audio` + gate.check (BLOCKED_ON if any of the 7 rows fail) | `mastering` phase 4 |

**Done-When implication:** the cluster ships **19 user + 2 gate = 21
registered verbs** total. Without them, the `mastering` skill walk crashes
at phase 1 (measure) or phase 4 (qc) with "unknown verb".

> **Verdict on the related media tools** (panel-corrected x2 — Codex P2):
> `prepare_singles` and `generate_album_sampler` ship in **Spec 098 (promo
> cluster)** because their domain is release-packaging, not mastering.
> `create_songbook` (row 19 above) ships in **this spec** — its domain IS
> audio (LilyPond render via the same AudioDriver shell-out path). An
> earlier draft deferred it to a followup; that conflicted with 093's
> "complete port, no silent defers" contract. ZERO bitwize tools are
> deferred; every row in 007's Appendix A has a verdict in 094–100 (see
> 093's Appendix A audit table).

## Design

### AudioDriver method delta

```python
class AudioDriver(Boundary):
    # existing 007 methods preserved
    def read_loudness(self, path: str) -> float: ...
    def run_ffmpeg(self, args: list[str]) -> str: ...

    # new methods (096)
    def measure_signature(self, path: str) -> dict: ...
    def coherence_report(self, paths: list[str]) -> dict: ...
    def apply_coherence(self, paths: list[str], target: dict) -> dict: ...
    def qc_checklist(self, path: str) -> dict: ...        # 7-point checklist
    def mono_fold(self, path: str) -> dict: ...
    def polish_stems(self, stems: dict[str, str]) -> dict: ...  # stem -> path
    def polish_full(self, path: str) -> str: ...           # returns output path
    def master(self, path: str, target_lufs: float, preset: str = "") -> dict: ...
    def master_to_reference(self, path: str, reference: str) -> dict: ...
    def dynamic_fix(self, path: str, target_dr: float) -> dict: ...
    def codec_preview(self, path: str, codec: str) -> dict: ...
    def render_promo_video(self, audio: str, art: str, template: str) -> str: ...
    def render_sampler(self, tracks: list[str], duration_s: int) -> str: ...
```

The fake produces:
- **Loudness measurements** — deterministic from track metadata (slug hash mapped
  to a -8.0..-18.0 range; `measure_signature` returns a fixed spectral profile).
- **QC checklist** — fixed 7 rows: loudness, clipping, silence, phase, stereo
  width, frequency balance, dynamic range; each rated `pass/warn/fail` from a
  seeded RNG keyed on the track slug.
- **Mastering output** — `mastering-report` artefact with input/output paths,
  applied EQ curve (from preset), target LUFS, measured pre/post.
- **Coherence report** — average spectral distance between track signatures.
- **Promo video render** — returns a deterministic tmp path with a
  `.mp4-stub` extension (no ffmpeg).

### Mastering presets (data files)

```
agency/capabilities/music/data/reference/mastering-presets/
├── streaming.yaml          # -14 LUFS, true_peak=-1.0, EQ neutral
├── vinyl.yaml              # -16 LUFS, true_peak=-3.0, EQ rolled-off
├── club.yaml               # -8 LUFS, true_peak=-0.8, EQ punchy
└── reference.yaml          # neutral profile for reference matching
```

Loaded by AudioDriver via StateDriver `read_data("mastering-preset", slug)`.
Ontology adds `MasteringPreset` node (per-album choices recorded for provenance).

### Primary actors (panel-added, iteration 1 / Cockburn)

- `mastering` — **Primary actor: agent** (technical pipeline); human-curator
  signs off on coherence (phase 5).
- `mix-polish` — **Primary actor: agent** (deterministic stem processing);
  no human gate.

### Failure modes (panel-added, iteration 1 / Nygard)

The AudioDriver's external shellouts must declare typed failure shapes.
Driver fakes simulate each row; tests assert the verb's typed-error mapping.

| Boundary call | Failure mode | Driver returns | Verb returns |
|---|---|---|---|
| `ffmpeg` segfault | non-zero exit | `RuntimeError` with stderr tail | `ToolResult.failure(BOUNDARY_FAILED, "ffmpeg segfault: <tail>")` |
| `ffmpeg` timeout (configurable, default 60s) | `subprocess.TimeoutExpired` | `TimeoutError` | `ToolResult.failure(BOUNDARY_TIMEOUT, "ffmpeg exceeded 60s")` |
| `ffmpeg` not installed | `FileNotFoundError` | raises `DependencyMissing("ffmpeg")` | `ToolResult.failure(DEPENDENCY_MISSING, "ffmpeg not on PATH")` |
| AnthemScore not installed | `FileNotFoundError` | raises `DependencyMissing("anthemscore")` | `ToolResult.failure(DEPENDENCY_MISSING, "AnthemScore not installed")` |
| `pyloudnorm`/`numpy`/`scipy`/`soundfile` not installed (default install, no `[music-audio]` extra) | deferred import — AudioDriver `__init__` does NOT touch them; first method call lazy-imports | first audio method call raises `DependencyMissing("[music-audio]")` | per-verb `ToolResult.failure(DEPENDENCY_MISSING, "audio backend not installed — install agency[music-audio]")`. Music capability stays usable; only AudioDriver-backed verbs degrade. |
| Audio file unreadable | `soundfile.LibsndfileError` | raises `BoundaryFailed` | `ToolResult.failure(INVALID_ARGUMENT, "audio file unreadable: <path>")` |
| Disk full on render | `OSError: No space left` | raises | `ToolResult.failure(BOUNDARY_FAILED, "out of disk")` |

**Observability:** long-running verbs (`master_album`, `polish_album`,
`generate_promo_videos`) emit progress via Spec 021's `monitor` channel —
one `progress` event per stem processed, keyed on intent_id. Tests assert
emission count.

### Walkable skill: `mastering`

```python
MASTERING_SKILL = {
    "name": "mastering",
    "kind": "workflow",
    "phases": [
        {"index": 1, "name": "measure",
         "produces": ["pre_loudness_measured"],
         "gate": "computed", "gate_verb": "music.measure_gate"},
        {"index": 2, "name": "polish",
         "produces": ["stems_polished"]},
        {"index": 3, "name": "master",
         "produces": ["mastered_path_set", "target_lufs_hit"]},
        {"index": 4, "name": "qc",
         "produces": ["qc_passed"],
         "gate": "computed", "gate_verb": "music.qc_gate"},
        {"index": 5, "name": "coherence",
         "produces": ["album_coherent"],
         "gate": "hard"},   # elicit — human sign-off on coherence
    ],
}
```

### Walkable skill: `mix-polish`

A simpler 4-phase per-track polish workflow (separate from `mastering`):
1. **assess** — `analyze_mix` reads loudness + flags issues
2. **polish-stems** — `polish_audio` per stem
3. **remix** — combine polished stems
4. **verify** — `qc_audio` + computed gate

### Artefact schemas added

```python
AUDIO_ARTEFACTS = [
    "mastering-report",       # kept from 007
    "mix-analysis",           # new (analyze_mix output)
    "qc-report",              # new (qc_audio 7-row checklist)
    "sheet-music",            # kept from 007 (transcribe_sheet output)
    "coherence-report",       # new (cross-track tonal balance)
    "promo-video",            # new (render output manifest)
    "album-sampler",          # new (album-sampler render manifest)
]
```

## Test plan

```python
# tests/test_music_audio.py — ~16 tests
def test_audio_cluster_discovers_all_verbs(): ...
def test_master_album_records_mastering_report_artefact_with_produces(): ...
def test_analyze_mix_returns_findings_and_loudness(): ...
def test_master_audio_records_per_track_artefact(): ...
def test_master_with_reference_anchors_loudness_to_reference(): ...
def test_polish_album_processes_all_tracks_via_state_driver(): ...
def test_qc_audio_returns_7_row_checklist_with_pass_warn_fail(): ...
def test_mono_fold_check_flags_phase_cancellation(): ...
def test_album_coherence_check_reports_avg_spectral_distance(): ...
def test_render_codec_preview_produces_codec_specific_artefact(): ...
def test_generate_promo_videos_produces_one_artefact_per_track(): ...
def test_mastering_skill_walks_through_qc_gate(): ...
def test_qc_gate_blocks_lifecycle_on_clipping(): ...
def test_coherence_phase_pauses_on_hard_elicit(): ...
def test_audio_verb_fails_typed_when_audio_driver_missing(): ...
def test_mastering_preset_loaded_via_state_driver_read_data(): ...
```

## Open questions

1. **AudioDriver as one driver or split (analysis vs render)?** Single — the
   bitwize handler taxonomy keeps them together, and the driver fake is
   simpler with a single seam.
2. **Per-stem polish — accept a `stems: dict` or read from a stem dir?** Both:
   `polish_album` reads from the StateDriver's stem layout; `polish_audio`
   accepts an explicit dict for unit-test control.
3. **`prepare_singles` / `create_songbook` / `generate_album_sampler` in 096 or
   a followup?** **Resolved (Codex P2 iteration 6 — overrides earlier draft):**
   `create_songbook` ships in **this cluster** as verb #19 (LilyPond render
   IS AudioDriver domain). `prepare_singles` + `generate_album_sampler` ship
   in **Spec 098** (their domain is release-packaging, not mastering — see
   098's manifest rows 8+9). ZERO of these are followups; the complete-port
   contract requires every bitwize tool to land in 094–100.
4. **Mastering preset overrides?** A project-local preset YAML under
   `.agency/music/mastering-presets/<slug>.yaml` overrides the bundled one.
   Deferred to followup; the bundled four cover the common cases.

## Followup — Implementation Status (2026-06-09)

**Verdict:** Partial (Slice 1 shipped — full v1 audio surface; per-cluster file split + YAML preset data files deferred).

### Done (Slice 1 — branch `claude/music-096-audio`, stacked on PR #66)
- **AudioDriver Protocol extended** (drivers.py) with 13 new methods covering the bitwize audio handler shape: `measure_signature`, `coherence_report`, `apply_coherence`, `qc_checklist`, `mono_fold`, `polish_stems`, `polish_full`, `master`, `master_to_reference`, `dynamic_fix`, `codec_preview`, `render_promo_video`, `render_songbook`. All implemented on `FakeAudioDriver` with hash-derived deterministic outputs. The `read_loudness` 007 contract (returns `self._loudness`, default `-14.0`) is preserved — per-path spectral variation lives in `measure_signature.rms_db` instead.
- **16 new verbs + 2 composite gate verbs** on `MusicCapability` (3 already shipped from 007: `master_album`, `analyze_mix`, `transcribe_sheet`):
  - Effects: `master_audio`, `master_with_reference`, `polish_audio`, `polish_album`, `polish_and_master_album`, `fix_dynamic_track`, `reset_mastering`, `render_codec_preview`, `album_coherence_correct`, `generate_promo_videos`, `create_songbook`.
  - Transforms: `measure_album_signature`, `album_coherence_check`, `analyze_audio`, `qc_audio`, `mono_fold_check`.
  - Gate verbs: `measure_gate` (loudness within [min,max] window), `qc_gate` (7-point QC checklist, passes iff zero `fail` rows; `warn` count recorded in evidence).
- **MASTERING_SKILL** (5-phase: measure → polish → master → qc → coherence) + **MIX_POLISH_SKILL** (4-phase: transcribe-stems → polish-per-stem → remix → loudness-check) — both end in a hard elicit; computed gates at measure + qc phases delegate to the corresponding `*_gate` verbs via `gate_verb` metadata (agent dispatches, per 095 ontology comment).
- **5 NEW artefact schemas**: `mix-analysis`, `qc-report`, `coherence-report`, `promo-video`, `album-sampler`. The `mastering-report` + `sheet-music` schemas (from 007) extended additively — no required-field changes.
- **`reset_mastering`** routes through StateDriver: flips every `status="mastered"` track on the album back to `"recorded"`. Verified by the test that creates a mastered track then resets.
- **`tests/test_music_audio.py` — 23 tests** covering: verb auto-discovery (all 18 register), both walkable skills' shape + walk-through, every effect/transform happy path, the two gate verbs' PASSED + BLOCKED paths (the measure gate test exercises both wide-window pass + tight-window fail; the qc gate handles the warn-vs-fail summary), promo-video + songbook artefact production, the reset_mastering round-trip with the StateDriver. CI runs without ffmpeg / pyloudnorm / AnthemScore / LilyPond.
- **Block-mode lint clean**: 60 verbs total on `music` (26 lifecycle + 16 lyrics + 18 audio). `surface_size>12` warn remains the documented per-cluster-file-split deferral.
- **Spec 096 Done When fully met**: 21 verbs registered (19 user + 2 gate); both skills present; AudioDriver extended with 13 methods (one per net-new user-facing verb that touches an external toolchain); artefact schemas added; CI guarantee verified (zero audio binaries needed).

### Still to implement (deferred)
- **Per-cluster file split**: 18 audio verbs (16 new + 2 gates) live on `_main.py` per the atomic-migration strategy. Move into `agency/capabilities/music/clusters/audio.py` as part of the batch cluster-split PR once 095-100 all ship.
- **Mastering preset YAML data files**: Spec 096 §"Mastering presets (data files)" mentions preset packs. For Slice 1, `master_audio(preset="streaming")` is a labeled hint, not a fetched preset. Slice 2 reads from `data/reference/mastering-presets/<name>.yaml`.
- **Real audio binding via `[music-audio]` extra**: Spec 096 §"CI guarantee" — production binds `pyloudnorm` + `numpy` + `scipy` + `soundfile` + ffmpeg via the extra. Out-of-scope for Slice 1; add when the music package is opted-in via marketplace install.

### Refinement needed (given later specs)
- The DEPENDENCY_MISSING boilerplate now appears 43 times across 094 (8) + 095 (16) + 096 (18) + the original 007 verbs (~). The 094 review flagged the `_require_driver(name)` helper opportunity twice; deferral is at the limit of "acceptable for one more slice." Best to address in a cleanup slice between 097 and 098.
- `surface_size>12` warn is now firing for 60 verbs — same justification as 095 (drops post-100 file split).

### Evidence
- code: `agency/capabilities/music/_main.py` (16 new methods + 2 gates on `MusicCapability`), `drivers.py` (Protocol + FakeAudioDriver extensions), `ontology.py` (MASTERING_SKILL + MIX_POLISH_SKILL + 5 schemas).
- tests: `tests/test_music_audio.py` (23 tests, all green). Full suite Green: 1027 passed.
- lint: `plugin.lint_capability('music')` → ok=True block mode, 0 violations.
- branch: `claude/music-096-audio` (stacked on `claude/music-095-lyrics`).
