---
spec_id: "083"
slug: publish-skill-api
status: shipped
last_updated: 2026-06-06
owner: "@agency"
depends_on: ["080"]   # the emitted per-capability Agent Skills
research_first: true
domain: capability
wave: 5
---

# Spec 083 — Publish capability skills via the Anthropic Skills API

## Why

Spec 080 made every capability *emit* a spec-faithful Agent Skill (SKILL.md +
`references/` + `scripts/`). Today those skills are consumable only by **Claude Code**
(filesystem discovery). The Anthropic **Skills API** (`POST /v1/skills` +
`/v1/skills/{id}/versions`, beta `skills-2025-10-02`) *uploads* custom skills
workspace-wide, making them usable by the **Claude API** and **Managed Agents** (and
claude.ai). Publishing turns an agency capability into a first-class Agent Skill on
**any** Claude surface — the distribution capstone of 080 (reflection
`reflection:33811f09`).

## Research first

- The `/v1/skills` create + version wire shape (zip package layout: SKILL.md at root
  + `references/` + `scripts/`), required beta headers, and the SDK binding
  (`client.beta.skills.*`). Record as a reflection.
- Versioning model: re-publishing a capability whose verbs changed → a new skill
  **version** (mirror agency's own bi-temporal `SUPERSEDED_BY` trail).
- Auth: `ANTHROPIC_API_KEY`; behaviour when absent (dry-run package, no upload).

## Design (provisional)

1. **`plugin.publish_skill(cap_name, dry_run=True)`** (effect) — builds the skill
   package for one capability from the live emit pipeline (`emit_skill` +
   `emit_references` + bundled `scripts/`), zips it, and `dry_run` returns the
   manifest; otherwise uploads via `client.beta.skills.create` / `.versions.create`,
   recording a `Published{skill_id, version}` Artefact that SERVES the intent.
2. **Boundary.** A stubbable `SkillsClient` (like `jules_client`) so tests never hit
   the network; `agency_doctor` reports whether publishing is configured.
3. **Idempotent versioning.** Re-publish detects an existing skill by name → creates
   a version, not a duplicate; the new Artefact `SUPERSEDED_BY`-trails the prior.

## Done When

- [ ] Research report recorded.
- [ ] `plugin.publish_skill` packages a capability's full skill triad; `dry_run`
  returns the manifest; upload path records a `Published` Artefact + provenance.
- [ ] `SkillsClient` boundary (stub in tests); `[publish]` extra + drift tag.
- [ ] Tests: package shape (SKILL.md at root + references), dry-run manifest,
  stubbed upload records provenance, re-publish supersedes. `pytest` green; drift clean.

## Spec-panel critique

- **Doctrine (effect role + provenance):** uploading is an external side effect —
  MUST be `role: "effect"`, recorded as an Artefact with SERVES + OBSERVED_DURING,
  and gated behind explicit intent (no silent publish). *Accepted.*
- **Safety:** publishing pushes to an external workspace — `dry_run=True` default,
  explicit opt-in to upload; confirm before first real publish. *Accepted.*
- **Scope creep:** don't build a full sync/lifecycle manager — v1 is create + version
  for ONE capability, on demand. *Accepted: single-cap, on-demand.*
- **Skeptic:** is workspace publishing worth it vs just shipping the Claude Code
  plugin? *Yes — it's the only path to agency capabilities inside Managed Agents /
  the API, which is where the 079 non-MCP-agent + hosted-agent themes converge.*

**Verdict:** APPROVE — effect+provenance, dry-run default, single-cap v1.

## Followup — Implementation Status (2026-06-06)

**Verdict:** Shipped (boundary + verb + provenance; live SDK binding noted for
first real publish).

- **`SkillsClient`** (`plugin/_skills_client.py`) — lazy boundary: zips the package
  + uploads via `client.beta.skills.create` / `.versions.create`; raises a clear
  error without the `anthropic` SDK / `ANTHROPIC_API_KEY` (never imports `anthropic`
  by default). Engine injects it as `skills_client` (param + `injectors`), stubbed
  in tests.
- **`plugin.publish_skill(name, dry_run=True)`** [role=effect] — packages the
  capability's emitted skill via `emit_skill` + `emit_references`, re-rooted to the
  Agent-Skills layout (SKILL.md at root + `references/`). `dry_run` (default) returns
  the manifest (`files`, `bytes`); `dry_run=False` uploads and records a
  `published-skill` Artefact (SERVES + OBSERVED_DURING). Emitted skill name is
  spec-legal hyphens (`skill_generator` → `skill-generator`).
- **`[publish]` extra** (anthropic SDK); optional — dry-run works offline.
- **Tests** — `tests/test_publish_skill.py` (4): dry-run manifest (no upload),
  upload packages + records provenance, underscore→hyphen name, unknown-cap error.
  Full suite green; `check-drift` clean; install regen committed.
- **Deferred:** verify the exact `client.beta.skills` zip-field binding against the
  live SDK on first real publish; re-publish-as-version (SUPERSEDED_BY trail).
