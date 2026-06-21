---
spec_id: "214"
slug: music-binding-derived-config
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "115"
depends_on: ["115", "117", "149", "170", "215", "209", "146"]
vision_goals: [4, 5]
affects:
  - agency/capabilities/music/_config.py
  - agency/capabilities/music/_doctor.py
  - tests/test_music_binding_derived.py
---

# Spec 214 — music binding: derived config + doctor

## Why

Spec 115 (music production-binding) wires the production drivers; Spec
117 (music-runtime-binding) closed the runtime gap with lazy
auto-wiring + `MusicConfig.bootstrap()`. The config surface
(content_root, drivers, name-exposure blocklist) is hand-maintained.
The derived-doc discipline (Spec 149) + deep doctor (Spec 170) should
extend to music: the config schema is derived, and `agency_doctor`
reports music-driver readiness so a user knows what's wired.

## Done When

- [ ] **`agency_doctor` reports music readiness** — typed report
      `MusicDoctorReport = {content_root: Path | None,
      content_root_writable: bool, drivers_wired: dict[str, DriverStatus],
      name_exposure_blocklist_size: int,
      managed_audio_available: bool, anthropic_extra_present: bool,
      max_body_tokens: int}` — every field DERIVED, none pinned.
- [ ] **The music-config schema is validated** against the live driver
      bundle — a missing driver yields a typed hint (Spec 170 pattern)
      naming the package, install command, and the doctor field that
      will flip green.
- [ ] **`MusicConfig.bootstrap()` is idempotent + reported** (extends
      Spec 117's bootstrap with doctor visibility); calling
      `bootstrap()` twice in a row is observable as a no-op via the
      doctor report's `bootstrap_invocations` counter.
- [ ] **Schema derivation lint** — running `scripts/check-doc-drift`
      catches a hand-edit to the music-config JSON schema that doesn't
      match the live `MusicConfig` dataclass.
- [ ] **Test**: doctor reports the music surface; a missing driver
      yields its hint; bootstrap idempotency holds.
- [ ] **TODO row + drift clean.**

## Measurable invariants (relationships, not pinned counts)

- **Derived parity** — for every field on `MusicConfig`, the same field
  appears in `MusicDoctorReport` with the live value; a drift test
  asserts the field-set equality.
- **Hint completeness** — for every driver kind with `wired=False`,
  the report carries a non-empty `hint` field (no silent missing).
- **Blocklist size invariance** — `name_exposure_blocklist_size ==
  len(NameExposureConfig.read().blocklist)` (the rendered field equals
  the live source — no copy-paste drift).
- **Bootstrap idempotency** — second `bootstrap()` mutates zero graph
  nodes; assertion is on `count(MusicConfigBootstrapEvent) == 1`
  after two calls.

## Worked example (Given/When/Then)

```text
Given:  content_root set + writable; LocalAudioDriver missing librosa;
        ManagedAudioDriver available; [anthropic] installed; blocklist
        contains 17 names
When:   agency_doctor()
Then:   returns AgencyDoctorReport including MusicDoctorReport with
        drivers_wired={"local_audio": {wired:False,
        hint:"pip install librosa==…"}, "managed_audio": {wired:True}}
        AND name_exposure_blocklist_size == 17
        AND anthropic_extra_present == True
        AND every field is DERIVED (no hardcoded constant)
```

## Failure modes (Nygard)

| Failure | Doctor response |
|---|---|
| `content_root` missing | `content_root=None`, `content_root_writable=False`, hint names the env var or config key to set |
| `content_root` set but unwritable (permission) | `writable=False` with the OS error in the hint |
| Driver build error (import succeeds but `__init__` raises) | `DriverStatus{wired:False, error_class:"…", error_msg:"…"}` — never silently "wired=True" |
| Blocklist file malformed | size=`None`, hint names the failing line; never silent zero (which would unblock leaks) |
| Drift detected (rendered config schema ≠ live dataclass) | `scripts/check-doc-drift` exits 1; CI blocks merge |
| Managed-audio dispatch unreachable (network down) | `managed_audio_available=False` with a network hint; never reported as "wired=True" optimistically |

## Interconnects

- **Drift-derivation chain** (149) · Spec 170 (doctor deepening).
- Spec 117 (runtime binding) is the wiring this reports.
- Spec 215 (music runtime doctor) consumes this report to drive the
  `music.diagnose()` self-routing decision.
- Spec 209 (Managed-Agent audio) supplies the `managed_audio_available`
  signal this surfaces.
- Spec 146 (output-prefix) — `max_body_tokens` is reported so users can
  reason about the output budget that controls Spec 207/210 paging.

## Open questions

1. One doctor section for music or per-cluster? **Recommend**: one
   music section — matches the single-doctor surface; per-cluster
   detail belongs under nested keys, not separate sections.
2. Where does the JSON schema render to? **Recommend**:
   `docs/guide/capabilities.md` (already generated by
   `scripts/gen-capability-docs`) — no new doc page.
3. Should the doctor report names of blocklisted entries? **Recommend**:
   NO — only the size and a hash. Blocklists may contain sensitive
   strings (talent, victims); the doctor must never leak them to a log.
