---
spec_id: "202"
slug: skills-api-publish-managed
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "083"
depends_on: ["083", "147", "180", "199"]
vision_goals: [8, 4]
affects:
  - agency/capabilities/plugin/_main.py
  - tests/test_skills_api_managed.py
---

# Spec 202 — publish skills as Managed-Agent skills

## Why

Spec 083 publishes a cap's Agent Skill to the Anthropic Skills API. The
`claude-api` Managed-Agents surface lets a persisted Agent reference
those skills (max 20 per agent) so a Managed-Agent session loads them on
demand. This closes the harness-in-harness loop (Goal 8): an agency
capability becomes a skill a Managed Agent (Spec 180's research fan-out,
or any user agent) can use — the agency engine projecting itself onto
the Anthropic agent platform.

## Done When

- [ ] **`AttachResult` typed return** — `AttachResult = {agent_id,
      skill_id, skill_count_before, skill_count_after,
      round_trip_ok: bool, artefact_node_id, request_id}`. The verb
      raises `BAD_REQUEST{detail:"cap"}` before the attach if
      `skill_count_before >= MAX_SKILLS_PER_AGENT` (configured,
      default 20 per current Managed-Agents limit).
- [ ] **`plugin.attach_skill_to_agent(skill_id, agent_id)`** — adds a
      published skill (Spec 083) to a persisted Managed Agent (Spec 147
      create-once doctrine), respecting the cap.
- [ ] **Invariant — cap relationship**: for every agent `A`,
      `count(attached_skills(A)) <= MAX_SKILLS_PER_AGENT` is a standing
      check; a regression fails CI (not a pinned 20 — config-derived).
- [ ] **Invariant — round-trip gating** (relationship): every successful
      attach has `validate_published_skill(skill_id).trigger_fired ==
      true` (Spec 199) within the last `ROUND_TRIP_TTL` (default 24h);
      a stale validation re-triggers the round-trip.
- [ ] **Invariant — provenance edge**: every attach writes a
      `(Invocation)-[:PRODUCES]->(Artefact{type:"skill_attach"})` and a
      `(Artefact)-[:ATTACHES_TO]->(Agent)` edge — both edges are
      traversed by `analyze.graph_query` (Spec 203 / Spec 125 doctrine:
      declare an edge ⇒ traverse it).
- [ ] **The research fan-out (Spec 180) loads its specialist skills**
      this way — a specialist Agent carries the agency `research` skill;
      detach on session end (Managed-Agents create-once survives).
- [ ] **Failure mode coverage** — Skills-API REFUSAL / NOT_FOUND /
      AGENT_VERSION_MISMATCH each yield typed errors; the partial-attach
      state is rolled back via Spec 137 Lock (idempotent).
- [ ] Test: attach respects the cap; a non-validated skill is refused;
      a stale round-trip re-triggers; provenance edges are queryable.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  agent "research-specialist" persisted via Spec 137 Lock with
        skill_count_before = 5 AND skill "agency.research" has a
        validate_published_skill report with trigger_fired=true,
        validated 2h ago (< ROUND_TRIP_TTL)
When:   plugin.attach_skill_to_agent("agency.research",
                                     "research-specialist") runs
Then:   AttachResult{round_trip_ok:true, skill_count_after: 6,
                    artefact_node_id: "art_..."}
        AND graph has (Invocation)-[:PRODUCES]->(Artefact)
            -[:ATTACHES_TO]->(Agent)
        AND analyze.graph_query "ATTACHES_TO research-specialist"
            returns the new edge

Given:  agent already has MAX_SKILLS_PER_AGENT skills attached
When:   attach_skill_to_agent is called
Then:   raises BAD_REQUEST{detail:"cap"} BEFORE any Skills-API call
        AND no provenance edge is written (no partial state)

Given:  Skills-API returns AGENT_VERSION_MISMATCH mid-attach
When:   attach runs
Then:   typed error returned; any partial Skills-API state rolled back
        via Spec 137 Lock; AttachResult NOT written; reflection emitted
```

## Failure modes (Nygard)

| Failure | Attach response |
|---|---|
| Skills-API `REFUSAL` | typed error; no provenance edge; never retry same request |
| Skills-API `RATE_LIMITED` | retry per Spec 147 budget; on exhaustion, typed error |
| Skills-API `NOT_FOUND` (skill or agent) | typed `BAD_REQUEST{detail:"not_found"}`; doctor hint |
| `AGENT_VERSION_MISMATCH` (Spec 147 create-once violated) | typed error; require re-resolution via Spec 137 Lock |
| Cap exceeded | rejected BEFORE Skills-API call; cheap fast-fail |
| Round-trip stale (> TTL) | auto-re-validate; on validation fail, refuse attach |
| Network outage mid-attach | Spec 137 Lock rollback; no orphan attached state |

## Interconnects

- **LLM-driver chain** (147) — Managed-Agents bridge + create-once.
- Spec 180 (research fan-out) is the first consumer.
- Spec 199 (publish round-trip) gates the attach.
- Spec 137 (canon-locks) stores Agent persistence + rollback state.
- Spec 203 (graph query) — the ATTACHES_TO edge is queryable as
  first-class provenance.
- Spec 170 (doctor) reports Managed-Agents readiness + per-agent skill
  counts.
- Spec 257 (managed-agents cache proof) re-verifies attach state across
  session boundaries.

## Open questions

1. Anthropic or custom skill type? **Recommend**: custom (`skill_id`
   from the Skills API, claude-api skill); the agency skills are
   project-specific, not Anthropic's prebuilt set.
2. Detach policy when an agent rotates? **Recommend**: detach + re-attach
   in a single Spec 137 Lock transaction; never leave dangling skills on
   a stale agent version.
3. Cap is a constant — what when Anthropic raises it? **Recommend**:
   `MAX_SKILLS_PER_AGENT` reads from the live Managed-Agents capability
   probe at startup, falling back to a documented default; never pinned
   to a snapshot (CLAUDE.md rule 8).
