---
spec_id: "375"
slug: pillar-skills
status: partial
state: draft
last_updated: 2026-06-22
owner: "@agency"
vision_goals: [3]
depends_on: ["371", "373"]
parent_spec: "370"
domain: skills
---

# Spec 375 — The 3 pillar skills (intent · lifecycle · memory)

> Child 5 of Spec 370. The three non-capability concepts of CORE.md's four become
> first-class, self-contained skills — so an agent can learn each pillar, not just
> each capability.

## Why
Agency emits a skill per capability but NONE for the concepts themselves. Intent,
Lifecycle and Memory are the spine every capability rides; an agent needs a skill
that teaches each.

## Design (sketch)
- Three `type: pillar` skills authored as committed `skill.yaml` (via 374 or by
  hand), rendered by the per-type pillar template (373):
  - **intent** — bootstrap → clarify/confirm → the clarity gate; how every session
    serves an intent; the critical-thinking methods.
  - **lifecycle** — open · move · close + read/find/check/watch; the A2A transition
    table; agent-as-parameterization.
  - **memory** — record/recall/link; the bi-temporal graph; provenance edges.
- A generation path for pillar skills (they aren't a `capabilities/<cap>/` folder —
  they're concept skills); `install.generate` emits them alongside the per-cap skills.
- Each is self-contained (A1) with one-deep references into the relevant substrate.

## Slices (TDD)
1. The pillar-skill source location + generation wiring.
2. Author the three pillar `skill.yaml` (intent, lifecycle, memory) + render them.

## Acceptance
- `skills/intent`, `skills/lifecycle`, `skills/memory` render as self-contained
  pillar skills (type=pillar), each teaching its concept with a real example.
- They appear in `agency_welcome` / the skill listing.

## Followup — Implementation Status (2026-06-22)

**Slice 1 — SHIPPED: source location + loader + per-type pillar template + render
(both paths) + all three pillars authored.** This is the first live consumer of an
R15 `type` field, so it also lands 373 Slice 1's pillar template. The listing
integration (acceptance #2 — pillars in `agency_welcome` / `skills.find`) is Slice 2.

**Owner decision (collision).** `intent` is already a live CAPABILITY owning
`skills/intent/SKILL.md` (lifecycle · memory are free). Per owner directive the
intent pillar AUGMENTS the capability skill with a concept section rather than
clobbering it; lifecycle · memory render standalone at `skills/<name>`.

Done (file:line evidence):
- `agency/pillars/{intent,lifecycle,memory}.yaml` — the three concept pillars as
  committed `skill.yaml` of `type: pillar` (kind=pillar, owner=capability), each
  with description (R1), a concept `overview`, when-to-use / when-not, and one
  `examples` entry (R9). intent → bootstrap/clarify/confirm + clarity gate +
  critical-thinking; lifecycle → open/move/close + read/find/check/watch + A2A;
  memory → record/recall/link + bi-temporal + provenance edges.
- `agency/_pillars.py` — `load_pillars(directory=None)` globs the source dir,
  YAML-loads each, validates via `parse_skill` (371), returns the dicts sorted by
  name (deterministic, A7). A malformed pillar is a fail-fast `ValueError` naming
  the file — a broken concept skill never silently vanishes from the install.
- `agency/render/skill/pillar.md` — the per-type pillar template (373 Slice 1's
  first variant): frontmatter (name/description/allowed-tools) + `# <Title> pillar`.
- `agency/skill_emit.py` — `_pillar_sections(skill)` builds the concept body
  (overview + optional when-to-use/when-not/example/mistakes/refs, frugal — no
  empty headers) CONCATENATED (not `Template.substitute`d, so a literal `$` in an
  example never breaks render); `render_pillar(skill)` → standalone
  `skills/<name>/SKILL.md`; `augment_with_pillar(existing_md, skill)` appends a
  `## The <Title> pillar (concept)` section to a colliding capability skill.
- `agency/install.py::generate` — after the per-cap emit loop, loads pillars and
  branches per name: collision (path already in files) → augment; else standalone.
- Tests: `tests/acceptance/features/pillar_skills.feature` + `test_pillar_skills.py`
  — 4 scenarios: (1) source loads as schema-valid type=pillar incl. all three; (2)
  a non-colliding pillar (lifecycle) renders standalone, self-contained (frontmatter
  + overview inline); (3) the intent pillar augments the capability skill — verb
  table RETAINED + concept section gained; (4) determinism (regen twice identical
  for both the standalone and augmented paths). 4/4 green; 278 across the
  skill/render/install/schema/naming blast radius; install regen + check-drift clean.

Still:
- **Slice 2** — listing integration: the pillars appear in `agency_welcome` /
  `skills.find` (`_all_skills` scans only capability `ontology.skills` today; pillars
  are not a capability, so they need a source the listing reads). Acceptance #2.
