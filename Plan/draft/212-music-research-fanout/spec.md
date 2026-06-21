---
spec_id: "212"
slug: music-research-fanout
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "099"
depends_on: ["099", "180", "147", "168", "210", "206", "150"]
vision_goals: [8, 4]
affects:
  - agency/capabilities/music/_main.py
  - agency/capabilities/music/clusters/research.py
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
      Managed-Agent specialists (legal/financial/journalism/biographical/
      historical — mirroring the bitwize-music researcher specialists)
      via the shared `research.fan_out` surface. Typed return:
      `MusicResearchResult = {album_id, subject: str, citations:
      list[CitationRef], specialist_runs: list[SpecialistRunRef],
      catalogue_links: list[NodeId], total_tokens: int}`.
- [ ] **No music-specific LLM code** — the upgrade lives in the shared
      research cap; music just delegates (the 099 pattern, validated).
- [ ] **Citations flow into the music catalogue** (Spec 097/210) as
      source provenance for a concept album — each citation node
      `SUPPORTS` the album intent and is queryable through Spec 210.
- [ ] **Reflections record specialist selection** (Spec 150) so the
      dogfood loop can amend the specialist routing over time.
- [ ] **Test**: a music research call uses the upgraded research path
      (mocked); citations link to the album; specialist-run count
      matches the requested specialist set.
- [ ] **TODO row + drift clean.**

## Measurable invariants (relationships, not pinned counts)

- **Zero music-specific LLM surface** — `grep -r "AnthropicDriver" in
  agency/capabilities/music/clusters/research.py` returns 0 lines; the
  delegation is the only code path (drop-in bar, CLAUDE.md).
- **Citation-to-catalogue density** — for every successful return,
  `count(citations) > 0` AND `len(catalogue_links) == len(citations)`
  (every citation lands as a catalogue node — no orphans).
- **Specialist coverage** — `set(run.specialist for run in
  specialist_runs) ⊆ shared_research_specialists` (no music-private
  specialist; if music needs one, Spec 099 must add it to the shared
  registry first).
- **Fan-out cost-locality** — `total_tokens ==
  sum(run.usage.total_tokens for run in specialist_runs)` (no hidden
  music-tier spend).

## Worked example (Given/When/Then)

```text
Given:  album_id with subject="2008 financial crisis"; request specialists=
        ["financial","historical","journalism"]; Spec 180 fan-out mocked
        to dispatch 3 Managed-Agent sessions returning 4, 6, 3 citations
        respectively
When:   music.research_subject(album_id, "2008 financial crisis",
        specialists=["financial","historical","journalism"])
Then:   returns MusicResearchResult with citations of length 13,
        specialist_runs of length 3, catalogue_links of length 13
        AND analyze.graph_query("Citations SUPPORTS album_id") returns
        the same 13 nodes
        AND no AnthropicDriver import inside the music research module
```

## Failure modes (Nygard)

| Failure | Verb response |
|---|---|
| One specialist `RATE_LIMITED` | partial return: completed specialists' citations land; the failed one carries a typed `SpecialistRunRef.status=rate_limited` so the caller retries |
| All specialists fail | typed failure; NO orphan citations land (atomic per specialist, but the verb returns a clean failure if zero produce) |
| Citation source webfetch refused (server-side web tool) | the citation is dropped from the run with a Reflection scoped to the URL; never silently included as broken |
| Catalogue link write fails for a citation | the citation IS returned but `catalogue_links` is shorter than `citations` — invariant test catches this immediately |
| `[anthropic]` extra missing | the shared research cap degrades (Spec 099 already specifies the scaffold path); music inherits unchanged |

## Interconnects

- Spec 180 (research fan-out) + Spec 168 (web depth) are inherited.
- Spec 210 (catalogue query) consumes the citations.
- Spec 147 (AnthropicDriver) — the shared research cap calls this,
  music never does.
- Spec 206 (produce-album walk) runs research as a creative-prep phase
  before lyrics.
- Spec 150 (dogfood) — specialist selection is a learnable parameter.

## Open questions

1. Any music-specific specialist role? **Recommend**: reuse the shared
   roles; a `music-rights` specialist is a Slice-2 if demand appears.
2. Where does the album-subject prompt live? **Recommend**: shared
   research cap holds the specialist prompts; music supplies only the
   subject string + the album context — no prompt drift across domains.
3. Should music auto-select specialists from the subject? **Recommend**:
   yes, behind a `auto_specialists=True` flag delegated to the shared
   research cap's selector (Spec 026 `llm_select` Matcher) — music
   never owns selection logic.
