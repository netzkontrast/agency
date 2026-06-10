---
spec_id: "177"
slug: plugin-reference-continuous-audit
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "064"
depends_on: ["064", "148", "175", "149"]
vision_goals: [5, 4]
affects:
  - scripts/check-plugin-reference
  - tests/test_plugin_reference_audit.py
---

# Spec 177 — plugin-reference continuous-compliance audit

## Why

Spec 064 (plugin-reference-compliance) brought the plugin to the
superpowers 5.1.0 + episodic-memory 1.4.2 reference patterns
(cross-platform hooks, `hooks.json` matcher, `.mcp.json` cwd, the
`using-agency` meta-skill). But it was a POINT-IN-TIME alignment.
Per the `working-with-claude-code` skill, the plugin reference evolves;
the alignment should be a STANDING audit so the plugin doesn't drift
from current Claude Code conventions as new slash commands (Spec 148)
and a derived install surface (Spec 175) land.

## Done When

- [ ] **`scripts/check-plugin-reference`** asserts the live plugin
      against the documented reference invariants: `plugin.json` shape,
      `hooks.json` matcher + async, `.mcp.json` env passthrough, the
      polyglot `run-hook.cmd`, every command file has valid frontmatter.
- [ ] **The new slash family (Spec 148) passes the command-frontmatter
      check** — a malformed `/agency-<skill>` fails CI.
- [ ] **Derived install surface (Spec 175) is audited** — marketplace
      entry shape stays reference-compliant.
- [ ] **CI job** runs it on every PR.
- [ ] Test: a malformed command file + a stale `.mcp.json` each trip the
      audit.
- [ ] TODO row + drift clean.

## Interconnects

- **UX-onboarding chain** (148): audits the new command surface.
- **Drift-derivation chain** (149/175): audits the derived install.
- Spec 064 is the parent alignment.

## Open questions

1. Pin to a Claude Code reference version? **Recommend**: track the
   `working-with-claude-code` skill's documented shape; re-run the
   audit when that skill updates (a doc-source marker, Spec 054 family).
