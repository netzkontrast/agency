---
spec_id: "209"
slug: music-audio-driver-managed
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "096"
depends_on: ["096", "147", "002", "021"]
vision_goals: [8, 3]
affects:
  - agency/capabilities/music/_main.py
  - tests/test_music_audio_managed.py
---

# Spec 209 — music audio: Managed-Agent processing driver

## Why

Spec 096 (music-audio) ships 18 verbs via the FakeAudioDriver +
production AudioDriver — the heavy DSP (mixing, mastering, stem
processing) runs locally. The `claude-api` Managed-Agents surface, with
its per-session sandbox + code-execution tool, can run the DSP on
Anthropic infrastructure for users without local audio deps — the
harness-in-harness ladder (Goal 8) applied to audio. The AudioDriver
boundary (Spec 002) already exists; this adds a Managed-Agent backend.

## Done When

- [ ] **A Managed-Agent AudioDriver** behind the Spec 002 boundary —
      dispatches DSP to a session whose environment carries the audio
      packages (Spec 147 `dispatch_session`); output files come back via
      the session-outputs Files API (claude-api skill).
- [ ] **Events stream as MonitorEvents** (Spec 021).
- [ ] **FakeAudioDriver stays the CI default** (zero binaries, Spec 096).
- [ ] **Provenance identical** across backends.
- [ ] Test: the Managed-Agent driver dispatches + collects an output
      (mocked session); Fake fallback unchanged.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) — Managed-Agents bridge.
- Spec 002 (driver boundary) is the seam; Spec 021 (monitor) the stream.

## Open questions

1. Managed-Agent or local default? **Recommend**: local when audio deps
   present (faster); Managed-Agent when absent (the zero-install path).
