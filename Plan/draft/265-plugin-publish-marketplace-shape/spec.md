---
spec_id: "265"
slug: plugin-publish-marketplace-shape
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "061"
depends_on: ["061", "175", "148", "177", "149", "259"]
vision_goals: [5]
affects:
  - .claude-plugin/marketplace.json
  - tests/test_marketplace_shape.py
---

# Spec 265 — plugin marketplace.json: full derived shape

## Why

Spec 061 made `marketplace.json` description read the live registry.
Spec 175 derives the install surface. But the PLUGIN MARKETPLACE entry
itself (per `developing-claude-code-plugins` skill) carries more than
description: name, version, source, dependencies, the advertised slash
command family. Today these are hand-edited; an agency wave that adds
a verb or a slash entry has to remember to update marketplace.json by
hand — drift waiting to happen. This spec lands the FULL derived
shape so `/plugin install agency` resolves to a manifest that is
guaranteed in-sync with the registry + charter + slash family.

## Done When

- [ ] **`.claude-plugin/marketplace.json` fully derived** from
      `pyproject.toml` (name + version + source URL) + the live
      registry (capabilities + verb counts) + the charter (vision_goals
      tagline) + the slash family (Spec 148).
- [ ] **Typed `MarketplaceShape` schema** asserted on every CI run:
      ```python
      class MarketplaceShape(TypedDict):
          name: str                       # from pyproject.toml
          version: str                    # from pyproject.toml
          source: dict                    # {type, url} from git remote
          description: str                # derived from charter Goal paragraph
          capabilities: list[str]         # live registry list
          slash_commands: list[str]       # Spec 148 family
          dependencies: dict[str, str]    # pyproject dev/runtime deps
          generated_at: str               # body, NOT prefix
      ```
- [ ] **Slash family from Spec 148 advertised** in
      `marketplace.json.slash_commands` — every shipped slash entry
      appears; unshipped drafts do not.
- [ ] **Version pinning** via the substrate hardening rules (Spec 092
      generalization, Spec 205) — `pyproject.toml.version` is the
      single source; marketplace mirrors it; both update together.
- [ ] **`check-plugin-reference` (Spec 177) gates the shape** — any
      reference in marketplace.json to a verb/skill/slash that does
      not exist in the live registry fails CI.
- [ ] **Measurable invariants** (relationships, not pinned values):
      - `marketplace.json.version == pyproject.toml.version` (always)
      - `set(marketplace.json.capabilities) ==
        set(live_registry.capabilities)` (set equality, not count)
      - `set(marketplace.json.slash_commands) ⊆
        set(commands/*.md basenames)` (every advertised slash exists)
      - `every dep in marketplace.json.dependencies appears in
        pyproject.toml[project|tool.poetry].dependencies`
      - `len(capabilities) > 0` (sanity — empty manifest is a bug)
- [ ] Test: marketplace.json round-trips through `/plugin install`
      (mocked harness); shape audit passes; a sabotaged stale verb
      reference trips Spec 177.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  live registry has 18 capabilities; pyproject.toml version
        bumps from 0.34.0 → 0.35.0; Spec 148 adds /agency-onboard
        as a new shipped slash entry
When:   derive-marketplace runs (part of Spec 149 derive-docs)
Then:   marketplace.json regenerates with:
        - version: "0.35.0" (mirrors pyproject)
        - capabilities: [..18 items..] (matches live set)
        - slash_commands: [..., "agency-onboard"] (Spec 148 reflected)
        - description: derived from charter Goal paragraph
        AND check-plugin-reference (Spec 177) passes
        AND Spec 259 self-test confirms marketplace.json updated

Given:  PR proposes removing a capability without updating
        marketplace.json
When:   CI runs check-plugin-reference
Then:   fails with "marketplace.json.capabilities includes 'X' but
        the live registry does not" — PR cannot merge until
        marketplace.json regenerates

Given:  user types `/plugin install agency` against a published
        marketplace
When:   the harness fetches marketplace.json and resolves dependencies
Then:   install succeeds; the slash family advertised matches what
        ships on disk; no orphan references
```

## Failure modes (Nygard)

| Failure | Marketplace response |
|---|---|
| Stale capability reference (registry removed it) | Spec 177 fails CI; marketplace.json must regenerate |
| Version mismatch (pyproject vs marketplace) | Spec 149 self-test trips; both update in lock-step |
| Slash entry advertised but commands/*.md missing | `set ⊆` invariant fails; CI blocks |
| Source URL drift (repo renamed) | Pyproject `repository` field is the source; marketplace mirrors; rename updates both |
| Dependencies fork (marketplace claims a dep not in pyproject) | Invariant fails; cannot merge |
| Marketplace published to a registry that pinned an old version | Versioned releases; the marketplace shape is per-release; no in-place mutation |
| `description` exceeds marketplace char limit | Derive a truncated form with a `…` ellipsis + link to charter; never silent overflow |

## Interconnects

- Spec 061 (parent — description derivation) — extends to full shape.
- Spec 175 (install surface derived) — sibling derivation; shares
  the live-registry read.
- Spec 148 (slash family) — provides the slash_commands list.
- Spec 177 (plugin reference audit) — gates the shape's references.
- Spec 149 (derived-doc discipline) — marketplace.json is a derived
  surface like TODO.md.
- Spec 259 (derived-doc self-test) — the self-test covers marketplace
  regeneration end-to-end.
- **UX-onboarding chain** completion at the install surface.

## Open questions

1. **Should the marketplace shape be one file per release, or one
   evolving file?** **Recommend**: evolving file in the repo;
   per-release snapshots in GitHub Releases (the install URL pins by
   tag).
2. **How are private / unshipped slash entries handled?**
   **Recommend**: only `status: shipped` slash entries appear; drafts
   never leak into the public marketplace.
3. **Cross-plugin dependencies (e.g. agency depending on the
   `claude-api` skill bundle)?** **Recommend**: list as dependencies
   with explicit version constraints; resolve at install time via the
   harness's standard dependency resolver per the
   `developing-claude-code-plugins` skill.
