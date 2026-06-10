---
spec_id: "212"
slug: music-research-fanout
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "099"
depends_on: ["099", "180", "147", "168"]
vision_goals: [8, 4]
affects:
  - agency/capabilities/music/_main.py
  - tests/test_music_research_fanout.py
---

# Spec 212 — music research fan-out (shared research substrate)

## Why

Spec 099 (music-research) ships 9 verbs that already delegate to
`agency.research`. The research cap is itself being enhanced with
Managed-Agent fan-out (Spec 180) + server-side web tools (Spec 168).
Music research (subject investigation for concept albums — the bitwize
investigative-research pattern) should inherit those upgrades for free:
its delegation picks up the fan-out + web-driver depth without a
music-specific change.

## Done When

- [ ] **Music research delegation inherits Spec 180 fan-out + Spec 168
      web depth** — a concept-album subject investigation can dispatch
      Managed-Agent specialists.
- [ ] **No music-specific LLM code** — the upgrade lives in the shared
      research cap; music just delegates (the 099 pattern, validated).
- [ ] **Citations flow into the music catalogue** (Spec 097/210) as
      source provenance for a concept album.
- [ ] Test: a music research call uses the upgraded research path
      (mocked); citations link to the album.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 180 (research fan-out) + Spec 168 (web depth) are inherited.
- Spec 210 (catalogue query) consumes the citations.

## Open questions

1. Any music-specific specialist role? **Recommend**: reuse the shared
   roles; a `music-rights` specialist is a Slice-2 if demand appears.
