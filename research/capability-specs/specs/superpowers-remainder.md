---
spec_id: superpowers-remainder-001
slug: superpowers-remainder
status: draft
owner: "@claude"
depends_on: []
affects:
  - "agency/capabilities/plugin.py"
  - "agency/capabilities/reflect.py"
source-repos:
  - "https://github.com/obra/superpowers-marketplace @ 6be22035d873c31ca246db4f4932a1098aea46fc"
estimated_jules_sessions: 2
domain: "superpowers"
wave: 1
---

# Superpowers Remainder Cluster

## Why
The port of superpowers into Agency (detailed in `docs/vision/specs/superpowers-port.md`) initially focused on core skill matrices. However, a complete ingestion mandates porting the *entire* system—including every plugin, every skill's `SKILL.md`, their associated `references/` docs, the `lib/` helper modules, `bin/` scripts, and any hooks or tooling present in the marketplace. We must bring these components into the Agency baseline, treating heavy instructional prose as T3 progressive-disclosure files, `lib/`/`bin/` logic as code-mode capability utilities, and rationalization checks into structural `gate` endpoints.

## Done When
- [ ] Implement `superpowers.reference` verb to fetch T3 context documents spanning all skill `references/` directories.
- [ ] Implement `superpowers.rationalize` as a `transform` block that enforces reasoning against defined rules.
- [ ] Port `bin/` execution scripts and `lib/` helper modules into standard Agency utility imports (or sandbox execution wrappers).
- [ ] Migrate all exhaustive `SKILL.md` configurations into Agency `OntologyExtension` registrations.
- [ ] Integrate remaining hooks into standard Agency lifecycle triggers.

## Source clones
```bash
git clone --depth=1 https://github.com/obra/superpowers-marketplace.git ~/work/vendor/superpowers-marketplace
# SHA: 6be22035d873c31ca246db4f4932a1098aea46fc
```

## Files
- Modify: `agency/capabilities/plugin.py`
- Modify: `agency/capabilities/reflect.py`

## Evidence
- `superpowers-marketplace/` base layout including `SKILL.md` definitions, `references/`, `lib/`, and `bin/` components.

## Self-Review
Completes the absolute 100% depth port of superpowers, moving beyond just skill schemas to include all executing scripts, helpers, and documentation layers as dictated by the deep ingestion mandate.
