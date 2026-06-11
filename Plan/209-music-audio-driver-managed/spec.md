---
spec_id: "209"
slug: music-audio-driver-managed
status: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "096"
depends_on: ["096", "147", "002", "021", "206", "215", "151"]
vision_goals: [8, 3]
affects:
  - agency/capabilities/music/_main.py
  - agency/capabilities/music/_drivers/_managed_audio.py
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

- [ ] **A `ManagedAudioDriver(AudioDriver)`** behind the Spec 002
      boundary — dispatches DSP to a session whose environment carries
      the audio packages (Spec 147 `dispatch_session`); output files
      come back via the session-outputs Files API (claude-api skill).
      Typed return: `AudioJobResult = {job_id, output_files: list[FileRef],
      duration_s: float, driver_kind: Literal["local","managed","fake"],
      session_id: SessionId | None, monitor_events: list[NodeId]}`.
- [ ] **Events stream as MonitorEvents** (Spec 021) — every
      `agent.tool_use` / `session.status_*` becomes a graph node SERVING
      the originating intent.
- [ ] **FakeAudioDriver stays the CI default** (zero binaries, Spec 096);
      the Managed-Agent driver activates only behind `xcap=True` OR when
      Spec 215's `music.diagnose()` reports `local_audio_missing=True`.
- [ ] **Provenance identical across backends** — a Reflection / Artefact
      emitted by the Fake, Local, and Managed drivers carries the same
      `driver_kind` discriminator but the same `intent_id` + `track_id`
      shape; downstream verbs (gates, catalogue) cannot tell which ran.
- [ ] **Pre-created Agent (Spec 147 doctrine)** — the music-audio agent
      YAML is vendored at `agency/capabilities/music/agents/audio.agent.yaml`;
      CI applies via `ant beta:agents update`. The `agent_id` + `version`
      land in a Spec 137 Lock; create-once.
- [ ] **Test**: the Managed-Agent driver dispatches + collects an output
      (mocked session); Fake fallback unchanged; both return
      byte-identical `AudioJobResult` shape minus the `driver_kind` tag.
- [ ] **TODO row + drift clean.**

## Measurable invariants (relationships, not pinned counts)

- **Backend interchangeability** — for any (track, recipe) tuple, the
  shape returned by Fake / Local / Managed drivers is identical EXCEPT
  for `driver_kind`, `session_id`, and the concrete bytes of
  `output_files`. Downstream gates and catalogue verbs work without a
  branch on `driver_kind`.
- **Event-to-graph coverage** — for any Managed run, `len(monitor_events) >=
  len(SessionStatusTransitions_observed)` — every status transition
  produces at least one graph node (no silent transitions).
- **Provenance density (cross-backend)** — `count(Artefact PRODUCES
  intent_id) >= 1` regardless of backend; the moat is non-negotiable.
- **Cost-locality** — Managed driver only invoked when explicitly
  selected OR local missing: `assert driver_kind == "managed" implies
  (config.prefer_managed or not local_audio_available)`.

## Worked example (Given/When/Then)

```text
Given:  no local DSP deps; xcap=True; Agent persisted via Spec 137 Lock;
        Anthropic SDK mocked to return SessionHandle then a Files API
        download of a mastered WAV
When:   music.master_track(track_id, recipe="streaming")
Then:   returns AudioJobResult{driver_kind="managed", output_files=[WAV],
        session_id=≠None, monitor_events=[≥3 NodeIds]}
        AND analyze.graph_query("MonitorEvents SERVES intent_id") returns
        the dispatched→running→idle→terminated chain
        AND the audio-release gate (Spec 100) accepts the output unchanged
```

## Failure modes (Nygard)

| Failure | Driver response |
|---|---|
| Managed session `TIMEOUT` | typed `Codes.DRIVER_TIMEOUT`; if `music.diagnose` reports local available, suggest local fallback; never silent re-dispatch |
| Session `status_terminated` with error | typed failure; the partial Files API output is NOT collected (corruption risk) |
| `ANTHROPIC_API_KEY` absent | the driver refuses construction at boot; FakeAudioDriver remains; doctor hint surfaces |
| Files API download fails mid-stream | retry up to 3×; then typed failure with the `session_id` for forensic replay |
| Spec 137 Lock missing `agent_id` | driver refuses dispatch with `Codes.MANAGED_AGENT_NOT_PROVISIONED`; CI bootstrap step is named in the hint |
| Local DSP deps PARTIALLY present | doctor reports the missing package; driver does not silently fall back to Fake (silent fallback hides real failures) |

## Interconnects

- **LLM-driver chain** (147) — Managed-Agents bridge.
- Spec 002 (driver boundary) is the seam; Spec 021 (monitor) the stream.
- Spec 206 (produce-album walk) consumes this as the audio phase, with
  the typed `driver_kind` recorded in the walk's `WalkResult`.
- Spec 215 (music runtime doctor) drives the backend-selection decision
  via `music.diagnose()`.
- Spec 151 (Codes coverage) supplies `DRIVER_TIMEOUT` +
  `MANAGED_AGENT_NOT_PROVISIONED`.

## Open questions

1. Managed-Agent or local default? **Recommend**: local when audio deps
   present (faster); Managed-Agent when absent (the zero-install path).
2. Concurrency cap on Managed sessions? **Recommend**: a per-intent
   concurrency budget of 4 (matches Spec 147 dispatch defaults); the
   walker (Spec 206) serializes phases anyway.
3. Where does the output WAV land? **Recommend**: download via Files API
   into the user's `content_root` (Spec 117 binding) under
   `audio/<track_id>/managed_<session_id>.wav` — collision-free, audit-
   trail in the filename.
