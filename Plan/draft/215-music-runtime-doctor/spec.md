---
spec_id: "215"
slug: music-runtime-doctor
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "117"
depends_on: ["117", "214", "209", "170", "206", "151"]
vision_goals: [3, 5]
affects:
  - agency/capabilities/music/_main.py
  - agency/capabilities/music/_doctor.py
  - tests/test_music_runtime_doctor.py
---

# Spec 215 — music runtime self-diagnose closure

## Why

Spec 117 (music-runtime-binding) is Partial — Slices 1+2 shipped (F1-F5
closed), but the lazy auto-wiring's failure modes (missing audio deps,
absent content_root, driver build error) surface as raw exceptions
rather than the typed `diagnose` the spec scoped. With the Managed-Agent
audio driver (Spec 209) as a fallback and the deep doctor (Spec 214),
the runtime can self-diagnose and route around a missing local
capability.

## Done When

- [ ] **`music.diagnose()` returns a typed readiness report** — typed
      shape `MusicDiagnose = {ok: bool, ready_drivers: list[str],
      missing_deps: list[MissingDep], fallback_offers: list[FallbackOffer],
      content_root_status: ContentRootStatus, recommended_action: str | None}`
      where `MissingDep = {package: str, install_cmd: str, blocks_verbs:
      list[str]}` and `FallbackOffer = {kind: Literal["managed_audio",…],
      enabling_flag: str, latency_class: Literal["fast","slow"]}`.
- [ ] **A missing local audio dep auto-suggests the Managed-Agent
      path** (Spec 209) instead of crashing — the offer carries the
      `xcap=True` flag the caller can flip.
- [ ] **Closes 117's `diagnose` scope** — the Partial flips toward
      Shipped once `music.diagnose` returns the typed report and the
      driver bootstrap path consults it before raising.
- [ ] **Diagnose-before-dispatch** — every music verb that requires a
      local driver consults `diagnose()` at entry; missing dep yields
      typed `Codes.CAPABILITY_DEGRADED` with the fallback offer in the
      error payload, not a raw `ImportError`.
- [ ] **Test**: `diagnose` reports a missing dep + the fallback offer;
      a verb call under the same conditions returns
      `Codes.CAPABILITY_DEGRADED` (never an `ImportError`).
- [ ] **TODO row + drift clean.**

## Measurable invariants (relationships, not pinned counts)

- **Diagnose ≡ doctor consistency** — every field in `MusicDiagnose`
  has a corresponding field in `MusicDoctorReport` (Spec 214); the two
  reports cannot drift.
- **No raw exception path** — `pytest --strict` over the music verbs
  with `librosa` uninstalled asserts ZERO `ImportError`/`ModuleNotFoundError`
  reaches the caller; every degraded path returns a typed `Codes.*`.
- **Fallback validity** — for every `FallbackOffer.kind`, the
  corresponding driver exists in the registry (the offer cannot point
  at a non-existent backend).
- **Recommended-action specificity** — `recommended_action` is non-None
  iff `ok=False`; when offered, it names an exact install command or
  flag to flip (no vague "install audio deps").

## Worked example (Given/When/Then)

```text
Given:  librosa not installed; soundfile not installed;
        ANTHROPIC_API_KEY set; xcap not enabled
When:   music.diagnose()
Then:   returns MusicDiagnose{ok=False,
        missing_deps=[{package:"librosa", install_cmd:"pip install
        librosa==…", blocks_verbs:["mix_track","master_track",…]},
        {package:"soundfile",…}],
        fallback_offers=[{kind:"managed_audio",
        enabling_flag:"xcap=True", latency_class:"slow"}],
        recommended_action:"Either `pip install agency[music-audio]`
        for local, or call with xcap=True to use the Managed-Agent
        backend"}
        AND a follow-up music.master_track(track_id) returns
        Codes.CAPABILITY_DEGRADED carrying the same FallbackOffer,
        NOT an ImportError
```

## Failure modes (Nygard)

| Failure | Diagnose response |
|---|---|
| `content_root` unwritable | `ok=False`, `content_root_status.writable=False`, no fallback offer (storage is local-only) |
| ALL audio paths unavailable (local missing + no API key) | `ok=False`, `fallback_offers=[]`, recommended_action names BOTH paths to enable |
| Managed-Agent reachable but Agent (Spec 137 Lock) not provisioned | offer flagged with `latency_class="slow"` AND a sub-hint to run the provisioning script |
| Network probe fails (egress blocked) | `managed_audio` not offered (would 10x latency on every call); recommended_action focuses local |
| Diagnose called from a degraded verb (recursion) | second-level diagnose is cached for 60s (avoids cascade); test asserts call-depth bound |
| Spec 214 doctor inconsistent with diagnose | install-time lint fails (drift catch) |

## Interconnects

- Spec 209 (Managed-Agent audio) is the fallback `diagnose` points to.
- Spec 214 (derived config) + Spec 170 (doctor) are the report surface;
  this verb reads them, never re-pins.
- Spec 206 (produce-album walk) calls `diagnose` before dispatch so a
  Partial walk surfaces missing deps BEFORE the lyrics phase spends
  driver tokens.
- Spec 151 (Codes coverage) supplies `CAPABILITY_DEGRADED`.

## Open questions

1. Auto-route to Managed-Agent or just suggest? **Recommend**: suggest
   (the user's egress policy governs); auto-route behind an opt-in flag.
2. Diagnose cache TTL? **Recommend**: 60s — long enough to avoid
   thrash inside one walk, short enough that a fresh `pip install`
   surfaces on the next call without a session restart.
3. Should `diagnose` probe Anthropic API liveness? **Recommend**: no —
   probing costs tokens; reading `ANTHROPIC_API_KEY` + the cached doctor
   `anthropic_extra_present` is enough. The first real call surfaces
   real-time failures via Spec 147's typed errors.
